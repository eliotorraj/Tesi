"""Report riproducibile da registri conclusi; non avvia LLM o compilazioni quantistiche."""
from __future__ import annotations
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comune import *
from registro import replay
import argparse
import csv
import statistics
import subprocess


def mean(values):
    values = [x for x in values if finite(x)]
    return statistics.mean(values) if values else None


def summarize(rows, expected):
    paired = [r for r in rows if r["delta_score"] is not None]
    diffs = [r["delta_score"] for r in paired]
    return {
        "expected": expected, "completed": len(rows), "paired": len(paired),
        "successes": sum(r["status"] == "success" for r in rows),
        "failures": sum(r["status"] != "success" for r in rows),
        "mean_incremental_paired": mean(r["score"] for r in paired),
        "mean_baseline_paired": mean(r["baseline_score"] for r in paired),
        "mean_delta": mean(diffs),
        "median_delta": statistics.median(diffs) if diffs else None,
        "worst_delta": min(diffs) if diffs else None,
        "better": sum(d > 1e-12 for d in diffs),
        "equal": sum(abs(d) <= 1e-12 for d in diffs),
        "worse": sum(d < -1e-12 for d in diffs),
        "memory_final": rows[-1]["memory_after"] if rows else 0,
        "circuits_using_memory": sum((r.get("retrieved_incremental") or 0) > 0 for r in rows),
        "mean_regret": mean(r["regret"] for r in rows),
        "regret_denominator": sum(r["regret"] is not None for r in rows),
        "oracle_complete": sum(r["oracle_exhaustive"] is True and r["regret"] is not None for r in rows),
        "oracle_partial": sum(r["oracle_exhaustive"] is False and r["regret"] is not None for r in rows),
        "facts_unverified": sum(r.get("facts_unverified") is True for r in rows),
        **{metric: {"mean_known": mean(r[metric] for r in rows),
                    "measured": sum(finite(r[metric]) for r in rows)}
           for metric in ("total_seconds", "baseline_total_seconds", "total_tokens",
                          "baseline_total_tokens", "choice_seconds", "compilation_seconds", "llm_calls")},
    }


def collect(experiment_id, oracle_path=None):
    data = {"revision": 1, "experiment_id": experiment_id, "created_at": now(),
            "kind": "measured_results", "orders": {}, "sources": {}, "oracle": None,
            "limitations": [
                "Confronto con esiti storici, non rieseguiti nello stesso ambiente temporale.",
                "Recupero esatto in memoria, con normalizzazione train fissa; tempi non equivalenti all'indice storico.",
                "Il prompt distingue singole osservazioni dagli esempi confrontati; cambia quando sono recuperate osservazioni.",
                "Quattro ordini degli stessi circuiti: non sono 360 osservazioni indipendenti.",
                "Test già esaminato; la nuova campagna valuta il comportamento sequenziale.",
                "L'oracle è il massimo osservato su tre seed e sulla griglia Qiskit, talvolta incompleta.",
                "Tempi noti fino all'arresto; dati mancanti e fallimenti non valgono zero.",
                "Memoria ed energia di picco non misurate.",
            ]}
    references = {}
    if oracle_path:
        oracle_path = Path(oracle_path).resolve()
        oracle = read(oracle_path)
        refs = oracle["rows"]
        if len({r["circuit_id"] for r in refs}) != len(refs):
            raise ValueError("Oracle con identificativi duplicati.")
        references = {r["circuit_id"]: r for r in refs}
        data["oracle"] = {"path": str(oracle_path), "sha256": sha(oracle_path),
                          "identity": oracle.get("oracle_identity"),
                          "note": "Riepilogo storico letto soltanto dal report; nessun dato passato al runner."}
    for order in ORDERS:
        base = campaign_path(experiment_id, order)
        if not (base / "contratto.json").exists():
            data["orders"][order] = {"status": "not_prepared", "rows": [], "summary": summarize([], 90)}
            continue
        contract = check_contract(base, verify_runtime=False)
        records, commits, _ = replay(base, contract)
        data["sources"][str(base / "contratto.json")] = sha(base / "contratto.json")
        data["sources"].update({str(REPO / p): h for p, h in contract["baseline_files"].items()})
        rows = []
        cumulative = []
        for position, commit in enumerate(commits, 1):
            source = contract["rows"][position-1]
            folder = step_folder(base, position, source)
            outcome = read(folder / "esito.json")
            baseline = read(BASELINE / "circuiti" / source["circuit_id"] / "esito.json")
            score = outcome.get("score") if valid_score(outcome) else None
            control = baseline.get("score") if valid_score(baseline) else None
            reference = references.get(source["circuit_id"])
            if reference and reference["source_sha256"] != source["source_sha256"]:
                raise ValueError("Oracle relativo a una sorgente diversa.")
            if reference and abs(reference["system_score"] - baseline["score"]) > 1e-12:
                raise ValueError("Oracle e controllo storico non concordano.")
            oracle_score = reference["oracle_score"] if reference else None
            if oracle_score is not None and (not finite(oracle_score) or not 0 <= oracle_score <= 1):
                raise ValueError("Score oracle non valido.")
            delta = score - control if score is not None and control is not None else None
            if delta is not None:
                cumulative.append(delta)
            retrieval = read(folder / "retrieval.json") if (folder / "retrieval.json").exists() else {}
            retrieved = retrieval.get("records", [])
            entry = {
                "order": order, "position": position, "circuit_id": source["circuit_id"],
                "source_sha256": source["source_sha256"], "status": outcome["status"],
                "score": score, "baseline_score": control, "delta_score": delta,
                "cumulative_mean_delta": mean(cumulative), "cumulative_paired_n": len(cumulative),
                "oracle_score": oracle_score, "oracle_exhaustive": reference["exhaustive"] if reference else None,
                "regret": oracle_score-score if oracle_score is not None and score is not None else None,
                "baseline_regret": oracle_score-control if oracle_score is not None and control is not None else None,
                "memory_before": commit["memory_before_count"], "memory_after": commit["memory_after_count"],
                "retrieved_incremental": sum(r["origin"] == "incremental" for r in retrieved) if retrieved else None,
                "nearest_distance": min((r["distance"] for r in retrieved), default=None),
                "facts_unverified": outcome.get("accepted_with_unverified_facts"),
                **{metric: outcome.get(metric) for metric in
                   ("total_seconds", "choice_seconds", "compilation_seconds", "total_tokens",
                    "llm_calls", "retries", "rag_seconds")},
                "baseline_total_seconds": baseline.get("total_seconds"),
                "baseline_total_tokens": baseline.get("total_tokens"),
            }
            rows.append(entry)
            data["sources"][str(folder / "commit.json")] = sha(folder / "commit.json")
        data["orders"][order] = {"status": "completed" if len(commits) == len(contract["rows"]) else "partial",
                                  "rows": rows, "summary": summarize(rows, len(contract["rows"]))}
    return data


def tex_escape(value):
    result = str(value)
    return "".join({"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                    "#": r"\#", "{": r"\{", "}": r"\}", "$": r"\$"}.get(c, c) for c in result)


def number(value, digits=4):
    return "--" if value is None else f"{value:.{digits}f}"


def order_label(order):
    return {"01_manifest": "Manifest", "02_inverso": "Inverso",
            "03_casuale_20261002": "Casuale 1", "04_casuale_20261003": "Casuale 2"}.get(order, order)


def plot(data, field, ylabel, *, scale=1):
    palette = ["blue!70!black", "orange!90!black", "green!50!black", "purple"]
    lines = [
        r"\begin{tikzpicture}\begin{axis}[width=\linewidth,height=5.0cm,grid=major,",
        r"xlabel={Posizione nel flusso},ylabel={" + ylabel + r"},",
        r"legend style={font=\scriptsize,at={(0.5,-0.25)},anchor=north,legend columns=2},",
        r"tick label style={font=\small},label style={font=\small},scaled y ticks=false]",
    ]
    count = 0
    for (order, item), color in zip(data["orders"].items(), palette):
        points = [(r["position"], r.get(field)) for r in item["rows"] if finite(r.get(field))]
        if points:
            count += 1
            coords = " ".join(f"({x},{y*scale:.10f})" for x, y in points)
            lines += [r"\addplot+[mark=none,thick,color=" + color + "] coordinates {" + coords + "};",
                      r"\addlegendentry{" + tex_escape(order_label(order)) + "}"]
    lines.append(r"\end{axis}\end{tikzpicture}")
    return "\n".join(lines) if count else r"\emph{Nessuna misura disponibile per questo grafico.}"


def render_tex(data):
    summary_rows, resource_rows = [], []
    for order, item in data["orders"].items():
        s = item["summary"]
        summary_rows.append(" & ".join([
            tex_escape(order_label(order)), f"{s['completed']}/{s['expected']}", str(s["paired"]),
            number(s["mean_incremental_paired"]), number(s["mean_baseline_paired"]),
            number(s["mean_delta"], 6), f"{s['better']}/{s['equal']}/{s['worse']}",
            str(s["failures"]), str(s["memory_final"])]) + r" \\")
        resource_rows.append(" & ".join([
            tex_escape(order_label(order)),
            number(s["total_seconds"]["mean_known"], 2) + "/" + number(s["baseline_total_seconds"]["mean_known"], 2),
            str(s["total_seconds"]["measured"]) + "/" + str(s["baseline_total_seconds"]["measured"]),
            number(s["total_tokens"]["mean_known"], 0) + "/" + number(s["baseline_total_tokens"]["mean_known"], 0),
            str(s["total_tokens"]["measured"]) + "/" + str(s["baseline_total_tokens"]["measured"]),
            str(s["circuits_using_memory"])]) + r" \\")
    status = "DATI SINTETICI: SOLO VERIFICA DEL SOFTWARE" if data.get("kind") == "synthetic_verification" else "RISULTATI OSSERVATI"
    if not any(x["rows"] for x in data["orders"].values()):
        status = "CAMPAGNE NON ANCORA ESEGUITE: NESSUN RISULTATO"
    text = r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage[italian]{babel}
\usepackage[margin=1.8cm]{geometry}\usepackage{booktabs,graphicx,pgfplots,hyperref}
\pgfplotsset{compat=1.18}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\begin{document}
\begin{center}{\Large Memoria incrementale per LLM + RAG}\\[4pt]
\textbf{@@STATUS@@}\\
Esperimento: \texttt{@@ID@@}
\end{center}
\section*{Obiettivo e condizioni}
Si valuta se le compilazioni concluse durante l'uso possano fornire esempi utili alle
decisioni successive. Ogni ordinamento parte dagli stessi 396 esempi train e da
una memoria incrementale vuota. Si considerano i 90 circuiti Test MQT Bench già
valutati, nell'ordine del manifest, nell'ordine inverso e in due permutazioni
con seed 20261002 e 20261003.
Il sistema usa Qwen3.5-4B Q8\_0 a temperatura zero, cinque esempi, distanza Manhattan
su 49 caratteristiche e trasformazione fissata sul train. La memoria dei quattro
ordini è indipendente. Una sola compilazione Qiskit, con seed zero e limite di
100 secondi, produce l'eventuale nuova osservazione.
Il risultato entra nella memoria solo dopo la conclusione del circuito: non può
influenzare la decisione che lo ha generato. Una singola esecuzione non viene
presentata come vincitrice di un confronto fra configurazioni.
\section*{Qualità e copertura}
Il controllo è LLM + RAG con Dataset fisso, dai registri storici.
Per ogni circuito riuscito in entrambi, $\Delta=S_{\mathrm{incrementale}}-S_{\mathrm{fisso}}$:
un valore positivo favorisce la memoria incrementale. La media usa soltanto
le coppie confrontabili; fallimenti e dati mancanti sono riportati separatamente.
La colonna $+ /= /-$ conta miglioramenti, parità e peggioramenti, con tolleranza
$10^{-12}$. Gli score sono stime di expected fidelity su Target sintetici.
\begin{center}\scriptsize
\begin{tabular}{lrrrrrrrr}\toprule
Ordine & Conclusi & Coppie & $S$ incr. & $S$ fisso & $\overline{\Delta}$ & $+ /= /-$ & Falliti & Aggiunte\\\midrule
@@SUMMARY@@
\bottomrule\end{tabular}\end{center}
@@QUALITY_PLOT@@
\par\small Il grafico mostra la differenza media cumulativa rispetto al controllo,
sui successi comuni osservati fino alla posizione indicata. I circuiti in una stessa
posizione possono differire fra ordinamenti; i denominatori sono conservati nei dati.
\normalsize
\clearpage
\section*{Utilizzo della memoria e risorse}
@@MEMORY_PLOT@@
\par Il grafico conta le osservazioni ammesse dopo ogni decisione.
La crescita della memoria non implica di per sé un miglioramento delle scelte.
\begin{center}\scriptsize
\begin{tabular}{lrrrrr}\toprule
Ordine & Tempo medio (s) & $n$ tempi & Token medi & $n$ token & Casi con memoria\\\midrule
@@RESOURCES@@
\bottomrule\end{tabular}\end{center}
Nelle colonne di tempi, token e denominatori, il primo valore riguarda il sistema
incrementale e il secondo il controllo storico sugli stessi circuiti conclusi.
I tempi comprendono preparazione, decisione, eventuali correzioni e compilazione.
I token contano l'intero ingresso e l'uscita per chiamata, incluso il contesto
riutilizzato dal server. Le medie usano solo misure disponibili: i denominatori
sono distinti. Le durate di esiti interrotti o in timeout sono tempi osservati
fino all'arresto. Non sono disponibili misure di energia o memoria di picco.
\section*{Riferimento oracle e limiti}
Quando disponibile, il report calcola anche $R-S$, dove $R$ è il massimo osservato
nella griglia di cinque dispositivi, dodici configurazioni e tre seed.
Lo scarto non viene troncato a zero. I riferimenti completi e parziali sono distinti
nei dati; un massimo incompleto non certifica l'ottimalità e il massimo su tre seed
è favorevole al riferimento rispetto alla singola compilazione del sistema.
Gli score oracle non entrano mai nel recupero o nella regola di ammissione.
@@LIMITS@@
Le tabelle per circuito e i riepiloghi leggibili da programma conservano i risultati
favorevoli e sfavorevoli. Ogni generazione del documento identifica con impronte
le fonti utilizzate. Il confronto è descrittivo e non attribuisce automaticamente
all'accumulo di memoria una superiorità generale.
\end{document}
"""
    replacements = {
        "@@STATUS@@": tex_escape(status), "@@ID@@": tex_escape(data["experiment_id"]),
        "@@SUMMARY@@": "\n".join(summary_rows), "@@RESOURCES@@": "\n".join(resource_rows),
        "@@QUALITY_PLOT@@": plot(data, "cumulative_mean_delta", r"$\overline{\Delta}$ (punti percentuali)", scale=100),
        "@@MEMORY_PLOT@@": plot(data, "memory_after", "Osservazioni ammesse"),
        "@@LIMITS@@": "\n\n".join(tex_escape(x) for x in data["limitations"]),
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def write_report(data, output, pdf=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    save(output / "dati.json", data)
    rows = [r for item in data["orders"].values() for r in item["rows"]]
    fields = list(rows[0]) if rows else ["order", "position", "circuit_id", "status", "score", "delta_score"]
    with (output / "circuiti.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (output / "riepilogo.csv").open("x", newline="", encoding="utf-8") as handle:
        fields = ["order", "completed", "paired", "mean_incremental_paired", "mean_baseline_paired", "mean_delta", "better", "equal", "worse", "failures", "memory_final"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for order, item in data["orders"].items():
            writer.writerow({"order": order, **{k: item["summary"][k] for k in fields if k != "order"}})
    tex = output / "rapporto.tex"
    tex.write_text(render_tex(data), encoding="utf-8")
    charts = output / "grafici"
    charts.mkdir()
    chart_specs = [
        ("qualita", "cumulative_mean_delta", r"$\overline{\Delta}$ (punti percentuali)", 100),
        ("memoria", "memory_after", "Osservazioni ammesse", 1),
    ]
    figure_paths = []
    for name, field, label, scale in chart_specs:
        figure = charts / (name + ".tex")
        figure.write_text(
            r"\documentclass[tikz,border=5pt]{standalone}\usepackage[T1]{fontenc}"
            r"\usepackage{pgfplots}\pgfplotsset{compat=1.18}\begin{document}" + "\n"
            + plot(data, field, label, scale=scale).replace(r"width=\linewidth", "width=16cm")
            + "\n" + r"\end{document}" + "\n", encoding="utf-8")
        figure_paths.append(figure)
    if pdf:
        for attempt in (1, 2):
            proc = subprocess.run(["pdflatex", "-no-shell-escape", "-halt-on-error",
                                   "-interaction=nonstopmode", tex.name],
                                  cwd=output, capture_output=True, text=True, timeout=90)
            (output / f"compilazione_{attempt}.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
            if proc.returncode:
                raise RuntimeError("Compilazione LaTeX fallita; sorgente e log conservati.")
        for figure in figure_paths:
            proc = subprocess.run(["pdflatex", "-no-shell-escape", "-halt-on-error",
                                   "-interaction=nonstopmode", figure.name],
                                  cwd=charts, capture_output=True, text=True, timeout=90)
            (charts / (figure.stem + "_compilazione.txt")).write_text(proc.stdout + proc.stderr, encoding="utf-8")
            if proc.returncode:
                raise RuntimeError("Compilazione del grafico fallita; log conservato.")
    save(output / "provenienza.json", {
        "generator_sha256": sha(Path(__file__)), "sources": data["sources"],
        "oracle": data.get("oracle"), "kind": data["kind"],
        "artifacts": {str(p.relative_to(output)): sha(p) for p in output.rglob("*") if p.is_file()},
    })
    return tex


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment-id", default=DEFAULT_ID)
    ap.add_argument("--oracle", type=Path, help="Riepilogo oracle storico opzionale, solo per analisi")
    ap.add_argument("--pdf", action="store_true", help="Compila con pdfLaTeX già installato")
    args = ap.parse_args(argv)
    data = collect(args.experiment_id, args.oracle)
    output = BASE / "report/risultati" / args.experiment_id / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    print(write_report(data, output, args.pdf))


if __name__ == "__main__":
    main()

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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracoli
sys.path.insert(0, str(REPO / "archivio/valutazione/rag_incrementale/report"))
import sintesi


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
                "MQT Bench già esaminato; la nuova campagna valuta il comportamento sequenziale.",
                "L'oracle è il massimo osservato su tre seed e sulla griglia Qiskit, talvolta incompleta.",
                "Tempi noti fino all'arresto; dati mancanti e fallimenti non valgono zero.",
                "Memoria ed energia di picco non misurate.",
            ]}
    circuits = sorted(test_rows(), key=lambda r: r["circuit_id"])
    data["circuits"] = circuits
    data["sources"].update({str(REPO / p): h for p,h in baseline_files(circuits).items()})
    data["baseline"] = {}
    for row in circuits:
        outcome = read(BASELINE / "circuiti" / row["circuit_id"] / "esito.json")
        data["baseline"][row["circuit_id"]] = {
            "score": outcome.get("score") if valid_score(outcome) else None,
            "status": outcome["status"]}
    references = {}
    if oracle_path:
        references, info, sources = oracoli.load_reference(oracle_path, circuits)
        data["oracle"] = info
        data["sources"].update(sources)
    data["references"] = references
    for order in ORDERS:
        base = campaign_path(experiment_id, order)
        if not (base / "contratto.json").exists():
            data["orders"][order] = {"status": "not_prepared", "rows": [], "summary": summarize([], 90)}
            continue
        contract = check_contract(base, verify_runtime=False)
        if data["oracle"]:
            if contract["targets"] != data["oracle"]["targets"]:
                raise ValueError("Target incrementali diversi dall'oracle.")
            for name in ("qiskit", "mqt.bench", "numpy"):
                if contract["versions"][name] != data["oracle"]["versions"][name]:
                    raise ValueError("Versione diversa dall'oracle: " + name)
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
            if reference and reference["system_score"] != control:
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
                "source_sha256": source["source_sha256"], "num_qubits": source.get("num_qubits"), "status": outcome["status"],
                "score": score, "baseline_score": control, "delta_score": delta,
                "cumulative_mean_delta": mean(cumulative), "cumulative_paired_n": len(cumulative),
                "oracle_score": oracle_score, "oracle_exhaustive": reference["exhaustive"] if reference else None,
                "regret": oracle_score-score if oracle_score is not None and score is not None else None,
                "baseline_regret": oracle_score-control if oracle_score is not None and control is not None else None,
                "relative_gap_percent": 100*(oracle_score-score)/oracle_score if oracle_score is not None and oracle_score > 0 and score is not None else None,
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
    data["comparisons"] = oracoli.compare_orders(data)
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
        r"\begin{tikzpicture}\begin{axis}[width=0.98\linewidth,height=3.9cm,grid=major,",
        r"xmin=1,xmax=90,xtick={1,10,20,30,40,50,60,70,80,90},xlabel={Posizione nel flusso},ylabel={" + ylabel + r"},",
        r"legend style={font=\scriptsize,at={(0.5,0)},yshift=-32pt,anchor=north,legend columns=4},",
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
    return sintesi.render_tex(data, oracoli, 'MQT Bench', 5)


def write_report(data, output, pdf=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    data["comparisons"] = oracoli.compare_orders(data)
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
        ("qualita", "cumulative_mean_delta", r"$\overline{\Delta}$ (\%)", 100),
        ("memoria", "memory_after", "Osservazioni ammesse", 1),
    ]
    specs = [(name, plot(data, field, label, scale=scale).replace(r"width=0.98\linewidth", "width=24cm"))
             for name, field, label, scale in chart_specs] + oracoli.figure_specs(data)
    figure_paths = []
    for name, body in specs:
        figure = charts / (name + ".tex")
        banner = r"\textbf{DATI SINTETICI - SOLO VERIFICA SOFTWARE}\par " if data["kind"] == "synthetic_verification" else ""
        figure.write_text(
            r"\documentclass[border=5pt]{standalone}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}"
            r"\usepackage{pgfplots}\pgfplotsset{compat=1.18}\begin{document}"
            r"\begin{minipage}{26.3cm}\centering " + banner + r"\textbf{" + tex_escape(oracoli.figure_title(name))
            + r"}\par\medskip " + body + r"\end{minipage}\end{document}" + "\n", encoding="utf-8")
        figure_paths.append(figure)
    for name, rows in (("confronto_ordinamenti.csv", data["comparisons"]["summary"]),
                       ("confronti_appaiati.csv", data["comparisons"]["pairwise"])):
        with (output / name).open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
                                 for key, value in row.items()})
    aligned = [{"order": order, **row} for order in data["orders"] for row in oracoli.aligned_rows(data, order)]
    with (output / "distanze_oracle.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(aligned[0]))
        writer.writeheader()
        writer.writerows(aligned)
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
        "generator_sha256": sha(Path(__file__)), "synthesis_module_sha256": sha(Path(sintesi.__file__)), "oracle_module_sha256": sha(Path(oracoli.__file__)), "sources": data["sources"],
        "oracle": data.get("oracle"), "kind": data["kind"],
        "artifacts": {str(p.relative_to(output)): sha(p) for p in output.rglob("*") if p.is_file()},
    })
    return tex


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment-id", default=DEFAULT_ID)
    ap.add_argument("--oracle", type=Path, default=ORACLE, help="dati.json del confronto oracle MQT Bench verificabile")
    ap.add_argument("--senza-oracle", action="store_true", help="Report esplicitamente privo del riferimento oracle")
    ap.add_argument("--pdf", action="store_true", help="Compila con pdfLaTeX già installato")
    args = ap.parse_args(argv)
    data = collect(args.experiment_id, None if args.senza_oracle else args.oracle)
    output = BASE / "report/risultati" / args.experiment_id / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    print(write_report(data, output, args.pdf))


if __name__ == "__main__":
    main()

"""Forma sintetica comune ai report incrementali; usa solo misure già raccolte."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import statistics

TOL = 1e-12


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def escape(value):
    return "".join({"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                    "#": r"\#", "{": r"\{", "}": r"\}", "$": r"\$"}.get(c, c)
                   for c in str(value))


def number(value, digits=3):
    return f"{value:.{digits}f}".replace(".", ",")


def conclusions(data):
    """Le osservazioni quantitative sono ricavate dalle coppie, senza sommare repliche."""
    if data.get("kind") != "measured_results":
        return r"Dati sintetici: verificano la forma del report e non consentono conclusioni sperimentali."
    count = len(data["circuits"])
    if not data["orders"] or any(item["status"] != "completed" for item in data["orders"].values()):
        return r"Campagna incompleta: i grafici descrivono soltanto le misure disponibili; non si trae una conclusione sui quattro ordinamenti."
    paired = []
    means = []
    for item in data["orders"].values():
        rows = [r for r in item["rows"] if finite(r.get("score")) and finite(r.get("baseline_score"))]
        paired.extend(rows)
        if rows:
            means.append(statistics.mean(r["score"] - r["baseline_score"] for r in rows))
    if not paired:
        return r"Non ci sono coppie confrontabili con RAG fisso."
    better = sum(r["score"] - r["baseline_score"] > TOL for r in paired)
    worse = sum(r["score"] - r["baseline_score"] < -TOL for r in paired)
    equal = len(paired) - better - worse
    negative = [x for x in means if x < -TOL]
    positive = [x for x in means if x > TOL]
    if len(negative) == len(data["orders"]):
        result = (f"Tutti e quattro gli ordinamenti hanno uno score medio inferiore al RAG fisso: "
                  f"la perdita va da {number(100*min(-x for x in negative))} a "
                  f"{number(100*max(-x for x in negative))}\\%.")
    else:
        result = (f"Gli ordinamenti con score medio inferiore al RAG fisso sono {len(negative)} su {len(data['orders'])}. ")
        if positive:
            result += (f"Il miglior guadagno medio è di {number(100*max(positive))}\\%"
                       + (f", contro una perdita massima media di {number(-100*min(negative))}\\%."
                          if negative else "."))
    result += (f" Su {len(paired)} confronti circuito-ordine, {equal} risultati restano invariati, "
               f"{worse} peggiorano e {better} migliorano.")
    losses = [r for r in paired if r["baseline_score"] > 0 and r["score"] < r["baseline_score"] - TOL]
    if losses:
        worst = max(losses, key=lambda r: r["baseline_score"] - r["score"])
        loss = worst["baseline_score"] - worst["score"]
        result += (f" La perdita individuale più ampia è di {number(100*loss, 2)}\\%, "
                   f"pari al {number(100*loss/worst['baseline_score'], 1)}\\% dello score del RAG fisso.")
    if len(negative) > len(positive):
        interpretation = (
            "Una spiegazione plausibile è che LLM + RAG non ottenga sempre la migliore compilazione. "
            "L'aggiunta automatica di esempi derivati da scelte subottimali può quindi peggiorare "
            "le informazioni recuperate dal Dataset rispetto alla versione originale senza incremento, "
            "anche se gli esempi originali restano intatti. I risultati sono coerenti con questa "
            "ipotesi, ma non dimostrano da soli che sia l'unica causa dei peggioramenti."
        )
        judgement = (
            "Nelle condizioni provate non emerge un beneficio sostanziale e affidabile "
            "dall'incremento automatico: i quattro ordinamenti non offrono un miglioramento "
            "medio consistente e i piccoli vantaggi, quando presenti, convivono con perdite "
            "rilevanti su singoli circuiti. "
        )
    else:
        interpretation = (
            "La qualità dei nuovi esempi e l'ordine con cui diventano disponibili possono "
            "influenzare le decisioni successive. Il confronto descrittivo non isola queste cause."
        )
        judgement = "Il vantaggio va valutato insieme alla variabilità fra ordinamenti e ai singoli peggioramenti. "
    limit = (
        f"Queste osservazioni riguardano questo campione di {count} circuiti e quattro sequenze "
        "degli stessi ingressi, non repliche indipendenti; non valgono necessariamente per ogni "
        "campione o test set. " + judgement +
        "Il beneficio dipende quindi troppo dalle condizioni del test e dall'ordinamento per "
        "essere dato per acquisito. Nell'uso quotidiano, la qualità della risposta può risentire "
        "della sequenza, spesso casuale dal punto di vista dell'utente, con cui vengono richieste le compilazioni."
    )
    return "\n\n".join([result, interpretation, limit])


def retrieval_usage(data, k):
    """Conta identità distinte e presenze dai recuperi vincolati ai commit originali."""
    if data.get("kind") != "measured_results":
        return {}

    def verified(path, expected):
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("Registro di recupero alterato: " + str(path))
        return json.loads(content)

    sources = data["sources"]
    usage = {}
    for order, item in data["orders"].items():
        if not item["rows"]:
            usage[order] = None
            continue
        suffix = f"/ordinamenti/{order}/campagne/{data['experiment_id']}/contratto.json"
        matches = [Path(p).parent for p in sources if p.endswith(suffix)]
        if len(matches) != 1:
            raise ValueError("Campagna di recupero non identificabile: " + order)
        base = matches[0]
        admitted, reused = {}, set()
        presences = total = decisions_using = 0
        for row in sorted(item["rows"], key=lambda r: r["position"]):
            folder = base / "circuiti" / f"{row['position']:03d}_{row['circuit_id']}"
            commit_path = folder / "commit.json"
            commit = verified(commit_path, sources[str(commit_path)])
            retrieval_path = folder / "retrieval.json"
            retrieval = verified(retrieval_path, commit["files"][retrieval_path.relative_to(base).as_posix()])
            records = retrieval["records"]
            if (retrieval["k"] != k or len(records) != k
                    or len({r["rag_id"] for r in records}) != k
                    or retrieval["memory_size"] != len(admitted)
                    or retrieval["memory_before_sha256"] != commit["memory_before_sha256"]):
                raise ValueError("Recupero incoerente con k o con la memoria: " + str(folder))
            incremental = [r for r in records if r["origin"] == "incremental"]
            if any(r["origin"] not in ("initial", "incremental") for r in records):
                raise ValueError("Origine degli esempi sconosciuta.")
            if len(incremental) != row["retrieved_incremental"]:
                raise ValueError("Conteggi diversi dai dati del report: " + str(folder))
            for record in incremental:
                position = admitted.get(record["rag_id"])
                if position != record["observation_position"] or position is None or position >= row["position"]:
                    raise ValueError("Esempio recuperato prima della sua ammissione: " + str(folder))
                reused.add(record["rag_id"])
            presences += len(incremental)
            total += len(records)
            decisions_using += bool(incremental)
            if commit["observation"] is not None:
                observation = commit["observation"]
                record = verified(base / observation["path"], observation["sha256"])
                if (record["record_id"] in admitted or record["position"] != row["position"]
                        or record["circuit_id"] != row["circuit_id"]
                        or record["source_sha256"] != row["source_sha256"]):
                    raise ValueError("Identità dell'esempio aggiunto incoerente: " + str(folder))
                admitted[record["record_id"]] = record["position"]
            if len(admitted) != row["memory_after"] or len(admitted) != commit["memory_after_count"]:
                raise ValueError("Numero di esempi aggiunti incoerente: " + str(folder))
        if decisions_using != item["summary"]["circuits_using_memory"]:
            raise ValueError("Numero di decisioni con memoria incoerente: " + order)
        usage[order] = {
            "added": len(admitted), "reused_distinct": len(reused),
            "incremental_presences": presences, "total_retrieved": total,
            "decisions_using_incremental": decisions_using,
            "decisions": len(item["rows"]),
        }
    return usage


def retrieval_table(data, labels, k):
    usage = retrieval_usage(data, k)
    if not any(usage.values()):
        return ""

    def ratio(numerator, denominator):
        if not denominator:
            return f"{numerator}/{denominator} (--)"
        return f"{numerator}/{denominator} ({number(100*numerator/denominator, 1)}\\%)"

    lines = [
        r"\section*{Riutilizzo degli esempi incrementali}",
        r"Un circuito aggiunto è riutilizzato se compare almeno una volta tra i $k$ esempi; "
        r"le presenze contano anche i recuperi ripetuti. "
        r"La tabella misura la presenza nel contesto dell'LLM, non il contributo allo score.",
        r"\begin{center}\begin{tabular}{lcc}\toprule",
        r"Ordinamento & Circuiti riutilizzati / aggiunti & Presenze incrementali / recuperi totali \\\midrule",
    ]
    for order, row in usage.items():
        values = (ratio(row["reused_distinct"], row["added"]) + " & "
                  + ratio(row["incremental_presences"], row["total_retrieved"])) if row else "-- & --"
        lines.append(escape(labels[order]) + " & " + values + r" \\")
    return "\n".join(lines + [r"\bottomrule\end{tabular}\end{center}"])


def render_tex(data, charts, benchmark, k):
    n = len(data["circuits"])
    comparison = charts.compare_orders(data)
    view = {**data, "comparisons": comparison}
    synthetic = data.get("kind") == "synthetic_verification"
    status = "DATI SINTETICI - SOLO VERIFICA SOFTWARE" if synthetic else "Confronto sui risultati osservati"
    control = ("Il controllo fisso riusa gli esiti della valutazione precedente."
               if k == 5 else "Il controllo fisso è una nuova esecuzione con $k=1$.")
    common = len(comparison["oracle_common_circuit_ids"])
    complete = sum(data["references"][cid]["exhaustive"] is True
                   for cid in comparison["oracle_common_circuit_ids"])
    partial = sum(data["references"][cid]["exhaustive"] is False
                  for cid in comparison["oracle_common_circuit_ids"])
    lines = [
        r"\documentclass[10pt,a4paper,landscape]{article}",
        r"\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage[italian]{babel}",
        r"\usepackage[margin=1.8cm]{geometry}\usepackage{booktabs,graphicx,pgfplots,hyperref,fancyhdr}",
        r"\pgfplotsset{compat=1.18}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}",
        r"\pagestyle{fancy}\fancyhf{}\lhead{" + benchmark + f" - RAG incrementale, k={k}" + r"}\rhead{Sintesi dei risultati}\cfoot{\thepage}",
        r"\setlength{\headheight}{14pt}\begin{document}",
        r"{\Large\bfseries RAG fisso e incrementale: " + benchmark + f", $k={k}$" + r"}\par",
        r"{\small " + status + r"}\par",
        f"Confrontiamo LLM + RAG con \\textbf{{Dataset fisso}} e lo stesso sistema con "
        f"\\textbf{{Dataset incrementale}} su \\textbf{{{n} circuiti Test {benchmark}}}. "
        "Il sistema incrementale viene valutato in quattro ordinamenti: Manifest, Inverso, "
        "Casuale 1 e Casuale 2 (seed 20261002 e 20261003). Ogni sequenza parte dagli stessi "
        "396 esempi train e aggiunge le nuove osservazioni solo dopo la compilazione del circuito.",
        f"Tutti usano Qwen3.5-4B Q8\\_0, temperatura zero e $k={k}$ esempi recuperati per decisione. "
        + control + " Lo score $S$ è la stima di expected fidelity su Target sintetici.",
        retrieval_table(data, charts.LABELS, k),
        r"\section*{Scarto dall'oracle}",
        r"$R$ è il massimo osservato nella griglia di cinque dispositivi, dodici configurazioni e tre seed; "
        r"può essere parziale e non rappresenta un massimo assoluto. Lo scarto è $R-S$: "
        r"più è basso, migliore è il risultato. Il grafico medio usa $100(R-S)$, espresso in \%.",
        r"\begin{center}" + charts.mean_gap_chart(view) + r"\end{center}",
        f"Medie sugli stessi {common}/{n} circuiti confrontabili in tutti i sistemi e con oracle: "
        f"{complete} riferimenti completi e {partial} parziali. "
        r"Nei grafici successivi sono mostrati tutti i circuiti, nello stesso ordine alfabetico; "
        r"la scala degli scarti è comune ai quattro ordinamenti. Un dato mancante non vale zero.",
    ]
    limits = charts.gap_limits(data)
    for order in data["orders"]:
        rows = charts.aligned_rows(data, order)
        for start in range(0, len(rows), 25):
            chunk = rows[start:start+25]
            lines += [
                r"\clearpage\section*{" + charts.LABELS[order] +
                f": scarto dall'oracle ({start+1}--{start+len(chunk)})" + "}",
                charts.circuit_chart(chunk, limits),
                r"\par\small \textcolor{red}{\textbf{Croce rossa: RAG fisso.}} "
                r"Punto blu: RAG incrementale; cerchio arancione: oracle. "
                r"Se il punto blu è a sinistra della croce rossa, l'incremento peggiora lo score.",
                r"La barra a destra misura $R-S$ in unità di score (0,10 = 10\%). "
                r"Verde: oracle completo; grigio e *: parziale; ?: oracle assente. "
                r"Un trattino indica uno scarto non disponibile; i valori negativi restano visibili.\normalsize",
            ]
    lines += [
        r"\par\begin{minipage}{\linewidth}",
        r"\section*{Conclusioni}",
        r"\begingroup\small\setlength{\parskip}{4pt}",
        conclusions(data),
        r"\par\endgroup\end{minipage}",
        r"\end{document}",
    ]
    return "\n\n".join(lines) + "\n"

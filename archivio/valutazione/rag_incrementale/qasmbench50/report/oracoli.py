"""Oracle e confronti: questo modulo viene importato soltanto dai report."""
from __future__ import annotations
import sys
from pathlib import Path
from itertools import combinations
import statistics
from comune import REPO, BASELINE, read, sha, finite

TOL = 1e-12
COLORS = ["blue!75!black", "orange!90!black", "green!45!black", "purple"]
LABELS = {"01_manifest": "Manifest", "02_inverso": "Inverso",
          "03_casuale_20261002": "Casuale 1", "04_casuale_20261003": "Casuale 2",
          "baseline": "RAG fisso"}


def load_reference(path, circuits):
    """Ricostruisce massimi e copertura dagli esiti originali verificati."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from archivio.valutazione.oracle_qasmbench.analizza import audit_oracle, audit_rag, build_rows
    path = Path(path).resolve()
    stored = read(path)
    if stored.get("synthetic") is not False:
        raise ValueError("Il report sperimentale richiede un oracle reale.")
    analysis = path.parents[2]
    if Path(stored["oracle_path"]).resolve() != analysis:
        raise ValueError("Provenienza del riepilogo oracle incoerente.")
    contract, summary, refs, pairs, sources, verified = audit_oracle(analysis)
    rag, execution, rag_sources = audit_rag(BASELINE.parents[1], contract["identity"])
    sources.update(rag_sources)
    rebuilt = build_rows(contract["identity"], refs, pairs, rag)
    if stored["rows"] != rebuilt or stored["oracle_identity"] != contract["identity_sha256"]:
        raise ValueError("Riepilogo oracle diverso dagli esiti originali.")
    expected = {r["circuit_id"]: r["source_sha256"] for r in circuits}
    if {r["circuit_id"]: r["source_sha256"] for r in rebuilt} != expected:
        raise ValueError("Oracle relativo a una selezione diversa dai 50 QASMBench.")
    if stored["model_sha256"] != execution["server"]["model_sha256"]:
        raise ValueError("Modello storico diverso da quello del confronto oracle.")
    sources[str(path)] = sha(path)
    for name in ("analizza.py", "oracle_core.py"):
        p = REPO / "archivio/valutazione/oracle_qasmbench" / name
        sources[str(p)] = sha(p)
    info = {"path": str(path), "sha256": sha(path), "identity": contract["identity_sha256"],
            "targets": contract["identity"]["catalog"]["target_sha256"],
            "versions": contract["identity"]["versions"], "results_verified": verified,
            "partial_references": sum(not r["exhaustive"] for r in rebuilt),
            "note": "Massimi e copertura ricalcolati; oracle letto soltanto dal report."}
    return {r["circuit_id"]: r for r in rebuilt}, info, sources


def average(values):
    values = [x for x in values if finite(x)]
    return statistics.mean(values) if values else None


def compare_orders(data):
    """Il riepilogo globale usa l'intersezione dei successi dei quattro ordini."""
    maps = {order: {r["circuit_id"]: r for r in item["rows"]} for order, item in data["orders"].items()}
    baseline = data["baseline"]
    references = data["references"]
    universe = [r["circuit_id"] for r in data["circuits"]]
    common = [cid for cid in universe if finite(baseline[cid].get("score")) and all(
        cid in rows and finite(rows[cid].get("score")) for rows in maps.values())]
    oracle_common = [cid for cid in common if finite(references.get(cid, {}).get("oracle_score"))]
    rows = []
    for order, items in {"baseline": baseline, **maps}.items():
        scores = [items[cid]["score"] for cid in common]
        gaps = [references[cid]["oracle_score"] - items[cid]["score"] for cid in oracle_common]
        rows.append({"order": order, "n_common": len(common), "mean_score": average(scores),
                     "n_oracle_common": len(oracle_common), "mean_gap": average(gaps),
                     "median_gap": statistics.median(gaps) if gaps else None,
                     "max_gap": max(gaps) if gaps else None,
                     "matches": sum(abs(g) <= TOL for g in gaps),
                     "above_reference": sum(g < -TOL for g in gaps),
                     "complete_references": sum(references[cid]["exhaustive"] is True for cid in oracle_common),
                     "partial_references": sum(references[cid]["exhaustive"] is False for cid in oracle_common)})
    pairwise = []
    for a, b in combinations(maps, 2):
        ids = [cid for cid in universe if cid in maps[a] and cid in maps[b]
               and finite(maps[a][cid].get("score")) and finite(maps[b][cid].get("score"))]
        differences = [maps[a][cid]["score"] - maps[b][cid]["score"] for cid in ids]
        pairwise.append({"order_a": a, "order_b": b, "paired": len(ids),
                         "mean_score_a_minus_b": average(differences),
                         "a_better": sum(v > TOL for v in differences),
                         "equal": sum(abs(v) <= TOL for v in differences),
                         "b_better": sum(v < -TOL for v in differences),
                         "circuit_ids": ids})
    return {"common_circuit_ids": common, "oracle_common_circuit_ids": oracle_common,
            "summary": rows, "pairwise": pairwise}


def aligned_rows(data, order):
    measured = {r["circuit_id"]: r for r in data["orders"][order]["rows"]}
    output = []
    for i, source in enumerate(data["circuits"], 1):
        cid = source["circuit_id"]
        outcome = measured.get(cid, {})
        reference = data["references"].get(cid, {})
        score = outcome.get("score")
        oracle = reference.get("oracle_score")
        output.append({"id": i, "circuit_id": cid, "size_group": source.get("size_group"),
                       "position": outcome.get("position"), "score": score,
                       "baseline_score": data["baseline"][cid].get("score"),
                       "oracle_score": oracle, "exhaustive": reference.get("exhaustive"),
                       "status": outcome.get("status", "not_started"),
                       "gap": oracle-score if finite(oracle) and finite(score) else None})
    return output


def gap_limits(data):
    values = [0.0]
    for order in data["orders"]:
        for row in aligned_rows(data, order):
            if finite(row["gap"]):
                values.append(row["gap"])
    low, high = min(values), max(values)
    span = max(high-low, .001)
    return low - (.06*span if low < 0 else 0), high + .06*span


def escape(text):
    return "".join({"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "$": r"\$",
                    "{": r"\{", "}": r"\}"}.get(c, c) for c in str(text))


def circuit_chart(rows, limits):
    """Stessa struttura del confronto oracle storico, con scala condivisa e segno."""
    low, high = limits
    score_x, score_w, gap_x, gap_w = 8.2, 10.0, 19.25, 6.15
    bottom = -.39*(len(rows)-1)-.24
    gap_position = lambda value: gap_x + gap_w*(value-low)/(high-low)
    lines = [r"\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]",
             r"\node[anchor=west,font=\bfseries] at (0,.85) {Circuito (* = oracle parziale; ? = assente)};",
             r"\node[anchor=west,font=\bfseries] at (8.2,.85) {Score: RAG e massimo osservato};",
             r"\node[anchor=west,font=\bfseries] at (19.25,.85) {Scarto $R-S$};"]
    for i, row in enumerate(rows):
        if i % 2 == 0:
            y = -.39*i
            lines.append(fr"\fill[gray!5] (0,{y-.18}) rectangle (25.65,{y+.18});")
    for val in [0, .2, .4, .6, .8, 1]:
        x = score_x + score_w*val
        lines += [fr"\draw[gray!25] ({x},.26)--({x},{bottom});",
                  fr"\node at ({x},.48) {{{val:.1f}}};"]
    ticks = sorted([value for value in (low + i*(high-low)/4 for i in range(5))
                    if abs(value) > .10*(high-low)] + [0.0])
    for val in ticks:
        x = gap_position(val)
        label = f"{val:.3g}"
        lines += [fr"\draw[gray!25] ({x},.26)--({x},{bottom});",
                  fr"\node[font=\scriptsize] at ({x},.48) {{{label}}};"]
    zero = gap_position(0)
    lines.append(fr"\draw[gray!65] ({zero},.26)--({zero},{bottom});")
    for i, row in enumerate(rows):
        y = -.39*i
        marker = "*" if row["exhaustive"] is False else ("?" if row["exhaustive"] is None else "")
        name = escape(row["circuit_id"].removeprefix("qasmbench_")) + marker
        lines.append(fr"\node[anchor=west] at (0,{y}) {{{row['id']:02d}\quad {name}}};")
        s, r, b = row["score"], row["oracle_score"], row["baseline_score"]
        if finite(s) and finite(r):
            lines.append(fr"\draw[gray,thick] ({score_x+score_w*s},{y})--({score_x+score_w*r},{y});")
        if finite(b):
            bx = score_x + score_w*b
            lines.append(fr"\draw[red,line width=1.2pt] ({bx-.085},{y-.085})--({bx+.085},{y+.085}) ({bx-.085},{y+.085})--({bx+.085},{y-.085});")
        if finite(r):
            lines.append(fr"\draw[orange!85!black,line width=.8pt] ({score_x+score_w*r},{y}) circle (2.2pt);")
        if finite(s):
            lines.append(fr"\fill[blue!75!black] ({score_x+score_w*s},{y}) circle (1.1pt);")
        else:
            label = "non eseguito" if row["status"] == "not_started" else escape(row["status"])
            lines.append(fr"\node[anchor=west,font=\scriptsize,text=gray!80!black] at (8.35,{y+.10}) {{{label}}};")
        if finite(row["gap"]):
            end = gap_position(row["gap"])
            color = "teal!75!black" if row["exhaustive"] is True else "gray!65"
            if abs(row["gap"]) > TOL:
                lines.append(fr"\fill[{color}] ({min(zero,end)},{y-.11}) rectangle ({max(zero,end)},{y+.11});")
            else:
                lines.append(fr"\fill[{color}] ({zero},{y}) circle (.8pt);")
        else:
            lines.append(fr"\node[text=gray] at ({zero},{y}) {{--}};")
    return "\n".join(lines + [r"\end{tikzpicture}"])


def mean_gap_chart(data):
    rows = data["comparisons"]["summary"]
    if not any(finite(r["mean_gap"]) for r in rows):
        return r"\emph{Nessun circuito confrontabile fra tutti gli ordini e l'oracle.}"
    values = [100*r["mean_gap"] for r in rows if finite(r["mean_gap"])]
    low, high = min([0.0] + values), max([0.0] + values)
    pad = max(high-low, .01)*.1
    ymin, ymax = low-pad if low < 0 else 0, high+pad
    lines = [r"\begin{tikzpicture}\begin{axis}[width=24cm,height=5cm,ybar,bar width=18pt,",
             f"ymin={ymin},ymax={ymax},bar shift=0pt,",
             r"ylabel={Scarto medio (\%)},xtick={1,2,3,4,5},",
             r"xticklabels={RAG fisso,Manifest,Inverso,Casuale 1,Casuale 2},",
             r"xmin=.5,xmax=5.5,grid=major,nodes near coords,point meta=y,every node near coord/.append style={font=\small},nodes near coords style={/pgf/number format/fixed,/pgf/number format/precision=3}]"]
    for i, (row, color) in enumerate(zip(rows, ["red!75"] + COLORS), 1):
        if finite(row["mean_gap"]):
            lines.append(fr"\addplot[fill={color},draw={color}] coordinates {{({i},{100*row['mean_gap']:.10f})}};")
    return "\n".join(lines + [r"\end{axis}\end{tikzpicture}"])


def gaps_chart(data):
    lines = [r"\begin{tikzpicture}\begin{axis}[width=24cm,height=5.8cm,grid=major,xmin=1,xmax=50,xtick={1,10,20,30,40,50},",
             r"xlabel={Indice comune del circuito (ordine alfabetico)},ylabel={Scarto $R-S$ (\%)},",
             r"unbounded coords=jump,legend style={at={(.5,0)},yshift=-32pt,anchor=north,legend columns=5,font=\scriptsize}]"]
    series = []
    first = next(iter(data["orders"]))
    series.append(("baseline", "gray!70", [(r["id"], r["oracle_score"]-r["baseline_score"]
                    if finite(r["oracle_score"]) and finite(r["baseline_score"]) else None)
                    for r in aligned_rows(data, first)]))
    for (order, _), color in zip(data["orders"].items(), COLORS):
        series.append((order, color, [(r["id"], r["gap"]) for r in aligned_rows(data, order)]))
    for order, color, points in series:
        if not any(finite(y) for _, y in points):
            continue
        coords = " ".join(f"({x},{100*y:.10f})" if finite(y) else f"({x},nan)" for x,y in points)
        style = "dashed" if order == "baseline" else "solid"
        lines += [fr"\addplot[mark=*,mark size=.7pt,{style},color={color}] coordinates {{{coords}}};",
                  fr"\addlegendentry{{{LABELS[order]}}}"]
    return "\n".join(lines + [r"\end{axis}\end{tikzpicture}"])


def figure_specs(data):
    figures = [("confronto_ordinamenti", mean_gap_chart(data)),
               ("scarti_ordinamenti", gaps_chart(data))]
    limits = gap_limits(data)
    for order in data["orders"]:
        rows = aligned_rows(data, order)
        for start in range(0, len(rows), 25):
            figures.append((f"oracle_{order}_{start//25+1}", circuit_chart(rows[start:start+25], limits)))
    return figures

def appendix_tex(data):
    fmt = lambda v: "--" if not finite(v) else f"{v:.6f}"
    comparison = data["comparisons"]
    lines = [r"\clearpage\section*{Confronto fra i quattro ordinamenti}",
             "Le medie seguenti usano gli stessi circuiti riusciti in tutti i quattro ordini e nel controllo storico. "
             "Per gli scarti si richiede anche un riferimento oracle. Un valore inferiore di $R-S$ indica uno score maggiore.",
             f"Circuiti comuni: {len(comparison['common_circuit_ids'])}/50; con oracle: {len(comparison['oracle_common_circuit_ids'])}/50.",
             r"\begin{center}\small\begin{tabular}{lrrrrrrr}\toprule",
             r"Sistema & $n$ score & Score medio & $n$ oracle & Scarto medio & Scarto mediano & Scarto massimo & Pari a $R$\\\midrule"]
    for row in comparison["summary"]:
        lines.append(" & ".join([LABELS[row["order"]], str(row["n_common"]), fmt(row["mean_score"]),
                     str(row["n_oracle_common"]), fmt(row["mean_gap"]), fmt(row["median_gap"]),
                     fmt(row["max_gap"]), str(row["matches"])]) + r" \\")
    lines += [r"\bottomrule\end{tabular}\end{center}", mean_gap_chart(data),
              r"\par Gli ordini sono quattro sequenze degli stessi cinquanta circuiti, non 200 osservazioni indipendenti. "
              r"Il confronto con RAG fisso riutilizza gli esiti storici; non certifica un effetto causale della sola memoria.",
              r"\clearpage\section*{Scarti sugli stessi circuiti}",
              gaps_chart(data),
              r"\par L'indice identifica sempre lo stesso circuito nei grafici e nelle tabelle CSV. "
              r"I dati mancanti interrompono le linee; non vengono rappresentati come zero.",
              r"\begin{center}\small\begin{tabular}{llrrrrr}\toprule",
              r"Ordine A & Ordine B & Coppie & Media $S_A-S_B$ & A migliore & Pari & B migliore\\\midrule"]
    for row in comparison["pairwise"]:
        lines.append(" & ".join([LABELS[row["order_a"]], LABELS[row["order_b"]], str(row["paired"]),
                    fmt(row["mean_score_a_minus_b"]), str(row["a_better"]), str(row["equal"]),
                    str(row["b_better"])]) + r" \\")
    lines += [r"\bottomrule\end{tabular}\end{center}",
              r"Ogni confronto A/B usa i successi comuni alla coppia indicata, con il proprio denominatore. "
              r"La tolleranza della parità è $10^{-12}$; una differenza positiva favorisce A."]
    limits = gap_limits(data)
    for order in data["orders"]:
        rows = aligned_rows(data, order)
        for start in range(0, len(rows), 25):
            chunk = rows[start:start+25]
            lines += [r"\clearpage\section*{" + LABELS[order] + f": distanza dall'oracle ({start+1}--{start+len(chunk)})" + "}",
                      circuit_chart(chunk, limits),
                      r"\par\small Punto blu: score incrementale; cerchio arancione: oracle; croce rossa: RAG fisso. "
                      r"La barra misura $R-S$ in unità di score. Verde: oracle completo; grigio e asterisco: parziale. "
                      r"La scala degli scarti è la stessa per tutti gli ordini. I valori negativi restano visibili.",
                      r"Lo score mancante è indicato con lo stato del tentativo; un trattino nella colonna dello scarto "
                      r"non significa parità. I circuiti seguono lo stesso ordine alfabetico, indipendente dall'ordine di esecuzione.\normalsize"]
    return "\n".join(lines)


def figure_title(name):
    if name.startswith("oracle_"):
        order, page = name.removeprefix("oracle_").rsplit("_", 1)
        return LABELS[order] + " - distanza dall'oracle, parte " + page
    return {"confronto_ordinamenti": "Scarto medio sui circuiti comuni",
            "scarti_ordinamenti": "Scarto per circuito nei quattro ordinamenti",
            "qualita": "Differenza cumulativa rispetto a RAG fisso",
            "memoria": "Crescita della memoria incrementale"}.get(name, name)

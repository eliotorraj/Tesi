'Oracle and comparisons: imported only by reports.'
from __future__ import annotations
import sys
from pathlib import Path
from itertools import combinations
import statistics
from comune import REPO, HISTORICAL_BASELINE as BASELINE, read, sha, finite, digest

TOL = 1e-12
COLORS = ["blue!75!black", "orange!90!black", "green!45!black", "purple"]
LABELS = {"01_manifest": "Manifest", "02_inverso": 'Reverse',
          "03_casuale_20261002": 'Random 1', "04_casuale_20261003": 'Random 2',
          "baseline": 'Fixed RAG k=1'}


def _audit_reference(analysis):
    'Reuse the existing MQT Bench verification without changing sources.'
    import subprocess
    import tempfile
    analyzer = REPO / "archivio/valutazione/oracle_test/confronto_llm_rag_k5/analizza.py"
    with tempfile.TemporaryDirectory(prefix="mqtbench_report_audit_") as tmp:
        output = Path(tmp)
        process = subprocess.run(
            [sys.executable, "-B", str(analyzer), "--oracle", str(analysis), "--output", str(output)],
            capture_output=True, text=True, timeout=180)
        if process.returncode:
            raise ValueError('MQT Bench oracle verification failed: ' + process.stderr[-2000:])
        return read(output / "dati.json"), read(output / "provenienza.json")


def load_reference(path, circuits):
    'Verify the 90-circuit MQT Bench reference from original outcomes.'
    path = Path(path).resolve()
    stored = read(path)
    if stored.get("synthetic", False):
        raise ValueError('The experimental report requires a real oracle.')
    if Path(stored["rag_path"]).resolve() != BASELINE.resolve():
        raise ValueError('The oracle source must come from the verified historical MQT Bench comparison.')
    analysis = Path(stored["oracle_path"]).resolve()
    rebuilt, audit = _audit_reference(analysis)
    for field in ("rows", "summary", "oracle_summary", "oracle_identity",
                  "system_contract", "oracle_versions", "model_sha256"):
        if stored.get(field) != rebuilt.get(field):
            raise ValueError('Oracle summary differs from original outcomes: ' + field)
    expected = {r["circuit_id"]: r["source_sha256"] for r in circuits}
    rows = rebuilt["rows"]
    if len(rows) != 90 or len(expected) != 90 or {
            r["circuit_id"]: r["source_sha256"] for r in rows} != expected:
        raise ValueError('Oracle selection differs from the 90 MQT Bench circuits.')
    root = analysis.parents[1]
    contract = read(root / "contratto.json")
    if digest(contract["identity"]) != contract["identity_sha256"]:
        raise ValueError('Invalid MQT Bench oracle identity.')
    sources = dict(audit["source_sha256"])
    result_manifest = Path(audit["oracle_result_hashes_manifest"]).resolve()
    if result_manifest != analysis / "provenienza.json":
        raise ValueError('Unexpected oracle-verification manifest.')
    for relative, checksum in read(result_manifest).items():
        result = (root / relative).resolve()
        if not result.is_relative_to(root):
            raise ValueError('Oracle outcome is outside the campaign.')
        sources[str(result)] = checksum
    sources[str(path)] = sha(path)
    analyzer = REPO / "archivio/valutazione/oracle_test/confronto_llm_rag_k5/analizza.py"
    sources[str(analyzer)] = sha(analyzer)
    info = {
        "path": str(path), "sha256": sha(path), "identity": contract["identity_sha256"],
        "targets": contract["identity"]["catalog"]["target_sha256"],
        "versions": contract["identity"]["versions"],
        "results_verified": audit["oracle_results_verified"],
        "partial_references": sum(not r["exhaustive"] for r in rows),
        "note": 'Maxima and coverage recomputed from MQT Bench outcomes; oracle read by the report only.'}
    return {r["circuit_id"]: r for r in rows}, info, sources


def average(values):
    values = [x for x in values if finite(x)]
    return statistics.mean(values) if values else None


def compare_orders(data):
    'The global summary uses the intersection of successes across four orderings.'
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
        output.append({"id": i, "circuit_id": cid, "num_qubits": source.get("num_qubits"),
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
    'Same layout as the historical oracle comparison, with a shared signed scale.'
    low, high = limits
    score_x, score_w, gap_x, gap_w = 8.2, 10.0, 19.25, 6.15
    bottom = -.39*(len(rows)-1)-.24
    gap_position = lambda value: gap_x + gap_w*(value-low)/(high-low)
    lines = [r"\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]",
             '\\node[anchor=west,font=\\bfseries] at (0,.85) {Circuit (* = partial oracle; ? = missing)};',
             '\\node[anchor=west,font=\\bfseries] at (8.2,.85) {Score: RAG and observed maximum};',
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
        name = escape(row["circuit_id"]) + marker
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
            label = 'not run' if row["status"] == "not_started" else escape(row["status"])
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
        return '\\emph{No circuit is comparable across all orderings and the oracle.}'
    values = [100*r["mean_gap"] for r in rows if finite(r["mean_gap"])]
    low, high = min([0.0] + values), max([0.0] + values)
    pad = max(high-low, .01)*.1
    ymin, ymax = low-pad if low < 0 else 0, high+pad
    lines = [r"\begin{tikzpicture}\begin{axis}[width=24cm,height=5cm,ybar,bar width=18pt,",
             f"ymin={ymin},ymax={ymax},bar shift=0pt,",
             'ylabel={Mean gap (\\%)},xtick={1,2,3,4,5},',
             'xticklabels={Fixed RAG k=1,Manifest,Reverse,Random 1,Random 2},',
             r"xmin=.5,xmax=5.5,grid=major,nodes near coords,point meta=y,every node near coord/.append style={font=\small},nodes near coords style={/pgf/number format/fixed,/pgf/number format/precision=3}]"]
    for i, (row, color) in enumerate(zip(rows, ["red!75"] + COLORS), 1):
        if finite(row["mean_gap"]):
            lines.append(fr"\addplot[fill={color},draw={color}] coordinates {{({i},{100*row['mean_gap']:.10f})}};")
    return "\n".join(lines + [r"\end{axis}\end{tikzpicture}"])


def gaps_chart(data):
    lines = [r"\begin{tikzpicture}\begin{axis}[width=24cm,height=5.8cm,grid=major,xmin=1,xmax=90,xtick={1,10,20,30,40,50,60,70,80,90},",
             'xlabel={Shared circuit index (alphabetical order)},ylabel={Gap $R-S$ (\\%)},',
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
    lines = ['\\clearpage\\section*{Comparison of the four orderings}',
             'The following means use the same circuits successful in all four orderings and the fixed k=1 control. Gaps also require an oracle reference. Lower $R-S$ means a higher score.',
             f"Shared circuits: {len(comparison['common_circuit_ids'])}/90; with oracle: {len(comparison['oracle_common_circuit_ids'])}/90.",
             r"\begin{center}\small\begin{tabular}{lrrrrrrr}\toprule",
             'System & Score $n$ & Mean score & Oracle $n$ & Mean gap & Median gap & Maximum gap & Equal to $R$\\\\\\midrule']
    for row in comparison["summary"]:
        lines.append(" & ".join([LABELS[row["order"]], str(row["n_common"]), fmt(row["mean_score"]),
                     str(row["n_oracle_common"]), fmt(row["mean_gap"]), fmt(row["median_gap"]),
                     fmt(row["max_gap"]), str(row["matches"])]) + r" \\")
    lines += [r"\bottomrule\end{tabular}\end{center}", mean_gap_chart(data),
              '\\par The four orderings are sequences of the same ninety circuits, not 360 independent observations. The control is a new fixed-RAG k=1 run; the comparison does not establish a causal effect of memory alone.',
              '\\clearpage\\section*{Gaps on the same circuits}',
              gaps_chart(data),
              '\\par The index identifies the same circuit in plots and CSV tables. Missing data interrupts lines rather than appearing as zero.',
              r"\begin{center}\small\begin{tabular}{llrrrrr}\toprule",
              'Order A & Order B & Pairs & Mean $S_A-S_B$ & A better & Tied & B better\\\\\\midrule']
    for row in comparison["pairwise"]:
        lines.append(" & ".join([LABELS[row["order_a"]], LABELS[row["order_b"]], str(row["paired"]),
                    fmt(row["mean_score_a_minus_b"]), str(row["a_better"]), str(row["equal"]),
                    str(row["b_better"])]) + r" \\")
    lines += [r"\bottomrule\end{tabular}\end{center}",
              'Each A/B comparison uses its own common successes and denominator. Tie tolerance is $10^{-12}$; a positive difference favors A.']
    limits = gap_limits(data)
    for order in data["orders"]:
        rows = aligned_rows(data, order)
        for start in range(0, len(rows), 25):
            chunk = rows[start:start+25]
            lines += [r"\clearpage\section*{" + LABELS[order] + f': distance from the oracle ({start + 1}--{start + len(chunk)})' + "}",
                      circuit_chart(chunk, limits),
                      '\\par\\small Blue point: incremental score; orange circle: oracle; red cross: fixed RAG k=1. Bars show $R-S$ in score units. Green: complete oracle; gray/asterisk: partial. Gap scales match across orderings. Negative values remain visible.',
                      'Missing scores are identified by attempt status; a dash in the gap column is not a tie. Circuits share alphabetical order independently of execution order.\\normalsize']
    return "\n".join(lines)


def figure_title(name):
    if name.startswith("oracle_"):
        order, page = name.removeprefix("oracle_").rsplit("_", 1)
        return LABELS[order] + ' - distance from the oracle, part ' + page
    return {"confronto_ordinamenti": 'Mean gap on shared circuits',
            "scarti_ordinamenti": 'Per-circuit gap across four orderings',
            "qualita": 'Cumulative difference from fixed RAG k=1',
            "memoria": 'Incremental memory growth'}.get(name, name)

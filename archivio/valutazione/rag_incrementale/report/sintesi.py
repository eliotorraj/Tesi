'Shared concise presentation for incremental reports using collected measurements only.'
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
    'Derive quantitative observations from pairs without pooling replicates.'
    if data.get("kind") != "measured_results":
        return 'Synthetic data checks report structure and supports no experimental conclusions.'
    count = len(data["circuits"])
    if not data["orders"] or any(item["status"] != "completed" for item in data["orders"].values()):
        return 'Incomplete campaign: plots describe available measurements only; no conclusion is drawn across the four orderings.'
    paired = []
    means = []
    for item in data["orders"].values():
        rows = [r for r in item["rows"] if finite(r.get("score")) and finite(r.get("baseline_score"))]
        paired.extend(rows)
        if rows:
            means.append(statistics.mean(r["score"] - r["baseline_score"] for r in rows))
    if not paired:
        return 'No pairs are comparable with fixed RAG.'
    better = sum(r["score"] - r["baseline_score"] > TOL for r in paired)
    worse = sum(r["score"] - r["baseline_score"] < -TOL for r in paired)
    equal = len(paired) - better - worse
    negative = [x for x in means if x < -TOL]
    positive = [x for x in means if x > TOL]
    if len(negative) == len(data["orders"]):
        result = (f'All four orderings have lower mean scores than fixed RAG: loss ranges from {number(100 * min((-x for x in negative)))} to {number(100 * max((-x for x in negative)))}\\%.')
    else:
        result = (f"Orderings with lower mean scores than fixed RAG: {len(negative)} out of {len(data['orders'])}. ")
        if positive:
            result += (f'The best mean gain is {number(100 * max(positive))}\\%'
                       + (f', against a largest mean loss of {number(-100 * min(negative))}\\%.'
                          if negative else "."))
    result += (f' On {len(paired)} circuit/order comparisons, {equal} results remain unchanged, {worse} worsen and {better} improve.')
    losses = [r for r in paired if r["baseline_score"] > 0 and r["score"] < r["baseline_score"] - TOL]
    if losses:
        worst = max(losses, key=lambda r: r["baseline_score"] - r["score"])
        loss = worst["baseline_score"] - worst["score"]
        result += (f" The largest individual loss is {number(100 * loss, 2)}\\%, equivalent to {number(100 * loss / worst['baseline_score'], 1)}\\% of the fixed-RAG score.")
    if len(negative) > len(positive):
        interpretation = (
            'One plausible explanation is that LLM + RAG does not always obtain the best compilation. Automatically adding examples from suboptimal choices may therefore reduce the quality of retrieved information relative to the original fixed Dataset, even while preserving the original examples. Results are consistent with this hypothesis but do not establish it as the sole cause of degradation.'
        )
        judgement = (
            'Under the tested conditions, automatic growth shows no substantial, reliable benefit: the four orderings do not consistently improve mean scores, and small gains, where present, coexist with substantial losses on individual circuits. '
        )
    else:
        interpretation = (
            'New-example quality and arrival order may affect later decisions. This descriptive comparison does not isolate those causes.'
        )
        judgement = 'Benefits must be assessed alongside variation between orderings and individual losses. '
    limit = (
        f'These observations concern this sample of {count} circuits and four sequences of the same inputs, not independent replicates; they need not hold for every sample or test set. ' + judgement +
        'Benefits therefore depend too much on Test conditions and ordering to be assumed. In everyday use, response quality may depend on the compilation-request sequence, which can appear arbitrary to the user.'
    )
    return "\n\n".join([result, interpretation, limit])


def retrieval_usage(data, k):
    'Count distinct identities and occurrences from retrieval bound to original commits.'
    if data.get("kind") != "measured_results":
        return {}

    def verified(path, expected):
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('Retrieval record changed: ' + str(path))
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
            raise ValueError('Cannot identify retrieval campaign: ' + order)
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
                raise ValueError('Retrieval is inconsistent with k or memory: ' + str(folder))
            incremental = [r for r in records if r["origin"] == "incremental"]
            if any(r["origin"] not in ("initial", "incremental") for r in records):
                raise ValueError('Unknown example origin.')
            if len(incremental) != row["retrieved_incremental"]:
                raise ValueError('Counts differ from report data: ' + str(folder))
            for record in incremental:
                position = admitted.get(record["rag_id"])
                if position != record["observation_position"] or position is None or position >= row["position"]:
                    raise ValueError('Example retrieved before admission: ' + str(folder))
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
                    raise ValueError('Inconsistent added-example identity: ' + str(folder))
                admitted[record["record_id"]] = record["position"]
            if len(admitted) != row["memory_after"] or len(admitted) != commit["memory_after_count"]:
                raise ValueError('Inconsistent number of added examples: ' + str(folder))
        if decisions_using != item["summary"]["circuits_using_memory"]:
            raise ValueError('Inconsistent count of decisions using memory: ' + order)
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
        '\\section*{Reuse of incremental examples}',
        'An added circuit is reused if it appears at least once among the $k$ examples; occurrences also count repeated retrieval. The table measures presence in the LLM context, not contribution to the score.',
        r"\begin{center}\begin{tabular}{lcc}\toprule",
        'Ordering & Circuits reused / added & Incremental appearances / total retrievals \\\\\\midrule',
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
    status = 'SYNTHETIC DATA - SOFTWARE CHECK ONLY' if synthetic else 'Comparison of observed results'
    control = ('The fixed control reuses outcomes from the previous evaluation.'
               if k == 5 else 'The fixed control is a new run with $k=1$.')
    common = len(comparison["oracle_common_circuit_ids"])
    complete = sum(data["references"][cid]["exhaustive"] is True
                   for cid in comparison["oracle_common_circuit_ids"])
    partial = sum(data["references"][cid]["exhaustive"] is False
                  for cid in comparison["oracle_common_circuit_ids"])
    lines = [
        r"\documentclass[10pt,a4paper,landscape]{article}",
        '\\usepackage[utf8]{inputenc}\\usepackage[T1]{fontenc}\\usepackage[english]{babel}',
        r"\usepackage[margin=1.8cm]{geometry}\usepackage{booktabs,graphicx,pgfplots,hyperref,fancyhdr}",
        r"\pgfplotsset{compat=1.18}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}",
        r"\pagestyle{fancy}\fancyhf{}\lhead{" + benchmark + f' - Incremental RAG, k={k}' + '}\\rhead{Result summary}\\cfoot{\\thepage}',
        r"\setlength{\headheight}{14pt}\begin{document}",
        '{\\Large\\bfseries Fixed and incremental RAG: ' + benchmark + f", $k={k}$" + r"}\par",
        r"{\small " + status + r"}\par",
        f'We compare LLM + RAG with a \\textbf{{fixed Dataset}} against the same system with an \\textbf{{incremental Dataset}} on \\textbf{{{n} Test circuits from {benchmark}}}. The incremental system uses four orderings: Manifest, Reverse, Random 1 and Random 2 (seeds 20261002 and 20261003). Each sequence starts from the same 396 train examples and adds observations only after compiling the circuit.',
        f'All use Qwen3.5-4B Q8\\_0, temperature zero and $k={k}$ retrieved examples per decision. '
        + control + ' Score $S$ estimates expected fidelity on synthetic Targets.',
        retrieval_table(data, charts.LABELS, k),
        '\\section*{Gap from the oracle}',
        '$R$ is the observed maximum over five devices, twelve configurations and three seeds; it may be partial and is not an absolute maximum. Gap is $R-S$: lower is better. The mean plot uses $100(R-S)$, expressed in \\%.',
        r"\begin{center}" + charts.mean_gap_chart(view) + r"\end{center}",
        f'Means over the same {common}/{n} circuits comparable across all systems and with an oracle: {complete} complete references and {partial} partial. Subsequent plots show every circuit in the same alphabetical order; gap scales are shared across all four orderings. Missing data is not zero.',
    ]
    limits = charts.gap_limits(data)
    for order in data["orders"]:
        rows = charts.aligned_rows(data, order)
        for start in range(0, len(rows), 25):
            chunk = rows[start:start+25]
            lines += [
                r"\clearpage\section*{" + charts.LABELS[order] +
                f': gap from the oracle ({start + 1}--{start + len(chunk)})' + "}",
                charts.circuit_chart(chunk, limits),
                '\\par\\small \\textcolor{red}{\\textbf{Red cross: fixed RAG.}} Blue point: incremental RAG; orange circle: oracle. A blue point left of the red cross means incrementing reduced the score.',
                'The right-hand bar shows $R-S$ in score units (0.10 = 10\\%). Green: complete oracle; gray/*: partial; ?: absent. A dash means an unavailable gap; negative values remain visible.\\normalsize',
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

'Retrieval validation on 88 cases, without an LLM or compilations.'
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
import time
from uuid import uuid4
from common import ROOT, ARCHIVE, SOURCE, STUDY, EVALUATION, digest, read, save, sha, source_path, now
sys.path.insert(0, str(ROOT))
from dag_wl_core import SUPPORTED_H, REPRESENTATION, prepare_index, descriptor, request_context, rank

BASE = EVALUATION/"validation_dag_wl"
AGGREGATES = ARCHIVE/"datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/expected_fidelity/full/global/qiskit_configuration_aggregates.jsonl"
CANDIDATES = ("manhattan",) + tuple(f"wl_h{h}" for h in SUPPORTED_H)
DEFAULT_RUN_ID = "wl_v3"
DESIGN = {
    "revision": "wl-validation-v3-h30", "split": "validation", "expected": 88,
    "candidates": list(CANDIDATES), "k": 5, "representation": REPRESENTATION,
    "primary": "regret of rank-1 pair of first retrieved example; success coverage reported separately",
    "common_denominator": "same circuits with observable top1 score in all 31 candidates",
    "secondary": "best observed score among union of displayed top3 pairs/ties across five examples",
    "reference": "best median of compatible pairs with seeds 0,1,2 all successful",
    "missing": "null, never zero; incomplete matrices and unobservable transfers counted",
    "selection": "manual after inspecting coverage, mean/median regret on common cases and cost; h smaller if equivalent",
    "extension": "h=7..30 added after inspection of wl_v2; adaptive validation, same 88 circuits",
    "parent_report_sha256": "1439c7376b6f7d7914c996b5ce645fbf019a9d2462560bf3caa390af42959beb",
    "llm_calls": 0, "new_compilations": 0,
}

def code_identity():
    from common import code_files
    result = code_files()
    for p in sorted(BASE.glob("*.py")):
        result["validation_dag_wl/"+p.name] = sha(p)
    return result

def validation_rows():
    if sha(SOURCE) != "c599eab17b6f64528067016e3d175cbfed597334f779ef8e515cf8787a788f53":
        raise ValueError('Source manifest changed.')
    rows = sorted((r for r in read(SOURCE)["circuits"] if r["split"] == "validation"), key=lambda r:r["circuit_id"])
    if len(rows) != 88 or len({r["circuit_id"] for r in rows}) != 88:
        raise ValueError('Exactly 88 validation circuits expected.')
    for r in rows:
        if sha(source_path(r)) != r["source_sha256"]:
            raise ValueError('Validation QASM changed.')
    return rows

def aggregate_hash():
    key = str(AGGREGATES.relative_to(ARCHIVE))
    frozen = read(STUDY/"frozen_study.json")
    expected = {**frozen["input_hashes"], **frozen["evaluation_input_hashes"]}[key]
    if sha(AGGREGATES) != expected:
        raise ValueError('Aggregates differ from the frozen source.')
    return expected

def load_scores(rows):
    'Filter the split before using scores; no test result is consulted.'
    known = {r["circuit_id"]:r for r in rows}
    tables = {cid:{} for cid in known}
    with AGGREGATES.open() as handle:
        for line in handle:
            r = json.loads(line)
            if r["split"] != "validation":
                continue
            c = r["circuit"]
            if c["circuit_id"] not in known or c["source_sha256"] != known[c["circuit_id"]]["source_sha256"]:
                raise ValueError('Inconsistent validation aggregate provenance.')
            key = (r["device"]["device_id"], r["configuration"]["config_id"])
            table = tables[c["circuit_id"]]
            if key in table:
                raise ValueError('Duplicate validation pair.')
            valid = (r["eligible_for_ranking"] and r["seeds"]["successful"] == [0,1,2]
                     and r["attempts"]["success_count"] == 3)
            score = r["score_statistics"]["median"] if valid else None
            if score is not None and not 0 <= score <= 1:
                raise ValueError('Score outside the allowed range.')
            table[key] = {"score": score, "summary_id": r["summary_id"],
                          "successful_seeds": r["seeds"]["successful"],
                          "timeout_count": r["attempts"]["timeout_count"],
                          "failure_count": r["attempts"]["failure_count"]}
    if any(not t for t in tables.values()):
        raise ValueError('Validation matrix missing.')
    return tables

def transfer_metrics(chosen, table, devices):
    from prototype.quantum_assistant.adapters.rag_dataset import as_example
    visible = [as_example(r, 0).prompt_input["label"] for r in chosen]
    def primary_pair(label):
        first = label["top_configurations"][0]
        return (first["device_id"], first["config_id"])
    first = primary_pair(visible[0])
    pairs = set()
    for label in visible:
        for c in label["top_configurations"][:3]:
            pairs.add((c["device_id"], c["config_id"]))
            for config in c.get("tied_score_config_ids", []):
                pairs.add((c["device_id"], config))
    eligible = {k:v["score"] for k,v in table.items() if k[0] in devices and v["score"] is not None}
    if not eligible:
        raise ValueError('No observed reference available.')
    reference = max(eligible.values())
    transferred = eligible.get(first)
    measured = [eligible[p] for p in sorted(pairs) if p in eligible]
    first_five = [eligible.get(primary_pair(label)) for label in visible]
    return {
        "reference": reference, "reference_is_exhaustive": all(v["score"] is not None for k,v in table.items() if k[0] in devices),
        "top1_pair": list(first), "top1_score": transferred,
        "top1_regret": reference-transferred if transferred is not None else None,
        "top1_observation": table.get(first),
        "top5_first_pair_scores": first_five,
        "displayed_pairs": [list(p) for p in sorted(pairs)],
        "displayed_pairs_count": len(pairs), "displayed_pairs_observed": len(measured),
        "best_displayed_score_observed": max(measured) if measured else None,
        "best_displayed_regret_observed": reference-max(measured) if measured else None,
        "best_displayed_is_optimistic_diagnostic_not_llm_score": True,
    }

def describe(values):
    values = [v for v in values if v is not None]
    return {"n":len(values), "mean":statistics.mean(values) if values else None,
            "median":statistics.median(values) if values else None}

def summarize(records):
    common = [r for r in records if r["status"] == "success" and all(
        r["methods"][m]["transfer"]["top1_regret"] is not None for m in CANDIDATES)]
    methods = {}
    for m in CANDIDATES:
        valid = [r["methods"][m] for r in records if r["status"] == "success"]
        methods[m] = {
            "circuits_retrieved":len(valid),
            "top1_score":describe([x["transfer"]["top1_score"] for x in valid]),
            "top1_regret":describe([x["transfer"]["top1_regret"] for x in valid]),
            "top1_regret_common":describe([r["methods"][m]["transfer"]["top1_regret"] for r in common]),
            "best_displayed_regret_observed":describe([x["transfer"]["best_displayed_regret_observed"] for x in valid]),
            "ranking_seconds":describe([x["ranking_seconds"] for x in valid]),
            "retrieved_size_ratio":describe([ratio for x in valid for ratio in x["retrieved_size_ratios"]]),
        }
    return {"expected":88, "recorded":len(records), "successes":sum(r["status"]=="success" for r in records),
            "failures":[r["circuit_id"] for r in records if r["status"]!="success"],
            "common_top1_circuits":[r["circuit_id"] for r in common],
            "incomplete_validation_matrices":sum(not r["methods"]["manhattan"]["transfer"]["reference_is_exhaustive"] for r in records if r["status"]=="success"),
            "methods":methods, "selected_h":None, "selection_pending":True,
            "note":'Indirect retrieval measurement, not an LLM evaluation. Medians over historical seeds 0,1,2.'}

def validation_check():
    from gates import software_targets, rag_integrity, selection_v2
    checks = {}
    for name, fn in (("selection",selection_v2),("software",software_targets),
                     ("train",rag_integrity),("validation",lambda:len(validation_rows())),
                     ("aggregates",aggregate_hash)):
        try:
            checks[name] = {"ok":True,"details":fn()}
        except Exception as exc:
            checks[name] = {"ok":False,"error":str(exc)}
    return {"ready":all(v["ok"] for v in checks.values()),"checks":checks}

def load_selection(path):
    'Used by both Tests: no implicit h and no automatic freezing.'
    value = read(path)
    core = {k:v for k,v in value.items() if k != "sha256"}
    if digest(core) != value.get("sha256") or (type(value["h"]) is not int or value["h"] not in SUPPORTED_H) or value["k"] != 5:
        raise ValueError('Invalid WL selection.')
    if value["design"] != DESIGN or value["code"] != code_identity():
        raise ValueError('Code or representation changed after WL selection.')
    report_path = BASE/"esecuzioni"/value["run_id"]/"riepilogo.json"
    if sha(report_path) != value["validation_report_sha256"]:
        raise ValueError('Validation result differs from the selection.')
    report = read(report_path)
    if report["successes"] != 88 or report["recorded"] != 88:
        raise ValueError('Selection requires 88 successful validation cases.')
    run = report_path.parent
    contract = read(run/"contratto.json")
    if sha(run/"contratto.json") != report["contract_sha256"] or contract["design"] != DESIGN or contract["code"] != code_identity():
        raise ValueError('Validation contract changed.')
    for relative, expected in report["record_hashes"].items():
        if sha(run/relative) != expected:
            raise ValueError('Validation outcomes changed.')
    if contract["aggregate_sha256"] != aggregate_hash() or contract["source_sha256"] != sha(SOURCE):
        raise ValueError('Validation sources changed.')
    return value

def cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--verifica", action="store_true")
    group.add_argument("--esegui", action="store_true")
    group.add_argument("--congela", action="store_true", help='Only after discussing the results')
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--h", type=int, choices=SUPPORTED_H)
    ap.add_argument("--motivazione")
    args = ap.parse_args(argv)
    import re
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.run_id):
        ap.error('run-id must contain only letters, numbers, _ and -.')
    run = BASE/"esecuzioni"/args.run_id
    if args.congela:
        if args.h is None or not args.motivazione:
            ap.error('--congela requires --h and --motivazione.')
        report = read(run/"riepilogo.json")
        if report["successes"] != 88 or report["recorded"] != 88:
            raise ValueError('Complete all 88 cases without technical errors.')
        contract = read(run/"contratto.json")
        if contract["code"] != code_identity() or contract["design"] != DESIGN:
            raise ValueError('Code changed since validation.')
        for relative, expected in report["record_hashes"].items():
            if sha(run/relative) != expected:
                raise ValueError('Validation record changed.')
        value = {"h":args.h,"k":5,"run_id":args.run_id,"at":now(),"motivation":args.motivazione,
                 "design":DESIGN,"code":code_identity(),"validation_report_sha256":sha(run/"riepilogo.json")}
        value["sha256"] = digest(value)
        destination = BASE/"selezioni"/args.run_id/f"wl_h{args.h}.json"
        save(destination, value)
        print('Frozen configuration: '+str(destination))
        return 0
    check = validation_check()
    save(BASE/"verifiche"/(uuid4().hex+".json"),check)
    print(json.dumps(check,ensure_ascii=False,indent=2),flush=True)
    if not check["ready"]:
        return 1
    if args.verifica:
        return 0
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus, record_features, EXPERIMENT_ID
    from prototype.quantum_assistant.adapters.qdrant_context import matching_records
    from prototype.quantum_assistant.adapters.rag_features import manhattan
    from numero_esempi import ensure_contract
    import portalocker
    run.mkdir(parents=True,exist_ok=True)
    with portalocker.Lock(str(run/".lock"),timeout=0):
        rows = validation_rows()
        contract = {"design":DESIGN,"code":code_identity(),"source_sha256":sha(SOURCE),
                    "aggregate_sha256":aggregate_hash(),"rag_seal_sha256":sha(ROOT/"data/seal.json")}
        ensure_contract(run/"contratto.json",contract)
        corpus = load_corpus()
        start = time.perf_counter()
        index, index_sha = prepare_index(corpus,run/"indice")
        tables = load_scores(rows)
        save(run/"sessioni"/(uuid4().hex+".json"),{"at":now(),"index_sha256":index_sha,
              "index_preparation_seconds":time.perf_counter()-start,"cold_or_warm":"inspect existing record timestamps"})
        for i,row in enumerate(rows,1):
            folder = run/"circuiti"/row["circuit_id"]
            path = folder/"esito.json"
            if path.exists():
                continue
            if (folder/"inizio.json").exists():
                save(path,{"status":"failure","circuit_id":row["circuit_id"],"split":"validation",
                           "error":"previous_interruption; preserved, use new run-id to repeat"})
                continue
            save(folder/"inizio.json",{"at":now(),"source_sha256":row["source_sha256"],"split":"validation"})
            try:
                qasm = source_path(row).read_text()
                query = descriptor(qasm)
                save(folder/"grafo.json",query)
                _, request, mask = request_context(qasm)
                devices = mask.available_device_ids
                # Ranking is sealed BEFORE reading the current validation score table.
                start = time.perf_counter()
                candidates = matching_records(corpus,devices=devices,objective=request.figure_of_merit,experiment_id=EXPERIMENT_ID)
                # request.features is the same source used by classic retrieval.
                features = request.features
                query_vector = corpus.transform.apply(features)
                classic = sorted(((r,manhattan(query_vector,corpus.transform.apply(record_features(r)))) for r in candidates),
                                 key=lambda x:(x[1],x[0]["rag_id"]))
                rankings = {"manhattan":(classic,time.perf_counter()-start)}
                for h in SUPPORTED_H:
                    start = time.perf_counter()
                    values = rank(corpus,index,query,devices,request.figure_of_merit,h)
                    rankings[f"wl_h{h}"] = (values,time.perf_counter()-start)
                retrieval = {}
                for method,(values,elapsed) in rankings.items():
                    if len(values)<5:
                        raise ValueError('Fewer than five candidates.')
                    retrieval[method] = {
                        "ranking_seconds":elapsed,
                        "score_kind":"distance_ascending" if method=="manhattan" else "similarity_descending",
                        "ranking":[{"rag_id":r["rag_id"],"value":v} for r,v in values]}
                save(folder/"recupero.json",retrieval)
                result = {"status":"success","split":"validation","circuit_id":row["circuit_id"],
                          "source_sha256":row["source_sha256"],"methods":{}}
                for method,(values,elapsed) in rankings.items():
                    chosen = [r for r,_ in values[:5]]
                    result["methods"][method] = {
                        "ranking_seconds":elapsed,
                        "retrieved_ids":[r["rag_id"] for r in chosen],
                        "retrieved_size_ratios":[r["retrieval_input"]["circuit"]["size"]/max(1,sum(n["label"][0] == "op" and n.get("name") != "barrier" for n in query["graph"]["nodes"])) for r in chosen],
                        "transfer":transfer_metrics(chosen,tables[row["circuit_id"]],devices)}
            except BaseException as exc:
                save(path,{"status":"failure","split":"validation","circuit_id":row["circuit_id"],
                           "error":type(exc).__name__,"message":str(exc)})
                raise
            save(path,result)
            print(f"Validation WL: {i}/88 {row['circuit_id']}",flush=True)
        paths = sorted((run/"circuiti").glob("*/esito.json"))
        records = [read(p) for p in paths]
        output = summarize(records)
        output["contract_sha256"] = sha(run/"contratto.json")
        output["index_sha256"] = index_sha
        output["record_hashes"] = {str(p.relative_to(run)):sha(p) for p in sorted((run/"circuiti").rglob("*.json"))}
        if (run/"riepilogo.json").exists():
            if read(run/"riepilogo.json") != output:
                raise ValueError('Previous summary differs.')
        else:
            save(run/"riepilogo.json",output)
        csv_path = run/"confronto.csv"
        if not csv_path.exists():
            with csv_path.open("x",newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["method","retrieved","top1_observed","common_n","mean_regret_common","median_regret_common","mean_ranking_seconds"])
                for m,v in output["methods"].items():
                    common=v["top1_regret_common"]
                    writer.writerow([m,v["circuits_retrieved"],v["top1_score"]["n"],common["n"],common["mean"],common["median"],v["ranking_seconds"]["mean"]])
        write_latex(run, output)
        print('Results to discuss: '+str(run/"riepilogo.json"))
        print('No configuration selected automatically; Tests not started.')
    return 0


def write_latex(run, result):
    'Regenerable standalone source: numbers come from the summary.'
    labels = {"manhattan":"Manhattan", **{f"wl_h{h}": f"WL, h={h}" for h in SUPPORTED_H}}
    rows, coords = [], []
    def number(x):
        return "--" if x is None else f"{x:.6f}"
    for i, method in enumerate(CANDIDATES):
        value = result["methods"][method]
        common = value["top1_regret_common"]
        rows.append(f'{labels[method]} & {value["top1_score"]["n"]}/88 & {common["n"]} & {number(common["mean"])} & {number(common["median"])} '+r'\\')
        if method != "manhattan" and common["mean"] is not None:
            coords.append(f'({i},{common["mean"]:.12g})')
    doc = """\\documentclass[a4paper,11pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage[english]{babel}
\\usepackage[margin=2.3cm]{geometry}
\\usepackage{booktabs,longtable,pgfplots,hyperref}
\\pgfplotsset{compat=1.18}
\\title{Validation of example retrieval with DAG and WL}
\\author{}\\date{}
\\begin{document}\\maketitle
We compare Manhattan and Weisfeiler--Lehman (WL) with 1 to 30 iterations,
always using five examples from the 396 train records. There are 88 validation circuits.
No LLM calls or new compilations were performed.
The representation uses the original DAGCircuit, directed edges with local
operand roles and numerical parameters discretized to $\\pi/8$.
The normalized kernel sums contributions from 0 to $h$.
\\section*{Measurement}
We transfer the first device/configuration pair from the first example.
The score and its observability come from preserved validation compilations.
Only pairs with successful seeds 0, 1 and 2 are allowed.
Regret is the difference from the best observed median score for that
circuit. Lower values indicate better transfer.
Missing scores remain missing; they do not become zero.
Shared means and medians use the same circuits for every method.
{\\small
\\begin{longtable}{lrrrr}\\toprule
Method & Observable & Shared cases & Mean regret & Median\\\\\\midrule\\endhead
@@ROWS@@
\\bottomrule\\end{longtable}}
\\begin{center}
\\begin{tikzpicture}
\\begin{axis}[width=.95\\linewidth,height=7cm,ymin=0,xmin=1,xmax=30,
xtick={1,5,10,15,20,25,30},xlabel={WL iterations},
ylabel={Mean regret on shared cases},legend pos=north east]
\\addplot+[mark=*,blue] coordinates {@@COORDS@@};
\\addlegendentry{WL}
@@BASELINE@@
\\end{axis}\\end{tikzpicture}
\\end{center}
\\section*{Limitations and selection}
The measurement concerns retrieval, not the LLM system's score.
@@INCOMPLETE@@ validation matrices are incomplete: the reference is the best
observed result, not necessarily the absolute best.
The JSON summary also preserves the best observed pair among all those
shown by the five examples, including ties. This is an optimistic indicator
and does not describe a decision available to the model.
Rankings are saved before score analysis.
Index construction/verification times are separate from comparisons.
Manhattan time here excludes Qdrant infrastructure.
The grid was extended after reviewing results for $h=1,\\ldots,6$.
This is adaptive validation on the same 88 cases.
The WL configuration must still be explicitly selected after discussing
coverage, regret on shared cases and costs. Equivalent results favor
fewer iterations.
Subsequent Tests use an already exposed corpus and do not provide new
independent confirmation.
\\section*{Reproducibility}
The contract, source fingerprints, graphs, rankings and outcomes are preserved
alongside this document. No Test result enters selection.
Algorithm source:
\\url{https://jmlr.org/papers/v12/shervashidze11a.html}.
The directed adaptation with edge roles is a choice made for this campaign.
\\end{document}
"""
    doc = doc.replace("@@ROWS@@","\n".join(rows)).replace("@@COORDS@@"," ".join(coords)).replace("@@INCOMPLETE@@",str(result["incomplete_validation_matrices"]))
    baseline = result["methods"]["manhattan"]["top1_regret_common"]["mean"]
    baseline_tex = "" if baseline is None else (
        r"\addplot[red,dashed] coordinates {(1,"+str(baseline)+")(30,"+str(baseline)+")};"
        +r"\addlegendentry{Manhattan}")
    doc = doc.replace("@@BASELINE@@", baseline_tex)
    target = run/"report_validation.tex"
    if target.exists():
        if target.read_text() != doc:
            raise ValueError('Existing LaTeX report differs.')
    else:
        with target.open("x") as handle:
            handle.write(doc)

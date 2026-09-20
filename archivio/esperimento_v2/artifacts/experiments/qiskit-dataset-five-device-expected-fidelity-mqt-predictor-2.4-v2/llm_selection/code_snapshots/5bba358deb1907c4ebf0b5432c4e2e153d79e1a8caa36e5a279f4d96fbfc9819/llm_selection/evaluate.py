"""Valuta la validation soltanto dopo i sigilli; riusa la matrice Qiskit."""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import dataset_scope_root
from qiskit_dataset.experiment_v2 import (
    PROTOCOL_VERSION, ORACLE_METHOD_ID, device_capacities, evaluate_common_methods, load_jsonl,
    source_manifest, summarize_results, validate_llm_decisions, validate_method_plan)
from scripts.mqt_predictor_protocol import EXPERIMENT_ID, METHOD_PLAN_DIR_V2, METHOD_RESULTS_DIR_V2, file_sha256
from .common import OUTPUT, ROOT, digest, read_json, write_json
from .study import MODEL_KEYS, FROZEN, require_all_sealed, immutable_json, model_root

def complete_sum(values):
    return sum(values) if all(v is not None for v in values) else None

def median_or_none(values):
    values=[v for v in values if v is not None]
    return median(values) if values else None

def episode_data(path, trial_id):
    decision=read_json(path/"decision.json")
    begin=read_json(path/"begin.json")
    attempts=[read_json(p) for p in sorted(path.glob("attempt_*/summary.json"))]
    responses=[a.get("response",{}) for a in attempts if a.get("llm_calls",0)]
    input_tokens=attempts[0].get("input_tokens")
    row={**decision,"trial_id":trial_id,"family":begin["circuit_metadata"].get("family",begin["circuit_metadata"].get("leakage_group")),
         "num_qubits":begin["circuit_metadata"].get("num_qubits"),
         "input_tokens":input_tokens,"first_attempt_valid":attempts[0]["status"]=="success",
         "first_attempt_json_valid":attempts[0].get("json_valid",False),
         "first_attempt_schema_valid":attempts[0].get("schema_valid",False),
         "total_input_tokens":complete_sum([(r.get("usage") or {}).get("prompt_tokens") for r in responses]),
         "total_output_tokens":complete_sum([(r.get("usage") or {}).get("completion_tokens") for r in responses]),
         "total_cached_tokens":complete_sum([(r.get("usage") or {}).get("cached_tokens") for r in responses]),
         "total_call_seconds":complete_sum([r.get("elapsed_seconds") for r in responses]),
         "ttft_seconds":responses[0].get("ttft_content_seconds") if responses else None,
         "prompt_processing_seconds":complete_sum([(r.get("timings") or {}).get("prompt_ms",0)/1000 if r.get("timings") else None for r in responses]),
         "generation_seconds":complete_sum([(r.get("timings") or {}).get("predicted_ms",0)/1000 if r.get("timings") else None for r in responses]),
         "retrieval_and_context_seconds":begin["retrieval_and_context_seconds"],
         "resource_run_key":begin["launch"]["process_start_time"],
         "peak_process_working_set_bytes":None,"peak_gpu_dedicated_bytes":None,"peak_gpu_shared_bytes":None,
         "minimum_available_ram_bytes":None,"maximum_gpu_hotspot_c":None,
         "resource_measurement_missing_reason":"No sample overlaps a measured HTTP call",
         "compiler_results_reused":True,"compiler_wall_time_new_seconds":0,
         "reasoning_tokens":None,"reasoning_tokens_missing_reason":"No separate reliable token counter; extended thinking disabled",
         "error_codes":dict(Counter(i["code"] for a in attempts for i in a.get("issues",[]))),
         "attempt_windows":[(r["started_at"],r["ended_at"]) for r in responses if r.get("started_at") and r.get("ended_at")]}
    raw=[r.get("content","") for r in responses]
    record={"schema_version":"1.0.0","experiment_id":EXPERIMENT_ID,"protocol_version":PROTOCOL_VERSION,
            "method_id":"llm_rag","method_config_sha256":None,"split":"validation",
            **{k:decision[k] for k in ("circuit_id","source_sha256","status","selected_device_id","selected_config_id","attempt_count","failure")},
            "raw_response_sha256":digest(raw),"timings_seconds":{"llm_calls":row["total_call_seconds"]},
            "usage":{"llm_calls":decision["llm_calls"],"repair_count":decision["repair_count"],
                     "input_tokens":row["total_input_tokens"],"output_tokens":row["total_output_tokens"]}}
    return row,record

def attach_resources(rows):
    by_run=defaultdict(list)
    for row in rows: by_run[row["resource_run_key"]].append(row)
    for directory in sorted((OUTPUT/"servers").glob("*")):
        if not (directory/"launch.json").exists(): continue
        launch=read_json(directory/"launch.json")
        targets=by_run.get(launch["process_start_time"],[])
        if not targets: continue
        if not (directory/"exit.json").exists(): raise ValueError("Stop inference server before final evaluation")
        for row in targets:
            row["_windows"]=[(datetime.fromisoformat(a),datetime.fromisoformat(b)) for a,b in row["attempt_windows"]]
        invalid_tail=False
        with (directory/"resources.jsonl").open(encoding="utf-8-sig") as stream:
            import json
            for line in stream:
                try: sample=json.loads(line)
                except (ValueError,UnicodeError): invalid_tail=True; break
                stamp=datetime.fromisoformat(sample["utc"])
                for row in targets:
                    if not any(a<=stamp<=b for a,b in row["_windows"]): continue
                    row["resource_measurement_missing_reason"]=None
                    for key,source in (("peak_process_working_set_bytes","working_set_bytes"),
                                       ("peak_gpu_dedicated_bytes","gpu_dedicated_bytes"),
                                       ("peak_gpu_shared_bytes","gpu_shared_bytes")):
                        value=sample.get(source)
                        if value is not None: row[key]=max(row[key] or 0,value)
                    value=sample.get("system_available_bytes")
                    if value is not None: row["minimum_available_ram_bytes"]=min(row["minimum_available_ram_bytes"] if row["minimum_available_ram_bytes"] is not None else value,value)
                    for sensor in sample.get("gpu_sensors",[]):
                        value=sensor.get("hotspot_c")
                        if value is not None: row["maximum_gpu_hotspot_c"]=max(row["maximum_gpu_hotspot_c"] or 0,value)
        for row in targets:
            row.pop("_windows",None)
            row["resource_log_incomplete_tail"]=invalid_tail
            row["server_resource_path"]=str(directory.relative_to(ROOT))

def trial_summary(rows):
    success=[r for r in rows if r["status"]=="success"]
    regrets=[r["regret_absolute"] for r in success if r["regret_absolute"] is not None]
    return {
        "circuits":len(rows),"valid_decisions":sum(r["decision_status"]=="success" for r in rows),
        "valid_and_compilable":len(success),"regret_available":len(regrets),
        "median_regret_absolute":median_or_none(regrets),
        "first_attempt_valid":sum(r["first_attempt_valid"] for r in rows),
        "first_attempt_json_valid":sum(r["first_attempt_json_valid"] for r in rows),
        "first_attempt_schema_valid":sum(r["first_attempt_schema_valid"] for r in rows),
        "total_llm_calls":sum(r["llm_calls"] for r in rows),
        "repairs":sum(r["repair_count"] for r in rows),
        "transport_retries":sum(r["transport_retries"] for r in rows),
        "total_call_seconds":complete_sum([r["total_call_seconds"] for r in rows]),
        "median_call_seconds":median_or_none([r["total_call_seconds"] for r in rows]),
        "total_output_tokens":complete_sum([r["total_output_tokens"] for r in rows]),
        "output_tokens_observed_lower_bound":sum(r["total_output_tokens"] or 0 for r in rows),
        "token_complete_circuits":sum(r["total_output_tokens"] is not None for r in rows),
        "peak_ram_bytes":max((r["peak_process_working_set_bytes"] or 0 for r in rows),default=0) or None,
        "peak_gpu_bytes":max((r["peak_gpu_dedicated_bytes"] or 0 for r in rows),default=0) or None,
        "oracle_available":sum(r["oracle_score"] is not None for r in rows),
        "device_exact_matches":sum(r["device_exact_match"] is True for r in rows),
        "configuration_exact_matches":sum(r["configuration_exact_match"] is True for r in rows),
        "pair_exact_matches":sum(r["pair_exact_match"] is True for r in rows),
        "accuracy_denominator":sum(r["oracle_score"] is not None for r in rows),
        "failures":dict(Counter(r["failure_category"] for r in rows if r["failure_category"])),
    }

def choose(rows_by_trial):
    summaries={key:trial_summary(rows) for key,rows in rows_by_trial.items()}
    eligible=list(sorted(summaries))
    steps=[]
    best=max(summaries[k]["valid_and_compilable"] for k in eligible)
    if best==0: return {"winner":None,"reason":"No valid and compilable candidate","steps":[],"summaries":summaries}
    eligible=[k for k in eligible if summaries[k]["valid_and_compilable"]==best]
    steps.append({"criterion":"valid_and_compilable","best":best,"remaining":eligible[:]})
    common=set.intersection(*[{r["source_sha256"] for r in rows_by_trial[k] if r["status"]=="success" and r["regret_absolute"] is not None} for k in eligible])
    if len(eligible)>1 and common:
        values={k:median(r["regret_absolute"] for r in rows_by_trial[k] if r["source_sha256"] in common) for k in eligible}
        value=min(values.values()); eligible=[k for k in eligible if values[k]==value]
        steps.append({"criterion":"median_regret_common","values":values,"common_source_hashes":sorted(common),"remaining":eligible[:]})
    else:
        steps.append({"criterion":"median_regret_common","applied":False,"common_count":len(common),
                      "reason":"single candidate" if len(eligible)==1 else "no common evaluable circuit"})
    for field,maximize in (("first_attempt_json_valid",True),("total_llm_calls",False),
                           ("total_call_seconds",False),("total_output_tokens",False)):
        if len(eligible)==1: break
        values={k:summaries[k][field] for k in eligible}
        if any(v is None for v in values.values()):
            steps.append({"criterion":field,"applied":False,"reason":"incomplete measurement","values":values}); continue
        value=(max if maximize else min)(values.values())
        eligible=[k for k in eligible if values[k]==value]
        steps.append({"criterion":field,"values":values,"remaining":eligible[:]})
    if len(eligible)>1: steps.append({"criterion":"lexicographic","remaining":eligible[:]})
    return {"winner":min(eligible),"steps":steps,"summaries":summaries,"regret_common_source_hashes":sorted(common)}

def write_csv(path, rows):
    keys=sorted(set().union(*(r.keys() for r in rows)))
    with Path(path).open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader()
        import json
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)

def evaluate(output_dir=None):
    # This is deliberately the first operation. No score file is opened before it.
    study,seal=require_all_sealed()
    root=OUTPUT/"studies"/study["study_id"]
    out=Path(output_dir) if output_dir else root/"analysis"
    out.mkdir(parents=True,exist_ok=True)
    catalog=load_catalog();manifest=source_manifest();capacities=device_capacities()
    plan=read_json(METHOD_PLAN_DIR_V2/"validation_method_plan.json")
    validate_method_plan(plan,split="validation",catalog=catalog,manifest=manifest,capacities=capacities)
    prepared={}
    for model in MODEL_KEYS:
        for config in study["configurations"]:
            trial=model+"/"+config["id"]
            descriptor={"study_sha256":digest(study),"model":model,"configuration":config}
            rows,records=zip(*(episode_data(p.parent,trial) for p in sorted((model_root(study,model)/config["id"]).glob("*/decision.json"))))
            for record in records: record["method_config_sha256"]=digest(descriptor)
            valid=validate_llm_decisions(records,method_id="llm_rag",split="validation",catalog=catalog,manifest=manifest,
                capacities=capacities,method_config={"methods":{"llm_rag":{"max_attempts":study["max_attempts"]}}},
                method_config_sha256=digest(descriptor))
            prepared[trial]=(list(rows),valid,descriptor)
    # All model decisions have now been verified independently of matrix scores.
    global_root=dataset_scope_root("expected_fidelity","full",experiment_id=EXPERIMENT_ID)/"global"
    runs_path=global_root/"qiskit_runs.jsonl";aggregates_path=global_root/"qiskit_configuration_aggregates.jsonl"
    runs=load_jsonl(runs_path);aggregates=load_jsonl(aggregates_path)
    if any(r.get("split")=="test" for r in [*runs,*aggregates]): raise ValueError("Unexpected test scores before release")
    fingerprints={"study":file_sha256(FROZEN),"decisions_seal":digest(seal),"qiskit_runs":file_sha256(runs_path),
                  "qiskit_aggregates":file_sha256(aggregates_path)}
    rows_by_trial={}; baselines=None
    for trial,(rows,records,descriptor) in prepared.items():
        results=evaluate_common_methods(split="validation",catalog=catalog,manifest=manifest,plan=plan,capacities=capacities,
            qiskit_runs=runs,qiskit_summaries=aggregates,llm_decisions={"llm_rag":records},qcompile_runs=[],
            method_config_sha256=digest(descriptor),llm_method_ids=("llm_rag",),include_qcompile=False)
        if baselines is None: baselines=[r for r in results if r["method_id"]!="llm_rag"]
        oracle={r["source_sha256"]:r for r in results if r["method_id"]==ORACLE_METHOD_ID}
        scored={r["source_sha256"]:r for r in results if r["method_id"]=="llm_rag"}
        for row in rows:
            result=scored[row["source_sha256"]]; reference=oracle[row["source_sha256"]]
            row["decision_status"]=row["status"]
            row.update(result);row["trial_id"]=trial
            available=reference["score"] is not None
            row["device_exact_match"]=row["decision_status"]=="success" and row["selected_device_id"]==reference["selected_device_id"] if available else None
            row["configuration_exact_match"]=row["decision_status"]=="success" and row["selected_config_id"]==reference["selected_config_id"] if available else None
            row["pair_exact_match"]=row["device_exact_match"] and row["configuration_exact_match"] if available else None
        rows_by_trial[trial]=rows
    all_rows=[r for rows in rows_by_trial.values() for r in rows]
    attach_resources(all_rows)
    selection=choose(rows_by_trial)
    immutable_json(out/"episode_results.json",all_rows)
    immutable_json(out/"baseline_results.json",baselines)
    immutable_json(out/"selection.json",selection)
    immutable_json(out/"input_fingerprints.json",fingerprints)
    write_csv(out/"episodes.csv",all_rows)
    write_csv(out/"trials.csv",[{"trial_id":k,**v} for k,v in selection["summaries"].items()])
    print("Validation evaluated; selected candidate:",selection["winner"],flush=True)
    return study,selection,out

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output-dir",type=Path);args=parser.parse_args()
    evaluate(args.output_dir)
if __name__=="__main__": main()

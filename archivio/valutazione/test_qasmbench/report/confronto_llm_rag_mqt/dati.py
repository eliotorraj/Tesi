'Reproducible analysis of records only: does not start models or quantum compilations.'
from __future__ import annotations
import csv, hashlib, json, math, statistics, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
AREA = HERE.parents[1]
ROOT = AREA.parents[2]
sys.path.insert(0, str(AREA))
from analizza import collect, summarize

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):
    v = [x for x in values if isinstance(x, (int, float)) and not isinstance(x, bool)]
    return {"n":len(v), "mean":statistics.mean(v) if v else None,
            "median":statistics.median(v) if v else None, "sum":sum(v) if v else None,
            "min":min(v) if v else None, "max":max(v) if v else None}
METRICS = ("score","total_seconds","compilation_seconds","compilation_process_seconds",
           "choice_seconds","rag_seconds","llm_response_seconds","input_tokens","output_tokens",
           "total_tokens","llm_calls","retries")
METHODS = ("llm_rag","mqt_predictor")
GROUPS = ("all","small","medium","large")
def analyze():
    manifest=read(AREA/"manifest.json")
    contract=read(AREA/"preparazione/contratto_congelato.json")
    rows, results, sources = collect()
    assert len(rows)==50 and len(results)==100, 'Incomplete campaign'
    assert Counter(r["size_group"] for r in rows)=={"small":30,"medium":15,"large":5}
    cfg=contract["plan"]["analysis"]
    groups=summarize(rows,results,cfg["bootstrap_draws"],cfg["bootstrap_seed"])
    detail=[]
    runs={}
    requests=[]
    for method in METHODS:
        runs[method]=read(AREA/"risultati"/method/"esecuzione.json")
        assert runs[method]["plan_sha256"]==sha(AREA/"piano.json")
        for r in rows:
            value=results[method,r["circuit_id"]]
            folder=AREA/"risultati"/method/"circuiti"/r["circuit_id"]
            original=AREA/"circuiti"/r["source_ref"]
            assert sha(original)==r["source_sha256"]
            # The runner reads/writes UTF-8 text, normalizing CRLF to LF.
            assert (folder/"input.qasm").read_text()==original.read_text()
            sources[str(original.relative_to(AREA))]=sha(original)
            if value["status"]=="success":
                assert value["validation"]["is_executable_on_target"]
                assert not value["underflow"] and not value["rounded_to_zero"]
            if method=="llm_rag":
                calls=sorted(folder.glob("attempt_*/call/request.json"))
                assert len(calls)==value["llm_calls"]
                assert value["token_usage_complete"]
                assert value["input_tokens"]+value["output_tokens"]==value["total_tokens"]
                for p in calls:
                    q=read(p)
                    requests.append({k:q.get(k) for k in ("temperature","seed","n_predict","top_p","top_k","min_p","cache_prompt")})
                assert len(calls)<=contract["plan"]["llm_max_completed_attempts"]
            # Fingerprints cover original attempts, prompts, responses and compiled circuits.
            for p in folder.rglob("*"):
                if p.is_file(): sources[str(p.relative_to(AREA))]=sha(p)
            detail.append({**r,**value})
    paired=[]
    for i,r in enumerate(rows,1):
        a,b=(results[m,r["circuit_id"]] for m in METHODS)
        if a["status"]==b["status"]=="success":
            paired.append({"index":i,"circuit_id":r["circuit_id"],"size_group":r["size_group"],
                           "llm_score":a["score"],"mqt_score":b["score"],"delta":a["score"]-b["score"],
                           "llm_total":a["total_seconds"],"mqt_total":b["total_seconds"],
                           "llm_compile":a["compilation_seconds"],"mqt_compile":b["compilation_seconds"]})
    for group in GROUPS:
        selected=[r for r in rows if group=="all" or r["size_group"]==group]
        pp=[p for p in paired if group=="all" or p["size_group"]==group]
        for method in METHODS:
            vv=[results[method,r["circuit_id"]] for r in selected]
            groups[group]["methods"][method].update({
                "metrics":{key:stats(v.get(key) for v in vv) for key in METRICS},
                "threshold_08":sum(v["status"]=="success" and v["score"]>=.8 for v in vv),
                "below_08":sum(v["status"]=="success" and v["score"]<.8 for v in vv),
                "devices_success":dict(Counter(v["device"] for v in vv if v["status"]=="success")),
                "calls":dict(Counter(str(v.get("llm_calls")) for v in vv)) if method=="llm_rag" else None})
        groups[group]["paired"].update({
            "llm_score":stats(p["llm_score"] for p in pp),
            "mqt_score":stats(p["mqt_score"] for p in pp),
            "llm_total":stats(p["llm_total"] for p in pp),
            "mqt_total":stats(p["mqt_total"] for p in pp),
            "llm_compile":stats(p["llm_compile"] for p in pp),
            "mqt_compile":stats(p["mqt_compile"] for p in pp),
            "llm_faster_total":sum(p["llm_total"]<p["mqt_total"] for p in pp),
            "llm_faster_compile":sum(p["llm_compile"]<p["mqt_compile"] for p in pp)})
    assert len({json.dumps(x,sort_keys=True) for x in requests})==1
    req=requests[0]
    assert req["temperature"]==0 and req["seed"]==20260913 and req["n_predict"]==4096
    a=[v for v in detail if v["method"]=="llm_rag"]
    failed=[v for v in detail if v["status"]!="success"]
    for v in failed:
        p=AREA/"risultati"/v["method"]/"circuiti"/v["circuit_id"]/"compilazione/selection.json"
        v["selection_before_timeout"]=read(p) if p.exists() else None
    llm={"unverified_facts":sum(v["accepted_with_unverified_facts"] for v in a),
         "verified_facts":sum(not v["accepted_with_unverified_facts"] for v in a),
         "calls_histogram":dict(Counter(str(v["llm_calls"]) for v in a)),
         "configs":dict(Counter(v["config_id"] for v in a)),
         "request_parameters":req,"request_count":len(requests)}
    # Compare with the preserved analysis using the same procedure and intervals.
    old=AREA/"report/generati/2026-09-30T09-00-35.872388+00-00-a7fd4923/riepilogo.json"
    if old.exists():
        for group in GROUPS:
            assert groups[group]["paired"]["bootstrap_95_percent"]==read(old)["summary"][group]["paired"]["bootstrap_95_percent"]
    sourcefiles=[AREA/"manifest.json",AREA/"piano.json",AREA/"preparazione/contratto_congelato.json",AREA/"analizza.py",
                 AREA/"strumenti/runner.py",AREA/"strumenti/worker.py",AREA/"strumenti/score.py"]
    for p in sourcefiles: sources[str(p.relative_to(AREA))]=sha(p)
    provenance={"paths_relative_to":"archivio/valutazione/test_qasmbench",
                "source_sha256":sources,"manifest_sha256":sha(AREA/"manifest.json"),
                "contract_sha256":sha(AREA/"preparazione/contratto_congelato.json"),
                "analysis":cfg,"source_revision":manifest["revision"],
                "run_metadata":{m:{k:v for k,v in run.items() if k not in ("preflight","server")} for m,run in runs.items()},
                "llm_server":runs["llm_rag"].get("server"),
                "classification":"additional-independent-test"}
    summary={"groups":groups,"llm":llm,"failed":failed,"paired":paired,"provenance":provenance}
    (HERE/"dati").mkdir(exist_ok=True)
    (HERE/"dati/riepilogo.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    fields=["circuit_id","size_group","qubits","method","status","score","log_score_unrounded","device","config_id",
            *[k for k in METRICS if k!="score"],"accepted_with_unverified_facts","error","source_sha256"]
    with (HERE/"dati/circuiti.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(detail)
    with (HERE/"dati/coppie.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    return rows,results,summary

if __name__=="__main__":
    rows,results,s=analyze()
    print(json.dumps({"paired":s["groups"]["all"]["paired"],
        "groups":{g:{m:{k:v for k,v in x.items() if k in ("threshold_08","below_08","statuses")} for m,x in s["groups"][g]["methods"].items()} for g in GROUPS},
        "llm":s["llm"],"failures":[(v["circuit_id"],v.get("selection_before_timeout")) for v in s["failed"]],
        "server_keys":list(s["provenance"]["llm_server"] or {}),
        "best_deltas":sorted(s["paired"],key=lambda p:p["delta"])[:4]+sorted(s["paired"],key=lambda p:p["delta"])[-4:]},indent=2))

'Separate descriptive analysis: reads QASMBench outcomes only.'
from __future__ import annotations
import csv,json,math,random,statistics,sys
from collections import Counter
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from common import AREA,PLAN,SOURCE,METHODS,read,sha,save,now

def summarize(rows, results, draws=10000, seed=20260901):
    'No imputation: quality only for pairs with two successes.'
    groups={}
    for group in ("all","small","medium","large"):
        selected=[r for r in rows if group=="all" or r["size_group"]==group]
        item={"expected":len(selected),"methods":{}}
        paired=[]
        for method in METHODS:
            values=[results.get((method,r["circuit_id"])) for r in selected]
            statuses=Counter(v["status"] if v else "missing" for v in values)
            scores=[v["score"] for v in values if v and v["status"]=="success"]
            times=[v["total_seconds"] for v in values if v and isinstance(v.get("total_seconds"),(int,float))]
            item["methods"][method]={"statuses":dict(statuses),"success_denominator":len(selected),
                "score_mean_successes":statistics.mean(scores) if scores else None,
                "score_denominator":len(scores),"mean_total_seconds_known":statistics.mean(times) if times else None,
                "time_denominator":len(times),
                "tokens_known":sum(v.get("known_input_tokens",0)+v.get("known_output_tokens",0) for v in values if v),
                "token_complete_circuits":sum(bool(v and v.get("token_usage_complete")) for v in values)}
        for row in selected:
            a,b=[results.get((m,row["circuit_id"])) for m in METHODS]
            if a and b and a["status"]==b["status"]=="success":
                paired.append((row["circuit_id"],a["score"]-b["score"]))
        delta=[v for _,v in paired]
        interval=None
        if len(delta)>=2:
            rng=random.Random(seed)
            means=sorted(statistics.mean(rng.choices(delta,k=len(delta))) for _ in range(draws))
            interval=[means[int(.025*(draws-1))],means[int(.975*(draws-1))]]
        item["paired"]={"n":len(delta),"circuit_ids":[name for name,_ in paired],
            "mean_difference_llm_minus_mqt":statistics.mean(delta) if delta else None,
            "median_difference":statistics.median(delta) if delta else None,
            "bootstrap_95_percent":interval,
            "llm_wins":sum(v>0 for v in delta),"ties":sum(v==0 for v in delta),"mqt_wins":sum(v<0 for v in delta)}
        groups[group]=item
    return groups

def collect():
    rows=read(SOURCE)["circuits"]
    contract_path=AREA/"preparazione/contratto_congelato.json"
    contract=read(contract_path) if contract_path.exists() else None
    if contract and contract["source_sha256"]!=sha(SOURCE):
        raise ValueError('Manifest differs from the executed contract.')
    results,inputs={},{}
    expected={r["circuit_id"]:r for r in rows}
    for method in METHODS:
        base=AREA/"risultati"/method
        begin=base/"esecuzione.json"
        paths=list((base/"circuiti").glob("*/esito.json"))
        if paths and not begin.exists(): raise ValueError('Missing run record: '+method)
        if begin.exists():
            run=read(begin)
            if not contract or run["contract_sha256"]!=sha(contract_path):
                raise ValueError('Contracts are not comparable: '+method)
            if run["method"]!=method or run["kind"]!="external_test" or run["expected_circuits"]!=50:
                raise ValueError('Run does not belong to the comparison.')
            inputs[str(begin.relative_to(AREA))]=sha(begin)
        for path in paths:
            value=read(path); ident=value["circuit_id"]
            row=expected.get(ident)
            if not row or path.parent.name!=ident or value["method"]!=method or value["source_sha256"]!=row["source_sha256"] or value["split"]!="external_test":
                raise ValueError('Outcome does not belong to the manifest: '+str(path))
            if value["status"] not in ("success","failure","timeout","interrupted"):
                raise ValueError('Unrecognized status')
            if value["status"]=="success" and (not isinstance(value.get("score"),(int,float)) or not math.isfinite(value["score"]) or not 0<=value["score"]<=1):
                raise ValueError('Invalid success score')
            results[method,ident]=value
            inputs[str(path.relative_to(AREA))]=sha(path)
    if not results: raise ValueError('No outcomes: the Test has not been started.')
    return rows,results,inputs

def main():
    rows,results,inputs=collect()
    plan=read(AREA/"preparazione/contratto_congelato.json")["plan"]
    analysis=plan["analysis"]
    summary=summarize(rows,results,analysis["bootstrap_draws"],analysis["bootstrap_seed"])
    out=AREA/"report/generati"/(now().replace(":","-")+"-"+uuid4().hex[:8])
    out.mkdir(parents=True)
    save(out/"riepilogo.json",{"at":now(),"summary":summary,"source_sha256":sha(SOURCE),
        "comparison_status":plan.get("exploratory"),"contract_sha256":sha(AREA/"preparazione/contratto_congelato.json"),
        "inputs":inputs,"analysis_script_sha256":sha(Path(__file__)),"analysis":analysis,
        "complete":len(results)==100,"note":'Estimated fidelity on synthetic Targets. No hardware execution. Missing values and failures are not zeros.'})
    fields=["circuit_id","size_group","qubits","method","status","score","log_score_unrounded",
        "rounded_to_zero","underflow","device","config_id","total_seconds","compilation_seconds",
        "choice_seconds","rag_seconds","llm_calls","retries","input_tokens","output_tokens","total_tokens","error","message"]
    with (out/"circuiti.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in rows:
            for method in METHODS:
                value={**row,**results.get((method,row["circuit_id"]),{"status":"missing"}),"method":method}
                writer.writerow({key:value.get(key) for key in fields})
    lines=['# Additional independent QASMBench test',"",
        'MQT uses the selector trained on 384 of the 396 planned train samples; adaptive collection at 100/300 seconds. Twelve samples excluded.',
        f'Available outcomes: {len(results)}/100. Circuits: 50. Quality compared only on shared successes.',
        'This is a purposive selection, not a random QASMBench sample. Intervals are descriptive.',
        'Positive difference: higher LLM + RAG score. Failures are reported separately.',
        "", '| Group | Circuits | LLM successes | MQT successes | Pairs | Mean difference | Descriptive 95% CI |',
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for group,item in summary.items():
        paired=item["paired"];methods=item["methods"]
        lines.append(f'| {group} | {item["expected"]} | {methods["llm_rag"]["statuses"].get("success",0)} | {methods["mqt_predictor"]["statuses"].get("success",0)} | {paired["n"]} | {paired["mean_difference_llm_minus_mqt"]} | {paired["bootstrap_95_percent"]} |')
    lines += ["",'Details, denominators, missing states and times: riepilogo.json and circuiti.csv.',
        'Score rounded to 10 decimal places; unrounded log-score preserved to diagnose zeros and underflow.',
        'No oracle computed, so no regret or optimality is reported. Peak memory not measured.']
    (out/"rapporto.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pairs=[(results.get(("llm_rag",r["circuit_id"])),results.get(("mqt_predictor",r["circuit_id"]))) for r in rows]
        pairs=[(a,b) for a,b in pairs if a and b and a["status"]==b["status"]=="success"]
        fig,ax=plt.subplots(figsize=(6,6))
        ax.scatter([b["score"] for a,b in pairs],[a["score"] for a,b in pairs])
        ax.plot([0,1],[0,1],color="gray",linestyle="--")
        ax.set(xlabel="MQT Predictor: expected fidelity",ylabel="LLM + RAG: expected fidelity",
            title=f'QASMBench: {len(pairs)} circuits with two successes',xlim=(0,1),ylim=(0,1))
        fig.tight_layout();fig.savefig(out/"confronto.png",dpi=180);fig.savefig(out/"confronto.svg");plt.close(fig)
    except ImportError:
        save(out/"grafico_non_disponibile.json",{"reason":'matplotlib is not installed; tables and analysis generated'})
    print(out)
    return 0
if __name__=="__main__": raise SystemExit(main())

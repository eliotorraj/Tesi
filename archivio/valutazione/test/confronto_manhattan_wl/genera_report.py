"""Confronto dai registri conservati: nessuna inferenza o compilazione quantistica."""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import json
import math
import statistics as st
import sys

REPO = Path(__file__).resolve().parents[4]
AREA = REPO/"archivio/valutazione/test"
sys.path.insert(0, str(REPO/"prototipo"))
sys.path.insert(0, str(AREA/"strumenti"))
from common import SOURCE
from runner import llm_metrics
from prototype.prompting import facts, minimal
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
from prototype.quantum_assistant.adapters.context import _compact_rag_example

BASES = {
    "M": AREA/"risultati/llm_rag",
    "W": AREA/"dag_wl_retrieval/risultati/llm_rag_dag_wl",
    "S": AREA/"dag_wl_sintesi/risultati/llm_rag_dag_wl_sintesi",
}

METRICS = ("score", "total_seconds", "compilation_seconds", "compilation_process_seconds",
           "choice_seconds", "rag_seconds", "llm_response_seconds", "input_tokens",
           "output_tokens", "total_tokens", "llm_calls", "retries", "first_input_tokens")
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
def stats(values):
    v = [x for x in values if isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x)]
    return {"n":len(v), "mean":st.mean(v) if v else None, "median":st.median(v) if v else None,
            "sum":sum(v), "min":min(v) if v else None, "max":max(v) if v else None}
def collect():
    sources = {}
    def read(p):
        sources[str(p.relative_to(REPO))] = sha(p)
        return json.loads(p.read_text(encoding="utf-8"))
    manifest = read(SOURCE)
    expected = {r["circuit_id"]:r for r in manifest["circuits"] if r["split"]=="test"}
    assert len(expected)==90
    corpus = load_corpus()
    train = {r["rag_id"]:r for r in corpus.records}
    runs = {}; retrieval = {}; views = {}; settings = {}; metadata = {}; attempts = []; rankings={}; summaries={}; preparation={}; examples={}
    for k,base in BASES.items():
        execution = read(base/"esecuzione.json")
        contract_path = base/"contratto_congelato.json" if k!="M" else AREA/"preparazione/contratto_congelato.json"
        contract = read(contract_path)
        assert sha(contract_path)==execution["contract_sha256"], (k,"contract hash")
        if k!="M": assert read(base/"circuiti/groundstate_medium_indep_qiskit_12/retrieval.json")["h"]==24
        metadata[k] = {"source":str(base.relative_to(REPO)), "started_at":execution["at"],
                       "kind":execution.get("kind",contract.get("kind")), "model_sha256":execution["server"]["model_sha256"],
                       "context":execution["server"].get("context_requested"),
                       "contract_sha256":execution["contract_sha256"],
                       "historical_code":execution["code"], "cpu_count":execution.get("cpu_count")}
        files = sorted((base/"circuiti").glob("*/esito.json"))
        assert {p.parent.name for p in files}==set(expected)
        rows = []; retrieval[k]={}; views[k]={}; rankings[k]={}
        preparation[k]=[read(p) for p in sorted((base/"preparazione").glob("*.json"))]
        if k!="M": read(base/"indice/manifest.json")
        cached_records={r["rag_id"]:r for r in (read(p) for p in sorted((base/"indice/record").glob("*.json")))} if k=="S" else {}


        for p in files:
            folder=p.parent; row=read(p); cid=row["circuit_id"]
            assert row["source_sha256"]==expected[cid]["source_sha256"] and row["split"]=="test"
            prompt=read(folder/"prompt.json"); enc=read(folder/"encoding.json"); ret=read(folder/"retrieval.json")
            assert len(ret["records"])==5
            view=minimal.model_input(prompt,max_examples=5)
            ctx=minimal.citation_context(prompt,max_examples=5)
            assert enc==facts.audit(prompt,max_examples=5)
            ids=[e["record_id"] for e in prompt["retrieved_labeled_examples"]]
            assert ids==list(ctx.aliases.values())==[e["rag_id"] for e in ret["records"]]
            for e in prompt["retrieved_labeled_examples"]:
                record=train[e["record_id"]]
                assert record["split"]=="train" and e["example"]==_compact_rag_example(record)
            retrieval[k][cid]=ids
            rankings[k][cid]=ret["records"]
            if k!="M": assert ret["h"]==24 and ret["k"]==5
            if k=="S":
                assert prompt["dag_summaries"]["current_circuit"]==ret["query"]["summary"]
                assert [e["example_id"] for e in prompt["dag_summaries"]["examples"]]==["E1","E2","E3","E4","E5"]
                for item in prompt["dag_summaries"]["examples"]:
                    recid=ids[int(item["example_id"][1:])-1]
                    cached=cached_records[recid]
                    assert item["summary"]==cached["summary"]
                if cid=="groundstate_medium_indep_qiskit_12":
                    examples={"circuit_id":cid,"summaries":prompt["dag_summaries"],"records":ret["records"]}
            else: assert "dag_summaries" not in prompt

            views[k][cid]={key:value for key,value in view.items() if key!="retrieved_labeled_examples"}
            computed=llm_metrics(folder)
            for key,value in computed.items():
                assert row[key]==value, (k,cid,key)
            first=read(folder/"attempt_1/context.json")
            row["first_input_tokens"]=first["input_tokens"]
            row["num_qubits"]=view["circuit"]["num_qubits"]
            row["index"]=len(rows)+1
            final=read(folder/"decision_validation.json"); decision=read(folder/"decision.json")
            assert final["canonical_response"]==decision
            row["facts_status"]=final["facts_status"]
            row["facts_verified"]=sum(c["result"]=="verified" for c in final["fact_checks"])
            row["facts_total"]=len(final["fact_checks"])
            row["fact_checks"]=final["fact_checks"]
            row["first_facts_status"]=read(folder/"attempt_1/validation.json")["facts_status"]
            row["first_valid"]=row["first_facts_status"]=="verified"
            row["choice_pair"]=[decision["selected_device"],decision["config_id"]]
            validations=sorted(folder.glob("attempt_*/validation.json"))
            assert len(validations)==row["llm_calls"]
            for path in validations:
                v=read(path); raw=read(path.parent/"call/response_raw.json")
                check=facts.verify(raw["content"],prompt,max_examples=5)
                for key in ("schema_valid","selection_valid","facts_status","fact_checks","canonical_response"):
                    assert check[key]==v[key],(k,cid,path,key)
                request=read(path.parent/"call/request.json")
                params={key:value for key,value in request.items() if key not in ("prompt","json_schema")}
                if settings: assert params==settings, (k,cid,"generation settings")
                else: settings=params
                assert request["json_schema"]==facts.response_schema(max_examples=5)
                context=read(path.parent/"context.json");read(path.parent/"call/timing.json")
                msg=read(path.parent/"template/request.json")["messages"]
                if k=="S":
                    from prototype.prompting.toon import encode_view
                    block=encode_view({"dag_summaries":prompt["dag_summaries"]})
                    assert block in msg[0]["content"]
                    if cid=="groundstate_medium_indep_qiskit_12" and v["attempt"]==1:
                        examples["actual_summary_toon"]=block
                else: assert "dag_summaries:" not in msg[0]["content"]

                assert context["input_tokens"]+context["output_budget"]<=context["context"]==60000
                attempts.append({"k":k,"circuit_id":cid,"attempt":v["attempt"],"facts_status":v["facts_status"],
                                 "input_tokens":context["input_tokens"],"output_tokens":raw["tokens_predicted"],
                                 "checks":v["fact_checks"]})
            assert json.loads(read(folder/f"attempt_{final['attempt']}/call/response_raw.json")["content"])==decision
            compiled=read(folder/"compilazione/result.json")
            if row["status"]=="success":
                assert row["score"]==compiled["score"] and 0<=row["score"]<=1
                assert row["device"]==decision["selected_device"] and row["config_id"]==decision["config_id"]
            rows.append(row)
        runs[k]=rows
    ids=sorted(expected)
    assert len({m["model_sha256"] for m in metadata.values()})==1
    assert all(retrieval["W"][c]==retrieval["S"][c] and rankings["W"][c]==rankings["S"][c] for c in ids)
    assert all(views["M"][c]==views["W"][c]==views["S"][c] for c in ids)
    aggregated={}
    for k,rows in runs.items():
        kinds=Counter((c["assertion"],c["result"]) for row in rows for c in row["fact_checks"])
        aggregated[k]={
            "n":len(rows),"successes":sum(r["status"]=="success" for r in rows),
            "threshold_08":sum(r["status"]=="success" and r["score"]>=.8 for r in rows),
            "metrics":{key:stats([r.get(key) for r in rows if key!="score" or r["status"]=="success"]) for key in METRICS},
            "retry_cases":sum(r["retries"]>0 for r in rows),
            "valid_first":sum(r["first_valid"] for r in rows),
            "valid_final":sum(r["facts_status"]=="verified" for r in rows),
            "facts_verified":sum(r["facts_verified"] for r in rows),
            "facts_total":sum(r["facts_total"] for r in rows),
            "fact_kinds":[{"assertion":a,"result":b,"n":n} for (a,b),n in sorted(kinds.items())],
        }
    byid={k:{r["circuit_id"]:r for r in rows} for k,rows in runs.items()}
    pairs=[]
    for a,b in [("W","M"),("S","M"),("S","W")]:
        common=[c for c in ids if all(byid[k][c]["status"]=="success" for k in (a,b))]
        ds=[byid[a][c]["score"]-byid[b][c]["score"] for c in common]
        pairs.append({"a":a,"b":b,"n":len(common),"delta":stats(ds),
                      "wins":sum(d>1e-12 for d in ds),"ties":sum(abs(d)<=1e-12 for d in ds),
                      "losses":sum(d< -1e-12 for d in ds),
                      "same_pair":sum(byid[a][c]["choice_pair"]==byid[b][c]["choice_pair"] for c in common)})
    groups=[]
    for label,lo,hi in [("Fino a 5",0,5),("Da 6 a 16",6,16),("Oltre 16",17,10000)]:
        chosen=[c for c in ids if lo<=byid["M"][c]["num_qubits"]<=hi]
        groups.append({"label":label,"n":len(chosen),"score":{k:stats([byid[k][c]["score"] for c in chosen]) for k in runs}})
    changed=[c for c in ids if len({byid[k][c]["score"] for k in runs})>1]
    changed.sort(key=lambda c:max(byid[k][c]["score"] for k in runs)-min(byid[k][c]["score"] for k in runs),reverse=True)
    for p in [Path(__file__),REPO/"prototipo/data/seal.json",
              REPO/"prototipo/data/rag_examples.jsonl",REPO/"prototipo/prototype/prompting/facts.py",
              REPO/"prototipo/prototype/prompting/minimal.py"]:
        sources[str(p.relative_to(REPO))]=sha(p)
    reference=AREA/"report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/confronto/latex"
    for p in [reference/"verifica.pdf",reference/"risultati.tex"]:sources[str(p.relative_to(REPO))]=sha(p)
    return {"runs":runs,"summary":aggregated,"pairs":pairs,"qubit_groups":groups,"changed_circuits":changed,
            "identical_all":90-len(changed),"metadata":metadata,"generation_settings":settings,
            "audited_attempts":attempts,"sources_sha256":sources,
            "checks":{"same_90_circuits_and_sources":True,"same_wl_retrieval_all_90":True,"summary_present_in_actual_messages":True,
                      "same_live_model_view":True,"same_gguf_and_generation_parameters":True,
                      "tokens_recomputed":True,"facts_revalidated":True},
            "retrieval_ids":retrieval,"preparation":preparation,"example":examples,
            "validation":read(REPO/"archivio/valutazione/validation_dag_wl/esecuzioni/wl_v3/riepilogo.json"),
            "selection":read(REPO/"archivio/valutazione/validation_dag_wl/selezioni/wl_v3/wl_h24.json"),
            "scope":"Analisi descrittiva: h selezionato su 88 validation, confronto finale sugli stessi 90 Test; baseline storica riutilizzata."}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=Path(__file__).parent)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if (args.output/"dati.json").exists():
        raise ValueError("Dati già presenti: scegliere una nuova cartella --output.")
    data=collect();dump(args.output/"dati.json",data)
    tables=args.output/"tabelle";tables.mkdir()
    fields=["k","index","circuit_id","num_qubits","status",*METRICS,"facts_status","facts_verified","facts_total","device","config_id"]
    with (tables/"circuiti.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for k,rows in data["runs"].items():
            for row in rows:w.writerow({"k":k,**row})
    dump(args.output/"provenienza.json",{"checks":data["checks"],"source_sha256":data["sources_sha256"]})
    print(json.dumps({"summary":data["summary"],"pairs":data["pairs"],"groups":data["qubit_groups"],
                      "changed":data["changed_circuits"],"identical_all":data["identical_all"]},indent=2))
if __name__=="__main__":main()

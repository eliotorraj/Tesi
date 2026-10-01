"""Analisi in sola lettura del Test RAG k=5 contro oracle max3. Nessuna compilazione."""
from pathlib import Path
import argparse, csv, hashlib, json, statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
DEFAULT=Path("/home/elio/oracoli_mqt_test/test_max3_v1/analisi/20260929T210523_9df1db2b")
TOL=1e-12
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--oracle",type=Path,default=DEFAULT); ap.add_argument("--output",type=Path,default=HERE/"risultati")
    a=ap.parse_args(); out=a.output
    if (out/"dati.json").exists(): raise SystemExit("Cartella già analizzata: usare --output con una cartella nuova.")
    sources={}
    def read(p):
        sources[str(p)]=sha(p)
        return json.loads(p.read_text(encoding="utf-8"))
    root=a.oracle.parents[1]
    oc=read(root/"contratto.json"); identity=oc["identity"]
    summary=read(a.oracle/"riepilogo.json")
    oracle=read(a.oracle/"oracle_test.json")
    pairs=read(a.oracle/"configurazioni.json")
    prov=read(a.oracle/"provenienza.json")
    base=REPO/"archivio/valutazione/test/risultati/llm_rag"
    contract=read(REPO/"archivio/valutazione/test/preparazione/contratto_congelato.json")
    execution=read(base/"esecuzione.json")
    assert execution["contract_sha256"]==sha(REPO/"archivio/valutazione/test/preparazione/contratto_congelato.json")
    assert identity["source_manifest_sha256"]==contract["source_sha256"]
    assert identity["seeds"]==[0,1,2] and contract["plan"]["qiskit_seed"]==0
    assert summary["identity_sha256"]==oc["identity_sha256"]
    expected={r["circuit_id"]:r for r in identity["circuits"]}
    assert len(expected)==len(oracle)==90 and set(expected)=={r["circuit_id"] for r in oracle}
    assert len(pairs)==5400
    pairmap={(p["circuit_id"],p["device"],p["config_id"]):p for p in pairs}
    assert len(pairmap)==5400
    # Rilegge tutti gli esiti originari e ricostruisce i massimi, non si fida solo dei riepiloghi.
    statuses=Counter(); seeds_by_pair=defaultdict(dict)
    for rel,h in prov.items():
        p=root/rel; b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()==h, str(p)
        r=json.loads(b); statuses[r["status"]]+=1
        key=(r["circuit_id"],r["device"],r["config_id"])
        assert r["seed"] not in seeds_by_pair[key]
        seeds_by_pair[key][r["seed"]]=r
        assert r["source_sha256"]==expected[r["circuit_id"]]["source_sha256"]
        assert r["target_sha256"]==identity["catalog"]["target_sha256"][r["device"]]
    assert len(prov)==16200 and dict(statuses)==summary["statuses"]
    for key,p in pairmap.items():
        raw=seeds_by_pair[key]; assert set(raw)=={0,1,2}
        assert {str(s):r["status"] for s,r in raw.items()}==p["seed_statuses"]
        vals=[r["score"] for r in raw.values() if r["status"]=="success"]
        assert (max(vals) if vals else None)==p["max_score"]
        assert all(p["seed_scores"][str(s)]==(r["score"] if r["status"]=="success" else None) for s,r in raw.items())
    rows=[]
    for o in oracle:
        cid=o["circuit_id"]; folder=base/"circuiti"/cid; r=read(folder/"esito.json")
        result=read(folder/"compilazione/result.json"); job=read(folder/"compilazione/job.json")
        retrieval=read(folder/"retrieval.json")
        assert len(retrieval["records"])==5
        assert r["status"]=="success" and r["method"]=="llm_rag" and r["split"]=="test"
        assert r["source_sha256"]==o["source_sha256"]==expected[cid]["source_sha256"]
        assert sha(folder/"input.qasm")==r["source_sha256"]; sources[str(folder/"input.qasm")]=sha(folder/"input.qasm")
        assert r["score"]==result["score"] and result["validation"]["is_executable_on_target"]
        assert job["decision"]["selected_device"]==r["device"] and job["decision"]["config_id"]==r["config_id"]
        ps=[p for p in pairs if p["circuit_id"]==cid and p["compatible"]]
        assert o["reference_score"]==max(p["max_score"] for p in ps if p["max_score"] is not None)
        assert o["reference_is_exhaustive"]==all(p["all_three_successful"] for p in ps)
        selected=pairmap[cid,r["device"],r["config_id"]]
        assert selected["max_score"] is not None
        score=r["score"]; ref=o["reference_score"]; best=selected["max_score"]
        d=round(ref-score,10); choice=round(ref-best,10); seed=round(best-score,10)
        seed0=selected["seed_scores"]["0"]
        rows.append(dict(circuit_id=cid,num_qubits=expected[cid]["num_qubits"],source_sha256=r["source_sha256"],
            system_score=score,oracle_score=ref,gap=d,gap_pp=100*d,relative_gap_percent=100*d/ref if ref else None,
            status="pari" if abs(d)<=TOL else ("sotto" if d>0 else "sopra"),
            exhaustive=o["reference_is_exhaustive"],device=r["device"],config_id=r["config_id"],
            selected_pair_max3=best,choice_gap=choice,within_pair_gap=seed,
            selected_pair_is_best=abs(choice)<=TOL,selected_pair_complete=selected["all_three_successful"],
            selected_seed_scores=selected["seed_scores"],selected_seed_statuses=selected["seed_statuses"],
            oracle_selected_seed0=seed0,seed0_repeat_difference=round(seed0-score,10) if seed0 is not None else None,
            best_seed0_global=o["best_seed0_score"],gap_vs_seed0_global=round(o["best_seed0_score"]-score,10),
            best_pairs=o["best_pairs"],successful_attempts=sum(len(p["successful_seeds"]) for p in ps),expected_attempts=3*len(ps)))
    rows.sort(key=lambda r:r["circuit_id"])
    for i,r in enumerate(rows,1): r["id"]=i
    def stats(rs):
        return dict(n=len(rs),mean_system=statistics.mean(r["system_score"] for r in rs),
          mean_oracle=statistics.mean(r["oracle_score"] for r in rs),mean_gap=statistics.mean(r["gap"] for r in rs),
          median_gap=statistics.median(r["gap"] for r in rs),max_gap=max(r["gap"] for r in rs),
          statuses=dict(Counter(r["status"] for r in rs)),best_pairs=sum(r["selected_pair_is_best"] for r in rs),
          within_001=sum(abs(r["gap"])<=.01 for r in rs))
    s=stats(rows); s["complete"]=stats([r for r in rows if r["exhaustive"]]); s["partial"]=stats([r for r in rows if not r["exhaustive"]])
    s["selected_pair_complete"]=sum(r["selected_pair_complete"] for r in rows)
    s["seed0_different"]=sum(r["seed0_repeat_difference"] is not None and abs(r["seed0_repeat_difference"])>TOL for r in rows)
    s["seed0_missing"]=sum(r["oracle_selected_seed0"] is None for r in rows)
    s["seed0_max_abs_difference"]=max(abs(r["seed0_repeat_difference"]) for r in rows if r["seed0_repeat_difference"] is not None)
    s["mean_choice_gap"]=statistics.mean(r["choice_gap"] for r in rows)
    s["mean_within_pair_gap"]=statistics.mean(r["within_pair_gap"] for r in rows)
    s["mean_gap_vs_seed0_global"]=statistics.mean(r["gap_vs_seed0_global"] for r in rows)
    data=dict(created_at=datetime.now(timezone.utc).isoformat(),oracle_path=str(a.oracle),rag_path=str(base),
      tolerance=TOL,summary=s,oracle_summary=summary,rows=rows,
      oracle_identity=oc["identity_sha256"],system_contract=execution["contract_sha256"],
      oracle_versions=identity["versions"],model_sha256=execution["server"]["model_sha256"])
    # Le fonti rimangono esterne ai generatori e alle pipeline di decisione.
    assert all(sha(Path(p))==h for p,h in sources.items())
    out.mkdir(parents=True,exist_ok=True)
    save(out/"dati.json",data)
    fields=["id","circuit_id","num_qubits","system_score","oracle_score","gap","gap_pp","relative_gap_percent","status","exhaustive","device","config_id","selected_pair_max3","choice_gap","within_pair_gap","selected_pair_is_best","selected_pair_complete","oracle_selected_seed0","seed0_repeat_difference","best_seed0_global","gap_vs_seed0_global","successful_attempts","expected_attempts","selected_seed_scores","best_pairs"]
    with (out/"confronto_90_circuiti.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],(list,dict)) else r[k] for k in fields})
    save(out/"provenienza.json",dict(source_sha256=sources,oracle_result_hashes_manifest=str(a.oracle/"provenienza.json"),
       oracle_results_verified=len(prov),script_sha256=sha(Path(__file__)),checks={"same_90_sources":True,"retrieval_k5_all_cases":True,"all_oracle_results_hash_checked":True,"all_pair_maxima_recomputed":True,"all_circuit_maxima_recomputed":True,"no_source_changes":True,"quantum_compilations_started":0}))
    print(json.dumps(s,ensure_ascii=False,indent=2))
    print("LARGEST",json.dumps(sorted(rows,key=lambda r:r["gap"],reverse=True)[:5],ensure_ascii=False,indent=2))
if __name__=="__main__": main()

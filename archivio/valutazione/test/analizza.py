"""Rigenera rapporti e confronto dai risultati esistenti; non esegue metodi."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from common import *
from report import generate
import numpy as np

def main():
    runs={}
    for method in METHODS:
        base=AREA/"risultati"/method
        if (base/"esecuzione.json").exists():
            generate(base)
            runs[method]={r["circuit_id"]:r for r in (read(p) for p in (base/"circuiti").glob("*/esito.json"))}
    contracts={read(AREA/"risultati"/m/"esecuzione.json")["contract_sha256"] for m in runs}
    if len(contracts)>1:
        raise ValueError("Contratti diversi: confronto rifiutato.")
    comparisons=[]
    for other in METHODS[1:]:
        left,right=runs.get("llm_rag",{}),runs.get(other,{})
        common=sorted(k for k in left.keys() & right.keys() if left[k]["status"]==right[k]["status"]=="success")
        differences=np.array([left[k]["score"]-right[k]["score"] for k in common])
        ci=None
        if len(common)>1:
            rng=np.random.default_rng(20260901)
            draws=np.mean(rng.choice(differences,size=(10000,len(common)),replace=True),axis=1)
            ci=np.quantile(draws,[0.025,0.975]).tolist()
        comparisons.append({"methods":["llm_rag",other],"common_successes":common,"n":len(common),
            "mean_score_difference":float(differences.mean()) if len(common) else None,
            "paired_bootstrap_95":ci,"interpretation":"descriptive; failures excluded from quality comparison",
            "completed":[len(left),len(right)],"successes":[sum(r["status"]=="success" for r in x.values()) for x in (left,right)]})
    payload={"available_methods":list(runs),"missing_methods":[m for m in METHODS if m not in runs],
             "plan":read(PLAN)["analysis"],"comparisons":comparisons}
    path=AREA/"confronti"/digest(payload)[:16]/"confronto.json"
    if not path.exists():save(path,payload)
    print(path)
if __name__=="__main__":main()

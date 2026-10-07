'Read campaign records without experimental runs.'
import json,sys,hashlib,statistics
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
AREA=HERE.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(AREA/"manifest.json")
contract=read(AREA/"preparazione/contratto_congelato.json")
result={"manifest_sha256":sha(AREA/"manifest.json"),"contract_sha256":sha(AREA/"preparazione/contratto_congelato.json"),
 "contract_keys":list(contract),"methods":{}}
for method in ("llm_rag","mqt_predictor"):
    base=AREA/"risultati"/method
    run=read(base/"esecuzione.json")
    rows=[read(p) for p in sorted((base/"circuiti").glob("*/esito.json"))]
    summary={"run":{k:v for k,v in run.items() if k not in ("code","preflight","server")},
        "server":{k:run.get("server",{}).get(k) for k in ("model_sha256","context_requested","context_reported")} if run.get("server") else None,"n":len(rows),"status":dict(Counter(r["status"] for r in rows)),
        "errors":[r for r in rows if r["status"]!="success"],
        "keys":sorted({k for r in rows for k in r}),
        "stats":{},"devices":dict(Counter(r.get("device") for r in rows)),
        "configurations":dict(Counter(r.get("config_id") for r in rows)),
        "facts":dict(Counter(str(r.get("accepted_with_unverified_facts")) for r in rows))}
    for key in ("score","log_score_unrounded","total_seconds","compilation_seconds","compilation_process_seconds",
        "choice_seconds","rag_seconds","llm_response_seconds","total_tokens","input_tokens","output_tokens","llm_calls","retries"):
        vals=[r[key] for r in rows if isinstance(r.get(key),(int,float))]
        summary["stats"][key]={"n":len(vals),"mean":statistics.mean(vals) if vals else None,
            "median":statistics.median(vals) if vals else None,"sum":sum(vals) if vals else None,
            "min":min(vals) if vals else None,"max":max(vals) if vals else None}
    summary["sample"]=rows[0]
    result["methods"][method]=summary
print(json.dumps(result,indent=2))

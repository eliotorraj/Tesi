"""Esporta una tabella della selezione e conserva i controlli preliminari."""
import csv,json,sys
from pathlib import Path
from uuid import uuid4
area=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(area/"strumenti"))
from common import read,save,sha,now
rows=read(area/"manifest.json")["circuits"]
path=area/"selezione.csv"
if not path.exists():
    with path.open("x",newline="",encoding="utf-8") as f:
        keys=["circuit_id","size_group","qubits","depth","operations","source_ref","source_sha256","upstream_url"]
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for row in rows: writer.writerow({k:row[k] for k in keys})
checks=[]
for p in sorted((area/"preparazione/verifiche").glob("*.json")):
    record=read(p)
    if "ready" not in record: continue
    checks.append({"source":str(p.relative_to(area)),"sha256":sha(p),"record":record})
out=area/"verifiche/registri"/("predisposizione-"+uuid4().hex+".json")
save(out,{"at":now(),"kind":"development_preparation","external_test_started":(area/"risultati").exists(),
    "manifest_sha256":sha(area/"manifest.json"),"counts":{"small":30,"medium":15,"large":5},
    "checks":checks,"technical_tests":{"passed":9,"observed_on":"2026-09-30","note":"Historical observation documented in SVILUPPO.md; this script does not execute tests","synthetic_bell":"success","external_circuits_evaluated":0},
    "earlier_checks":[{"kind":"preflight","methods":["llm_rag","mqt_predictor"],"status":"external_timeout","timeout_seconds":120},
        {"kind":"mqt_artifact_verification","status":"cancelled","reason":"Missing expected ML selector established while scanning large RL archives"}]})
print(out)

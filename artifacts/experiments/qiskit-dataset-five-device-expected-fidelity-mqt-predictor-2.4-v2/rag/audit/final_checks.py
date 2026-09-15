from pathlib import Path
import json,subprocess,sys
root=Path.cwd()
audit=root/"artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/rag/audit"
rag=audit.parent
report=json.loads((rag/"validation_check.json").read_text())
print("Validation:",{k:v for k,v in report.items() if k!="rows"},flush=True)
commands=[
 ("prepare_repeat",["scripts/17_rag_v2.py","prepare"],0),
 ("verify_index",["scripts/17_rag_v2.py","verify"],0),
 ("pretest_audit",["scripts/15_release_test_v2.py"],1),
 ("install_check",["scripts/01_check_install.py","--require-frozen-targets"],0),
]
source=next(iter(sorted((rag.parent/"sources/validation").glob("*.qasm"))))
for backend in ("qdrant","reference"):
 commands.append(("query_"+backend,["scripts/17_rag_v2.py","query","--qasm",str(source),"--backend",backend,"--k","5"],0))
results={}
before={p.name:p.read_bytes() for p in (rag/"index").glob("*.json")}
for name,args,expected in commands:
 result=subprocess.run([sys.executable,*args],cwd=root,text=True,capture_output=True)
 (audit/(name+".log")).write_text(result.stdout+result.stderr)
 results[name]=result.returncode
 print(name, result.returncode,flush=True)
 assert result.returncode==expected,(name,result.stdout[-1000:],result.stderr[-1000:])
assert before=={p.name:p.read_bytes() for p in (rag/"index").glob("*.json")}
q=json.loads((audit/"query_qdrant.log").read_text()); r=json.loads((audit/"query_reference.log").read_text())
assert q["examples"]==r["examples"] and q["prompt_sha256"]==r["prompt_sha256"]
gate=json.loads((audit/"pretest_audit.log").read_text())
print("Gates:",gate["gates"],flush=True)
assert gate["gates"]["rag_qdrant_collection"] and gate["gates"]["rag_validation_pipeline"]
assert not (rag.parent/"manifests/test_release.json").exists()
summary={"commands":results,"repeat_preserves_manifests":True,"query_matches_reference":True,"test_sealed":True,"gates":gate["gates"]}
(audit/"final_checks.json").write_text(json.dumps(summary,indent=2)+"\n")

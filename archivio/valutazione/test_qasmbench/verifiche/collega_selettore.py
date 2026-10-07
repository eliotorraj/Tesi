'Record the explicit choice of the 384-sample selector without changing .venv.'
import hashlib,json,shutil
from pathlib import Path
area=Path(__file__).resolve().parents[1]
origin=area.parent/"test_mqt_esplorativo"
expected="681da87b3d373d27edd9bbabd7424d2b9eb16bf0d18794147fdcdbbe4faa4189"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
model=origin/"runtime/trained_clf_expected_fidelity.joblib"
if sha(model)!=expected: raise ValueError('Selector differs from the selected one')
if (area/"preparazione/contratto_congelato.json").exists(): raise ValueError('Campaign already frozen')
runtime=area/"runtime";runtime.mkdir(exist_ok=True)
for source in (model,model.with_suffix(".metadata.json")):
    target=runtime/source.name
    if target.exists() and sha(target)!=sha(source): raise ValueError('Copy differs; not overwritten')
    if not target.exists(): shutil.copy2(source,target)
plan=json.loads((area/"piano.json").read_text())
exploratory=json.loads((origin/"piano.json").read_text())["exploratory"]
exploratory["publication_status"]="additional-independent-test"
exploratory["waived_requirements"]=["396 training samples","ML frozen-protocol conformity declarations"]
exploratory["selection_authorized"]="User selected current exploratory 384-sample classifier on 2026-09-30"
exploratory["metadata_sha256"]=sha(model.with_suffix(".metadata.json"))
plan["exploratory"]=exploratory
plan["mqt_selector"]="runtime/trained_clf_expected_fidelity.joblib"
(area/"piano.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
gate=(origin/"strumenti/mqt_gate.py").read_text()
(area/"strumenti/mqt_gate.py").write_text(gate)
provenance={"source":str(model),"model_sha256":expected,"metadata_sha256":exploratory["metadata_sha256"],
    "gate_source":str(origin/"strumenti/mqt_gate.py"),"gate_source_sha256":sha(origin/"strumenti/mqt_gate.py"),
    "training_samples":384,"expected_training_samples":396,"excluded_samples":12,
    "successful_compilations":1853,"required_compilations":1878,
    "publication_status":"additional-independent-test","authorized_on":"2026-09-30"}
out=area/"selettore_mqt.json"
if out.exists(): raise ValueError('Selection already recorded')
out.write_text(json.dumps(provenance,indent=2)+"\n")
print(json.dumps(provenance,indent=2))

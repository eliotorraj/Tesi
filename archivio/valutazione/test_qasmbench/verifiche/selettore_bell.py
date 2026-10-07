'Check the selector alone on synthetic Bell, without RL or QASMBench compilations.'
import sys
from pathlib import Path
from uuid import uuid4
area=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(area/"strumenti"))
from common import read,save,sha,now,PLAN
record={"at":now(),"kind":"synthetic_selector_check","source":"Bell synthetic; not external test"}
out=area/"verifiche/registri"/("selettore-bell-"+uuid4().hex+".json")
try:
    from qiskit import QuantumCircuit
    import mqt.predictor.ml.predictor as ml
    selector=area/read(PLAN)["mqt_selector"]
    if sha(selector)!=read(PLAN)["exploratory"]["model_sha256"]: raise ValueError('SHA-256 differs')
    ml.get_path_trained_model=lambda figure_of_merit:selector
    from mqt.predictor.ml import predict_device_for_figure_of_merit
    circuit=QuantumCircuit(2);circuit.h(0);circuit.cx(0,1);circuit.measure_all()
    selected=predict_device_for_figure_of_merit(circuit,figure_of_merit="expected_fidelity")
    record.update(status="success",device=selected.description,model_sha256=sha(selector))
except Exception as exc:
    record.update(status="failure",error=type(exc).__name__,message=str(exc))
save(out,record)
print(record)
raise SystemExit(record["status"]!="success")

'Static checks of downloaded candidates, without scores or models.'
import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from qiskit import QuantumCircuit
area=Path(__file__).resolve().parents[1]
records=[]
for path in sorted((area/"circuiti").rglob("*.qasm")):
    row={"file":str(path.relative_to(area)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    try:
        qc=QuantumCircuit.from_qasm_file(str(path))
        flat=qc.decompose(reps=10)
        measured=set()
        for item in flat.data:
            if item.operation.name in ("reset","if_else","while_loop","for_loop") or getattr(item.operation,"condition",None) is not None:
                raise ValueError('dynamic operations')
            if item.operation.name=="measure": measured.update(item.qubits)
            elif item.operation.name!="barrier" and measured.intersection(item.qubits): raise ValueError('mid-circuit measurements')
        row.update(ok=True,qubits=qc.num_qubits,operations=qc.size())
    except Exception as exc: row.update(ok=False,error=type(exc).__name__,message=str(exc))
    records.append(row)
out=area/"verifiche/registri"/(uuid4().hex+".json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"kind":"static_development_check","at":datetime.now(timezone.utc).isoformat(),"records":records},indent=2)+"\n")
print(json.dumps({"checked":len(records),"failures":[r for r in records if not r["ok"]],"log":str(out)},indent=2))

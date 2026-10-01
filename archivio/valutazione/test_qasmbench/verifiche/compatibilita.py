"""Controlla parsing e maschera hardware senza RAG, inferenza o compilazioni."""
import sys,json
from pathlib import Path
from uuid import uuid4
AREA=Path(__file__).resolve().parents[1]
REPO=AREA.parents[2]
sys.path[:0]=[str(REPO/"prototipo"),str(AREA/"strumenti")]
from common import read,save,now,SOURCE,source_path
from qiskit_dataset.catalog import load_catalog
from prototype.quantum_assistant.adapters.request import QasmRequestParser,RequestSemanticValidator
from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog,HardwareMaskBuilder
from prototype.quantum_assistant.models import UiSubmission
catalog=load_catalog()
hardware=MqtHardwareCatalog(catalog.supported_device_ids,configuration_catalog=catalog).snapshot()
rows=[]
for row in read(SOURCE)["circuits"]:
    result={"circuit_id":row["circuit_id"],"source_sha256":row["source_sha256"]}
    try:
        request=QasmRequestParser().parse(UiSubmission(request_id=row["circuit_id"],user_text="",qasm2=source_path(row).read_text()))
        request=RequestSemanticValidator().normalize(request,hardware)
        mask=HardwareMaskBuilder().filter(request,hardware)
        if not mask.available_device_ids: raise ValueError("Nessun dispositivo compatibile")
        result.update(ok=True,devices=list(mask.available_device_ids),feature_count=len(request.features))
    except Exception as exc:
        result.update(ok=False,error=type(exc).__name__,message=str(exc))
    rows.append(result)
path=AREA/"verifiche/registri"/("compatibilita-"+uuid4().hex+".json")
save(path,{"at":now(),"kind":"static_development_check","records":rows})
print(json.dumps({"checked":len(rows),"failures":[r for r in rows if not r["ok"]],"log":str(path)},indent=2))
raise SystemExit(any(not r["ok"] for r in rows))

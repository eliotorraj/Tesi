"""Controlli MQT isolati; selettore operativo oppure canonico storico."""
from pathlib import Path
import json
import sys
repo=Path(__file__).resolve().parents[3]
archive=repo/"archivio/esperimento_v2"
sys.path.insert(0,str(archive));sys.path.insert(0,str(archive/"scripts"))
import mqt_model_artifacts as models
from mqt_predictor_protocol import *
from mqt.predictor.ml.helper import get_path_trained_model as ml_path
from mqt.predictor.rl.helper import get_path_trained_model as rl_path
sys.path.insert(0,str(repo/"prototipo/addestramento/mqt"))
from deduplica import validate_selection_metadata
errors=[]; report={}
errors.extend(str(x) for x in package_version_mismatches())
for device in FROZEN_DEVICES:
    name=models.rl_model_filename(device)
    canonical=CANONICAL_MODEL_ROOT_V2/"rl"/name
    runtime=rl_path()/name
    for role,path in (("canonical",canonical),("runtime",runtime)):
        details,issues=models.validate_rl_archive(path)
        errors.extend(f"{device}/{role}: {e}" for e in issues)
    if canonical.is_file() and runtime.is_file():
        if file_sha256(canonical)!=file_sha256(runtime):
            errors.append(device+": copie RL diverse")
        metadata,issues=models.validate_rl_training_metadata(canonical.with_suffix(".metadata.json"),
            device_name=device,model_sha256=file_sha256(canonical),expected_max_steps=64,
            expected_num_timesteps=RL_FINAL_TIMESTEPS)
        errors.extend(f"{device}: {e}" for e in issues)
        report[device]={"sha256":file_sha256(canonical),"metadata":metadata}
active=repo/"prototipo/addestramento/mqt/modelli"/models.ML_MODEL_FILENAME
canonical=active if active.exists() else CANONICAL_MODEL_ROOT_V2/"ml"/models.ML_MODEL_FILENAME
runtime=ml_path("expected_fidelity")
for role,path in (("canonical",canonical),("runtime",runtime)):
    details,issues=models.validate_ml_classifier(path)
    errors.extend(f"ML/{role}: {e}" for e in issues)
if canonical.is_file() and runtime.is_file():
    metadata,issues=models.validate_ml_training_metadata(canonical.with_suffix(".metadata.json"),
        model_sha256=file_sha256(canonical))
    errors.extend(issues)
    errors.extend(validate_selection_metadata(metadata, TRAINING_CIRCUITS_V2))
    if file_sha256(canonical)!=file_sha256(runtime):errors.append("Copie ML diverse")
    if metadata.get("source_manifest_sha256")!=file_sha256(SOURCE_MANIFEST_V2):
        errors.append("ML: provenienza corpus non valida")
    for device,details in report.items():
        if metadata.get("rl_models",{}).get(device,{}).get("sha256")!=details["sha256"]:
            errors.append("ML addestrato con RL diversi: "+device)
    report["ML"]={"sha256":file_sha256(canonical),"metadata":metadata,"path":str(canonical)}
print(json.dumps({"models":report,"errors":errors},default=str))
raise SystemExit(bool(errors))

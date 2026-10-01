"""Controlli MQT isolati; selettore operativo oppure canonico storico."""
from pathlib import Path
import json
import sys
from common import REPO as repo
archive=repo/"archivio/esperimento_v2"
sys.path.insert(0,str(archive));sys.path.insert(0,str(archive/"scripts"))
import mqt_model_artifacts as models
from mqt_predictor_protocol import *
from mqt.predictor.ml.helper import get_path_trained_model as ml_path
from mqt.predictor.rl.helper import get_path_trained_model as rl_path
sys.path.insert(0,str(repo/"archivio/valutazione/addestramento/mqt"))
from deduplica import validate_selection_metadata
from validazione_selettore import validate_ml_classifier
errors=[]; report={}
errors.extend(str(x) for x in package_version_mismatches())
for device in FROZEN_DEVICES:
    name=models.rl_model_filename(device)
    canonical=CANONICAL_MODEL_ROOT_V2/"rl"/name
    runtime=rl_path()/name
    print("Verifica RL: "+device, file=sys.stderr, flush=True)
    # Una verifica ZIP basta per copie con SHA-256 uguali; nessun controllo di integrita eliminato.
    if not canonical.is_file() or not runtime.is_file():
        errors.append(device+": copia canonica o runtime mancante")
        continue
    canonical_hash=file_sha256(canonical)
    runtime_hash=file_sha256(runtime)
    if canonical_hash!=runtime_hash:
        errors.append(device+": copie RL diverse")
    details,issues=models.validate_rl_archive(canonical)
    errors.extend(f"{device}/canonical: {e}" for e in issues)
    metadata,issues=models.validate_rl_training_metadata(canonical.with_suffix(".metadata.json"),
        device_name=device,model_sha256=canonical_hash,expected_max_steps=64,
        expected_num_timesteps=RL_FINAL_TIMESTEPS)
    errors.extend(f"{device}: {e}" for e in issues)
    report[device]={"sha256":canonical_hash,"runtime_sha256":runtime_hash,"metadata":metadata}
from collections import Counter
import numpy as np
from common import AREA, PLAN, read, sha
base=repo/"archivio/valutazione/addestramento/mqt/importazioni/portatile_20260924/mqt/finalizzazioni/ripresa300_20260923_230922_168082"
canonical=base/models.ML_MODEL_FILENAME
runtime=AREA/"runtime"/models.ML_MODEL_FILENAME
try:
    metadata=read(canonical.with_suffix(".metadata.json"))
    names=list(map(str,np.load(base/"training_data/names_list_expected_fidelity.npy",allow_pickle=False)))
    samples=np.load(base/"training_data/training_data_expected_fidelity.npy",allow_pickle=True)
    labels=list(map(str,[sample[1] for sample in samples]))
    if len(names)!=len(set(names)) or len(names)!=len(labels) or len(names)!=metadata.get("training_sample_count"):
        errors.append("Campioni ML incoerenti con la copertura dichiarata")
    manifest=read(SOURCE_MANIFEST_V2)
    train={r["circuit_id"]:r for r in manifest["circuits"] if r["split"]=="train"}
    hashes=[]
    for name in names:
        if name not in train:
            errors.append("Campione ML esterno al train: "+name)
            continue
        expected=train[name]["source_sha256"]
        if sha(base/"sources"/(name+".qasm"))!=expected:
            errors.append("Sorgente ML cambiato: "+name)
        hashes.append(expected)
    if len(set(hashes))!=len(hashes):
        errors.append("Campioni ML duplicati per hash")
    if dict(Counter(labels))!=metadata.get("label_distribution"):
        errors.append("Distribuzione delle etichette diversa dai metadati")
    for role,path in (("canonical",canonical),("runtime",runtime)):
        details,issues=validate_ml_classifier(path,observed=labels)
        errors.extend("ML/"+role+": "+e for e in issues)
        if details.get("classes")!=metadata.get("learned_classes"):
            errors.append("Classi ML diverse dai metadati")
    expected_model=read(PLAN)["exploratory"]["model_sha256"]
    if sha(canonical)!=expected_model or sha(runtime)!=expected_model:
        errors.append("Copie ML diverse dal modello esplorativo fissato")
    if sha(runtime.with_suffix(".metadata.json"))!=read(PLAN)["exploratory"]["metadata_sha256"]:
        errors.append("Impronta metadati ML cambiata")
    if read(runtime.with_suffix(".metadata.json"))!=metadata:
        errors.append("Metadati ML runtime diversi")
    _,issues=models.validate_ml_training_metadata(canonical.with_suffix(".metadata.json"),model_sha256=sha(canonical))
    waived=("experiment_id non conforme:","matches_frozen_protocol non conforme:","protocol non conforme:","protocol_version non conforme:")
    errors.extend(e for e in issues if not e.startswith(waived))
    if metadata.get("source_manifest_sha256")!=sha(SOURCE_MANIFEST_V2):
        errors.append("ML: provenienza corpus non valida")
    for device,details in report.items():
        if metadata.get("rl_models",{}).get(device,{}).get("sha256")!=details["sha256"]:
            errors.append("ML addestrato con RL diversi: "+device)
    report["ML"]={"sha256":sha(canonical),"metadata":metadata,"path":str(canonical),
                  "runtime":str(runtime),"observed_training_samples":len(names)}
    report["exploratory"]=read(PLAN)["exploratory"]
except Exception as exc:
    errors.append("Verifica ML: "+type(exc).__name__+": "+str(exc))
print(json.dumps({"models":report,"errors":errors},default=str))
raise SystemExit(bool(errors))

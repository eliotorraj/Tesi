'Isolated MQT checks; operational or historical canonical selector.'
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
    for role,path in (("canonical",canonical),("runtime",runtime)):
        details,issues=models.validate_rl_archive(path)
        errors.extend(f"{device}/{role}: {e}" for e in issues)
    if canonical.is_file() and runtime.is_file():
        if file_sha256(canonical)!=file_sha256(runtime):
            errors.append(device+': RL copies differ')
        metadata,issues=models.validate_rl_training_metadata(canonical.with_suffix(".metadata.json"),
            device_name=device,model_sha256=file_sha256(canonical),expected_max_steps=64,
            expected_num_timesteps=RL_FINAL_TIMESTEPS)
        errors.extend(f"{device}: {e}" for e in issues)
        report[device]={"sha256":file_sha256(canonical),"metadata":metadata}
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
        errors.append('ML samples are inconsistent with declared coverage')
    manifest=read(SOURCE_MANIFEST_V2)
    train={r["circuit_id"]:r for r in manifest["circuits"] if r["split"]=="train"}
    hashes=[]
    for name in names:
        if name not in train:
            errors.append('ML sample outside train: '+name)
            continue
        expected=train[name]["source_sha256"]
        if sha(base/"sources"/(name+".qasm"))!=expected:
            errors.append('ML source changed: '+name)
        hashes.append(expected)
    if len(set(hashes))!=len(hashes):
        errors.append('ML samples contain duplicate hashes')
    if dict(Counter(labels))!=metadata.get("label_distribution"):
        errors.append('Label distribution differs from metadata')
    for role,path in (("canonical",canonical),("runtime",runtime)):
        details,issues=validate_ml_classifier(path,observed=labels)
        errors.extend("ML/"+role+": "+e for e in issues)
        if details.get("classes")!=metadata.get("learned_classes"):
            errors.append('ML classes differ from metadata')
    expected_model=read(PLAN)["exploratory"]["model_sha256"]
    if sha(canonical)!=expected_model or sha(runtime)!=expected_model:
        errors.append('ML copies differ from the fixed exploratory model')
    if read(runtime.with_suffix(".metadata.json"))!=metadata:
        errors.append('Runtime ML metadata differs')
    _,issues=models.validate_ml_training_metadata(canonical.with_suffix(".metadata.json"),model_sha256=sha(canonical))
    waived=('experiment_id does not conform:','matches_frozen_protocol does not conform:','protocol does not conform:','protocol_version does not conform:')
    errors.extend(e for e in issues if not e.startswith(waived))
    if metadata.get("source_manifest_sha256")!=sha(SOURCE_MANIFEST_V2):
        errors.append('ML: invalid corpus provenance')
    for device,details in report.items():
        if metadata.get("rl_models",{}).get(device,{}).get("sha256")!=details["sha256"]:
            errors.append('ML trained with different RL models: '+device)
    report["ML"]={"sha256":sha(canonical),"metadata":metadata,"path":str(canonical),
                  "runtime":str(runtime),"observed_training_samples":len(names)}
    report["exploratory"]=read(PLAN)["exploratory"]
except Exception as exc:
    errors.append('ML check: '+type(exc).__name__+": "+str(exc))
print(json.dumps({"models":report,"errors":errors},default=str))
raise SystemExit(bool(errors))

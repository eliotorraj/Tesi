"""Installa nel runtime corrente i modelli canonici verificati, preservando i precedenti."""
from pathlib import Path
import shutil
import sys
import motore_ml as trainer
from addestra import sync_rl
from mqt_model_artifacts import validate_ml_classifier, validate_ml_training_metadata

def main():
    import portalocker
    with portalocker.Lock(str(trainer.ACTIVE_ROOT/".training.lock"),timeout=0):
        canonical=trainer.CANONICAL_MODELS_DIR/trainer.get_ml_model_path("expected_fidelity").name
        _,errors=validate_ml_classifier(canonical)
        if errors:raise SystemExit(str(errors))
        metadata,errors=validate_ml_training_metadata(canonical.with_suffix(".metadata.json"),
            model_sha256=trainer.file_sha256(canonical))
        if errors:raise SystemExit(str(errors))
        for device in trainer.FROZEN_DEVICES:
            path=trainer.CANONICAL_RL_MODELS_DIR/f"model_expected_fidelity_{device}.zip"
            if metadata.get("rl_models",{}).get(device,{}).get("sha256")!=trainer.file_sha256(path):
                raise SystemExit("Il selettore usa modelli RL diversi: "+device)
        sync_rl(False)
        target=trainer.get_ml_model_path("expected_fidelity")
        if target.exists() and trainer.file_sha256(target)!=trainer.file_sha256(canonical):
            backup=trainer.ACTIVE_ROOT/"precedenti"/trainer.file_sha256(target)/target.name
            backup.parent.mkdir(parents=True,exist_ok=True)
            if not backup.exists():shutil.copy2(target,backup)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(canonical,target)
        print("Selettore installato: "+str(target))
if __name__=="__main__":main()

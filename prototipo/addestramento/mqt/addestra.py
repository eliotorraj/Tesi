"""Avvio ufficiale: verifica i cinque RL e addestra il selettore sui 422 train.

Il motore usa worker spawn senza fork e connessioni BQSKit per circuito.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import motore_ml as trainer

def sync_rl(dry_run):
    import shutil
    from mqt_model_artifacts import validate_rl_archive
    for device in trainer.FROZEN_DEVICES:
        name=f"model_expected_fidelity_{device}.zip"
        source=trainer.CANONICAL_RL_MODELS_DIR/name
        if not source.is_file():
            raise SystemExit("Trasferire il modello RL canonico: "+str(source))
        info,errors=validate_rl_archive(source)
        _,meta_errors=trainer.validate_rl_training_metadata(source.with_suffix(".metadata.json"),
            device_name=device,model_sha256=trainer.file_sha256(source),expected_max_steps=64,
            expected_num_timesteps=trainer.RL_FINAL_TIMESTEPS)
        if errors or meta_errors:
            raise SystemExit(f"Modello RL non conforme: {device}: {errors+meta_errors}")
        target=trainer.get_rl_model_dir()/name
        if target.exists() and trainer.file_sha256(target)==trainer.file_sha256(source):
            continue
        if dry_run:
            print("Da sincronizzare nel runtime: "+name)
            continue
        if target.exists():
            backup=trainer.ACTIVE_ROOT/"precedenti"/trainer.file_sha256(target)/target.name
            backup.parent.mkdir(parents=True,exist_ok=True)
            if not backup.exists():shutil.copy2(target,backup)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)

if __name__=="__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        trainer.parse_args()
    dry="--dry-run" in sys.argv
    if dry:
        sync_rl(True)
        trainer.verify_circuit_directory(trainer.TRAINING_CIRCUITS_V2, allowed_splits=("train",), manifest_path=trainer.SOURCE_MANIFEST_V2)
        # Il controllo completo del trainer richiede le copie runtime.
        missing=[d for d in trainer.FROZEN_DEVICES
                 if not (trainer.get_rl_model_dir()/f"model_expected_fidelity_{d}.zip").is_file()]
        if missing:
            print("I cinque RL canonici sono verificati. L'avvio effettivo li copiera nel runtime.")
            raise SystemExit(0)
    import portalocker
    lock=trainer.ACTIVE_ROOT/".training.lock"
    with portalocker.Lock(str(lock),timeout=0):
        if not dry: sync_rl(False)
        raise SystemExit(trainer.main())

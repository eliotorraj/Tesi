"""Official entry point: verify RL models and train the selector on unique train QASM.

The engine uses spawned workers without fork and per-circuit BQSKit connections.
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
            raise SystemExit('Transfer the canonical RL model: '+str(source))
        info,errors=validate_rl_archive(source)
        _,meta_errors=trainer.validate_rl_training_metadata(source.with_suffix(".metadata.json"),
            device_name=device,model_sha256=trainer.file_sha256(source),expected_max_steps=64,
            expected_num_timesteps=trainer.RL_FINAL_TIMESTEPS)
        if errors or meta_errors:
            raise SystemExit(f'RL model does not match requirements: {device}: {errors + meta_errors}')
        target=trainer.get_rl_model_dir()/name
        if target.exists() and trainer.file_sha256(target)==trainer.file_sha256(source):
            continue
        if dry_run:
            print('To synchronize into the runtime: '+name)
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
        _, selection = trainer.select_unique(trainer.TRAINING_CIRCUITS_V2)
        print(f"Verified train: {selection['source_circuit_count']} sources, {selection['unique_circuit_count']} unique samples, {selection['alias_count']} alias")
        # The full trainer check requires runtime copies.
        missing=[d for d in trainer.FROZEN_DEVICES
                 if not (trainer.get_rl_model_dir()/f"model_expected_fidelity_{d}.zip").is_file()]
        if missing:
            print('Canonical RL models are verified. Execution will copy them into the runtime.')
            raise SystemExit(0)
    import portalocker
    trainer.ACTIVE_ROOT.mkdir(parents=True,exist_ok=True)
    lock=trainer.ACTIVE_ROOT/".training.lock"
    with portalocker.Lock(str(lock),timeout=0):
        if not dry: sync_rl(False)
        raise SystemExit(trainer.main())

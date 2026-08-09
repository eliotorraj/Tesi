"""Train a non-smoke RL compiler for one device and figure of merit."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Any

# Keep the expensive BQSKit passes tractable. MQT also lowers
# max_synthesis_size to 2 in this profile; configure_bqskit_runtime restores
# that single limit because the bundled RL corpus contains 3-qubit gates.
os.environ.setdefault("GITHUB_ACTIONS", "true")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")

import mqt.predictor.rl.actions as predictor_actions
from mqt.bench.targets import get_device
from mqt.predictor.rl import Predictor
from mqt.predictor.rl.helper import get_path_trained_model
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODEL_DIR = PROJECT_ROOT / "artifacts" / "models" / "rl"
_ORIGINAL_BQSKIT_COMPILE = predictor_actions.bqskit_compile


def configure_bqskit_runtime(max_synthesis_size: int) -> None:
    """Override only MQT's BQSKit synthesis limit at runtime.

    MQT's lightweight profile is useful for local training, but it sets
    ``max_synthesis_size=2``. The bundled corpus contains ``ccx`` and
    ``cswap`` gates acting on three qubits, so a BQSKit action otherwise
    aborts PPO. The action lambdas resolve ``bqskit_compile`` when executed;
    replacing that module-level symbol keeps the 22 action IDs and the other
    lightweight settings unchanged and does not modify ``.venv``.
    """

    def compile_with_project_limit(*args: Any, **kwargs: Any) -> Any:
        kwargs["max_synthesis_size"] = max_synthesis_size
        return _ORIGINAL_BQSKIT_COMPILE(*args, **kwargs)

    predictor_actions.bqskit_compile = compile_with_project_limit


def load_model_or_exit(checkpoint: Path, **kwargs: Any) -> MaskablePPO:
    """Load a PPO checkpoint and explain common partial-save corruption."""
    try:
        return MaskablePPO.load(checkpoint, **kwargs)
    except RuntimeError as error:
        if "PytorchStreamReader failed locating file" in str(error):
            raise SystemExit(
                "Checkpoint non caricabile, probabilmente per salvataggio interrotto o incompleto:\n"
                f"  {checkpoint}\n"
                "Riprendi da un checkpoint periodico precedente, per esempio *_2048_steps.zip.\n"
                f"Dettaglio PyTorch: {error}"
            ) from error
        raise


def save_model_atomically(model: MaskablePPO, final_path: Path) -> Path:
    """Avoid leaving a corrupt final checkpoint when saving is interrupted."""
    final_zip = final_path.with_suffix(".zip") if final_path.suffix != ".zip" else final_path
    final_zip.parent.mkdir(parents=True, exist_ok=True)
    temp_path = final_zip.with_name(f".{final_zip.stem}.{os.getpid()}.tmp.zip")
    temp_path.unlink(missing_ok=True)
    model.save(temp_path)
    temp_path.replace(final_zip) #for every Path object, replace is an wrapped version of the raw os.replace function, they still do the same thing
    return final_zip


def install_model_atomically(source: Path, destination: Path) -> None:
    """Install the canonical model into MQT's environment-owned runtime path."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copy2(source, temp)
    os.replace(temp, destination)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Per esempio ibm_falcon_27.")
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default="expected_fidelity")
    parser.add_argument("--timesteps", type=int, default=100_000)
    parser.add_argument("--training-circuits", type=Path, help="Directory QASM personalizzata; usa il dataset incluso se omessa.")
    parser.add_argument("--checkpoint-every", type=int, default=2_048, help="Salva un checkpoint ogni N step.")
    parser.add_argument("--resume-from", type=Path, help="Checkpoint .zip da cui riprendere il training.")
    parser.add_argument(
        "--bqskit-max-synthesis-size",
        type=int,
        default=3,
        help=(
            "Massima arita sintetizzata da BQSKit. Il default 3 gestisce i "
            "gate ccx/cswap del Training set bundled senza modificare .venv."
        ),
    )
    parser.add_argument("--allow-overwrite", action="store_true", help="Consenti di sovrascrivere un modello esistente.")
    return parser.parse_args()


def main() -> int:
    """Train the RL policy using MQT Predictor's production PPO settings."""
    args = parse_args()
    if args.timesteps <= 0:
        raise SystemExit("--timesteps deve essere positivo.")
    if args.checkpoint_every <= 0:
        raise SystemExit("--checkpoint-every deve essere positivo.")
    if not 2 <= args.bqskit_max_synthesis_size <= 8:
        raise SystemExit("--bqskit-max-synthesis-size deve essere compreso tra 2 e 8.")
    if args.training_circuits and not args.training_circuits.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {args.training_circuits}")
    if args.resume_from and not args.resume_from.is_file():
        raise SystemExit(f"Checkpoint non trovato: {args.resume_from}")

    device = get_device(args.device)
    model_name = f"model_{args.metric}_{device.description}"
    filename = f"model_{args.metric}_{device.description}.zip"
    canonical_model = CANONICAL_MODEL_DIR / filename
    runtime_model = get_path_trained_model() / filename
    if canonical_model.exists() and not args.allow_overwrite:
        raise SystemExit(
            f"Il modello canonico esiste gia: {canonical_model}\n"
            "Usa --allow-overwrite solo se vuoi davvero sostituirlo."
        )

    checkpoint_dir = PROJECT_ROOT / "artifacts" / "checkpoints" / "rl" / device.description
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    tensorboard_dir = PROJECT_ROOT / "artifacts" / "logs" / "rl" / model_name
    tensorboard_dir.mkdir(parents=True, exist_ok=True)

    print(f"Training RL: device={device.description}, metrica={args.metric}, target={args.timesteps} step")
    print(f"Checkpoint: {checkpoint_dir} (ogni {args.checkpoint_every} step)")
    configure_bqskit_runtime(args.bqskit_max_synthesis_size)
    print(
        "BQSKit: profilo locale leggero, "
        f"max_synthesis_size={args.bqskit_max_synthesis_size} (override runtime)"
    )
    predictor = Predictor(
        device=device,
        figure_of_merit=args.metric,
        path_training_circuits=args.training_circuits,
    )

    monitor_csv = tensorboard_dir / "monitor.csv"
    predictor.env = Monitor(predictor.env, filename=str(monitor_csv))

    if args.resume_from:
        model = load_model_or_exit(
            args.resume_from,
            env=predictor.env,
            tensorboard_log=str(tensorboard_dir),
        )
        completed_timesteps = model.num_timesteps
        remaining_timesteps = args.timesteps - completed_timesteps
        if remaining_timesteps <= 0:
            raise SystemExit(
                f"Il checkpoint contiene gia {completed_timesteps} step, almeno quanto il target {args.timesteps}."
            )
        print(f"Ripresa da {args.resume_from}: completati={completed_timesteps}, restanti={remaining_timesteps}")
    else:
        model = MaskablePPO(
            MaskableMultiInputActorCriticPolicy,
            predictor.env,
            verbose=2,
            tensorboard_log=str(tensorboard_dir),
            gamma=0.98,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
        )
        remaining_timesteps = args.timesteps

    checkpoint_callback = CheckpointCallback(
        save_freq=args.checkpoint_every,
        save_path=str(checkpoint_dir),
        name_prefix=model_name,
        save_replay_buffer=False,
        save_vecnormalize=False,
        verbose=2,
    )

    try:
        model.learn(
            total_timesteps=remaining_timesteps,
            reset_num_timesteps=args.resume_from is None,
            callback=checkpoint_callback,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        interrupted_path = checkpoint_dir / f"{model_name}_interrupted_{model.num_timesteps}_steps.zip"
        saved_path = save_model_atomically(model, interrupted_path)
        print(f"\nTraining interrotto. Checkpoint di emergenza: {saved_path}")
        return 130

    # The workspace copy is authoritative. qcompile also requires a runtime
    # mirror with this exact filename inside the installed package.
    saved_path = save_model_atomically(model, canonical_model)
    install_model_atomically(saved_path, runtime_model)
    print(f"Modello canonico: {saved_path}")
    print(f"Copia runtime installata: {runtime_model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


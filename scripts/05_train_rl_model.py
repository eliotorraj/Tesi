"""Train a non-smoke RL compiler for one device and figure of merit."""

from __future__ import annotations

import argparse
from contextlib import chdir
from pathlib import Path

from mqt.bench.targets import get_device
from mqt.predictor.rl import Predictor
from mqt.predictor.rl.helper import get_path_trained_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Per esempio ibm_falcon_27.")
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default="expected_fidelity")
    parser.add_argument("--timesteps", type=int, default=100_000)
    parser.add_argument("--training-circuits", type=Path, help="Directory QASM personalizzata; usa il dataset incluso se omessa.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Consenti di sovrascrivere un modello esistente.")
    return parser.parse_args()


def main() -> int:
    """Train the RL policy using MQT Predictor's production PPO settings."""
    args = parse_args()
    if args.timesteps <= 0:
        raise SystemExit("--timesteps deve essere positivo.")
    if args.training_circuits and not args.training_circuits.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {args.training_circuits}")

    device = get_device(args.device)
    model_path = get_path_trained_model() / f"model_{args.metric}_{device.description}.zip"
    if model_path.exists() and not args.allow_overwrite:
        raise SystemExit(f"Il modello esiste già: {model_path}\nUsa --allow-overwrite solo se vuoi davvero sostituirlo.")

    print(f"Training RL reale: device={device.description}, metrica={args.metric}, passi={args.timesteps}")
    predictor = Predictor(
        device=device,
        figure_of_merit=args.metric,
        path_training_circuits=args.training_circuits,
    )
    # Do not set model_name: qcompile only loads model_<metric>_<device>.zip.
    log_dir = PROJECT_ROOT / "artifacts" / "training_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with chdir(log_dir):
        predictor.train_model(timesteps=args.timesteps)
    print(f"Modello salvato: {model_path}")
    print("Esegui subito un backup: python scripts/model_store.py export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

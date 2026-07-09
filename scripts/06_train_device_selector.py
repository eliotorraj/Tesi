"""Generate labels and train the supervised MQT device selector."""

from __future__ import annotations

import argparse
from pathlib import Path

from mqt.bench.targets import get_device
from mqt.predictor.ml import Predictor
from mqt.predictor.ml.helper import get_path_trained_model as get_ml_model_path
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--devices", nargs="+", required=True, help="Device con un modello RL già addestrato.")
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default="expected_fidelity")
    parser.add_argument("--uncompiled-circuits", type=Path, help="Directory QASM; usa il dataset incluso se omessa.")
    parser.add_argument("--compiled-circuits", type=Path, help="Directory di output per i circuiti compilati.")
    parser.add_argument("--timeout", type=int, default=7200, help="Timeout per singola compilazione, in secondi.")
    parser.add_argument("--num-workers", type=int, default=1, help="Worker paralleli per compilazione/dataset; 1 evita conflitti BQSKit.")
    return parser.parse_args()


def main() -> int:
    """Compile training circuits across devices and fit the Random Forest selector."""
    args = parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout deve essere positivo.")
    if args.num_workers <= 0:
        raise SystemExit("--num-workers deve essere positivo.")
    if args.uncompiled_circuits and not args.uncompiled_circuits.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {args.uncompiled_circuits}")

    devices = [get_device(name) for name in args.devices]
    missing_models = []
    for device in devices:
        path = get_rl_model_dir() / f"model_{args.metric}_{device.description}.zip"

        if not path.exists():
            missing_models.append(path)

    if missing_models:
        formatted = "\n".join(f"  - {path}" for path in missing_models)
        raise SystemExit("Mancano i seguenti modelli RL:\n" + formatted)

    compiled_dir = args.compiled_circuits
    if args.uncompiled_circuits and compiled_dir is None:
        compiled_dir = PROJECT_ROOT / "artifacts" / "device_selector" / "compiled"
    if compiled_dir:
        compiled_dir.mkdir(parents=True, exist_ok=True)

    print("Questa fase compila ogni circuito per ogni device e può richiedere molto tempo.")
    print(f"Device: {', '.join(device.description for device in devices)}")
    print(f"Metrica: {args.metric}")
    print(f"Worker: {args.num_workers}")
    predictor = Predictor(
        devices=devices,
        figure_of_merit=args.metric,
    )
    predictor.compile_training_circuits(
        path_uncompiled_circuits=args.uncompiled_circuits,
        path_compiled_circuits=compiled_dir,
        timeout=args.timeout,
        num_workers=args.num_workers,
    )
    predictor.generate_training_data(
        path_uncompiled_circuits=args.uncompiled_circuits,
        path_compiled_circuits=compiled_dir,
        num_workers=args.num_workers,
    )
    predictor.train_random_forest_model()

    model_path = get_ml_model_path(args.metric)
    print(f"Device selector salvato: {model_path}")
    print("Esegui subito un backup: python scripts/model_store.py export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

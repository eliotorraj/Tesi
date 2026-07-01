"""Train tiny deterministic models that validate the MQT Predictor pipeline."""

from __future__ import annotations

import argparse
import time
from contextlib import chdir
from pathlib import Path

from joblib import load
from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.targets import get_device
from mqt.predictor.ml import Predictor as MLPredictor
from mqt.predictor.ml.helper import get_path_trained_model as get_ml_model_path
from mqt.predictor.rl import Predictor as RLPredictor
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir
from qiskit.qasm2 import dump


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEVICE = "ibm_falcon_127"
DEFAULT_METRIC = "expected_fidelity"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default=DEFAULT_METRIC)
    parser.add_argument("--timesteps", type=int, default=100, help="Passi RL; 100 è sufficiente solo per lo smoke test.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in secondi per circuito durante il setup ML.")
    return parser.parse_args()


def create_training_circuits(target_dir: Path) -> None:
    """Create the same small GHZ family used by the upstream integration test."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for qubits in range(2, 8):
        path = target_dir / f"ghz_{qubits}.qasm"
        if path.exists():
            continue
        circuit = get_benchmark("ghz", BenchmarkLevel.ALG, qubits)
        with path.open("w", encoding="utf-8") as stream:
            dump(circuit, stream)


def main() -> int:
    """Train a minimal RL policy and a one-class device selector."""
    args = parse_args()
    if args.timesteps <= 0 or args.timeout <= 0:
        raise SystemExit("--timesteps e --timeout devono essere positivi.")

    print("ATTENZIONE: questi modelli verificano la pipeline, non la qualità del compilatore.")
    print("Il selettore usa un solo device; la scelta supervisionata è quindi volutamente banale.\n")

    device = get_device(args.device)
    run_dir = PROJECT_ROOT / "artifacts" / "smoke"
    uncompiled_dir = run_dir / "uncompiled"
    compiled_dir = run_dir / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    create_training_circuits(uncompiled_dir)

    rl_model_path = get_rl_model_dir() / f"model_{args.metric}_{device.description}.zip"
    ml_model_path = get_ml_model_path(args.metric)

    started = time.perf_counter()
    if rl_model_path.exists():
        print(f"Modello RL già presente, training saltato: {rl_model_path}")
    else:
        print(f"Training RL smoke: device={device.description}, metrica={args.metric}, passi={args.timesteps}")
        predictor = RLPredictor(
            device=device,
            figure_of_merit=args.metric,
            path_training_circuits=uncompiled_dir,
        )
        # Keep the default model_name='model': qcompile relies on this exact naming convention.
        with chdir(run_dir):
            predictor.train_model(timesteps=args.timesteps, test=True)
        if not rl_model_path.exists():
            raise RuntimeError(f"Il training non ha creato il file atteso: {rl_model_path}")
        print(f"Modello RL creato: {rl_model_path}")

    if ml_model_path.exists():
        print(f"Modello ML già presente, training saltato: {ml_model_path}")
        classifier = load(ml_model_path)
        selected_classes = [str(label) for label in classifier.classes_]
        missing_for_existing_selector = [
            get_rl_model_dir() / f"model_{args.metric}_{device_name}.zip"
            for device_name in selected_classes
            if not (get_rl_model_dir() / f"model_{args.metric}_{device_name}.zip").exists()
        ]
        if missing_for_existing_selector:
            formatted = "\n".join(f"  - {path}" for path in missing_for_existing_selector)
            raise RuntimeError(
                "Il selettore ML esistente usa device privi del corrispondente modello RL:\n"
                + formatted
                + "\nLo smoke test non sovrascrive un selettore esistente."
            )
        print("Classi del selettore esistente: " + ", ".join(selected_classes))
    else:
        print("Genero circuiti compilati, label e classificatore supervisionato...")
        selector = MLPredictor(
            devices=[device],
            figure_of_merit=args.metric,
        )
        selector.compile_training_circuits(
            path_uncompiled_circuits=uncompiled_dir,
            path_compiled_circuits=compiled_dir,
            timeout=args.timeout,
            num_workers=1,
        )
        selector.generate_training_data(
            path_uncompiled_circuits=uncompiled_dir,
            path_compiled_circuits=compiled_dir,
            num_workers=1,
        )
        selector.train_random_forest_model()
        if not ml_model_path.exists():
            raise RuntimeError("Il setup del device selector non è terminato correttamente.")
        print(f"Modello ML creato: {ml_model_path}")

    elapsed = time.perf_counter() - started
    print(f"\nSmoke training completato in {elapsed:.1f} s.")
    print("Ora esegui: python scripts/04_test_qcompile.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

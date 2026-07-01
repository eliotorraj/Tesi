"""Verify the Python environment and the MQT Predictor installation."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version


PACKAGES = (
    "mqt.predictor",
    "mqt.bench",
    "qiskit",
    "qiskit-aer",
    "qiskit-ibm-runtime",
    "qiskit-qasm3-import",
    "pytket",
    "pytket-qiskit",
    "sb3-contrib",
    "stable-baselines3",
    "torch",
    "scikit-learn",
    "bqskit",
)


def main() -> int:
    """Print environment information and return a process status code."""
    print("=== Ambiente Python ===")
    print(f"Python:      {platform.python_version()}")
    print(f"Eseguibile:  {sys.executable}")
    print(f"Sistema:     {platform.platform()}")

    missing: list[str] = []
    print("\n=== Pacchetti ===")
    for package in PACKAGES:
        try:
            installed_version = version(package)
        except PackageNotFoundError:
            missing.append(package)
            installed_version = "MANCANTE"
        print(f"{package:<20} {installed_version}")

    if missing:
        print("\nInstallazione incompleta: " + ", ".join(missing), file=sys.stderr)
        return 1

    from mqt.predictor.ml.helper import get_path_trained_model as get_ml_model_path
    from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir

    print("\n=== Artefatti del modello ===")
    print(f"Directory modelli RL: {get_rl_model_dir()}")
    print(f"Modello ML atteso:    {get_ml_model_path('expected_fidelity')}")
    print("\nInstallazione MQT Predictor: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

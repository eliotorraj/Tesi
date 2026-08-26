"""Verify the runtime needed by the direct-Qiskit Dataset pipeline."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version


PACKAGES = (
    "mqt.predictor",
    "mqt.bench",
    "qiskit",
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

    try:
        from mqt.bench.targets import get_device
        from mqt.predictor.ml.helper import create_feature_vector, get_openqasm_gates
        from mqt.predictor.reward import expected_fidelity
        from qiskit import QuantumCircuit, transpile
    except ImportError as error:
        print(f"\nAPI runtime non disponibile: {error}", file=sys.stderr)
        return 1

    del create_feature_vector, expected_fidelity, get_device, get_openqasm_gates
    del QuantumCircuit, transpile
    print("\nAPI Dataset Qiskit diretto: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

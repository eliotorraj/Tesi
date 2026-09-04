"""Esegue i tentativi Qiskit con salvataggio, limite di tempo e ripresa."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, load_catalog
from qiskit_dataset.core import load_manifest
from qiskit_dataset.generation import generate_dataset


def parse_args() -> argparse.Namespace:
    """Legge e controlla le opzioni della generazione."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("pilot", "full"), default="pilot")
    parser.add_argument(
        "--split",
        choices=("train", "validation", "test"),
        help=(
            "Limita l'esecuzione a uno split. Con il catalogo v2 il default "
            "sicuro è train; test richiede il gate di apertura."
        ),
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
    )
    parser.add_argument(
        "--device",
        help="Device MQT Bench; se omesso usa il default del catalogo.",
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=100.0)
    parser.add_argument(
        "--limit-runs",
        type=int,
        help="Esegue solo i primi N tentativi mancanti; utile per smoke test.",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="Riesegue i record failure/timeout gia in cache.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignora la cache per i tentativi selezionati.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra soltanto la cardinalita pianificata.",
    )
    args = parser.parse_args()
    if args.workers <= 0:
        parser.error("--workers deve essere positivo.")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds deve essere positivo.")
    if args.limit_runs is not None and args.limit_runs <= 0:
        parser.error("--limit-runs deve essere positivo.")
    return args


def main() -> None:
    """Mostra il piano oppure genera i tentativi ancora necessari."""
    args = parse_args()
    catalog = load_catalog(args.catalog)
    device_id = catalog.require_device(args.device)
    if args.dry_run:
        selected_split = args.split
        if catalog.experiment_id is not None and selected_split is None:
            selected_split = "train"
        if catalog.experiment_id is not None and selected_split == "test":
            from scripts.mqt_predictor_protocol import validate_test_release_record

            try:
                validate_test_release_record()
            except (FileNotFoundError, ValueError) as error:
                raise SystemExit(str(error)) from error
        manifest = load_manifest(
            args.scope,
            str(catalog.objective["name"]),
            device_id,
            catalog.experiment_id,
        )
        selected_circuits = [
            circuit
            for circuit in manifest["circuits"]
            if selected_split is None or circuit["split"] == selected_split
        ]
        compatible_circuits = [
            circuit
            for circuit in selected_circuits
            if circuit.get("device_compatibility", {}).get("compatible", True)
        ]
        print(
            json.dumps(
                {
                    "scope": args.scope,
                    "experiment_id": catalog.experiment_id,
                    "split": selected_split,
                    "device_id": device_id,
                    "circuits": len(selected_circuits),
                    "compatible_circuits": len(compatible_circuits),
                    "configurations": len(catalog.configurations),
                    "seeds": list(catalog.seeds),
                    "attempts_planned": (
                        len(compatible_circuits)
                        * len(catalog.configurations)
                        * len(catalog.seeds)
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    status = generate_dataset(
        args.scope,
        catalog,
        workers=args.workers,
        timeout_seconds=args.timeout_seconds,
        limit_runs=args.limit_runs,
        retry_failures=args.retry_failures,
        force=args.force,
        device_id=device_id,
        split=args.split,
    )
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

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
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
    )
    parser.add_argument(
        "--device",
        help="Device MQT Bench; se omesso usa il default del catalogo.",
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
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
        manifest = load_manifest(
            args.scope,
            str(catalog.objective["name"]),
            device_id,
        )
        print(
            json.dumps(
                {
                    "scope": args.scope,
                    "device_id": device_id,
                    "circuits": len(manifest["circuits"]),
                    "compatible_circuits": manifest["counts"].get(
                        "compatible_circuits",
                        len(manifest["circuits"]),
                    ),
                    "configurations": len(catalog.configurations),
                    "seeds": list(catalog.seeds),
                    "attempts_planned": manifest["counts"]["attempts_planned"],
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
    )
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

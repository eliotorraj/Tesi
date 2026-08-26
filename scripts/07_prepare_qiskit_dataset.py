"""Prepare deterministic pilot/full circuit splits for the Qiskit Dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, load_catalog
from qiskit_dataset.core import prepare_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("pilot", "full", "both"),
        default="both",
        help="Pilot da 10 circuiti, corpus completo da 600, oppure entrambi.",
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
    parser.add_argument(
        "--source-circuits",
        type=Path,
        help="Override opzionale della cartella con i 600 QASM MQT.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog)
    device_id = catalog.require_device(args.device)
    scopes = ("pilot", "full") if args.scope == "both" else (args.scope,)
    result = {}
    for scope in scopes:
        manifest = prepare_dataset(
            scope,
            catalog,
            source=args.source_circuits,
            device_id=device_id,
        )
        result[scope] = {
            "manifest_id": manifest["manifest_id"],
            "counts": manifest["counts"],
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

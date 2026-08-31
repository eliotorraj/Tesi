"""Unisce le viste dei dispositivi in un Dataset generale senza modificarle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.aggregation import aggregate_device_datasets
from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, load_catalog


def parse_args() -> argparse.Namespace:
    """Legge e controlla le opzioni dell'aggregazione generale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("pilot", "full"), default="pilot")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
    )
    parser.add_argument(
        "--devices",
        nargs="+",
        help=(
            "Subset esplicito; se omesso aggrega tutti i mini-Dataset "
            "completi disponibili."
        ),
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--require-all-supported",
        action="store_true",
        help="Fallisce se manca anche uno dei device supportati dal catalogo.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Valida e calcola le statistiche senza scrivere la vista globale.",
    )
    args = parser.parse_args()
    if not 1 <= args.top_k <= 3:
        parser.error("--top-k deve essere compreso tra 1 e 3.")
    return args


def main() -> None:
    """Controlla o costruisce la vista generale e mostra le statistiche."""
    args = parse_args()
    catalog = load_catalog(args.catalog)
    statistics = aggregate_device_datasets(
        args.scope,
        catalog,
        top_k=args.top_k,
        device_ids=args.devices,
        require_all_supported=args.require_all_supported,
        write=not args.check_only,
    )
    print(json.dumps(statistics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

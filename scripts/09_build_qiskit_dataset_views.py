"""Costruisce gli aggregati e gli esempi RAG destinati all'addestramento."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, load_catalog
from qiskit_dataset.views import build_dataset_views


def parse_args() -> argparse.Namespace:
    """Legge le opzioni usate per costruire le viste del Dataset."""
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
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.top_k <= 3:
        parser.error("--top-k deve essere compreso tra 1 e 3.")
    return args


def main() -> None:
    """Costruisce le viste del dispositivo e ne mostra le statistiche."""
    args = parse_args()
    catalog = load_catalog(args.catalog)
    device_id = catalog.require_device(args.device)
    statistics = build_dataset_views(
        args.scope,
        catalog,
        top_k=args.top_k,
        device_id=device_id,
    )
    print(json.dumps(statistics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

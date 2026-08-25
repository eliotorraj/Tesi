"""Build configuration aggregates and train-only RAG JSONL."""

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("pilot", "full"), default="pilot")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
    )
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k deve essere positivo.")
    return args


def main() -> None:
    args = parse_args()
    statistics = build_dataset_views(
        args.scope,
        load_catalog(args.catalog),
        top_k=args.top_k,
    )
    print(json.dumps(statistics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

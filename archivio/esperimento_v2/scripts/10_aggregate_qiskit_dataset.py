'Merge device views into a global Dataset without changing them.'

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
    'Read and check global aggregation options.'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("pilot", "full"), default="full")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help='v2 catalog; for historical data, specify the catalog under archivio/protocollo_v1/configs/.',
    )
    parser.add_argument(
        "--devices",
        nargs="+",
        help=(
            'Explicit subset; otherwise aggregate all available complete mini-Datasets.'
        ),
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--require-all-supported",
        action="store_true",
        help='Fail if any catalog-supported device is missing.',
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help='Validate and compute statistics without writing the global view.',
    )
    args = parser.parse_args()
    if not 1 <= args.top_k <= 3:
        parser.error('--top-k must be between 1 and 3.')
    return args


def main() -> None:
    'Check or build the global view and show statistics.'
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

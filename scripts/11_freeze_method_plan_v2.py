"""Congela il piano dei metodi e le estrazioni casuali senza leggere gli score."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.experiment_v2 import (
    atomic_json_write,
    build_method_plan,
    device_capacities,
    load_json,
    source_manifest,
    validate_method_configuration,
)
from scripts.mqt_predictor_protocol import METHOD_PLAN_DIR_V2

DEFAULT_CATALOG = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_method_configuration(require_frozen=False)
    catalog = load_catalog(args.catalog)
    manifest = source_manifest()
    plan = build_method_plan(
        args.split,
        catalog,
        manifest=manifest,
        capacities=device_capacities(),
    )
    output = args.output or METHOD_PLAN_DIR_V2 / f"{args.split}_method_plan.json"
    if output.exists():
        if load_json(output) != plan:
            raise SystemExit(
                f"Il piano esistente è diverso e non verrà sovrascritto: {output}"
            )
        print(f"Piano già congelato e identico: {output}")
    else:
        atomic_json_write(output, plan)
        print(f"Piano congelato: {output}")
    print(
        json.dumps(
            {
                "split": args.split,
                "circuit_count": plan["circuit_count"],
                "random_draw_count": sum(
                    len(row["repetitions"])
                    for row in plan["random_selection"]["rows"]
                ),
                "plan_sha256": plan["plan_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

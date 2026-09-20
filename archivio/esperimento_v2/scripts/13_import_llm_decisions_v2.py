"""Valida e congela decisioni LLM terminali senza consultare gli score."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.experiment_v2 import (
    LLM_METHOD_IDS,
    atomic_jsonl_write,
    device_capacities,
    load_json,
    load_jsonl,
    source_manifest,
    validate_llm_decisions,
    validate_method_configuration,
    validate_method_plan,
)
from scripts.mqt_predictor_protocol import (
    METHOD_CONFIG_V2,
    METHOD_PLAN_DIR_V2,
    METHOD_RESULTS_DIR_V2,
    file_sha256,
    validate_test_release_record,
)

DEFAULT_CATALOG = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--method", choices=LLM_METHOD_IDS, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split == "test":
        validate_test_release_record()
    config = validate_method_configuration(require_frozen=True)
    catalog = load_catalog(args.catalog)
    manifest = source_manifest()
    capacities = device_capacities()
    plan = load_json(METHOD_PLAN_DIR_V2 / f"{args.split}_method_plan.json")
    validate_method_plan(
        plan,
        split=args.split,
        catalog=catalog,
        manifest=manifest,
        capacities=capacities,
    )
    validated = validate_llm_decisions(
        load_jsonl(args.input),
        method_id=args.method,
        split=args.split,
        catalog=catalog,
        manifest=manifest,
        capacities=capacities,
        method_config=config,
        method_config_sha256=file_sha256(METHOD_CONFIG_V2),
    )
    output = args.output or (
        METHOD_RESULTS_DIR_V2
        / args.split
        / f"{args.method}_decisions.jsonl"
    )
    if output.exists() and load_jsonl(output) != validated:
        raise SystemExit(
            f"Decisioni già congelate e diverse; file non modificato: {output}"
        )
    if not output.exists():
        atomic_jsonl_write(output, validated)
    print(f"Decisioni congelate: {output} ({len(validated)} circuiti)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

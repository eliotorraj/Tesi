'Freeze the method plan and random draws without reading scores.'

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
    stable_sha256,
    validate_method_configuration,
)
from scripts.mqt_predictor_protocol import METHOD_PLAN_DIR_V2, TEST_RELEASE_RECORD, file_sha256

DEFAULT_CATALOG = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--align-execution-policy",
        action="store_true",
        help='Archive the 300s/2 plan and realign it to 100s/6 without changing draws.',
    )
    return parser.parse_args()


def freeze_method_plan(
    output: Path,
    plan: dict,
    *,
    align_execution_policy: bool = False,
    release_record: Path = TEST_RELEASE_RECORD,
) -> str:
    'Save the plan or realign only the earlier policy while preserving it.'
    previous = load_json(output) if output.exists() else None
    if previous == plan:
        return 'already frozen and identical'
    if release_record.exists():
        raise ValueError('Test is already open: the plan cannot change.')
    if previous is None:
        atomic_json_write(output, plan)
        return "congelato"
    if not align_execution_policy:
        raise ValueError(f'The existing plan differs and will not be overwritten: {output}')

    old_core = {key: value for key, value in previous.items() if key != "plan_sha256"}
    new_core = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if (
        previous.get("plan_sha256") != stable_sha256(old_core)
        or plan.get("plan_sha256") != stable_sha256(new_core)
    ):
        raise ValueError('Invalid plan hash: realignment refused.')
    if (
        old_core.pop("qiskit_execution_policy", None)
        != {"timeout_seconds": 300, "workers": 2}
        or new_core.pop("qiskit_execution_policy", None)
        != {"timeout_seconds": 100, "workers": 6}
        or old_core != new_core
    ):
        raise ValueError(
            'Only the 300s/2 to 100s/6 transition is allowed; draws, circuits and other parameters must remain identical.'
        )

    previous_bytes = output.read_bytes()
    previous_file_hash = file_sha256(output)
    history = output.parent / "history"
    archive = history / f"{output.stem}.{previous['plan_sha256']}.json"
    history.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        if archive.read_bytes() != previous_bytes:
            raise ValueError(f'Earlier archive differs: {archive}')
    else:
        with archive.open("xb") as stream:
            stream.write(previous_bytes)
    atomic_json_write(output, plan)
    atomic_json_write(
        history / f"{output.stem}.{plan['plan_sha256']}.alignment.json",
        {
            "schema_version": "1.0.0",
            "reason": 'Alignment with the approved Qiskit policy: 100 seconds, 6 workers.',
            "previous_plan_sha256": previous["plan_sha256"],
            "current_plan_sha256": plan["plan_sha256"],
            "previous_file_sha256": previous_file_hash,
            "current_file_sha256": file_sha256(output),
            "archived_plan": archive.name,
            "random_selection_unchanged": previous["random_selection"] == plan["random_selection"],
            "test_released": False,
        },
    )
    return 'aligned to 100s/6; previous plan archived'


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
    try:
        status = freeze_method_plan(
            output, plan, align_execution_policy=args.align_execution_policy,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f'Plan {status}: {output}')
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

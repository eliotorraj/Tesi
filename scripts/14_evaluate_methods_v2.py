"""Valuta tutti i metodi sullo stesso split dopo avere sigillato le scelte."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import dataset_scope_root
from qiskit_dataset.experiment_v2 import (
    LLM_METHOD_IDS,
    atomic_json_write,
    atomic_jsonl_write,
    device_capacities,
    evaluate_common_methods,
    load_json,
    load_jsonl,
    source_manifest,
    stable_sha256,
    summarize_results,
    validate_llm_decisions,
    validate_method_configuration,
    validate_method_plan,
    validate_qcompile_runs,
)
from scripts.mqt_predictor_protocol import (
    EXPERIMENT_ID,
    METHOD_CONFIG_V2,
    METHOD_PLAN_DIR_V2,
    METHOD_RESULTS_DIR_V2,
    file_sha256,
    validate_test_release_record,
)
from scripts.mqt_model_artifacts import validate_model_set

DEFAULT_CATALOG = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--scope", choices=("full",), default="full")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split == "test":
        validate_test_release_record()
    method_config = validate_method_configuration(require_frozen=True)
    catalog = load_catalog(args.catalog)
    manifest = source_manifest()
    capacities = device_capacities()
    plan_path = METHOD_PLAN_DIR_V2 / f"{args.split}_method_plan.json"
    plan = load_json(plan_path)
    validate_method_plan(
        plan,
        split=args.split,
        catalog=catalog,
        manifest=manifest,
        capacities=capacities,
    )

    # Le decisioni e gli esiti qcompile vengono validati prima di aprire la
    # matrice Qiskit che contiene l'oracle.
    decision_paths = {
        method_id: METHOD_RESULTS_DIR_V2
        / args.split
        / f"{method_id}_decisions.jsonl"
        for method_id in LLM_METHOD_IDS
    }
    decisions = {
        method_id: validate_llm_decisions(
            load_jsonl(path),
            method_id=method_id,
            split=args.split,
            catalog=catalog,
            manifest=manifest,
            capacities=capacities,
            method_config=method_config,
            method_config_sha256=file_sha256(METHOD_CONFIG_V2),
        )
        for method_id, path in decision_paths.items()
    }
    qcompile_path = (
        METHOD_RESULTS_DIR_V2 / args.split / "mqt_qcompile_runs.jsonl"
    )
    model_report, model_errors = validate_model_set(expected_max_steps=64)
    if model_errors:
        raise SystemExit(
            "Modelli MQT non conformi alla valutazione:\n  - "
            + "\n  - ".join(model_errors)
        )
    model_hashes = {
        name: item["canonical_sha256"]
        for name, item in model_report.items()
    }
    qcompile = validate_qcompile_runs(
        load_jsonl(qcompile_path),
        split=args.split,
        manifest=manifest,
        expected_model_set_sha256=stable_sha256(model_hashes),
    )

    scope_root = dataset_scope_root(
        "expected_fidelity",
        args.scope,
        experiment_id=EXPERIMENT_ID,
    )
    global_root = scope_root / "global"
    runs_path = global_root / "qiskit_runs.jsonl"
    summaries_path = global_root / "qiskit_configuration_aggregates.jsonl"
    results = evaluate_common_methods(
        split=args.split,
        catalog=catalog,
        manifest=manifest,
        plan=plan,
        capacities=capacities,
        qiskit_runs=load_jsonl(runs_path),
        qiskit_summaries=load_jsonl(summaries_path),
        llm_decisions=decisions,
        qcompile_runs=qcompile,
        method_config_sha256=file_sha256(METHOD_CONFIG_V2),
    )
    fingerprints = {
        "catalog": file_sha256(args.catalog),
        "method_config": file_sha256(METHOD_CONFIG_V2),
        "method_plan": file_sha256(plan_path),
        "qcompile_runs": file_sha256(qcompile_path),
        "qiskit_runs": file_sha256(runs_path),
        "qiskit_summaries": file_sha256(summaries_path),
        **{
            f"{method_id}_decisions": file_sha256(path)
            for method_id, path in decision_paths.items()
        },
    }
    summary = summarize_results(
        results,
        split=args.split,
        input_fingerprints=fingerprints,
    )
    output_dir = args.output_dir or METHOD_RESULTS_DIR_V2 / args.split / "evaluation"
    result_path = output_dir / "method_results.jsonl"
    summary_path = output_dir / "evaluation_summary.json"
    if not args.overwrite and (result_path.exists() or summary_path.exists()):
        raise SystemExit(
            f"Output già presente: {output_dir}. Usa --overwrite solo per una "
            "rigenerazione dagli stessi input congelati."
        )
    atomic_jsonl_write(result_path, results)
    atomic_json_write(summary_path, summary)
    print(f"Risultati comuni: {result_path}")
    print(f"Riepilogo: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

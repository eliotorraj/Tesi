"""Verifica tutti i prerequisiti e, su richiesta, apre lo split test."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_model_artifacts import validate_model_set
from mqt_predictor_protocol import (
    CANONICAL_MODEL_ROOT_V2,
    COMPILATION_TIMEOUT_SECONDS,
    EXPERIMENT_ID,
    EXPERIMENT_ROOT,
    EXPECTED_PACKAGE_VERSIONS,
    FROZEN_TARGET_SHA256,
    METHOD_CONFIG_V2,
    METHOD_PLAN_DIR_V2,
    METHOD_RESULTS_DIR_V2,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    SOURCE_MANIFEST_V2,
    TEST_RELEASE_RECORD,
    TRAINING_CIRCUITS_V2,
    VALIDATION_CIRCUITS_V2,
    assert_records_belong_to_split,
    file_sha256,
    installed_package_versions,
    package_version_mismatches,
    validate_test_release_record,
    verify_circuit_directory,
)
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import dataset_scope_root
from qiskit_dataset.experiment_v2 import (
    atomic_json_write,
    device_capacities,
    load_json,
    load_jsonl,
    source_manifest,
    validate_method_configuration,
    validate_method_plan,
    validate_qiskit_matrix,
)

CATALOG_PATH = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"
QCOMPILE_CANARY = (
    EXPERIMENT_ROOT / "logs" / "qcompile" / "validation_report.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="Scrive il record di apertura soltanto se ogni gate è superato.",
    )
    parser.add_argument("--output", type=Path, default=TEST_RELEASE_RECORD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        try:
            record = validate_test_release_record(args.output)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        print(f"Test già aperto con record valido: {args.output}")
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0

    gates: dict[str, bool] = {}
    details: dict[str, Any] = {}

    def check(name: str, function: Callable[[], Any]) -> Any | None:
        try:
            value = function()
        except Exception as error:
            gates[name] = False
            details[name] = f"{type(error).__name__}: {error}"
            return None
        gates[name] = True
        details[name] = value if value is not None else "ok"
        return value

    check(
        "software_versions",
        lambda: (
            installed_package_versions()
            if not package_version_mismatches()
            else (_ for _ in ()).throw(
                ValueError(str(package_version_mismatches()))
            )
        ),
    )
    capacities = check("frozen_targets", device_capacities)
    manifest = check("source_manifest", source_manifest)
    check(
        "training_partition",
        lambda: verify_circuit_directory(
            TRAINING_CIRCUITS_V2,
            allowed_splits=("train",),
        ),
    )
    check(
        "validation_partition",
        lambda: verify_circuit_directory(
            VALIDATION_CIRCUITS_V2,
            allowed_splits=("validation",),
        ),
    )
    catalog = check("catalog", lambda: load_catalog(CATALOG_PATH))
    method_config = check(
        "method_configuration",
        lambda: validate_method_configuration(require_frozen=True),
    )

    plans: dict[str, dict[str, Any]] = {}
    if manifest is not None and catalog is not None and capacities is not None:
        for split in ("validation", "test"):
            plan_path = METHOD_PLAN_DIR_V2 / f"{split}_method_plan.json"

            def check_plan(
                path: Path = plan_path,
                selected_split: str = split,
            ) -> dict[str, Any]:
                plan = load_json(path)
                validate_method_plan(
                    plan,
                    split=selected_split,
                    catalog=catalog,
                    manifest=manifest,
                    capacities=capacities,
                )
                plans[selected_split] = plan
                return {
                    "path": str(path),
                    "sha256": file_sha256(path),
                    "plan_sha256": plan["plan_sha256"],
                }

            check(f"{split}_method_plan", check_plan)
    else:
        gates["validation_method_plan"] = False
        gates["test_method_plan"] = False
        details["validation_method_plan"] = "Prerequisiti mancanti."
        details["test_method_plan"] = "Prerequisiti mancanti."

    scope_root = dataset_scope_root(
        "expected_fidelity",
        "full",
        experiment_id=EXPERIMENT_ID,
    )
    global_root = scope_root / "global"
    runs_path = global_root / "qiskit_runs.jsonl"
    summaries_path = global_root / "qiskit_configuration_aggregates.jsonl"
    rag_path = global_root / "rag_examples.jsonl"

    def check_qiskit_validation() -> dict[str, Any]:
        if manifest is None or catalog is None or capacities is None:
            raise ValueError("Prerequisiti mancanti.")
        runs = load_jsonl(runs_path)
        summaries = load_jsonl(summaries_path)
        if any(record.get("split") == "test" for record in [*runs, *summaries]):
            raise ValueError("Sono già presenti risultati test prima dell'apertura.")
        run_index, summary_index = validate_qiskit_matrix(
            runs,
            summaries,
            split="validation",
            catalog=catalog,
            manifest=manifest,
            capacities=capacities,
        )
        return {
            "validation_runs": len(run_index),
            "validation_summaries": len(summary_index),
        }

    check("qiskit_validation_matrix", check_qiskit_validation)

    def check_rag() -> dict[str, Any]:
        if manifest is None:
            raise ValueError("Manifest sorgente non disponibile.")
        records = load_jsonl(rag_path)
        assert_records_belong_to_split(
            records,
            allowed_split="train",
            manifest=manifest,
        )
        hashes = [
            str(record["retrieval_input"]["circuit"]["source_sha256"])
            for record in records
        ]
        if len(hashes) != len(set(hashes)):
            raise ValueError("L'indice RAG contiene alias SHA-256 duplicati.")
        return {"records": len(records), "unique_source_sha256": len(set(hashes))}

    check("rag_train_only", check_rag)
    model_report = check(
        "mqt_models",
        lambda: (
            lambda value: value[0]
            if not value[1]
            else (_ for _ in ()).throw(ValueError("; ".join(value[1])))
        )(validate_model_set(expected_max_steps=64)),
    )

    def check_canary() -> dict[str, Any]:
        report = load_json(QCOMPILE_CANARY)
        results = report.get("results")
        if (
            report.get("status") != "success"
            or not isinstance(results, list)
            or len(results) != 6
            or not all(item.get("strict_success") is True for item in results)
            or sum(item.get("mode") == "qcompile" for item in results) != 1
            or report.get("limits")
            != {
                "max_steps": 64,
                "timeout_seconds": COMPILATION_TIMEOUT_SECONDS,
            }
        ):
            raise ValueError("Il report non prova cinque canary RL e un qcompile.")
        return {"path": str(QCOMPILE_CANARY), "sha256": file_sha256(QCOMPILE_CANARY)}

    check("qcompile_canary", check_canary)

    validation_dir = METHOD_RESULTS_DIR_V2 / "validation" / "evaluation"
    validation_summary_path = validation_dir / "evaluation_summary.json"
    validation_results_path = validation_dir / "method_results.jsonl"

    def check_validation_evaluation() -> dict[str, Any]:
        summary = load_json(validation_summary_path)
        if (
            summary.get("experiment_id") != EXPERIMENT_ID
            or summary.get("protocol_version") != PROTOCOL_VERSION
            or summary.get("split") != "validation"
            or summary.get("status") != "complete"
            or summary.get("circuit_count") != 88
        ):
            raise ValueError("Valutazione validation non completa o fuori protocollo.")
        if not validation_results_path.is_file():
            raise FileNotFoundError(validation_results_path)
        return {
            "summary_sha256": file_sha256(validation_summary_path),
            "results_sha256": file_sha256(validation_results_path),
        }

    check("validation_evaluation", check_validation_evaluation)

    if manifest is not None:
        details["source_manifest"] = {
            "sha256": file_sha256(SOURCE_MANIFEST_V2),
            "corpus_sha256": manifest["corpus_sha256"],
            "counts": manifest["counts"],
        }
    if catalog is not None:
        details["catalog"] = {
            "catalog_id": catalog.catalog_id,
            "devices": list(catalog.supported_device_ids),
            "configurations": len(catalog.configurations),
            "seeds": list(catalog.seeds),
            "execution_policy": dict(catalog.execution_policy),
        }

    ready = bool(gates) and all(gates.values())
    audit = {
        "schema_version": "1.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
        "release_ready": ready,
        "gates": gates,
        "details": details,
    }
    print(json.dumps(audit, indent=2, sort_keys=True, default=str))
    if not args.release:
        return 0 if ready else 1
    if not ready:
        raise SystemExit("Test non aperto: almeno un gate non è stato superato.")

    frozen_paths = [
        CATALOG_PATH,
        METHOD_CONFIG_V2,
        SOURCE_MANIFEST_V2,
        METHOD_PLAN_DIR_V2 / "validation_method_plan.json",
        METHOD_PLAN_DIR_V2 / "test_method_plan.json",
        QCOMPILE_CANARY,
        rag_path,
        validation_summary_path,
        validation_results_path,
    ]
    frozen_paths.extend(
        path
        for path in CANONICAL_MODEL_ROOT_V2.rglob("*")
        if path.is_file()
    )
    frozen_files = {
        path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix(): file_sha256(path)
        for path in sorted(frozen_paths)
    }
    record = {
        "schema_version": "1.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "status": "released",
        "released_at": datetime.now(UTC).isoformat(),
        "source_manifest_sha256": file_sha256(SOURCE_MANIFEST_V2),
        "target_sha256": FROZEN_TARGET_SHA256,
        "software": EXPECTED_PACKAGE_VERSIONS,
        "gates": gates,
        "frozen_files": frozen_files,
    }
    atomic_json_write(args.output, record)
    validate_test_release_record(args.output)
    print(f"Test aperto: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

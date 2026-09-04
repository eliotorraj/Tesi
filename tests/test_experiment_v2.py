from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import SCHEMA_VERSION, make_run_id, stable_id
from qiskit_dataset.experiment_v2 import (
    build_method_plan,
    split_circuits,
    summarize_results,
    validate_method_configuration,
    validate_qcompile_runs,
    validate_qiskit_matrix,
)
from qiskit_dataset.generation import generate_dataset
from qiskit_dataset.views import AGGREGATE_SCHEMA_VERSION
from scripts.mqt_predictor_protocol import (
    EXPERIMENT_ID,
    EXPECTED_PACKAGE_VERSIONS,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    SOURCE_MANIFEST_V2,
    assert_records_belong_to_split,
    file_sha256,
    semantic_circuit_sha256,
    validate_test_release_record,
    verify_circuit_directory,
    verify_source_manifest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_CATALOG = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"
METHOD_CONFIG = PROJECT_ROOT / "configs" / "experiment_methods_v2.json"
QASM_A = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
x q[0];
"""
QASM_A_FORMATTED = """OPENQASM 2.0;
include "qelib1.inc";
qreg renamed[1];
barrier renamed;
x renamed[0];
"""
QASM_B = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];
"""


class ExperimentV2Tests(unittest.TestCase):
    def test_committed_corpus_has_frozen_counts_and_no_cross_split_leakage(self) -> None:
        manifest = verify_source_manifest()
        self.assertEqual(manifest["counts"]["circuits"], 600)
        self.assertEqual(
            manifest["counts"]["by_split"],
            {"train": 422, "validation": 88, "test": 90},
        )
        for field in ("source_sha256", "semantic_sha256", "leakage_group"):
            split_by_value: dict[str, set[str]] = {}
            for record in manifest["circuits"]:
                split_by_value.setdefault(str(record[field]), set()).add(
                    str(record["split"])
                )
            self.assertFalse(
                {
                    value: splits
                    for value, splits in split_by_value.items()
                    if len(splits) > 1
                }
            )

    def test_semantic_duplicate_across_splits_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            train = root / "train.qasm"
            validation = root / "validation.qasm"
            test = root / "test.qasm"
            train.write_text(QASM_A, encoding="utf-8")
            validation.write_text(QASM_B, encoding="utf-8")
            test.write_text(QASM_A_FORMATTED, encoding="utf-8")
            self.assertEqual(
                semantic_circuit_sha256(train),
                semantic_circuit_sha256(test),
            )
            circuits = []
            for split, count, source in (
                ("train", 422, train),
                ("validation", 88, validation),
                ("test", 90, test),
            ):
                for index in range(count):
                    circuits.append(
                        {
                            "circuit_id": f"{split}-{index}",
                            "file_name": source.name,
                            "source_ref": source.name,
                            "source_sha256": file_sha256(source),
                            "split": split,
                            "leakage_group": f"{split}-group",
                            "num_qubits": 1,
                        }
                    )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps({"circuits": circuits}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Leakage tra split"):
                verify_source_manifest(
                    manifest_path,
                    require_frozen_file_hash=False,
                )

    def test_training_directory_rejects_even_a_hash_valid_test_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_train = root / "source_train.qasm"
            source_test = root / "source_test.qasm"
            source_train.write_text(QASM_A, encoding="utf-8")
            source_test.write_text(QASM_B, encoding="utf-8")
            directory = root / "training"
            directory.mkdir()
            (directory / "train.qasm").write_text(QASM_A, encoding="utf-8")
            (directory / "test.qasm").write_text(QASM_B, encoding="utf-8")
            manifest = {
                "experiment_id": EXPERIMENT_ID,
                "circuits": [
                    {
                        "file_name": "train.qasm",
                        "source_sha256": file_sha256(source_train),
                        "semantic_sha256": semantic_circuit_sha256(source_train),
                        "split": "train",
                    },
                    {
                        "file_name": "test.qasm",
                        "source_sha256": file_sha256(source_test),
                        "semantic_sha256": semantic_circuit_sha256(source_test),
                        "split": "test",
                    },
                ],
            }
            manifest_path = root / "v2.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non previsti"):
                verify_circuit_directory(
                    directory,
                    allowed_splits=("train",),
                    manifest_path=manifest_path,
                )

    def test_rag_contract_rejects_validation_and_test_hashes(self) -> None:
        manifest = {
            "circuits": [
                {"split": "train", "source_sha256": "a" * 64},
                {"split": "validation", "source_sha256": "b" * 64},
                {"split": "test", "source_sha256": "c" * 64},
            ]
        }
        assert_records_belong_to_split(
            [{"split": "train", "source_sha256": "a" * 64}],
            allowed_split="train",
            manifest=manifest,
        )
        with self.assertRaisesRegex(ValueError, "fuori split"):
            assert_records_belong_to_split(
                [{"split": "test", "source_sha256": "c" * 64}],
                allowed_split="train",
                manifest=manifest,
            )

    def test_test_generation_requires_a_valid_release_not_a_marker(self) -> None:
        catalog = load_catalog(V2_CATALOG)
        with patch(
            "scripts.mqt_predictor_protocol.validate_test_release_record",
            side_effect=FileNotFoundError("sigillato"),
        ):
            with self.assertRaisesRegex(RuntimeError, "sigillato"):
                generate_dataset(
                    "full",
                    catalog,
                    workers=1,
                    timeout_seconds=1,
                    split="test",
                )

    def test_v2_generation_rejects_a_different_execution_policy(self) -> None:
        catalog = load_catalog(V2_CATALOG)
        with self.assertRaisesRegex(ValueError, "Politica di esecuzione"):
            generate_dataset(
                "full",
                catalog,
                workers=1,
                timeout_seconds=300,
                split="train",
            )
        with self.assertRaisesRegex(ValueError, "Politica di esecuzione"):
            generate_dataset(
                "full",
                catalog,
                workers=2,
                timeout_seconds=120,
                split="train",
            )

    def test_fake_release_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "experiment_id": EXPERIMENT_ID,
                        "protocol": PROTOCOL_ID,
                        "protocol_version": PROTOCOL_VERSION,
                        "status": "released",
                        "source_manifest_sha256": (
                            file_sha256(SOURCE_MANIFEST_V2)
                            if SOURCE_MANIFEST_V2.is_file()
                            else None
                        ),
                        "target_sha256": FROZEN_TARGET_SHA256,
                        "software": EXPECTED_PACKAGE_VERSIONS,
                        "gates": {"all": True},
                        "frozen_files": {"missing.txt": "0" * 64},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "file congelato mancante"):
                validate_test_release_record(path)

    def test_v2_catalog_freezes_the_complete_stack_and_methodology(self) -> None:
        catalog = load_catalog(V2_CATALOG)
        self.assertEqual(catalog.supported_device_ids, FROZEN_DEVICES)
        self.assertEqual(dict(catalog.required_versions), EXPECTED_PACKAGE_VERSIONS)
        self.assertEqual(tuple(catalog.seeds), (0, 1, 2))
        self.assertEqual(len(catalog.configurations), 12)
        self.assertEqual(dict(catalog.target_sha256), FROZEN_TARGET_SHA256)
        self.assertEqual(
            dict(catalog.execution_policy),
            {"workers": 2, "timeout_seconds": 300},
        )

    def test_qcompile_timeout_is_a_terminal_observation(self) -> None:
        circuits = [
            {
                "circuit_id": f"validation-{index:03d}",
                "source_sha256": hashlib.sha256(
                    f"validation-{index}".encode()
                ).hexdigest(),
                "split": "validation",
                "num_qubits": 2,
            }
            for index in range(88)
        ]
        model_hashes = {
            f"model-{index}": hashlib.sha256(
                f"model-{index}".encode()
            ).hexdigest()
            for index in range(6)
        }
        model_set_sha256 = hashlib.sha256(
            json.dumps(
                model_hashes,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        records = []
        for circuit in circuits:
            for repetition_index in range(3):
                identity = {
                    "experiment_id": EXPERIMENT_ID,
                    "protocol_version": PROTOCOL_VERSION,
                    "method_id": "mqt_qcompile",
                    "split": "validation",
                    "circuit_id": circuit["circuit_id"],
                    "source_sha256": circuit["source_sha256"],
                    "repetition_index": repetition_index,
                    "model_set_sha256": model_set_sha256,
                }
                records.append(
                    {
                        "schema_version": "1.0.0",
                        "experiment_id": EXPERIMENT_ID,
                        "protocol_version": PROTOCOL_VERSION,
                        "method_id": "mqt_qcompile",
                        "split": "validation",
                        "circuit_id": circuit["circuit_id"],
                        "source_sha256": circuit["source_sha256"],
                        "repetition_index": repetition_index,
                        "status": "timeout",
                        "run_id": "mqt_run_"
                        + hashlib.sha256(
                            json.dumps(
                                identity,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode()
                        ).hexdigest(),
                        "selected_device_id": None,
                        "target_sha256": None,
                        "score": None,
                        "failure": {"category": "compilation_timeout"},
                        "provenance": {
                            "source_manifest_sha256": (
                                file_sha256(SOURCE_MANIFEST_V2)
                                if SOURCE_MANIFEST_V2.is_file()
                                else None
                            ),
                            "model_set_sha256": model_set_sha256,
                            "model_hashes": model_hashes,
                            "software": EXPECTED_PACKAGE_VERSIONS,
                            "controlled_seed": None,
                            "repetition_semantics": (
                                "fresh_process_without_exposed_seed"
                            ),
                            "timeout_seconds": 300,
                        },
                    }
                )
        validated = validate_qcompile_runs(
            records,
            split="validation",
            manifest={"circuits": circuits},
            expected_model_set_sha256=model_set_sha256,
        )
        self.assertEqual(len(validated), 264)
        summary = summarize_results(
            [
                {
                    "method_id": "mqt_qcompile",
                    "status": "timeout",
                    "regret_absolute": None,
                    "failure_category": "compilation_timeout",
                }
            ],
            split="validation",
            input_fingerprints={},
        )
        self.assertEqual(summary["methods"]["mqt_qcompile"]["timeouts"], 1)
        self.assertEqual(summary["methods"]["mqt_qcompile"]["failures"], 0)

    def test_random_plan_is_deterministic_and_has_270_test_draws(self) -> None:
        catalog = load_catalog(V2_CATALOG)
        manifest = {
            "circuits": [
                {
                    "circuit_id": f"test-{index:03d}",
                    "source_sha256": hashlib.sha256(
                        f"test-{index}".encode()
                    ).hexdigest(),
                    "split": "test",
                    "num_qubits": 2,
                }
                for index in range(90)
            ]
        }
        capacities = {device_id: 200 for device_id in FROZEN_DEVICES}
        first = build_method_plan(
            "test",
            catalog,
            manifest=manifest,
            capacities=capacities,
        )
        second = build_method_plan(
            "test",
            catalog,
            manifest=manifest,
            capacities=capacities,
        )
        self.assertEqual(first, second)
        self.assertEqual(
            sum(
                len(row["repetitions"])
                for row in first["random_selection"]["rows"]
            ),
            270,
        )

    def test_comparison_split_rejects_duplicate_source_hashes(self) -> None:
        circuits = [
            {
                "circuit_id": f"validation-{index:03d}",
                "source_sha256": hashlib.sha256(
                    f"validation-{index}".encode()
                ).hexdigest(),
                "split": "validation",
                "num_qubits": 2,
            }
            for index in range(88)
        ]
        circuits[1]["source_sha256"] = circuits[0]["source_sha256"]
        with self.assertRaisesRegex(ValueError, "source_sha256 duplicati"):
            split_circuits("validation", {"circuits": circuits})

    def test_qiskit_matrix_recomputes_run_and_summary_contracts(self) -> None:
        full_catalog = load_catalog(V2_CATALOG)
        device_id = full_catalog.supported_device_ids[0]
        configuration = full_catalog.configurations[0]
        seed = full_catalog.seeds[0]
        catalog = replace(
            full_catalog,
            default_device_id=device_id,
            supported_device_ids=(device_id,),
            configurations=(configuration,),
            seeds=(seed,),
        )
        capacities = {device_id: 200}
        circuits = [
            {
                "circuit_id": f"validation-{index:03d}",
                "source_sha256": hashlib.sha256(
                    f"validation-{index}".encode()
                ).hexdigest(),
                "split": "validation",
                "num_qubits": 2,
            }
            for index in range(88)
        ]
        device = {
            "device_id": device_id,
            "num_qubits": capacities[device_id],
            "target_sha256": FROZEN_TARGET_SHA256[device_id],
        }
        configuration_record = {
            **configuration.to_dict(),
            "catalog_id": catalog.catalog_id,
        }
        runs = []
        summaries = []
        for circuit in circuits:
            run_id = make_run_id(
                circuit,
                configuration.to_dict(),
                seed,
                device_id=device_id,
                target_sha256=FROZEN_TARGET_SHA256[device_id],
                objective=catalog.objective,
                versions=EXPECTED_PACKAGE_VERSIONS,
                catalog_id=catalog.catalog_id,
                experiment_id=EXPERIMENT_ID,
                protocol_version=PROTOCOL_VERSION,
                fixed_transpile_options=catalog.fixed_transpile_options,
                execution_policy=catalog.execution_policy,
            )
            score = 0.5
            runs.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "experiment_id": EXPERIMENT_ID,
                    "protocol_version": PROTOCOL_VERSION,
                    "run_id": run_id,
                    "dataset_scope": "full",
                    "split": "validation",
                    "objective": dict(catalog.objective),
                    "circuit": dict(circuit),
                    "device": dict(device),
                    "configuration": dict(configuration_record),
                    "seed_transpiler": seed,
                    "status": "success",
                    "phase": "completed",
                    "score": score,
                    "target_validation": {
                        "is_executable_on_target": True,
                    },
                    "compiled_circuit": {},
                    "failure": None,
                    "provenance": {
                        "versions": EXPECTED_PACKAGE_VERSIONS,
                        "compiler": "qiskit.transpile",
                        "fixed_transpile_options": dict(
                            catalog.fixed_transpile_options
                        ),
                        "execution_policy": dict(catalog.execution_policy),
                        "generator": "qiskit_dataset.generation",
                        "resume_contract_sha256": run_id.removeprefix("run_"),
                    },
                }
            )
            summary_id = stable_id(
                "summary",
                {
                    "circuit_id": circuit["circuit_id"],
                    "source_sha256": circuit["source_sha256"],
                    "device_id": device_id,
                    "configuration": configuration.to_dict(),
                    "objective": catalog.objective["name"],
                    "catalog_id": catalog.catalog_id,
                },
            )
            summaries.append(
                {
                    "schema_version": AGGREGATE_SCHEMA_VERSION,
                    "experiment_id": EXPERIMENT_ID,
                    "protocol_version": PROTOCOL_VERSION,
                    "summary_id": summary_id,
                    "dataset_scope": "full",
                    "split": "validation",
                    "objective": dict(catalog.objective),
                    "circuit": dict(circuit),
                    "device": dict(device),
                    "configuration": dict(configuration_record),
                    "seeds": {
                        "expected": [seed],
                        "observed": [seed],
                        "successful": [seed],
                        "failed": [],
                        "timed_out": [],
                    },
                    "attempts": {
                        "expected_count": 1,
                        "observed_count": 1,
                        "success_count": 1,
                        "failure_count": 0,
                        "timeout_count": 0,
                        "complete": True,
                        "success_rate": 1.0,
                    },
                    "score_observations": [
                        {
                            "run_id": run_id,
                            "seed_transpiler": seed,
                            "score": score,
                        }
                    ],
                    "eligible_for_ranking": True,
                    "ranking_metric": (
                        "median_expected_fidelity_across_seeds"
                    ),
                    "ranking_score": score,
                    "run_ids": [run_id],
                }
            )
        run_index, summary_index = validate_qiskit_matrix(
            runs,
            summaries,
            split="validation",
            catalog=catalog,
            manifest={"circuits": circuits},
            capacities=capacities,
        )
        self.assertEqual(len(run_index), 88)
        self.assertEqual(len(summary_index), 88)

        resume_contract = runs[0]["provenance"]["resume_contract_sha256"]
        runs[0]["provenance"]["resume_contract_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Tentativo Qiskit v2"):
            validate_qiskit_matrix(
                runs,
                summaries,
                split="validation",
                catalog=catalog,
                manifest={"circuits": circuits},
                capacities=capacities,
            )
        runs[0]["provenance"]["resume_contract_sha256"] = resume_contract

        summaries[0]["ranking_score"] = 0.25
        with self.assertRaisesRegex(ValueError, "non allineato ai raw run"):
            validate_qiskit_matrix(
                runs,
                summaries,
                split="validation",
                catalog=catalog,
                manifest={"circuits": circuits},
                capacities=capacities,
            )

    def test_unconfigured_llm_models_block_protocol_freeze(self) -> None:
        validate_method_configuration(METHOD_CONFIG, require_frozen=False)
        with self.assertRaisesRegex(ValueError, "non sono ancora congelati"):
            validate_method_configuration(METHOD_CONFIG, require_frozen=True)

    def test_frozen_llm_configuration_requires_real_budget_values(self) -> None:
        config = json.loads(METHOD_CONFIG.read_text(encoding="utf-8"))
        config["status"] = "frozen"
        for method_id, record in config["methods"].items():
            record.update(
                {
                    "provider": "provider",
                    "model_id": (
                        "same-model"
                        if method_id != "frontier_llm"
                        else "frontier-model"
                    ),
                    "model_revision": "immutable-revision",
                    "prompt_version": "v1",
                    "prompt_sha256": "a" * 64,
                    "temperature": 0,
                    "request_timeout_seconds": 120,
                    "max_output_tokens": 512,
                }
            )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "methods.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            validate_method_configuration(path, require_frozen=True)
            config["methods"]["llm_no_rag"]["request_timeout_seconds"] = 0
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "request_timeout_seconds",
            ):
                validate_method_configuration(path, require_frozen=True)

    def test_legacy_qiskit_aggregate_is_rejected_by_v2_matrix(self) -> None:
        catalog = load_catalog(V2_CATALOG)
        circuits = [
            {
                "circuit_id": f"validation-{index:03d}",
                "source_sha256": hashlib.sha256(
                    f"validation-{index}".encode()
                ).hexdigest(),
                "split": "validation",
                "num_qubits": 2,
            }
            for index in range(88)
        ]
        first = circuits[0]
        legacy_summary = {
            "experiment_id": None,
            "protocol_version": None,
            "split": "validation",
            "circuit": first,
            "device": {
                "device_id": FROZEN_DEVICES[0],
                "target_sha256": FROZEN_TARGET_SHA256[FROZEN_DEVICES[0]],
            },
            "configuration": {"config_id": catalog.configurations[0].config_id},
        }
        with self.assertRaisesRegex(ValueError, "v2 non conforme"):
            validate_qiskit_matrix(
                [],
                [legacy_summary],
                split="validation",
                catalog=catalog,
                manifest={"circuits": circuits},
                capacities={device_id: 200 for device_id in FROZEN_DEVICES},
            )


if __name__ == "__main__":
    unittest.main()

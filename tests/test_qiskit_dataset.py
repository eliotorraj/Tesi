from __future__ import annotations

import json
import unittest
from io import StringIO
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.qasm2 import dump as qasm_dump

from prototype.quantum_assistant.adapters.parsing import (
    QasmRequestParser,
    WidthCompatibilityFilter,
)
from prototype.quantum_assistant.adapters.validation import (
    StructuredRecommendationValidator,
)
from prototype.quantum_assistant.models import HardwareProfile, UiSubmission
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import expand_attempts, load_manifest, stable_id
from qiskit_dataset.generation import execute_attempt
from qiskit_dataset.views import aggregate_runs, build_rag_examples


EXPECTED_KEYS = {
    (2, None, None),
    (3, None, None),
    (2, "sabre", "sabre"),
    (2, "dense", "sabre"),
    (2, "trivial", "sabre"),
    (3, "sabre", "sabre"),
    (3, "dense", "sabre"),
    (3, "trivial", "sabre"),
    (2, "sabre", "lookahead"),
    (2, "sabre", "basic"),
    (3, "sabre", "lookahead"),
    (3, "sabre", "basic"),
}


def _qasm2() -> str:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    stream = StringIO()
    qasm_dump(circuit, stream)
    return stream.getvalue()


def _synthetic_circuit(circuit_id: str, split: str) -> dict[str, object]:
    return {
        "circuit_id": circuit_id,
        "file_name": f"{circuit_id}.qasm",
        "benchmark_family": "synthetic",
        "leakage_group": f"group_{split}",
        "generator": "qiskit",
        "declared_num_qubits": 2,
        "num_qubits": 2,
        "num_clbits": 0,
        "depth": 2,
        "size": 2,
        "operation_counts": {"cx": 1, "h": 1},
        "source_sha256": stable_id("source", circuit_id).split("_", 1)[1],
        "canonical_circuit_id": circuit_id,
        "duplicate_group_size": 1,
        "is_exact_duplicate": False,
        "is_duplicate_alias": False,
        "split": split,
        "features": {
            "extractor": "test",
            "dimension": 49,
            "values": {f"feature_{index}": float(index) for index in range(49)},
        },
        "source_ref": f"circuits/{split}/{circuit_id}.qasm",
    }


def _success_run(
    circuit: dict[str, object],
    configuration: object,
    seed: int,
    score: float,
) -> dict[str, object]:
    configuration_dict = configuration.to_dict()
    return {
        "schema_version": "1.0.0",
        "run_id": stable_id(
            "run",
            {
                "circuit": circuit["circuit_id"],
                "config": configuration_dict["config_id"],
                "seed": seed,
            },
        ),
        "dataset_scope": "pilot",
        "split": circuit["split"],
        "objective": {
            "name": "expected_fidelity",
            "direction": "maximize",
            "implementation": "mqt.predictor.reward.expected_fidelity",
        },
        "circuit": circuit,
        "device": {
            "device_id": "ibm_falcon_127",
            "num_qubits": 127,
            "target_sha256": "a" * 64,
        },
        "configuration": {
            **configuration_dict,
            "catalog_id": "qiskit_expected_fidelity_pilot_v1",
        },
        "seed_transpiler": seed,
        "status": "success",
        "phase": "completed",
        "score": score,
        "target_validation": {"is_executable_on_target": True},
        "compiled_circuit": {"qasm_sha256": "b" * 64},
        "timings_seconds": {
            "transpilation": 1.0 + seed,
            "total": 2.0 + seed,
        },
        "failure": None,
        "provenance": {},
    }


class QiskitCatalogTests(unittest.TestCase):
    def test_catalog_is_the_exact_twelve_tuple_allowlist(self) -> None:
        catalog = load_catalog()
        self.assertEqual(len(catalog.configurations), 12)
        self.assertEqual(catalog.allowed_keys, EXPECTED_KEYS)
        self.assertEqual(catalog.seeds, (0, 1, 2))
        self.assertEqual(len(catalog.by_id), 12)
        baseline = catalog.by_id["o2_default_default"]
        self.assertEqual(
            baseline.transpile_kwargs(),
            {"optimization_level": 2},
        )

    def test_catalog_rejects_cross_product_and_excluded_values(self) -> None:
        catalog = load_catalog()
        for key in (
            (1, None, None),
            (2, "dense", "basic"),
            (2, None, "sabre"),
            (3, "sabre", "none"),
            (3, "sabre", "stochastic"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                catalog.require_allowed(*key)

    def test_prototype_validator_uses_complete_tuple_membership(self) -> None:
        submission = UiSubmission(
            request_id="request-catalog",
            user_text="Compila",
            qasm2=_qasm2(),
            figure_of_merit="expected_fidelity",
        )
        request = QasmRequestParser().parse(submission)
        hardware = HardwareProfile(
            device_id="ibm_falcon_127",
            num_qubits=127,
            operation_names=("x", "cx"),
            coupling_edges=((0, 1),),
        )
        compatibility = WidthCompatibilityFilter().filter(
            request,
            (hardware,),
        )
        raw = {
            "selected_device": "ibm_falcon_127",
            "figure_of_merit": "expected_fidelity",
            "compiler": "qiskit",
            "qiskit_plan": {
                "optimization_level": 2,
                "seed_transpiler": 0,
                "layout_method": "dense",
                "routing_method": "basic",
            },
            "explanation": "test",
            "evidence": ["test"],
            "warnings": [],
        }
        result = StructuredRecommendationValidator().validate(
            raw,
            request,
            compatibility,
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("12 configurazioni" in error for error in result.errors)
        )


class QiskitSplitAndPlanTests(unittest.TestCase):
    def test_committed_manifests_have_expected_counts_and_no_leakage(self) -> None:
        catalog = load_catalog()
        pilot = load_manifest("pilot")
        full = load_manifest("full")
        self.assertEqual(pilot["counts"]["by_split"], {
            "test": 2,
            "train": 6,
            "validation": 2,
        })
        self.assertEqual(full["counts"]["by_split"], {
            "test": 90,
            "train": 422,
            "validation": 88,
        })
        self.assertEqual(full["counts"]["circuits"], 600)
        self.assertEqual(full["counts"]["unique_source_hashes"], 574)
        self.assertEqual(full["counts"]["duplicate_hash_groups"], 26)

        split_by_hash: dict[str, set[str]] = {}
        for circuit in full["circuits"]:
            split_by_hash.setdefault(circuit["source_sha256"], set()).add(
                circuit["split"]
            )
            self.assertEqual(circuit["features"]["dimension"], 49)
            self.assertEqual(len(circuit["features"]["values"]), 49)
        self.assertTrue(all(len(splits) == 1 for splits in split_by_hash.values()))

        pilot_plan = expand_attempts(
            pilot,
            catalog,
            target_sha256="a" * 64,
            versions={"mqt.predictor": "2.3.0", "mqt.bench": "2.0.0", "qiskit": "2.1.1"},
        )
        full_plan = expand_attempts(
            full,
            catalog,
            target_sha256="a" * 64,
            versions={"mqt.predictor": "2.3.0", "mqt.bench": "2.0.0", "qiskit": "2.1.1"},
        )
        self.assertEqual(len(pilot_plan), 360)
        self.assertEqual(len(full_plan), 21600)
        self.assertEqual(len({item["run_id"] for item in full_plan}), 21600)
        self.assertLessEqual(
            {item["run_id"] for item in pilot_plan},
            {item["run_id"] for item in full_plan},
        )


class QiskitAggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog()
        self.train_circuit = _synthetic_circuit("train_circuit", "train")
        self.validation_circuit = _synthetic_circuit(
            "validation_circuit",
            "validation",
        )
        self.manifest = {
            "dataset_scope": "pilot",
            "circuits": [self.train_circuit, self.validation_circuit],
        }
        self.target = {
            "device_id": "ibm_falcon_127",
            "num_qubits": 127,
            "target_sha256": "a" * 64,
        }

    def _complete_runs(self) -> list[dict[str, object]]:
        runs: list[dict[str, object]] = []
        for circuit in (self.train_circuit, self.validation_circuit):
            for index, configuration in enumerate(
                self.catalog.configurations
            ):
                if circuit["split"] == "validation":
                    scores = (0.5, 0.5, 0.5)
                elif index == 0:
                    scores = (0.1, 0.9, 0.9)
                elif index == 1:
                    scores = (0.8, 0.8, 1.0)
                else:
                    value = 0.7 - index / 100
                    scores = (value, value, value)
                for seed, score in zip(
                    self.catalog.seeds,
                    scores,
                    strict=True,
                ):
                    runs.append(
                        _success_run(
                            circuit,
                            configuration,
                            seed,
                            score,
                        )
                    )
        return runs

    def test_median_across_seeds_drives_rank_and_rag_is_train_only(self) -> None:
        summaries = aggregate_runs(
            self.manifest,
            self._complete_runs(),
            self.catalog,
            self.target,
        )
        train = [
            summary
            for summary in summaries
            if summary["circuit"]["circuit_id"] == "train_circuit"
        ]
        winner = next(summary for summary in train if summary["rank"] == 1)
        self.assertEqual(
            winner["configuration"]["config_id"],
            "o2_default_default",
        )
        self.assertEqual(winner["score_statistics"]["median"], 0.9)
        self.assertEqual(len(train), 12)
        self.assertTrue(all(summary["eligible_for_ranking"] for summary in train))

        rag = build_rag_examples(summaries, top_k=3)
        self.assertEqual(len(rag), 1)
        self.assertEqual(rag[0]["split"], "train")
        self.assertEqual(len(rag[0]["top_configurations"]), 3)
        self.assertNotIn("seed", json.dumps(rag[0]["top_configurations"]))

    def test_incomplete_seed_set_is_not_eligible(self) -> None:
        runs = self._complete_runs()
        runs = [
            run
            for run in runs
            if not (
                run["circuit"]["circuit_id"] == "train_circuit"
                and run["configuration"]["config_id"] == "o2_default_default"
                and run["seed_transpiler"] == 2
            )
        ]
        summaries = aggregate_runs(
            self.manifest,
            runs,
            self.catalog,
            self.target,
        )
        summary = next(
            item
            for item in summaries
            if item["circuit"]["circuit_id"] == "train_circuit"
            and item["configuration"]["config_id"] == "o2_default_default"
        )
        self.assertFalse(summary["attempts"]["complete"])
        self.assertFalse(summary["eligible_for_ranking"])
        self.assertIsNone(summary["rank"])


class QiskitFailureRecordTests(unittest.TestCase):
    def test_source_failure_preserves_full_attempt_context(self) -> None:
        catalog = load_catalog()
        circuit = _synthetic_circuit("missing_source", "train")
        configuration = catalog.configurations[0]
        task = {
            "run_id": stable_id("run", "missing-source"),
            "dataset_scope": "pilot",
            "split": "train",
            "objective": dict(catalog.objective),
            "circuit": circuit,
            "target_record": {
                "device_id": catalog.device_id,
                "num_qubits": 127,
                "target_sha256": "a" * 64,
            },
            "configuration": configuration.to_dict(),
            "catalog_id": catalog.catalog_id,
            "seed_transpiler": 0,
            "versions": {
                "mqt.predictor": "2.3.0",
                "mqt.bench": "2.0.0",
                "qiskit": "2.1.1",
            },
            "fixed_transpile_options": {
                "approximation_degree": 1.0,
                "num_processes": 1,
            },
            "timeout_seconds": 1.0,
            "source_path": "/path/intentionally/absent.qasm",
            "device_id": catalog.device_id,
        }
        record = execute_attempt(task)
        self.assertEqual(record["status"], "failure")
        self.assertEqual(record["phase"], "source_loading")
        self.assertIsNone(record["score"])
        self.assertEqual(record["circuit"]["circuit_id"], "missing_source")
        self.assertEqual(record["device"]["device_id"], catalog.device_id)
        self.assertEqual(
            record["configuration"]["config_id"],
            "o2_default_default",
        )
        self.assertEqual(record["seed_transpiler"], 0)
        self.assertEqual(record["failure"]["phase"], "source_loading")
        self.assertEqual(record["failure"]["category"], "source_error")
        self.assertTrue(record["failure"]["exception_type"])
        self.assertTrue(record["failure"]["message"])


class JsonSchemaFilesTests(unittest.TestCase):
    def test_schema_files_are_valid_json(self) -> None:
        root = Path(__file__).resolve().parents[1] / "schemas"
        for name in (
            "qiskit_run.schema.json",
            "qiskit_configuration_aggregate.schema.json",
            "qiskit_rag_example.schema.json",
        ):
            with self.subTest(name=name):
                with (root / name).open(encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.assertEqual(
                    payload["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )


if __name__ == "__main__":
    unittest.main()

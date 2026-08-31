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
from prototype.quantum_assistant.models import (
    EvidenceRegistry,
    HardwareProfile,
    UiSubmission,
)
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import (
    dataset_circuits_root,
    dataset_scope_root,
    expand_attempts,
    load_manifest,
    resolve_circuit_source,
    sha256_file,
    stable_id,
)
from qiskit_dataset.generation import build_timeout_diagnostics, execute_attempt
from qiskit_dataset.reporting import failure_detail_rows
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
EXPECTED_DEVICES = (
    "ibm_falcon_27",
    "ibm_heron_133",
    "ibm_falcon_127",
    "ibm_heron_156",
    "quantinuum_h2_56",
)


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
    *,
    device_id: str = "ibm_falcon_127",
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
                "device": device_id,
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
            "device_id": device_id,
            "num_qubits": 127,
            "target_sha256": stable_id("target", device_id).split("_", 1)[1],
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
        self.assertEqual(catalog.default_device_id, "ibm_falcon_127")
        self.assertEqual(catalog.supported_device_ids, EXPECTED_DEVICES)
        for device_id in EXPECTED_DEVICES:
            self.assertEqual(catalog.require_device(device_id), device_id)

    def test_device_paths_are_isolated_and_reject_path_traversal(self) -> None:
        legacy = dataset_scope_root("expected_fidelity", "pilot")
        falcon = dataset_scope_root(
            "expected_fidelity", "pilot", "ibm_falcon_127"
        )
        self.assertEqual(falcon.parent, legacy)
        self.assertEqual(falcon.name, "ibm_falcon_127")
        with self.assertRaises(ValueError):
            dataset_scope_root("expected_fidelity", "pilot", "../escape")
        with self.assertRaises(ValueError):
            load_catalog().require_device("unknown_device")

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
            "schema_version": "2.0.0",
            "request_id": request.request_id,
            "catalog_snapshot_id": request.catalog_snapshot_id,
            "selected_device": "ibm_falcon_127",
            "figure_of_merit": "expected_fidelity",
            "compiler": "qiskit",
            "qiskit_plan": {
                "optimization_level": 2,
                "seed_transpiler": 0,
                "layout_method": "dense",
                "routing_method": "basic",
            },
            "evidence_refs": [],
            "claims": [
                {
                    "claim_id": "live-compatibility",
                    "claim_type": "live_compatibility",
                    "parameters": {"device_id": "ibm_falcon_127"},
                    "evidence_ref_ids": [],
                },
                {
                    "claim_id": "historical-evidence-unavailable",
                    "claim_type": "historical_evidence_unavailable",
                    "parameters": {},
                    "evidence_ref_ids": [],
                },
            ],
        }
        result = StructuredRecommendationValidator().validate(
            raw,
            request,
            compatibility,
            evidence_registry=EvidenceRegistry(),
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("12 configurazioni" in error for error in result.errors)
        )


class QiskitSplitAndPlanTests(unittest.TestCase):
    def test_committed_manifests_have_expected_counts_and_no_leakage(self) -> None:
        catalog = load_catalog()
        pilot = load_manifest(
            "pilot",
            device_id=catalog.default_device_id,
        )
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

    def test_pilot_uses_one_shared_integrity_checked_circuit_store(self) -> None:
        catalog = load_catalog()
        shared_root = dataset_circuits_root("expected_fidelity", "pilot")
        self.assertEqual(len(list(shared_root.glob("*/*.qasm"))), 10)
        for device_id in catalog.supported_device_ids:
            device_root = dataset_scope_root(
                "expected_fidelity", "pilot", device_id
            )
            self.assertFalse((device_root / "circuits").exists())
            manifest = load_manifest("pilot", device_id=device_id)
            self.assertEqual(manifest["schema_version"], "2.0.0")
            self.assertEqual(
                manifest["circuit_storage"]["layout"],
                "shared_scope_root",
            )
            for circuit in manifest["circuits"]:
                source = resolve_circuit_source(
                    "expected_fidelity",
                    "pilot",
                    str(circuit["source_ref"]),
                )
                self.assertTrue(source.is_file())
                self.assertEqual(
                    sha256_file(source),
                    circuit["source_sha256"],
                )

    def test_attempt_plan_skips_width_incompatible_circuits(self) -> None:
        catalog = load_catalog()
        compatible = _synthetic_circuit("compatible", "train")
        compatible["device_compatibility"] = {
            "compatible": True,
            "device_num_qubits": 27,
            "reason": None,
        }
        incompatible = _synthetic_circuit("incompatible", "train")
        incompatible["num_qubits"] = 90
        incompatible["device_compatibility"] = {
            "compatible": False,
            "device_num_qubits": 27,
            "reason": "circuit_width_90_exceeds_device_width_27",
        }
        manifest = {
            "dataset_scope": "pilot",
            "device_id": "ibm_falcon_27",
            "circuits": [compatible, incompatible],
        }
        attempts = expand_attempts(
            manifest,
            catalog,
            target_sha256="a" * 64,
            versions={
                "mqt.predictor": "2.3.0",
                "mqt.bench": "2.0.0",
                "qiskit": "2.1.1",
            },
            device_id="ibm_falcon_27",
        )
        self.assertEqual(len(attempts), 36)
        self.assertEqual(
            {item["circuit"]["circuit_id"] for item in attempts},
            {"compatible"},
        )
        self.assertEqual(
            {item["device_id"] for item in attempts},
            {"ibm_falcon_27"},
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
            "schema_version": "1.0.0",
            "dataset_scope": "pilot",
            "catalog_id": self.catalog.catalog_id,
            "objective": dict(self.catalog.objective),
            "seeds": list(self.catalog.seeds),
            "circuits": [self.train_circuit, self.validation_circuit],
        }
        self.target = {
            "device_id": "ibm_falcon_127",
            "num_qubits": 127,
            "target_sha256": stable_id(
                "target", "ibm_falcon_127"
            ).split("_", 1)[1],
        }

    def _complete_runs(
        self,
        *,
        device_id: str = "ibm_falcon_127",
        score_shift: float = 0.0,
    ) -> list[dict[str, object]]:
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
                            score + score_shift,
                            device_id=device_id,
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
        self.assertEqual(rag[0]["schema_version"], "2.0.0")
        self.assertEqual(rag[0]["view_scope"], "device_specific")
        self.assertEqual(
            rag[0]["selected_device"]["device_id"],
            "ibm_falcon_127",
        )
        evidence_ids = {
            item["evidence_id"] for item in rag[0]["evidence"]
        }
        for claim in rag[0]["claims"]:
            self.assertLessEqual(set(claim["evidence_ids"]), evidence_ids)
        self.assertTrue(
            all(
                item["stability"]["observations"]
                for item in rag[0]["evidence"]
            )
        )

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

    def test_global_rag_selects_device_then_top_three_configurations(self) -> None:
        first = aggregate_runs(
            self.manifest,
            self._complete_runs(device_id="ibm_falcon_127"),
            self.catalog,
            self.target,
        )
        second = aggregate_runs(
            self.manifest,
            self._complete_runs(
                device_id="ibm_heron_133",
                score_shift=0.05,
            ),
            self.catalog,
            {
                **self.target,
                "device_id": "ibm_heron_133",
                "target_sha256": stable_id(
                    "target", "ibm_heron_133"
                ).split("_", 1)[1],
            },
        )
        example = build_rag_examples(
            first + second,
            top_k=3,
            device_order=self.catalog.supported_device_ids,
        )[0]
        self.assertEqual(example["view_scope"], "global_multi_device")
        self.assertEqual(
            example["selected_device"]["device_id"],
            "ibm_heron_133",
        )
        self.assertEqual(
            {item["device_id"] for item in example["top_configurations"]},
            {"ibm_heron_133"},
        )
        self.assertEqual(
            len(example["retrieval_input"]["compatible_devices"]),
            2,
        )
        self.assertNotIn("selected_device", example["retrieval_input"])

    def test_global_rag_tie_break_is_explicitly_non_causal(self) -> None:
        first = aggregate_runs(
            self.manifest,
            self._complete_runs(device_id="ibm_falcon_27"),
            self.catalog,
            {
                **self.target,
                "device_id": "ibm_falcon_27",
                "target_sha256": stable_id(
                    "target", "ibm_falcon_27"
                ).split("_", 1)[1],
            },
        )
        second = aggregate_runs(
            self.manifest,
            self._complete_runs(device_id="ibm_falcon_127"),
            self.catalog,
            self.target,
        )
        example = build_rag_examples(
            first + second,
            top_k=3,
            device_order=self.catalog.supported_device_ids,
        )[0]
        self.assertEqual(
            example["selected_device"]["device_id"],
            "ibm_falcon_27",
        )
        device_claim = next(
            claim
            for claim in example["claims"]
            if claim["claim_type"] == "selected_device"
        )
        self.assertIn("parità", device_claim["text"])
        self.assertIn("non dimostrano superiorità", device_claim["text"])

    def test_rag_rejects_more_than_three_labeled_configurations(self) -> None:
        summaries = aggregate_runs(
            self.manifest,
            self._complete_runs(),
            self.catalog,
            self.target,
        )
        with self.assertRaises(ValueError):
            build_rag_examples(summaries, top_k=4)


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

    def test_timeout_diagnostics_separate_observation_from_inference(self) -> None:
        traceback_text = """Traceback (most recent call last):
  File "/tmp/qiskit/transpiler/passes/layout/vf2_post_layout.py", line 363, in _score_layout
    value = target[gate]
  File "/workspace/qiskit_dataset/generation.py", line 1, in on_alarm
    raise AttemptTimeoutError()
"""
        diagnostics = build_timeout_diagnostics(
            traceback_text=traceback_text,
            phase="transpilation",
            timeout_seconds=120.0,
            elapsed_seconds=120.01,
            configuration={
                "optimization_level": 3,
                "layout_method": "sabre",
                "routing_method": "lookahead",
            },
            qiskit_version="2.1.1",
        )
        self.assertEqual(
            diagnostics["interrupted_stack_frame"]["function"],
            "_score_layout",
        )
        self.assertEqual(
            diagnostics["inference"]["qiskit_stage"],
            "optimization",
        )
        self.assertEqual(
            diagnostics["inference"]["configuration_component"],
            {"name": "optimization_level", "value": 3},
        )
        self.assertFalse(
            diagnostics["inference"]["causal_attribution_supported"]
        )
        self.assertIsNone(diagnostics["last_completed_pass"])

        run = {
            "run_id": "run_" + "a" * 64,
            "status": "timeout",
            "phase": "transpilation",
            "seed_transpiler": 0,
            "circuit": {
                "circuit_id": "c",
                "benchmark_family": "synthetic",
                "generator": "qiskit",
                "num_qubits": 2,
                "depth": 2,
                "size": 2,
            },
            "device": {
                "device_id": "ibm_falcon_127",
                "num_qubits": 127,
                "target_sha256": "b" * 64,
            },
            "configuration": {
                "config_id": "o3_sabre_lookahead",
                "optimization_level": 3,
                "layout_method": "sabre",
                "routing_method": "lookahead",
            },
            "timings_seconds": {"total": 120.01},
            "failure": {
                "phase": "transpilation",
                "category": "timeout",
                "exception_type": "AttemptTimeoutError",
                "message": "timeout",
                "traceback": traceback_text,
                "timeout_seconds": 120.0,
            },
            "provenance": {"versions": {"qiskit": "2.1.1"}},
        }
        row = failure_detail_rows([run])[0]
        self.assertEqual(row["interrupted_pass_function"], "_score_layout")
        self.assertEqual(row["inferred_qiskit_stage"], "optimization")
        self.assertEqual(row["causal_attribution_supported"], False)


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

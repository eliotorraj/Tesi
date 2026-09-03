from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from qiskit import QuantumCircuit
from qiskit.qasm2 import dump as qasm_dump


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "04_train_device_selector.py"
SPEC = importlib.util.spec_from_file_location("train_device_selector", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
TRAIN_SELECTOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRAIN_SELECTOR
SPEC.loader.exec_module(TRAIN_SELECTOR)


class DeviceSelectorTrainingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source_dir = self.root / "source"
        self.compiled_dir = self.root / "compiled"
        self.output_dir = self.root / "output"
        self.source_dir.mkdir()
        self.compiled_dir.mkdir()

        self.source = self.source_dir / "example.qasm"
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
        self._write_qasm(self.source, circuit)
        self.circuit = circuit

        self.device_names = ["ibm_falcon_27", "ibm_falcon_127"]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def _write_qasm(path: Path, circuit: QuantumCircuit) -> None:
        with path.open("w", encoding="utf-8") as handle:
            qasm_dump(circuit, handle)

    @staticmethod
    def _strict_record(**overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "status": "success",
            "mode": "rl",
            "validation_version": TRAIN_SELECTOR.VALIDATION_VERSION,
            "terminated": True,
            "truncated": False,
            "termination_reason": "terminate",
            "native": True,
            "laid_out": True,
            "routed": True,
            "passes": ["Optimize1qGatesDecomposition", "terminate"],
            "qasm_sha256": "qasm-hash",
            "target_validation": {"is_executable_on_target": True},
            "mqt_predictor_version": TRAIN_SELECTOR.package_version("mqt.predictor"),
            "rl_max_steps": 64,
            "seed": 7,
            "model_sha256": "model-hash",
            "target_sha256": "target-hash",
        }
        record.update(overrides)
        return record

    def test_choose_best_device_ignores_failed_candidates(self) -> None:
        winner = TRAIN_SELECTOR.choose_best_device(
            ["device_a", "device_b", "device_c"],
            [0.25, TRAIN_SELECTOR.WORST_SCORE, 0.8],
        )
        self.assertEqual(winner, "device_c")

    def test_choose_best_device_returns_none_when_every_rl_failed(self) -> None:
        winner = TRAIN_SELECTOR.choose_best_device(
            ["device_a", "device_b"],
            [TRAIN_SELECTOR.WORST_SCORE, TRAIN_SELECTOR.WORST_SCORE],
        )
        self.assertIsNone(winner)


    def test_scoring_device_reuses_one_target_instance(self) -> None:
        cached_device = SimpleNamespace(description="device_a")
        TRAIN_SELECTOR.scoring_device.cache_clear()
        try:
            with patch.object(
                TRAIN_SELECTOR,
                "get_device",
                return_value=cached_device,
            ) as get_device:
                first = TRAIN_SELECTOR.scoring_device("device_a")
                second = TRAIN_SELECTOR.scoring_device("device_a")
            self.assertIs(first, cached_device)
            self.assertIs(second, cached_device)
            get_device.assert_called_once_with("device_a")
        finally:
            TRAIN_SELECTOR.scoring_device.cache_clear()

    def test_single_worker_scoring_bypasses_joblib(self) -> None:
        predictor = SimpleNamespace(
            devices=[SimpleNamespace(description="device_a")]
        )
        generated = (([0.0], "device_a"), "example", [0.5])
        with (
            patch.object(
                TRAIN_SELECTOR,
                "generate_training_sample",
                return_value=generated,
            ) as generate,
            patch.object(
                TRAIN_SELECTOR,
                "Parallel",
                side_effect=AssertionError("joblib non deve essere usato"),
            ),
        ):
            TRAIN_SELECTOR.generate_training_arrays(
                predictor,
                [self.source],
                self.compiled_dir,
                self.output_dir,
                "expected_fidelity",
                1,
                {"example|device_a"},
            )
        generate.assert_called_once()

    def test_only_complete_rl_manifest_record_is_strict_success(self) -> None:
        self.assertTrue(
            TRAIN_SELECTOR.is_strict_rl_success(
                self._strict_record(),
            )
        )

    def test_fallback_and_timeout_recovery_are_not_strict_rl_successes(self) -> None:
        records = {
            "fallback": self._strict_record(
                status="success_fallback",
                mode="fallback",
                fallback_reason="RL timeout",
            ),
            "timeout_recovery": self._strict_record(
                status="success_recovered_after_timeout",
                phase="rl",
            ),
        }
        for case, record in records.items():
            with self.subTest(case=case):
                self.assertFalse(TRAIN_SELECTOR.is_strict_rl_success(record))

    def test_strict_rl_success_rejects_invalid_termination_trace(self) -> None:
        invalid_records = {
            "not_terminated": self._strict_record(terminated=False),
            "missing_terminate": self._strict_record(
                passes=["Optimize1qGatesDecomposition"],
            ),
            "truncated": self._strict_record(truncated=True),
            "not_target_valid": self._strict_record(
                target_validation={"is_executable_on_target": False},
            ),
        }
        for case, record in invalid_records.items():
            with self.subTest(case=case):
                self.assertFalse(TRAIN_SELECTOR.is_strict_rl_success(record))

    def test_strict_rl_success_requires_matching_run_provenance(self) -> None:
        record = self._strict_record()
        expected = {
            "rl_max_steps": 64,
            "seed": 7,
            "model_sha256": "model-hash",
            "target_sha256": "target-hash",
        }
        self.assertTrue(TRAIN_SELECTOR.is_strict_rl_success(record, **expected))

        mismatches = {
            "rl_max_steps": 65,
            "seed": 8,
            "model_sha256": "different-model-hash",
            "target_sha256": "different-target-hash",
        }
        for field, value in mismatches.items():
            with self.subTest(field=field, condition="mismatch"):
                actual = dict(expected)
                actual[field] = value
                self.assertFalse(
                    TRAIN_SELECTOR.is_strict_rl_success(record, **actual),
                )

            with self.subTest(field=field, condition="missing"):
                incomplete_record = dict(record)
                incomplete_record.pop(field)
                self.assertFalse(
                    TRAIN_SELECTOR.is_strict_rl_success(
                        incomplete_record,
                        **expected,
                    ),
                )

    def test_strict_success_keys_require_matching_qasm_and_provenance_hashes(self) -> None:
        job = TRAIN_SELECTOR.CompilationJob(
            source=self.source,
            output=self.compiled_dir / "example_expected_fidelity-device_a.qasm",
            circuit_name="example",
            device_name="device_a",
            num_qubits=2,
        )
        self._write_qasm(job.output, self.circuit)
        manifest = self.root / "manifest.jsonl"
        record = self._strict_record(
            key=job.key,
            qasm_sha256=TRAIN_SELECTOR.file_sha256(job.output),
        )
        manifest.write_text(json.dumps(record) + "\n", encoding="utf-8")
        run_configuration = {
            "rl_max_steps": 64,
            "seed": 7,
            "model_sha256_by_device": {"device_a": "model-hash"},
            "target_sha256_by_device": {"device_a": "target-hash"},
        }

        self.assertEqual(
            TRAIN_SELECTOR.strict_rl_success_keys(
                [job],
                manifest,
                **run_configuration,
            ),
            {job.key},
        )

        changed_circuit = self.circuit.copy()
        changed_circuit.x(0)
        self._write_qasm(job.output, changed_circuit)
        self.assertEqual(
            TRAIN_SELECTOR.strict_rl_success_keys(
                [job],
                manifest,
                **run_configuration,
            ),
            set(),
        )

    def test_infrastructure_failures_do_not_consume_retry_budget(self) -> None:
        manifest = self.root / "manifest.jsonl"
        records = [
            {"key": "first|device", "attempt": 1, "status": "failed"},
            {
                "key": "first|device",
                "attempt": 9,
                "status": "rl_runtime_unavailable",
            },
            {
                "key": "second|device",
                "attempt": 4,
                "status": "rl_runtime_unavailable",
            },
            {"key": "third|device", "attempt": 7, "status": "rl_model_load_failed"},
            {"key": "fourth|device", "attempt": 8, "status": "rl_model_startup_timeout"},
        ]
        manifest.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

        attempts, statuses = TRAIN_SELECTOR.load_manifest(manifest)

        self.assertEqual(attempts, {"first|device": 1})
        self.assertEqual(statuses["first|device"], "rl_runtime_unavailable")
        self.assertEqual(statuses["second|device"], "rl_runtime_unavailable")

    def test_coverage_report_accepts_only_fully_covered_circuits(self) -> None:
        complete_source = self.source_dir / "complete.qasm"
        incomplete_source = self.source_dir / "incomplete.qasm"
        jobs = [
            TRAIN_SELECTOR.CompilationJob(
                source=complete_source,
                output=self.compiled_dir / "complete-device_a.qasm",
                circuit_name="complete",
                device_name="device_a",
                num_qubits=2,
            ),
            TRAIN_SELECTOR.CompilationJob(
                source=incomplete_source,
                output=self.compiled_dir / "incomplete-device_a.qasm",
                circuit_name="incomplete",
                device_name="device_a",
                num_qubits=2,
            ),
            TRAIN_SELECTOR.CompilationJob(
                source=incomplete_source,
                output=self.compiled_dir / "incomplete-device_b.qasm",
                circuit_name="incomplete",
                device_name="device_b",
                num_qubits=2,
            ),
        ]
        source_paths = {
            "complete": complete_source,
            "incomplete": incomplete_source,
        }
        successes = {"complete|device_a", "incomplete|device_a"}

        complete, missing = TRAIN_SELECTOR.coverage_report(
            jobs,
            source_paths,
            successes,
        )

        self.assertEqual(complete, [complete_source])
        self.assertEqual([job.key for job in missing], ["incomplete|device_b"])

        complete, missing = TRAIN_SELECTOR.coverage_report(
            jobs,
            source_paths,
            {job.key for job in jobs},
        )
        self.assertEqual(complete, [complete_source, incomplete_source])
        self.assertEqual(missing, [])

    def test_latest_manifest_record_ignores_interrupted_running_record(self) -> None:
        manifest = self.root / "manifest.jsonl"
        records = [
            {"key": "example|ibm_falcon_27", "status": "success", "mode": "rl"},
            {"key": "example|ibm_falcon_27", "status": "running"},
        ]
        manifest.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        latest = TRAIN_SELECTOR.latest_manifest_records(manifest)
        self.assertEqual(latest["example|ibm_falcon_27"]["status"], "success")

    def test_stale_qasm_is_not_recovered_as_current_rl_output(self) -> None:
        compiled_path = self.compiled_dir / "stale.qasm"
        self._write_qasm(compiled_path, self.circuit)
        previous_version = TRAIN_SELECTOR.file_version(compiled_path)
        self.assertFalse(
            TRAIN_SELECTOR.output_changed(compiled_path, previous_version),
        )

        changed_circuit = self.circuit.copy()
        changed_circuit.x(0)
        self._write_qasm(compiled_path, changed_circuit)
        self.assertTrue(TRAIN_SELECTOR.output_changed(compiled_path, previous_version))

    def test_partial_rl_failure_keeps_circuit_and_assigns_worst_score(self) -> None:
        successful_device = self.device_names[0]
        compiled_path = (
            self.compiled_dir
            / f"example_critical_depth-{successful_device}.qasm"
        )
        self._write_qasm(compiled_path, self.circuit)
        successful_key = f"example|{successful_device}"

        devices = [
            TRAIN_SELECTOR.get_device(device_name)
            for device_name in self.device_names
        ]
        predictor = SimpleNamespace(devices=devices)
        TRAIN_SELECTOR.generate_training_arrays(
            predictor,
            [self.source],
            self.compiled_dir,
            self.output_dir,
            "critical_depth",
            1,
            {successful_key},
        )

        training_data = np.load(
            self.output_dir / "training_data_critical_depth.npy",
            allow_pickle=True,
        )
        names = np.load(
            self.output_dir / "names_list_critical_depth.npy",
            allow_pickle=True,
        )
        scores = np.load(
            self.output_dir / "scores_list_critical_depth.npy",
            allow_pickle=True,
        )

        self.assertEqual(len(training_data), 1)
        self.assertEqual(str(names[0]), "example")
        self.assertEqual(str(training_data[0][1]), successful_device)
        self.assertGreater(float(scores[0][0]), TRAIN_SELECTOR.WORST_SCORE)
        self.assertEqual(float(scores[0][1]), TRAIN_SELECTOR.WORST_SCORE)


if __name__ == "__main__":
    unittest.main()

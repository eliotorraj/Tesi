from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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

    def test_fallback_manifest_record_is_not_an_rl_success(self) -> None:
        self.assertTrue(
            TRAIN_SELECTOR.is_strict_rl_success(
                {"status": "success", "mode": "rl"},
            )
        )
        self.assertFalse(
            TRAIN_SELECTOR.is_strict_rl_success(
                {
                    "status": "success_fallback",
                    "mode": "fallback",
                    "fallback_reason": "RL timeout",
                },
            )
        )
        self.assertTrue(
            TRAIN_SELECTOR.is_strict_rl_success(
                {"status": "success_recovered_after_timeout", "phase": "rl"},
            )
        )

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

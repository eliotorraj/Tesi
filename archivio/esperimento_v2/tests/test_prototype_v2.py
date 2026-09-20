from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from mqt.bench.targets import get_device
from mqt.predictor.ml.helper import create_feature_vector
from qiskit import QuantumCircuit

from prototype.quantum_assistant.adapters.hardware import (
    HardwareCatalogIntegrityError, MqtHardwareCatalog,
)
from prototype.quantum_assistant.adapters.llm import CallableLlmGateway
from prototype.quantum_assistant.adapters.request import QasmRequestParser, FEATURE_NAMES
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.models import UiSubmission
from qiskit_dataset.catalog import V2_CATALOG_PATH, load_catalog
from qiskit_dataset.experiment_v2 import stable_sha256
from scripts.mqt_predictor_protocol import FROZEN_TARGET_SHA256

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("freeze_method_plan", ROOT / "scripts/11_freeze_method_plan_v2.py")
FREEZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FREEZER)


class PrototypeV2Tests(unittest.TestCase):
    def test_parser_matches_dataset_for_extended_qasm_gates(self) -> None:
        source = '''OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
u(0.1,0.2,0.3) q[0];
cry(0.5) q[0],q[1];
cp(0.7) q[0],q[1];
rxx(0.4) q[0],q[1];
'''
        parsed = QasmRequestParser().parse(UiSubmission(
            request_id="extended-qasm", qasm2=source, user_text="",
            figure_of_merit="expected_fidelity",
        ))
        expected = QuantumCircuit.from_qasm_str(source)
        self.assertEqual(parsed.operation_names, tuple(sorted(expected.count_ops())))
        self.assertEqual(parsed.num_qubits, expected.num_qubits)
        for name, value in zip(FEATURE_NAMES, create_feature_vector(expected), strict=True):
            self.assertAlmostEqual(parsed.features[name], float(value))

    def test_default_service_uses_v2_and_frozen_targets(self) -> None:
        service = build_default_service(
            device_names=tuple(FROZEN_TARGET_SHA256), dataset_path=Path("unused.jsonl"),
            llm_gateway=CallableLlmGateway(lambda prompt: None),
        )
        snapshot = service.hardware_catalog.snapshot()
        self.assertEqual(snapshot.configuration_catalog_id, "qiskit_expected_fidelity_mqt_2_4_v2")
        self.assertEqual({d.device_id: d.target_hash for d in snapshot.devices}, FROZEN_TARGET_SHA256)

    def test_snapshot_is_stable_across_independent_processes(self) -> None:
        code = (
            "from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog; "
            "print(MqtHardwareCatalog(('ibm_falcon_27',)).snapshot().catalog_snapshot_id)"
        )
        values = [subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, check=True,
            capture_output=True, text=True, timeout=60,
        ).stdout.strip() for _ in range(2)]
        self.assertTrue(values[0].startswith("hardware_catalog_"))
        self.assertEqual(values[0], values[1])

    def test_target_calibration_drift_is_an_integrity_error(self) -> None:
        target = get_device("ibm_falcon_27")
        qargs = next(iter(target["cx"]))
        target["cx"][qargs].error += 0.001
        with patch("prototype.quantum_assistant.adapters.hardware.get_device", return_value=target):
            with self.assertRaises(HardwareCatalogIntegrityError):
                MqtHardwareCatalog(("ibm_falcon_27",)).snapshot()

    def test_v2_metadata_is_copied_and_affects_snapshot(self) -> None:
        catalog = load_catalog(V2_CATALOG_PATH)
        adapter = MqtHardwareCatalog(("ibm_falcon_27",), configuration_catalog=catalog)
        catalog.target_sha256["ibm_falcon_27"] = "0" * 64
        original = adapter.snapshot()
        self.assertEqual(original.devices[0].target_hash, FROZEN_TARGET_SHA256["ibm_falcon_27"])
        changed = MqtHardwareCatalog(("ibm_falcon_27",), configuration_catalog=replace(
            load_catalog(V2_CATALOG_PATH), execution_policy={"workers": 5, "timeout_seconds": 100},
        )).snapshot()
        self.assertNotEqual(original.catalog_snapshot_id, changed.catalog_snapshot_id)

    def test_wrong_software_version_is_rejected(self) -> None:
        catalog = replace(load_catalog(V2_CATALOG_PATH), required_versions={"qiskit": "0.0.0"})
        with self.assertRaises(HardwareCatalogIntegrityError):
            MqtHardwareCatalog(("ibm_falcon_27",), configuration_catalog=catalog)


class PlanAlignmentTests(unittest.TestCase):
    @staticmethod
    def plan(timeout=100, workers=6):
        core = {
            "split": "validation", "circuit_count": 1,
            "qiskit_execution_policy": {"timeout_seconds": timeout, "workers": workers},
            "random_selection": {"seed": 20260901, "rows": [{"selected_device_id": "ibm_falcon_27"}]},
        }
        return {**core, "plan_sha256": stable_sha256(core)}

    def test_policy_alignment_archives_exact_bytes_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "validation_method_plan.json"
            old = self.plan(300, 2); current = self.plan()
            original_bytes = json.dumps(old, indent=4).encode()
            output.write_bytes(original_bytes)
            options = {"align_execution_policy": True, "release_record": root / "release.json"}
            FREEZER.freeze_method_plan(output, current, **options)
            self.assertEqual(json.loads(output.read_text()), current)
            archive = root / "history" / f"validation_method_plan.{old['plan_sha256']}.json"
            self.assertEqual(archive.read_bytes(), original_bytes)
            record_path = next((root / "history").glob("*.alignment.json"))
            record = json.loads(record_path.read_text())
            self.assertTrue(record["random_selection_unchanged"])
            before = {p: p.read_bytes() for p in root.rglob("*.json")}
            FREEZER.freeze_method_plan(output, current, **options)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*.json")})

    def test_alignment_rejects_changed_draws_bad_hash_and_released_test(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "plan.json"; release = root / "release.json"
            for scenario in ("draw", "hash", "released", "no_flag", "other_policy"):
                with self.subTest(scenario=scenario):
                    old = self.plan(300, 2); current = self.plan()
                    if scenario == "draw":
                        old["random_selection"]["rows"][0]["selected_device_id"] = "ibm_falcon_127"
                        old["plan_sha256"] = stable_sha256({k:v for k,v in old.items() if k != "plan_sha256"})
                    elif scenario == "hash":
                        old["plan_sha256"] = "0" * 64
                    elif scenario == "released":
                        release.write_text("{}")
                    elif scenario == "other_policy":
                        old = self.plan(200, 2)
                    output.write_text(json.dumps(old))
                    before = output.read_bytes()
                    with self.assertRaises(ValueError):
                        FREEZER.freeze_method_plan(output, current,
                            align_execution_policy=scenario != "no_flag", release_record=release)
                    self.assertEqual(output.read_bytes(), before)
                    self.assertFalse((root / "history").exists())
                    if release.exists():
                        release.unlink()

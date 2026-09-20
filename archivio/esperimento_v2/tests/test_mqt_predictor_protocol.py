from __future__ import annotations

import sys
import unittest
from pathlib import Path

from mqt.bench.targets import get_device


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mqt_predictor_protocol import FROZEN_DEVICES  # noqa: E402
from mqt_predictor_protocol import FROZEN_TARGET_SHA256  # noqa: E402
from mqt_predictor_protocol import LEGACY_QISKIT_DATASET_TARGET_SHA256  # noqa: E402
from mqt_predictor_protocol import TARGET_FINGERPRINT_SCHEMA_VERSION  # noqa: E402
from mqt_predictor_protocol import legacy_comparable_target_sha256  # noqa: E402
from mqt_predictor_protocol import target_payload  # noqa: E402
from mqt_predictor_protocol import target_sha256  # noqa: E402


class PredictorProtocolTests(unittest.TestCase):
    def test_all_frozen_target_fingerprints_match_mqt_bench_2_2_3(self) -> None:
        observed = {
            device_name: target_sha256(get_device(device_name))
            for device_name in FROZEN_DEVICES
        }
        self.assertEqual(observed, FROZEN_TARGET_SHA256)

    def test_legacy_schema_comparison_detects_four_native_target_drifts(self) -> None:
        observed = {
            device_name: legacy_comparable_target_sha256(get_device(device_name))
            for device_name in FROZEN_DEVICES
        }
        drifted = {
            device_name
            for device_name in FROZEN_DEVICES
            if observed[device_name] != LEGACY_QISKIT_DATASET_TARGET_SHA256[device_name]
        }
        self.assertEqual(drifted, set(FROZEN_DEVICES[:-1]))
        self.assertEqual(observed[FROZEN_DEVICES[-1]], LEGACY_QISKIT_DATASET_TARGET_SHA256[FROZEN_DEVICES[-1]])

    def test_control_flow_instructions_have_stable_names(self) -> None:
        payload = target_payload(get_device("ibm_falcon_27"))
        self.assertEqual(
            payload["fingerprint_schema_version"],
            TARGET_FINGERPRINT_SCHEMA_VERSION,
        )
        names = [instruction["name"] for instruction in payload["instructions"]]
        self.assertIn("if_else", names)
        self.assertNotIn("<property object", " ".join(names))


if __name__ == "__main__":
    unittest.main()

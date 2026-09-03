from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mqt_model_artifacts import (  # noqa: E402
    EXPECTED_ACTION_COUNT,
    EXPECTED_FEATURE_COUNT,
    EXPECTED_OBSERVATION_KEYS,
    EXPECTED_RL_BQSKIT_PROFILE,
    REQUIRED_RL_ARCHIVE_MEMBERS,
    validate_ml_classifier,
    validate_rl_archive,
    validate_rl_training_metadata,
)
from mqt_predictor_protocol import FROZEN_DEVICES  # noqa: E402
from mqt_predictor_protocol import FROZEN_TARGET_SHA256  # noqa: E402
from mqt_predictor_protocol import PROTOCOL_ID  # noqa: E402


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_script("sync_models_for_tests", "05_sync_models.py")
QCOMPILE_AUDIT = load_script("validate_qcompile_for_tests", "07_validate_qcompile.py")
RL_AUDIT = load_script("audit_rl_models_for_tests", "08_audit_rl_models.py")


class DummyClassifier:
    def __init__(self, classes: tuple[str, ...]) -> None:
        self.classes_ = np.asarray(classes)
        self.n_features_in_ = EXPECTED_FEATURE_COUNT

    def predict_proba(self, values):
        rows = len(values)
        return np.full((rows, len(self.classes_)), 1.0 / len(self.classes_))


class ModelArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_rl_archive(self, path: Path, *, omit: str | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            for member in REQUIRED_RL_ARCHIVE_MEMBERS:
                if member == omit:
                    continue
                if member == "_stable_baselines3_version":
                    payload = b"2.9.0\n"
                elif member == "data":
                    spaces = ", ".join(
                        f"'{key}': Box(0.0, 1.0, (1,), float32)"
                        for key in sorted(EXPECTED_OBSERVATION_KEYS)
                    )
                    payload = json.dumps(
                        {
                            "num_timesteps": 100_000,
                            "action_space": {"n": str(EXPECTED_ACTION_COUNT)},
                            "observation_space": {"spaces": "{" + spaces + "}"},
                        }
                    ).encode("utf-8")
                else:
                    payload = b"test"
                archive.writestr(member, payload)

    def test_rl_archive_requires_stable_baselines_members(self) -> None:
        valid = self.root / "valid.zip"
        self.make_rl_archive(valid)
        metadata, errors = validate_rl_archive(valid)
        self.assertEqual(errors, [])
        self.assertEqual(metadata["sb3_version"], "2.9.0")
        self.assertEqual(metadata["action_count"], EXPECTED_ACTION_COUNT)
        self.assertEqual(set(metadata["observation_keys"]), EXPECTED_OBSERVATION_KEYS)

        incomplete = self.root / "incomplete.zip"
        self.make_rl_archive(incomplete, omit="policy.pth")
        _metadata, errors = validate_rl_archive(incomplete)
        self.assertTrue(any("policy.pth" in error for error in errors))

    def test_rl_training_metadata_is_bound_to_frozen_model_and_target(self) -> None:
        device_name = FROZEN_DEVICES[0]
        path = self.root / "model.metadata.json"
        payload = {
            "bqskit_profile": EXPECTED_RL_BQSKIT_PROFILE,
            "device": device_name,
            "figure_of_merit": "expected_fidelity",
            "max_steps": 64,
            "model_sha256": "model-digest",
            "mqt_predictor_version": "2.4.0",
            "num_timesteps": 100_000,
            "protocol": PROTOCOL_ID,
            "target": {
                "target_sha256": FROZEN_TARGET_SHA256[device_name],
            },
            "target_matches_frozen_protocol": True,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        _metadata, errors = validate_rl_training_metadata(
            path,
            device_name=device_name,
            model_sha256="model-digest",
            expected_max_steps=64,
        )
        self.assertEqual(errors, [])

        payload["model_sha256"] = "different"
        path.write_text(json.dumps(payload), encoding="utf-8")
        _metadata, errors = validate_rl_training_metadata(
            path,
            device_name=device_name,
            model_sha256="model-digest",
            expected_max_steps=64,
        )
        self.assertTrue(any("model_sha256" in error for error in errors))


    def test_unresolved_lfs_pointer_is_not_a_model(self) -> None:
        pointer = self.root / "pointer.zip"
        pointer.write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:" + "0" * 64 + "\nsize 123\n",
            encoding="utf-8",
        )
        _metadata, errors = validate_rl_archive(pointer)
        self.assertTrue(any("Git LFS" in error for error in errors))

    def test_ml_classifier_requires_all_frozen_classes_and_49_features(self) -> None:
        valid = self.root / "valid.joblib"
        joblib.dump(DummyClassifier(FROZEN_DEVICES), valid)
        metadata, errors = validate_ml_classifier(valid)
        self.assertEqual(errors, [])
        self.assertEqual(set(metadata["classes"]), set(FROZEN_DEVICES))

        incomplete = self.root / "incomplete.joblib"
        joblib.dump(DummyClassifier(FROZEN_DEVICES[:1]), incomplete)
        _metadata, errors = validate_ml_classifier(incomplete)
        self.assertTrue(any("classi non conformi" in error for error in errors))

    def test_atomic_copy_refuses_different_destination_without_overwrite(self) -> None:
        source = self.root / "source.zip"
        destination = self.root / "destination.zip"
        self.make_rl_archive(source)
        self.make_rl_archive(destination)
        with zipfile.ZipFile(destination, "a") as archive:
            archive.writestr("different", b"value")

        with self.assertRaises(FileExistsError):
            SYNC.atomic_copy(source, destination, "rl", overwrite=False)
        self.assertTrue(SYNC.atomic_copy(source, destination, "rl", overwrite=True))
        self.assertEqual(source.read_bytes(), destination.read_bytes())

    def test_sync_scope_contains_only_frozen_artifacts(self) -> None:
        pairs = SYNC.artifact_pairs(self.root, "all")
        self.assertEqual(len(pairs), len(FROZEN_DEVICES) + 1)
        self.assertEqual(
            {pair.name for pair in pairs if pair.kind == "rl"},
            {f"model_expected_fidelity_{device}.zip" for device in FROZEN_DEVICES},
        )
        self.assertEqual(
            [pair.name for pair in pairs if pair.kind == "ml"],
            ["trained_clf_expected_fidelity.joblib"],
        )


class QcompileAuditTests(unittest.TestCase):
    def test_strict_result_requires_terminate_and_target_valid_output(self) -> None:
        valid = {
            "status": "success",
            "mode": "rl",
            "device": FROZEN_DEVICES[0],
            "passes": ["BasisTranslator", "terminate"],
            "terminated": True,
            "truncated": False,
            "validation": {"is_executable_on_target": True},
            "expected_fidelity": 0.9,
        }
        self.assertEqual(QCOMPILE_AUDIT.strict_result_problems(valid), [])

        truncated = dict(
            valid,
            passes=["BasisTranslator"],
            terminated=False,
            truncated=True,
        )
        self.assertIn(
            "trace non terminato da terminate",
            QCOMPILE_AUDIT.strict_result_problems(truncated),
        )
        self.assertIn(
            "episodio RL troncato",
            QCOMPILE_AUDIT.strict_result_problems(truncated),
        )

        invalid_target = dict(valid, validation={"is_executable_on_target": False})
        self.assertIn(
            "circuito non eseguibile sul Target",
            QCOMPILE_AUDIT.strict_result_problems(invalid_target),
        )

    def test_strict_result_rejects_device_outside_protocol(self) -> None:
        result = {
            "status": "success",
            "device": "not_frozen",
            "passes": ["terminate"],
            "validation": {"is_executable_on_target": True},
            "expected_fidelity": 1.0,
        }
        self.assertTrue(
            any(
                "device fuori protocollo" in problem
                for problem in QCOMPILE_AUDIT.strict_result_problems(result)
            )
        )


class RLAuditTests(unittest.TestCase):
    def test_compilation_evidence_distinguishes_raw_and_strict_success(self) -> None:
        strict = {
            "device": FROZEN_DEVICES[0],
            "status": "success",
            "mode": "rl",
            "validation_version": 1,
            "terminated": True,
            "truncated": False,
            "termination_reason": "terminate",
            "passes": ["terminate"],
            "target_validation": {"is_executable_on_target": True},
            "qasm_sha256": "digest",
            "model_sha256": "model-digest",
            "mqt_predictor_version": "2.4.0",
            "target_sha256": "target-digest",
        }
        legacy = {
            "device": FROZEN_DEVICES[0],
            "status": "success",
        }
        timeout = {
            "device": FROZEN_DEVICES[0],
            "status": "timeout",
        }
        evidence = RL_AUDIT.compilation_evidence(
            {"strict": strict, "legacy": legacy, "timeout": timeout},
            FROZEN_DEVICES[0],
            model_sha256="model-digest",
            target_sha256="target-digest",
        )
        self.assertEqual(evidence["raw_successes"], 2)
        self.assertEqual(evidence["strict_successes"], 1)
        self.assertEqual(evidence["pairs"], 3)


if __name__ == "__main__":
    unittest.main()

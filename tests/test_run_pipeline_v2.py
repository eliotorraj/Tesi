from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_script():
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_v2_for_tests",
        SCRIPTS_DIR / "16_run_pipeline_v2.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = load_script()


class PipelineRunnerTests(unittest.TestCase):
    def test_named_groups_partition_the_frozen_devices_exactly(self) -> None:
        flattened = tuple(
            device
            for devices in RUNNER.RL_GROUPS.values()
            for device in devices
        )
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(set(flattened), set(RUNNER.FROZEN_DEVICES))

    def test_rl_command_is_explicit_and_never_overwrites(self) -> None:
        device = RUNNER.FROZEN_DEVICES[0]
        command = RUNNER.rl_training_command(device, None)
        self.assertIn("03_train_rl_model.py", command[1])
        self.assertEqual(command[command.index("--device") + 1], device)
        self.assertEqual(
            command[command.index("--timesteps") + 1],
            str(RUNNER.RL_TRAINING_TIMESTEPS),
        )
        self.assertEqual(command[command.index("--seed") + 1], "0")
        self.assertNotIn("--allow-overwrite", command)
        self.assertNotIn("--allow-target-drift", command)

    def test_qiskit_orchestration_cannot_request_test(self) -> None:
        with patch.object(RUNNER, "run_checked") as mocked:
            RUNNER.run_qiskit_full(
                SimpleNamespace(workers=2, timeout_seconds=300)
            )
        commands = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(len(commands), len(RUNNER.FROZEN_DEVICES) * 4 + 1)
        for command in commands:
            self.assertNotIn("--include-test", command)
            if "--split" in command:
                self.assertIn(
                    command[command.index("--split") + 1],
                    ("train", "validation"),
                )

    def test_canary_runs_one_missing_train_attempt_per_device(self) -> None:
        with patch.object(RUNNER, "run_checked") as mocked:
            RUNNER.run_qiskit_canary(
                SimpleNamespace(workers=2, timeout_seconds=300)
            )
        commands = [call.args[0] for call in mocked.call_args_list]
        generation = [
            command for command in commands if "--limit-runs" in command
        ]
        self.assertEqual(len(generation), len(RUNNER.FROZEN_DEVICES))
        for command in generation:
            self.assertEqual(command[command.index("--split") + 1], "train")
            self.assertEqual(command[command.index("--limit-runs") + 1], "1")

    def test_resume_specs_accept_relative_paths_and_reject_duplicates(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            checkpoint = Path(directory) / "checkpoint.zip"
            checkpoint.write_bytes(b"checkpoint")
            relative = checkpoint.relative_to(PROJECT_ROOT)
            device = RUNNER.FROZEN_DEVICES[0]
            parsed = RUNNER.parse_resume_specs([f"{device}={relative}"])
            self.assertEqual(parsed[device], checkpoint.resolve())
            with self.assertRaises(SystemExit):
                RUNNER.parse_resume_specs(
                    [f"{device}={relative}", f"{device}={relative}"]
                )

    def test_invalid_qiskit_split_is_rejected_in_code(self) -> None:
        with self.assertRaises(ValueError):
            RUNNER.qiskit_generate_command(
                RUNNER.FROZEN_DEVICES[0],
                "test",
                workers=2,
                timeout_seconds=300,
            )


if __name__ == "__main__":
    unittest.main()

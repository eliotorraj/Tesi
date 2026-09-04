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
    def test_models_group_contains_all_frozen_devices_in_order(self) -> None:
        self.assertEqual(RUNNER.RL_GROUPS["models"], RUNNER.FROZEN_DEVICES)

    def test_rl_command_is_explicit_and_never_overwrites(self) -> None:
        device = RUNNER.FROZEN_DEVICES[0]
        command = RUNNER.rl_training_command(device, None)
        self.assertIn("03_train_rl_model.py", command[1])
        self.assertEqual(command[command.index("--device") + 1], device)
        self.assertEqual(
            command[command.index("--timesteps") + 1],
            str(RUNNER.RL_TRAINING_TIMESTEPS),
        )
        self.assertEqual(
            command[command.index("--checkpoint-every") + 1],
            str(RUNNER.RL_CHECKPOINT_EVERY),
        )
        self.assertEqual(RUNNER.RL_CHECKPOINT_EVERY, 10_240)
        self.assertEqual(RUNNER.RL_CHECKPOINT_EVERY, 5 * RUNNER.RL_ROLLOUT_STEPS)
        self.assertEqual(RUNNER.RL_FINAL_TIMESTEPS, 100_352)
        self.assertEqual(command[command.index("--seed") + 1], "0")
        self.assertNotIn("--allow-overwrite", command)
        self.assertNotIn("--allow-target-drift", command)

    def test_resume_rejects_unaligned_and_emergency_snapshots(self) -> None:
        device = RUNNER.FROZEN_DEVICES[0]

        def metadata(num_timesteps: int) -> dict[str, int]:
            return {
                "seed": RUNNER.RL_SEED,
                "target_timesteps": RUNNER.RL_TRAINING_TIMESTEPS,
                "num_timesteps": num_timesteps,
            }

        with (
            patch.object(RUNNER, "file_sha256", return_value="digest"),
            patch.object(
                RUNNER,
                "validate_rl_archive",
                side_effect=lambda _path: ({}, []),
            ),
            patch.object(
                RUNNER,
                "validate_rl_training_metadata",
                side_effect=[
                    (metadata(2_048), []),
                    (metadata(3_000), []),
                    (metadata(2_048), []),
                ],
            ),
            patch.object(
                RUNNER,
                "SOURCE_MANIFEST_V2",
                Path("/definitely-missing-source-manifest.json"),
            ),
        ):
            aligned_steps, aligned_errors = RUNNER.checkpoint_problems(
                Path("model_latest_rollout.zip"),
                device,
            )
            _unaligned_steps, unaligned_errors = RUNNER.checkpoint_problems(
                Path("model_3000_steps.zip"),
                device,
            )
            _emergency_steps, emergency_errors = RUNNER.checkpoint_problems(
                Path("model_interrupted.zip"),
                device,
            )

        self.assertEqual(aligned_steps, 2_048)
        self.assertEqual(aligned_errors, [])
        self.assertTrue(
            any("non allineato" in error for error in unaligned_errors)
        )
        self.assertTrue(
            any("emergenza" in error for error in emergency_errors)
        )

    def test_ml_canary_is_compile_only_and_reusable(self) -> None:
        with patch.object(RUNNER, "run_checked") as mocked:
            RUNNER.run_ml_canary(
                SimpleNamespace(
                    timeout=300,
                    startup_timeout=240,
                    num_workers=1,
                    max_attempts=1,
                    limit_circuits=10,
                )
            )
        commands = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(len(commands), 3)
        command = commands[-1]
        self.assertIn("04_train_device_selector.py", command[1])
        self.assertIn("--compile-only", command)
        self.assertEqual(command[command.index("--limit-circuits") + 1], "10")
        self.assertEqual(command[command.index("--timeout") + 1], "300")
        self.assertNotIn("--allow-incomplete", command)

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

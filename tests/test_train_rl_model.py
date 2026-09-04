from __future__ import annotations

import importlib.util
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from mqt.predictor.rl import actions as predictor_actions
from mqt.predictor.rl.actions import bqskit_actions as predictor_bqskit_actions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "03_train_rl_model.py"
SPEC = importlib.util.spec_from_file_location("train_rl_model", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
TRAIN_RL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRAIN_RL
SPEC.loader.exec_module(TRAIN_RL)


class RLTrainingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_module_compile = predictor_bqskit_actions.bqskit_compile
        self.original_script_compile = TRAIN_RL._ORIGINAL_BQSKIT_COMPILE

    def tearDown(self) -> None:
        predictor_bqskit_actions.bqskit_compile = self.original_module_compile
        TRAIN_RL._ORIGINAL_BQSKIT_COMPILE = self.original_script_compile

    def test_runtime_override_selects_max_synthesis_size_from_gate_arity(self) -> None:
        captured: list[dict[str, Any]] = []

        def fake_compile(*args: Any, **kwargs: Any) -> str:
            captured.append({"args": args, "kwargs": kwargs})
            return "compiled"

        TRAIN_RL._ORIGINAL_BQSKIT_COMPILE = fake_compile
        TRAIN_RL.configure_bqskit_runtime(seed=7)

        for gate_arities, expected_limit in (((1, 2), 2), ((1, 2, 3), 3)):
            circuit = SimpleNamespace(
                gate_set_no_blocks=[SimpleNamespace(num_qudits=arity) for arity in gate_arities]
            )
            result = predictor_bqskit_actions.bqskit_compile(
                circuit,
                optimization_level=1,
                synthesis_epsilon=0.1,
                max_synthesis_size=8,
                seed=10,
                num_workers=1,
            )

            self.assertEqual(result, "compiled")
            self.assertEqual(captured[-1]["args"], (circuit,))
            self.assertEqual(
                captured[-1]["kwargs"],
                {
                    "optimization_level": 1,
                    "synthesis_epsilon": 0.1,
                    "max_synthesis_size": expected_limit,
                    "seed": 7,
                    "num_workers": 1,
                },
            )

    def test_runtime_override_does_not_change_action_ids(self) -> None:
        before = [
            (action.name, action.origin, action.pass_type)
            for actions in predictor_actions.get_actions_by_pass_type().values()
            for action in actions
        ]

        TRAIN_RL.configure_bqskit_runtime()

        after = [
            (action.name, action.origin, action.pass_type)
            for actions in predictor_actions.get_actions_by_pass_type().values()
            for action in actions
        ]
        self.assertEqual(after, before)


    def test_checkpoint_callback_saves_after_completed_rollouts(self) -> None:
        checkpoint_dir = Path("/tmp/checkpoints")
        callback = TRAIN_RL.AtomicCheckpointCallback(
            save_freq=10_240,
            save_dir=checkpoint_dir,
            name_prefix="model",
            metadata_factory=lambda path, steps: {
                "path": str(path),
                "num_timesteps": steps,
            },
        )
        callback.model = SimpleNamespace(num_timesteps=0)

        def fake_save(_model: Any, path: Path) -> Path:
            return path

        with (
            patch.object(
                TRAIN_RL,
                "save_model_atomically",
                side_effect=fake_save,
            ) as save,
            patch.object(TRAIN_RL, "write_training_metadata") as metadata,
        ):
            callback._on_rollout_start()
            self.assertEqual(save.call_count, 0)

            callback.model.num_timesteps = 2_048
            callback._on_rollout_start()
            self.assertEqual(
                save.call_args_list[-1].args[1].name,
                "model_latest_rollout.zip",
            )

            callback.model.num_timesteps = 10_240
            callback._on_rollout_start()

        saved_names = [call.args[1].name for call in save.call_args_list]
        self.assertEqual(
            saved_names,
            ["model_latest_rollout.zip", "model_latest_rollout.zip", "model_10240_steps.zip"],
        )
        self.assertEqual(metadata.call_count, 3)
    def test_bqskit_action_timeout_interrupts_a_stalled_action(self) -> None:
        with self.assertRaises(TRAIN_RL.BQSKitActionTimeoutError):
            with TRAIN_RL.bqskit_action_timeout(0.01):
                time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()

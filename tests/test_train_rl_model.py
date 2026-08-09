from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import mqt.predictor.rl.actions as predictor_actions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "03_train_rl_model.py"
SPEC = importlib.util.spec_from_file_location("train_rl_model", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
TRAIN_RL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRAIN_RL
SPEC.loader.exec_module(TRAIN_RL)


class RLTrainingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_module_compile = predictor_actions.bqskit_compile
        self.original_script_compile = TRAIN_RL._ORIGINAL_BQSKIT_COMPILE

    def tearDown(self) -> None:
        predictor_actions.bqskit_compile = self.original_module_compile
        TRAIN_RL._ORIGINAL_BQSKIT_COMPILE = self.original_script_compile

    def test_runtime_override_selects_max_synthesis_size_from_gate_arity(self) -> None:
        captured: list[dict[str, Any]] = []

        def fake_compile(*args: Any, **kwargs: Any) -> str:
            captured.append({"args": args, "kwargs": kwargs})
            return "compiled"

        TRAIN_RL._ORIGINAL_BQSKIT_COMPILE = fake_compile
        TRAIN_RL.configure_bqskit_runtime()

        for gate_arities, expected_limit in (((1, 2), 2), ((1, 2, 3), 3)):
            circuit = SimpleNamespace(
                gate_set_no_blocks=[SimpleNamespace(num_qudits=arity) for arity in gate_arities]
            )
            result = predictor_actions.bqskit_compile(
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
                    "seed": 10,
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


if __name__ == "__main__":
    unittest.main()
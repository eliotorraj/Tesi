from __future__ import annotations

import importlib.util
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import numpy as np
import torch
from mqt.bench.targets import get_device
from mqt.predictor.rl import Predictor, actions as predictor_actions
from qiskit import QuantumCircuit, qasm2
from stable_baselines3.common.preprocessing import preprocess_obs
from mqt.predictor.rl.actions import bqskit_actions as predictor_bqskit_actions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "03_train_rl_model.py"
SPEC = importlib.util.spec_from_file_location("train_rl_model", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
TRAIN_RL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRAIN_RL
SPEC.loader.exec_module(TRAIN_RL)


class RLObservationSpaceTests(unittest.TestCase):
    @staticmethod
    def circuit() -> QuantumCircuit:
        circuit = QuantumCircuit(2)
        circuit.x(0)
        circuit.cz(0, 1)
        circuit.measure_all()
        return circuit

    def mapped_observation(self, environment: Any) -> dict[str, Any]:
        observation, _ = environment.reset(self.circuit(), seed=0)
        for name in ("BasisTranslator", "DenseLayout"):
            action = next(
                index for index in environment.valid_actions
                if environment.action_set[index].name == name
            )
            observation, _, terminated, truncated, info = environment.step(action)
            self.assertFalse(terminated)
            self.assertFalse(truncated, info)
        return observation

    def test_smaller_targets_keep_existing_model_spaces(self) -> None:
        for device_name in ("ibm_falcon_27", "ibm_falcon_127", "quantinuum_h2_56"):
            with self.subTest(device=device_name):
                environment = Predictor(
                    device=get_device(device_name), figure_of_merit="expected_fidelity"
                ).env
                original_spaces = dict(environment.observation_space.spaces)
                TRAIN_RL.configure_qubit_observation_space(environment)
                for key, original in original_spaces.items():
                    self.assertIs(environment.observation_space[key], original)
                self.assertEqual(environment.observation_space["num_qubits"].n, 128)

    def test_mapped_heron_observations_are_encodable_without_clipping(self) -> None:
        for device_name in ("ibm_heron_133", "ibm_heron_156"):
            with self.subTest(device=device_name):
                environment = Predictor(
                    device=get_device(device_name), figure_of_merit="expected_fidelity"
                ).env
                original_spaces = dict(environment.observation_space.spaces)
                observation = self.mapped_observation(environment)
                width = environment.device.num_qubits
                self.assertEqual(observation["num_qubits"], width)
                tensors = {
                    key: torch.as_tensor(value).unsqueeze(0)
                    for key, value in observation.items()
                }
                with self.assertRaisesRegex(RuntimeError, "Class values must be smaller"):
                    preprocess_obs(tensors, environment.observation_space)

                metadata = TRAIN_RL.configure_qubit_observation_space(environment)
                encoded = preprocess_obs(tensors, environment.observation_space)
                self.assertTrue(environment.observation_space.contains(observation))
                self.assertEqual(encoded["num_qubits"].shape, (1, width + 1))
                self.assertEqual(encoded["num_qubits"].argmax().item(), width)
                self.assertEqual(metadata["num_qubits_n"], width + 1)
                for key, original in original_spaces.items():
                    if key != "num_qubits":
                        self.assertIs(environment.observation_space[key], original)

    def next_action_mask(self, environment: Any) -> np.ndarray:
        # Exercise actual MQT passes deterministically, avoiding expensive
        # random BQSKit actions in this pipeline-only training check.
        name = ("BasisTranslator", "DenseLayout", "terminate")[environment.num_steps]
        index = next(
            index for index in environment.valid_actions
            if environment.action_set[index].name == name
        )
        mask = np.zeros(environment.action_space.n, dtype=bool)
        mask[index] = True
        return mask

    def test_heron_ppo_training_resume_and_inference(self) -> None:
        for device_name in ("ibm_heron_133", "ibm_heron_156"):
            with self.subTest(device=device_name), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                qasm2.dump(self.circuit(), directory / "circuit_2.qasm")

                def new_environment() -> Any:
                    environment = Predictor(
                        device=get_device(device_name),
                        figure_of_merit="expected_fidelity",
                        path_training_circuits=directory,
                        max_steps=64,
                    ).env
                    TRAIN_RL.configure_qubit_observation_space(environment)
                    return environment

                environment = new_environment()
                model = TRAIN_RL.MaskablePPO(
                    TRAIN_RL.MaskableMultiInputActorCriticPolicy,
                    environment,
                    n_steps=4,
                    batch_size=4,
                    n_epochs=1,
                    policy_kwargs={
                        "net_arch": {"pi": [2], "vf": [2]},
                        "ortho_init": False,
                    },
                    seed=0,
                    device="cpu",
                )
                with patch.object(
                    environment, "action_masks",
                    side_effect=lambda: self.next_action_mask(environment),
                ):
                    model.learn(total_timesteps=4)
                self.assertEqual(model.num_timesteps, 4)
                self.assertEqual(model._n_updates, 1)
                checkpoint = directory / "model.zip"
                model.save(checkpoint)

                resumed_environment = new_environment()
                resumed = TRAIN_RL.load_model_or_exit(checkpoint, env=resumed_environment)
                with patch.object(
                    resumed_environment, "action_masks",
                    side_effect=lambda: self.next_action_mask(resumed_environment),
                ):
                    resumed.learn(total_timesteps=4, reset_num_timesteps=False)
                self.assertEqual(resumed.num_timesteps, 8)
                self.assertEqual(resumed._n_updates, 2)

                # qcompile and the ML workers load the saved policy without
                # an env. Prediction must use the widened space from the ZIP,
                # even when MQT constructs an unmodified inference env.
                inference_environment = Predictor(
                    device=get_device(device_name), figure_of_merit="expected_fidelity"
                ).env
                observation = self.mapped_observation(inference_environment)
                loaded = TRAIN_RL.MaskablePPO.load(checkpoint, device="cpu")
                action, _ = loaded.predict(
                    observation,
                    action_masks=inference_environment.action_masks(),
                    deterministic=True,
                )
                self.assertIn(int(action), inference_environment.valid_actions)


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


    def test_vf2_budget_is_local_and_preserves_action_ids(self) -> None:
        environment = Predictor(device=get_device("quantinuum_h2_56"), figure_of_merit="expected_fidelity").env
        other = Predictor(device=get_device("quantinuum_h2_56"), figure_of_merit="expected_fidelity").env
        before = dict(environment.action_set)
        metadata = TRAIN_RL.configure_vf2_layout_runtime(environment, seed=7)
        self.assertEqual(metadata, TRAIN_RL.vf2_layout_metadata(7))
        self.assertEqual(list(environment.action_set), list(before))
        for index, old_action in before.items():
            action = environment.action_set[index]
            self.assertEqual((action.name, action.origin, action.pass_type),
                             (old_action.name, old_action.origin, old_action.pass_type))
            self.assertIs(other.action_set[index], old_action)
            if action.name == "VF2Layout":
                bounded = action.transpile_pass(environment.device)[0]
                original = old_action.transpile_pass(environment.device)[0]
                self.assertEqual(bounded.call_limit, 10_000)
                self.assertEqual(bounded.seed, 7)
                self.assertIsNone(original.call_limit)
                self.assertIsNot(action, old_action)
            else:
                self.assertIs(action, old_action)

    def test_vf2_layout_completes_on_symmetric_quantinuum_target(self) -> None:
        environment = Predictor(device=get_device("quantinuum_h2_56"), figure_of_merit="expected_fidelity").env
        TRAIN_RL.configure_vf2_layout_runtime(environment)
        circuit = QuantumCircuit(20)
        for qubit in range(19):
            circuit.cx(qubit, qubit + 1)
        circuit.measure_all()
        environment.reset(circuit, seed=0)
        for name in ("BasisTranslator", "VF2Layout"):
            action = next(index for index in environment.valid_actions
                          if environment.action_set[index].name == name)
            _, _, terminated, truncated, info = environment.step(action)
            self.assertFalse(terminated)
            self.assertFalse(truncated, info)
        self.assertIsNotNone(environment.layout)
        self.assertEqual(environment.state.num_qubits, 56)
        self.assertTrue(environment.valid_actions)

    def test_vf2_no_solution_leaves_other_layout_actions_available(self) -> None:
        environment = Predictor(device=get_device("ibm_falcon_27"), figure_of_merit="expected_fidelity").env
        TRAIN_RL.configure_vf2_layout_runtime(environment)
        # Falcon's coupling graph has no triangle. The native search must return
        # without a layout; MQT must still allow another mapping action.
        circuit = QuantumCircuit(3)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(2, 0)
        circuit.measure_all()
        environment.reset(circuit, seed=0)
        for name in ("BasisTranslator", "VF2Layout"):
            action = next(index for index in environment.valid_actions
                          if environment.action_set[index].name == name)
            _, _, terminated, truncated, info = environment.step(action)
            self.assertFalse(terminated)
            self.assertFalse(truncated, info)
        self.assertIsNone(environment.layout)
        self.assertEqual(environment.state.num_qubits, 3)
        self.assertIn("DenseLayout", [environment.action_set[index].name
                                      for index in environment.valid_actions])

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

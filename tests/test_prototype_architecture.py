from __future__ import annotations

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.qasm2 import dump as qasm_dump

from prototype.quantum_assistant.adapters.context import (
    JsonDatasetContextRetriever,
)
from prototype.quantum_assistant.adapters.llm import CallableLlmGateway
from prototype.quantum_assistant.adapters.parsing import (
    QasmRequestParser,
    WidthCompatibilityFilter,
)
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.models import (
    ApprovedCompilation,
    HardwareProfile,
    UiSubmission,
)
from prototype.quantum_assistant.services import ConfirmationRequiredError


def qasm_for_two_qubit_circuit() -> str:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    stream = StringIO()
    qasm_dump(circuit, stream)
    return stream.getvalue()


def valid_llm_response(device_id: str) -> dict[str, object]:
    return {
        "selected_device": device_id,
        "figure_of_merit": "expected_fidelity",
        "compiler": "qiskit",
        "qiskit_plan": {
            "optimization_level": 1,
            "seed_transpiler": 7,
            "layout_method": None,
            "routing_method": None,
        },
        "explanation": "Il device supporta la larghezza del circuito.",
        "evidence": ["live_request.circuit.num_qubits"],
        "warnings": [],
    }


class PrototypeArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.submission = UiSubmission(
            request_id="request-1",
            user_text="Scegli un device e proponi una compilazione.",
            qasm2=qasm_for_two_qubit_circuit(),
            figure_of_merit="expected_fidelity",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_invalid_llm_response_is_retried_then_compiled_after_confirmation(
        self,
    ) -> None:
        prompts = []
        responses = [
            valid_llm_response("device_not_available"),
            valid_llm_response("ibm_falcon_27"),
        ]

        def callback(prompt):
            prompts.append(prompt)
            return responses[len(prompts) - 1]

        service = build_default_service(
            device_names=("ibm_falcon_27",),
            dataset_path=self.root / "not_ready_yet.json",
            llm_gateway=CallableLlmGateway(callback),
            max_llm_attempts=2,
            retrieval_limit=3,
        )
        result = service.recommend(self.submission)

        self.assertEqual(result.attempts, 2)
        self.assertEqual(
            result.recommendation.selected_device,
            "ibm_falcon_27",
        )
        self.assertTrue(
            prompts[1].payload["previous_validation_errors"],
        )

        with self.assertRaises(ConfirmationRequiredError):
            service.compile_approved(
                ApprovedCompilation(
                    recommendation_result=result,
                    user_confirmed=False,
                )
            )

        artifact = service.compile_approved(
            ApprovedCompilation(
                recommendation_result=result,
                user_confirmed=True,
            )
        )
        self.assertEqual(artifact.device_id, "ibm_falcon_27")
        self.assertTrue(artifact.validation["is_executable_on_target"])
        self.assertIn("OPENQASM 2.0", artifact.qasm2)

    def test_width_filter_marks_small_hardware_unavailable(self) -> None:
        request = QasmRequestParser().parse(self.submission)
        report = WidthCompatibilityFilter().filter(
            request,
            (
                HardwareProfile(
                    device_id="one_qubit_device",
                    num_qubits=1,
                    operation_names=("x",),
                    coupling_edges=(),
                ),
                HardwareProfile(
                    device_id="two_qubit_device",
                    num_qubits=2,
                    operation_names=("x", "cx"),
                    coupling_edges=((0, 1),),
                ),
            ),
        )

        self.assertEqual(report.available_device_ids, ("two_qubit_device",))
        self.assertEqual(
            report.unavailable["one_qubit_device"],
            ("insufficient_qubits:2>1",),
        )

    def test_json_retriever_exposes_only_prompt_input(self) -> None:
        parser = QasmRequestParser()
        request = parser.parse(self.submission)
        hardware = HardwareProfile(
            device_id="ibm_falcon_27",
            num_qubits=27,
            operation_names=("x", "cx"),
            coupling_edges=((0, 1),),
        )
        report = WidthCompatibilityFilter().filter(request, (hardware,))
        dataset = {
            "records": [
                {
                    "record_id": "record-1",
                    "input": {
                        "objective": {"name": "expected_fidelity"},
                        "circuit": {
                            "name": "historical",
                            "summary": {"num_qubits": 2},
                            "features": {"by_name": dict(request.features)},
                            "qasm2": "historical qasm intentionally omitted",
                        },
                        "compatible_backends": [
                            {"id": "ibm_falcon_27", "num_qubits": 27}
                        ],
                        "user_constraints": {},
                    },
                    "expected_output": {
                        "selected_device": "secret_training_target"
                    },
                    "deterministic_ground_truth": {
                        "candidate_outcomes": ["evaluation_only"]
                    },
                }
            ]
        }
        dataset_path = self.root / "dataset.json"
        dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

        examples = JsonDatasetContextRetriever(dataset_path).retrieve(
            request,
            report,
            limit=1,
        )

        self.assertEqual(len(examples), 1)
        serialized = json.dumps(examples[0].prompt_input)
        self.assertNotIn("secret_training_target", serialized)
        self.assertNotIn("evaluation_only", serialized)
        self.assertNotIn("historical qasm intentionally omitted", serialized)


if __name__ == "__main__":
    unittest.main()

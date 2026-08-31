from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from io import StringIO
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.qasm2 import dump as qasm_dump

from prototype.quantum_assistant.adapters.llm import CallableLlmGateway
from prototype.quantum_assistant.controller import PrototypeController
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.models import (
    CompilationArtifact,
    EvidenceRegistry,
    UiSubmission,
)
from prototype.quantum_assistant.services import (
    ConfirmationRequiredError,
    LlmValidationExhaustedError,
)


def _qasm2() -> str:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    stream = StringIO()
    qasm_dump(circuit, stream)
    return stream.getvalue()


def _valid_response(
    prompt,
    *,
    selected_device: str = "ibm_falcon_27",
) -> dict[str, object]:
    live_request = prompt.payload["live_request"]
    return {
        "schema_version": "2.0.0",
        "request_id": live_request["request_id"],
        "catalog_snapshot_id": live_request["catalog_snapshot_id"],
        "selected_device": selected_device,
        "figure_of_merit": "expected_fidelity",
        "compiler": "qiskit",
        "qiskit_plan": {
            "optimization_level": 2,
            "seed_transpiler": 7,
            "layout_method": None,
            "routing_method": None,
        },
        "evidence_refs": [],
        "claims": [
            {
                "claim_id": "live-compatibility",
                "claim_type": "live_compatibility",
                "parameters": {"device_id": selected_device},
                "evidence_ref_ids": [],
            },
            {
                "claim_id": "historical-evidence-unavailable",
                "claim_type": "historical_evidence_unavailable",
                "parameters": {},
                "evidence_ref_ids": [],
            },
        ],
    }


class _CountingRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def retrieve(self, request, compatibility, *, limit):
        del request, compatibility, limit
        self.calls += 1
        return ()


class _FakeCompiler:
    def __init__(self) -> None:
        self.calls = 0

    def compile(self, request, recommendation):
        del request
        self.calls += 1
        return CompilationArtifact(
            device_id=recommendation.selected_device,
            qasm2="OPENQASM 2.0;\nqreg q[1];\n",
            depth=0,
            size=0,
            operation_counts={},
            validation={"is_executable_on_target": True},
            compiler_metadata={"compiler": "fake"},
        )


class LlmOutputValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.submission = UiSubmission(
            request_id="request-output-validation",
            user_text="Scegli una configurazione valida.",
            qasm2=_qasm2(),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _service(
        self,
        callback,
        *,
        max_attempts: int = 3,
        devices: tuple[str, ...] = ("ibm_falcon_27",),
    ):
        return build_default_service(
            device_names=devices,
            dataset_path=self.root / "missing.jsonl",
            llm_gateway=CallableLlmGateway(callback),
            max_llm_attempts=max_attempts,
            retrieval_limit=2,
        )

    def test_valid_json_text_and_mapping_are_accepted_first_pass(self) -> None:
        for output_kind in ("text", "mapping", "text_with_whitespace"):
            with self.subTest(output_kind=output_kind):
                prompts = []

                def callback(prompt):
                    prompts.append(prompt)
                    response = _valid_response(prompt)
                    if output_kind == "mapping":
                        return response
                    encoded = json.dumps(response)
                    if output_kind == "text_with_whitespace":
                        return f" \n{encoded}\t "
                    return encoded

                result = self._service(callback, max_attempts=1).recommend(
                    self.submission
                )
                self.assertEqual(result.attempts, 1)
                self.assertEqual(len(prompts), 1)
                self.assertEqual(
                    prompts[0].payload["previous_validation_errors"],
                    [],
                )
                self.assertEqual(
                    result.recommendation.explanation,
                    (
                        "Il dispositivo ibm_falcon_27 rispetta i vincoli "
                        "verificati per la richiesta corrente. Tra i circuiti "
                        "più simili recuperati non sono disponibili risultati "
                        "storici utilizzabili per sostenere la raccomandazione."
                    ),
                )
                self.assertEqual(result.recommendation.evidence, ())
                self.assertEqual(
                    result.recommendation.warnings,
                    (
                        "La raccomandazione non dispone di evidenze storiche "
                        "utilizzabili.",
                    ),
                )

    def test_invalid_json_forms_receive_safe_structured_feedback(self) -> None:
        fence = chr(96) * 3
        invalid_documents = {
            "malformed": "{",
            "markdown": fence + "json\n{}\n" + fence,
            "surrounding_text": "Risposta: {}",
            "multiple_objects": "{}{}",
            "array": "[]",
            "duplicate_key": (
                '{"schema_version":"2.0.0",'
                '"schema_version":"2.0.0"}'
            ),
            "non_finite": '{"value": NaN}',
            "non_utf8": b"\xff",
        }
        for label, invalid_document in invalid_documents.items():
            with self.subTest(label=label):
                prompts = []
                retriever = _CountingRetriever()

                def callback(prompt):
                    attempt = len(prompts)
                    prompts.append(prompt)
                    if attempt == 0:
                        return invalid_document
                    return json.dumps(_valid_response(prompt))

                service = self._service(callback, max_attempts=2)
                service.context_retriever = retriever
                result = service.recommend(self.submission)

                self.assertEqual(result.attempts, 2)
                self.assertEqual(len(prompts), 2)
                self.assertEqual(retriever.calls, 1)
                feedback = prompts[1].payload["previous_validation_errors"]
                self.assertEqual(
                    feedback[0]["code"],
                    "LLM_OUTPUT_JSON_INVALID",
                )
                self.assertEqual(feedback[0]["path"], "$")
                self.assertEqual(
                    set(feedback[0]),
                    {"code", "path", "message"},
                )
                serialized_feedback = json.dumps(feedback)
                for forbidden in ("Traceback", "JSONDecodeError", "Expecting"):
                    self.assertNotIn(forbidden, serialized_feedback)
                for key in (
                    "live_request",
                    "retrieved_labeled_examples",
                    "configuration_catalog",
                ):
                    self.assertEqual(
                        prompts[0].payload[key],
                        prompts[1].payload[key],
                    )

    def test_closed_schema_rejects_unknown_missing_and_wrong_fields(self) -> None:
        def extra_root(response):
            response["invented"] = True

        def extra_plan(response):
            response["qiskit_plan"]["invented"] = True

        def missing_claims(response):
            response.pop("claims")

        def boolean_seed(response):
            response["qiskit_plan"]["seed_transpiler"] = True

        def negative_seed(response):
            response["qiskit_plan"]["seed_transpiler"] = -1

        def empty_claims(response):
            response["claims"] = []

        def llm_prose(response):
            response["explanation"] = "Testo libero non accettato."

        cases = (
            ("extra_root", extra_root, "$.invented"),
            ("extra_plan", extra_plan, "$.qiskit_plan.invented"),
            ("missing_claims", missing_claims, "$.claims"),
            (
                "boolean_seed",
                boolean_seed,
                "$.qiskit_plan.seed_transpiler",
            ),
            (
                "negative_seed",
                negative_seed,
                "$.qiskit_plan.seed_transpiler",
            ),
            ("empty_claims", empty_claims, "$.claims"),
            ("llm_prose", llm_prose, "$.explanation"),
        )
        for label, mutate, expected_path in cases:
            with self.subTest(label=label):
                prompts = []

                def callback(prompt):
                    attempt = len(prompts)
                    prompts.append(prompt)
                    response = _valid_response(prompt)
                    if attempt == 0:
                        mutate(response)
                    return json.dumps(response)

                result = self._service(callback, max_attempts=2).recommend(
                    self.submission
                )
                self.assertEqual(result.attempts, 2)
                feedback = prompts[1].payload["previous_validation_errors"]
                self.assertTrue(
                    all(
                        issue["code"] == "LLM_OUTPUT_SCHEMA_INVALID"
                        for issue in feedback
                    )
                )
                self.assertIn(
                    expected_path,
                    {issue["path"] for issue in feedback},
                )

    def test_retry_feedback_is_bounded(
        self,
    ) -> None:
        prompts = []

        def callback(prompt):
            attempt = len(prompts)
            prompts.append(prompt)
            response = _valid_response(prompt)
            if attempt == 0:
                response["explanation"] = "Prosa non prevista"
                response.update(
                    {f"unknown_{index}": index for index in range(20)}
                )
            return response

        result = self._service(callback, max_attempts=2).recommend(
            self.submission
        )

        self.assertEqual(result.attempts, 2)
        feedback = prompts[1].payload["previous_validation_errors"]
        self.assertEqual(len(feedback), 12)
        self.assertEqual(
            feedback[-1]["code"],
            "LLM_OUTPUT_ISSUES_TRUNCATED",
        )

    def test_semantic_errors_are_reported_with_stable_codes(self) -> None:
        cases = (
            (
                lambda response: response["claims"][0]["parameters"].update(
                    {"device_id": "ibm_falcon_127"}
                ),
                "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
            ),
            (
                lambda response: response.__setitem__(
                    "selected_device",
                    "unknown_device",
                ),
                "LLM_OUTPUT_UNKNOWN_DEVICE",
            ),
            (
                lambda response: response.__setitem__(
                    "request_id",
                    "another-request",
                ),
                "LLM_OUTPUT_REQUEST_MISMATCH",
            ),
            (
                lambda response: response.__setitem__(
                    "catalog_snapshot_id",
                    "hardware_catalog_" + "0" * 64,
                ),
                "LLM_OUTPUT_CATALOG_MISMATCH",
            ),
            (
                lambda response: response["qiskit_plan"].update(
                    {
                        "optimization_level": 2,
                        "layout_method": "dense",
                        "routing_method": "basic",
                    }
                ),
                "LLM_OUTPUT_CONFIGURATION_NOT_ALLOWED",
            ),
        )
        for mutate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                prompts = []

                def callback(prompt):
                    attempt = len(prompts)
                    prompts.append(prompt)
                    response = _valid_response(prompt)
                    if attempt == 0:
                        mutate(response)
                    return response

                result = self._service(callback, max_attempts=2).recommend(
                    self.submission
                )
                self.assertEqual(result.attempts, 2)
                codes = {
                    issue["code"]
                    for issue
                    in prompts[1].payload["previous_validation_errors"]
                }
                self.assertIn(expected_code, codes)

    def test_known_but_masked_device_is_not_eligible(self) -> None:
        prompts = []
        submission = replace(
            self.submission,
            allowed_devices=("ibm_falcon_27",),
        )

        def callback(prompt):
            attempt = len(prompts)
            prompts.append(prompt)
            selected = (
                "ibm_heron_133"
                if attempt == 0
                else "ibm_falcon_27"
            )
            return _valid_response(prompt, selected_device=selected)

        result = self._service(
            callback,
            max_attempts=2,
            devices=("ibm_falcon_27", "ibm_heron_133"),
        ).recommend(submission)

        self.assertEqual(result.attempts, 2)
        feedback = prompts[1].payload["previous_validation_errors"]
        self.assertIn(
            "LLM_OUTPUT_DEVICE_NOT_ELIGIBLE",
            {issue["code"] for issue in feedback},
        )

    def test_device_specific_configuration_allowlist_is_checked(self) -> None:
        service = self._service(lambda prompt: _valid_response(prompt))
        prepared = service.prepare_request(self.submission)
        profile = replace(
            prepared.hardware_catalog.devices[0],
            allowed_qiskit_configuration_ids=("o3_default_default",),
        )
        catalog = replace(
            prepared.hardware_catalog,
            devices=(profile,),
        )
        mask = replace(
            prepared.mask_result,
            available=(profile,),
        )
        prompt = type(
            "Prompt",
            (),
            {
                "payload": {
                    "live_request": {
                        "request_id": prepared.request.request_id,
                        "catalog_snapshot_id": (
                            prepared.request.catalog_snapshot_id
                        ),
                    }
                }
            },
        )()
        result = service.validator.validate(
            _valid_response(prompt),
            prepared.request,
            mask,
            catalog,
            evidence_registry=EvidenceRegistry(),
        )

        self.assertFalse(result.is_valid)
        self.assertIn(
            "LLM_OUTPUT_CONFIGURATION_NOT_SUPPORTED_BY_DEVICE",
            {issue.code for issue in result.issues},
        )

    def test_exhaustion_has_stable_error_and_exact_attempt_count(self) -> None:
        prompts = []

        def callback(prompt):
            prompts.append(prompt)
            return "{"

        with self.assertRaises(LlmValidationExhaustedError) as caught:
            self._service(callback, max_attempts=3).recommend(self.submission)

        error = caught.exception
        self.assertEqual(len(prompts), 3)
        self.assertEqual(error.attempts, 3)
        self.assertEqual(error.code, "LLM_OUTPUT_VALIDATION_EXHAUSTED")
        self.assertFalse(error.retryable)
        payload = error.to_dict()
        self.assertEqual(payload["attempts"], 3)
        self.assertEqual(
            payload["issues"][0]["code"],
            "LLM_OUTPUT_JSON_INVALID",
        )
        self.assertNotIn("Traceback", json.dumps(payload))

        with self.assertRaises(ValueError):
            self._service(lambda prompt: "{}", max_attempts=0)

    def test_infrastructure_and_adapter_errors_are_not_retried(self) -> None:
        failures = (
            ConnectionError("servizio non disponibile"),
            ["not", "a", "json", "object"],
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                prompts = []

                def callback(prompt):
                    prompts.append(prompt)
                    if isinstance(failure, BaseException):
                        raise failure
                    return failure

                expected = (
                    ConnectionError
                    if isinstance(failure, BaseException)
                    else TypeError
                )
                with self.assertRaises(expected):
                    self._service(callback).recommend(self.submission)
                self.assertEqual(len(prompts), 1)

        class BrokenValidator:
            def validate(self, *args, **kwargs):
                del args, kwargs
                raise AssertionError("errore interno")

        prompts = []

        def valid_callback(prompt):
            prompts.append(prompt)
            return _valid_response(prompt)

        service = self._service(valid_callback)
        service.validator = BrokenValidator()
        with self.assertRaises(AssertionError):
            service.recommend(self.submission)
        self.assertEqual(len(prompts), 1)

    def test_catalog_context_error_is_not_retried(self) -> None:
        prompts = []

        def callback(prompt):
            prompts.append(prompt)
            return _valid_response(prompt)

        service = self._service(callback)
        base_filter = service.compatibility_filter

        class MismatchedFilter:
            def filter(self, request, hardware):
                result = base_filter.filter(request, hardware)
                return replace(
                    result,
                    catalog_snapshot_id="hardware_catalog_" + "0" * 64,
                )

        service.compatibility_filter = MismatchedFilter()
        with self.assertRaises(RuntimeError):
            service.recommend(self.submission)
        self.assertEqual(len(prompts), 1)

    def test_only_valid_output_reaches_confirmation_and_compilation(self) -> None:
        invalid_compiler = _FakeCompiler()
        invalid_service = self._service(lambda prompt: "{", max_attempts=1)
        invalid_service.compiler = invalid_compiler
        invalid_controller = PrototypeController(invalid_service)

        with self.assertRaises(LlmValidationExhaustedError):
            invalid_controller.request_recommendation(self.submission)
        with self.assertRaises(KeyError):
            invalid_controller.compile_recommendation(
                self.submission.request_id,
                user_confirmed=True,
            )
        self.assertEqual(invalid_compiler.calls, 0)

        valid_compiler = _FakeCompiler()
        valid_service = self._service(
            lambda prompt: json.dumps(_valid_response(prompt)),
            max_attempts=1,
        )
        valid_service.compiler = valid_compiler
        valid_controller = PrototypeController(valid_service)
        recommendation = valid_controller.request_recommendation(
            self.submission
        )
        self.assertEqual(valid_compiler.calls, 0)

        with self.assertRaises(ConfirmationRequiredError):
            valid_controller.compile_recommendation(
                recommendation["request_id"],
                user_confirmed=False,
            )
        self.assertEqual(valid_compiler.calls, 0)

        artifact = valid_controller.compile_recommendation(
            recommendation["request_id"],
            user_confirmed=True,
        )
        self.assertEqual(valid_compiler.calls, 1)
        self.assertTrue(artifact["validation"]["is_executable_on_target"])


if __name__ == "__main__":
    unittest.main()

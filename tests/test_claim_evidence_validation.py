from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from qiskit import QuantumCircuit
from qiskit.qasm2 import dump as qasm_dump

from prototype.quantum_assistant.adapters.context import (
    EvidenceRegistryDataError,
    _compact_rag_example,
)
from prototype.quantum_assistant.adapters.llm import CallableLlmGateway
from prototype.quantum_assistant.controller import PrototypeController
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.models import (
    ApprovedCompilation,
    CompilationArtifact,
    RetrievedExample,
    UiSubmission,
)
from prototype.quantum_assistant.services import (
    ConfirmationRequiredError,
    LlmValidationExhaustedError,
    UnvalidatedRecommendationError,
)


DEVICE_ID = "ibm_falcon_27"
OTHER_DEVICE_ID = "ibm_heron_133"
CONFIGURATION_ID = "o2_default_default"
OTHER_CONFIGURATION_ID = "o3_default_default"

RECORD_ID = "rag_" + "a" * 64
DEVICE_SOURCE_CLAIM_ID = "claim_" + "b" * 64
CONFIGURATION_SOURCE_CLAIM_ID = "claim_" + "c" * 64
EVIDENCE_ID = "evidence_" + "d" * 64
OTHER_EVIDENCE_ID = "evidence_" + "e" * 64
SUMMARY_ID = "summary_" + "6" * 64
OTHER_SUMMARY_ID = "summary_" + "7" * 64

SECOND_RECORD_ID = "rag_" + "1" * 64
SECOND_DEVICE_SOURCE_CLAIM_ID = "claim_" + "2" * 64
SECOND_CONFIGURATION_SOURCE_CLAIM_ID = "claim_" + "3" * 64
SECOND_EVIDENCE_ID = "evidence_" + "4" * 64
SECOND_OTHER_EVIDENCE_ID = "evidence_" + "5" * 64

CAVEAT_ID = "expected_fidelity_is_estimate"
CAVEAT_TEXT = (
    "Expected fidelity e una stima offline, non una misura su hardware reale."
)
OTHER_CAVEAT_ID = "closed_candidate_set"
OTHER_CAVEAT_TEXT = "Il risultato vale soltanto nel gruppo storico valutato."


def _qasm2() -> str:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    stream = StringIO()
    qasm_dump(circuit, stream)
    return stream.getvalue()


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return value


def _evidence(
    evidence_id: str,
    device_id: str,
    configuration_id: str,
    summary_character: str,
    value: float,
) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "evidence_type": "offline_seed_aggregate",
        "summary_id": "summary_" + summary_character * 64,
        "device_id": device_id,
        "config_id": configuration_id,
        "metric": "median_expected_fidelity_across_seeds",
        "aggregation": {
            "method": "median",
            "value": value,
            "sample_count": 3,
        },
    }


def _rag_example(
    *,
    record_id: str = RECORD_ID,
    distance: float = 0.05,
    device_id: str = DEVICE_ID,
    configuration_id: str = CONFIGURATION_ID,
    optimization_level: int = 2,
    device_source_claim_id: str = DEVICE_SOURCE_CLAIM_ID,
    configuration_source_claim_id: str = CONFIGURATION_SOURCE_CLAIM_ID,
    evidence_id: str = EVIDENCE_ID,
    other_evidence_id: str = OTHER_EVIDENCE_ID,
    device_claim_evidence_ids: tuple[str, ...] | None = None,
) -> RetrievedExample:
    if device_claim_evidence_ids is None:
        device_claim_evidence_ids = (evidence_id,)
    other_configuration = (
        OTHER_CONFIGURATION_ID
        if configuration_id == CONFIGURATION_ID
        else CONFIGURATION_ID
    )
    return RetrievedExample(
        record_id=record_id,
        distance=distance,
        prompt_input={
            "rag_id": record_id,
            "label": {
                "selected_device": {
                    "device_id": device_id,
                    "best_summary_id": SUMMARY_ID,
                    "best_config_id": configuration_id,
                    "median_score": 0.91,
                },
                "top_configurations": [
                    {
                        "rank": 1,
                        "device_id": device_id,
                        "config_id": configuration_id,
                        "claim_id": configuration_source_claim_id,
                        "evidence_id": evidence_id,
                        "optimization_level": optimization_level,
                        "layout_method": None,
                        "routing_method": None,
                        "summary_id": SUMMARY_ID,
                        "median_score": 0.91,
                    }
                ],
            },
            "claims": [
                {
                    "claim_id": device_source_claim_id,
                    "claim_type": "selected_device",
                    "evidence_ids": list(device_claim_evidence_ids),
                    "caveat_ids": [CAVEAT_ID],
                },
                {
                    "claim_id": configuration_source_claim_id,
                    "claim_type": "ranked_configuration",
                    "evidence_ids": [evidence_id],
                    "caveat_ids": [CAVEAT_ID],
                },
            ],
            "evidence": [
                _evidence(
                    evidence_id,
                    device_id,
                    configuration_id,
                    "6",
                    0.91,
                ),
                _evidence(
                    other_evidence_id,
                    device_id,
                    other_configuration,
                    "7",
                    0.89,
                ),
            ],
            "scientific_caveats": [
                {"caveat_id": CAVEAT_ID, "text": CAVEAT_TEXT},
                {
                    "caveat_id": OTHER_CAVEAT_ID,
                    "text": OTHER_CAVEAT_TEXT,
                },
            ],
        },
    )


def _second_example(
    *,
    device_id: str = DEVICE_ID,
    configuration_id: str = CONFIGURATION_ID,
    optimization_level: int = 2,
) -> RetrievedExample:
    return _rag_example(
        record_id=SECOND_RECORD_ID,
        distance=0.1,
        device_id=device_id,
        configuration_id=configuration_id,
        optimization_level=optimization_level,
        device_source_claim_id=SECOND_DEVICE_SOURCE_CLAIM_ID,
        configuration_source_claim_id=SECOND_CONFIGURATION_SOURCE_CLAIM_ID,
        evidence_id=SECOND_EVIDENCE_ID,
        other_evidence_id=SECOND_OTHER_EVIDENCE_ID,
    )


def _legacy_example() -> RetrievedExample:
    return RetrievedExample(
        record_id="legacy-record",
        distance=0.01,
        prompt_input={
            "objective": {"name": "expected_fidelity"},
            "circuit": {
                "name": "legacy",
                "features": {"by_name": {}},
            },
            "compatible_backends": [{"id": DEVICE_ID}],
            "user_constraints": {},
        },
    )


def _historical_response(
    request_id: str,
    catalog_snapshot_id: str,
) -> dict[str, object]:
    return {
        "schema_version": "2.0.0",
        "request_id": request_id,
        "catalog_snapshot_id": catalog_snapshot_id,
        "selected_device": DEVICE_ID,
        "figure_of_merit": "expected_fidelity",
        "compiler": "qiskit",
        "qiskit_plan": {
            "optimization_level": 2,
            "seed_transpiler": 7,
            "layout_method": None,
            "routing_method": None,
        },
        "evidence_refs": [
            {
                "reference_id": "ref-device",
                "record_id": RECORD_ID,
                "source_type": "historical_result",
                "source_id": EVIDENCE_ID,
                "source_claim_id": DEVICE_SOURCE_CLAIM_ID,
            },
            {
                "reference_id": "ref-configuration",
                "record_id": RECORD_ID,
                "source_type": "historical_result",
                "source_id": EVIDENCE_ID,
                "source_claim_id": CONFIGURATION_SOURCE_CLAIM_ID,
            },
        ],
        "claims": [
            {
                "claim_id": "claim-device-support",
                "claim_type": "historical_device_support",
                "parameters": {"device_id": DEVICE_ID},
                "evidence_ref_ids": ["ref-device"],
            },
            {
                "claim_id": "claim-configuration-support",
                "claim_type": "historical_configuration_support",
                "parameters": {
                    "device_id": DEVICE_ID,
                    "configuration_id": CONFIGURATION_ID,
                },
                "evidence_ref_ids": ["ref-configuration"],
            },
            {
                "claim_id": "claim-live-compatibility",
                "claim_type": "live_compatibility",
                "parameters": {"device_id": DEVICE_ID},
                "evidence_ref_ids": [],
            },
        ],
    }


def _no_history_response(
    request_id: str,
    catalog_snapshot_id: str,
) -> dict[str, object]:
    response = _historical_response(request_id, catalog_snapshot_id)
    response["evidence_refs"] = []
    response["claims"] = [
        {
            "claim_id": "claim-live-compatibility",
            "claim_type": "live_compatibility",
            "parameters": {"device_id": DEVICE_ID},
            "evidence_ref_ids": [],
        },
        {
            "claim_id": "claim-no-history",
            "claim_type": "historical_evidence_unavailable",
            "parameters": {},
            "evidence_ref_ids": [],
        },
    ]
    return response


def _response_from_prompt(prompt, *, with_history: bool = True):
    live_request = prompt.payload["live_request"]
    factory = _historical_response if with_history else _no_history_response
    return factory(
        live_request["request_id"],
        live_request["catalog_snapshot_id"],
    )


def _append_caveat_claim(
    response: dict[str, object],
    source_id: str,
) -> None:
    response["evidence_refs"].append(
        {
            "reference_id": "ref-caveat",
            "record_id": RECORD_ID,
            "source_type": "scientific_caveat",
            "source_id": source_id,
        }
    )
    response["claims"].append(
        {
            "claim_id": "claim-scientific-caveat",
            "claim_type": "scientific_caveat",
            "parameters": {"caveat_id": source_id},
            "evidence_ref_ids": ["ref-caveat"],
        }
    )


def _add_second_record_support(response: dict[str, object]) -> None:
    response["evidence_refs"].extend(
        [
            {
                "reference_id": "ref-device-second",
                "record_id": SECOND_RECORD_ID,
                "source_type": "historical_result",
                "source_id": SECOND_EVIDENCE_ID,
                "source_claim_id": SECOND_DEVICE_SOURCE_CLAIM_ID,
            },
            {
                "reference_id": "ref-configuration-second",
                "record_id": SECOND_RECORD_ID,
                "source_type": "historical_result",
                "source_id": SECOND_EVIDENCE_ID,
                "source_claim_id": SECOND_CONFIGURATION_SOURCE_CLAIM_ID,
            },
        ]
    )
    response["claims"][0]["evidence_ref_ids"].append("ref-device-second")
    response["claims"][1]["evidence_ref_ids"].append(
        "ref-configuration-second"
    )


class _StaticRetriever:
    def __init__(self, examples) -> None:
        self.examples = tuple(examples)
        self.calls = 0

    def retrieve(self, request, compatibility, *, limit):
        del request, compatibility
        self.calls += 1
        return self.examples[:limit]


class _CountingRegistryBuilder:
    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.calls = 0
        self.registries = []

    def build(self, examples):
        self.calls += 1
        registry = self.delegate.build(examples)
        self.registries.append(registry)
        return registry


class _RegistrySpyValidator:
    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.registries = []

    def validate(self, *args, evidence_registry, **kwargs):
        self.registries.append(evidence_registry)
        return self.delegate.validate(
            *args,
            evidence_registry=evidence_registry,
            **kwargs,
        )


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


class ClaimEvidenceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.submission = UiSubmission(
            request_id="request-claim-evidence",
            user_text="Scegli una configurazione valida.",
            qasm2=_qasm2(),
        )
        self.service = self._service(lambda prompt: "{}")
        self.prepared = self.service.prepare_request(self.submission)
        self.example = _rag_example()
        self.registry = self.service.evidence_registry_builder.build(
            (self.example,)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _service(self, callback, *, max_attempts: int = 3):
        return build_default_service(
            device_names=(DEVICE_ID,),
            dataset_path=self.root / "missing.jsonl",
            llm_gateway=CallableLlmGateway(callback),
            max_llm_attempts=max_attempts,
            retrieval_limit=5,
        )

    def _response(self) -> dict[str, object]:
        return _historical_response(
            self.prepared.request.request_id,
            self.prepared.request.catalog_snapshot_id,
        )

    def _validate(self, response, *, registry=None):
        return self.service.validator.validate(
            response,
            self.prepared.request,
            self.prepared.mask_result,
            self.prepared.hardware_catalog,
            evidence_registry=self.registry if registry is None else registry,
        )

    @staticmethod
    def _codes(result) -> set[str]:
        return {issue.code for issue in result.issues}

    def _assert_dataset_error_before_llm(
        self,
        example: RetrievedExample,
    ) -> EvidenceRegistryDataError:
        retriever = _StaticRetriever((example,))
        llm_calls = []

        def callback(prompt):
            llm_calls.append(prompt)
            return _response_from_prompt(prompt)

        service = self._service(callback)
        service.context_retriever = retriever
        with self.assertRaises(EvidenceRegistryDataError) as caught:
            service.recommend(self.submission)
        self.assertEqual(retriever.calls, 1)
        self.assertEqual(llm_calls, [])
        return caught.exception

    def test_registry_keeps_rag_ignores_legacy_and_preserves_rank(self) -> None:
        registry = self.service.evidence_registry_builder.build(
            (_legacy_example(), self.example)
        )
        self.assertEqual(len(registry.records), 1)
        record = registry.records[0]
        self.assertEqual(record.record_id, RECORD_ID)
        self.assertEqual(record.rank, 2)
        self.assertEqual(record.distance, 0.05)
        self.assertEqual(record.selected_device_id, DEVICE_ID)
        self.assertEqual(record.source_claims[0].evidence_ids, (EVIDENCE_ID,))
        self.assertEqual(
            record.top_configurations[0].configuration_id,
            CONFIGURATION_ID,
        )
        self.assertEqual(record.evidence[0].value, 0.91)
        self.assertEqual(record.caveats[0].text, CAVEAT_TEXT)
        self.assertEqual(
            self.service.evidence_registry_builder.build(
                (_legacy_example(),)
            ).records,
            (),
        )

    def test_registry_accepts_first_real_global_rag_record(self) -> None:
        dataset_path = (
            Path(__file__).resolve().parents[1]
            / "datasets"
            / "expected_fidelity"
            / "pilot"
            / "global"
            / "rag_examples.jsonl"
        )
        with dataset_path.open(encoding="utf-8") as handle:
            raw_record = json.loads(handle.readline())
        example = RetrievedExample(
            record_id=raw_record["rag_id"],
            distance=0.0,
            prompt_input=_compact_rag_example(raw_record),
        )
        registry = self.service.evidence_registry_builder.build((example,))
        self.assertEqual(len(registry.records), 1)
        self.assertEqual(registry.records[0].record_id, raw_record["rag_id"])
        self.assertEqual(
            registry.records[0].selected_device_id,
            raw_record["selected_device"]["device_id"],
        )

    def test_top_configuration_must_match_its_evidence_before_llm(
        self,
    ) -> None:
        mutations = (
            ("summary_id", OTHER_SUMMARY_ID),
            ("median_score", 0.5),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                payload = _thaw(self.example.prompt_input)
                payload["label"]["top_configurations"][0][field] = value
                malformed = RetrievedExample(
                    record_id=RECORD_ID,
                    distance=0.05,
                    prompt_input=payload,
                )
                self._assert_dataset_error_before_llm(malformed)

    def test_selected_device_label_must_match_rank_one_before_llm(
        self,
    ) -> None:
        payload = _thaw(self.example.prompt_input)
        payload["label"]["selected_device"]["best_config_id"] = (
            OTHER_CONFIGURATION_ID
        )
        malformed = RetrievedExample(
            record_id=RECORD_ID,
            distance=0.05,
            prompt_input=payload,
        )
        self._assert_dataset_error_before_llm(malformed)

    def test_declared_rag_missing_all_evidence_fields_is_not_legacy(
        self,
    ) -> None:
        payload = _thaw(self.example.prompt_input)
        for field in (
            "label",
            "claims",
            "evidence",
            "scientific_caveats",
        ):
            payload.pop(field)
        self.assertIn("rag_id", payload)
        malformed = RetrievedExample(
            record_id=RECORD_ID,
            distance=0.05,
            prompt_input=payload,
        )
        self._assert_dataset_error_before_llm(malformed)

    def test_invented_or_out_of_top_k_record_is_rejected(self) -> None:
        outside_top_k = _second_example()
        self.assertNotEqual(outside_top_k.record_id, RECORD_ID)
        for record_id in ("invented-record", outside_top_k.record_id):
            with self.subTest(record_id=record_id):
                response = self._response()
                response["evidence_refs"][0]["record_id"] = record_id
                result = self._validate(response)
                self.assertFalse(result.is_valid)
                self.assertIn(
                    "LLM_OUTPUT_EVIDENCE_RECORD_UNKNOWN",
                    self._codes(result),
                )

    def test_unknown_or_incoherent_evidence_and_claim_are_rejected(
        self,
    ) -> None:
        cases = (
            (
                "source_id",
                "unknown-evidence",
                "LLM_OUTPUT_EVIDENCE_UNKNOWN",
            ),
            (
                "source_claim_id",
                "unknown-claim",
                "LLM_OUTPUT_SOURCE_CLAIM_UNKNOWN",
            ),
            (
                "source_id",
                OTHER_EVIDENCE_ID,
                "LLM_OUTPUT_EVIDENCE_LINK_MISMATCH",
            ),
        )
        for field, value, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                response = self._response()
                response["evidence_refs"][0][field] = value
                result = self._validate(response)
                self.assertFalse(result.is_valid)
                self.assertIn(expected_code, self._codes(result))

    def test_unknown_or_unlinked_caveat_is_rejected(self) -> None:
        cases = (
            ("unknown-caveat", "LLM_OUTPUT_CAVEAT_UNKNOWN"),
            (OTHER_CAVEAT_ID, "LLM_OUTPUT_CAVEAT_EVIDENCE_MISMATCH"),
        )
        for caveat_id, expected_code in cases:
            with self.subTest(caveat_id=caveat_id):
                response = self._response()
                _append_caveat_claim(response, caveat_id)
                result = self._validate(response)
                self.assertFalse(result.is_valid)
                self.assertIn(expected_code, self._codes(result))

    def test_device_and_configuration_parameters_must_match_output(
        self,
    ) -> None:
        cases = (
            (
                0,
                {"device_id": OTHER_DEVICE_ID},
                "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
            ),
            (
                1,
                {
                    "device_id": DEVICE_ID,
                    "configuration_id": OTHER_CONFIGURATION_ID,
                },
                "LLM_OUTPUT_CONFIGURATION_CLAIM_MISMATCH",
            ),
        )
        for claim_index, parameters, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                response = self._response()
                response["claims"][claim_index]["parameters"] = parameters
                result = self._validate(response)
                self.assertFalse(result.is_valid)
                self.assertIn(expected_code, self._codes(result))

    def test_historical_device_and_configuration_sources_must_match(
        self,
    ) -> None:
        other_device = _second_example(device_id=OTHER_DEVICE_ID)
        registry = self.service.evidence_registry_builder.build(
            (self.example, other_device)
        )
        response = self._response()
        response["evidence_refs"][0].update(
            {
                "record_id": SECOND_RECORD_ID,
                "source_id": SECOND_EVIDENCE_ID,
                "source_claim_id": SECOND_DEVICE_SOURCE_CLAIM_ID,
            }
        )
        result = self._validate(response, registry=registry)
        self.assertIn(
            "LLM_OUTPUT_DEVICE_EVIDENCE_MISMATCH",
            self._codes(result),
        )

        other_configuration = _second_example(
            configuration_id=OTHER_CONFIGURATION_ID,
            optimization_level=3,
        )
        registry = self.service.evidence_registry_builder.build(
            (self.example, other_configuration)
        )
        response = self._response()
        response["evidence_refs"][1].update(
            {
                "record_id": SECOND_RECORD_ID,
                "source_id": SECOND_EVIDENCE_ID,
                "source_claim_id": SECOND_CONFIGURATION_SOURCE_CLAIM_ID,
            }
        )
        result = self._validate(response, registry=registry)
        self.assertIn(
            "LLM_OUTPUT_CONFIGURATION_EVIDENCE_MISMATCH",
            self._codes(result),
        )

    def test_historical_claim_requires_all_and_only_source_evidence(
        self,
    ) -> None:
        two_evidence_source = _rag_example(
            device_claim_evidence_ids=(EVIDENCE_ID, OTHER_EVIDENCE_ID),
        )
        registry = self.service.evidence_registry_builder.build(
            (two_evidence_source,)
        )
        incomplete = self._validate(self._response(), registry=registry)
        self.assertIn(
            "LLM_OUTPUT_SOURCE_EVIDENCE_SET_MISMATCH",
            self._codes(incomplete),
        )
        self.assertEqual(
            {
                issue.path
                for issue in incomplete.issues
                if issue.code == "LLM_OUTPUT_SOURCE_EVIDENCE_SET_MISMATCH"
            },
            {"$.claims[0].evidence_ref_ids"},
        )

        extraneous = self._response()
        extraneous["evidence_refs"].append(
            {
                "reference_id": "ref-device-extra",
                "record_id": RECORD_ID,
                "source_type": "historical_result",
                "source_id": OTHER_EVIDENCE_ID,
                "source_claim_id": DEVICE_SOURCE_CLAIM_ID,
            }
        )
        extraneous["claims"][0]["evidence_ref_ids"].append(
            "ref-device-extra"
        )
        result = self._validate(extraneous)
        self.assertIn(
            "LLM_OUTPUT_SOURCE_EVIDENCE_SET_MISMATCH",
            self._codes(result),
        )

    def test_duplicate_unused_and_reused_references_are_rejected(self) -> None:
        def duplicate_reference_id(response):
            response["evidence_refs"][1]["reference_id"] = "ref-device"

        def duplicate_source(response):
            extra = deepcopy(response["evidence_refs"][0])
            extra["reference_id"] = "ref-device-copy"
            response["evidence_refs"].append(extra)
            response["claims"][0]["evidence_ref_ids"].append(
                "ref-device-copy"
            )

        def duplicate_claim_id(response):
            response["claims"][2]["claim_id"] = response["claims"][0][
                "claim_id"
            ]

        def unused_reference(response):
            response["evidence_refs"].append(
                {
                    "reference_id": "ref-unused",
                    "record_id": RECORD_ID,
                    "source_type": "scientific_caveat",
                    "source_id": CAVEAT_ID,
                }
            )

        def reused_reference(response):
            response["claims"][1]["evidence_ref_ids"].append("ref-device")

        cases = (
            (
                duplicate_reference_id,
                "LLM_OUTPUT_EVIDENCE_REFERENCE_ID_DUPLICATE",
            ),
            (duplicate_source, "LLM_OUTPUT_EVIDENCE_SOURCE_DUPLICATE"),
            (duplicate_claim_id, "LLM_OUTPUT_CLAIM_ID_DUPLICATE"),
            (unused_reference, "LLM_OUTPUT_EVIDENCE_REFERENCE_UNUSED"),
            (reused_reference, "LLM_OUTPUT_EVIDENCE_REFERENCE_REUSED"),
        )
        for mutate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                response = self._response()
                mutate(response)
                result = self._validate(response)
                self.assertFalse(result.is_valid)
                self.assertIn(expected_code, self._codes(result))

    def test_exactly_one_claim_for_each_required_role(self) -> None:
        for claim_index in (0, 1):
            with self.subTest(missing_claim=claim_index):
                response = self._response()
                response["claims"].pop(claim_index)
                result = self._validate(response)
                self.assertIn(
                    "LLM_OUTPUT_HISTORICAL_SUPPORT_INCOMPLETE",
                    self._codes(result),
                )

        for claim_index in (0, 1):
            with self.subTest(duplicated_claim=claim_index):
                response = self._response()
                duplicate = deepcopy(response["claims"][claim_index])
                duplicate["claim_id"] += "-duplicate"
                duplicate["evidence_ref_ids"] = []
                response["claims"].append(duplicate)
                result = self._validate(response)
                self.assertIn(
                    "LLM_OUTPUT_HISTORICAL_SUPPORT_INCOMPLETE",
                    self._codes(result),
                )

    def test_no_evidence_contract_is_explicit_and_non_fabricating(self) -> None:
        empty_registry = self.service.evidence_registry_builder.build(
            (_legacy_example(),)
        )
        response = _no_history_response(
            self.prepared.request.request_id,
            self.prepared.request.catalog_snapshot_id,
        )
        result = self._validate(response, registry=empty_registry)
        self.assertTrue(result.is_valid)
        recommendation = result.recommendation
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.evidence, ())
        self.assertEqual(
            recommendation.warnings,
            (
                "La raccomandazione non dispone di evidenze storiche "
                "utilizzabili.",
            ),
        )
        self.assertIn(
            "non sono disponibili risultati storici utilizzabili",
            recommendation.explanation,
        )

        contradicted = self._validate(response)
        self.assertIn(
            "LLM_OUTPUT_EVIDENCE_UNAVAILABLE_CONTRADICTED",
            self._codes(contradicted),
        )
        fabricated = self._validate(
            self._response(),
            registry=empty_registry,
        )
        self.assertIn(
            "LLM_OUTPUT_EVIDENCE_NOT_AVAILABLE",
            self._codes(fabricated),
        )

    def test_rendering_and_caveats_are_deterministic(self) -> None:
        response = self._response()
        _append_caveat_claim(response, CAVEAT_ID)

        first = self._validate(response)
        second = self._validate(deepcopy(response))
        self.assertTrue(first.is_valid)
        self.assertTrue(second.is_valid)
        recommendation = first.recommendation
        self.assertEqual(recommendation, second.recommendation)
        self.assertEqual(
            recommendation.explanation,
            (
                f"I risultati dei circuiti storici {RECORD_ID} sostengono "
                f"la scelta del dispositivo {DEVICE_ID}. "
                f"I risultati dei circuiti storici {RECORD_ID} sostengono "
                f"la configurazione {CONFIGURATION_ID} per il dispositivo "
                f"{DEVICE_ID}. Il dispositivo {DEVICE_ID} rispetta i vincoli "
                "verificati per la richiesta corrente. La raccomandazione "
                "tiene conto delle avvertenze scientifiche associate alle "
                "evidenze storiche."
            ),
        )
        self.assertEqual(
            recommendation.evidence,
            (
                f"Circuito storico {RECORD_ID}: dispositivo={DEVICE_ID}, "
                f"configurazione={CONFIGURATION_ID}, "
                "mediana della fedeltà attesa=0.91, campioni=3 "
                f"(evidenza {EVIDENCE_ID}).",
                f"Circuito storico {RECORD_ID}: avvertenza {CAVEAT_ID}.",
            ),
        )
        self.assertEqual(
            recommendation.warnings,
            (
                CAVEAT_TEXT,
                "Le evidenze riguardano compilazioni storiche di circuiti "
                "simili e non misurano il risultato del circuito corrente.",
            ),
        )

    def test_rendering_is_invariant_to_all_llm_array_orders(self) -> None:
        registry = self.service.evidence_registry_builder.build(
            (self.example, _second_example())
        )
        response = self._response()
        _add_second_record_support(response)
        _append_caveat_claim(response, CAVEAT_ID)
        baseline = self._validate(response, registry=registry)
        self.assertTrue(baseline.is_valid)

        permuted = deepcopy(response)
        permuted["claims"].reverse()
        permuted["evidence_refs"].reverse()
        for claim in permuted["claims"]:
            claim["evidence_ref_ids"].reverse()
        reordered = self._validate(permuted, registry=registry)
        self.assertTrue(reordered.is_valid)
        self.assertEqual(
            reordered.recommendation.explanation,
            baseline.recommendation.explanation,
        )
        self.assertEqual(
            reordered.recommendation.evidence,
            baseline.recommendation.evidence,
        )
        self.assertEqual(
            reordered.recommendation.warnings,
            baseline.recommendation.warnings,
        )

    def test_retry_reuses_one_registry_and_retrieves_once(self) -> None:
        prompts = []
        retriever = _StaticRetriever((self.example,))

        def callback(prompt):
            prompts.append(prompt)
            response = _response_from_prompt(prompt)
            if len(prompts) == 1:
                response["evidence_refs"][0]["record_id"] = "invented"
            return response

        service = self._service(callback, max_attempts=2)
        service.context_retriever = retriever
        registry_builder = _CountingRegistryBuilder(
            service.evidence_registry_builder
        )
        service.evidence_registry_builder = registry_builder
        validator = _RegistrySpyValidator(service.validator)
        service.validator = validator

        result = service.recommend(self.submission)

        self.assertEqual(result.attempts, 2)
        self.assertEqual(retriever.calls, 1)
        self.assertEqual(registry_builder.calls, 1)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(len(validator.registries), 2)
        self.assertIs(validator.registries[0], registry_builder.registries[0])
        self.assertIs(validator.registries[1], registry_builder.registries[0])
        self.assertEqual(
            prompts[0].payload["allowed_evidence_registry"],
            prompts[1].payload["allowed_evidence_registry"],
        )
        feedback_codes = {
            issue["code"]
            for issue in prompts[1].payload["previous_validation_errors"]
        }
        self.assertIn("LLM_OUTPUT_EVIDENCE_RECORD_UNKNOWN", feedback_codes)

    def test_claim_evidence_errors_exhaust_exact_attempt_limit(self) -> None:
        calls = []
        retriever = _StaticRetriever((self.example,))

        def callback(prompt):
            calls.append(prompt)
            response = _response_from_prompt(prompt)
            response["evidence_refs"][0]["source_id"] = "unknown"
            return response

        service = self._service(callback, max_attempts=2)
        service.context_retriever = retriever
        with self.assertRaises(LlmValidationExhaustedError) as caught:
            service.recommend(self.submission)

        self.assertEqual(len(calls), 2)
        self.assertEqual(retriever.calls, 1)
        self.assertEqual(caught.exception.attempts, 2)
        self.assertIn(
            "LLM_OUTPUT_EVIDENCE_UNKNOWN",
            {issue.code for issue in caught.exception.issues},
        )

    def test_malformed_dataset_is_not_retried_or_sent_to_llm(self) -> None:
        malformed_payload = dict(self.example.prompt_input)
        malformed_payload.pop("evidence")
        malformed = RetrievedExample(
            record_id=RECORD_ID,
            distance=0.05,
            prompt_input=malformed_payload,
        )
        retriever = _StaticRetriever((malformed,))
        llm_calls = []

        def callback(prompt):
            llm_calls.append(prompt)
            return _response_from_prompt(prompt)

        service = self._service(callback)
        service.context_retriever = retriever
        with self.assertRaises(EvidenceRegistryDataError):
            service.recommend(self.submission)

        self.assertEqual(retriever.calls, 1)
        self.assertEqual(llm_calls, [])

    def test_manually_constructed_result_cannot_reach_compiler(self) -> None:
        compiler = _FakeCompiler()
        service = self._service(
            lambda prompt: _response_from_prompt(prompt),
            max_attempts=1,
        )
        service.context_retriever = _StaticRetriever((self.example,))
        service.compiler = compiler
        issued_result = service.recommend(self.submission)
        manual_result = replace(issued_result)
        self.assertIsNot(manual_result, issued_result)

        with self.assertRaises(UnvalidatedRecommendationError) as caught:
            service.compile_approved(
                ApprovedCompilation(
                    recommendation_result=manual_result,
                    user_confirmed=True,
                )
            )

        self.assertEqual(caught.exception.code, "RECOMMENDATION_NOT_ISSUED")
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(compiler.calls, 0)

    def test_confirmation_and_compilation_wait_for_valid_output(self) -> None:
        invalid_compiler = _FakeCompiler()
        invalid_retriever = _StaticRetriever((self.example,))

        def always_invalid(prompt):
            response = _response_from_prompt(prompt)
            response["evidence_refs"][0]["record_id"] = "invented"
            return response

        invalid_service = self._service(always_invalid, max_attempts=1)
        invalid_service.context_retriever = invalid_retriever
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

        compiler = _FakeCompiler()
        retriever = _StaticRetriever((self.example,))
        llm_calls = 0

        def invalid_then_valid(prompt):
            nonlocal llm_calls
            llm_calls += 1
            self.assertEqual(compiler.calls, 0)
            response = _response_from_prompt(prompt)
            if llm_calls == 1:
                response["evidence_refs"][0]["record_id"] = "invented"
            return response

        service = self._service(invalid_then_valid, max_attempts=2)
        service.context_retriever = retriever
        service.compiler = compiler
        controller = PrototypeController(service)
        recommendation = controller.request_recommendation(self.submission)
        self.assertEqual(llm_calls, 2)
        self.assertEqual(compiler.calls, 0)

        with self.assertRaises(ConfirmationRequiredError):
            controller.compile_recommendation(
                recommendation["request_id"],
                user_confirmed=False,
            )
        self.assertEqual(compiler.calls, 0)

        artifact = controller.compile_recommendation(
            recommendation["request_id"],
            user_confirmed=True,
        )
        self.assertEqual(compiler.calls, 1)
        self.assertTrue(artifact["validation"]["is_executable_on_target"])


if __name__ == "__main__":
    unittest.main()

"""Nuovo contratto: contenuti minimi, citazioni locali e controlli applicativi."""
import copy
from dataclasses import replace
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import test_claim_evidence_validation as fixtures
from prototype.prompting.minimal import audit, citation_context, model_input, response_schema
from prototype.prompting.rendering import messages
from prototype.quantum_assistant.adapters.context import StructuredPromptBuilder
from prototype.quantum_assistant.models import ApprovedCompilation, CompilationArtifact, PromptEnvelope
from prototype.quantum_assistant.services import UnvalidatedRecommendationError
from llm_selection.configuration import payload
from llm_selection import gateway, run


class MinimalPromptTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.ClaimEvidenceValidationTests()
        self.f.setUp()
        self.f.service.prompt_builder = StructuredPromptBuilder()
        examples = []
        for i in range(5):
            e = fixtures._rag_example(record_id="rag_" + str(i + 1) * 64)
            data = fixtures._thaw(e.prompt_input)
            data["input"] = {
                "circuit": {"source_sha256": str(i) * 64, "num_qubits": 2,
                            "features": {"values": {"gate_count_h": 0.0, "depth": 1.2345678901234567}}},
                "compatible_devices": [{"device_id": fixtures.DEVICE_ID, "target_sha256": "a" * 64}],
            }
            examples.append(replace(e, prompt_input=data))
        self.examples = tuple(examples)
        self.registry = self.f.service.evidence_registry_builder.build(self.examples)
        self.prompt = self.f.service.prompt_builder.build(
            self.f.prepared.request, self.f.prepared.mask_result, self.examples,
            evidence_registry=self.registry).payload
        self.context = citation_context(self.prompt)

    def tearDown(self):
        self.f.tearDown()

    def response(self, **changes):
        return {"selected_device": fixtures.DEVICE_ID, "config_id": fixtures.CONFIGURATION_ID,
                "claim": "Il dispositivo e la configurazione sono suggeriti dagli esempi citati.",
                "evidence": ["E2", "E4"], **changes}

    def validate(self, response, **kwargs):
        return self.f.service.validator.validate(
            response, self.f.prepared.request, self.f.prepared.mask_result,
            self.f.prepared.hardware_catalog, evidence_registry=kwargs.pop("registry", self.registry),
            citation_context=kwargs.pop("context", self.context), **kwargs)

    def test_projection_preserves_order_features_and_canonical_input(self):
        original = copy.deepcopy(self.prompt)
        view = model_input(self.prompt)
        self.assertEqual(self.prompt, original)
        on_disk = json.loads(json.dumps(self.prompt))
        self.assertEqual(messages(self.prompt, "base"), messages(on_disk, "base"))
        self.assertEqual(citation_context(self.prompt), citation_context(on_disk))
        self.assertEqual(view["circuit"]["features"], self.prompt["live_request"]["circuit"]["features"])
        self.assertEqual([e["id"] for e in view["retrieved_labeled_examples"]], ["E1", "E2", "E3", "E4", "E5"])
        for source, shown in zip(self.prompt["retrieved_labeled_examples"], view["retrieved_labeled_examples"]):
            self.assertEqual(source["example"]["input"]["circuit"]["features"], shown["circuit"]["features"])
            self.assertEqual(shown["compatible_devices"], [fixtures.DEVICE_ID])
            self.assertNotIn("evidence", shown)
            self.assertNotIn("claims", shown)
        text = messages(self.prompt, "checklist")[0]["content"]
        for forbidden in ("qasm2", "OPENQASM", "source_sha256", "summary_id", "record_id",
                          "rag_id", "claim_id", "caveat_id", "catalog_snapshot_id", "shared_values"):
            self.assertNotIn(forbidden, text)
        self.assertIsNone(re.search(r"[0-9a-f]{64}", text))
        self.assertEqual(text.count('"compatible_hardware"'), 1)

    def test_schema_and_transport_agree_without_old_contract(self):
        request = payload(self.prompt, {"temperature": 0, "prompt_variant": "base"})
        schema = request["response_format"]["schema"]
        self.assertEqual(schema, response_schema(self.prompt))
        self.assertEqual(set(schema["required"]), {"selected_device", "config_id", "claim", "evidence"})
        self.assertNotIn("request_id", json.dumps(schema))

    def test_free_claim_citations_resolve_without_fabricated_structured_claims(self):
        result = self.validate(self.response())
        self.assertTrue(result.is_valid, result.issues)
        rec = result.recommendation
        self.assertEqual(rec.evidence, ("E2", "E4"))
        self.assertEqual([c.record_id for c in rec.example_citations],
                         [self.examples[1].record_id, self.examples[3].record_id])
        self.assertEqual(rec.claim, self.response()["claim"])
        self.assertEqual(rec.schema_version, "3.0.0")
        self.assertEqual(rec.qiskit_plan.seed_transpiler, 0)
        self.assertEqual(rec.claims, ())
        self.assertEqual(rec.evidence_references, ())
        # Provenance validation does not pretend to prove the free-text assertion.
        self.assertTrue(self.validate(self.response(config_id="o3_default_default")).is_valid)

    def test_invalid_references_json_types_and_claim(self):
        for response in (
            self.response(evidence=["E6"]), self.response(evidence=["E2", "E2"]),
            self.response(evidence=[]), self.response(claim="   "),
            self.response(claim=3), self.response(claim="x" * 1201),
            self.response(evidence=["rag_" + "a" * 64]),
            self.response(config_id="invented"), self.response(selected_device="unavailable"),
            '{"selected_device":"x","selected_device":"y"}', "[]",
        ):
            with self.subTest(response=str(response)[:80]):
                self.assertFalse(self.validate(response).is_valid)
        old = self.f._response()
        self.assertFalse(self.validate(old).is_valid)

    def test_context_cannot_be_reused_for_other_request_registry_or_order(self):
        for context in (
            replace(self.context, request_id="another-request"),
            replace(self.context, catalog_snapshot_id="another-catalog"),
            replace(self.context, record_ids=tuple(reversed(self.context.record_ids))),
            replace(self.context, registry_sha256="wrong"),
            replace(self.context, request_sha256="wrong"),
        ):
            with self.assertRaises(RuntimeError):
                self.validate(self.response(), context=context)
        with self.assertRaises(RuntimeError):
            self.validate(self.response(), registry=self.f.registry)

    def test_unknown_alias_for_shorter_context_and_no_rag(self):
        prompt = self.f.service.prompt_builder.build(
            self.f.prepared.request, self.f.prepared.mask_result, (self.f.example,),
            evidence_registry=self.f.registry).payload
        result = self.validate(self.response(evidence=["E5"]), registry=self.f.registry,
                               context=citation_context(prompt))
        self.assertIn("LLM_OUTPUT_UNKNOWN_EXAMPLE", {i.code for i in result.issues})
        registry = self.f.service.evidence_registry_builder.build(())
        prompt = self.f.service.prompt_builder.build(
            self.f.prepared.request, self.f.prepared.mask_result, (), evidence_registry=registry).payload
        context = citation_context(prompt)
        self.assertTrue(self.validate(self.response(evidence=[], claim="Scelta senza supporto storico."),
                                      registry=registry, context=context).is_valid)
        self.assertFalse(self.validate(self.response(), registry=registry, context=context).is_valid)
        self.assertEqual(response_schema(prompt)["properties"]["evidence"]["maxItems"], 0)

    def test_device_configuration_restrictions_remain_enforced(self):
        compatibility = replace(self.f.prepared.mask_result,
            available=(replace(self.f.prepared.mask_result.available[0],
                               allowed_qiskit_configuration_ids=("o3_default_default",)),))
        result = self.f.service.validator.validate(self.response(), self.f.prepared.request, compatibility,
            self.f.prepared.hardware_catalog, evidence_registry=self.registry, citation_context=self.context)
        self.assertIn("LLM_OUTPUT_CONFIGURATION_NOT_SUPPORTED_BY_DEVICE", {i.code for i in result.issues})

    def test_feedback_cannot_reintroduce_qasm_or_ids(self):
        prompt = copy.deepcopy(self.prompt)
        prompt["previous_validation_errors"] = [
            {"code": "LLM_OUTPUT_SCHEMA_INVALID", "path": "$." + "a" * 64,
             "message": "OPENQASM 2.0; qasm2 source_sha256 " + "b" * 64}]
        text = messages(prompt, "base")[0]["content"]
        self.assertNotIn("OPENQASM", text)
        self.assertNotIn("b" * 64, text)
        self.assertNotIn("a" * 64, text)
        self.assertEqual(citation_context(prompt), self.context)

    def test_service_repairs_with_stable_aliases_and_compilation_gate(self):
        service = self.f.service
        service.context_retriever = Mock()
        service.context_retriever.retrieve.return_value = self.examples
        sent = []
        def generate(prompt):
            sent.append(prompt.payload)
            return self.response(evidence=["E6"] if len(sent) == 1 else ["E2"])
        service.llm_gateway = Mock(generate=generate)
        service.compiler = Mock()
        result = service.recommend(self.f.submission)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(citation_context(sent[0]), citation_context(sent[1]))
        self.assertTrue(sent[1]["previous_validation_errors"])
        service.context_retriever.retrieve.assert_called_once()
        service.compiler.compile.assert_not_called()
        with self.assertRaises(UnvalidatedRecommendationError):
            service.compile_approved(ApprovedCompilation(replace(result, attempts=1), True))
        service.compile_approved(ApprovedCompilation(result, True))
        service.compiler.compile.assert_called_once_with(result.request, result.recommendation)

    def test_local_gateway_records_request_bound_map_and_raw_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            answer = json.dumps(self.response())
            with patch.object(gateway, "audit_tokens", return_value=100), \
                 patch.object(gateway, "native_payload", side_effect=lambda p, _: p), \
                 patch.object(gateway, "generate", return_value={"transport_success": True, "content": answer}) as send:
                raw = gateway.LocalLlmGateway(directory, {"temperature": 0, "prompt_variant": "base"}, 8192, 60).generate(
                    PromptEnvelope(self.prompt))
            self.assertEqual(raw, answer)
            self.assertEqual(send.call_args.args[0]["response_format"]["schema"], response_schema(self.prompt))
            stored = json.loads(next(Path(directory).glob("*/encoding.json")).read_text())
            self.assertEqual(stored, audit(self.prompt))
            self.assertTrue(self.validate(raw).is_valid)

    def test_episode_repair_recovery_and_contract_change_protection(self):
        saved = {"prompt_sha256": "input", "source_sha256": "source", "circuit_id": "fixture",
                 "circuit_metadata": {"split": "train"}, "registry_sha256": "registry",
                 "examples": [], "features": [], "retrieval_and_prompt_seconds": 0.1, "prompt": self.prompt}
        responses = [{"content": json.dumps(self.response(evidence=refs)), "transport_success": True,
                      "elapsed_seconds": 1.25} for refs in (["E6"], ["E2"])]
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(run, "audit_tokens", return_value=100), \
                 patch.object(run, "native_payload", side_effect=lambda p, _: p), \
                 patch.object(run, "generate", side_effect=responses) as generate, \
                 patch("llm_selection.train_check.check", return_value={"applicable": False}):
                directory = Path(folder)/"episode"
                result = run.episode(directory, saved, {"id": "p0_t0", "prompt_variant": "base", "temperature": 0},
                                     self.f.service, self.f.prepared, self.registry, 0.1, {"context": 8192})
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["llm_calls"], 2)
                self.assertEqual(result["measured_call_seconds"], 2.5)
                before = json.loads((directory/"attempt_1/encoding.json").read_text())
                after = json.loads((directory/"attempt_2/encoding.json").read_text())
                self.assertEqual(before["aliases"], after["aliases"])
                self.assertEqual(before["citation_context"], after["citation_context"])
                with patch("prototype.prompting.rendering.BASE_INSTRUCTION", "Changed"):
                    with self.assertRaisesRegex(ValueError, "new episode label"):
                        run.episode(directory, saved, {"id": "p0_t0", "prompt_variant": "base", "temperature": 0},
                                    self.f.service, self.f.prepared, self.registry, 0.1, {"context": 8192})
                self.assertEqual(generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()

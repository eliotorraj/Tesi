"""Controlli su dati invariati, fonti inventate, errori reali e ripresa."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from llm_selection.compact_prompt import encode, decode, model_input, expand_response, audit
from llm_selection.configuration import messages
from llm_selection.common import read_json
from llm_selection import run
from llm_selection.train_check import check
from llm_selection.run import summarize_response
import test_claim_evidence_validation as fixtures

class CompactPromptTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ClaimEvidenceValidationTests()
        self.fixture.setUp()
        f = self.fixture
        self.prompt = f.service.prompt_builder.build(f.prepared.request, f.prepared.mask_result,
                                                     (f.example,), evidence_registry=f.registry).payload
    def tearDown(self):
        self.fixture.tearDown()

    def test_all_nested_data_and_exact_qasm_survive_compaction(self):
        prompt = copy.deepcopy(self.prompt)
        block = [{"long_field_name": i, "source_hash": "a"*64, "precise": 1.2345678901234567e-120} for i in range(5)]
        prompt["duplicate_blocks"] = [block, copy.deepcopy(block)]
        original = copy.deepcopy(prompt)
        encoded = encode(prompt)
        self.assertEqual(decode(encoded), original)
        self.assertEqual(prompt, original)
        self.assertEqual(model_input(encoded)["live_request"]["circuit"]["qasm2"],
                         prompt["live_request"]["circuit"]["qasm2"])
        self.assertEqual(model_input(encoded)["response_contract"]["json_schema"],
                         prompt["response_contract"]["json_schema"])
        self.assertEqual(len(model_input(encoded)["retrieved_labeled_examples"]), 1)
        self.assertTrue(encoded["shared_values"])
        self.assertNotIn("NEVER source_id", messages(prompt, "base")[0]["content"])
        self.assertNotIn("qasm2", messages(prompt, "base")[0]["content"])

    def test_known_aliases_preserve_validity_without_filling_fields(self):
        f = self.fixture
        response = f._response()
        aliases = {"R1": fixtures.RECORD_ID, "E1": fixtures.EVIDENCE_ID,
                   "C1": fixtures.DEVICE_SOURCE_CLAIM_ID, "C2": fixtures.CONFIGURATION_SOURCE_CLAIM_ID}
        inverse = {value: key for key, value in aliases.items()}
        for ref in response["evidence_refs"]:
            for key in ("record_id", "source_id", "source_claim_id"):
                ref[key] = inverse[ref[key]]
        original = copy.deepcopy(response)
        expanded = expand_response(json.dumps(response), aliases)
        self.assertTrue(f._validate(expanded).is_valid)
        self.assertEqual(response, original)
        self.assertEqual(expanded, f._response())
        response["evidence_refs"][0]["source_id"] = "E999"
        self.assertFalse(f._validate(expand_response(json.dumps(response), aliases)).is_valid)
        response = copy.deepcopy(original)
        del response["evidence_refs"][0]["source_claim_id"]
        result = f._validate(expand_response(json.dumps(response), aliases))
        self.assertIn("LLM_OUTPUT_SOURCE_CLAIM_REQUIRED", {i.code for i in result.issues})

    def test_local_ids_are_never_expanded_even_if_they_look_like_source_aliases(self):
        obj = {"evidence_refs": [{"reference_id": "C1", "record_id": "R1", "source_claim_id": "C1"}],
               "claims": [{"claim_id": "C1", "evidence_ref_ids": ["C1"]}]}
        expanded = expand_response(json.dumps(obj), {"C1": "claim_original", "R1": "rag_original"})
        self.assertEqual(expanded["evidence_refs"][0]["reference_id"], "C1")
        self.assertEqual(expanded["claims"], obj["claims"])
        self.assertEqual(expanded["evidence_refs"][0]["source_claim_id"], "claim_original")

    def test_malformed_json_is_not_repaired_by_alias_expansion(self):
        for raw in ('{"x":1,"x":2}', '{"x":', '["R1"]'):
            self.assertEqual(expand_response(raw, {"R1": "rag_original"}), raw)

    def test_real_validation_errors_serialize_and_keep_latency(self):
        f = self.fixture
        response = f._response()
        del response["evidence_refs"][0]["source_claim_id"]
        transport = {"content": json.dumps(response), "transport_success": True, "elapsed_seconds": 2.75}
        summary = summarize_response(transport, 1, 100, f.service, f.prepared, f.registry)
        self.assertEqual(summary["status"], "invalid_output")
        self.assertEqual(summary["response"]["elapsed_seconds"], 2.75)
        self.assertIn("LLM_OUTPUT_SOURCE_CLAIM_REQUIRED", {i["code"] for i in summary["issues"]})
        json.dumps(summary)
        valid = summarize_response({**transport, "content": json.dumps(f._response())}, 1, 100,
                                   f.service, f.prepared, f.registry)
        self.assertEqual(valid["status"], "success")
        json.dumps(valid)

    def test_real_error_is_sent_to_repair_and_changed_prompt_cannot_reuse_result(self):
        f = self.fixture
        valid = {"selected_device": fixtures.DEVICE_ID, "config_id": fixtures.CONFIGURATION_ID,
                 "claim": "Scelta basata sull'esempio.", "evidence": ["E1"]}
        invalid = {**valid, "evidence": ["E5"]}
        responses = [{"content": json.dumps(value), "transport_success": True, "elapsed_seconds": 2.75}
                     for value in (invalid, valid)]
        saved = {"prompt_sha256": "input", "source_sha256": "source", "circuit_id": "case",
                 "circuit_metadata": {"split": "validation"}, "registry_sha256": "registry",
                 "examples": [], "features": [], "retrieval_and_prompt_seconds": 0.1, "prompt": self.prompt}
        config = {"id": "p0_t0", "prompt_variant": "base", "temperature": 0.0}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/"case"
            with patch.object(run, "audit_tokens", return_value=100), patch.object(run, "native_payload", side_effect=lambda request, _: request), \
                    patch.object(run, "generate", side_effect=responses) as generate:
                result = run.episode(directory, saved, config, f.service, f.prepared, f.registry, 0.1,
                                     {"context": 131072})
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["llm_calls"], 2)
                self.assertEqual(result["measured_call_seconds"], 5.5)
                repair = read_json(directory/"attempt_2"/"prompt.json")["previous_validation_errors"]
                self.assertIn("LLM_OUTPUT_UNKNOWN_EXAMPLE", {i["code"] for i in repair})
                with patch("prototype.prompting.rendering.BASE_INSTRUCTION", "Changed instructions"):
                    with self.assertRaisesRegex(ValueError, "new episode label"):
                        run.episode(directory, saved, config, f.service, f.prepared, f.registry, 0.1,
                                    {"context": 131072})
                self.assertEqual(generate.call_count, 2)
                from prototype.prompting import messages as shared_messages
                for number, call in enumerate(generate.call_args_list, 1):
                    sent = call.args[0]
                    recorded = read_json(directory/f"attempt_{number}"/"prompt.json")
                    self.assertEqual(sent["messages"], shared_messages(recorded, "base"))
                    self.assertNotIn("shared_values", sent["messages"][0]["content"])

    def test_zero_distance_does_not_substitute_for_source_identity(self):
        saved = {"circuit_metadata": {"split": "train"}, "source_sha256": "actual",
                 "prompt": {"live_request": {"figure_of_merit": "expected_fidelity"},
                 "retrieved_labeled_examples": [{"record_id": "R1", "distance": 0,
                     "example": {"input": {"circuit": {"source_sha256": "different"}},
                                 "objective": {"name": "expected_fidelity"}}}]}}
        result = check(saved)
        self.assertFalse(result["self_retrieved_at_zero"])
        self.assertEqual(result["zero_distance_record_ids"], ["R1"])
        saved["circuit_metadata"]["split"] = "validation"
        self.assertEqual(check(saved), {"applicable": False})

    def test_reserved_markers_and_cyclic_references_are_rejected(self):
        prompt = copy.deepcopy(self.prompt)
        prompt["unexpected"] = {"$use": "D1"}
        with self.assertRaises(ValueError):
            encode(prompt)
        encoded = encode(self.prompt)
        encoded["shared_values"]["cycle"] = {"$use": "cycle"}
        encoded["prompt"]["unexpected"] = {"$use": "cycle"}
        with self.assertRaises(ValueError):
            decode(encoded)



    def test_common_encoding_is_recorded_in_code_provenance(self):
        from llm_selection.provenance import code_files, ROOT
        shared = ROOT / "prototype/prompting"
        tracked = set(code_files())
        self.assertTrue(set(shared.glob("*.py")).issubset(tracked))
        self.assertIn(ROOT/"schemas/llm_recommendation_v3.schema.json", tracked)

    def test_legacy_imports_delegate_to_the_shared_implementation(self):
        from prototype.prompting import compact, complete_graph, wire
        from llm_selection import compact_prompt, complete_graph as legacy_graph, wire as legacy_wire
        self.assertIs(compact_prompt.encode, compact.encode)
        self.assertIs(legacy_graph.encode, complete_graph.encode)
        self.assertIs(legacy_wire.unpack, wire.unpack)

if __name__ == "__main__":
    unittest.main()

"""Verifica il codec reale e la conservazione dei dati attraverso Node/TOON."""
import copy
import json
import unittest
from prototype.prompting.toon import encode_view, decode_view, project, metadata
from prototype.prompting.minimal import model_input, audit, response_schema
from prototype.prompting.rendering import messages, REPAIR_INSTRUCTION
from llm_selection.configuration import payload
import test_minimal_prompt as fixtures


class ToonTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.MinimalPromptTests()
        self.fixture.setUp()

    def tearDown(self):
        self.fixture.tearDown()

    def test_real_codec_preserves_complete_prompt_and_json_answer_contract(self):
        prompt = self.fixture.prompt
        original = copy.deepcopy(prompt)
        request = payload(prompt, {"temperature": 0, "prompt_variant": "checklist"})
        text = request["messages"][0]["content"]
        fence = chr(96) * 3
        data = text.split(fence + "toon\n", 1)[1].split("\n" + fence, 1)[0]
        self.assertEqual(decode_view(data), json.loads(json.dumps(model_input(prompt))))
        self.assertEqual(prompt, original)
        self.assertEqual(request["response_format"]["schema"], response_schema(prompt))
        self.assertEqual(text.count("response_schema:"), 1)
        self.assertIn("Return JSON, not TOON", text)
        self.assertNotIn(REPAIR_INSTRUCTION, text)
        record = audit(prompt)
        self.assertTrue(record["toon_roundtrip_verified"])
        self.assertFalse(record["roundtrip_verified"])  # The full canonical prompt still omits QASM.
        self.assertEqual(record["serialization"]["version"], "4.1.1")
        self.assertEqual(messages(prompt, "base", serialization="json")[0]["content"].splitlines()[1][0], "{")

    def test_table_keeps_all_features_and_directed_edge_order(self):
        features = {"zeros": 0.0, "ratio": 0.14285714285714285, "tiny": 1e-12, "large": 9007199254740991}
        view = {
            "circuit": {"features": features},
            "retrieved_labeled_examples": [
                {"id": "E1", "circuit": {"features": {"values": {**features, "zeros": 1.0}}}},
                {"id": "E2", "circuit": {"features": {"values": features}}},
            ],
            "compatible_hardware": [
                {"id": "grouped", "coupling_edges": [[0, 1], [0, 2], [1, 0], [2, 0]]},
                {"id": "unsorted", "coupling_edges": [[0, 1], [1, 0], [0, 2]]},
                {"id": "descending", "coupling_edges": [[2, 0], [0, 2]]},
                {"id": "full", "coupling_edges": {"topology": "fully_connected", "directed": True, "self_loops": False}},
            ],
        }
        before = copy.deepcopy(view)
        projected = project(view)
        self.assertEqual(len(projected["circuit_features"]), len(features))
        self.assertEqual(set(projected["circuit_features"]["zeros"]), {"current", "E1", "E2"})
        self.assertIn("coupling_adjacency", projected["compatible_hardware"][0])
        self.assertIn("coupling_edges", projected["compatible_hardware"][1])
        self.assertIn("coupling_edges", projected["compatible_hardware"][2])
        self.assertEqual(decode_view(encode_view(view)), view)
        self.assertEqual(view, before)

    def test_nonuniform_features_and_special_strings_are_not_lost(self):
        view = {"circuit": {"features": {"zeros": 0.0}},
                "retrieved_labeled_examples": [{"id": "E1", "circuit": {"features": {"values": {"other": 2.0}, "unit": "ratio"}}}],
                "values": ['001', 'true', 'false', 'null', 'a,b', 'c:d', 'line\nnext', 'è', '"quote"', '\t'],
                "empty": [], "boolean": False, "absent": None}
        self.assertNotIn("circuit_features", project(view))
        self.assertEqual(decode_view(encode_view(view)), view)

    def test_precision_loss_is_rejected_instead_of_sending_changed_data(self):
        with self.assertRaisesRegex(ValueError, "change input values"):
            encode_view({"circuit": {"features": {"integer": 9007199254740993}}})
        with self.assertRaises(ValueError):
            encode_view({"value": float("nan")})

    def test_repair_and_no_rag_use_the_same_codec_without_new_aliases(self):
        prompt = copy.deepcopy(self.fixture.prompt)
        prompt["previous_validation_errors"] = [{"code": "LLM_OUTPUT_DEVICE_NOT_ELIGIBLE", "path": "$.selected_device"}]
        text = messages(prompt, "base")[0]["content"]
        self.assertEqual(text.count(REPAIR_INSTRUCTION), 1)
        self.assertIn("Dispositivo non ammesso", text)
        empty = {"circuit": {"features": {"zero": 0.0}}, "retrieved_labeled_examples": [], "compatible_hardware": []}
        self.assertEqual(decode_view(encode_view(empty)), empty)

    def test_provenance_includes_the_installed_encoder_and_lock(self):
        from llm_selection.provenance import code_files, ROOT
        paths = {str(p.relative_to(ROOT)) for p in code_files()}
        for file in ("codec.mjs", "package.json", "package-lock.json", "node-lock.json",
                     "node_modules/@toon-format/toon/dist/index.mjs"):
            self.assertIn("prototype/prompting/toon_runtime/" + file, paths)


if __name__ == "__main__":
    unittest.main()

"""Prove su Bell e risposte simulate: nessuna inferenza o apertura del Test."""
from pathlib import Path
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"strumenti"))
from common import ROOT, AREA, read, save, sha
import numero_esempi as entry
from prototype.prompting import facts, minimal, toon


class ExampleCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import prepare
        cls.qasm = (ROOT/"examples/bell.qasm").read_text()
        cls.one = entry.prepare_k(cls.qasm, k=1)
        cls.ten = entry.prepare_k(cls.qasm, k=10)
        cls.five = prepare(cls.qasm)
        cls.view = minimal.model_input(cls.ten[1], max_examples=10)

    def response(self, alias="E10"):
        e = self.view["retrieved_labeled_examples"][9]
        return {
            "selected_device": e["selected_device"], "config_id": "o2_default_default",
            "facts": [{"assertion": "selected_device_matches_example", "example_id": alias}],
            "hypothesis": "Proposta tecnica non verificata.",
        }

    def test_manhattan_prefixes_and_independent_reference(self):
        from prototype.quantum_assistant.adapters.qdrant_context import LocalReferenceContextRetriever
        from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog, HardwareMaskBuilder
        from qiskit_dataset.catalog import load_catalog
        ids = lambda data: [r["rag_id"] for r in data[2]["records"]]
        self.assertEqual(ids(self.one), ids(self.ten)[:1])
        self.assertEqual(ids(self.five), ids(self.ten)[:5])
        self.assertEqual(len(set(ids(self.ten))), 10)
        catalog = load_catalog()
        hardware = MqtHardwareCatalog(catalog.supported_device_ids, configuration_catalog=catalog).snapshot()
        mask = HardwareMaskBuilder().filter(self.ten[0], hardware)
        expected = LocalReferenceContextRetriever().retrieve(self.ten[0], mask, limit=10)
        self.assertEqual(ids(self.ten), [r.record_id for r in expected])
        self.assertEqual([r["distance"] for r in self.ten[2]["records"]], [r.distance for r in expected])
        self.assertEqual([r["example_id"] for r in self.ten[2]["records"]], [f"E{i}" for i in range(1,11)])

    def test_ten_aliases_toon_roundtrip_and_real_support(self):
        self.assertEqual(toon.decode_view(toon.encode_view(self.view)), json.loads(json.dumps(self.view)))
        text = facts.messages(self.ten[1], max_examples=10)[0]["content"]
        self.assertIn("E1-E10", text)
        good = facts.verify(self.response(), self.ten[1], max_examples=10)
        self.assertTrue(good["schema_valid"] and good["selection_valid"])
        self.assertEqual(good["facts_status"], "verified")
        self.assertEqual(good["fact_checks"][0]["record_id"], self.ten[2]["records"][9]["rag_id"])
        bad = self.response()
        bad["selected_device"] = next(d["id"] for d in self.view["compatible_hardware"]
                                      if d["id"] != bad["selected_device"])
        self.assertEqual(facts.verify(bad, self.ten[1], max_examples=10)["facts_status"], "unverified")
        self.assertFalse(facts.verify(self.response("E11"), self.ten[1], max_examples=10)["schema_valid"])
        self.assertEqual(facts.verify(self.response("E2"), self.one[1])["facts_status"], "unverified")
        duplicate = copy.deepcopy(self.ten[1])
        duplicate["retrieved_labeled_examples"][9] = duplicate["retrieved_labeled_examples"][0]
        with self.assertRaises(ValueError):
            minimal.model_input(duplicate, max_examples=10)
        with self.assertRaises(ValueError):
            minimal.model_input(self.ten[1])

    def test_five_default_contract_unchanged(self):
        prompt = self.five[1]
        self.assertEqual(facts.response_schema(), facts.SCHEMA)
        self.assertEqual(facts.messages(prompt), facts.messages(prompt, max_examples=5))
        self.assertEqual(facts.audit(prompt), facts.audit(prompt, max_examples=5))
        self.assertEqual(minimal.model_input(prompt), minimal.model_input(prompt, max_examples=5))
        self.assertIn("E1-E5", facts.messages(prompt)[0]["content"])
        for k in (0, 5, 11, True, 1.0):
            with self.assertRaises(ValueError):
                entry.retrieval_policy(k)

    def test_no_silent_reduction_when_examples_missing(self):
        with patch("app.prepare", return_value=self.one):
            with self.assertRaisesRegex(ValueError, "recuperati 1"):
                entry.prepare_k(self.qasm, k=10)

    def test_runner_ten_examples_retries_tokens_and_validation(self):
        import runner
        source = ROOT/"examples/bell.qasm"
        row = {"circuit_id": "bell_synthetic", "source_sha256": sha(source), "technical_source": str(source)}
        completions = []
        def http(endpoint, payload, folder):
            if endpoint == "/apply-template":
                return {"prompt": "synthetic"}
            if endpoint == "/tokenize":
                return {"tokens": list(range(100))}
            self.assertEqual(endpoint, "/completion")
            self.assertEqual(payload["json_schema"], facts.response_schema(max_examples=10))
            response = self.response()
            if len(completions) < 2:
                response["facts"] = [{"assertion": "selected_device_has_enough_qubits", "example_id": "E10"}]
            completions.append(response)
            raw = {"content": json.dumps(response), "tokens_predicted": 8}
            save(folder/"response_raw.json", raw)
            save(folder/"timing.json", {"seconds": 0.1})
            return raw
        with tempfile.TemporaryDirectory() as temp, patch("app.Http", return_value=http), \
             patch.object(runner, "compile_job", return_value={"status": "success", "score": 0.5}):
            folder = Path(temp)
            result = runner.evaluate(row, folder, "llm_rag_k10", "http://localhost:8089",
                                     technical=True, prepare_fn=lambda _: self.ten, max_examples=10)
            self.assertEqual(result["status"], "success", result)
            self.assertEqual(result["llm_calls"], 3)
            self.assertEqual(result["retries"], 2)
            self.assertEqual(result["total_tokens"], 324)
            self.assertAlmostEqual(result["llm_response_seconds"], 0.3)
            self.assertEqual(len(read(folder/"encoding.json")["citation_context"]["record_ids"]), 10)
            self.assertEqual(read(folder/"decision_validation.json")["fact_checks"][0]["example_id"], "E10")

    def test_context_overflow_stops_before_generation(self):
        from app import decide
        endpoints = []
        def http(endpoint, payload, folder):
            endpoints.append(endpoint)
            if endpoint == "/apply-template":
                return {"prompt": "synthetic"}
            if endpoint == "/tokenize":
                return {"tokens": list(range(56000))}
            self.fail("No generation allowed")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Contesto insufficiente"):
                decide(self.ten[1], Path(temp), http, 60000, max_examples=10)
            self.assertEqual(read(Path(temp)/"attempt_1/context.json")["input_tokens"], 56000)
        self.assertEqual(endpoints, ["/apply-template", "/tokenize"])

    def test_campaign_isolation_resume_and_contract_refusal(self):
        calls = []
        rows = [{"circuit_id": f"synthetic_{i:03d}", "source_sha256": str(i), "split": "test"} for i in range(90)]
        original_read = read
        def reader(path):
            return {"circuits": rows} if path == entry.SOURCE else original_read(path)
        def evaluate(row, folder, method, *args, **kwargs):
            calls.append((row["circuit_id"], method))
            self.assertEqual(kwargs["prepare_fn"].keywords["k"], int(method.removeprefix("llm_rag_k")))
            self.assertEqual(kwargs["max_examples"], 10 if method.endswith("10") else 5)
            save(folder/"esito.json", dict(row, method=method, status="success", score=0.5, retries=0))
        historical = AREA/"preparazione/contratto_congelato.json"
        before = historical.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(entry, "BASE", Path(temp)), patch.object(entry, "read", side_effect=reader), \
                 patch.object(entry, "preflight", return_value={"ready": True, "checks": {}}), \
                 patch.object(entry, "verify_server", return_value={"model": "synthetic"}), \
                 patch.object(entry, "frozen_contract", return_value={"synthetic": True}), \
                 patch.object(entry, "code_files", return_value={"synthetic": "sha"}), \
                 patch.object(entry, "evaluate", side_effect=evaluate), redirect_stdout(io.StringIO()):
                for k in (1, 10):
                    self.assertEqual(entry.cli(k, ["--esegui"]), 0)
                    self.assertEqual(entry.cli(k, ["--esegui"]), 0)
                with patch.object(entry, "frozen_contract", return_value={"synthetic": "changed"}):
                    with self.assertRaisesRegex(ValueError, "Ripresa incompatibile"):
                        entry.cli(1, ["--esegui"])
            self.assertEqual(len(calls), 180)
            self.assertEqual({m for _,m in calls}, {"llm_rag_k1", "llm_rag_k10"})
            for k in (1,10):
                base = Path(temp)/f"k_{k}/risultati/llm_rag_k{k}"
                self.assertEqual(len(list((base/"circuiti").glob("*/esito.json"))), 90)
                self.assertEqual(read(base/"contratto_congelato.json")["retrieval"]["k"], k)
        self.assertEqual(historical.read_bytes(), before)

    def test_verifica_never_uses_server_or_starts_cases(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(entry, "BASE", Path(temp)), \
             patch.object(entry, "preflight", return_value={"ready": True, "checks": {}}), \
             patch.object(entry, "verify_server", side_effect=AssertionError("Server forbidden")), \
             patch.object(entry, "evaluate", side_effect=AssertionError("Test forbidden")), redirect_stdout(io.StringIO()):
            for k in (1,10):
                self.assertEqual(entry.cli(k, ["--verifica"]), 0)
            self.assertFalse(list(Path(temp).glob("k_*/risultati")))


if __name__ == "__main__":
    unittest.main()

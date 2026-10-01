"""Verifiche tecniche: nessuna inferenza e nessun circuito Test eseguito."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "strumenti"))
from common import ROOT, read
from llm_recupero_random import ensure_contract
from recupero_random import prepare_random, select_records
from prototype.prompting.minimal import model_input, citation_context
from prototype.prompting.facts import verify
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus, EXPERIMENT_ID

class RandomRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_corpus()
        cls.devices = sorted({r["selected_device"]["device_id"] for r in cls.corpus.records})

    def test_reproducible_distinct_and_order_independent(self):
        from dataclasses import replace
        args = (self.devices, "expected_fidelity", "synthetic-source", 20260927)
        first, meta = select_records(self.corpus, *args)
        second, other = select_records(replace(self.corpus, records=tuple(reversed(self.corpus.records))), *args)
        self.assertEqual(first, second)
        self.assertEqual(meta, other)
        self.assertEqual(len({r["rag_id"] for r in first}), 5)
        self.assertTrue(all(r["split"] == "train" for r in first))
        changed, _ = select_records(self.corpus, *args[:-1], 20260928)
        self.assertNotEqual([r["rag_id"] for r in first], [r["rag_id"] for r in changed])

    def test_same_eligibility_and_no_distance(self):
        from dataclasses import replace
        from prototype.quantum_assistant.adapters.qdrant_context import matching_records
        device = self.devices[0]
        expected = matching_records(self.corpus, devices=[device], objective="expected_fidelity",
                                    experiment_id=EXPERIMENT_ID)
        chosen, meta = select_records(self.corpus, [device], "expected_fidelity", "x", 1)
        self.assertEqual(meta["candidate_count"], len(expected))
        self.assertTrue(all(r["selected_device"]["device_id"] == device for r in chosen))
        # Meno di cinque candidati: nessun ripiego su altri split o dispositivi.
        with self.assertRaises(ValueError):
            select_records(replace(self.corpus, records=tuple(expected[:4])), [device],
                           "expected_fidelity", "x", 1)

    def test_bell_prompt_preserves_aliases_and_validator_without_qdrant(self):
        with patch("app.prepare_index", side_effect=AssertionError("Indice vietato")), \
             patch("prototype.quantum_assistant.adapters.qdrant_context.manhattan",
                   side_effect=AssertionError("Distanza vietata")), \
             patch("prototype.quantum_assistant.adapters.qdrant_context.query_exact",
                   side_effect=AssertionError("Ricerca vietata")):
            _, prompt, log = prepare_random((ROOT/"examples/bell.qasm").read_text(), seed=1)
        view = model_input(prompt)
        self.assertEqual(len(view["retrieved_labeled_examples"]), 5)
        self.assertEqual(list(citation_context(prompt).aliases.values()),
                         [r["rag_id"] for r in log["records"]])
        self.assertTrue(all(r["distance"] is None for r in log["records"]))
        self.assertTrue(all("distance" not in e for e in view["retrieved_labeled_examples"]))
        example = view["retrieved_labeled_examples"][0]
        response = {"selected_device": example["selected_device"], "config_id": "o2_default_default",
                    "facts": [{"assertion": "selected_device_matches_example", "example_id": "E1"}],
                    "hypothesis": "Proposta tecnica non verificata."}
        self.assertEqual(verify(response, prompt)["facts_status"], "verified")

    def test_contract_refuses_mixed_resume_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"contratto.json"
            original = {"retrieval": {"seed": 1}, "code": {"a": "hash1"}}
            ensure_contract(path, original)
            content = path.read_bytes()
            ensure_contract(path, original)
            for changed in ({"retrieval": {"seed": 2}, "code": {"a": "hash1"}},
                            {"retrieval": {"seed": 1}, "code": {"a": "hash2"}}):
                with self.assertRaises(ValueError):
                    ensure_contract(path, changed)
            self.assertEqual(path.read_bytes(), content)

    def test_runner_uses_injected_preparation_and_keeps_logs(self):
        import runner
        from common import sha
        source = ROOT/"examples/bell.qasm"
        row = {"circuit_id": "bell_synthetic", "source_sha256": sha(source), "technical_source": str(source)}
        calls = []
        def prepare(qasm):
            calls.append(qasm)
            return prepare_random(qasm, seed=2)
        def decide(prompt, *args):
            view = model_input(prompt)
            return {"canonical_response": {
                "selected_device": view["compatible_hardware"][0]["id"],
                "config_id": "o2_default_default", "facts": [], "hypothesis": "Synthetic stub"},
                "facts_status": "verified"}
        with tempfile.TemporaryDirectory() as directory, \
             patch("app.prepare", side_effect=AssertionError("Preparazione standard vietata")), \
             patch("app.decide", side_effect=decide), \
             patch.object(runner, "compile_job", return_value={"status": "success", "score": 0.5}):
            folder = Path(directory)
            result = runner.evaluate(row, folder, "llm_recupero_random", "http://localhost:8089",
                                     technical=True, prepare_fn=prepare)
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(read(folder/"retrieval.json")["records"]), 5)
            self.assertEqual(result["split"], "technical")

    def test_cli_ninety_synthetic_cases_resume_in_separate_area(self):
        import io
        from contextlib import redirect_stdout
        import llm_recupero_random as entry
        from common import save, AREA
        calls = []
        rows = [{"circuit_id": f"synthetic_{i:03d}", "source_sha256": str(i), "split": "test"}
                for i in range(90)]
        original_read = read
        def reader(path):
            return {"circuits": rows} if path == entry.SOURCE else original_read(path)
        def evaluate(row, folder, method, *args, **kwargs):
            calls.append(row["circuit_id"])
            self.assertEqual(method, "llm_recupero_random")
            self.assertIn("prepare_fn", kwargs)
            save(folder/"esito.json", dict(row, method=method, status="success", score=0.5, retries=0))
        historical = AREA/"preparazione/contratto_congelato.json"
        before = historical.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            area = Path(directory)
            with patch.object(entry, "BASE", area), patch.object(entry, "read", side_effect=reader), \
                 patch.object(entry, "preflight", return_value={"ready": True, "checks": {}}), \
                 patch.object(entry, "verify_server", return_value={"model": "synthetic"}), \
                 patch.object(entry, "frozen_contract", return_value={"synthetic": True}), \
                 patch.object(entry, "code_files", return_value={"synthetic": "sha"}), \
                 patch.object(entry, "evaluate", side_effect=evaluate), redirect_stdout(io.StringIO()):
                self.assertEqual(entry.cli(["--esegui", "--seed", "123"]), 0)
                self.assertEqual(entry.cli(["--esegui", "--seed", "123"]), 0)
            self.assertEqual(len(calls), 90)
            base = area/"seed_123/risultati/llm_recupero_random"
            self.assertTrue((base/"contratto_congelato.json").is_file())
            self.assertEqual(len(list((base/"circuiti").glob("*/esito.json"))), 90)
        self.assertEqual(historical.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()

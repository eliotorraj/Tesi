'Offline checks without LLM calls or a campaign on the 90 Test circuits.'
from __future__ import annotations
from comune import *
import tempfile
import types
import unittest
from unittest.mock import patch
from adattatore import prepare, model_view, messages, decide
from memoria import make_observation, rank_examples
from registro import replay, finish_step, expected_observation
from esperimento import run_campaign
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
from prototype.prompting import facts, minimal

QASM = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;\n'


class FakeHttp:
    def __init__(self, response=None):
        self.calls = 0
        self.response = response or {
            "selected_device": "ibm_falcon_27", "config_id": "o2_default_default",
            "facts": [{"assertion": "selected_device_has_enough_qubits"}],
            "hypothesis": 'Proposed configuration for the supplied circuit.',
        }

    def __call__(self, endpoint, payload, directory):
        directory.mkdir(parents=True)
        save(directory / "request.json", payload)
        if endpoint == "/apply-template":
            result = {"prompt": json.dumps(payload["messages"])}
        elif endpoint == "/tokenize":
            result = {"tokens": [1] * 100}
        else:
            self.calls += 1
            result = {"content": json.dumps(self.response), "tokens_predicted": 20, "stop": True}
        save(directory / "response_raw.json", result)
        save(directory / "timing.json", {"seconds": 0.01})
        return result


class IncrementalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_corpus()
        from scripts.mqt_predictor_protocol import FROZEN_TARGET_SHA256
        cls.targets = FROZEN_TARGET_SHA256

    def row(self, i):
        qasm = QASM + "// fixture " + str(i) + "\n"
        return {"circuit_id": f"fixture_{i}", "source_sha256": hashlib.sha256(qasm.encode()).hexdigest(),
                "split": "test", "_qasm": qasm}

    def contract(self, rows, order="01_manifest"):
        return {"experiment_id": "verification", "order": order, "rows": rows,
                "initial_source_hashes": [r["retrieval_input"]["circuit"]["source_sha256"] for r in self.corpus.records],
                "targets": self.targets, "plan": {"llm_timeout_seconds": 1, "compilation_timeout_seconds": 10}}

    def fixture_evaluator(self, row, folder, *, corpus, observations, position, **kwargs):
        folder.mkdir(parents=True)
        prompt, retrieval = prepare(row["_qasm"], corpus=corpus, observations=observations, row=row, position=position)
        decision = {"selected_device": "ibm_falcon_27", "config_id": "o2_default_default"}
        result = {"circuit_id": row["circuit_id"], "source_sha256": row["source_sha256"],
                  "status": "success", "score": 0.9, "device": decision["selected_device"],
                  "config_id": decision["config_id"], "finished_at": "2026-10-02T00:00:00Z",
                  "validation": {"is_executable_on_target": True},
                  "total_seconds": 1.0, "total_tokens": 120, "choice_seconds": 0.5,
                  "compilation_seconds": 0.5, "llm_calls": 1}
        save(folder / "begin.json", {"synthetic": True})
        (folder / "input.qasm").write_text(row["_qasm"])
        save(folder / "prompt.json", prompt)
        save(folder / "retrieval.json", retrieval)
        save(folder / "decision.json", decision)
        save(folder / "compilazione/result.json", result)
        (folder / "compilazione/compiled.qasm").write_text("// SYNTHETIC TEST FIXTURE\n" + QASM)
        save(folder / "esito.json", result)
        return result

    def test_server_transport_override_and_model_identity(self):
        import io
        import app
        from esperimento import verify_server
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "fixture.gguf"
            model.write_bytes(b"SYNTHETIC SERVER FIXTURE")
            artifact = {"size_bytes": model.stat().st_size, "gguf_sha256": sha(model)}
            props = {"model_path": str(model), "default_generation_settings": {"n_ctx": 60000}}
            args = types.SimpleNamespace(model_path=model, url="http://localhost:1/", transport="native")
            with patch.dict(app.CONFIG, {"profile": {"artifact": artifact}}), \
                 patch("platform.release", return_value="microsoft-standard-WSL2"), \
                 patch("urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(json.dumps(props).encode())) as native, \
                 patch("subprocess.run", return_value=types.SimpleNamespace(stdout=json.dumps(props).encode())) as windows:
                self.assertEqual(verify_server(args)["transport"], "native")
                self.assertEqual(native.call_count, 1)
                self.assertEqual(windows.call_count, 0)
                args.transport = "windows"
                self.assertEqual(verify_server(args)["transport"], "windows")
                args.transport = "auto"
                self.assertEqual(verify_server(args)["transport"], "windows")
                self.assertEqual(windows.call_count, 2)
                props["default_generation_settings"]["n_ctx"] = 8192
                args.transport = "native"
                with self.assertRaises(ValueError):
                    verify_server(args)
                model.write_bytes(b"CHANGED")
                with self.assertRaises(ValueError):
                    verify_server(args)

    def test_four_orders_reproducible(self):
        rows = [self.row(i) for i in range(20)]
        orders = [order_rows(rows, key) for key in ORDERS]
        self.assertEqual(orders[0], rows)
        self.assertEqual(orders[1], list(reversed(rows)))
        self.assertEqual(len({tuple(r["circuit_id"] for r in order) for order in orders}), 4)
        for key, result in zip(ORDERS, orders):
            self.assertEqual(result, order_rows(rows, key))
            self.assertEqual({r["circuit_id"] for r in result}, {r["circuit_id"] for r in rows})

    def test_empty_memory_matches_all_90_historical_retrievals(self):
        paths = sorted((BASELINE / "circuiti").glob("*/retrieval.json"))
        self.assertEqual(len(paths), 90)
        for path in paths:
            prompt = read(path.parent / "prompt.json")
            result = read(path.parent / "esito.json")
            live = prompt["live_request"]
            ranked = rank_examples(self.corpus, [], live["circuit"]["features"],
                                   [d["id"] for d in live["compatible_hardware"]],
                                   result["source_sha256"], 1)
            historical = read(path)["records"]
            self.assertEqual([r["rag_id"] for r in ranked], [r["rag_id"] for r in historical], path.parent.name)
            for a, b in zip(ranked, historical):
                self.assertAlmostEqual(a["distance"], b["distance"], places=13)

    def test_prompt_unchanged_without_observations(self):
        row = self.row(1)
        prompt, _ = prepare(row["_qasm"], corpus=self.corpus, observations=[], row=row, position=1)
        self.assertEqual(messages(prompt), facts.messages(prompt))
        self.assertEqual(model_view(prompt), minimal.model_input(prompt))

    def test_observation_not_best_or_median_and_future_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            rows = [self.row(1), self.row(2)]
            contract = self.contract(rows)
            save(base / "contratto.json", contract)
            folder = step_folder(base, 1, rows[0])
            self.fixture_evaluator(rows[0], folder, corpus=self.corpus, observations=[], position=1)
            observation, _ = expected_observation(base, folder, rows[0], 1, [], contract)
            prompt, _ = prepare(rows[1]["_qasm"], corpus=self.corpus, observations=[observation], row=rows[1], position=2)
            view = model_view(prompt)
            seen = [r for r in view["retrieved_labeled_examples"] if r.get("evidence_kind") == "single_execution"]
            self.assertEqual(len(seen), 1)
            from prototype.prompting.toon import encode_view, decode_view
            self.assertEqual(decode_view(encode_view(view)), json.loads(json.dumps(view)))
            self.assertEqual(facts.audit(prompt)["schema_version"], "4.0.0")
            self.assertIn("single_execution", messages(prompt)[0]["content"])
            self.assertNotIn("top_configurations", seen[0])
            self.assertNotIn("median_score", seen[0]["observed_configuration"])
            chosen = {"selected_device": "ibm_falcon_27", "config_id": "o2_default_default",
                      "facts": [{"assertion": "selected_pair_among_reported_best", "example_id": seen[0]["id"]}],
                      "hypothesis": 'Proposal to check.'}
            self.assertEqual(facts.verify(chosen, prompt)["facts_status"], "unverified")
            chosen["facts"][0]["assertion"] = "selected_device_matches_example"
            self.assertEqual(facts.verify(chosen, prompt)["facts_status"], "verified")
            with self.assertRaises(ValueError):
                prepare(rows[1]["_qasm"], corpus=self.corpus, observations=[observation], row=rows[1], position=1)
            same, log = prepare(rows[0]["_qasm"], corpus=self.corpus, observations=[observation], row=rows[0], position=2)
            self.assertTrue(all(r["origin"] == "initial" for r in log["records"]))

    def test_sequential_resume_isolation_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            rows = [self.row(i) for i in range(3)]
            contract = self.contract(rows)
            save(base / "contratto.json", contract)
            args = types.SimpleNamespace(url="http://localhost:1", transport="native")
            calls = []
            def evaluator(row, folder, **kw):
                calls.append((kw["position"], len(kw["observations"])))
                return self.fixture_evaluator(row, folder, **kw)
            run_campaign(base, contract, self.corpus, args, evaluator=evaluator)
            self.assertEqual(calls, [(1, 0), (2, 1), (3, 2)])
            records, commits, _ = replay(base, contract)
            self.assertEqual(len(records), 3)
            run_campaign(base, contract, self.corpus, args, evaluator=evaluator)
            self.assertEqual(len(calls), 3)
            other = base / "other_order"
            other.mkdir()
            save(other / "contratto.json", self.contract(rows, "02_inverso"))
            self.assertEqual(replay(other, self.contract(rows, "02_inverso"))[0], [])
            (step_folder(base, 1, rows[0]) / "decision.json").write_text("{}")
            with self.assertRaises(ValueError):
                replay(base, contract)

    def test_interruption_not_retried_and_pending_observation_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            rows = [self.row(1), self.row(2)]
            contract = self.contract(rows)
            save(base / "contratto.json", contract)
            first = step_folder(base, 1, rows[0])
            first.mkdir(parents=True)
            save(first / "begin.json", {"synthetic": True})
            args = types.SimpleNamespace(url="http://localhost:1", transport="native")
            calls = []
            def evaluator(row, folder, **kw):
                calls.append(row["circuit_id"])
                return self.fixture_evaluator(row, folder, **kw)
            run_campaign(base, contract, self.corpus, args, evaluator=evaluator)
            records, commits, _ = replay(base, contract)
            self.assertEqual(calls, ["fixture_2"])
            self.assertEqual(len(records), 1)
            self.assertEqual(read(first / "esito.json")["status"], "interrupted")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            row = self.row(3)
            contract = self.contract([row])
            save(base / "contratto.json", contract)
            folder = step_folder(base, 1, row)
            self.fixture_evaluator(row, folder, corpus=self.corpus, observations=[], position=1)
            observation, _ = expected_observation(base, folder, row, 1, [], contract)
            save(base / "memoria_incrementale/records/001.json", observation)
            self.assertEqual(replay(base, contract)[0], [])
            run_campaign(base, contract, self.corpus, args,
                         evaluator=lambda *a, **kw: self.fail('No new decision is allowed'))
            self.assertEqual(len(replay(base, contract)[0]), 1)

    def test_failed_and_zero_score_admission(self):
        row = self.row(1)
        for status, value, admitted in (("failure", None, False), ("timeout", None, False), ("success", 0, True)):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                contract = self.contract([row])
                save(base / "contratto.json", contract)
                folder = step_folder(base, 1, row)
                self.fixture_evaluator(row, folder, corpus=self.corpus, observations=[], position=1)
                for name in ("esito.json", "compilazione/result.json"):
                    result = read(folder / name)
                    result.update(status=status, score=value)
                    (folder / name).write_text(json.dumps(result))
                record, reason = expected_observation(base, folder, row, 1, [], contract)
                self.assertEqual(record is not None, admitted)
                if admitted:
                    self.assertEqual(record["observed_configuration"]["score"], 0)

    def test_decide_three_attempt_policy_with_fake_http(self):
        row = self.row(1)
        prompt, _ = prepare(row["_qasm"], corpus=self.corpus, observations=[], row=row, position=1)
        http = FakeHttp()
        with tempfile.TemporaryDirectory() as tmp:
            result = decide(prompt, Path(tmp), http)
        self.assertEqual(http.calls, 1)
        self.assertEqual(result["facts_status"], "verified")
        http = FakeHttp({"selected_device": "ibm_falcon_27", "config_id": "o2_default_default",
                         "facts": [{"assertion": "same_qubit_count_as_example", "example_id": "E5"}],
                         "hypothesis": 'Proposal.'})
        # Force an unsupported fact independently of the retrieved circuit sizes.
        http.response["facts"] = [{"assertion": "selected_device_has_enough_qubits", "example_id": "E1"}]
        with tempfile.TemporaryDirectory() as tmp:
            result = decide(prompt, Path(tmp), http)
        self.assertEqual(http.calls, 3)
        self.assertEqual(result["status"], "accepted_with_unverified_facts")

    def test_real_bell_compilation_with_simulated_llm(self):
        from adattatore import evaluate
        row = self.row(10)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "bell.qasm"
            source.write_text(row["_qasm"])
            folder = base / "step"
            with patch("adattatore.source_path", return_value=source), patch("adattatore.app.Http", return_value=FakeHttp()):
                result = evaluate(row, folder, corpus=self.corpus, observations=[], position=1,
                                  url="http://localhost:1", transport="native",
                                  plan={"llm_timeout_seconds": 1, "compilation_timeout_seconds": 100})
            self.assertEqual(result["status"], "success", result)
            self.assertTrue(0 <= result["score"] <= 1)
            self.assertEqual(result["llm_calls"], 1)
            self.assertEqual(result["total_tokens"], 120)
            observation, _ = expected_observation(base, folder, row, 1, [], self.contract([row]))
            self.assertIsNotNone(observation)
            self.assertFalse(observation["observed_configuration"]["optimality_verified"])

    def test_report_pairs_failures_and_missing_measurements(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('incremental_report', BASE / 'report/genera.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        summarize = module.summarize
        rows = []
        for value, delta, status in [(0, -0.5, "success"), (None, None, "timeout"), (0.9, 0.1, "success")]:
            row = {"score": value, "delta_score": delta, "baseline_score": 0.5 if value == 0 else 0.8,
                   "status": status, "memory_after": 2, "retrieved_incremental": 1,
                   "regret": None, "oracle_exhaustive": None, "facts_unverified": False}
            row.update({k: None for k in ("total_seconds", "baseline_total_seconds", "total_tokens",
                                         "baseline_total_tokens", "choice_seconds", "compilation_seconds", "llm_calls")})
            rows.append(row)
        summary = summarize(rows, 90)
        self.assertEqual(summary["paired"], 2)
        self.assertEqual(summary["failures"], 1)
        self.assertAlmostEqual(summary["mean_delta"], -0.2)
        self.assertIsNone(summary["total_tokens"]["mean_known"])
        self.assertEqual(summary["total_tokens"]["measured"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Contratto v4, fallback, ripresa e confronto su riferimenti incompleti."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from prototype.prompting import facts
from llm_selection.common import OUTPUT, read_json, write_json
from llm_selection.v2 import run
from llm_selection.v2.settings import CONFIGURATIONS
from llm_selection.v2.evaluate import observed_references, choose
from llm_selection.v2.__main__ import resources_ready

VIEW = {
    "circuit": {"name": "current", "num_qubits": 5},
    "compatible_hardware": [{"id": "device_a", "num_qubits": 10}],
    "configuration_catalog": [{"config_id": "c1"}, {"config_id": "c2"}],
    "retrieved_labeled_examples": [
        {"id": "E1", "circuit": {"name": "historical", "num_qubits": 5}, "selected_device": "device_a",
         "top_configurations": [{"device_id": "device_a", "config_id": "c1", "tied_score_config_ids": ["c2"], "median_score": .8}]}],
}

def answer(assertion="selected_device_has_enough_qubits", **extra):
    return {"selected_device": "device_a", "config_id": "c2",
            "facts": [{"assertion": assertion, **extra}], "hypothesis": "Una proposta da verificare sul circuito corrente."}

class FactsTests(unittest.TestCase):
    def check(self, response):
        with patch.object(facts, "model_input", return_value=copy.deepcopy(VIEW)), \
             patch.object(facts, "citation_context", return_value=SimpleNamespace(aliases={"E1": "train-id"})):
            return facts.verify(json.dumps(response), {})

    def test_tied_historical_pair(self):
        r = self.check(answer("selected_pair_among_reported_best", example_id="E1"))
        self.assertEqual(r["facts_status"], "verified")
        self.assertEqual(r["fact_checks"][0]["resolved"]["historical_rows"][0]["median_score"], .8)

    def test_one_or_two_facts_only(self):
        for count in (0, 3):
            data = answer()
            data["facts"] *= count
            self.assertFalse(self.check(data)["schema_valid"])
        data = answer()
        data["facts"].append({"assertion": "same_qubit_count_as_example", "example_id": "E1"})
        self.assertTrue(self.check(data)["schema_valid"])

    def test_bad_reference_and_device(self):
        r = self.check(answer("selected_device_matches_example", example_id="E2"))
        self.assertTrue(r["schema_valid"])
        self.assertTrue(r["selection_valid"])
        self.assertEqual(r["facts_status"], "unverified")
        data = answer()
        data["selected_device"] = "unknown"
        self.assertFalse(self.check(data)["selection_valid"])

    def test_hypothesis_not_certified_or_repaired(self):
        data = answer()
        data["hypothesis"] = "E3 guarantees perfect performance."
        r = self.check(data)
        self.assertEqual(r["facts_status"], "verified")
        self.assertEqual(r["hypothesis_status"], "not_evaluated")
        self.assertTrue(r["hypothesis_contains_example_ids"])
        self.assertFalse(r["explanation_fully_verified"])

    def test_hypothesis_length_limit(self):
        data = answer()
        data["hypothesis"] = "a" * 1000
        self.assertTrue(self.check(data)["schema_valid"])
        data["hypothesis"] += "a"
        self.assertFalse(self.check(data)["schema_valid"])

    def test_duplicate_json_and_blank_hypothesis(self):
        with patch.object(facts, "model_input", return_value=VIEW):
            self.assertFalse(facts.verify('{"a":1,"a":2}', {})["json_valid"])
        data = answer()
        data["hypothesis"] = " "
        self.assertFalse(self.check(data)["schema_valid"])

    def test_no_implicit_historical_pair_requirement(self):
        data = answer()
        data["config_id"] = "c1"
        view = copy.deepcopy(VIEW)
        view["retrieved_labeled_examples"][0]["top_configurations"] = []
        with patch.object(facts, "model_input", return_value=view), patch.object(facts, "citation_context", return_value=SimpleNamespace(aliases={})):
            result = facts.verify(json.dumps(data), {})
        self.assertTrue(result["selection_valid"])
        self.assertEqual(result["facts_status"], "verified")

class EpisodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = read_json(sorted((OUTPUT / "prompts/train").glob("*.json"))[0])
        view = facts.model_input(cls.saved["prompt"])
        device = view["compatible_hardware"][0]
        cls.good = {"selected_device": device["id"],
                    "config_id": device.get("allowed_qiskit_configuration_ids", [c["config_id"] for c in view["configuration_catalog"]])[0],
                    "facts": [{"assertion": "selected_device_has_enough_qubits"}],
                    "hypothesis": "Propongo questa coppia; il risultato resta da verificare."}
        cls.bad = copy.deepcopy(cls.good)
        cls.bad["facts"] = [{"assertion": "selected_device_matches_example"}]

    def fake_generate(self, answers):
        iterator = iter(answers)
        def invoke(payload, directory, timeout):
            directory.mkdir(parents=True)
            write_json(directory / "request.json", payload)
            value = next(iterator)
            if isinstance(value, BaseException):
                raise value
            response = {"transport_success": value != "reset", "curl_exit_code": 56 if value == "reset" else 0,
                        "content": "" if value == "reset" else json.dumps(value),
                        "elapsed_seconds": 1.0, "usage": {"prompt_tokens": 100, "completion_tokens": 20},
                        "started_at": "2026-09-19T00:00:00+00:00", "ended_at": "2026-09-19T00:00:01+00:00"}
            write_json(directory / "response.json", response)
            return response
        return invoke

    def call(self, directory, answers):
        launch = {"context": 60000, "process_start_time": "test", "run_directory": str(directory / "server")}
        with patch.object(run, "audit_tokens", return_value=100), patch.object(run, "native_payload", return_value={}), \
             patch.object(run, "generate", side_effect=self.fake_generate(answers)):
            return run.episode(directory, self.saved, CONFIGURATIONS[0], launch, runtime_hashes={})

    def test_three_bad_facts_are_success_with_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "episode"
            result = self.call(folder, [self.bad] * 3)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["attempt_count"], 3)
            self.assertEqual(result["repair_count"], 2)
            self.assertEqual(result["facts_status"], "unverified")
            self.assertTrue(result["accepted_with_unverified_facts"])
            self.assertEqual(read_json(folder / "attempt_3/fact_validation.json")["facts_status"], "unverified")

    def test_repair_then_success(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.call(Path(temp) / "episode", [self.bad, self.good])
            self.assertEqual(result["attempt_count"], 2)
            self.assertEqual(result["facts_status"], "verified")

    def test_invalid_schema_not_salvaged(self):
        bad = copy.deepcopy(self.good)
        bad["facts"] = []
        with tempfile.TemporaryDirectory() as temp:
            result = self.call(Path(temp) / "episode", [bad] * 3)
            self.assertEqual(result["status"], "failure")
            self.assertIsNone(result["selected_device_id"])

    def test_last_pair_invalid_does_not_salvage_earlier_choice(self):
        invalid = copy.deepcopy(self.good)
        invalid["selected_device"] = "unknown"
        with tempfile.TemporaryDirectory() as temp:
            result = self.call(Path(temp) / "episode", [self.bad, self.bad, invalid])
            self.assertEqual(result["status"], "failure")

    def test_reset_repeats_attempt_one_without_losing_record(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "episode"
            with self.assertRaises(run.RetryableInterruption):
                self.call(folder, ["reset"])
            self.assertFalse((folder / "attempt_1").exists())
            self.assertEqual(len(list((folder / "interrupted/attempt_1").iterdir())), 1)
            result = self.call(folder, [self.good])
            self.assertEqual(result["attempt_count"], 1)
            self.assertEqual(result["repair_count"], 0)
            self.assertEqual(result["llm_calls"], 2)
            self.assertEqual(result["transport_retries"], 1)

    def test_old_resource_timeout_is_void_after_server_restart(self):
        for keep_summary in (False, True):
            with self.subTest(keep_summary=keep_summary), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp) / "episode"
                self.call(folder, [self.good])
                (folder / "decision.json").unlink()
                attempt = folder / "attempt_1"
                old_server = Path(temp) / "old_server"
                write_json(old_server / "resource_abort.json", {"reason": "ram"})
                start = read_json(attempt / "started.json")
                start["server_run_directory"] = str(old_server)
                write_json(attempt / "started.json", start)
                response = read_json(attempt / "call/response.json")
                response.update(transport_success=False, curl_exit_code=28, content="")
                write_json(attempt / "call/response.json", response)
                if keep_summary:
                    summary = read_json(attempt / "summary.json")
                    summary.update(status="timeout", response=response)
                    write_json(attempt / "summary.json", summary)
                else:
                    (attempt / "summary.json").unlink()
                with self.assertRaises(run.RetryableInterruption):
                    self.call(folder, [])
                recovered = self.call(folder, [self.good])
                self.assertEqual(recovered["attempt_count"], 1)
                self.assertEqual(recovered["llm_calls"], 2)
                self.assertEqual(recovered["repair_count"], 0)

    def test_completed_call_recovered_without_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "episode"
            result = self.call(folder, [self.good])
            (folder / "decision.json").unlink()
            (folder / "attempt_1/summary.json").unlink()
            recovered = self.call(folder, [])
            self.assertEqual(recovered["attempt_count"], 1)
            self.assertTrue(read_json(folder / "attempt_1/summary.json")["recovered_completed_response"])
            self.assertEqual(recovered["selected_config_id"], result["selected_config_id"])

class ReferenceTests(unittest.TestCase):
    def test_incomplete_matrix_has_observed_reference(self):
        def row(config, eligible, score):
            return {"split": "validation", "circuit": {"source_sha256": "hash", "circuit_id": "c"},
                    "device": {"device_id": "d"}, "configuration": {"config_id": config},
                    "eligible_for_ranking": eligible, "ranking_score": score,
                    "attempts": {"success_count": 3 if eligible else 2, "observed_count": 3},
                    "score_observations": [{"seed_transpiler": i} for i in range(3)]}
        reference = observed_references([row("a", True, .8), row("b", False, None)])["hash"]
        self.assertEqual(reference["score"], .8)
        self.assertFalse(reference["matrix_complete"])
        self.assertEqual(reference["eligible_pairs"], 1)

    def test_evaluation_refuses_unsealed_before_loading_scores(self):
        from llm_selection.v2 import evaluate as module
        with patch.object(module, "require_sealed", side_effect=ValueError("not sealed")), patch.object(module, "load_jsonl") as load:
            with self.assertRaises(ValueError):
                module.evaluate("unsealed")
            load.assert_not_called()

    def test_selection_prioritizes_completeness_then_regret_then_repairs(self):
        def row(score, repairs=0, status="success"):
            return {"source_sha256": "same", "status": status, "regret_absolute": score,
                    "first_attempt_facts_verified": True, "facts_status": "verified",
                    "accepted_with_unverified_facts": False, "repair_count": repairs,
                    "physical_calls": 1 + repairs, "transport_retries": 0,
                    "total_call_seconds": 1, "total_output_tokens": 20,
                    "facts_checked": 1, "facts_verified": 1, "failure_category": None}
        self.assertEqual(choose({"a": [row(.1, 2)], "b": [row(.2)]})["winner"], "a")
        self.assertEqual(choose({"a": [row(.1, 2)], "b": [row(.1)]})["winner"], "b")
        self.assertEqual(choose({"a": [row(.1)], "b": [row(None, status="failure")]})["winner"], "a")

    def test_resource_hysteresis(self):
        guards = {"minimum_available_bytes": 1024**3, "resume_hotspot_c": 100, "maximum_edge_c": 95}
        sample = {"system_available_bytes": 2 * 1024**3, "gpu_sensors": [{"hotspot_c": 99, "edge_c": 65}]}
        self.assertTrue(resources_ready(sample, guards))
        sample["gpu_sensors"][0]["hotspot_c"] = 101
        self.assertFalse(resources_ready(sample, guards))
        sample["gpu_sensors"] = []
        self.assertFalse(resources_ready(sample, guards))

class PipelineIntegrationTests(unittest.TestCase):
    def test_analysis_uses_observed_reference_and_writes_new_artifacts(self):
        from contextlib import ExitStack
        from llm_selection.v2 import evaluate as module
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out = root / "study"
            folder = out / "qwen/p0_t0/c/decision.json"
            write_json(folder, {})
            write_json(out / "frozen_study.json", {})
            write_json(out / "all_decisions_sealed.json", {})
            study = {"study_id": "synthetic", "configurations": [CONFIGURATIONS[0]], "max_attempts": 3,
                     "evaluation_input_hashes": {}, "models": {"qwen": {}}, "fixed": {}, "policy": {}}
            row = {"source_sha256": "h", "circuit_id": "c", "status": "success", "repair_count": 0,
                   "first_attempt_facts_verified": True, "facts_status": "verified",
                   "accepted_with_unverified_facts": False, "physical_calls": 1,
                   "transport_retries": 0, "total_call_seconds": 1, "total_input_tokens": 10,
                   "total_output_tokens": 20, "facts_checked": 1, "facts_verified": 1}
            record = {"usage": {}, "timings_seconds": {}}
            agg = {"split": "validation", "circuit": {"source_sha256": "h", "circuit_id": "c"},
                   "device": {"device_id": "d"}, "configuration": {"config_id": "a"},
                   "eligible_for_ranking": True, "ranking_score": .8,
                   "attempts": {"success_count": 3, "observed_count": 3},
                   "score_observations": [{"seed_transpiler": i} for i in range(3)]}
            result = {"method_id": "llm_rag", "source_sha256": "h", "status": "success",
                      "score": .6, "regret_absolute": None, "failure_category": None}
            with ExitStack() as stack:
                patches = {"ROOT": root, "MODEL_KEYS": ("qwen",), "require_sealed": lambda _: study,
                           "study_root": lambda _: out, "load_catalog": lambda: None,
                           "source_manifest": lambda: {"circuits": [{"source_sha256": "h", "split": "validation"}]},
                           "device_capacities": lambda: {}, "validate_method_plan": lambda *a, **k: None,
                           "episode_data": lambda *a: (copy.deepcopy(row), copy.deepcopy(record)),
                           "enrich_costs": lambda *a: [], "validate_llm_decisions": lambda rows, **k: rows,
                           "matrix_paths": lambda: (root / "runs", root / "aggregates"),
                           "verify_hashes": lambda *a: None,
                           "load_jsonl": lambda p: [] if p.name == "runs" else [agg],
                           "evaluate_common_methods": lambda **k: [result], "attach_resources": lambda _: None,
                           "METHOD_PLAN_DIR_V2": root}
                write_json(root / "validation_method_plan.json", {})
                for name, value in patches.items():
                    stack.enter_context(patch.object(module, name, value))
                selected = module.evaluate("synthetic")
            self.assertEqual(selected["winner"], "qwen/p0_t0")
            saved = read_json(out / "analysis/episode_results.json")[0]
            self.assertAlmostEqual(saved["regret_absolute"], .2)
            self.assertIsNone(saved["regret_exhaustive_absolute"])
            self.assertTrue((out / "analysis/reference_scores.jsonl").exists())
            self.assertTrue((out / "selection_complete.json").exists())

    def test_new_report_sources_without_inference(self):
        from llm_selection.v2 import report
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = {"trial_id": "qwen/p0_t0", "source_sha256": "h", "status": "success", "regret_absolute": .2,
                   "repair_count": 0, "first_attempt_facts_verified": True, "facts_status": "verified",
                   "accepted_with_unverified_facts": False, "physical_calls": 1, "transport_retries": 0,
                   "total_call_seconds": 1, "total_output_tokens": 20, "facts_checked": 1,
                   "facts_verified": 1, "failure_category": None}
            write_json(root / "analysis/episode_results.json", [row])
            write_json(root / "analysis/selection.json", {"winner": "qwen/p0_t0"})
            write_json(root / "frozen_study.json", {"models": {"qwen": {"context": 60000, "micro_batch": 128}}})
            def fake_plot(*a, **k):
                write_json(root / "report/figures/manifest.json", [])
            with patch.object(report, "study_root", return_value=root), patch.object(report.subprocess, "run", side_effect=fake_plot), \
                 patch("llm_selection.v2.study.require_sealed"):
                report.build_report("synthetic", compile_pdf=False)
            self.assertIn("Seconda selezione", (root / "report/validation_selection.tex").read_text())
            self.assertTrue((root / "report/paired_uncertainty.json").exists())

if __name__ == "__main__":
    unittest.main()


class TechnicalCodeReviewTests(unittest.TestCase):
    def test_report_change_allowed_but_inference_change_rejected(self):
        from llm_selection.v2.study import verify_technical_code
        original = {"llm_selection/v2/report.py": "before", "llm_selection/v2/run.py": "fixed"}
        revised = {**original, "llm_selection/v2/report.py": "after"}
        self.assertEqual(verify_technical_code(original, revised)["kind"], "report_or_freeze_only")
        with self.assertRaises(ValueError):
            verify_technical_code(original, {**revised, "llm_selection/v2/run.py": "changed"})

    def test_study_runtime_must_match_original_snapshot(self):
        import llm_selection.v2.study as study
        from llm_selection.common import digest
        from scripts.mqt_predictor_protocol import file_sha256
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name = "llm_selection/v2/study.py"
            current = root / name
            current.parent.mkdir(parents=True)
            original_text = "def verify(): return True\ndef freeze(): return 1\n"
            current.write_text(original_text)
            original = {name: file_sha256(current)}
            old = root / "output/code_snapshots" / digest(original) / name
            old.parent.mkdir(parents=True)
            old.write_text(original_text)
            with patch.object(study, "ROOT", root), patch.object(study, "OUTPUT", root / "output"):
                current.write_text("def verify(): return True\ndef freeze(): return 2\n")
                self.assertEqual(study.verify_technical_code(original, {name: file_sha256(current)})["kind"], "report_or_freeze_only")
                current.write_text("def verify(): return False\ndef freeze(): return 2\n")
                with self.assertRaises(ValueError):
                    study.verify_technical_code(original, {name: file_sha256(current)})

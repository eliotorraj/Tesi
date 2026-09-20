"""Verifiche delle proprietà scientifiche e della ripresa, con soli dati sintetici."""
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from llm_selection import run, study, evaluate
from llm_selection.common import write_json, read_json, digest
from llm_selection.wire import pack, unpack
from qiskit_dataset.experiment_v2 import evaluate_common_methods

@dataclass
class Issue:
    code: str="LLM_OUTPUT_SCHEMA_INVALID"

def metric_row(cid, success=True, regret=0.1):
    return {"source_sha256":cid,"status":"success" if success else "failure",
        "decision_status":"success" if success else "failure",
        "regret_absolute":regret if success else None,"first_attempt_valid":success,
        "first_attempt_json_valid":success,"first_attempt_schema_valid":success,
        "llm_calls":1,"repair_count":0,"transport_retries":0,"total_call_seconds":1.0,
        "total_output_tokens":20,"peak_process_working_set_bytes":None,"peak_gpu_dedicated_bytes":None,
        "oracle_score":1.0,"device_exact_match":False,"configuration_exact_match":False,
        "pair_exact_match":False,"failure_category":None if success else "invalid_output"}

class SelectionTests(unittest.TestCase):
    def test_failure_cannot_improve_rank_by_removing_hard_case(self):
        rows={"complete":[metric_row("a",regret=.1),metric_row("b",regret=.9)],
              "selective":[metric_row("a",regret=0),metric_row("b",False)]}
        self.assertEqual(evaluate.choose(rows)["winner"],"complete")

    def test_equal_coverage_compares_same_circuits(self):
        rows={"a":[metric_row("x",regret=.2),metric_row("y",regret=0),metric_row("z",False)],
              "b":[metric_row("x",regret=.1),metric_row("y",False),metric_row("z",regret=.9)]}
        result=evaluate.choose(rows)
        self.assertEqual(result["winner"],"b")
        self.assertEqual(result["regret_common_source_hashes"],["x"])

    def test_no_winner_when_all_candidates_fail(self):
        self.assertIsNone(evaluate.choose({"a":[metric_row("x",False)]})["winner"])

    def test_missing_measurement_is_not_zero(self):
        self.assertIsNone(evaluate.complete_sum([1,None]))
        self.assertEqual(evaluate.complete_sum([]),0)

    def test_evaluator_cannot_open_scores_before_all_seals(self):
        with patch.object(evaluate,"require_all_sealed",side_effect=ValueError("not sealed")),patch.object(evaluate,"load_jsonl") as loader:
            with self.assertRaisesRegex(ValueError,"not sealed"): evaluate.evaluate()
            loader.assert_not_called()

    def test_test_methods_cannot_be_reduced(self):
        with self.assertRaisesRegex(ValueError,"test richiede"):
            evaluate_common_methods(split="test",catalog=None,manifest=None,plan=None,capacities=None,
                qiskit_runs=[],qiskit_summaries=[],llm_decisions={},qcompile_runs=[],
                method_config_sha256="",llm_method_ids=("llm_rag",),include_qcompile=False)

    def test_tampered_sealed_response_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);write_json(root/"response.json",{"answer":"old"})
            descriptor={"study_id":"synthetic"}
            write_json(root/"sealed.json",{"study_sha256":digest(descriptor),
                       "files":{"response.json":study.file_sha256(root/"response.json")}})
            study.verify_model_seal(root,descriptor)
            write_json(root/"response.json",{"answer":"new"})
            with self.assertRaisesRegex(ValueError,"modified"): study.verify_model_seal(root,descriptor)

    def test_table_roundtrip_keeps_all_values_and_qasm(self):
        original={"qasm":"OPENQASM 2.0;\nqreg q[2];\n",
                  "values":[{"a":i,"b":1e-120,"c":[{"nested":True}]} for i in range(8)]}
        self.assertEqual(unpack(pack(original)),original)

class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.root=Path(self.temporary.name)/"trial"/"case"
        self.saved={"prompt_sha256":"input","source_sha256":"source","circuit_id":"case",
            "circuit_metadata":{"split":"train"},"registry_sha256":"registry","examples":[],
            "features":[],"retrieval_and_prompt_seconds":0.1,"prompt":{"live_request":{"request_id":"fixture","catalog_snapshot_id":"fixture","figure_of_merit":"expected_fidelity","circuit":{"features":{}},"compatible_hardware":[]},"allowed_evidence_registry":{"records":[]},"configuration_catalog":{"allowed_configurations":[]},"response_contract":{"json_schema":{}}}}
        self.config={"id":"p0_t0","prompt_variant":"base","temperature":0.0}
        self.service=SimpleNamespace(validator=SimpleNamespace(validate=lambda *a,**k:SimpleNamespace(
            issues=[Issue()],is_valid=False)))
        self.context=SimpleNamespace(request=None,mask_result=None,hardware_catalog=None)

    def tearDown(self): self.temporary.cleanup()

    def episode(self):
        return run.episode(self.root,self.saved,self.config,self.service,self.context,{},.1,{"context":run.payload(self.saved["prompt"],self.config)["max_tokens"]+1024})

    def test_three_invalid_calls_are_terminal_and_never_repeated(self):
        response={"transport_success":True,"content":"{}","elapsed_seconds":1.0,"curl_exit_code":0}
        with patch.object(run,"audit_tokens",return_value=10),patch.object(run,"native_payload",return_value={}),patch.object(run,"generate",return_value=response) as generate:
            result=self.episode()
            self.assertEqual(result["llm_calls"],3)
            self.assertEqual(result["repair_count"],2)
            self.assertEqual(generate.call_count,3)
            again=self.episode()
            self.assertEqual(again,result)
            self.assertEqual(generate.call_count,3)

    def test_interrupted_dispatched_call_is_counted_and_not_reissued(self):
        write_json(self.root/"attempt_1"/"call"/"request.json",{"prompt":"synthetic"})
        with patch.object(run,"generate") as generate:
            result=self.episode()
            self.assertEqual(result["llm_calls"],1)
            self.assertEqual(result["failure"]["category"],"interrupted_attempt")
            generate.assert_not_called()

    def test_saved_complete_response_is_recovered_without_a_new_call(self):
        response={"transport_success":True,"content":"saved","elapsed_seconds":1.0,"curl_exit_code":0}
        write_json(self.root/"attempt_1"/"call"/"response.json",response)
        write_json(self.root/"attempt_1"/"prompt.json", self.saved["prompt"])
        write_json(self.root/"attempt_1"/"encoding.json", run.encoding_audit(self.saved["prompt"]))
        summary={"status":"success","attempt":1,"issues":[],"llm_calls":1,"response":response,
                 "selected_device_id":"device","selected_config_id":"config"}
        with patch.object(run,"summarize_response",return_value=summary) as validate,patch.object(run,"generate") as generate:
            result=self.episode()
            self.assertEqual(result["status"],"success")
            self.assertEqual(result["llm_calls"],1)
            self.assertEqual(result["repair_count"],0)
            validate.assert_called_once()
            generate.assert_not_called()

    def test_first_valid_answer_ends_episode(self):
        response={"transport_success":True,"content":"valid","elapsed_seconds":1.0,"curl_exit_code":0}
        summary={"status":"success","attempt":1,"issues":[],"llm_calls":1,"response":response,
                 "selected_device_id":"device","selected_config_id":"config"}
        with patch.object(run,"summarize_response",return_value=summary),patch.object(run,"audit_tokens",return_value=10), \
                patch.object(run,"native_payload",return_value={}),patch.object(run,"generate",return_value=response) as generate:
            result=self.episode()
            self.assertEqual(result["status"],"success")
            generate.assert_called_once()
            self.assertFalse((self.root/"attempt_2").exists())

    def test_context_failure_performs_no_inference(self):
        with patch.object(run,"audit_tokens",return_value=5000),patch.object(run,"generate") as generate:
            result=self.episode()
            self.assertEqual(result["llm_calls"],0)
            self.assertEqual(result["failure"]["category"],"full_prompt_exceeds_context")
            generate.assert_not_called()


class GraphTests(unittest.TestCase):
    def test_complete_graph_encoding_preserves_qasm_evidence_and_edge_order(self):
        from llm_selection.complete_graph import encode,decode
        original={"live_request":{"compatible_hardware":[
            {"num_qubits":3,"coupling_edges":[[i,j] for i in range(3) for j in range(3) if i!=j]}],
            "qasm":"OPENQASM 2.0;\nqreg q[3];\n"},"evidence":[{"score":1e-190}]}
        packed=encode(original)
        self.assertIsInstance(packed["live_request"]["compatible_hardware"][0]["coupling_edges"],dict)
        self.assertEqual(decode(packed),original)
        original["live_request"]["compatible_hardware"][0]["coupling_edges"].reverse()
        self.assertEqual(encode(original),original)

    def test_incomplete_graph_is_not_encoded_as_complete(self):
        from llm_selection.complete_graph import encode
        original={"live_request":{"compatible_hardware":[{"num_qubits":3,"coupling_edges":[[0,1],[1,0]]}]}}
        self.assertEqual(encode(original),original)

class ServerTests(unittest.TestCase):
    def test_dead_server_stops_remaining_cases(self):
        with tempfile.TemporaryDirectory() as folder,patch("llm_selection.controller.health",return_value=None):
            with self.assertRaisesRegex(RuntimeError,"remaining cases are pending"):
                run.ensure_server_available(Path(folder),{"failure":{"category":"transport_failure"}})

    def test_stopped_server_recovery_does_not_invent_exit_time(self):
        from llm_selection import server_state
        import json
        with tempfile.TemporaryDirectory() as folder,patch.object(server_state.subprocess,"run",
                return_value=SimpleNamespace(stdout=json.dumps({"owned_process_running":False,"pid":123}))), \
                patch("llm_selection.common.windows_path",return_value="synthetic"):
            directory=Path(folder)
            observed=server_state.ensure_stopped(directory)
            self.assertIsNone(observed["ended_at"])
            self.assertFalse((directory/"exit.json").exists())
            self.assertTrue((directory/"recovery_closed.json").exists())

    def test_running_server_cannot_be_declared_stopped(self):
        from llm_selection import server_state
        with tempfile.TemporaryDirectory() as folder,patch.object(server_state.subprocess,"run",
                return_value=SimpleNamespace(stdout='{"owned_process_running":true}')), \
                patch("llm_selection.common.windows_path",return_value="synthetic"):
            with self.assertRaisesRegex(ValueError,"Stop inference server"):
                server_state.ensure_stopped(Path(folder))
            self.assertFalse((Path(folder)/"recovery_closed.json").exists())


class AnalysisIntegrationTests(unittest.TestCase):
    def test_validation_subset_uses_qiskit_scores_without_qcompile(self):
        from qiskit_dataset import experiment_v2 as experiment
        configs=experiment.QISKIT_DEFAULT_CONFIG_IDS
        circuit={"circuit_id":"synthetic","source_sha256":"hash","num_qubits":2,"split":"validation"}
        catalog=SimpleNamespace(supported_device_ids=("device",),
            configurations=[SimpleNamespace(config_id=c) for c in configs],seeds=(0,1,2))
        runs={};summaries={}
        for index,config in enumerate(configs):
            score=.5+.25*index
            observations=[]
            for seed in catalog.seeds:
                run_id=f"{config}-{seed}"
                runs[("hash","device",config,seed)]={"status":"success","score":score,"run_id":run_id,"seed_transpiler":seed}
                observations.append({"run_id":run_id,"seed_transpiler":seed,"score":score})
            summaries[("hash","device",config)]={"eligible_for_ranking":True,"ranking_score":score,
                "device":{"device_id":"device"},"configuration":{"config_id":config},
                "score_observations":observations,"summary_id":config}
        plan={"plan_sha256":"synthetic","random_selection":{"rows":[{"source_sha256":"hash","repetitions":[
            {"repetition_index":seed,"selected_device_id":"device","selected_config_id":configs[0],"qiskit_seed":seed}
            for seed in catalog.seeds]}]}}
        decision={"source_sha256":"hash","status":"success","selected_device_id":"device","selected_config_id":configs[0],
                  "attempt_count":1,"raw_response_sha256":"raw"}
        with patch.object(experiment,"validate_qiskit_matrix",return_value=(runs,summaries)), \
                patch.object(experiment,"split_circuits",return_value=[circuit]):
            results=experiment.evaluate_common_methods(split="validation",catalog=catalog,manifest={},plan=plan,
                capacities={"device":2},qiskit_runs=[],qiskit_summaries=[],llm_decisions={"llm_rag":[decision]},
                qcompile_runs=[],method_config_sha256="configuration",llm_method_ids=("llm_rag",),include_qcompile=False)
        selected=next(r for r in results if r["method_id"]=="llm_rag")
        self.assertEqual(selected["score"],.5)
        self.assertAlmostEqual(selected["regret_absolute"],.25)
        self.assertFalse(any(r["method_id"] in ("llm_no_rag","frontier_llm",experiment.QCOMPILE_METHOD_ID) for r in results))

    def test_resources_from_two_server_invocations_are_both_kept(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            row={"resource_run_key":"a","attempt_windows":[("a","2026-01-01T00:00:00+00:00","2026-01-01T00:00:02+00:00"),
                    ("b","2026-01-01T00:00:00+00:00","2026-01-01T00:00:02+00:00")],
                 "peak_process_working_set_bytes":None,"peak_gpu_dedicated_bytes":None,"peak_gpu_shared_bytes":None,
                 "minimum_available_ram_bytes":None,"maximum_gpu_hotspot_c":None}
            for key,value in (("a",10),("b",20)):
                directory=root/"servers"/key
                write_json(directory/"launch.json",{"process_start_time":key})
                write_json(directory/"exit.json",{"exit_code":0})
                (directory/"resources.jsonl").write_text(json.dumps({"utc":"2026-01-01T00:00:01+00:00",
                    "working_set_bytes":value,"system_available_bytes":100-value})+"\n")
            with patch.object(evaluate,"OUTPUT",root),patch.object(evaluate,"ROOT",root):
                evaluate.attach_resources([row])
            self.assertEqual(row["peak_process_working_set_bytes"],20)
            self.assertEqual(row["minimum_available_ram_bytes"],80)
            self.assertEqual(len(row["server_resource_paths"]),2)
            self.assertIn("servers/b/resources.jsonl",row["server_resource_sources"])

    def test_report_sources_are_built_from_saved_rows_without_inference(self):
        from llm_selection import report
        from llm_selection.configuration import FIXED
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);analysis=root/"studies"/"synthetic"/"analysis"
            row={**metric_row("x"),"trial_id":"qwen/p0_t0","family":"synthetic","num_qubits":2}
            selection=evaluate.choose({"qwen/p0_t0":[row]})
            profile={"weight_precision":"Q8_0","context":4096,"cache_type":"q8_0","precision_reason":"Synthetic fixture",
                     "batch":64,"micro_batch":16,"gpu_layers":"all",
                     "artifact":{"base_repository":"synthetic","url":"https://example.invalid/fixture","gguf_sha256":"0"*64}}
            write_json(root/"final.json",{"winner":selection["winner"]})
            write_json(root/"frozen_study.json",{"study_id":"synthetic","models":{"qwen":profile},"fixed":FIXED,"timeout_seconds":3600})
            write_json(analysis/"episode_results.json",[row]);write_json(analysis/"selection.json",selection)
            def plotting_fixture(*args,**kwargs):
                write_json(root/"report"/"figures"/"manifest.json",[])
            with patch.object(report,"OUTPUT",root),patch.object(report,"FINAL",root/"final.json"), \
                    patch.object(report,"verify_local_selection"),patch.object(report.subprocess,"run",side_effect=plotting_fixture), \
                    patch("llm_selection.technical.technical_summary",return_value={"episodes":[],"servers":[],"episode_status_counts":{}}):
                result=report.build_report(compile_pdf=False)
            self.assertIsNone(result["pdf"])
            self.assertTrue((root/"report"/"validation_selection.tex").is_file())
            self.assertTrue((root/"report"/"standalone.tex").is_file())
            self.assertTrue((root/"report"/"technical_history.json").is_file())


class ControllerDiagnosticsTests(unittest.TestCase):
    def test_memory_abort_reports_observed_ram_and_threshold(self):
        from llm_selection.controller import failure_message
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            write_json(root/"resource_abort.json",{"reason":"available_ram_below_operational_limit",
                "last_sample":{"system_available_bytes":1090904064}})
            write_json(root/"launch.json",{"guards":{"minimum_available_bytes":1610612736}})
            message=failure_message(root,root/"runner.log")
            self.assertIn("1.02 GiB",message)
            self.assertIn("1.50 GiB",message)
            self.assertIn("resource_abort.json",message)

    def test_unexpected_runner_error_shows_original_log(self):
        from llm_selection.controller import failure_message
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"runner.log").write_text("ValueError: synthetic configuration mismatch")
            self.assertIn("synthetic configuration mismatch",failure_message(root,root/"runner.log"))

class NativeWeightVerificationTests(unittest.TestCase):
    def test_native_hash_proof_is_saved(self):
        import json
        from llm_selection import weights
        artifact={"local_path":"/mnt/d/models/synthetic.gguf","gguf_sha256":"a"*64,"size_bytes":123}
        record={"valid":True,"sha256":"a"*64,"size_bytes":123,"method":"Windows"}
        with tempfile.TemporaryDirectory() as folder,patch.object(weights.subprocess,"run",
                return_value=SimpleNamespace(returncode=0,stdout=json.dumps(record),stderr="")) as invoke:
            destination=Path(folder)/"proof.json"
            weights.verify_weights(artifact,destination)
            self.assertEqual(read_json(destination),record)
            arguments=invoke.call_args.args[0]
            self.assertIn("D:\\models\\synthetic.gguf",arguments)
            self.assertTrue(any("verify_weights.ps1" in arg for arg in arguments))

    def test_native_hash_cannot_accept_inconsistent_proof(self):
        from llm_selection import weights
        artifact={"local_path":"/mnt/d/models/synthetic.gguf","gguf_sha256":"a"*64,"size_bytes":123}
        with patch.object(weights.subprocess,"run",return_value=SimpleNamespace(returncode=0,
                stdout='{"valid":true,"sha256":"different","size_bytes":123}',stderr="")):
            with self.assertRaisesRegex(ValueError,"inconsistent"): weights.verify_weights(artifact)


class NativeLogStorageTests(unittest.TestCase):
    def test_server_log_link_points_to_native_directory_without_creating_target(self):
        from llm_selection.storage import allocate_server_directory
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);logical=root/"project"/"servers"/"trial-qwen";native=root/"native"
            event=root/"events.jsonl"
            record=allocate_server_directory(logical,event,native_root=native)
            self.assertTrue(logical.is_symlink())
            self.assertFalse((native/"trial-qwen").exists())
            self.assertEqual(logical.resolve(),native/"trial-qwen")
            (native/"trial-qwen").mkdir()
            write_json(native/"trial-qwen"/"launch.json",{"synthetic":True})
            self.assertEqual(read_json(logical/"launch.json"),{"synthetic":True})
            self.assertEqual(record["event"],"server_log_storage_allocated")

    def test_existing_server_logs_are_never_relocated_or_overwritten(self):
        from llm_selection.storage import allocate_server_directory
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);logical=root/"project"/"trial-qwen";logical.mkdir(parents=True)
            write_json(logical/"launch.json",{"old":True})
            with self.assertRaisesRegex(ValueError,"already exist"):
                allocate_server_directory(logical,root/"events.jsonl",native_root=root/"native")
            self.assertEqual(read_json(logical/"launch.json"),{"old":True})

    def test_existing_native_directory_or_dangling_link_is_not_reused(self):
        from llm_selection.storage import allocate_server_directory
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);logical=root/"project"/"trial-qwen";native=root/"native"
            (native/"trial-qwen").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,"already exist"):
                allocate_server_directory(logical,root/"events.jsonl",native_root=native)
            logical.parent.mkdir();logical.symlink_to(root/"missing",target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"already exist"):
                allocate_server_directory(logical,root/"events.jsonl",native_root=root/"different")

if __name__=="__main__": unittest.main()

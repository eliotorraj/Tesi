"""Regressioni su dati sintetici: isolamento, errori, ripresa, metriche e score."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"strumenti"))
from common import ROOT, AREA, save, read, sha
from runner import compile_job, llm_metrics, interrupted_result
from report import summary

class TestProtocol(unittest.TestCase):
    def test_no_rag_has_no_examples_and_capacity_fact(self):
        from app import prepare
        from prototype.prompting.facts import messages, verify
        from prototype.prompting.minimal import model_input
        with patch("app.load_corpus",side_effect=AssertionError("RAG accessed")):
            _,prompt,_=prepare((ROOT/"examples/bell.qasm").read_text(),rag=False)
        view=model_input(prompt)
        self.assertEqual(view["retrieved_labeled_examples"],[])
        self.assertIn("exactly one fact",messages(prompt)[0]["content"])
        choice={"selected_device":view["compatible_hardware"][0]["id"],
                "config_id":view["configuration_catalog"][0]["config_id"],
                "facts":[{"assertion":"selected_device_has_enough_qubits"}],"hypothesis":"Prova tecnica."}
        result=verify(choice,prompt)
        self.assertTrue(result["schema_valid"] and result["selection_valid"])
        self.assertEqual(result["facts_status"],"verified")
        choice["facts"]=[{"assertion":"selected_device_matches_example","example_id":"E1"}]
        self.assertEqual(verify(choice,prompt)["facts_status"],"unverified")


    def test_random_real_compilation_without_rag(self):
        from runner import evaluate
        source=ROOT/"examples/bell.qasm"
        row={"circuit_id":"bell","source_sha256":sha(source),"technical_source":str(source)}
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            with patch("app.load_corpus",side_effect=AssertionError("RAG accessed")):
                result=evaluate(row,folder,"random","http://localhost:8089",technical=True)
            self.assertEqual(result["status"],"success",result)
            self.assertIsNotNone(result["score"])
            self.assertTrue((folder/"compilazione/compiled.qasm").exists())


    def test_ninety_cases_and_resume_without_other_methods(self):
        import runner
        import io
        from contextlib import redirect_stdout
        from common import read as original_read
        rows=[{"circuit_id":f"synthetic_{i:03d}","source_sha256":str(i),"split":"test"} for i in range(90)]
        def reader(path):
            return {"circuits":rows} if path==runner.SOURCE else original_read(path)
        calls=[]
        def fake_evaluate(row,folder,method,*args):
            calls.append((row["circuit_id"],method))
            save(folder/"esito.json",dict(row,method=method,status="success",score=0.5,retries=0))
        with tempfile.TemporaryDirectory() as temp:
            area=Path(temp)
            with patch.object(runner,"AREA",area), patch.object(runner,"read",side_effect=reader), \
                 patch.object(runner,"preflight",return_value={"ready":True,"checks":{}}), \
                 patch.object(runner,"freeze",return_value="synthetic_contract"), \
                 patch.object(runner,"evaluate",side_effect=fake_evaluate), \
                 patch.object(sys,"argv",["casuale.py","--esegui"]),redirect_stdout(io.StringIO()):
                self.assertEqual(runner.cli("random"),0)
                self.assertEqual(runner.cli("random"),0)
            self.assertEqual(len(calls),90)
            self.assertEqual({method for _,method in calls},{"random"})
            self.assertEqual({p.name for p in (area/"risultati").iterdir()},{"random"})
            self.assertFalse((AREA/"preparazione/contratto_congelato.json").exists())

    def test_immutable_write(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"result.json"
            save(p,{"first":1})
            with self.assertRaises(FileExistsError):save(p,{"first":2})
            self.assertEqual(read(p),{"first":1})

    def test_interruption_is_retained_not_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            interrupted_result({"circuit_id":"x","source_sha256":"a"},folder,"random")
            self.assertEqual(read(folder/"esito.json")["status"],"interrupted")

    def test_tokens_and_retries_include_failed_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for i in (1,2):
                call=root/f"attempt_{i}/call"
                save(call/"failure.json",{"seconds":1.5})
                save(call.parent/"context.json",{"input_tokens":12})
            save(root/"attempt_1/call/response_raw.json",{"tokens_evaluated":12,"tokens_predicted":7})
            result=llm_metrics(root)
            self.assertEqual(result["retries"],1)
            self.assertIsNone(result["total_tokens"])
            self.assertEqual(result["known_output_tokens"],7)
            self.assertEqual(result["llm_response_seconds"],3)

    def test_quality_uses_only_successes_and_reports_missing(self):
        rows=[{"status":"success","score":0.8,"total_seconds":2},{"status":"failure","score":None}]
        result=summary(rows,90)
        self.assertEqual(result["mean_score"],0.8)
        self.assertEqual(result["failures"],1)
        self.assertEqual(result["pending"],88)
        self.assertEqual(result["total_seconds"]["missing_circuits"],1)

    def test_dead_worker_and_timeout_never_succeed(self):
        from subprocess import Popen
        with tempfile.TemporaryDirectory() as temp:
            result=compile_job(Path(temp)/"timeout",{"method":"random","source":"unused"},0.001)
            self.assertEqual(result["status"],"timeout")
            self.assertIsNone(result["score"])
        with tempfile.TemporaryDirectory() as temp:
            result=compile_job(Path(temp)/"failed",{"method":"random","source":"/missing.qasm"},100)
            self.assertEqual(result["status"],"failure")
            self.assertIsNone(result["score"])


    def test_mqt_worker_accepts_target_from_selector(self):
        from qiskit import QuantumCircuit,transpile
        from mqt.bench.targets import get_device
        from worker import main
        target=get_device("ibm_falcon_27")
        circuit=transpile(QuantumCircuit.from_qasm_file(ROOT/"examples/bell.qasm"),
                          target=target,seed_transpiler=0,num_processes=1)
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp)/"job.json"
            save(job,{"method":"mqt_predictor","source":str(ROOT/"examples/bell.qasm")})
            with patch("mqt.predictor.ml.predict_device_for_figure_of_merit",return_value=target), \
                 patch("mqt.predictor.rl.rl_compile",return_value=(circuit,["terminate"])):
                code=main(job)
            self.assertEqual(code,0,read(job.parent/"result.json"))
            self.assertEqual(read(job.parent/"result.json")["device"],"ibm_falcon_27")

    def test_score_matches_installed_mqt(self):
        from qiskit import QuantumCircuit,transpile
        from mqt.bench.targets import get_device
        from mqt.predictor.reward import expected_fidelity as original
        from score import expected_fidelity
        for name in ("ibm_falcon_27","quantinuum_h2_56"):
            source=QuantumCircuit(2);source.h(0);source.cx(0,1);source.measure_all()
            target=get_device(name)
            circuit=transpile(source,target=target,seed_transpiler=0,num_processes=1)
            self.assertEqual(expected_fidelity(circuit,target)["score"],original(circuit,target))

class TestTrainer(unittest.TestCase):
    def setUp(self):
        import os
        from collections import deque
        path=ROOT/"addestramento/mqt/motore_ml.py"
        tree=ast.parse(path.read_text())
        names={"append_manifest","repair_tail","load_manifest","record_matches_run_configuration"}
        tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        self.ns={"Path":Path,"Any":object,"json":json,"os":os,"NON_ATTEMPT_STATUSES":set(),
                 "ACTIVE_TIMEOUT":100,"package_version":lambda _: "2.4.0"}
        exec(compile(tree,str(path),"exec"),self.ns)

    def test_partial_tail_kept_and_next_record_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"manifest.jsonl"
            path.write_bytes(b'{"key":"old","attempt":1,"status":"success"}\n{"key":')
            self.ns["append_manifest"](path,{"key":"new","attempt":1,"status":"success"})
            attempts,statuses=self.ns["load_manifest"](path)
            self.assertEqual(statuses,{"old":"success","new":"success"})
            self.assertTrue(list(Path(temp).glob("*.partial-*")))

    def test_internal_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"manifest.jsonl"
            path.write_text('bad\n{"key":"x"}\n')
            with self.assertRaises(ValueError):self.ns["append_manifest"](path,{"key":"new"})

    def test_timeout_part_of_identity(self):
        record={"mqt_predictor_version":"2.4.0","rl_max_steps":64,"seed":0,
                "model_sha256":"m","target_sha256":"t","timeout_seconds":300}
        kwargs={"rl_max_steps":64,"seed":0,"model_sha256":"m","target_sha256":"t"}
        self.assertFalse(self.ns["record_matches_run_configuration"](record,**kwargs))
        record["timeout_seconds"]=100
        self.assertTrue(self.ns["record_matches_run_configuration"](record,**kwargs))

if __name__=="__main__":unittest.main()

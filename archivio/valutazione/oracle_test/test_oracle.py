'Checks with synthetic data; no quantum-circuit compilation.'
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
import copy
import os
import tempfile
import time
import unittest
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import oracle_core as c
import genera_oracle_test as app
import oracle_worker as worker

def identity():
    return {"circuits":[{"circuit_id":"synthetic","source_sha256":"source","num_qubits":2,"split":"test"}],
            "devices":{"d":{"num_qubits":10,"sha256":"target"},"too_small":{"num_qubits":1,"sha256":"target"}},
            "configurations":[{"config_id":"cfg","optimization_level":2,"layout_method":None,"routing_method":None}],
            "catalog":{"fixed_transpile_options":{"approximation_degree":1.0,"num_processes":1}},
            "seeds":[0,1,2],"timeout_seconds":100,"workers":2,"startup_watchdog_seconds":60}

def success(j,value):
    return {**c.terminal(j,"success",None),"score":value,"validation":{"is_executable_on_target":True},
            "timings":{"total":.1},"compiled_sha256":c.hashlib.sha256(b"mock-compiled").hexdigest()}

class OracleTests(unittest.TestCase):
    def test_max_not_median_and_ties(self):
        ident=identity();records={}
        for j in c.jobs(ident):
            records[j["job_id"]]=success(j,[.1,.9,.3][j["seed"]]) if j["compatible"] else c.terminal(j,"incompatible","capacity")
        pairs,refs=c.aggregate_rows(ident,records)
        self.assertEqual(refs[0]["reference_score"],.9)
        self.assertEqual(refs[0]["best_seed0_score"],.1)
        self.assertTrue(refs[0]["reference_is_exhaustive"])
        self.assertEqual(refs[0]["best_pairs"][0]["best_seeds"],[1])
        for j in c.jobs(ident):
            if j["compatible"] and j["seed"]==2:records[j["job_id"]]=success(j,.9)
        self.assertEqual(c.aggregate_rows(ident,records)[1][0]["best_pairs"][0]["best_seeds"],[1,2])

    def test_partial_seed_does_not_discard_good_scores(self):
        ident=identity();js=list(c.jobs(ident))
        records={js[0]["job_id"]:success(js[0],.8),js[1]["job_id"]:c.terminal(js[1],"timeout","deadline")}
        _,refs=c.aggregate_rows(ident,records)
        self.assertEqual(refs[0]["reference_score"],.8)
        self.assertFalse(refs[0]["reference_is_exhaustive"])
        self.assertFalse(refs[0]["all_attempts_terminal"])

    def test_no_results_null_and_zero_is_a_valid_score(self):
        ident=identity();_,refs=c.aggregate_rows(ident,{})
        self.assertIsNone(refs[0]["reference_score"])
        j=next(c.jobs(ident))
        _,refs=c.aggregate_rows(ident,{j["job_id"]:success(j,0)})
        self.assertEqual(refs[0]["reference_score"],0)

    def test_global_max_across_pairs(self):
        ident=identity();ident["configurations"].append({**ident["configurations"][0],"config_id":"cfg2"})
        records={}
        for j in c.jobs(ident):
            if j["compatible"]:records[j["job_id"]]=success(j,.95 if j["config_id"]=="cfg2" else .8)
        ref=c.aggregate_rows(ident,records)[1][0]
        self.assertEqual(ref["reference_score"],.95)
        self.assertEqual(ref["best_pairs"][0]["config_id"],"cfg2")

    def test_bad_result_rejected(self):
        j=next(c.jobs(identity()))
        for value in [float("nan"),float("inf"),-.1,1.1,True]:
            with self.assertRaises(ValueError):c.validate_result(j,success(j,value))
        r=success(j,.8);r["seed"]=7
        with self.assertRaises(ValueError):c.validate_result(j,r)
        r=success(j,.8);r["timings"]["total"]=100.01
        with self.assertRaises(ValueError):c.validate_result(j,r)

    def test_output_inside_repo_or_symlink_rejected(self):
        with self.assertRaises(ValueError):c.external_path(c.REPO/"oracle-output")
        with self.assertRaises(ValueError):c.external_path(c.REPO.parent)
        with tempfile.TemporaryDirectory() as tmp:
            link=Path(tmp)/"alias";link.symlink_to(c.REPO,target_is_directory=True)
            with self.assertRaises(ValueError):c.external_path(link/"hidden")

    def test_atomic_publication_never_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.json";c.publish(p,{"x":1})
            with self.assertRaises(FileExistsError):c.publish(p,{"x":2})
            self.assertEqual(c.read(p),{"x":1})

    def test_resume_interruption_is_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);j=next(c.jobs(identity()))
            c.publish(folder/"inizio.json",{"job":j})
            r=c.resolve_existing(folder,j)
            self.assertEqual(r["status"],"interrupted")
            self.assertEqual(c.resolve_existing(folder,j),r)

    def test_resume_recovers_completed_result_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);j=next(c.jobs(identity()))
            c.publish(folder/"inizio.json",{"job":j})
            c.publish_bytes(folder/"compiled.qasm",b"mock-compiled")
            c.publish(folder/"worker_result.json",success(j,.75))
            self.assertEqual(c.resolve_existing(folder,j)["score"],.75)
            (folder/"compiled.qasm").write_text("altered")
            with self.assertRaises(ValueError):c.resolve_existing(folder,j)

    def test_contract_change_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);ident=identity();ident["circuits"]=[];ident["code_sha256"]={}
            c.prepare(out,ident)
            ident["workers"]=1
            with self.assertRaises(ValueError):c.prepare(out,ident)

    def test_supervisor_mock_and_resume_no_repeated_attempts(self):
        calls=[]
        class Process:
            def __init__(self,args,**kwargs):
                self.pid=200000+len(calls);self.returncode=0
                folder=Path(args[-1]);j=c.read(folder/"inizio.json")["job"];calls.append(j)
                c.publish_bytes(folder/"compiled.qasm",b"mock-compiled")
                c.publish(folder/"worker_result.json",success(j,.1+j["seed"]*.2))
                assert kwargs["env"]["OMP_NUM_THREADS"]=="1"
            def poll(self):return 0
            def wait(self):return 0
        with tempfile.TemporaryDirectory() as tmp,patch.object(app.subprocess,"Popen",Process),patch.object(app,"kill",lambda p:p.wait()):
            out=Path(tmp);ident=identity()
            app.run(out,ident);app.run(out,ident)
            self.assertEqual([j["seed"] for j in calls],[0,1,2])
            dest,summary=c.analyze(out,ident)
            self.assertEqual(summary["statuses"],{"success":3,"incompatible":3})
            self.assertTrue(summary["complete"])
            self.assertEqual(c.read(dest/"oracle_test.json")[0]["reference_score"],.5)

    def test_hard_watchdog_timeout_preserves_late_file(self):
        class Process:
            def __init__(self,args,**kwargs):
                self.pid=id(self);self.returncode=None
                folder=Path(args[-1]);j=c.read(folder/"inizio.json")["job"]
                c.publish(folder/"ready.json",{"started_monotonic":time.monotonic()-102})
                c.publish_bytes(folder/"compiled.qasm",b"mock-compiled")
                c.publish(folder/"worker_result.json",success(j,.99))
            def poll(self):return self.returncode
            def wait(self):self.returncode=-9;return -9
        with tempfile.TemporaryDirectory() as tmp,patch.object(app.subprocess,"Popen",Process),patch.object(app,"kill",lambda p:p.wait()):
            out=Path(tmp);app.run(out,identity())
            results=[c.read(p) for p in (out/"tentativi").glob("*/esito.json")]
            timed=[r for r in results if r["status"]=="timeout"]
            self.assertEqual(len(timed),3)
            self.assertTrue(all(r["score"] is None and r["worker_result_preserved"] for r in timed))


    def test_real_process_watchdog_without_quantum_compilation(self):
        stub = """import json,pathlib,sys,time
folder=pathlib.Path(sys.argv[1])
tmp=folder/'ready.tmp'
tmp.write_text(json.dumps({'started_monotonic':time.monotonic()}))
tmp.rename(folder/'ready.json')
time.sleep(20)
"""
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"run";out.mkdir()
            helper=Path(tmp)/"helper";helper.mkdir()
            (helper/"oracle_worker.py").write_text(stub)
            ident=identity();ident["seeds"]=[0];ident["workers"]=1;ident["timeout_seconds"]=.05
            with patch.object(app,"HERE",helper):
                app.run(out,ident)
            results=[c.read(p) for p in (out/"tentativi").glob("*/esito.json")]
            self.assertEqual(sorted(r["status"] for r in results),["incompatible","timeout"])
            self.assertTrue(all(r["score"] is None for r in results))

    def test_worker_passes_each_seed_and_fixed_options_without_compiling(self):
        from qiskit import QuantumCircuit
        payload={"synthetic_target":True}
        fake=SimpleNamespace(num_qubits=2,data=[],depth=lambda:0,size=lambda:0,count_ops=lambda:{})
        ident=identity();ident["devices"]={"d":{"num_qubits":10,"sha256":c.digest(payload)}}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);source=out/"sorgenti/synthetic.qasm"
            c.publish_bytes(source,b"synthetic-source-for-mocked-parser")
            ident["circuits"][0]["source_sha256"]=c.sha(source)
            for j in c.jobs(ident):
                folder=out/"tentativi"/j["job_id"]
                c.publish(folder/"inizio.json",{"job":j,"supervisor_pid":os.getppid()})
                with patch.object(worker.ctypes,"CDLL",return_value=SimpleNamespace(prctl=lambda *_:0)),\
                     patch.object(QuantumCircuit,"from_qasm_file",return_value=fake),\
                     patch("qiskit.transpile",return_value=fake) as transpile,\
                     patch("mqt.bench.targets.get_device",return_value=fake),\
                     patch("scripts.mqt_predictor_protocol.target_payload",return_value=payload),\
                     patch("prototype.quantum_assistant.adapters.compilation._validate_compiled_circuit",return_value={"is_executable_on_target":True}),\
                     patch("score.expected_fidelity",return_value={"score":.8}),\
                     patch("qiskit.qasm2.dumps",return_value="mock-compiled"):
                    self.assertEqual(worker.main(folder),0)
                    opts=transpile.call_args.kwargs
                    self.assertEqual(opts["seed_transpiler"],j["seed"])
                    self.assertEqual(opts["num_processes"],1)
                    self.assertEqual(opts["approximation_degree"],1)
                    self.assertNotIn("layout_method",opts)
                    self.assertEqual(c.read(folder/"worker_result.json")["score"],.8)

if __name__=="__main__":
    unittest.main(verbosity=2)

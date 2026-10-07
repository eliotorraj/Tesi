'Synthetic checks of records and comparisons; never run inference on the 50 circuits.'
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
AREA=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(AREA),str(AREA/"strumenti")]
import analizza,common,gates,runner

class Checks(unittest.TestCase):
    def test_manifest_and_counts(self):
        self.assertEqual(gates.corpus()["counts"],{"small":30,"medium":15,"large":5})
        rows=common.read(common.SOURCE)["circuits"]
        self.assertEqual(len(list((AREA/"circuiti").rglob("*.qasm"))),50)
        self.assertTrue(all(common.source_path(r).is_relative_to(AREA/"circuiti") for r in rows))

    def test_record_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"record.json"
            common.save(p,{"status":"failure"})
            with self.assertRaises(FileExistsError): common.save(p,{"status":"success"})
            self.assertEqual(common.read(p),{"status":"failure"})

    def test_pairing_and_missing_are_not_zero(self):
        rows=[{"circuit_id":str(i),"size_group":"small"} for i in range(3)]
        values={("llm_rag","0"):{"status":"success","score":.8},
            ("mqt_predictor","0"):{"status":"success","score":.5},
            ("llm_rag","1"):{"status":"timeout","score":None},
            ("mqt_predictor","1"):{"status":"success","score":.2}}
        result=analizza.summarize(rows,values,draws=100)["all"]
        self.assertEqual(result["paired"]["n"],1)
        self.assertAlmostEqual(result["paired"]["mean_difference_llm_minus_mqt"],.3)
        self.assertIsNone(result["paired"]["bootstrap_95_percent"])
        self.assertEqual(result["methods"]["llm_rag"]["statuses"],{"success":1,"timeout":1,"missing":1})

    def test_no_external_path(self):
        with self.assertRaises(ValueError): common.contained(AREA,"../../outside.qasm")

    def test_worker_timeout_preserves_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"strumenti").mkdir()
            (root/"strumenti/worker.py").write_text("import time\ntime.sleep(10)\n")
            with patch.object(runner,"AREA",root):
                result=runner.compile_job(root/"job",{"method":"synthetic"},.05)
            self.assertEqual(result["status"],"timeout")
            self.assertTrue((root/"job/job.json").is_file())
            with self.assertRaises(FileExistsError):
                runner.compile_job(root/"job",{"method":"synthetic"},.05)

    def test_qiskit_worker_on_synthetic_bell(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"bell.qasm"
            source.write_text('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;')
            result=runner.compile_job(root/"job",{"method":"llm_rag","source":str(source),
                "decision":{"selected_device":"ibm_falcon_27","config_id":"o2_default_default"}},60)
            self.assertEqual(result["status"],"success",result)
            self.assertTrue(0<=result["score"]<=1)
            self.assertTrue(result["validation"]["is_executable_on_target"])
            self.assertTrue((root/"job/compiled.qasm").is_file())

    def test_interrupted_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            row={"circuit_id":"synthetic","source_sha256":"x"}
            runner.interrupted_result(row,Path(tmp),"mqt_predictor")
            record=common.read(Path(tmp)/"esito.json")
            self.assertEqual(record["status"],"interrupted")
            self.assertEqual(record["split"],"external_test")
            self.assertIsNone(record["score"])

    def test_report_generation_with_synthetic_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            area=Path(tmp)
            rows=[{"circuit_id":str(i),"source_sha256":str(i),"size_group":"small" if i<30 else "medium" if i<45 else "large","qubits":2} for i in range(50)]
            common.save(area/"manifest.json",{"circuits":rows})
            common.save(area/"piano.json",{"analysis":{"bootstrap_draws":100,"bootstrap_seed":7}})
            common.save(area/"preparazione/contratto_congelato.json",{"source_sha256":common.sha(area/"manifest.json"),"plan":common.read(area/"piano.json")})
            contract=common.sha(area/"preparazione/contratto_congelato.json")
            for method in common.METHODS:
                common.save(area/"risultati"/method/"esecuzione.json",{"contract_sha256":contract,"method":method,"kind":"external_test","expected_circuits":50})
                common.save(area/"risultati"/method/"circuiti/0/esito.json",{"circuit_id":"0","source_sha256":"0","method":method,"split":"external_test","status":"success","score":.5})
            with patch.object(analizza,"AREA",area),patch.object(analizza,"SOURCE",area/"manifest.json"),patch.object(analizza,"PLAN",area/"piano.json"):
                self.assertEqual(analizza.main(),0)
            generated=list((area/"report/generati").iterdir())
            self.assertEqual(len(generated),1)
            report=common.read(generated[0]/"riepilogo.json")
            self.assertFalse(report["complete"])
            self.assertEqual(report["summary"]["all"]["paired"]["n"],1)
            self.assertEqual(len((generated[0]/"circuiti.csv").read_text().splitlines()),101)

    def test_report_rejects_foreign_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            area=Path(tmp)
            manifest={"circuits":[{"circuit_id":"x","source_sha256":"expected","size_group":"small"}]}
            common.save(area/"manifest.json",manifest)
            common.save(area/"preparazione/contratto_congelato.json",{"source_sha256":common.sha(area/"manifest.json")})
            contract=common.sha(area/"preparazione/contratto_congelato.json")
            common.save(area/"risultati/llm_rag/esecuzione.json",{"contract_sha256":contract,"method":"llm_rag","kind":"external_test","expected_circuits":50})
            common.save(area/"risultati/llm_rag/circuiti/x/esito.json",{"circuit_id":"x","source_sha256":"foreign","method":"llm_rag","split":"external_test","status":"success","score":1})
            with patch.object(analizza,"AREA",area),patch.object(analizza,"SOURCE",area/"manifest.json"):
                with self.assertRaises(ValueError): analizza.collect()

if __name__=="__main__": unittest.main(verbosity=2)

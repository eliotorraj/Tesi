"""Controlli del report su dati inventati; nessuna chiamata ai modelli."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dati import aggregate, sha, write_json, load_run
from genera_recupero_random import load_random, validate_summary, METHOD, KIND


class RandomReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root/METHOD
        self.path = self.base/"analisi/report.json"
        self.source = self.root/"manifest.json"
        plan = {"circuits":1}
        write_json(self.root/"piano.json",plan)
        write_json(self.source,{"circuits":[{"circuit_id":"a","source_sha256":"qasmhash","split":"test"}]})
        policy = dict(revision="random-examples-v1", k=5,sampling="uniform_without_replacement",distance="not_computed")
        contract = dict(method=METHOD,kind=KIND,retrieval=dict(policy,seed=7),
                        parent_plan_sha256=sha(self.root/"piano.json"),
                        inputs=dict(plan=plan,source_sha256=sha(self.source)))
        write_json(self.base/"contratto_congelato.json",contract)
        ch = sha(self.base/"contratto_congelato.json")
        write_json(self.base/"esecuzione.json",dict(method=METHOD,kind=KIND,seed=7,
                                                   contract_sha256=ch,expected_circuits=1))
        row = dict(circuit_id="a",source_sha256="qasmhash",method=METHOD,split="test",status="success",
                   score=0.7,retries=2,total_seconds=3,compilation_seconds=1,
                   compilation_process_seconds=1.1,choice_seconds=1.9,llm_response_seconds=1.5,total_tokens=100)
        write_json(self.base/"circuiti/a/esito.json",row)
        encoded = json.dumps(dict(seed=7,source_sha256="qasmhash"),sort_keys=True,separators=(",",":")).encode()
        self.retrieval = dict(policy=policy,seed=7,derived_seed=int(hashlib.sha256(encoded).hexdigest(),16),
            source_sha256="qasmhash",candidate_count=5,
            records=[dict(example_id=f"E{i}",rag_id=f"r{i}",distance=None,record_sha256=f"h{i}") for i in range(1,6)])
        write_json(self.base/"circuiti/a/retrieval.json",self.retrieval)
        _, s = aggregate([row],["a"],METHOD)
        saved = {k:s[k] for k in ("expected_circuits","completed_circuits","successes","failures","pending")}
        saved.update(method=METHOD,kind=KIND,seed=7,contract_sha256=ch,retries=2,score_denominator=1,
                     mean_score=0.7,secondary=dict(median_score=0.7,failure_causes={}),
                     sources={"circuiti/a/esito.json":sha(self.base/"circuiti/a/esito.json")})
        for key in ("total_seconds","compilation_seconds","compilation_process_seconds",
                    "choice_seconds","llm_response_seconds","total_tokens"):
            m=s["metrics"][key]
            saved[key]=dict(sum_known=m["sum_known"],mean_known=m["mean"],measured_circuits=1,missing_circuits=0)
        self.saved=saved
        write_json(self.path,saved)

    def load(self):
        with patch("genera_recupero_random.AREA",self.root), patch("genera_recupero_random.SOURCE",self.source), patch("genera_recupero_random.REPO",self.root):
            return load_random(self.path)

    def test_valid_extension_and_original_loader_remains_strict(self):
        run,_=self.load()
        self.assertEqual(run["summary"]["successes"],1)
        with self.assertRaisesRegex(ValueError,"Identità"):
            load_run(self.base,{"a":"qasmhash"},sha(self.base/"contratto_congelato.json"),None)

    def test_rejects_changed_outcome(self):
        p=self.base/"circuiti/a/esito.json"
        p.write_text(p.read_text().replace("0.7","0.6"))
        with self.assertRaisesRegex(ValueError,"impronte"):
            self.load()

    def test_rejects_incorrect_summary(self):
        self.saved["mean_score"]=0.9
        write_json(self.path,self.saved)
        with self.assertRaisesRegex(ValueError,"mean_score"):
            self.load()

    def test_rejects_wrong_seed_and_repeated_example(self):
        for change in ("seed","duplicate"):
            with self.subTest(change=change):
                retrieval=copy.deepcopy(self.retrieval)
                if change=="seed":
                    retrieval["seed"]=8
                else:
                    retrieval["records"][1]["rag_id"]="r1"
                write_json(self.base/"circuiti/a/retrieval.json",retrieval)
                with self.assertRaises(ValueError):
                    self.load()


if __name__=="__main__":
    unittest.main()

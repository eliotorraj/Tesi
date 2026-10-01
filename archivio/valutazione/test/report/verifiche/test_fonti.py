"""Verifica il cambio di origine MQT senza eseguire modelli o compilazioni."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dati import read, sha, write_json, compare, run_label
from fonti import load_sources, validate_exploratory_contract


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.area = self.root/'test'
        self.external = self.root/'test_mqt_esplorativo'
        self.plan = {'test_id':'test-indipendenti-v1','circuits':1,'split':'test','compilation_timeout_seconds':100,'scoring':'expected_fidelity'}
        self.original = {'plan':self.plan,'source_sha256':'manifest','selection':{'winner':'qwen'},'rag_seal_sha256':'rag','code':{'worker.py':'original'}}
        self.expected = {'a':'a-hash'}
        self.make_run(self.area,self.original,0.2)
        exploratory = copy.deepcopy(self.original)
        exploratory['plan'].update(test_id='mqt-esplorativo-384-v1',exploratory={'training_samples':384})
        exploratory['code']={'worker.py':'exploratory'}
        self.make_run(self.external,exploratory,0.7)

    def tearDown(self):
        self.tmp.cleanup()

    def make_run(self, area, contract, score):
        write_json(area/'piano.json',contract['plan'])
        write_json(area/'preparazione/contratto_congelato.json',contract)
        base=area/'risultati/mqt_predictor'
        write_json(base/'esecuzione.json',{'method':'mqt_predictor','kind':'test','expected_circuits':1,
            'contract_sha256':sha(area/'preparazione/contratto_congelato.json'),'plan_sha256':sha(area/'piano.json')})
        write_json(base/'circuiti/a/esito.json',{'method':'mqt_predictor','circuit_id':'a','source_sha256':'a-hash','split':'test','status':'success','score':score})

    def test_separate_mqt_selected_once_with_own_contract(self):
        before={str(p):sha(p) for p in self.root.rglob('*.json')}
        runs=load_sources(self.area,self.expected,self.original)
        run=runs['mqt_predictor']
        self.assertEqual(run['summary']['episodes'],1)
        self.assertEqual(run['summary']['metrics']['score']['mean'],0.7)
        self.assertTrue(run['source']['exploratory'])
        self.assertIn('(espl.)',run_label('mqt_predictor',run))
        self.assertEqual(run['source']['base'],str(self.external/'risultati/mqt_predictor'))
        self.assertEqual(before,{str(p):sha(p) for p in self.root.rglob('*.json')})
        self.assertEqual(compare(runs,{'bootstrap_seed':1,'bootstrap_draws':10,'confidence':0.95})['exploratory_methods'],['mqt_predictor'])

    def test_original_supported_when_no_external_result(self):
        (self.external/'risultati/mqt_predictor/esecuzione.json').unlink()
        run=load_sources(self.area,self.expected,self.original)['mqt_predictor']
        self.assertFalse(run['source']['exploratory'])
        self.assertEqual(run['rows'][0]['score'],0.2)

    def test_explicit_alternative_location(self):
        moved=self.root/'other_mqt';self.external.rename(moved)
        run=load_sources(self.area,self.expected,self.original,mqt_area=moved)['mqt_predictor']
        self.assertEqual(run['source']['area'],str(moved))

    def test_explicit_missing_location_fails_without_fallback(self):
        with self.assertRaises(ValueError):
            load_sources(self.area,self.expected,self.original,mqt_area=self.root/'absent')

    def test_different_evaluation_criteria_are_rejected(self):
        external=read(self.external/'preparazione/contratto_congelato.json')
        for key,value in [('compilation_timeout_seconds',300),('split','validation'),('scoring','other')]:
            altered=copy.deepcopy(external);altered['plan'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_exploratory_contract(self.original,altered,altered['plan'])
        altered=copy.deepcopy(external);altered['source_sha256']='other'
        with self.assertRaises(ValueError):
            validate_exploratory_contract(self.original,altered,altered['plan'])

    def test_unfrozen_plan_or_undeclared_exploration_rejected(self):
        external=read(self.external/'preparazione/contratto_congelato.json')
        changed=copy.deepcopy(external['plan']);changed['exploratory']['training_samples']=395
        with self.assertRaises(ValueError):validate_exploratory_contract(self.original,external,changed)
        del external['plan']['exploratory']
        with self.assertRaises(ValueError):validate_exploratory_contract(self.original,external,external['plan'])

    def test_result_contract_still_verified(self):
        path=self.external/'risultati/mqt_predictor/esecuzione.json'
        meta=read(path);meta['contract_sha256']='wrong';write_json(path,meta)
        with self.assertRaises(ValueError):load_sources(self.area,self.expected,self.original)


if __name__=='__main__':unittest.main()

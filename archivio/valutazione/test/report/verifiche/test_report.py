'Regression checks using synthetic data. Do not run the Test or quantum compilers.'
import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dati import aggregate, paired, compare, load_run, write_json, number
from impaginazione import esc

PLAN={'bootstrap_seed':20260901,'bootstrap_draws':10000,'confidence':0.95}


def episode(cid,score=0.8,**extra):
    return dict(circuit_id=cid,source_sha256=cid+'-hash',method='llm_rag',split='test',
                status='success',score=score,total_seconds=10,compilation_seconds=2,
                llm_response_seconds=6,total_tokens=100,retries=0,**extra)


class AggregationTests(unittest.TestCase):
    def test_equal_weight_for_circuits_not_episodes(self):
        rows=[episode('a',0.2),episode('a',0.4),episode('b',0.9)]
        circuits,s=aggregate(rows,['a','b'],'llm_rag')
        self.assertAlmostEqual(circuits[0]['score'],0.3)
        self.assertAlmostEqual(s['metrics']['score']['mean'],0.6)
        self.assertEqual(s['metrics']['total_tokens']['sum_known'],300)
        self.assertEqual(s['episodes'],3)
        self.assertEqual(s['completed_circuits'],2)

    def test_timeout_is_failure_and_not_zero_score_or_internal_time(self):
        failed=episode('b');failed.update(status='timeout',score=None,compilation_seconds=None,total_seconds=100)
        circuits,s=aggregate([episode('a'),failed],['a','b','c'],'llm_rag')
        self.assertEqual((s['successes'],s['failures'],s['pending']),(1,1,1))
        self.assertEqual(s['metrics']['score']['mean'],0.8)
        self.assertEqual(s['metrics']['total_seconds']['mean'],55)
        self.assertEqual(s['metrics']['compilation_seconds']['missing_episodes'],1)
        self.assertIsNone(circuits[1]['compilation_seconds'])
        self.assertEqual(circuits[2]['status'],'pending')

    def test_mixed_replicates_keep_failures_and_partial_coverage(self):
        bad=episode('a');bad.update(status='failure',score=None,total_tokens=None,known_input_tokens=11,known_output_tokens=0)
        cs,s=aggregate([episode('a'),bad],['a'],'llm_rag')
        self.assertEqual(cs[0]['status'],'mixed')
        self.assertEqual(cs[0]['score'],0.8)
        self.assertEqual(cs[0]['total_tokens_n'],1)
        self.assertEqual(cs[0]['total_tokens_missing'],1)
        self.assertEqual(s['metrics']['total_tokens']['partially_measured_circuits'],1)
        self.assertEqual(s['known_input_tokens']['sum_known'],11)

    def test_non_llm_does_not_get_fake_zero_token_or_retry_metrics(self):
        _,s=aggregate([episode('a')],['a'],'random')
        self.assertNotIn('total_tokens',s['metrics'])
        self.assertNotIn('retries',s['metrics'])

    def test_zero_score_and_zero_retry_are_real_measurements(self):
        _,s=aggregate([episode('a',0)],['a'],'llm_rag')
        self.assertEqual(s['metrics']['score']['n'],1)
        self.assertEqual(s['metrics']['retries']['mean'],0)
        self.assertFalse(number(float('nan')))
        self.assertFalse(number(True))

    def test_interrupted_is_terminal_failure(self):
        row=episode('a');row.update(status='interrupted',score=None,total_seconds=None)
        _,s=aggregate([row],['a'],'llm_rag')
        self.assertEqual(s['failures'],1)
        self.assertIsNone(s['metrics']['total_seconds']['sum_known'])

    def test_paired_interval_preserves_identity_and_excludes_failure(self):
        left=[{'circuit_id':'a','score':0.7},{'circuit_id':'b','score':0.3},{'circuit_id':'c','score':0.5}]
        right=[{'circuit_id':'b','score':0.1},{'circuit_id':'a','score':0.5},{'circuit_id':'c','score':None}]
        p=paired(left,right,PLAN)
        self.assertEqual(p['circuit_ids'],['a','b'])
        self.assertAlmostEqual(p['mean_difference'],0.2)
        for bound in p['paired_bootstrap_95']:self.assertAlmostEqual(bound,0.2)
        self.assertEqual(p,paired(left,right,PLAN))
        self.assertIsNone(paired(left,right[:1],PLAN)['paired_bootstrap_95'])

    def test_future_mqt_added_without_changing_existing_pair(self):
        def run(score):return {'rows':[{}],'circuits':[{'circuit_id':'a','score':score}]}
        runs={'llm_rag':run(0.8),'llm_senza_rag':run(0.5),'random':run(0.4)}
        old=compare(runs,PLAN)
        self.assertEqual(old['missing_methods'],['mqt_predictor'])
        runs['mqt_predictor']=run(0.7)
        new=compare(runs,PLAN)
        self.assertEqual(new['missing_methods'],[])
        self.assertEqual(old['pairs']['random'],new['pairs']['random'])
        self.assertAlmostEqual(new['pairs']['mqt_predictor']['mean_difference'],0.1)

    def test_tex_escapes_all_special_characters(self):
        self.assertEqual(esc('a_1%&'),r'a\_1\%\&')


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)/'mqt_predictor'
        write_json(self.base/'esecuzione.json',dict(method='mqt_predictor',kind='test',expected_circuits=1,contract_sha256='contract',plan_sha256='plan'))
        self.row=episode('a');self.row['method']='mqt_predictor'
        self.path=self.base/'circuiti/a/esito.json';write_json(self.path,self.row)

    def tearDown(self):self.temp.cleanup()

    def load(self):return load_run(self.base,{'a':'a-hash'},'contract','plan')

    def test_mqt_ingestion_is_read_only(self):
        before=self.path.read_bytes();run=self.load()
        self.assertEqual(run['summary']['successes'],1)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertNotIn('total_tokens',run['summary']['metrics'])

    def test_different_contract_rejected(self):
        with self.assertRaises(ValueError):load_run(self.base,{'a':'a-hash'},'other','plan')

    def test_wrong_split_hash_invalid_score_and_measurement_rejected(self):
        for change in ({'split':'validation'},{'source_sha256':'wrong'},{'score':None},{'total_seconds':-1},{'score':1.1}):
            write_json(self.path,dict(self.row,**change))
            with self.assertRaises(ValueError):self.load()

    def test_replicates_allowed_but_nested_summary_rejected(self):
        second=self.base/'circuiti/a/episodi/e2/esito.json';write_json(second,self.row)
        with self.assertRaises(ValueError):self.load()
        self.path.unlink();write_json(self.base/'circuiti/a/episodi/e1/esito.json',self.row)
        run=self.load()
        self.assertEqual(run['summary']['episodes'],2)
        self.assertEqual(run['summary']['completed_circuits'],1)


if __name__=='__main__':unittest.main()

"""Prove del confronto con score fittizi: mai avviare il compilatore."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import archivio.valutazione.oracle_qasmbench.oracle_core as c
import archivio.valutazione.oracle_qasmbench.analizza as a
import archivio.valutazione.oracle_qasmbench.impagina as report
from archivio.valutazione.oracle_qasmbench.test_oracle import identity,success


def fixture_rows():
    ident=identity();ident['circuits'][0]['size_group']='small'
    records={}
    for j in c.jobs(ident):
        records[j['job_id']]=success(j,[.8,.9,.85][j['seed']]) if j['compatible'] else c.terminal(j,'incompatible','capacity')
    pairs,refs=c.aggregate_rows(ident,records)
    rag={'synthetic':{'status':'success','score':.95,'device':'d','config_id':'cfg'}}
    return ident,pairs,refs,rag


def preview_data():
    ident,pairs,refs,rag=fixture_rows();base=a.build_rows(ident,refs,pairs,rag)[0]
    rows=[]
    for i in range(50):
        row=copy.deepcopy(base);row.update(id=i+1,circuit_id=f'qasmbench_synthetic_validation_circuit_n{i+1}',num_qubits=i+2,
            system_score=.30+i*.01,oracle_score=.34+i*.01,gap=.04,choice_gap=.03,within_pair_gap=.01,
            size_group='small' if i<30 else ('medium' if i<45 else 'large'),exhaustive=i%3==0)
        if i==0:row.update(gap=-.025,system_score=.7,oracle_score=.675,status='sopra')
        elif i==1:row.update(gap=None,oracle_score=None,choice_gap=None,within_pair_gap=None,status='non confrontabile')
        else:row['status']='sotto'
        rows.append(row)
    s=a.summarize(rows)
    return {'rows':rows,'summary':s,'oracle_summary':{'statuses':{'success':7500,'timeout':1000,'failure':104,'incompatible':396},
        'plan':{'matrix_cells':9000,'incompatible_cells':396,'compilations':8604},'complete':True,'pending':0,
        'circuits_with_reference':49,'terminal':9000},'system_started_at':'COLLAUDO CON DATI FITTIZI','oracle_versions':{'qiskit':'2.5.0','mqt.predictor':'2.4.0'},
        'python':'3.12.13','oracle_path':'/DATI_FITTIZI/oracle','rag_path':'/DATI_FITTIZI/rag','synthetic':True}


class ComparisonTests(unittest.TestCase):
    def test_signed_gap_and_decomposition(self):
        ident,pairs,refs,rag=fixture_rows();r=a.build_rows(ident,refs,pairs,rag)[0]
        self.assertEqual(r['gap'],-.05);self.assertEqual(r['status'],'sopra')
        self.assertAlmostEqual(r['gap'],r['choice_gap']+r['within_pair_gap'])
        self.assertEqual(r['seed0_repeat_difference'],-.15)

    def test_missing_reference_stays_missing(self):
        ident,pairs,refs,rag=fixture_rows();pairs,refs=c.aggregate_rows(ident,{})
        row=a.build_rows(ident,refs,pairs,rag)[0];s=a.summarize([row])
        self.assertIsNone(row['gap']);self.assertEqual(s['compared'],0)
        self.assertIsNone(s['mean_gap']);self.assertEqual(s['complete']['n'],0)
        self.assertEqual(s['decomposition_n'],0)

    def test_failed_system_is_not_zero(self):
        ident,pairs,refs,rag=fixture_rows();rag['synthetic'].update(status='timeout',score=None)
        row=a.build_rows(ident,refs,pairs,rag)[0]
        self.assertIsNone(row['gap']);self.assertEqual(a.summarize([row])['compared'],0)

    def test_zero_reference_no_relative_division(self):
        ident,pairs,refs,rag=fixture_rows()
        records={j['job_id']:success(j,0) for j in c.jobs(ident) if j['compatible']}
        pairs,refs=c.aggregate_rows(ident,records);rag['synthetic']['score']=0
        row=a.build_rows(ident,refs,pairs,rag)[0]
        self.assertEqual(row['gap'],0);self.assertIsNone(row['relative_gap_percent'])
        self.assertEqual(a.summarize([row])['partial']['n'],0)

    def test_original_result_tamper_and_aggregate_tamper(self):
        # 50 sorgenti sintetiche, due dispositivi e una configurazione per velocità.
        ident=identity();ident.update(schema='qasmbench50-oracle-max3-v1',source_manifest_sha256=c.SOURCE_SHA)
        source=b'synthetic qasm placeholder, not parsed';h=c.hashlib.sha256(source).hexdigest()
        ident['circuits']=[dict(circuit_id=f'synthetic_{i}',source_sha256=h,num_qubits=2,size_group='small') for i in range(50)]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            c.publish(root/'contratto.json',{'identity':ident,'identity_sha256':c.digest(ident),'plan':c.plan_counts(ident)})
            for row in ident['circuits']:c.publish_bytes(root/'sorgenti'/(row['circuit_id']+'.qasm'),source)
            first=next(c.jobs(ident));folder=root/'tentativi'/first['job_id']
            c.publish_bytes(folder/'compiled.qasm',b'mock-compiled');c.publish(folder/'esito.json',success(first,.75))
            directory,_=c.analyze(root,ident)
            self.assertEqual(a.audit_oracle(directory)[-1],1)
            (folder/'esito.json').write_text('{}')
            with self.assertRaises(ValueError):a.audit_oracle(directory)
            (folder/'esito.json').write_text(json.dumps(success(first,.75),ensure_ascii=False,indent=2)+'\n')
            refs=c.read(directory/'oracle_test.json');refs[0]['reference_score']=.99
            (directory/'oracle_test.json').write_text(json.dumps(refs))
            with self.assertRaises(ValueError):a.audit_oracle(directory)

    def test_layout_fifty_rows_negative_and_missing(self):
        data=preview_data()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);(directory/'dati.json').write_text(json.dumps(data))
            tex=report.render(directory).read_text()
            self.assertEqual(tex.count(r'\titolo{Score e scarto per circuito:'),2)
            self.assertEqual(tex.count(r'\titolo{Tabella completa:'),2)
            self.assertIn('DATI FITTIZI',tex)
            self.assertLess(report.gap_scale(data['rows'])[0],0)
            with self.assertRaises(ValueError):report.render(directory)

    def test_end_to_end_with_real_rag_and_only_simulated_oracle(self):
        ident=c.preflight();rag,_,_=a.audit_rag(c.REPO/'archivio/valutazione/test_qasmbench',ident)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'mock_oracle';root.mkdir()
            c.publish(root/'contratto.json',{'identity':ident,'identity_sha256':c.digest(ident),'plan':c.plan_counts(ident)})
            for row in ident['circuits']:
                c.publish_bytes(root/'sorgenti'/(row['circuit_id']+'.qasm'),c.source_path(row).read_bytes())
            # Soltanto esiti inventati: nessun worker viene avviato.
            for job in c.jobs(ident):
                value=rag[job['circuit_id']]
                if (job['device'],job['config_id'])!=(value['device'],value['config_id']):continue
                folder=root/'tentativi'/job['job_id']
                c.publish_bytes(folder/'compiled.qasm',b'mock-compiled')
                c.publish(folder/'esito.json',success(job,value['score']))
            directory,_=c.analyze(root,ident)
            output=directory/'confronto'
            data=a.compare(directory,c.REPO/'archivio/valutazione/test_qasmbench',output)
            self.assertEqual(data['summary']['compared'],50)
            self.assertEqual(data['summary']['statuses'],{'pari':50})
            self.assertEqual(data['summary']['complete']['n'],0)
            self.assertEqual(data['oracle_summary']['terminal'],150)
            data['synthetic']=True
            (output/'dati.json').write_text(json.dumps(data))
            self.assertIn('DATI FITTIZI',report.render(output).read_text())

    def test_no_compilation_entrypoint_from_readonly_actions(self):
        import archivio.valutazione.oracle_qasmbench.genera_oracle_test as cli
        with patch.object(cli,'preflight',return_value=identity()),patch.object(cli,'run') as run,patch.object(cli,'prepare') as prepare,patch.object(cli.sys,'argv',['oracle','--verifica']):
            self.assertEqual(cli.main(),0)
        run.assert_not_called();prepare.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)

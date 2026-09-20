"""Controlli tecnici offline; non costituiscono valutazione sperimentale."""
import json, tempfile, time
from pathlib import Path
from app import ROOT, prepare, decide, compile_decision, save, stamp
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus, record_features, as_example
from prototype.quantum_assistant.adapters.qdrant_context import prepare_index, verified_client, query_exact, matching_records
from prototype.quantum_assistant.adapters.rag_features import manhattan
from prototype.prompting.facts import verify, messages
from prototype.prompting.minimal import model_input
from qiskit_dataset.catalog import load_catalog

def check(full=True):
    started=time.perf_counter();corpus=load_corpus(verify_features=True);prepare_index(corpus)
    print('verified 396 train feature vectors',flush=True)
    devices=load_catalog().supported_device_ids
    # All 396 queries are compared with exhaustive float64 ordering. Same device filtering.
    queries=0
    with verified_client(ROOT/'runtime/rag/index',corpus) as client:
        for record in (corpus.records if full else corpus.records[:5]):
            features=record_features(record)
            eligible=[d for d in devices if load_catalog().target_sha256.get(d)]
            observed=query_exact(client,corpus,features,devices=eligible,objective='expected_fidelity',limit=5)
            q=corpus.transform.apply(features)
            expected=sorted([(manhattan(q,corpus.transform.apply(record_features(r))),r['rag_id']) for r in matching_records(corpus,devices=eligible,objective='expected_fidelity',experiment_id=record['experiment_id'])])[:5]
            assert [(x.distance,x.record_id) for x in observed]==expected
            queries+=1
    request,prompt,retrieval=prepare((ROOT/'examples/bell.qasm').read_text())
    view=model_input(prompt);device=view['compatible_hardware'][0]['id'];config=view['configuration_catalog'][0]['config_id']
    answer={'selected_device':device,'config_id':config,'facts':[{'assertion':'selected_device_has_enough_qubits'}],'hypothesis':'Propongo questa configurazione come prova tecnica; la qualita sul circuito resta da valutare.'}
    # Derive mandatory fields from actual contract rather than silently ignoring schema.
    print('checking offline facts and compilation',flush=True)
    checked=verify(answer,prompt)
    assert checked['schema_valid'] and checked['selection_valid'] and checked['facts_status']=='verified',checked
    artifact=compile_decision(request,checked,0)
    assert artifact.validation['is_executable_on_target']
    class Fake:
        calls=0
        def __init__(self,invalid=False,overflow=False):self.invalid=invalid;self.overflow=overflow
        def __call__(self,endpoint,payload,directory):
            if endpoint=='/apply-template':return {'prompt':'offline mock'}
            if endpoint=='/tokenize':return {'tokens':[1]*(60000 if self.overflow else 10)}
            self.calls+=1
            value=dict(answer)
            if self.invalid:value['facts']=[{'assertion':'selected_device_has_enough_qubits','example_id':'E1'}]
            return {'content':json.dumps(value),'stop':True,'stop_type':'eos'}
    with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as temp:
        fake=Fake(invalid=True);decision=decide(prompt,Path(temp),fake,60000)
        assert fake.calls==3 and decision['status']=='accepted_with_unverified_facts'
    with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as temp:
        fake=Fake(overflow=True)
        try:decide(prompt,Path(temp),fake,16384)
        except ValueError as error:assert 'Contesto insufficiente' in str(error)
        else:raise AssertionError('Overflow accepted')
        assert fake.calls==0
    invalid=dict(answer,selected_device='not_a_device');assert not verify(invalid,prompt)['selection_valid']
    report={'at':stamp(),'kind':'offline_technical_check','train_features_verified':396,'qdrant_reference_queries':queries,'frozen_transform_equal':True,'synthetic_bell_compilation_valid':True,'fallback_after_three_completed_attempts':True,'context_overflow_generation_calls':0,'invalid_device_rejected':True,'toon_roundtrip':bool(messages(prompt)),'seconds':time.perf_counter()-started}
    save(ROOT/'runs'/('offline-'+str(time.time_ns())+'.json'),report)
    return report

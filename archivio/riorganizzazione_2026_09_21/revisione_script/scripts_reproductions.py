"""Riproduzioni isolate dei rilievi sugli script: nessun modello o servizio reale."""
from __future__ import annotations
import ast, csv, json, os, queue, tempfile, time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SOURCE=ROOT/'archivio/esperimento_v2/scripts'

def extract(file,names,namespace,*,nested=False):
    tree=ast.parse((SOURCE/file).read_text())
    scope=ast.walk(tree) if nested else tree.body
    nodes=[n for n in scope if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module,str(SOURCE/file),'exec'),namespace)
    return namespace

def run():
    evidence={}
    with tempfile.TemporaryDirectory(prefix='simulazioni_script_',dir=OUT) as temporary:
        tmp=Path(temporary)
        base={'Path':Path,'json':json,'os':os,'Any':object,'NON_ATTEMPT_STATUSES':{'rl_model_load_failed','rl_model_startup_timeout','rl_runtime_unavailable'}}
        ns=extract('04_train_device_selector.py',{'append_manifest','load_manifest','latest_manifest_records'},dict(base))
        log=tmp/'partial.jsonl';log.write_text('{"key":"interrotto"')
        ns['append_manifest'](log,{'key':'nuovo|device','attempt':1,'status':'success'})
        attempts,statuses=ns['load_manifest'](log)
        evidence['S02_jsonl_partial_tail']={'raw':log.read_text(),'attempts':attempts,'statuses':statuses,'new_record_lost':not attempts}
        assert not attempts

        ns=extract('04_train_device_selector.py',{'record_matches_run_configuration'},{'package_version':lambda _: '2.4.0'})
        record={'mqt_predictor_version':'2.4.0','rl_max_steps':64,'seed':0,'model_sha256':'model','target_sha256':'target','duration_seconds':150,'timeout_seconds':300}
        accepted=ns['record_matches_run_configuration'](record,rl_max_steps=64,seed=0,model_sha256='model',target_sha256='target')
        evidence['S04_timeout_not_in_cache_key']={'recorded_timeout':300,'recorded_duration':150,'requested_timeout_in_followup':100,'provenance_accepted':accepted,'function_has_timeout_parameter':False}
        assert accepted

        # Il processo è fittizio. Termina quando il genitore legge la fase; il risultato è già nella coda.
        events=[{'type':'ready'},{'type':'started','key':'toy|device'},{'type':'phase','key':'toy|device','phase':'rl'}, {'type':'result','key':'toy|device','status':'success'}, {'type':'done'}]
        class FakeProcess:
            pid=12345
            exitcode=0
            def __init__(self,**kwargs): self.alive=True
            def start(self): pass
            def is_alive(self): return self.alive
            def join(self,**kwargs): pass
        process=FakeProcess()
        class FakeQueue:
            def get(self,**kwargs):
                item=events.pop(0)
                if item['type']=='phase':process.alive=False
                return dict(item,device='device',pid=process.pid)
            def close(self): pass
        class FakeRuntime:
            server_port=1234
            def __init__(self,**kwargs):pass
            def start(self):pass
            def stop(self):pass
            def is_alive(self):return True
        context=SimpleNamespace(Queue=lambda:FakeQueue(),Process=lambda **kwargs:process)
        ns=dict(base,deque=deque,dataclass=dataclass,time=time,queue=queue,
            get_context=lambda _:context,BQSKitRuntime=FakeRuntime,utc_now=lambda:'simulation',
            package_version=lambda _:'2.4.0',warn_about_memory=lambda _:None,
            strict_rl_success_keys=lambda *a,**kw:set(),device_worker=lambda *a:None,
            file_version=lambda _:None,output_changed=lambda *a:False,
            _terminate_worker_process=lambda p:None,WORKER_WATCHDOG_GRACE_SECONDS=30)
        ns=extract('04_train_device_selector.py',{'WorkerState','CompilationJob','append_manifest','load_manifest','latest_manifest_records','group_pending_jobs','record_matches_run_configuration','compile_resumably'},ns)
        log=tmp/'queue.jsonl';job=ns['CompilationJob'](tmp/'input.qasm',tmp/'output.qasm','toy','device',2)
        ns['compile_resumably']([job],metric='expected_fidelity',rl_max_steps=64,seed=0,model_sha256_by_device={'device':'m'},target_sha256_by_device={'device':'t'},num_workers=1,timeout=100,startup_timeout=240,fallback_timeout=60,fallback_enabled=False,fallback_optimization_level=2,max_attempts=1,manifest_path=log,log_dir=tmp,progress_every=1)
        records=[json.loads(l) for l in log.read_text().splitlines()]
        evidence['S03_pending_worker_results']={'persisted_statuses':[r['status'] for r in records],'unread_messages':events,'real_process_started':False}
        assert records[-1]['status']=='worker_crash' and any(x['type']=='result' for x in events)

        class Pipe:
            def poll(self,timeout):return True
            def recv(self):raise EOFError('simulated child exit')
            def close(self):pass
        process=FakeProcess()
        ns=extract('12_run_qcompile_v2.py',{'run_once'},{'get_context':lambda _:SimpleNamespace(Pipe=lambda **kw:(Pipe(),Pipe()),Process=lambda **kw:process),'_worker':None,'time':time,'_terminate':lambda _:None})
        try:ns['run_once']('fake-qasm',100)
        except EOFError as error:evidence['S05_qcompile_eof']={'exception':type(error).__name__,'terminal_record_returned':False,'real_process_started':False}
        else:raise AssertionError('Expected unhandled EOF')

        canary={'status':'success','results':[{'strict_success':True,'mode':'rl'} for _ in range(5)]+[{'strict_success':True,'mode':'qcompile'}],'limits':{'max_steps':64,'timeout_seconds':100},'artifacts':{'old-model':{'canonical_sha256':'outdated'}}}
        ns=extract('15_release_test_v2.py',{'check_canary'},{'load_json':lambda _:canary,'QCOMPILE_CANARY':tmp/'old_canary.json','file_sha256':lambda _:'simulated-file-hash','COMPILATION_TIMEOUT_SECONDS':100},nested=True)
        evidence['S07_stale_canary_gate']={'accepted':bool(ns['check_canary']()),'canary_model_hash':'outdated','current_model_hash_compared':False,'test_release_executed':False}
        assert evidence['S07_stale_canary_gate']['accepted']

        # La prima porzione è esattamente il controllo delle righe 456-469 del trainer.
        tree=ast.parse((SOURCE/'03_train_rl_model.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        guard=next(n for n in main.body if isinstance(n,ast.If) and n.lineno==456)
        checkpoint_dir=tmp/'checkpoints';checkpoint_dir.mkdir();model_name='toy_model'
        for suffix in ['_interrupted.zip','_interrupted.metadata.json']:(checkpoint_dir/(model_name+suffix)).write_text('old')
        exec(compile(ast.Module(body=[guard],type_ignores=[]),'trainer_guard','exec'),{'args':SimpleNamespace(run_name='existing',resume_from=None),'checkpoint_dir':checkpoint_dir,'model_name':model_name})
        monitor_path=ROOT/'.venv/lib/python3.12/site-packages/stable_baselines3/common/monitor.py'
        sb3=ast.parse(monitor_path.read_text());cls=next(n for n in sb3.body if isinstance(n,ast.ClassDef) and n.name=='ResultsWriter')
        ns={'os':os,'csv':csv,'json':json,'Monitor':SimpleNamespace(EXT='monitor.csv')}
        module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),cls],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(monitor_path),'exec'),ns)
        monitor=tmp/'monitor.csv';monitor.write_text('previous episode data\n');writer=ns['ResultsWriter'](str(monitor));writer.file_handler.close()
        evidence['S08_restart_overwrites_episode_log']={'restart_guard_accepted':True,'old_episode_data_retained':'previous episode data' in monitor.read_text(),'actual_sb3_writer_only':True,'training_executed':False}
        assert not evidence['S08_restart_overwrites_episode_log']['old_episode_data_retained']
    # Verificatori di provenienza: nessun ZIP o classificatore viene caricato.
    import runpy
    protocol=runpy.run_path(str(SOURCE/'mqt_predictor_protocol.py'))
    ns=dict(protocol,json=json,EXPECTED_RL_BQSKIT_PROFILE='ci-lightweight-dynamic-synthesis')
    ns=extract('mqt_model_artifacts.py',{'validate_rl_training_metadata','validate_ml_training_metadata'},ns)
    with tempfile.TemporaryDirectory(prefix='simulazioni_provenienza_',dir=OUT) as temporary:
        tmp=Path(temporary);device=protocol['FROZEN_DEVICES'][0]
        rl={
            'bqskit_profile':'ci-lightweight-dynamic-synthesis','checkpoint_every':protocol['RL_CHECKPOINT_EVERY'],
            'device':device,'experiment_id':protocol['EXPERIMENT_ID'],'figure_of_merit':protocol['FIGURE_OF_MERIT'],
            'model_sha256':'model-sha','mqt_predictor_version':'2.4.0','protocol':protocol['PROTOCOL_ID'],
            'protocol_version':protocol['PROTOCOL_VERSION'],'target_matches_frozen_protocol':True,
            'training_circuit_count':422,'rollout_steps':2048,'training_split':'train','target_timesteps':100000,
            'num_timesteps':protocol['RL_FINAL_TIMESTEPS'],'max_steps':64,
            'target':{'target_sha256':protocol['FROZEN_TARGET_SHA256'][device]},
            'training_manifest_sha256':'DIFFERENT-MANIFEST'}
        path=tmp/'rl.json';path.write_text(json.dumps(rl))
        _,rl_errors=ns['validate_rl_training_metadata'](path,device_name=device,model_sha256='model-sha',expected_max_steps=64,expected_num_timesteps=protocol['RL_FINAL_TIMESTEPS'])
        ml={
            'experiment_id':protocol['EXPERIMENT_ID'],'figure_of_merit':protocol['FIGURE_OF_MERIT'],
            'matches_frozen_protocol':True,'model_sha256':'ml-sha','protocol':protocol['PROTOCOL_ID'],
            'protocol_version':protocol['PROTOCOL_VERSION'],'source_circuit_count':422,'training_split':'train',
            'targets':{d:{'target_sha256':h} for d,h in protocol['FROZEN_TARGET_SHA256'].items()},
            'software':protocol['EXPECTED_PACKAGE_VERSIONS'],'source_manifest_sha256':'DIFFERENT-MANIFEST',
            'rl_models':{d:{'sha256':'DIFFERENT-RL-POLICY'} for d in protocol['FROZEN_DEVICES']}}
        path=tmp/'ml.json';path.write_text(json.dumps(ml));_,ml_errors=ns['validate_ml_training_metadata'](path,model_sha256='ml-sha')
        evidence['S10_provenance_bindings']={'rl_errors':rl_errors,'ml_errors':ml_errors,'nonmatching_manifest_accepted':not rl_errors and not ml_errors,'nonmatching_rl_policy_reference_accepted':not ml_errors,'models_loaded':False}
        assert not rl_errors and not ml_errors
    (OUT/'scripts_simulations.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__=='__main__':run()

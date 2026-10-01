"""Confronto finale in una nuova campagna; nessuna lettura dei vecchi esiti."""
from pathlib import Path
import random,time
from uuid import uuid4
import settings as s
import llm
from processi import execute
from genera import task

METHODS={'llm_rag','llm_senza_rag','random','llm_recupero_random','mqt','llm_rag_k1','llm_rag_k10','llm_wl','llm_wl_sintesi'}

def freeze():
    from seleziona import verify_selection
    selection=verify_selection()
    methods=s.CONFIG['test_methods']
    if not methods or set(methods)-METHODS or len(set(methods))!=len(methods):raise ValueError('Metodi Test non validi')
    value={"selection_sha256":s.sha(s.VALIDATION/'selezione.json'),"contract_sha256":s.sha(s.WORK/'contratto.json'),
           "methods":methods,"seed":s.CONFIG['test_seed'],"random_seed":s.CONFIG['random_seed'],
           "dataset_sha256":s.sha(s.WORK/'data/rag_examples.jsonl'),"models":None,"wl_sha256":None}
    if 'mqt' in methods:
        from gestione import assets
        value['models']=assets()
        technical=s.read(s.MQT/'prove_tecniche/superate.json')
        if technical['assets']!=value['models']:raise ValueError('Ripetere la prova tecnica con i modelli correnti')
    if set(methods)&{'llm_wl','llm_wl_sintesi'}:value['wl_sha256']=s.sha(s.VALIDATION/'wl/selezione.json')
    s.same_or_save(s.TEST/'contratto.json',value)
    return value

def check():
    s.require_prepared();c=s.read(s.TEST/'contratto.json')
    if c['selection_sha256']!=s.sha(s.VALIDATION/'selezione.json') or c['dataset_sha256']!=s.sha(s.WORK/'data/rag_examples.jsonl'):raise ValueError('Fonti Test cambiate')
    if c.get('models'):
        from gestione import assets
        if c['models']!=assets():raise ValueError('Modelli MQT diversi dal congelamento Test')
    return c

def run(method):
    import portalocker
    from qiskit_dataset.catalog import load_catalog
    manifest=s.require_prepared();c=check();catalog=load_catalog()
    if method not in c['methods']:raise ValueError('Metodo non previsto dal piano congelato')
    selection=s.read(s.VALIDATION/'selezione.json');model=selection['model'];temperature=selection['winner']['temperature']
    wl=None;k=1 if method=='llm_rag_k1' else 10 if method=='llm_rag_k10' else s.CONFIG['retrieval_k']
    if method.startswith('llm'):
        props=llm.verify_server(model)
        if method in ('llm_wl','llm_wl_sintesi'):
            from dag_wl_core import prepare_index
            from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
            if s.sha(s.VALIDATION/'wl/selezione.json')!=c['wl_sha256']:raise ValueError('Selezione WL modificata')
            corpus=load_corpus();index,index_hash=prepare_index(corpus,s.TEST/method/'indice')
            wl=(corpus,index,s.read(s.VALIDATION/'wl/selezione.json')['h'],index_hash)
    folder=s.TEST/method;folder.mkdir(parents=True,exist_ok=True)
    with portalocker.Lock(str(s.TEST/'.lock'),timeout=0):
        if method.startswith('llm'):s.save(folder/'servers'/(uuid4().hex+'.json'),props)
        for row in manifest['circuits']:
            if row['split']!='test':continue
            case=folder/'circuiti'/row['circuit_id'];out=case/'esito.json'
            if out.exists():continue
            start=time.perf_counter();decision=None
            if (case/'begin.json').exists():
                s.save(out,{"status":"interrupted","score":None,"circuit_id":row['circuit_id'],"method":method});continue
            s.save(case/'begin.json',{"circuit":row,"contract_sha256":s.sha(s.TEST/'contratto.json')})
            try:
                if method.startswith('llm'):
                    decision=llm.decision(row,case/'llm',model,temperature,method,k,wl)
                    chosen=decision.get('canonical_response')
                    if not chosen:
                        result={"status":decision['status'],"score":None,"error":decision.get('error')}
                    else:
                        t=task(row,chosen['selected_device'],catalog.by_id[chosen['config_id']],c['seed'],catalog,manifest)
                        result=execute(case/'compilazione',{'kind':'qiskit','task':t},catalog.execution_policy['timeout_seconds'])
                elif method=='random':
                    pairs=[(d,cfg) for d in catalog.supported_device_ids if row['num_qubits']<=manifest['targets'][d]['num_qubits'] for cfg in catalog.configurations]
                    if not pairs:raise ValueError('Nessuna coppia compatibile')
                    rng=random.Random(int(s.digest({'seed':c['random_seed'],'source':row['source_sha256']}),16))
                    d,cfg=rng.choice(pairs);chosen={'selected_device':d,'config_id':cfg.config_id};s.save(case/'decision.json',chosen)
                    result=execute(case/'compilazione',{'kind':'qiskit','task':task(row,d,cfg,c['seed'],catalog,manifest)},catalog.execution_policy['timeout_seconds'])
                else:
                    result=execute(case/'compilazione',{'kind':'mqt','source':str(s.WORK/row['source_ref']),'seed':c['seed']},catalog.execution_policy['timeout_seconds'])
                value={"circuit_id":row['circuit_id'],"source_sha256":row['source_sha256'],"method":method,
                       "status":result['status'],"score":result.get('score'),"compilation":result,
                       "decision":decision,"total_seconds":time.perf_counter()-start,"memory":None}
                s.save(out,value)
            except Exception as exc:
                s.save(out,{"circuit_id":row['circuit_id'],"method":method,"status":"failure","score":None,"error":type(exc).__name__,"message":str(exc),"total_seconds":time.perf_counter()-start})
            except BaseException:
                if not out.exists():s.save(out,{"circuit_id":row['circuit_id'],"method":method,"status":"interrupted","score":None})
                raise
            print(method,row['circuit_id'],s.read(out)['status'],flush=True)
    from analizza import report
    return report()

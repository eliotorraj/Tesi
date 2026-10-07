'Frozen LLM grid, validation decisions and score-separated selection.'
from pathlib import Path
from statistics import mean,median
from collections import Counter
from uuid import uuid4
import settings as s
import llm

def candidate_id(model,temperature):return model+'__t'+str(float(temperature)).replace('.','_')
def freeze():
    manifest=s.require_prepared()
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    corpus=load_corpus(verify_features=True)
    if not (s.DATASET/'aggregati.json').is_file():raise ValueError('Incomplete train/validation Dataset')
    models=llm.freeze_models()
    result={"models":models,"candidates":[{"id":candidate_id(id,t),"model":id,"temperature":t} for id,m in models.items() for t in m['temperatures']],
            "corpus_sha256":s.sha(s.WORK/'manifest.json'),"dataset_sha256":corpus.source_sha256,
            "aggregates_sha256":s.sha(s.DATASET/'aggregati.json'),"experiment_contract":s.sha(s.WORK/'contratto.json'),
            "criterion":s.CONFIG['validation_criterion'],"k":s.CONFIG['retrieval_k']}
    s.same_or_save(s.VALIDATION/'contratto.json',result)
    return {"candidates":len(result['candidates']),"circuits":manifest['counts']['validation']}

def contract():
    s.require_prepared();c=s.read(s.VALIDATION/'contratto.json')
    if c['aggregates_sha256']!=s.sha(s.DATASET/'aggregati.json') or c['dataset_sha256']!=s.sha(s.WORK/'data/rag_examples.jsonl'):raise ValueError('Validation data were modified')
    current=llm.freeze_models()
    if c['models']!=current:raise ValueError('Model registry or weights differ from frozen identities')
    return c

def run(model_id):
    import portalocker
    c=contract();manifest=s.require_prepared();model=c['models'][model_id]
    props=llm.verify_server(model)
    with portalocker.Lock(str(s.VALIDATION/'.lock'),timeout=0):
        for candidate in c['candidates']:
            if candidate['model']!=model_id:continue
            folder=s.VALIDATION/'candidati'/candidate['id']
            s.save(folder/'servers'/(uuid4().hex+'.json'),props)
            for row in manifest['circuits']:
                if row['split']=='validation':
                    result=llm.decision(row,folder/'circuiti'/row['circuit_id'],model,candidate['temperature'],k=c['k'])
                    print(candidate['id'],row['circuit_id'],result['status'],flush=True)
    return {"model":model_id,"status":"recorded"}

def select():
    c=contract();manifest=s.require_prepared()
    # Seal decisions before loading the evaluation matrix.
    decisions={};sources={}
    for candidate in c['candidates']:
        rows={}
        for row in manifest['circuits']:
            if row['split']!='validation':continue
            p=s.VALIDATION/'candidati'/candidate['id']/'circuiti'/row['circuit_id']/'decision.json'
            if not p.is_file():raise ValueError('Missing decision: '+str(p))
            rows[row['circuit_id']]=s.read(p);sources[str(p.relative_to(s.VALIDATION))]=s.sha(p)
        decisions[candidate['id']]=rows
    s.same_or_save(s.VALIDATION/'decisioni_sigillate.json',sources)
    matrix=s.read(s.DATASET/'aggregati.json');scores={};best={}
    for a in matrix:
        if a['split']=='validation' and a['eligible_for_ranking']:
            id=a['circuit']['circuit_id'];value=a['ranking_score']
            scores[(id,a['device']['device_id'],a['configuration']['config_id'])]=value
            best[id]=max(best.get(id,float('-inf')),value)
    evaluated={};valid={}
    for candidate,rows in decisions.items():
        evaluated[candidate]={}
        for id,d in rows.items():
            response=d.get('canonical_response')
            if response and (id,response['selected_device'],response['config_id']) in scores:
                evaluated[candidate][id]=best[id]-scores[(id,response['selected_device'],response['config_id'])]
        valid[candidate]=len(evaluated[candidate])
    top=max(valid.values())
    if top==0:raise ValueError('No valid, evaluable configuration')
    eligible=[id for id,n in valid.items() if n==top]
    common=set.intersection(*(set(evaluated[id]) for id in eligible))
    if not common:raise ValueError('No common observable circuits among eligible candidates')
    table=[]
    for candidate,rows in decisions.items():
        regrets=[evaluated[candidate][id] for id in sorted(common) if id in evaluated[candidate]]
        table.append({"candidate":candidate,"valid_and_compilable":valid[candidate],"common_count":len(regrets),
           "mean_regret":mean(regrets) if regrets else None,"median_regret":median(regrets) if regrets else None,
           "repairs":sum(d['metrics']['repairs'] for d in rows.values()),
           "llm_seconds":sum(d["metrics"]["llm_seconds"] for d in rows.values()) if all(d["metrics"]["llm_seconds"] is not None for d in rows.values()) else None,
           "output_tokens":sum(d["metrics"]["output_tokens"] for d in rows.values()) if all(d["metrics"]["output_tokens"] is not None for d in rows.values()) else None,"calls":sum(d['metrics']['calls'] for d in rows.values()),
           "statuses":dict(Counter(d["status"] for d in rows.values())),
           "facts_statuses":dict(Counter(d.get("facts_status","unavailable") for d in rows.values()))})
    key=c['criterion']
    if key not in ('mean_regret','median_regret'):raise ValueError('Unsupported criterion')
    eligible_rows=[x for x in table if x['candidate'] in eligible]
    measured=[metric for metric in ('llm_seconds','output_tokens') if all(x[metric] is not None for x in eligible_rows)]
    ranking=sorted(eligible_rows,key=lambda x:(x[key],x['repairs'],x['calls'],*(x[metric] for metric in measured),x['candidate']))
    winner=next(x for x in c['candidates'] if x['id']==ranking[0]['candidate'])
    result={"winner":winner,"model":c['models'][winner['model']],"criterion":key,
            "common_circuits":sorted(common),"eligible_candidates":eligible,"table":table,"contract_sha256":s.sha(s.VALIDATION/'contratto.json'),
            "decisions_seal_sha256":s.sha(s.VALIDATION/'decisioni_sigillate.json'),"test_used":False}
    s.same_or_save(s.VALIDATION/'selezione.json',result)
    return result


def verify_selection():
    'Check seal, decisions, matrix and selected identity without regenerating data.'
    c=contract();result=s.read(s.VALIDATION/'selezione.json')
    if result['contract_sha256']!=s.sha(s.VALIDATION/'contratto.json'):raise ValueError('Validation contract changed')
    if result['decisions_seal_sha256']!=s.sha(s.VALIDATION/'decisioni_sigillate.json'):raise ValueError('Decision seal changed')
    for path,expected in s.read(s.VALIDATION/'decisioni_sigillate.json').items():
        if s.sha(s.VALIDATION/path)!=expected:raise ValueError('Validation decision changed: '+path)
    if result['model']!=c['models'][result['winner']['model']]:raise ValueError('Selected model is inconsistent')
    return result

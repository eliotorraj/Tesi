"""Selezione della profondità WL sul recupero validation, senza chiamate LLM."""
from statistics import mean
import settings as s


def select():
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    from dag_wl_core import descriptor,prepare_index,rank,request_context
    import portalocker
    manifest=s.require_prepared();corpus=load_corpus(verify_features=True)
    grid=s.CONFIG['wl_iterations']
    if not grid or len(set(grid))!=len(grid) or any(type(h) is not int or not 1<=h<=30 for h in grid):
        raise ValueError('wl_iterations deve contenere interi distinti fra 1 e 30')
    root=s.VALIDATION/'wl';root.mkdir(parents=True,exist_ok=True)
    with portalocker.Lock(str(root/'.lock'),timeout=0):
        s.same_or_save(root/'contratto.json',{'grid':grid,'k':5,'criterion':'max evaluable coverage, min mean best-in-five regret, min h',
            'experiment':s.sha(s.WORK/'contratto.json'),'dataset':corpus.source_sha256,'matrix':s.sha(s.DATASET/'aggregati.json')})
        index,index_hash=prepare_index(corpus,root/'indice')
        rankings={};sources={}
        for row in manifest['circuits']:
            if row['split']!='validation':continue
            path=root/'recupero'/(row['circuit_id']+'.json')
            if not path.exists():
                qasm=(s.WORK/row['source_ref']).read_text()
                _,request,mask=request_context(qasm);query=descriptor(qasm)
                values={str(h):[r['rag_id'] for r,score in rank(corpus,index,query,mask.available_device_ids,request.figure_of_merit,h)[:5]] for h in grid}
                s.save(path,{'circuit_id':row['circuit_id'],'source_sha256':row['source_sha256'],'index_sha256':index_hash,'rankings':values})
            rankings[row['circuit_id']]=s.read(path)['rankings'];sources[str(path.relative_to(root))]=s.sha(path)
        # Le graduatorie dipendono soltanto da QASM e train. Ora si leggono gli score validation.
        s.same_or_save(root/'recuperi_sigillati.json',sources)
        scores={};best={}
        for record in s.read(s.DATASET/'aggregati.json'):
            if record['split']=='validation' and record['eligible_for_ranking']:
                id=record['circuit']['circuit_id'];score=record['ranking_score']
                scores[(id,record['device']['device_id'],record['configuration']['config_id'])]=score
                best[id]=max(best.get(id,float('-inf')),score)
        by_id={r['rag_id']:r for r in corpus.records};regrets={h:{} for h in grid}
        for id,values in rankings.items():
            if id not in best:continue
            for h in grid:
                observed=[]
                for rag_id in values[str(h)]:
                    r=by_id[rag_id];device=r['selected_device']['device_id']
                    for cfg in r['top_configurations']:
                        key=(id,device,cfg['config_id'])
                        if key in scores:observed.append(scores[key])
                if observed:regrets[h][id]=best[id]-max(observed)
        coverage=max(map(len,regrets.values()))
        if not coverage:raise ValueError('Nessuna scelta recuperata valutabile')
        eligible=[h for h in grid if len(regrets[h])==coverage]
        common=set.intersection(*(set(regrets[h]) for h in eligible))
        if not common:raise ValueError('Nessun circuito comune fra le profondità eleggibili')
        table=[{'h':h,'evaluable':len(regrets[h]),'common_count':sum(id in regrets[h] for id in common),
                'mean_best_in_five_regret':mean(regrets[h][id] for id in common) if h in eligible else None} for h in grid]
        winner=min((r for r in table if r['h'] in eligible),key=lambda r:(r['mean_best_in_five_regret'],r['h']))
        result={'h':winner['h'],'table':table,'common_circuits':sorted(common),'index_sha256':index_hash,
                'contract_sha256':s.sha(root/'contratto.json'),'retrieval_seal_sha256':s.sha(root/'recuperi_sigillati.json'),
                'criterion':'mean_best_in_five_regret','llm_called':False,'test_used':False}
        s.same_or_save(root/'selezione.json',result)
        return result

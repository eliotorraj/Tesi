'Maximum observed in the Test grid, separate from model suggestions.'
from genera import task
from processi import execute
import settings as s

def run():
    from esegui import check
    from qiskit_dataset.catalog import load_catalog
    import portalocker
    check();manifest=s.require_prepared();catalog=load_catalog();root=s.TEST/'oracle';root.mkdir(parents=True,exist_ok=True)
    results=[]
    with portalocker.Lock(str(s.TEST/'.lock'),timeout=0):
        for row in manifest['circuits']:
            if row['split']!='test':continue
            values=[]
            for device in catalog.supported_device_ids:
                if row['num_qubits']>manifest['targets'][device]['num_qubits']:continue
                for config in catalog.configurations:
                    for seed in catalog.seeds:
                        t=task(row,device,config,seed,catalog,manifest)
                        record=execute(root/'tentativi'/t['run_id'],{'kind':'qiskit','task':t},catalog.execution_policy['timeout_seconds'])
                        values.append({"device":device,"config":config.config_id,"seed":seed,"score":record.get('score'),"status":record['status']})
            scores=[v['score'] for v in values if v['score'] is not None];maximum=max(scores) if scores else None
            value={"circuit_id":row['circuit_id'],"reference_score":maximum,"reference_is_exhaustive":bool(values) and len(scores)==len(values),"trials":values,"best":[v for v in values if maximum is not None and v['score']==maximum]}
            s.same_or_save(root/'circuiti'/(row['circuit_id']+'.json'),value);results.append(value)
        s.same_or_save(root/'oracle.json',results)
    return {"circuits":len(results),"complete":sum(x['reference_is_exhaustive'] for x in results)}

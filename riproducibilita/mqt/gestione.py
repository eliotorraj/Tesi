"""Prepara i modelli nel solo ambiente dedicato alla riproduzione."""
from pathlib import Path
import sys, runpy
import settings as s

def own_environment():
    expected=(s.KIT/'.venv').resolve()
    if Path(sys.prefix).resolve()!=expected:
        raise ValueError('Per addestrare/installare MQT usare '+str(expected/'bin/python')+'; il vecchio ambiente non viene modificato')

def hardware():
    from mqt.bench.targets import get_device
    from scripts.mqt_predictor_protocol import target_record,package_version_mismatches
    c=s.read(s.CATALOG_TEMPLATE)
    return {"versions_mismatches":package_version_mismatches(),"devices":[target_record(get_device(d)) for d in c['supported_device_ids']]}

def training(kind,args):
    if args and args[0]=="--":args=args[1:]
    if not any(x in args for x in ("--help","-h")):
        own_environment();s.require_prepared()
    path=s.KIT/'mqt'/('addestra_rl.py' if kind=='rl' else 'addestra_selettore.py')
    sys.argv=[str(path),*args]
    runpy.run_path(str(path),run_name='__main__')

def assets():
    from scripts.mqt_predictor_protocol import FROZEN_DEVICES,RL_FINAL_TIMESTEPS
    from mqt_model_artifacts import validate_rl_archive,validate_rl_training_metadata
    from validazione_selettore import validate_ml_classifier
    from mqt.predictor.rl.helper import get_path_trained_model
    from mqt.predictor.ml.helper import get_path_trained_model as ml_path
    paths=[]
    for device in FROZEN_DEVICES:
        p=s.MQT/'models/rl'/f'model_expected_fidelity_{device}.zip'
        _,errors=validate_rl_archive(p)
        if errors:raise ValueError(str(errors))
        _,errors=validate_rl_training_metadata(p.with_suffix('.metadata.json'),device_name=device,model_sha256=s.sha(p),expected_max_steps=64,expected_num_timesteps=RL_FINAL_TIMESTEPS)
        if errors:raise ValueError(str(errors))
        runtime=get_path_trained_model()/p.name
        if not runtime.is_file() or s.sha(runtime)!=s.sha(p):raise ValueError('Modello RL runtime non sincronizzato')
        paths.extend([p,p.with_suffix('.metadata.json')])
    runtime=ml_path('expected_fidelity');canonical=s.MQT/'modelli'/runtime.name
    _,errors=validate_ml_classifier(canonical)
    if errors:raise ValueError(str(errors))
    if not runtime.is_file() or s.sha(runtime)!=s.sha(canonical):raise ValueError('Selettore runtime non sincronizzato')
    meta=s.read(canonical.with_suffix('.metadata.json'))
    if meta['source_manifest_sha256']!=s.sha(s.WORK/'manifest.json'):raise ValueError('Selettore di un altro corpus')
    paths.extend([canonical,canonical.with_suffix('.metadata.json')])
    return {str(p.relative_to(s.MQT)):s.sha(p) for p in paths}


def technical():
    """Bell sintetico su ogni politica e sul selettore completo: nessun circuito Test."""
    from processi import execute
    from qiskit_dataset.catalog import load_catalog
    import portalocker
    s.require_prepared();models=assets();catalog=load_catalog()
    identity=s.digest(models);root=s.MQT/'prove_tecniche'/identity;root.mkdir(parents=True,exist_ok=True)
    qasm=root/'bell.qasm'
    text='OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;\n'
    if not qasm.exists():qasm.write_text(text)
    with portalocker.Lock(str(root/'.lock'),timeout=0):
        results={}
        for device in [*catalog.supported_device_ids,None]:
            name=device or 'selettore_completo'
            results[name]=execute(root/name,{'kind':'mqt','source':str(qasm),'seed':s.CONFIG['test_seed'],'device':device},catalog.execution_policy['timeout_seconds'])
        if any(x['status']!='success' for x in results.values()):raise ValueError('Prove MQT non tutte riuscite; vedere '+str(root))
        value={'assets':models,'sources':{name:s.sha(root/name/'result.json') for name in results},'directory':str(root)}
        s.same_or_save(s.MQT/'prove_tecniche/superate.json',value)
    return {'status':'passed','checks':len(results),'directory':str(root)}

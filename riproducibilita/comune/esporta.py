"""Esporta il train e il framework scelto in una nuova directory, mai sopra prototipo/."""
from pathlib import Path
import inspect
import json
import shutil
import settings as s


def export(destination):
    from seleziona import verify_selection
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    from llm import verify_server
    selection=verify_selection();corpus=load_corpus(verify_features=True)
    dest=Path(destination).expanduser().resolve()
    if dest.exists():raise ValueError('La destinazione deve essere nuova: '+str(dest))
    if dest.is_relative_to(s.KIT) and not dest.is_relative_to(s.OUTPUT/'esportazioni'):
        raise ValueError('Dentro riproducibilita usare esportazioni/; oppure scegliere una directory esterna')
    if dest.is_relative_to(s.KIT.parent/'prototipo') or dest.is_relative_to(s.KIT.parent/'archivio'):
        raise ValueError('Non esportare dentro prototipo o archivio')
    dest.mkdir(parents=True)
    ignore=shutil.ignore_patterns('__pycache__','node_modules','runtime','runs')
    shutil.copytree(s.KIT/'comune/framework',dest,dirs_exist_ok=True,ignore=ignore)
    shutil.copytree(s.WORK/'data',dest/'data')
    shutil.copy2(s.CATALOG_PATH,dest/'catalogo.json')
    shutil.copytree(s.SCHEMAS,dest/'schemas')
    (dest/'qiskit_dataset').mkdir();(dest/'qiskit_dataset/__init__.py').write_text('')
    for n in ['catalog.py','experiment_v2.py']:shutil.copy2(s.KIT/'dataset/qiskit_dataset'/n,dest/'qiskit_dataset'/n)
    (dest/'scripts').mkdir();(dest/'scripts/__init__.py').write_text('')
    protocol=(s.KIT/'comune/template_export/mqt_predictor_protocol.py').read_text()
    protocol+='\nfrom settings import CATALOG_PATH\n_catalog=json.loads(CATALOG_PATH.read_text())\nEXPERIMENT_ID=_catalog["experiment_id"]\nFROZEN_TARGET_SHA256=_catalog["target_sha256"]\n'
    (dest/'scripts/mqt_predictor_protocol.py').write_text(protocol)
    (dest/'settings.py').write_text('from pathlib import Path\nimport hashlib\nKIT=WORK=Path(__file__).resolve().parent\nSCHEMAS=KIT/"schemas"\nCATALOG_PATH=KIT/"catalogo.json"\ndef sha(path):\n    h=hashlib.sha256()\n    with Path(path).open("rb") as f:\n        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)\n    return h.hexdigest()\n')
    model={**selection['model'],'temperature':selection['winner']['temperature']}
    model['file']='modelli/modello.gguf';model.pop('path',None)
    config=s.read(s.KIT/'configurazioni/generazione_llm.json');config['selected']=model
    config['fixed'].update(model.get('generation',{}));config['fixed']['seed']=s.CONFIG['seed']
    s.save(dest/'configurazioni/generazione_llm.json',config)
    (dest/'modelli').mkdir();(dest/'modelli/.gitkeep').touch()
    verifier='from pathlib import Path, PureWindowsPath\nimport os,platform,shutil,subprocess,json,urllib.request\nimport settings as s\n\n'+inspect.getsource(verify_server)
    (dest/'controlla_modello.py').write_text(verifier)
    app=(dest/'app.py').read_text()
    app=app.replace("PROFILES={'desktop':60000,'laptop':16384}","PROFILES={'selected':CONFIG['selected']['context']}")
    app=app.replace("default='desktop'","default='selected'")
    app=app.replace("run.add_argument('--url',default='http://127.0.0.1:8089')","run.add_argument('--url',default=CONFIG['selected']['url']);run.add_argument('--model-path',type=Path,default=ROOT/CONFIG['selected']['file'])")
    app=app.replace("        source=args.qasm.read_text(encoding='utf-8')", "        from controlla_modello import verify_server\n        model={**CONFIG['selected'],'path':str(args.model_path.resolve()),'url':args.url}\n        save(directory/'server.json',verify_server(model))\n        source=args.qasm.read_text(encoding='utf-8')")
    app=app.replace("Http(args.url,args.timeout)","Http(args.url,args.timeout,transport=CONFIG['selected'].get('transport','native'))")
    (dest/'app.py').write_text(app)
    shutil.copy2(s.KIT/'comune/template_export/requirements.txt',dest/'requirements.txt')
    (dest/'setup.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "${BASH_SOURCE[0]}")"\npython3.12 -m venv .venv\n.venv/bin/python -m pip install -r requirements.txt\nnpm --prefix prototype/prompting/toon_runtime ci --ignore-scripts\n.venv/bin/python app.py check\n')
    s.save(dest/'provenienza.json',{'experiment_id':s.EXPERIMENT_ID,'selection':selection,'dataset_sha256':corpus.source_sha256,'code':s.code_identity(),'weights_included':False})
    (dest/'.gitignore').write_text('.venv/\nruntime/\nruns/\nnode_modules/\n__pycache__/\n*.gguf\n')
    (dest/'README.md').write_text('# Prototipo generato\n\nQuesto framework usa il Dataset train della nuova esecuzione e il modello scelto sulla validation. Non legge archivio o riproducibilita.\n\nServono Python 3.12, Node.js 22/npm e un server llama.cpp compatibile. Eseguire `bash setup.sh`, inserire il GGUF selezionato in `modelli/modello.gguf` e avviare il server con il contesto e i parametri in `configurazioni/generazione_llm.json`. I pesi non sono copiati; l’impronta viene verificata prima dell’inferenza.\n\nUso: `.venv/bin/python app.py run /percorso/circuito.qasm --compile`. L’opzione `--model-path` accetta un GGUF già disponibile altrove. `app.py check` controlla installazione e dati; `app.py prepare` costruisce l’indice RAG. I registri si trovano in `runs/`. La temperatura selezionata è applicata anche quando è diversa da zero.\n')
    return {'directory':str(dest),'train_records':len(corpus.records),'weights_copied':False,'model':model['id'],'temperature':model['temperature']}

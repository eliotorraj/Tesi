'Export train data and the selected framework into a new directory, never over prototipo/.'
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
    if dest.exists():raise ValueError('The destination must be new: '+str(dest))
    if dest.is_relative_to(s.KIT) and not dest.is_relative_to(s.OUTPUT/'esportazioni'):
        raise ValueError('Inside riproducibilita, use esportazioni/; otherwise choose an external directory')
    if dest.is_relative_to(s.KIT.parent/'prototipo') or dest.is_relative_to(s.KIT.parent/'archivio'):
        raise ValueError('Do not export inside prototipo or archivio')
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
    (dest/'README.md').write_text("""# Generated prototype

This framework uses the new run's train Dataset and the model selected on validation. It does not read the archive or reproduction toolkit.

Requirements: Python 3.12, Node.js 22/npm and a compatible llama.cpp server. Run `bash setup.sh`, place the selected GGUF in `modelli/modello.gguf` and start the server with the context and parameters in `configurazioni/generazione_llm.json`. Weights are not copied; their fingerprint is checked before inference.

Usage: `.venv/bin/python app.py run /path/to/circuit.qasm --compile`. `--model-path` accepts a GGUF already available elsewhere. `app.py check` checks installation and data; `app.py prepare` builds the RAG index. Request records are in `runs/`. The selected temperature is applied even when nonzero.
""")
    return {'directory':str(dest),'train_records':len(corpus.records),'weights_copied':False,'model':model['id'],'temperature':model['temperature']}

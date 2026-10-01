"""Collaudo isolato: copia del kit, QASM piccoli, server finto, nessun peso reale."""
from pathlib import Path
import argparse
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

KIT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,help='Directory nuova in cui conservare il collaudo')
    parser.add_argument('--configuratore',action='store_true',help='Crea e usa un esperimento nominato attraverso i nuovi comandi')
    a=parser.parse_args()
    root=a.directory.resolve() if a.directory else Path(tempfile.mkdtemp(prefix='ripro-check-'))
    if a.directory:root.mkdir(parents=True,exist_ok=False)
    kit=root/'kit'
    shutil.copytree(KIT,kit,ignore=shutil.ignore_patterns('.venv','__pycache__','esecuzioni','artefatti','risultati','esportazioni'))
    model=root/'mock.gguf';model.write_bytes(b'SYNTHETIC FIXTURE - NOT A MODEL\n')
    cfg=json.loads((kit/'configurazioni/esperimento.json').read_text())
    cfg.update(experiment_id='technical-check',corpus=str(root/'circuits'),catalog=str(root/'catalog.json'),
        model_registry=str(root/'models.json'),retrieval_k=5,wl_iterations=[1,2],
        test_methods=['random','llm_rag','llm_senza_rag','llm_recupero_random','llm_wl','llm_wl_sintesi'])
    for split,indices in [('train',range(5)),('validation',[5]),('test',[6])]:
        for i in indices:
            path=root/'circuits'/split/f'{split}_{i}.qasm';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\nrx({(i+1)/10}) q[1];\ncx q[0],q[1];\nmeasure q -> c;\n')
    catalog=json.loads((kit/'configurazioni/catalogo.json').read_text())
    catalog['supported_device_ids']=['ibm_falcon_27'];catalog['target_sha256']={'ibm_falcon_27':catalog['target_sha256']['ibm_falcon_27']}
    catalog['configurations']=catalog['configurations'][:1];catalog['execution_policy']['workers']=1
    catalog['execution_policy']['timeout_seconds']=300
    (root/'catalog.json').write_text(json.dumps(catalog));config=root/'config.json';config.write_text(json.dumps(cfg))
    class Handler(http.server.BaseHTTPRequestHandler):
        calls=0
        def log_message(self,*args):pass
        def send(self,value):
            raw=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):self.send({'model_path':str(model),'default_generation_settings':{'n_ctx':60000},'build_info':'synthetic-test-server'})
        def do_POST(self):
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path=='/apply-template':self.send({'prompt':data['messages'][0]['content']})
            elif self.path=='/tokenize':self.send({'tokens':[1,2,3]})
            elif self.path=='/completion':
                Handler.calls+=1
                answer={'selected_device':'ibm_falcon_27','config_id':'o2_default_default',
                    'facts':[{'assertion':'selected_device_has_enough_qubits'}],
                    'hypothesis':'Risposta sintetica esclusivamente per il collaudo software.'}
                if data['temperature']!=0:answer['config_id']='not_allowed'
                self.send({'content':json.dumps(answer),'stop':True,'stop_type':'eos','tokens_predicted':50,'timings':{'prompt_n':3,'predicted_n':50}})
            else:self.send({'error':'endpoint not supported'})
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    models={'models':[{'id':'synthetic','file':str(model),'context':60000,'max_output_tokens':4096,'temperatures':[0,.4],
        'precision':'synthetic','source':'software-check-only','url':f'http://127.0.0.1:{server.server_port}','transport':'native'}]}
    (root/'models.json').write_text(json.dumps(models))
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','RIPRO_CONFIG':str(config),'RIPRO_OUTPUT':str(root/'output'),
         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}
    command=[sys.executable,'-B',str(kit/'esperimento.py'),'--config',str(config),'--output',str(root/'output')]
    outcomes=[]
    def run(*args,ok=True):
        label=' '.join(args);print('CHECK',label,flush=True);start=time.perf_counter()
        result=subprocess.run([*command,*args],env=env,cwd=root,capture_output=True,text=True,timeout=1800)
        log=root/'logs'/f'{len(outcomes):02d}.txt';log.parent.mkdir(exist_ok=True);log.write_text(result.stdout+'\n'+result.stderr)
        outcomes.append({'command':label,'returncode':result.returncode,'seconds':time.perf_counter()-start,'log':str(log)})
        if (result.returncode==0)!=ok:raise AssertionError(f'{label}: {result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}')
        return result
    def read(p):return json.loads(p.read_text())
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    if a.configuratore:
        def configure(*args, ok=True):
            result=subprocess.run([sys.executable,'-B',str(kit/'configura.py'),*args],env=env,cwd=kit,capture_output=True,text=True,timeout=60)
            label='configura '+ ' '.join(args)
            log=root/'logs'/f'{len(outcomes):02d}.txt';log.parent.mkdir(exist_ok=True);log.write_text(result.stdout+'\n'+result.stderr)
            outcomes.append({'command':label,'returncode':result.returncode,'log':str(log)})
            if (result.returncode==0)!=ok:raise AssertionError(label+'\n'+result.stdout+'\n'+result.stderr)
            return result
        configure('nuovo','technical-check','--profilo','gpu','--sistemi',*cfg['test_methods'])
        configure('circuiti','technical-check','--cartella',str(root/'circuits'))
        configure('dispositivi','technical-check','ibm_falcon_27')
        configure('compilazioni','technical-check','o2_default_default')
        configure('aggiungi-modello','technical-check','synthetic','--file',str(model),'--fonte','software-check-only','--revisione','fixture-v1','--precisione','synthetic',
                  '--url',f'http://127.0.0.1:{server.server_port}','--contesto','60000','--temperature','0','0.4')
        configure('modelli','technical-check','synthetic')
        # Eseguibile simulato: il vero avviatore costruisce e registra il comando CPU.
        fake=root/'fake-llama-server'
        fake.write_text('#!'+sys.executable+'\nimport sys\nprint("synthetic llama executable", sys.argv[1:])\n')
        fake.chmod(0o755)
        configure('risorse','technical-check','--processi','1','--timeout-compilazione','300','--gpu-layers','0','--risultati',str(root/'output'),'--server-bin',str(fake))
        configure('parametri','technical-check','--wl','1','2')
        configure('verifica','technical-check')
        config=kit/'configurazioni/esperimenti/technical-check/esperimento.json'
        cfg=read(config)
        env['RIPRO_CONFIG']=str(config);env.pop('RIPRO_OUTPUT',None)
        command=[sys.executable,'-B',str(kit/'esperimento.py'),'--esperimento','technical-check']
        run('server','synthetic','--list-devices')
        run('server','synthetic')
        launches=list((root/'output/esecuzioni/technical-check/servers').glob('*/avvio.json'))
        launch=read(launches[0]);actual=launch['command']
        assert actual[actual.index('--n-gpu-layers')+1]=='0'
        assert actual[actual.index('--device')+1]=='none'
        run('server','synthetic','--controlla')
        assert 'prepara' in run('stato').stdout
    work=root/'output/esecuzioni/technical-check';val=root/'output/validation/risultati/technical-check';test=root/'output/test/risultati/technical-check'
    try:
        run('verifica');run('prepara');run('test','congela',ok=False)
        if a.configuratore:
            configure('sistemi','technical-check','random',ok=False)
            configure('duplica','technical-check','next-check')
            configure('parametri','next-check','--temperature','0')
            assert 'dataset' in run('stato').stdout
        # Una sovrapposizione fra split va rifiutata prima di congelare altre esecuzioni.
        leakage=root/'circuits/test/test_6.qasm';original=leakage.read_text();leakage.write_text((root/'circuits/train/train_0.qasm').read_text())
        run('prepara',ok=False);leakage.write_text(original)
        run('dataset');seal=read(work/'data/seal.json');assert seal['record_count']==5
        examples=[json.loads(line) for line in (work/'data/rag_examples.jsonl').read_text().splitlines()]
        assert all(r['split']=='train' and r['retrieval_input']['circuit']['circuit_id'].startswith('train_') for r in examples)
        attempts=list((root/'output/dataset/artefatti/technical-check/tentativi').glob('*/result.json'))
        assert len(attempts)==18 and all(read(p)['status']=='success' for p in attempts)
        hashes={str(p):sha(p) for p in attempts};run('dataset');assert hashes=={str(p):sha(p) for p in attempts}
        run('validation','congela')
        if a.configuratore:assert 'validation esegui --modello synthetic' in run('stato').stdout
        run('validation','esegui','--modello','synthetic')
        calls=Handler.calls;run('validation','esegui','--modello','synthetic');assert Handler.calls==calls
        run('validation','seleziona');selection=read(val/'selezione.json');assert selection['winner']['temperature']==0 and selection['test_used'] is False
        assert any(r['valid_and_compilable']==0 for r in selection['table'])
        run('validation','report');run('validation','wl');run('test','congela')
        for method in cfg['test_methods']:run('test','esegui','--metodo',method)
        results=[read(test/m/'circuiti/test_6/esito.json') for m in cfg['test_methods']]
        assert all(r['status']=='success' and r['score'] is not None for r in results),results
        count=Handler.calls;run('test','esegui','--metodo','llm_rag');assert Handler.calls==count
        run('test','oracle');run('test','analizza')
        if a.configuratore:assert '1/1 esiti registrati' in run('stato').stdout
        exported=root/'exported';run('esporta',str(exported));assert not list(exported.rglob('*.gguf'))
        # Le dipendenze JS sono installate separatamente dal sorgente esportato.
        shutil.copytree(kit/'comune/framework/prototype/prompting/toon_runtime/node_modules',exported/'prototype/prompting/toon_runtime/node_modules')
        checked=subprocess.run([sys.executable,'-B',str(exported/'app.py'),'check'],env=env,cwd=exported,capture_output=True,text=True)
        assert checked.returncode==0,checked.stderr
        used=subprocess.run([sys.executable,'-B',str(exported/'app.py'),'run',str(root/'circuits/test/test_6.qasm'),'--model-path',str(model),'--compile'],env=env,cwd=exported,capture_output=True,text=True)
        assert used.returncode==0,used.stderr
        # Dopo il congelamento, una modifica della configurazione deve essere rifiutata.
        cfg['seed']+=1;config.write_text(json.dumps(cfg));run('test','congela',ok=False)
        latex=[]
        if shutil.which('pdflatex'):
            for p in (root/'output').rglob('report.tex'):
                build=subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode',p.name],cwd=p.parent,capture_output=True,text=True)
                assert build.returncode==0,build.stdout[-2000:]
                latex.append(str(p))
        report={'status':'passed','kind':'software-check-with-synthetic-LLM','scientific_training_performed':False,'named_configuration':a.configuratore,
                'technical_resources':{'qiskit_workers':1,'compilation_timeout_seconds':300,'blas_threads':1},
                'dataset_attempts':18,'test_methods':cfg['test_methods'],'llm_calls':Handler.calls,'checks':outcomes,'latex_compiled':latex,'directory':str(root)}
        (root/'esito.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    finally:
        server.shutdown()
        (root/'comandi.json').write_text(json.dumps(outcomes,indent=2))
        print('Registri conservati:',root,flush=True)
if __name__=='__main__':main()

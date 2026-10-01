"""Avvia un server llama.cpp esterno, conserva versione e parametri; non scarica pesi."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bootstrap
import argparse,subprocess,shutil
from urllib.parse import urlparse
from uuid import uuid4
import settings as s
from llm import freeze_models


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('modello',nargs='?');parser.add_argument('--bin',default='llama-server')
    parser.add_argument('--device',help='Identificativo GPU restituito dal backend llama.cpp')
    parser.add_argument('--list-devices',action='store_true')
    parser.add_argument('--gpu-layers',type=int,default=999)
    parser.add_argument('--threads',type=int,default=6)
    a=parser.parse_args()
    executable=shutil.which(a.bin) or str(Path(a.bin).resolve())
    if a.list_devices:return subprocess.run([executable,'--list-devices']).returncode
    if not a.modello:parser.error('Specificare ID del modello oppure --list-devices')
    if a.threads<1 or a.gpu_layers<0:parser.error('Thread positivi e strati GPU non negativi richiesti')
    if a.gpu_layers==0 and a.device not in (None,'none'):parser.error('CPU richiede device none')
    model=s.model_registry()[a.modello];path=Path(model['path'])
    if not path.is_file():raise ValueError('GGUF mancante: '+str(path))
    if model.get('sha256') and s.sha(path)!=model['sha256']:raise ValueError('GGUF diverso dal registro')
    executable=shutil.which(a.bin) or str(Path(a.bin).resolve())
    revision=subprocess.run([executable,'--version'],capture_output=True,text=True,check=True)
    url=urlparse(model['url'])
    if url.hostname not in ('localhost','127.0.0.1') or not url.port:raise ValueError('Specificare localhost e porta')
    server=model.get('server',{})
    command=[executable,'--model',str(path),'--ctx-size',str(model['context']),'--host','127.0.0.1','--port',str(url.port),
        '--parallel','1','--jinja','--n-gpu-layers',str(a.gpu_layers),'--threads',str(a.threads),
        '--threads-batch',str(a.threads),'--flash-attn','on','--no-context-shift','--cache-ram','0',
        '--fit','off','--load-mode','none','--metrics',
        '--cache-type-k',server.get('cache_type_k','q8_0'),'--cache-type-v',server.get('cache_type_v','q8_0'),
        '--batch-size',str(server.get('batch_size',512)),'--ubatch-size',str(server.get('ubatch_size',128))]
    if a.gpu_layers==0:command+=['--device','none']
    elif a.device:command+=['--device',a.device]
    devices=subprocess.run([executable,'--list-devices'],capture_output=True,text=True,check=True)
    folder=s.WORK/'servers'/(a.modello+'-'+uuid4().hex)
    s.save(folder/'avvio.json',{'command':command,'version_stdout':revision.stdout,'version_stderr':revision.stderr,
        'available_devices':devices.stdout+devices.stderr,'gpu_temperature_monitor':False,
        'executable_sha256':s.sha(executable),'model_sha256':s.sha(path),'model':model})
    print('Registri server:',folder,flush=True)
    with (folder/'stdout.log').open('w') as out,(folder/'stderr.log').open('w') as err:
        proc=subprocess.Popen(command,stdout=out,stderr=err)
        try:code=proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
        s.save(folder/'fine.json',{'returncode':code})
    return code
if __name__=='__main__':raise SystemExit(main())

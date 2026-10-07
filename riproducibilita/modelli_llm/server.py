'Launch an external llama.cpp server and record version/settings; do not download weights.'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bootstrap
import argparse,subprocess,shutil
from urllib.parse import urlparse
from uuid import uuid4
import settings as s
from llm import verify_server
from comune.opzioni_server import add_arguments


def main(argv=None,args=None):
    parser=argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    a=args if args is not None else parser.parse_args(argv)
    if a.controlla and a.list_devices:parser.error('Choose --controlla or --list-devices')
    models=s.model_registry()
    if a.modello and a.modello not in models:raise ValueError('Candidate not selected: '+a.modello)
    model=models[a.modello] if a.modello else {}
    server=model.get('server',{})
    binary=a.bin or server.get('binary','llama-server')
    executable=shutil.which(binary)
    if a.controlla:
        if not model:parser.error('--controlla requires a model ID')
        observed=s.sha(model['path'])
        if model.get('sha256') and model['sha256']!=observed:raise ValueError('GGUF differs from the registry')
        verify_server({**model,'sha256':observed})
        print('Server ready: model and context match',a.modello)
        return 0
    if not executable:raise ValueError('llama-server not found or not executable: '+binary+'; use configura.py risorse NAME --server-bin PATH')
    if a.list_devices:return subprocess.run([executable,'--list-devices']).returncode
    if not a.modello:parser.error('Specify a model ID or --list-devices')
    if model.get('transport','native')=='windows':
        raise ValueError('This launcher runs Linux servers. For Windows transport, start the server with the desktop scripts, then use server '+a.modello+' --controlla')
    a.threads=a.threads if a.threads is not None else server.get('threads',6)
    a.gpu_layers=a.gpu_layers if a.gpu_layers is not None else server.get('gpu_layers',999)
    a.device=a.device if a.device is not None else server.get('device')
    if a.threads<1 or a.gpu_layers<0:parser.error('Positive thread count and nonnegative GPU layer count required')
    if a.gpu_layers==0 and a.device not in (None,'none'):parser.error('CPU requires device none')
    path=Path(model['path'])
    if not path.is_file():raise ValueError('Missing GGUF: '+str(path))
    if model.get('sha256') and s.sha(path)!=model['sha256']:raise ValueError('GGUF differs from the registry')
    revision=subprocess.run([executable,'--version'],capture_output=True,text=True,check=True)
    url=urlparse(model['url'])
    if url.hostname not in ('localhost','127.0.0.1') or not url.port:raise ValueError('Specify localhost and a port')
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
    print('Server records:',folder,flush=True)
    with (folder/'stdout.log').open('w') as out,(folder/'stderr.log').open('w') as err:
        proc=subprocess.Popen(command,stdout=out,stderr=err)
        try:code=proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
        s.save(folder/'fine.json',{'returncode':code})
    return code
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as exc:
        print('Error:',exc,file=sys.stderr)
        raise SystemExit(2)

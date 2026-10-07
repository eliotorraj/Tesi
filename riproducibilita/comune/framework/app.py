'QASM -> train RAG -> Qwen facts v4 -> configuration -> optional compilation.'
from __future__ import annotations
import argparse, dataclasses, datetime, hashlib, json, os, platform, shutil, subprocess, sys, time, urllib.request
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4
from qiskit_dataset.catalog import load_catalog
from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog, HardwareMaskBuilder
from prototype.quantum_assistant.adapters.request import QasmRequestParser, RequestSemanticValidator
from prototype.quantum_assistant.adapters.context import StructuredEvidenceRegistryBuilder, StructuredPromptBuilder
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus, DEFAULT_RAG_ROOT
from prototype.quantum_assistant.adapters.qdrant_context import prepare_index, QdrantContextRetriever
from prototype.quantum_assistant.adapters.compilation import QiskitDeterministicCompiler
from prototype.quantum_assistant.models import UiSubmission, Recommendation, QiskitCompilationPlan
from prototype.prompting.facts import messages, response_schema, verify, audit
from prototype.prompting.toon import node_path

ROOT=Path(__file__).resolve().parent
from settings import KIT
CONFIG=json.loads((KIT/'configurazioni/generazione_llm.json').read_text())
PROFILES={'desktop':60000,'laptop':16384}

def save(path,value):
    'Create a new record; refuse to overwrite an earlier attempt.'
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False)
        handle.write('\n');handle.flush();os.fsync(handle.fileno())

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def prepare(qasm,allowed=(),*,rag=True,rag_limit=5):
    'Prepare train-only evidence; the standard path retains five examples.'
    if type(rag_limit) is not int or rag_limit not in (1, 5, 10):
        raise ValueError('Supported example counts: 1, 5 or 10.')
    started=time.perf_counter();catalog=load_catalog()
    hardware=MqtHardwareCatalog(catalog.supported_device_ids,configuration_catalog=catalog).snapshot()
    parsed=QasmRequestParser().parse(UiSubmission(request_id=str(uuid4()),user_text='',qasm2=qasm,allowed_devices=tuple(allowed)))
    request=RequestSemanticValidator().normalize(parsed,hardware)
    mask=HardwareMaskBuilder().filter(request,hardware)
    if not mask.available_device_ids:
        raise ValueError('No device is compatible with the circuit and constraints.')
    examples=()
    rag_started=time.perf_counter()
    if rag:
        corpus=load_corpus();prepare_index(corpus)
        examples=QdrantContextRetriever().retrieve(request,mask,limit=rag_limit)
    rag_seconds=time.perf_counter()-rag_started if rag else 0.0
    registry=StructuredEvidenceRegistryBuilder(configuration_catalog=catalog).build(examples)
    prompt=StructuredPromptBuilder(configuration_catalog=catalog,max_examples=max(5,rag_limit)).build(request,mask,examples,evidence_registry=registry)
    return request,prompt.payload,{'seconds':time.perf_counter()-started,'rag_seconds':rag_seconds,'records':[{'rag_id':x.record_id,'distance':x.distance} for x in examples]}

class LlmTransportError(RuntimeError):
    'The server did not return a usable response: stop execution.'


class Http:
    'Connect to the local server and preserve requests, responses and errors.'
    def __init__(self,url,timeout=600,transport="native"):
        if transport not in ("native","windows"):raise ValueError('Invalid HTTP transport')
        self.transport=transport
        if not url.startswith(('http://127.0.0.1:','http://localhost:')):
            raise ValueError('The prototype requires a local server on localhost.')
        self.url=url.rstrip('/');self.timeout=timeout
    def __call__(self,endpoint,payload,directory):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
        save(directory/'request.json',payload)
        started=time.perf_counter()
        try:
            if self.transport=='windows':
                source=subprocess.check_output(['wslpath','-w',str(directory/'request.json')],text=True).strip()
                curl=shutil.which('curl.exe')
                if not curl:raise RuntimeError('Windows curl.exe is unavailable in the WSL PATH.')
                cmd=[curl,'--silent','--show-error','--fail-with-body','--max-time',str(self.timeout),'-H','Content-Type: application/json','--data-binary','@'+source,self.url+endpoint]
                proc=subprocess.run(cmd,capture_output=True,timeout=self.timeout+10)
                raw=proc.stdout
                (directory/'stderr.txt').write_bytes(proc.stderr)
                (directory/'response_raw.json').write_bytes(raw)
                if proc.returncode:raise RuntimeError('curl transport error: '+str(proc.returncode))
            else:
                req=urllib.request.Request(self.url+endpoint,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=self.timeout) as response:raw=response.read()
                (directory/'response_raw.json').write_bytes(raw)
            result=json.loads(raw)
            if result.get('error'):raise RuntimeError(str(result['error']))
            save(directory/'timing.json',{'seconds':time.perf_counter()-started,'ended_at':stamp()})
            return result
        except BaseException as exc:
            for name,data in [('response_partial.bin',getattr(exc,'output',None) or getattr(exc,'partial',None)),('stderr_partial.txt',getattr(exc,'stderr',None))]:
                if data is not None:(directory/name).write_bytes(data if isinstance(data,bytes) else str(data).encode())
            save(directory/'failure.json',{'type':type(exc).__name__,'message':str(exc),'seconds':time.perf_counter()-started,'completed_logical_attempt':False})
            if isinstance(exc, Exception):
                raise LlmTransportError(f'{endpoint}: {exc}') from exc
            raise

def decide(prompt,directory,http,context,*,max_examples=5,temperature=None,max_output_tokens=None,fixed=None):
    "Check token counts and apply the official v4 contract's three attempts."
    selected=CONFIG.get("selected",{})
    if temperature is None:temperature=selected.get("temperature",0.0)
    if max_output_tokens is None:max_output_tokens=selected.get("max_output_tokens",4096)
    feedback=[]
    for attempt in range(1,4):
        folder=Path(directory)/f'attempt_{attempt}';folder.mkdir()
        chat={'messages':messages(prompt,feedback,max_examples=max_examples),'chat_template_kwargs':{'enable_thinking':False},'reasoning_effort':'none'}
        formatted=http('/apply-template',chat,folder/'template')
        tokenized=http('/tokenize',{'content':formatted['prompt'],'add_special':False,'parse_special':True},folder/'tokenize')
        count=len(tokenized['tokens']);save(folder/'context.json',{'input_tokens':count,'output_budget':max_output_tokens,'context':context})
        if count+max_output_tokens>context:
            raise ValueError(f'Insufficient context: {count}+{max_output_tokens} > {context}. No generation performed; no examples removed.')
        excluded={'stream_options','max_tokens','chat_template_kwargs','reasoning_effort','reasoning_format'}
        payload={k:v for k,v in (fixed or CONFIG['fixed']).items() if k not in excluded}
        payload.update(temperature=temperature,stream=False,prompt=formatted['prompt'],json_schema=response_schema(max_examples=max_examples),n_predict=max_output_tokens,return_tokens=True)
        response=http('/completion',payload,folder/'call')
        if response.get('truncated') or response.get('stop_type')=='limit' or response.get('stop') is False:
            raise RuntimeError('Incomplete response or truncated context; see the record.')
        checked=verify(response.get('content',''),prompt,max_examples=max_examples)
        checked.update(attempt=attempt,input_tokens=count,timings=response.get('timings'),tokens_predicted=response.get('tokens_predicted'))
        save(folder/'validation.json',checked)
        eligible=checked['schema_valid'] and checked['selection_valid']
        if eligible and (checked['facts_status']=='verified' or attempt==3):
            checked.update(status='success' if checked['facts_status']=='verified' else 'accepted_with_unverified_facts',completed_attempts=attempt,hypothesis_status='not_semantically_verified')
            return checked
        feedback=checked['issues']
    raise ValueError('No structurally valid, allowed pair after three attempts.')

def compile_decision(request,decision,seed):
    'Compile only the allowed pair with the seed selected for this trial.'
    canonical=decision['canonical_response'];config=load_catalog().by_id[canonical['config_id']]
    recommendation=Recommendation(selected_device=canonical['selected_device'],figure_of_merit='expected_fidelity',qiskit_plan=QiskitCompilationPlan(optimization_level=config.optimization_level,seed_transpiler=seed,layout_method=config.layout_method,routing_method=config.routing_method),explanation=canonical['hypothesis'],evidence=(),schema_version='4.0.0',config_id=config.config_id)
    return QiskitDeterministicCompiler().compile(request,recommendation)

def check_installation():
    'Check required runtime components without launching experiments.'
    from prototype.prompting.toon import encode_view, decode_view, metadata
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Python 3.12 is required.')
    expected = dict(line.strip().split("==") for line in (ROOT / "requirements.txt").read_text().splitlines() if "==" in line)
    packages = {name: version(name) for name in expected}
    if packages != expected:
        raise RuntimeError('Dependencies differ from requirements.txt: ' + str(packages))
    catalog = load_catalog()
    MqtHardwareCatalog(catalog.supported_device_ids, configuration_catalog=catalog).snapshot()
    corpus = load_corpus()
    probe = {"installation_check": [1, 2, 3]}
    if decode_view(encode_view(probe)) != probe:
        raise RuntimeError('The TOON codec does not preserve values.')
    return {"status": "ready", "python": platform.python_version(), "packages": packages,
            "train_records": len(corpus.records), "devices": list(catalog.supported_device_ids),
            "toon": metadata(), "llm_server_checked": False,
            "note": 'Local check; launchers verify server and weight availability.'}


def main():
    'Separate preparation, checks and new requests; retain every error.'
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare',help='Verify train data and build local Qdrant storage')
    sub.add_parser('check',help='Check environment, train data, Targets and TOON without inference')
    run=sub.add_parser('run',help='Recommend and optionally compile a QASM circuit')
    run.add_argument('qasm',type=Path);run.add_argument('--profile',choices=PROFILES,default='desktop')
    run.add_argument('--url',default='http://127.0.0.1:8089');run.add_argument('--timeout',type=int,default=600)
    run.add_argument('--compile',action='store_true');run.add_argument('--seed-transpiler',type=int,default=0)
    run.add_argument('--device',action='append',default=[],help='Restrict allowed devices; repeatable')
    args=ap.parse_args()
    if args.command=='prepare':
        print(json.dumps(prepare_index(load_corpus()),indent=2));return
    if args.command=='check':
        print(json.dumps(check_installation(),indent=2));return
    directory=ROOT/'runs'/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8]);directory.mkdir(parents=True)
    started=time.perf_counter()
    try:
        source=args.qasm.read_text(encoding='utf-8');(directory/'input.qasm').write_text(source,encoding='utf-8')
        save(directory/'begin.json',{'at':stamp(),'kind':'technical_prototype','split':'user_input_not_experimental_test','profile':args.profile,'context':PROFILES[args.profile],'config':CONFIG,'input_sha256':hashlib.sha256(source.encode()).hexdigest(),'compile_requested':args.compile,'seed_transpiler':args.seed_transpiler,'python':sys.version,'platform':platform.platform(),'packages':{n:version(n) for n in ['qiskit','mqt.bench','numpy','networkx','qdrant-client','portalocker']},'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*.py') if not any(x in p.parts for x in ['runtime','_source','.venv'])},'measurements_missing':['process_memory','host_power'],'node_path':str(node_path()),'node_sha256':hashlib.sha256(node_path().read_bytes()).hexdigest()})
        request,prompt,retrieval=prepare(source,args.device)
        save(directory/'prompt.json',prompt);save(directory/'retrieval.json',retrieval);save(directory/'encoding.json',audit(prompt))
        decision=decide(prompt,directory,Http(args.url,args.timeout),PROFILES[args.profile])
        selected=decision['canonical_response'];configuration=load_catalog().by_id[selected['config_id']]
        decision['transpile']={'target_device':selected['selected_device'],**configuration.transpile_kwargs(),'seed_transpiler':args.seed_transpiler}
        save(directory/'decision.json',decision)
        if args.compile:
            begin=time.perf_counter();artifact=compile_decision(request,decision,args.seed_transpiler)
            (directory/'compiled.qasm').write_text(artifact.qasm2,encoding='utf-8')
            summary=dataclasses.asdict(artifact);summary.pop('qasm2');summary['seconds']=time.perf_counter()-begin
            save(directory/'compilation.json',summary)
        save(directory/'end.json',{'at':stamp(),'status':'completed','seconds':time.perf_counter()-started})
        print(json.dumps({'directory':str(directory),'status':decision['status'],'response':selected,'facts_status':decision['facts_status'],'hypothesis_status':decision['hypothesis_status'],'transpile':decision['transpile'],'compiled':args.compile},indent=2,ensure_ascii=False))
    except BaseException as exc:
        save(directory/'failure.json',{'at':stamp(),'type':type(exc).__name__,'message':str(exc),'seconds':time.perf_counter()-started})
        print(f'Error: {exc}\nRecord: {directory}',file=sys.stderr)
        raise

if __name__=='__main__':main()

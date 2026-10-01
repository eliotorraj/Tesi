"""Modelli sostituibili, identità del server, prompt e registri delle decisioni."""
from pathlib import Path, PureWindowsPath
import json, math, os, platform, random, shutil, subprocess, time, urllib.request
import settings as s

def freeze_models():
    result={}
    for id,model in s.model_registry().items():
        p=Path(model["path"])
        if not p.is_file():raise ValueError("GGUF mancante: "+str(p)+"; inserire i pesi oppure rimuovere il candidato dal registro prima del congelamento")
        observed=s.sha(p)
        if model.get("sha256") and model["sha256"]!=observed:raise ValueError("Hash GGUF diverso: "+id)
        temperatures=model.get("temperatures",s.CONFIG["temperatures"])
        if not temperatures or len(temperatures)!=len(set(temperatures)) or any(not isinstance(t,(float,int)) or not math.isfinite(t) or t<0 for t in temperatures):raise ValueError("Temperature non valide")
        if not 0<int(model["max_output_tokens"])<int(model["context"]):raise ValueError("Budget token non valido")
        result[id]={**model,"sha256":observed,"size_bytes":p.stat().st_size,"temperatures":temperatures}
    return result

def verify_server(model):
    path=Path(model["path"])
    if s.sha(path)!=model["sha256"]:raise ValueError("Pesi cambiati dopo il congelamento")
    url=model["url"].rstrip('/')
    if not url.startswith(("http://127.0.0.1:","http://localhost:")):raise ValueError("Usare un server llama.cpp locale")
    curl=shutil.which("curl.exe")
    if model.get("transport","native")=="windows":
        if not curl:raise ValueError("curl.exe Windows non disponibile")
        response=subprocess.run([curl,"--silent","--show-error","--fail","--max-time","20",url+"/props"],capture_output=True,check=True)
        props=json.loads(response.stdout)
    else:
        with urllib.request.urlopen(url+"/props",timeout=20) as response:props=json.load(response)
    served=props.get("model_path","");served_path=Path(served)
    if os.name=="posix" and PureWindowsPath(served).drive:
        win=PureWindowsPath(served);served_path=Path('/mnt')/win.drive[0].lower()/Path(*win.parts[1:])
    if not served_path.is_file() or s.sha(served_path)!=model["sha256"]:raise ValueError("Non è verificabile l'identità del modello servito: "+served)
    allocated=props.get("default_generation_settings",{}).get("n_ctx",props.get("n_ctx"))
    requested=int(model["context"])
    if allocated not in (requested,((requested+255)//256)*256):raise ValueError("Contesto del server diverso da quello congelato")
    return props

def prepare(qasm,method="llm_rag",k=5,wl=None):
    import app
    if method in ("llm_wl","llm_wl_sintesi"):
        from dag_wl_core import prepare_wl
        corpus,index,h,index_hash=wl
        return prepare_wl(qasm,corpus=corpus,index=index,h=h,with_summary=method=="llm_wl_sintesi",index_sha256=index_hash)
    if method!="llm_recupero_random":return app.prepare(qasm,rag=method!="llm_senza_rag",rag_limit=k)
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus,as_example
    from prototype.quantum_assistant.adapters.context import StructuredEvidenceRegistryBuilder,StructuredPromptBuilder
    from prototype.quantum_assistant.adapters.qdrant_context import matching_records
    from dag_wl_core import request_context
    start=time.perf_counter();catalog,request,mask=request_context(qasm);corpus=load_corpus()
    candidates=sorted(matching_records(corpus,devices=mask.available_device_ids,objective=request.figure_of_merit,experiment_id=s.EXPERIMENT_ID),key=lambda x:x["rag_id"])
    if len(candidates)<k:raise ValueError("Esempi compatibili insufficienti")
    seed=int(s.digest({"seed":s.CONFIG["random_seed"],"qasm":qasm}),16)
    chosen=random.Random(seed).sample(candidates,k)
    examples=tuple(as_example(x,0.) for x in chosen)
    registry=StructuredEvidenceRegistryBuilder(configuration_catalog=catalog).build(examples)
    prompt=StructuredPromptBuilder(configuration_catalog=catalog,max_examples=max(5,k)).build(request,mask,examples,evidence_registry=registry)
    return request,prompt.payload,{"seconds":time.perf_counter()-start,"seed":seed,"distance_semantics":"not_measured",
            "records":[{"rag_id":x["rag_id"],"distance":None} for x in chosen]}

def metrics(folder):
    calls=[]
    for p in sorted(Path(folder).glob('attempt_*/call/request.json')):
        response=p.parent/'response_raw.json';timing=p.parent/'timing.json'
        data={}
        if response.exists():
            try:data=s.read(response)
            except (ValueError,UnicodeError):pass
        times=data.get('timings') or {}
        calls.append({"input_tokens":times.get('prompt_n'),"output_tokens":data.get('tokens_predicted',times.get('predicted_n')),
                      "seconds":s.read(timing)['seconds'] if timing.exists() else None})
    def total(key):
        vals=[x[key] for x in calls]
        return sum(vals) if vals and all(x is not None for x in vals) else None
    return {"calls":len(calls),"repairs":max(0,len(calls)-1),"input_tokens":total('input_tokens'),"output_tokens":total('output_tokens'),"llm_seconds":total('seconds'),"physical_calls":calls}

def decision(row,folder,model,temperature,method="llm_rag",k=5,wl=None):
    import app
    folder=Path(folder);end=folder/'decision.json'
    if end.exists():return s.read(end)
    if (folder/'begin.json').exists():
        value={"status":"interrupted","canonical_response":None,"metrics":metrics(folder)}
        s.save(end,value);return value
    s.save(folder/'begin.json',{"circuit":row,"model":model,"temperature":temperature,"method":method,"k":k,"contract_sha256":s.sha(s.WORK/'contratto.json')})
    start=time.perf_counter()
    original_messages=app.messages
    try:
        source=(s.WORK/row['source_ref']).read_text()
        request,prompt,retrieval=prepare(source,method,k,wl)
        s.save(folder/'prompt.json',prompt);s.save(folder/'retrieval.json',retrieval)
        if method=='llm_wl_sintesi':
            from prototype.prompting.toon import encode_view,decode_view
            summary=prompt['dag_summaries'];encoded=encode_view(summary)
            if decode_view(encoded)!=summary:raise ValueError('Sintesi TOON non reversibile')
            def with_summary(*args,**kwargs):
                msgs=original_messages(*args,**kwargs)
                msgs[-1]['content']+='\nDAG summaries (not predicted scores):\n'+encoded
                return msgs
            app.messages=with_summary
        fixed=s.read(s.KIT/'configurazioni/generazione_llm.json')['fixed']
        fixed.update(model.get('generation',{}));fixed['seed']=s.CONFIG['seed']
        result=app.decide(prompt,folder,app.Http(model['url'],timeout=model.get('timeout',600),transport=model.get('transport','native')),
                          model['context'],max_examples=max(5,k),temperature=temperature,
                          max_output_tokens=model['max_output_tokens'],fixed=fixed)
    except Exception as exc:
        result={"status":"failure","canonical_response":None,"error":type(exc).__name__,"message":str(exc)}
    except BaseException:
        s.save(end,{"status":"interrupted","canonical_response":None,"metrics":metrics(folder),"decision_seconds":time.perf_counter()-start})
        raise
    finally:app.messages=original_messages
    result.update(metrics=metrics(folder),decision_seconds=time.perf_counter()-start)
    s.save(end,result);return result

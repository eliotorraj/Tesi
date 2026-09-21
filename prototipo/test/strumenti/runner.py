"""Esecuzione autonoma di un metodo. L'analisi non avvia altri metodi."""
from __future__ import annotations
import argparse
import json
import os
import platform
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import *
from gates import preflight, freeze

def terminate(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True)
    process.wait()

def compile_job(folder, job, timeout):
    save(folder/"job.json",job)
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", GITHUB_ACTIONS="true")
    started = time.perf_counter()
    timed_out = False
    with (folder/"stdout.txt").open("xb") as out, (folder/"stderr.txt").open("xb") as err:
        process = subprocess.Popen([sys.executable,str(AREA/"strumenti/worker.py"),str(folder/"job.json")],
            stdout=out,stderr=err,env=env,start_new_session=os.name=="posix")
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate(process)
            if not (folder/"result.json").exists():
                save(folder/"result.json",{"status":"timeout","score":None,"compilation_seconds":None,
                    "error":"process_timeout","timeout_seconds":timeout})
        except BaseException:
            terminate(process)
            raise
        finally:
            # Un runtime RL potrebbe lasciare discendenti anche dopo l'uscita del padre.
            if os.name == "posix":
                terminate(process)
    if not (folder/"result.json").exists():
        save(folder/"result.json",{"status":"failure","score":None,"compilation_seconds":None,
            "error":"worker_without_result","exit_code":process.returncode})
    result = read(folder/"result.json")
    if timed_out and result["status"]!="timeout":
        save(folder/"deadline.json",{"timeout_seconds":timeout,"late_result_preserved":True})
        result=dict(result,status="timeout",score=None,error="process_timeout",late_result_preserved=True)
    result["compilation_process_seconds"] = time.perf_counter()-started
    return result

def llm_metrics(folder):
    calls = sorted(folder.glob("attempt_*/call"))
    input_tokens, output_tokens, response_seconds = [], [], []
    for call in calls:
        raw = call/"response_raw.json"
        try:
            response = read(raw)
            usage = response.get("timings") or {}
            output_tokens.append(response.get("tokens_predicted", usage.get("predicted_n")))
            input_tokens.append(read(call.parent/"context.json")["input_tokens"] if (call.parent/"context.json").exists() else None)
        except (ValueError, OSError):
            input_tokens.append(None); output_tokens.append(None)
        timing = call/"timing.json" if (call/"timing.json").exists() else call/"failure.json"
        response_seconds.append(read(timing).get("seconds") if timing.exists() else None)
    def total(values):
        return sum(values) if all(isinstance(v,(int,float)) for v in values) else None
    tin, tout = total(input_tokens), total(output_tokens)
    return {"llm_calls":len(calls),"retries":max(0,len(calls)-1),
            "input_tokens":tin,"output_tokens":tout,
            "total_tokens":tin+tout if tin is not None and tout is not None else None,
            "known_input_tokens":sum(x for x in input_tokens if isinstance(x,(int,float))),
            "known_output_tokens":sum(x for x in output_tokens if isinstance(x,(int,float))),
            "token_usage_complete":tin is not None and tout is not None,
            "llm_response_seconds":total(response_seconds),
            "token_measurement":"full tokenized input plus server output per physical call; cached input counted; missing stays null"}

def evaluate(row, folder, method, url, technical=False):
    from app import prepare, decide, Http, PROFILES
    from prototype.prompting.facts import audit
    from prototype.prompting.minimal import model_input
    started = time.perf_counter()
    source = Path(row["technical_source"]) if technical else source_path(row)
    save(folder/"begin.json",{"at":now(),"circuit":row,"method":method,"source_sha256":sha(source)})
    result = {"circuit_id":row["circuit_id"],"source_sha256":row["source_sha256"],
              "split":"technical" if technical else "test","method":method,
              "retries":0,"compilation_seconds":None,"choice_seconds":None,
              "llm_response_seconds":None,"total_tokens":None,"status":"failure","score":None}
    pending_interrupt = None
    try:
        qasm = source.read_text(encoding="utf-8")
        (folder/"input.qasm").write_text(qasm,encoding="utf-8")
        choice = None
        if method != "mqt_predictor":
            choice_start = time.perf_counter()
            request, prompt, retrieval = prepare(qasm,rag=method=="llm_rag")
            save(folder/"prompt.json",prompt)
            save(folder/"retrieval.json",retrieval)
            result["rag_seconds"]=retrieval["rag_seconds"]
            if method.startswith("llm"):
                save(folder/"encoding.json",audit(prompt))
                decision = decide(prompt, folder, Http(url,read(PLAN)["llm_timeout_seconds"]),PROFILES["desktop"])
                choice = decision["canonical_response"]
                result["accepted_with_unverified_facts"] = decision["facts_status"]!="verified"
                save(folder/"decision_validation.json",decision)
            else:
                view = model_input(prompt)
                pairs = [(d["id"],c["config_id"]) for d in view["compatible_hardware"]
                         for c in view["configuration_catalog"]
                         if c["config_id"] in d.get("allowed_qiskit_configuration_ids", [x["config_id"] for x in view["configuration_catalog"]])]
                seed = int(digest({"seed":read(PLAN)["random_seed"],"circuit":row["source_sha256"]}),16)
                device, config = random.Random(seed).choice(pairs)
                choice = {"selected_device":device,"config_id":config,"seed":seed}
            result["choice_seconds"] = time.perf_counter()-choice_start
            result["config_id"]=choice["config_id"]
            save(folder/"decision.json",choice)  # Scelta durevole PRIMA della compilazione.
        compiled = compile_job(folder/"compilazione",
            {"method":method,"source":str((folder/"input.qasm").resolve()),"decision":choice,"rl_device":row.get("rl_device")},
            read(PLAN)["compilation_timeout_seconds"])
        if method!="mqt_predictor":
            compiled.pop("choice_seconds",None)
        result.update(compiled)
    except BaseException as exc:
        result.update(status="interrupted" if isinstance(exc,(KeyboardInterrupt,SystemExit)) else "failure",
                      score=None,error=type(exc).__name__,message=str(exc))
        if isinstance(exc,(KeyboardInterrupt,SystemExit)):
            pending_interrupt = exc
    result["total_seconds"] = time.perf_counter()-started
    result["finished_at"] = now()
    if method.startswith("llm"):
        result.update(llm_metrics(folder))
    save(folder/"esito.json",result)
    if pending_interrupt:
        raise pending_interrupt
    return result

def interrupted_result(row, folder, method):
    # Arresto improvviso: non ripetere una decisione o compilazione dall'esito incerto.
    result = {"circuit_id":row["circuit_id"],"source_sha256":row["source_sha256"],"split":"test",
              "method":method,"status":"interrupted","score":None,"total_seconds":None,
              "compilation_seconds":None,"choice_seconds":None,"llm_response_seconds":None,
              "retries":0,"total_tokens":None,"error":"previous_process_terminated_without_final_record"}
    if method.startswith("llm"):
        result.update(llm_metrics(folder))
    save(folder/"esito.json",result)

def verify_server(args):
    from app import CONFIG, Http
    from pathlib import PureWindowsPath
    model = args.model_path
    if model is None or not model.is_file():
        raise ValueError("--model-path deve indicare il GGUF usato dal server.")
    artifact = CONFIG["profile"]["artifact"]
    if model.stat().st_size!=artifact["size_bytes"] or sha(model)!=artifact["gguf_sha256"]:
        raise ValueError("Il GGUF non coincide con il modello selezionato.")
    # /props e' GET; passare attraverso lo stesso ponte curl Windows usato dal prototipo.
    if "microsoft" in platform.release().lower():
        process=subprocess.run(["curl.exe","--silent","--show-error","--fail","--max-time","20",args.url+"/props"],
                               capture_output=True,check=True)
        props=json.loads(process.stdout)
    else:
        import urllib.request
        with urllib.request.urlopen(args.url+"/props",timeout=20) as response:
            props=json.load(response)
    defaults=props.get("default_generation_settings",{})
    context=defaults.get("n_ctx",props.get("n_ctx"))
    if context!=60000:
        raise ValueError("Il server deve usare il profilo desktop con contesto 60000: "+str(context))
    served=props.get("model_path","")
    if PureWindowsPath(served).name!=model.name and Path(served).name!=model.name:
        raise ValueError("Il percorso modello dichiarato dal server non coincide col GGUF fornito.")
    served_path=Path(served)
    if os.name=="posix" and PureWindowsPath(served).drive:
        win=PureWindowsPath(served)
        served_path=Path("/mnt")/win.drive[0].lower()/Path(*win.parts[1:])
    if not served_path.is_file() or sha(served_path)!=artifact["gguf_sha256"]:
        raise ValueError("Impossibile verificare il GGUF effettivamente dichiarato dal server: "+served)
    return {"model_sha256":artifact["gguf_sha256"],"props":props,"url":args.url}

def cli(method):
    ap=argparse.ArgumentParser(description="Test indipendente: "+method)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verifica",action="store_true",help="Controlli senza Test e senza inferenza")
    mode.add_argument("--esegui",action="store_true",help="Esegue/riprende i 90 circuiti Test")
    mode.add_argument("--tecnico",action="store_true",help="Solo Bell sintetico; non apre il Test")
    ap.add_argument("--url",default="http://127.0.0.1:8089")
    ap.add_argument("--model-path",type=Path)
    args=ap.parse_args()
    if not args.url.startswith(("http://127.0.0.1:","http://localhost:")):
        ap.error("Il server deve essere locale.")
    audit=preflight(method)
    save(AREA/"preparazione/verifiche"/(method+"-"+uuid4().hex+".json"),audit)
    print(json.dumps(audit,ensure_ascii=False,indent=2),flush=True)
    if not audit["ready"]:
        return 1
    if args.verifica:
        print("Controlli statici superati. I metodi LLM verificano server e GGUF all'avvio.")
        return 0
    if method=="mqt_predictor" and args.esegui:
        identity=digest(audit["checks"]["mqt_models"]["details"])
        verified=False
        for path in (AREA/"prove_tecniche/mqt_predictor").glob("*/verifica_mqt.json"):
            record=read(path)
            files=record.get("files",{})
            if record.get("model_identity")==identity and len(files)==6:
                verified=all(sha(path.parent/name)==value and read(path.parent/name)["status"]=="success"
                             for name,value in files.items())
            if verified:break
        if not verified:
            raise ValueError("Eseguire prima mqt_predictor.py --tecnico: servono cinque prove RL e una qcompile.")
    server=None
    if method.startswith("llm"):
        server_log=AREA/"preparazione/verifiche"/(method+"-server-"+uuid4().hex+".json")
        try:
            server=verify_server(args)
            save(server_log,{"at":now(),"ok":True,"details":server})
        except Exception as exc:
            save(server_log,{"at":now(),"ok":False,"error":type(exc).__name__,"message":str(exc)})
            raise
    base=AREA/"prove_tecniche"/method/uuid4().hex if args.tecnico else AREA/"risultati"/method
    base.mkdir(parents=True,exist_ok=True)
    import portalocker
    with portalocker.Lock(str(base/".lock"),timeout=0):
        if args.tecnico:
            contract=None
        else:
            preparation=AREA/"preparazione"
            preparation.mkdir(parents=True,exist_ok=True)
            with portalocker.Lock(str(preparation/".freeze.lock"),timeout=120):
                contract=freeze()
        begin=base/"esecuzione.json"
        model_identity=digest(audit["checks"]["mqt_models"]["details"]) if method=="mqt_predictor" else None
        config={"method":method,"model_identity":model_identity,"contract_sha256":contract,"plan_sha256":sha(PLAN),
                "expected_circuits":(6 if method=="mqt_predictor" else 1) if args.tecnico else 90,
                "kind":"technical" if args.tecnico else "test"}
        if begin.exists():
            old=read(begin)
            if any(old[k]!=v for k,v in config.items()):
                raise ValueError("Ripresa incompatibile con la precedente esecuzione.")
        else:
            save(begin,{**config,"at":now(),"python":sys.version,"platform":platform.platform(),
                        "cpu_count":os.cpu_count(),"server":server,"code":code_files(),
                        "memory_measurement":"not collected"})
        save(base/"sessioni"/(uuid4().hex+".json"),{"at":now(),"server":server,
             "python":sys.version,"platform":platform.platform()})
        if args.tecnico:
            source=ROOT/"examples/bell.qasm"
            rows=[{"circuit_id":"bell_tecnico","source_sha256":sha(source),"technical_source":str(source)}]
            if method=="mqt_predictor":
                from qiskit_dataset.catalog import load_catalog
                rows += [dict(rows[0],circuit_id="bell_rl_"+device,rl_device=device)
                         for device in load_catalog().supported_device_ids]
        else:
            rows=sorted((r for r in read(SOURCE)["circuits"] if r["split"]=="test"),key=lambda r:r["circuit_id"])
        for i,row in enumerate(rows,1):
            folder=base/"circuiti"/row["circuit_id"]
            if (folder/"esito.json").exists():
                continue
            if (folder/"begin.json").exists():
                interrupted_result(row,folder,method)
            else:
                evaluate(row,folder,method,args.url,args.tecnico)
            print(f"{method}: {i}/{len(rows)} {row['circuit_id']}",flush=True)
        if args.tecnico and method=="mqt_predictor":
            files={str(p.relative_to(base)):sha(p) for p in (base/"circuiti").glob("*/esito.json")}
            save(base/"verifica_mqt.json",{"model_identity":model_identity,"files":files,"at":now()})
        from report import generate
        output=generate(base)
        print("Risultati e rapporto: "+str(output))
    return 0

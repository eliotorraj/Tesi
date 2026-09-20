"""Supervisore sequenziale: un solo modello, registri persistenti, ripresa esplicita."""
from __future__ import annotations
import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path
from .common import OUTPUT, ROOT, now, append_jsonl, read_json, write_json, windows_path
from .gateway import CURL, BASE
from .configuration import TIMEOUT_SECONDS, MAX_ATTEMPTS
from .hardware import DEFAULT_BATCH, DEFAULT_MICRO_BATCH, DEFAULT_GUARDS, server_arguments
from .study import MODEL_KEYS, verify_frozen_study, model_root
from scripts.mqt_predictor_protocol import file_sha256, TEST_RELEASE_RECORD

POWERSHELL="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
def ps_command(script, *arguments):
    return [POWERSHELL,"-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass",
            "-File",windows_path(ROOT/"llm_selection"/script),*map(str,arguments)]

class ExperimentStopped(RuntimeError):
    """Arresto operativo già documentato, da mostrare senza traceback generico."""

def log_tail(path, limit=6000):
    path=Path(path)
    if not path.exists(): return ""
    with path.open("rb") as stream:
        stream.seek(max(0,path.stat().st_size-limit))
        return stream.read().decode("utf-8",errors="replace").strip()

def failure_message(server_dir, log_path):
    abort_path=server_dir/"resource_abort.json"
    if abort_path.exists():
        abort=read_json(abort_path)
        sample=abort.get("last_sample",{})
        reason=abort.get("reason")
        if reason=="available_ram_below_operational_limit":
            launch=read_json(server_dir/"launch.json")
            available=sample.get("system_available_bytes")
            threshold=launch["guards"]["minimum_available_bytes"]
            measured=f"{available/2**30:.2f} GiB" if available is not None else "non disponibile"
            message=f"Prova fermata per RAM libera insufficiente: {measured}; soglia {threshold/2**30:.2f} GiB."
        else:
            message="Prova fermata dal monitor delle risorse: "+str(reason)+"."
        return message+"\nDettagli: "+str(abort_path)+"\nI risultati già salvati restano conservati; gli altri circuiti sono in attesa."
    monitor_path=server_dir/"monitor_error.json"
    if monitor_path.exists():
        return "Errore del monitor: "+str(read_json(monitor_path).get("error"))+"\nRegistro: "+str(monitor_path)
    return "Il processo delle prove si è fermato.\nRegistro: "+str(log_path)+"\n"+log_tail(log_path)

def health():
    result=subprocess.run([CURL,"--silent","--fail","--max-time","5",BASE+"/health"],
                          capture_output=True,timeout=10)
    if result.returncode: return None
    try: return json.loads(result.stdout)
    except ValueError: return None

def stop(server_dir, reason, log):
    if not (server_dir/"launch.json").exists() or (server_dir/"exit.json").exists(): return
    result=subprocess.run(ps_command("stop.ps1","-RunDirectory",windows_path(server_dir),"-Reason",reason),
                          stdout=log,stderr=subprocess.STDOUT,timeout=30)
    if result.returncode: raise RuntimeError("Owned server stop failed; inspect controller log")

def launch(model,profile,server_dir,log,events):
    manifest=read_json(OUTPUT/"models"/model/(profile["weight_precision"]+"_manifest.json"))
    model_path=Path(manifest["local_path"])
    from .storage import allocate_server_directory
    allocation=allocate_server_directory(server_dir,events)
    print("Registri del server su "+allocation["windows_directory"],flush=True)
    print(model+": verifica SHA-256 nativa Windows dei pesi; può richiedere alcuni minuti.",flush=True)
    append_jsonl(events,{"at":now(),"event":"weight_hash_check_started","model":model})
    from .weights import verify_weights
    verify_weights(manifest,events.parent/(model+"_weight_verification.json"))
    if (OUTPUT/"stop_requested.json").exists(): raise RuntimeError("User pause requested before model loading")
    command=ps_command("serve.ps1","-ModelPath",windows_path(model_path),"-RunDirectory",windows_path(server_dir),
        *server_arguments(profile))
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    started=time.monotonic()
    try:
        while time.monotonic()-started<600:
            if process.poll() is not None: raise RuntimeError("Server monitor exited during loading")
            if (server_dir/"resource_abort.json").exists(): raise RuntimeError("Resource guard stopped model loading")
            if (server_dir/"launch.json").exists() and health()=={"status":"ok"}:
                append_jsonl(events,{"at":now(),"event":"server_ready","model":model,"startup_wall_seconds":time.monotonic()-started,"run_directory":str(server_dir)})
                print(model+": server pronto; avvio delle prove.",flush=True)
                return process
            time.sleep(2)
        raise TimeoutError("Model loading exceeded 600 seconds")
    except BaseException as error:
        stop(server_dir,"controller_startup_failure",log)
        process.wait(timeout=30)
        if isinstance(error,Exception):
            raise ExperimentStopped(failure_message(server_dir,Path(log.name))) from error
        raise

def wait_runner(command, log, server_dir):
    """Progress is printed for the user; no assistant polling is needed."""
    import signal
    child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    next_update=time.monotonic()
    try:
        while child.poll() is None:
            if time.monotonic()>=next_update:
                path=server_dir/"stderr.log"
                tail=""
                if path.exists():
                    with path.open("rb") as source:
                        source.seek(max(0,path.stat().st_size-4096))
                        lines=source.read().decode(errors="replace").splitlines()
                        tail=lines[-1] if lines else ""
                print(now()+" | "+server_dir.name+" | "+tail,flush=True)
                next_update=time.monotonic()+30
            time.sleep(1)
        return child.returncode
    except BaseException:
        child.send_signal(signal.SIGINT)
        try: child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill();child.wait(timeout=10)
        raise

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--technical",action="store_true")
    parser.add_argument("--model",choices=MODEL_KEYS)
    parser.add_argument("--label",required=True)
    parser.add_argument("--episode-label",help="Technical episodes to resume; use a new controller --label.")
    parser.add_argument("--precision",choices=("BF16","Q8_0"),default="Q8_0")
    parser.add_argument("--context",type=int,default=131072)
    parser.add_argument("--cache-type",default="q8_0")
    parser.add_argument("--gpu-layers",default="all")
    parser.add_argument("--batch",type=int,default=DEFAULT_BATCH)
    parser.add_argument("--micro-batch",type=int,default=DEFAULT_MICRO_BATCH)
    parser.add_argument("--pause-hotspot",type=int,default=DEFAULT_GUARDS["pause_hotspot_c"])
    parser.add_argument("--resume-hotspot",type=int,default=DEFAULT_GUARDS["resume_hotspot_c"])
    parser.add_argument("--maximum-hotspot",type=int,default=DEFAULT_GUARDS["maximum_hotspot_c"])
    parser.add_argument("--maximum-edge",type=int,default=DEFAULT_GUARDS["maximum_edge_c"])
    parser.add_argument("--circuit",action="append")
    parser.add_argument("--technical-timeout",type=int,default=TIMEOUT_SECONDS)
    parser.add_argument("--technical-max-attempts",type=int,choices=range(1,MAX_ATTEMPTS+1),default=MAX_ATTEMPTS)
    args=parser.parse_args()
    if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.label) or not args.label:
        raise ValueError("Use a simple unique controller label")
    if TEST_RELEASE_RECORD.exists(): raise ValueError("Selection cannot run after test release")
    if args.technical and not args.model: raise ValueError("Technical trial requires a model")
    if args.technical_timeout <= 0: raise ValueError("Timeout must be positive")
    if args.technical:
        from .study import FROZEN,NATIVE_CONTEXT
        if FROZEN.exists(): raise ValueError("Technical selection profiles must be tested before study freezing")
        if not 0<args.context<=NATIVE_CONTEXT[args.model]: raise ValueError("Context exceeds native limit")
    if not args.technical and (args.circuit or args.episode_label): raise ValueError("Validation cannot select a subset or technical label")
    episode_label=args.episode_label or args.label
    if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in episode_label): raise ValueError("Invalid episode label")
    study=None if args.technical else verify_frozen_study()
    models=(args.model,) if args.technical or args.model else MODEL_KEYS
    lock=(OUTPUT/"controller.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    directory=OUTPUT/"controllers"/args.label
    directory.mkdir(parents=True,exist_ok=False)
    events=directory/"events.jsonl"
    write_json(directory/"request.json",vars(args))
    for model in models:
        if (OUTPUT/"stop_requested.json").exists():
            append_jsonl(events,{"at":now(),"event":"user_pause_before_model","model":model})
            return
        if not args.technical and (model_root(study,model)/"sealed.json").exists():
            from .study import verify_model_seal
            verify_model_seal(model_root(study,model),study)
            append_jsonl(events,{"at":now(),"event":"already_sealed_skipped","model":model})
            continue
        profile={"weight_precision":args.precision,"context":args.context,"cache_type":args.cache_type,
                 "gpu_layers":args.gpu_layers,"batch":args.batch,"micro_batch":args.micro_batch,
                 "guards":dict(DEFAULT_GUARDS, pause_hotspot_c=args.pause_hotspot,
                    resume_hotspot_c=args.resume_hotspot, maximum_hotspot_c=args.maximum_hotspot,
                    maximum_edge_c=args.maximum_edge)} if args.technical else study["models"][model]
        server_arguments(profile)  # Reject inconsistent limits before hashing/loading weights.
        server_dir=OUTPUT/"servers"/(args.label+"-"+model)
        with (directory/(model+".log")).open("w",encoding="utf-8") as log:
            monitor=launch(model,profile,server_dir,log,events)
            try:
                for circuit in args.circuit or [None]:
                    command=[sys.executable,"-m","llm_selection.run","--model",model,"--server-run",str(server_dir),
                             "--label",episode_label if args.technical else study["study_id"]]
                    if args.technical:
                        command+=["--technical","--config","p1_t0","--technical-timeout",str(args.technical_timeout),
                                  "--technical-max-attempts",str(args.technical_max_attempts)]
                        if circuit: command+=["--circuit",circuit]
                    append_jsonl(events,{"at":now(),"event":"runner_started","model":model,"command":command})
                    code=wait_runner(command,log,server_dir)
                    append_jsonl(events,{"at":now(),"event":"runner_ended","model":model,"exit_code":code})
                    if code==75:
                        append_jsonl(events,{"at":now(),"event":"user_paused_after_circuit","model":model})
                        return
                    if code:
                        message=failure_message(server_dir,Path(log.name))
                        append_jsonl(events,{"at":now(),"event":"runner_failure","message":message})
                        raise ExperimentStopped(message)
            finally:
                stop(server_dir,"controller_run_finished",log)
                monitor.wait(timeout=30)
        append_jsonl(events,{"at":now(),"event":"model_finished","model":model})
    if not args.technical and not args.model:
        from .study import seal_all
        from .evaluate import evaluate
        from .finalize import finalize
        seal_all(); evaluate(); finalize()
        from .report import build_report
        build_report()
    write_json(directory/"finished.json",{"at":now(),"technical":args.technical,"models":models})
    fcntl.flock(lock,fcntl.LOCK_UN)

if __name__=="__main__":
    try: main()
    except ExperimentStopped as error:
        print(str(error),file=sys.stderr,flush=True)
        raise SystemExit(1) from None

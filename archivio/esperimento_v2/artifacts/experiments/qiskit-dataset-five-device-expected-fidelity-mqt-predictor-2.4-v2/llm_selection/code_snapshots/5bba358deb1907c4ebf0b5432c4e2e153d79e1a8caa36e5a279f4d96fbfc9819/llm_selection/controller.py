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
from .study import MODEL_KEYS, verify_frozen_study, model_root
from scripts.mqt_predictor_protocol import file_sha256, TEST_RELEASE_RECORD

POWERSHELL="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
def ps_command(script, *arguments):
    return [POWERSHELL,"-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass",
            "-File",windows_path(ROOT/"llm_selection"/script),*map(str,arguments)]

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
    if file_sha256(model_path)!=manifest["gguf_sha256"]: raise ValueError("Model weight hash mismatch before launch")
    command=ps_command("serve.ps1","-ModelPath",windows_path(model_path),"-RunDirectory",windows_path(server_dir),
        "-Context",profile["context"],"-CacheType",profile["cache_type"],"-GpuLayers",profile["gpu_layers"],
        "-Batch",profile["batch"],"-MicroBatch",profile["micro_batch"])
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    started=time.monotonic()
    try:
        while time.monotonic()-started<600:
            if process.poll() is not None: raise RuntimeError("Server monitor exited during loading")
            if (server_dir/"resource_abort.json").exists(): raise RuntimeError("Resource guard stopped model loading")
            if (server_dir/"launch.json").exists() and health()=={"status":"ok"}:
                append_jsonl(events,{"at":now(),"event":"server_ready","model":model,"startup_wall_seconds":time.monotonic()-started,"run_directory":str(server_dir)})
                return process
            time.sleep(2)
        raise TimeoutError("Model loading exceeded 600 seconds")
    except BaseException:
        stop(server_dir,"controller_startup_failure",log)
        process.wait(timeout=30)
        raise

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--technical",action="store_true")
    parser.add_argument("--model",choices=MODEL_KEYS)
    parser.add_argument("--label",required=True)
    parser.add_argument("--precision",choices=("BF16","Q8_0"),default="Q8_0")
    parser.add_argument("--context",type=int,default=131072)
    parser.add_argument("--cache-type",default="q8_0")
    parser.add_argument("--gpu-layers",default="all")
    parser.add_argument("--batch",type=int,default=64)
    parser.add_argument("--micro-batch",type=int,default=16)
    parser.add_argument("--circuit",action="append")
    parser.add_argument("--technical-timeout",type=int,default=3600)
    args=parser.parse_args()
    if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.label) or not args.label:
        raise ValueError("Use a simple unique controller label")
    if TEST_RELEASE_RECORD.exists(): raise ValueError("Selection cannot run after test release")
    if args.technical and not args.model: raise ValueError("Technical trial requires a model")
    if not args.technical and args.circuit: raise ValueError("Validation cannot select a subset")
    study=None if args.technical else verify_frozen_study()
    models=(args.model,) if args.technical or args.model else MODEL_KEYS
    lock=(OUTPUT/"controller.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    directory=OUTPUT/"controllers"/args.label
    directory.mkdir(parents=True,exist_ok=False)
    events=directory/"events.jsonl"
    write_json(directory/"request.json",vars(args))
    for model in models:
        if not args.technical and (model_root(study,model)/"sealed.json").exists():
            from .study import verify_model_seal
            verify_model_seal(model_root(study,model),study)
            append_jsonl(events,{"at":now(),"event":"already_sealed_skipped","model":model})
            continue
        profile={"weight_precision":args.precision,"context":args.context,"cache_type":args.cache_type,
                 "gpu_layers":args.gpu_layers,"batch":args.batch,"micro_batch":args.micro_batch} if args.technical else study["models"][model]
        server_dir=OUTPUT/"servers"/(args.label+"-"+model)
        with (directory/(model+".log")).open("w",encoding="utf-8") as log:
            monitor=launch(model,profile,server_dir,log,events)
            try:
                for circuit in args.circuit or [None]:
                    command=[sys.executable,"-m","llm_selection.run","--model",model,"--server-run",str(server_dir),
                             "--label",args.label if args.technical else study["study_id"]]
                    if args.technical:
                        command+=["--technical","--config","p1_t0","--technical-timeout",str(args.technical_timeout)]
                        if circuit: command+=["--circuit",circuit]
                    append_jsonl(events,{"at":now(),"event":"runner_started","model":model,"command":command})
                    result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                    append_jsonl(events,{"at":now(),"event":"runner_ended","model":model,"exit_code":result.returncode})
                    if result.returncode: raise RuntimeError("Runner stopped; remaining cases must not be relabeled as model failures")
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

if __name__=="__main__": main()

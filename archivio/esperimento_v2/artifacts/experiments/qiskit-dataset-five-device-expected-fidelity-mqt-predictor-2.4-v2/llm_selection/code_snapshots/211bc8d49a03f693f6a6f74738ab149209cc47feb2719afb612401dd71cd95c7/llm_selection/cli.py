"""Comandi manuali dell'esperimento. Nessun avvio implicito durante status/doctor."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
from .common import OUTPUT, ROOT, read_json, write_json, now
STOP_REQUEST=OUTPUT/"stop_requested.json"

def status():
    active=[]
    for proc in Path("/proc").glob("[0-9]*"):
        try: args=(proc/"cmdline").read_bytes().split(b"\0")
        except (OSError,PermissionError): continue
        if b"llm_selection.controller" in args or b"llm_selection.run" in args:
            active.append({"pid":int(proc.name),"command":[a.decode(errors="replace") for a in args if a]})
    studies=[]
    for directory in sorted((OUTPUT/"studies").glob("*")):
        if directory.is_dir():
            counts={model:len(list((directory/model).glob("*/*/decision.json"))) for model in ("qwen","phi","gemma")}
            studies.append({"study_id":directory.name,"terminal_decisions":counts,
                           "all_sealed":(directory/"all_decisions_sealed.json").exists()})
    return {"active_processes":active,"stop_requested":STOP_REQUEST.exists(),"studies":studies,
            "frozen_study":(OUTPUT/"frozen_study.json").exists(),
            "local_winner":read_json(OUTPUT/"final_configuration.json")["winner"] if (OUTPUT/"final_configuration.json").exists() else None}

def doctor():
    from .study import MODEL_KEYS
    models={}
    import subprocess
    runtime=OUTPUT/"runtime/python/bin/python"
    runtime_info={"packages":{}}
    if runtime.exists():
        probe=subprocess.run([str(runtime),"-m","llm_selection.runtime_check"],cwd=ROOT,capture_output=True,text=True,timeout=15)
        if probe.returncode==0: runtime_info=json.loads(probe.stdout)
    for model in MODEL_KEYS:
        models[model]={precision:{"present":(OUTPUT/"models"/model/(precision+".gguf")).exists(),
                                  "verified_record":(OUTPUT/"models"/model/(precision+"_verified.json")).exists()}
                       for precision in ("BF16","Q8_0")}
    return {"root":str(ROOT),"models_directory":str((OUTPUT/"models").resolve()),"models":models,
            "llama_server_present":(OUTPUT/"runtime/b10930/llama-server.exe").exists(),
            "pause_utility_present":(OUTPUT/"runtime/pstools/pssuspend64.exe").exists(),
            "plotting_available":runtime_info["packages"].get("matplotlib") is not None,
            "isolated_runtime":runtime_info,
            "tectonic_present":(OUTPUT/"runtime/tectonic/tectonic").exists(),
            "validation_prompts":len(list((OUTPUT/"prompts"/"validation").glob("*.json"))),
            "test_release_present":(OUTPUT.parent/"manifests/test_release.json").exists(),
            "note":"Read-only readiness inventory; model hashes and long-prompt feasibility are checked when a run is launched."}

def profiles(labels, destination):
    from .study import MODEL_KEYS
    result={}
    for model,label in zip(MODEL_KEYS,labels):
        decisions=sorted((OUTPUT/"technical_episodes"/label/model).glob("*/*/decision.json"))
        if not decisions: raise ValueError(f"No completed technical episodes: {label}")
        begins=[read_json(path.parent/"begin.json") for path in decisions]
        launch=begins[0]["launch"]
        profile_keys=("context","cache_type","gpu_layers","batch","micro_batch","guards","model_path")
        if any({k:b["launch"].get(k) for k in profile_keys}!={k:launch.get(k) for k in profile_keys} for b in begins):
            raise ValueError("Technical episodes use different hardware profiles; do not combine them")
        precision=Path(launch["model_path"].replace("\\","/")).stem
        if precision not in ("BF16","Q8_0"): raise ValueError("Unknown weight precision")
        result[model]={key:launch[key] for key in ("context","cache_type","gpu_layers","batch","micro_batch","guards")}
        result[model].update(weight_precision=precision,
            precision_reason=f"User-selected technical profile {label}; see preserved trials and resource logs. Validation scores were not used.",
            technical_evidence=[str(path.relative_to(ROOT)) for path in decisions])
    if Path(destination).exists(): raise ValueError("Profiles output already exists")
    write_json(destination,result)
    return {"profiles":str(destination),"next":"Review the technical outcomes and precision reasons, then freeze the study."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("status");sub.add_parser("doctor");sub.add_parser("technical-summary")
    sub.add_parser("stop",help="Stop after the current circuit; preserve completed work.")
    sub.add_parser("clear-stop",help="Clear a previous stop request before explicit resume.")
    p=sub.add_parser("profiles");p.add_argument("--qwen",required=True);p.add_argument("--phi",required=True);p.add_argument("--gemma",required=True)
    p.add_argument("--output",type=Path,default=OUTPUT/"profiles_to_freeze.json")
    sub.add_parser("analyze")
    args=parser.parse_args()
    if args.command=="status": result=status()
    elif args.command=="doctor": result=doctor()
    elif args.command=="technical-summary":
        from .technical import technical_summary
        result=technical_summary()
    elif args.command=="stop":
        write_json(STOP_REQUEST,{"at":now(),"reason":"user_requested_pause_after_current_circuit"})
        result={"stop_requested":True,"behavior":"The current circuit is completed; no further circuit or model is started."}
    elif args.command=="clear-stop":
        if status()["active_processes"]: raise ValueError("Wait for active runners to exit before clearing a stop request")
        if STOP_REQUEST.exists():
            archive=OUTPUT/"stop_history"/(now().replace(":","-")+".json")
            archive.parent.mkdir(parents=True,exist_ok=True)
            STOP_REQUEST.replace(archive)
        result={"stop_requested":False}
    elif args.command=="profiles": result=profiles((args.qwen,args.phi,args.gemma),args.output)
    else:
        from .evaluate import evaluate
        from .finalize import finalize
        from .report import build_report
        evaluate();finalize();result=build_report()
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()

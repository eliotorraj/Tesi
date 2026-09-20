"""Esecuzione riprendibile. Questo modulo non carica la matrice degli score."""
from __future__ import annotations
import argparse
import copy
from prototype.prompting.compact import audit as encoding_audit, expand_response, REVISION
from .common import json_ready
import fcntl
import json
import resource
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
from prototype.quantum_assistant.factory import build_default_service
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.experiment_v2 import stable_sha256, source_manifest
from scripts.mqt_predictor_protocol import FROZEN_DEVICES, file_sha256, TEST_RELEASE_RECORD
from .common import OUTPUT, ROOT, append_jsonl, digest, now, read_json, write_json
from .configuration import CONFIGURATIONS, MAX_ATTEMPTS, TIMEOUT_SECONDS, payload
from .gateway import audit_tokens, generate, native_payload

def prepare_context(service, saved):
    if stable_sha256(saved["prompt"]) != saved["prompt_sha256"]:
        raise ValueError("Stored prompt hash mismatch")
    live = saved["prompt"]["live_request"]
    qasm = live["circuit"]["qasm2"]
    import hashlib
    if hashlib.sha256(qasm.encode()).hexdigest() != saved["source_sha256"]:
        raise ValueError("Full circuit no longer matches source hash")
    request={"schema_version":"1.0.0","request_id":str(uuid5(NAMESPACE_URL,"rag-validation/"+saved["source_sha256"])),
             "catalog_snapshot_id":service.hardware_catalog.snapshot().catalog_snapshot_id,
             "circuit":{"format":"openqasm2","name":saved["circuit_id"],"source":qasm},
             "figure_of_merit_id":"expected_fidelity","hardware_constraints":{}}
    started = time.perf_counter()
    context = service.prepare_request(request)
    examples = service.context_retriever.retrieve(context.request,context.mask_result,limit=5)
    registry = service.evidence_registry_builder.build(examples)
    rebuilt = service.prompt_builder.build(context.request,context.mask_result,examples,evidence_registry=registry)
    if stable_sha256(rebuilt.payload) != saved["prompt_sha256"]:
        raise ValueError("Live parser/retrieval/context differs from frozen input")
    return context, registry, time.perf_counter()-started

def summarize_response(response, number, input_tokens, service, context, registry, *, aliases=None):
    summary={"attempt":number,"input_tokens":input_tokens,"response":response,"llm_calls":1}
    if not response["transport_success"]:
        category="timeout" if response["curl_exit_code"]==28 else "transport_failure"
        summary.update(status=category,issues=[],failure={"category":category})
        return summary
    canonical = expand_response(response["content"], aliases or {})
    summary["canonical_response"] = canonical
    validated=service.validator.validate(canonical,context.request,context.mask_result,
                                          context.hardware_catalog,evidence_registry=registry)
    summary["issues"]=[json_ready(item) for item in validated.issues]
    summary["status"]="success" if validated.is_valid else "invalid_output"
    summary["json_valid"]=not any(i.code=="LLM_OUTPUT_JSON_INVALID" for i in validated.issues)
    summary["schema_valid"]=not any(i.code in ("LLM_OUTPUT_JSON_INVALID","LLM_OUTPUT_SCHEMA_INVALID") for i in validated.issues)
    if validated.is_valid:
        recommendation=validated.recommendation
        plan=recommendation.qiskit_plan
        config=load_catalog().find(plan.optimization_level,plan.layout_method,plan.routing_method)
        summary["selected_device_id"]=recommendation.selected_device
        summary["selected_config_id"]=config.config_id
        summary["recommendation"]=json_ready(recommendation)
    return summary

def episode(directory, saved, configuration, service, context, registry, context_seconds, launch, timeout=TIMEOUT_SECONDS, max_attempts=MAX_ATTEMPTS):
    if timeout <= 0 or not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise ValueError("Invalid inference budget")
    initial_request_sha256 = digest(payload(saved["prompt"], configuration))
    if (directory/"decision.json").exists():
        previous=read_json(directory/"begin.json")
        if previous.get("initial_request_sha256") != initial_request_sha256:
            raise ValueError("Changed prompt encoding/instructions: use a new episode label")
        if previous["input_prompt_sha256"] != saved["prompt_sha256"] or previous["configuration"] != configuration:
            raise ValueError("Terminal episode belongs to different inputs")
        return read_json(directory/"decision.json")
    directory.mkdir(parents=True,exist_ok=True)
    started = time.perf_counter()
    from .train_check import check as check_train
    self_check=check_train(saved)
    if self_check["applicable"] and saved["prompt"].get("retrieved_labeled_examples") and not self_check["self_retrieved_at_zero"]:
        raise ValueError("Train self-example not retrieved at zero distance; inspect retrieval before inference")
    header={"created_at":now(),"circuit_id":saved["circuit_id"],"source_sha256":saved["source_sha256"],
            "split":saved["circuit_metadata"]["split"],"configuration":configuration,"timeout_seconds":timeout,
            "max_attempts":max_attempts, "prompt_encoding_revision":REVISION,
            "initial_request_sha256":initial_request_sha256, "train_self_check":self_check,
            "input_prompt_sha256":saved["prompt_sha256"],"registry_sha256":saved["registry_sha256"],
            "examples":saved["examples"],"circuit_metadata":saved["circuit_metadata"],
            "feature_vector":saved["features"],"retrieval_and_context_seconds":context_seconds,
            "python_peak_rss_after_context_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            "original_preparation_seconds":saved["retrieval_and_prompt_seconds"],
            "original_preparation_reused":True,"launch":launch}
    if (directory/"begin.json").exists():
        old=read_json(directory/"begin.json")
        if old.get("initial_request_sha256") != initial_request_sha256:
            raise ValueError("Changed prompt encoding/instructions: use a new episode label")
        if old["input_prompt_sha256"] != saved["prompt_sha256"] or old["configuration"] != configuration:
            raise ValueError("Cannot resume an episode with changed inputs")
        if old.get("timeout_seconds",3600) != timeout or old.get("max_attempts",3) != max_attempts:
            raise ValueError("Changed inference budget requires a new episode label")
        header=old
    else:
        write_json(directory/"begin.json",header)
    attempts=[]
    issues=[]
    decision={"status":"failure","selected_device_id":None,"selected_config_id":None,
              "failure":{"category":"invalid_output"}}
    for number in range(1,max_attempts+1):
        attempt_dir=directory/f"attempt_{number}"
        summary_path=attempt_dir/"summary.json"
        if summary_path.exists():
            summary=read_json(summary_path)
        elif attempt_dir.exists():
            # A started call has an uncertain outcome: do not silently repeat it.
            if (attempt_dir/"call"/"response.json").exists():
                response=read_json(attempt_dir/"call"/"response.json")
                token_file=attempt_dir/"audit"/"tokenizer"/"response.json"
                count=len(read_json(token_file)["tokens"]) if token_file.exists() else None
                encoding=read_json(attempt_dir/"encoding.json") if (attempt_dir/"encoding.json").exists() else {}
                summary=summarize_response(response,number,count,service,context,registry,aliases=encoding.get("aliases",{}))
                summary["recovered_completed_response_at"]=now()
            else:
                summary={"attempt":number,"status":"interrupted","issues":[],
                         "llm_calls":int((attempt_dir/"call"/"request.json").exists()),
                         "call_outcome_known":False,
                         "failure":{"category":"interrupted_attempt"},"recovered_at":now()}
            write_json(summary_path,summary)
        else:
            attempt_dir.mkdir()
            prompt=copy.deepcopy(saved["prompt"])
            prompt["previous_validation_errors"]=issues
            request=payload(prompt,configuration)
            write_json(attempt_dir/"prompt.json",prompt)
            encoding=encoding_audit(prompt)
            write_json(attempt_dir/"encoding.json",encoding)
            write_json(attempt_dir/"started.json",{"at":now(),"attempt":number,
                "resource_run_key":launch.get("process_start_time"),"server_run_directory":launch.get("run_directory")})
            call_dispatched=False
            response=None
            try:
                input_tokens=audit_tokens(request,attempt_dir/"audit")
                if input_tokens+request["max_tokens"] > int(launch["context"]):
                    summary={"attempt":number,"status":"context_failure","issues":[],
                             "input_tokens":input_tokens,"llm_calls":0,
                             "failure":{"category":"full_prompt_exceeds_context"}}
                else:
                    call_dispatched=True
                    response=generate(native_payload(request,attempt_dir/"audit"),attempt_dir/"call",timeout=timeout)
                    summary=summarize_response(response,number,input_tokens,service,context,registry,aliases=encoding["aliases"])
            except Exception as error:
                summary={"attempt":number,"status":"infrastructure_failure","issues":[],
                         "llm_calls":int(call_dispatched),"call_outcome_known":not call_dispatched,
                         "failure":{"category":"infrastructure_failure","type":type(error).__name__,"message":str(error)}}
                if response is not None:
                    summary["response"]=response
                    summary["call_outcome_known"]=True
            write_json(summary_path,summary)
        if "resource_run_key" not in summary:
            attempt_start=read_json(attempt_dir/"started.json") if (attempt_dir/"started.json").exists() else {}
            summary["resource_run_key"]=attempt_start.get("resource_run_key",header["launch"].get("process_start_time"))
            write_json(summary_path,summary)
        if self_check["applicable"] and "canonical_response" in summary:
            summary["train_self_check"]=check_train(saved,summary["canonical_response"],valid=summary["status"]=="success")
            write_json(summary_path,summary)
        attempts.append(summary)
        if summary["status"]=="success":
            decision={"status":"success","selected_device_id":summary["selected_device_id"],
                      "selected_config_id":summary["selected_config_id"],"failure":None}
            break
        if summary["status"]!="invalid_output":
            decision["status"]="timeout" if summary["status"]=="timeout" else "failure"
            decision["failure"]=summary.get("failure",{"category":summary["status"]})
            break
        issues=summary["issues"]
    decision.update(circuit_id=saved["circuit_id"],source_sha256=saved["source_sha256"],
                    split=saved["circuit_metadata"]["split"],configuration_id=configuration["id"],
                    attempt_count=len(attempts),llm_calls=sum(a.get("llm_calls",0) for a in attempts),
                    repair_count=max(0,sum(a.get("llm_calls",0) for a in attempts)-1),
                    transport_retries=0,ended_at=now(),this_invocation_seconds=time.perf_counter()-started,
                    measured_call_seconds=sum(a.get("response",{}).get("elapsed_seconds",0) for a in attempts),
                    python_process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    python_rss_method="Linux getrusage ru_maxrss, cumulative process high-water mark; not an exclusive per-call peak",
                    attempts_sha256=digest(attempts),input_prompt_sha256=saved["prompt_sha256"],
                    train_self_check=attempts[-1].get("train_self_check",self_check))
    write_json(directory/"decision.json",decision)
    print(f"{directory.parent.name} {saved['circuit_id']} {decision['status']} calls={decision['llm_calls']}",flush=True)
    return decision

def ensure_server_available(server_dir, decision):
    if (server_dir/"resource_abort.json").exists() or (server_dir/"monitor_error.json").exists():
        raise RuntimeError("Server stopped by resource monitor; remaining cases are pending, not model failures")
    if (decision.get("failure") or {}).get("category") in ("transport_failure","infrastructure_failure"):
        from .controller import health
        if health()!={"status":"ok"}:
            raise RuntimeError("Inference server unavailable; remaining cases are pending")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",required=True,choices=("qwen","phi","gemma"))
    parser.add_argument("--server-run",required=True,type=Path)
    parser.add_argument("--technical",action="store_true")
    parser.add_argument("--technical-timeout",type=int)
    parser.add_argument("--technical-max-attempts",type=int,choices=range(1,MAX_ATTEMPTS+1))
    parser.add_argument("--label",required=True)
    parser.add_argument("--circuit")
    parser.add_argument("--config",choices=[c["id"] for c in CONFIGURATIONS])
    args=parser.parse_args()
    if TEST_RELEASE_RECORD.exists(): raise ValueError("Selection is closed after test release")
    if args.technical_timeout is not None and args.technical_timeout <= 0: raise ValueError("Timeout must be positive")
    if not args.technical and (args.circuit or args.config or args.technical_timeout or args.technical_max_attempts):
        raise ValueError("Validation must cover the complete frozen grid")
    split="train" if args.technical else "validation"
    launch=read_json(args.server_run/"launch.json")
    launch["run_directory"]=str(args.server_run.resolve())
    if args.model not in launch["model_path"].replace("\\","/").split("/"):
        raise ValueError("Loaded model does not match requested family")
    study=None
    if not args.technical:
        from .study import verify_frozen_study
        study=verify_frozen_study()
        if args.label!=study["study_id"]: raise ValueError("Use frozen study identifier")
        from .study import verify_launch
        verify_launch(study,args.model,launch)
    root=OUTPUT/("technical_episodes" if args.technical else "studies")/args.label/args.model
    root.mkdir(parents=True,exist_ok=True)
    from .provenance import capture
    if not args.technical and (root/"sealed.json").exists():
        from .study import verify_model_seal
        verify_model_seal(root,study)
        return
    if not (root/"provenance.json").exists(): capture(root)
    invocation=root/"invocations"/now().replace(":","-")
    capture(invocation)
    launch["invocation_provenance"]=str((invocation/"provenance.json").relative_to(ROOT))
    lock=(OUTPUT/"execution.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    service=build_default_service(device_names=FROZEN_DEVICES,llm_gateway=UnconfiguredLlmGateway(),retrieval_limit=5)
    paths=sorted((OUTPUT/"prompts"/split).glob("*.json"))
    expected={r["circuit_id"] for r in source_manifest()["circuits"] if r["split"]==split}
    if not args.technical and ({p.stem for p in paths}!=expected or len(paths)!=88):
        raise ValueError("Expected exactly the 88 frozen validation cases")
    if args.circuit:
        paths=[p for p in paths if p.stem==args.circuit]
        if len(paths)!=1: raise ValueError("Unknown technical circuit")
    configurations=[c for c in CONFIGURATIONS if not args.config or c["id"]==args.config]
    for index,path in enumerate(paths):
        if (OUTPUT/"stop_requested.json").exists():
            print("Pause requested; completed circuits preserved",flush=True)
            raise SystemExit(75)
        saved=read_json(path)
        if saved["circuit_metadata"]["split"]!=split: raise ValueError("Split mismatch")
        ordered=configurations[index%len(configurations):]+configurations[:index%len(configurations)]
        # Even completed episodes must verify the current prompt before reuse.
        context,registry,seconds=prepare_context(service,saved)
        for config in ordered:
            decision=episode(root/config["id"]/path.stem,saved,config,service,context,registry,seconds,launch,
                             timeout=args.technical_timeout or TIMEOUT_SECONDS,
                             max_attempts=args.technical_max_attempts or MAX_ATTEMPTS)
            ensure_server_available(args.server_run,decision)
    if (OUTPUT/"stop_requested.json").exists(): raise SystemExit(75)
    if not args.technical:
        from .study import seal_model
        seal_model(root,study)
    fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=="__main__": main()

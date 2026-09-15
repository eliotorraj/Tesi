"""Esecuzione riprendibile. Questo modulo non carica la matrice degli score."""
from __future__ import annotations
import argparse
import copy
from dataclasses import asdict
import fcntl
import json
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

def episode(directory, saved, configuration, service, context, registry, context_seconds, launch, timeout=TIMEOUT_SECONDS):
    if (directory/"decision.json").exists():
        previous=read_json(directory/"begin.json")
        if previous["input_prompt_sha256"] != saved["prompt_sha256"] or previous["configuration"] != configuration:
            raise ValueError("Terminal episode belongs to different inputs")
        return read_json(directory/"decision.json")
    directory.mkdir(parents=True,exist_ok=True)
    started = time.perf_counter()
    header={"created_at":now(),"circuit_id":saved["circuit_id"],"source_sha256":saved["source_sha256"],
            "split":saved["circuit_metadata"]["split"],"configuration":configuration,"timeout_seconds":timeout,
            "input_prompt_sha256":saved["prompt_sha256"],"registry_sha256":saved["registry_sha256"],
            "examples":saved["examples"],"circuit_metadata":saved["circuit_metadata"],
            "feature_vector":saved["features"],"retrieval_and_context_seconds":context_seconds,
            "original_preparation_seconds":saved["retrieval_and_prompt_seconds"],
            "original_preparation_reused":True,"launch":launch}
    if (directory/"begin.json").exists():
        old=read_json(directory/"begin.json")
        if old["input_prompt_sha256"] != saved["prompt_sha256"] or old["configuration"] != configuration:
            raise ValueError("Cannot resume an episode with changed inputs")
        header=old
    else:
        write_json(directory/"begin.json",header)
    attempts=[]
    issues=[]
    decision={"status":"failure","selected_device_id":None,"selected_config_id":None,
              "failure":{"category":"invalid_output"}}
    for number in range(1,MAX_ATTEMPTS+1):
        attempt_dir=directory/f"attempt_{number}"
        summary_path=attempt_dir/"summary.json"
        if summary_path.exists():
            summary=read_json(summary_path)
        elif attempt_dir.exists():
            # A started call has an uncertain outcome: do not silently repeat it.
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
            write_json(attempt_dir/"started.json",{"at":now(),"attempt":number})
            call_dispatched=False
            try:
                input_tokens=audit_tokens(request,attempt_dir/"audit")
                if input_tokens+request["max_tokens"] > int(launch["context"]):
                    summary={"attempt":number,"status":"context_failure","issues":[],
                             "input_tokens":input_tokens,"llm_calls":0,
                             "failure":{"category":"full_prompt_exceeds_context"}}
                else:
                    call_dispatched=True
                    response=generate(native_payload(request,attempt_dir/"audit"),attempt_dir/"call",timeout=timeout)
                    summary={"attempt":number,"input_tokens":input_tokens,"response":response,"llm_calls":1}
                    if not response["transport_success"]:
                        category="timeout" if response["curl_exit_code"]==28 else "transport_failure"
                        summary.update(status=category,issues=[],failure={"category":category})
                    else:
                        validated=service.validator.validate(response["content"],context.request,context.mask_result,
                                                              context.hardware_catalog,evidence_registry=registry)
                        summary["issues"]=[asdict(item) for item in validated.issues]
                        summary["status"]="success" if validated.is_valid else "invalid_output"
                        summary["json_valid"]=not any(i.code=="LLM_OUTPUT_JSON_INVALID" for i in validated.issues)
                        summary["schema_valid"]=not any(i.code in ("LLM_OUTPUT_JSON_INVALID","LLM_OUTPUT_SCHEMA_INVALID") for i in validated.issues)
                        if validated.is_valid:
                            recommendation=validated.recommendation
                            plan=recommendation.qiskit_plan
                            config=load_catalog().find(plan.optimization_level,plan.layout_method,plan.routing_method)
                            summary["selected_device_id"]=recommendation.selected_device
                            summary["selected_config_id"]=config.config_id
                            summary["recommendation"]=asdict(recommendation)
            except Exception as error:
                summary={"attempt":number,"status":"infrastructure_failure","issues":[],
                         "llm_calls":int(call_dispatched),"call_outcome_known":not call_dispatched,
                         "failure":{"category":"infrastructure_failure","type":type(error).__name__,"message":str(error)}}
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
                    attempts_sha256=digest(attempts),input_prompt_sha256=saved["prompt_sha256"])
    write_json(directory/"decision.json",decision)
    print(f"{directory.parent.name} {saved['circuit_id']} {decision['status']} calls={decision['llm_calls']}",flush=True)
    return decision

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",required=True,choices=("qwen","phi","gemma"))
    parser.add_argument("--server-run",required=True,type=Path)
    parser.add_argument("--technical",action="store_true")
    parser.add_argument("--technical-timeout",type=int)
    parser.add_argument("--label",required=True)
    parser.add_argument("--circuit")
    parser.add_argument("--config",choices=[c["id"] for c in CONFIGURATIONS])
    args=parser.parse_args()
    if TEST_RELEASE_RECORD.exists(): raise ValueError("Selection is closed after test release")
    if not args.technical and (args.circuit or args.config or args.technical_timeout):
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
    if not (root/"provenance.json").exists(): capture(root)
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
        saved=read_json(path)
        if saved["circuit_metadata"]["split"]!=split: raise ValueError("Split mismatch")
        ordered=configurations[index%len(configurations):]+configurations[:index%len(configurations)]
        if all((root/c["id"]/path.stem/"decision.json").exists() for c in ordered): continue
        context,registry,seconds=prepare_context(service,saved)
        for config in ordered:
            decision=episode(root/config["id"]/path.stem,saved,config,service,context,registry,seconds,launch,timeout=args.technical_timeout or TIMEOUT_SECONDS)
            if (args.server_run/"resource_abort.json").exists() or (args.server_run/"monitor_error.json").exists():
                raise RuntimeError("Server stopped by resource monitor; remaining cases are pending, not model failures")
    if not args.technical:
        from .study import seal_model
        seal_model(root,study)
    fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=="__main__": main()

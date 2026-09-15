"""Analisi a posteriori: nessuna inferenza, compilazione o lettura degli score."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, statistics, csv, traceback
from llm_selection.common import ROOT, OUTPUT
from llm_selection.run import prepare_context, summarize_response
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
from scripts.mqt_predictor_protocol import FROZEN_DEVICES
from llm_selection.complete_graph import encode

LABEL = "qwen-prova-07"
DEST = Path(__file__).resolve().parent
BASE = OUTPUT/"technical_episodes"/LABEL/"qwen"
SERVER = OUTPUT/"servers"/(LABEL+"-qwen")
CONTROLLER = OUTPUT/"controllers"/LABEL
def read(p):
    return json.loads(p.read_text())
def write(name, data):
    with (DEST/name).open("x") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.write("\n")
provenance=read(BASE/"provenance.json")
changed=[name for name,expected in provenance["code_hashes"].items()
    if not (ROOT/name).exists() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected]
if changed:
    raise RuntimeError("Code differs from original run: "+repr(changed))
service=build_default_service(device_names=FROZEN_DEVICES,llm_gateway=UnconfiguredLlmGateway(),retrieval_limit=5)
rows=[]
validations={}
sections={}
for d in sorted((BASE/"p1_t0").iterdir()):
    a=d/"attempt_1"
    r=read(a/"call/response.json")
    dec=read(d/"decision.json")
    b=read(d/"begin.json")
    count=len(read(a/"audit/tokenizer/response.json")["tokens"])
    t=r["timings"]
    complete=r["transport_success"]
    row={
        "circuit_id":d.name,"split":b["split"],"registered_status":dec["status"],
        "registered_failure":dec["failure"]["category"],"input_tokens":count,
        "processed_tokens_last_observed":t["prompt_n"],
        "remaining_tokens_last_observed":max(0,count-t["prompt_n"]),
        "progress_percent_last_observed":100*t["prompt_n"]/count,
        "call_seconds":r["elapsed_seconds"],"prompt_seconds_last_observed":t["prompt_ms"]/1000,
        "prompt_complete":complete,
        "generation_seconds":t["predicted_ms"]/1000 if complete else None,
        "generated_tokens":t["predicted_n"],"prompt_tokens_per_second":t["prompt_per_second"],
        "generation_tokens_per_second":t["predicted_per_second"] if complete else None,
        "time_to_first_content_seconds":r["ttft_content_seconds"],
        "finish_reason":r["finish_reason"],"reused_prefix_tokens":t["cache_n"],
        "context_seconds":b["retrieval_and_context_seconds"],
        "registered_measured_call_seconds":dec["measured_call_seconds"],
        "python_peak_rss_bytes":dec["python_process_peak_rss_bytes"]}
    rows.append(row)
    prompt=encode(read(a/"prompt.json"))
    sections[d.name]={k:len(json.dumps(v,ensure_ascii=False,separators=(",",":"))) for k,v in prompt.items()}
    if not complete:
        validations[d.name]={"revalidated":False,"reason":"no response content; timeout"}
        continue
    saved=read(OUTPUT/"prompts/train"/(d.name+".json"))
    context,registry,_=prepare_context(service,saved)
    validated=service.validator.validate(r["content"],context.request,context.mask_result,context.hardware_catalog,evidence_registry=registry)
    findings={"revalidated":True,"is_valid":validated.is_valid,"issues":[i.to_dict() for i in validated.issues]}
    try:
        summarize_response(r,1,count,service,context,registry)
        findings["original_summarizer_exception"]=None
    except Exception as e:
        findings["original_summarizer_exception"]={"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
    try:
        decoded=json.loads(r["content"])
        findings["json_syntax_valid"]=True
        findings["unaccepted_proposal"]={k:decoded.get(k) for k in ["selected_device","qiskit_plan"]}
    except json.JSONDecodeError as e:
        findings["json_syntax_valid"]=False
        findings["json_error"]=str(e)
    validations[d.name]=findings
    print(d.name,validated.is_valid,[i.code for i in validated.issues],flush=True)
samples=[json.loads(s) for s in (SERVER/"resources.jsonl").read_text().splitlines()]
def stat(values):
    values=[v for v in values if v is not None]
    return {"count":len(values),"min":min(values),"max":max(values),"mean_sample_weighted":statistics.mean(values),"median":statistics.median(values)} if values else {"count":0}
resources={k:stat([s.get(k) for s in samples]) for k in ["system_available_bytes","working_set_bytes","peak_working_set_bytes","private_bytes","gpu_dedicated_bytes","gpu_shared_bytes","cpu_seconds"]}
resources.update({k:stat([gpu.get(k) for s in samples for gpu in s.get("gpu_sensors",[])]) for k in ["edge_c","hotspot_c","gpu_activity_percent","asic_power_w","fan_rpm"]})
events=[json.loads(s) for s in (CONTROLLER/"events.jsonl").read_text().splitlines()]
end=read(CONTROLLER/"finished.json")["at"]
wall=(datetime.fromisoformat(end)-datetime.fromisoformat(events[0]["at"])).total_seconds()
inputs=[f for root in [BASE,CONTROLLER,SERVER] for f in root.rglob("*") if f.is_file()]
metadata={
    "created_at":datetime.now(timezone.utc).isoformat(),"label":LABEL,
    "method":"Read original logs; revalidate three stored responses with unchanged code and rebuilt prompt hashes. No LLM call, compilation, or validation/test score access.",
    "original_code_hashes_verified":True,"phase":"train_technical","controller_wall_seconds":wall,
    "controller_start_utc":events[0]["at"],"controller_end_utc":end,
    "calls":len(rows),"input_tokens_total":sum(r["input_tokens"] for r in rows),
    "processed_prompt_tokens_last_observed_total":sum(r["processed_tokens_last_observed"] for r in rows),
    "generated_tokens_total":sum(r["generated_tokens"] for r in rows),
    "call_seconds_total":sum(r["call_seconds"] for r in rows),
    "prompt_seconds_last_observed_total":sum(r["prompt_seconds_last_observed"] for r in rows),
    "generation_seconds_completed_total":sum(r["generation_seconds"] or 0 for r in rows),
    "resource_sample_count":len(samples),"resources":resources,
    "server_exit":read(SERVER/"exit.json"),"launch":read(SERVER/"launch.json"),
    "raw_files_count":len(inputs),"raw_bytes":sum(f.stat().st_size for f in inputs),
    "limitations":[
        "Timeout progress is the last saved observation, not a measurement at cancellation.",
        "Resource means are sample-weighted; GPU memory counters apply to server PID, activity/temperature/power apply to adapter.",
        "Private bytes are committed address space, not resident RAM. Shared GPU memory alone does not prove paging.",
        "Three decision.json files report measured_call_seconds=0 despite real timings saved in call/response.json.",
        "Use timings.cache_n for reused prefix tokens; usage.cached_tokens is a different end-of-call counter.",
        "This technical run provides no quality score, validation ranking, or hardware fidelity result."]}
write("statistics.json",metadata)
write("offline_validation.json",validations)
write("prompt_section_characters.json",{"unit":"compact JSON characters after reversible encoding; not tokens","circuits":sections})
write("per_circuit.json",rows)
with (DEST/"per_circuit.csv").open("x",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write("source_hashes.json",{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs})
print(json.dumps({k:v for k,v in metadata.items() if k not in ["resources","launch","limitations"]},indent=2))

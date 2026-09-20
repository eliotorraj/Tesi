"""Bozze per discussione. Conteggi soltanto: nessuna generazione o modifica al flusso."""
from pathlib import Path
from datetime import datetime, timezone
import copy, json, re, hashlib
from collections import Counter
from llm_selection.common import OUTPUT, read_json
from llm_selection.configuration import payload, CONFIGURATIONS
from llm_selection.gateway import audit_tokens
from llm_selection.complete_graph import encode

DEST=Path(__file__).resolve().parent
SOURCE=OUTPUT/"technical_episodes/qwen-prova-07/qwen/p1_t0/dj_indep_tket_2/attempt_1"
original=read_json(SOURCE/"prompt.json")
configuration=next(c for c in CONFIGURATIONS if c["id"]=="p1_t0")
def write(name,value):
    with (DEST/name).open("x",encoding="utf8") as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
def dump(v):
    return json.dumps(v,ensure_ascii=False,separators=(",",":"))

def rag_count(prompt,k):
    result=copy.deepcopy(prompt)
    result["retrieved_labeled_examples"]=result["retrieved_labeled_examples"][:k]
    identifiers={r["record_id"] for r in result["retrieved_labeled_examples"]}
    result["allowed_evidence_registry"]["records"]=[r for r in result["allowed_evidence_registry"]["records"] if r["record_id"] in identifiers]
    result["response_contract"]["required_values"]["historical_record_ids"]=[r["record_id"] for r in result["retrieved_labeled_examples"]]
    return result

def sparse(circuit):
    result=copy.deepcopy(circuit)
    for field in ("features",):
        if field in result:
            features=result[field]
            values=features.get("values",features)
            reduced={k:v for k,v in values.items() if not(k.startswith("gate_count_") and v==0)}
            result[field]={"values":reduced} if "values" in features else reduced
    result.pop("source_sha256",None)
    return result

def compact(prompt):
    result=copy.deepcopy(prompt)
    result["live_request"]["circuit"]=sparse(result["live_request"]["circuit"])
    hardware=result["live_request"]["compatible_hardware"]
    for device in hardware:
        device.pop("target_hash",None)
        device["metadata"]={k:v for k,v in device.get("metadata",{}).items() if k in ("native_gateset_id","calibration_kind","live_hardware_data")}
    caveats={}
    for entry in result["retrieved_labeled_examples"]:
        example=entry["example"]
        for caveat in example["scientific_caveats"]:
            if caveat["caveat_id"] in caveats:
                assert caveats[caveat["caveat_id"]]==caveat["text"]
            caveats[caveat["caveat_id"]]=caveat["text"]
        record=next(r for r in result["allowed_evidence_registry"]["records"] if r["record_id"]==entry["record_id"])
        original_evidence={e["evidence_id"]:e for e in example["evidence"]}
        for evidence in record["evidence"]:
            full=original_evidence[evidence["evidence_id"]]
            assert evidence["value"]==full["aggregation"]["value"]
            stability=full["stability"]
            evidence["stability"]={k:stability[k] for k in ("success_rate","score_min","score_max","score_std_population")}
            assert evidence["sample_count"]==full["aggregation"]["sample_count"]
        record["caveat_ids"]=[c["caveat_id"] for c in record.pop("caveats")]
        # Canonical record retains source claims, top configs, aggregate evidence.
        entry["example"]={
            "input":{"circuit":sparse(example["input"]["circuit"]),
                     "compatible_device_ids":[d["device_id"] for d in example["input"]["compatible_devices"]],
                     "user_constraints":example["input"]["user_constraints"]},
            "label":{"selected_device":example["label"]["selected_device"]},
        }
    result["historical_objective"]=prompt["retrieved_labeled_examples"][0]["example"]["objective"]
    assert all(e["example"]["objective"]==result["historical_objective"] for e in prompt["retrieved_labeled_examples"])
    result["scientific_caveats"]=caveats
    result["rules"] += [
        "Omitted gate_count_* features are exactly zero. Other feature values are retained.",
        "Historical source claims, configuration rankings, aggregate scores and stability appear once in allowed_evidence_registry. Historical examples link to it by record_id.",
        "Execution identifiers, per-seed observations and provenance hashes are retained by the application outside this prompt. The historical aggregates here are not scores of the current circuit.",
    ]
    return result

def aliases(prompt):
    mapping={}
    counters=Counter()
    prefixes={"rag":"R","claim":"C","evidence":"E","summary":"S"}
    def convert(v):
        if isinstance(v,dict):
            return {k:convert(x) for k,x in v.items()}
        if isinstance(v,list):
            return [convert(x) for x in v]
        if isinstance(v,str):
            match=re.fullmatch(r"(rag|claim|evidence|summary)_[0-9a-f]{64}",v)
            if match:
                if v not in mapping:
                    prefix=prefixes[match[1]]
                    counters[prefix]+=1
                    mapping[v]=prefix+str(counters[prefix])
                return mapping[v]
        return v
    result=convert(prompt)
    result["rules"].append("Use the short R/C/E/S identifiers exactly as supplied. The application resolves each identifier to its original immutable record. This proposal requires an explicit identifier-resolution adapter.")
    return result,{short:original for original,short in mapping.items()}

variants=[
    ("original_5",original,"Original prompt; five RAG records."),
    ("original_2",rag_count(original,2),"Only k changes to two; matching registry/allowed IDs updated."),
    ("compact_5",compact(original),"Five records; duplicate evidence removed, aggregate stability retained; per-seed observations and provenance stay in source artifacts."),
    ("compact_2",compact(rag_count(original,2)),"Same compact representation with two records."),
]
for name,prompt,note in list(variants):
    if name.startswith("compact"):
        aliased,mapping=aliases(prompt)
        write(name+"_aliases_map.json",mapping)
        variants.append((name+"_aliases",aliased,note+" Short reversible IDs require a new application adapter."))

metrics=[]
for name,prompt,note in variants:
    request=payload(prompt,configuration)
    count=audit_tokens(request,DEST/("audit_"+name))
    write(name+".json",prompt)
    (DEST/(name+".txt")).write_text(request["messages"][0]["content"],encoding="utf8")
    metrics.append({"variant":name,"rag_examples":len(prompt["retrieved_labeled_examples"]),
                    "input_tokens":count,"characters":len(request["messages"][0]["content"]),
                    "note":note,"prompt_sha256":hashlib.sha256(dump(prompt).encode()).hexdigest()})
    print(name,count,flush=True)
base_count=metrics[0]["input_tokens"]
for row in metrics:
    row["reduction_percent"]=100*(1-row["input_tokens"]/base_count)
write("counts.json",metrics)
# Independent section token counts are not exactly additive at boundaries.
represented=encode(original)
section_counts={}
from llm_selection.gateway import request as http_request
for key in ("live_request","retrieved_labeled_examples","allowed_evidence_registry","response_contract","configuration_catalog","rules"):
    r=http_request("/tokenize",{"content":dump(represented[key]),"add_special":False,"parse_special":True},DEST/("section_"+key))
    section_counts[key]={"characters":len(dump(represented[key])),"tokens_standalone":len(r["tokens"])}
write("section_counts.json",section_counts)
allstrings=[]
def strings(v):
    if isinstance(v,str):allstrings.append(v)
    elif isinstance(v,dict):
        for x in v.values():strings(x)
    elif isinstance(v,list):
        for x in v:strings(x)
strings(represented)
longids=[x for x in allstrings if re.fullmatch(r"(?:[a-zA-Z0-9_]+_)?[0-9a-f]{64}",x)]
write("metadata.json",{
    "created_at":datetime.now(timezone.utc).isoformat(),"source":str(SOURCE),
    "phase":"train_prompt_design_proposal","circuit":"dj_indep_tket_2",
    "long_hash_identifier_occurrences":len(longids),"long_hash_identifier_unique":len(set(longids)),
    "long_hash_identifier_characters":sum(map(len,longids)),
    "method":"Counts from existing Qwen server /apply-template and /tokenize only. No /completion call. No server restart or hardware/profile change.",
    "limitations":["One train circuit only; counts are not latency or answer-quality measurements.",
        "Compact variants omit raw per-seed observations, execution IDs and repeated provenance from the model input; these remain in original files. Aggregates, min/max, standard deviation and success rate remain.",
        "Short identifiers require an application adapter before the existing semantic validator. Drafts are not installed in the production prompt builder.",
        "Five-to-two RAG variants remove evidence and require validation; two is not demonstrated optimal.",
        "Current prompt includes its own train circuit among retrieved examples; no quality/generalization inference is drawn."],
})
print(json.dumps(metrics,indent=2))

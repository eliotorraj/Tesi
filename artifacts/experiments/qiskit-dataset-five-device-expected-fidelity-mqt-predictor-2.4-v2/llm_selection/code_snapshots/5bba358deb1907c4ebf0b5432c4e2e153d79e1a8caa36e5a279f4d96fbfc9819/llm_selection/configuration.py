"""Griglia piccola comune; la selezione viene sigillata solo dopo le prove train."""
import copy
import json
BASE_INSTRUCTION = (
    "Read the complete request below. Recommend one compatible device and one allowed "
    "Qiskit configuration. Return only the JSON object required by response_contract. "
    "Use the historical examples as evidence, never as a measurement of the new circuit."
)
CHECKLIST = (
    "Before answering, check internally: copy the live request_id and catalog_snapshot_id; "
    "select hardware from the compatible list; match all plan fields to one allowed configuration; "
    "include live_compatibility; support both device and exact configuration with historical claims. "
    "Each historical reference needs the exact record_id, evidence source_id and source_claim_id "
    "from allowed_evidence_registry. The parameters of each cited historical claim must match "
    "the corresponding source claim. Do not output this checklist or extra prose."
)
CONFIGURATIONS = [
    {"id":"p0_t0","prompt_variant":"base","temperature":0.0},
    {"id":"p0_t07","prompt_variant":"base","temperature":0.7},
    {"id":"p1_t0","prompt_variant":"checklist","temperature":0.0},
]
FIXED = {
    "max_tokens":2048, "top_p":0.95, "top_k":40, "min_p":0.0,
    "seed":20260913, "repeat_penalty":1.0, "presence_penalty":0.0,
    "frequency_penalty":0.0, "mirostat":0, "typical_p":1.0,
    "cache_prompt":True, "stream":True, "stream_options":{"include_usage":True},
    "timings_per_token":True, "return_progress":True,
    "chat_template_kwargs":{"enable_thinking":False},
    "reasoning_effort":"none", "reasoning_format":"none",
}
TIMEOUT_SECONDS = 3600
MAX_ATTEMPTS = 3

def messages(prompt, variant):
    from .complete_graph import encode, NOTE
    represented=encode(prompt)
    note=NOTE+"\n\n" if represented!=prompt else ""
    text = BASE_INSTRUCTION + "\n\n" + note + json.dumps(represented,ensure_ascii=False,separators=(",",":"))
    if variant == "checklist":
        checklist=CHECKLIST if prompt.get("retrieved_labeled_examples") else (
            "Before answering, check internally: copy the live request_id and catalog_snapshot_id; "
            "select hardware from the compatible list; match all plan fields to one allowed configuration; "
            "include live_compatibility and use only the evidence actually provided. "
            "No historical examples were retrieved; do not invent historical references or claims. "
            "Do not output this checklist or extra prose.")
        text += "\n\n" + checklist
    elif variant != "base": raise ValueError("Unknown prompt variant")
    return [{"role":"user","content":text}]

def payload(prompt, configuration):
    result=copy.deepcopy(FIXED)
    result["temperature"]=configuration["temperature"]
    result["messages"]=messages(prompt,configuration["prompt_variant"])
    result["response_format"]={"type":"json_object","schema":prompt["response_contract"]["json_schema"]}
    return result

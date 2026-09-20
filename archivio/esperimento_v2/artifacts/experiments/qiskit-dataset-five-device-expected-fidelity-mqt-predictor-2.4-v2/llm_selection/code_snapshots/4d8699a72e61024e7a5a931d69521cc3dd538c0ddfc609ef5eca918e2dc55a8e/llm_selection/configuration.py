"""Griglia piccola comune; la selezione viene sigillata solo dopo le prove train."""
import copy
from prototype.prompting.rendering import messages
CONFIGURATIONS = [
    {"id":"p0_t0","prompt_variant":"base","temperature":0.0},
    {"id":"p0_t07","prompt_variant":"base","temperature":0.7},
    {"id":"p1_t0","prompt_variant":"checklist","temperature":0.0},
]
FIXED = {
    "max_tokens":4096, "top_p":0.95, "top_k":40, "min_p":0.0,
    "seed":20260913, "repeat_penalty":1.0, "presence_penalty":0.0,
    "frequency_penalty":0.0, "mirostat":0, "typical_p":1.0,
    "cache_prompt":True, "stream":True, "stream_options":{"include_usage":True},
    "timings_per_token":True, "return_progress":True,
    "chat_template_kwargs":{"enable_thinking":False},
    "reasoning_effort":"none", "reasoning_format":"none",
}
# Limite operativo comune dal 14 settembre: il prototipo deve rispondere in minuti.
TIMEOUT_SECONDS = 3600
MAX_ATTEMPTS = 3

def payload(prompt, configuration):
    result=copy.deepcopy(FIXED)
    result["temperature"]=configuration["temperature"]
    result["messages"]=messages(prompt,configuration["prompt_variant"])
    from prototype.prompting.minimal import response_schema
    result["response_format"]={"type":"json_object","schema":response_schema(prompt)}
    return result

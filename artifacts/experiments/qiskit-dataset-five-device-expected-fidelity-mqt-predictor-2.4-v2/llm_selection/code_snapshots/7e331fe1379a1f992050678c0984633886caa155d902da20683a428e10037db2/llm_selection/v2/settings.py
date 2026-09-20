"""Regole esplicite della seconda validation."""
import copy
from llm_selection.common import OUTPUT
from llm_selection.configuration import FIXED, MAX_ATTEMPTS, TIMEOUT_SECONDS
REVISION = "facts-v4-toon2-20260919"

CONFIGURATIONS = [
    {"id": "p0_t0", "prompt_variant": "facts", "temperature": 0.0},
    {"id": "p0_t04", "prompt_variant": "facts", "temperature": 0.4},
    {"id": "p0_t07", "prompt_variant": "facts", "temperature": 0.7},
]
MODEL_KEYS = ("qwen", "phi", "gemma")
POLICY = {
    "contract": "4.0.0", "prompt_revision": REVISION,
    "facts_min": 1, "facts_max": 2, "hypothesis_max_characters": 400,
    "hypothesis_semantics": "not validated; avoid citation IDs by instruction only",
    "max_completed_attempts": 3,
    "exhausted_facts": "accept final structurally valid response with allowed pair; record facts as unverified",
    "interruptions": "archive incomplete physical call; repeat same logical attempt without consuming budget",
    "timeout_without_resource_interruption": "terminal timeout, not an unlimited retry",
    "reference": "maximum median score among compatible pairs with all seeds 0,1,2 successful",
    "missing_scores": "null, publish circuit identities and denominators",
    "selection_order": ["maximum valid_and_compilable", "minimum median observed regret on common circuits",
                        "minimum repairs", "minimum all physical generation calls",
                        "minimum measured call seconds if complete", "minimum output tokens if complete", "lexicographic"],
    "bootstrap": {"unit": "circuit", "draws": 2000, "seed": 20260913, "scope": "descriptive"},
    "recoverable_resource_failures": "wait until resources recover; no model failure",
    "unexplained_transport_restarts": 3,
}

def study_root(study_id):
    if not study_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in study_id):
        raise ValueError("Invalid study ID")
    if study_id == "local-llm-v1":
        raise ValueError("The historical study cannot be modified by v2")
    return OUTPUT / "studies" / study_id

def payload(prompt, configuration, feedback=()):
    from prototype.prompting.facts import messages, response_schema
    result = copy.deepcopy(FIXED)
    result.update(temperature=configuration["temperature"], messages=messages(prompt, feedback),
                  response_format={"type": "json_object", "schema": response_schema()})
    return result

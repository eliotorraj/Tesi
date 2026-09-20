"""Prompt reversibile: nessun circuito, esempio, campo o valore viene eliminato."""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
import json
import re
from . import complete_graph
from .wire import unpack

REVISION = "lossless-v2-20260914"
OPAQUE = re.compile(r"(?:(?:rag|claim|evidence|summary|run|target|snapshot)_[0-9a-f]{64}|[0-9a-f]{64})$")
PREFIX = {"rag": "R", "claim": "C", "evidence": "E", "summary": "S", "run": "U"}
NOTE = (
    "Input encoding is lossless. R#, C#, E#, S#, U#, H# are opaque source identifiers: "
    "copy them exactly when citing sources. Their long originals are restored by the application. "
    "shared_values stores repeated data once; an object with only $use means that exact shared value. "
    "An object with exactly $columns and $rows is a table: each row assigns its values to the columns in order. "
    "These notations apply only to input data. Keep the full response_contract JSON output structure."
)

def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def _map(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_map(item, mapping) for item in value]
    if isinstance(value, dict):
        return {mapping.get(key, key): _map(item, mapping) for key, item in value.items()}
    return value

def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        if set(value) in ({"$use"}, {"$columns", "$rows"}):
            raise ValueError("Input collides with reserved lossless encoding marker")
        for key, item in value.items():
            yield key
            yield from _strings(item)

def _tables(value):
    if isinstance(value, dict):
        return {k: _tables(v) for k, v in value.items()}
    if isinstance(value, list):
        nested = [_tables(v) for v in value]
        # pack is reversible, but tiny tables may be larger than their input.
        candidate = nested
        if len(nested) >= 4 and all(isinstance(row, dict) for row in nested):
            columns = list(nested[0])
            if columns and all(set(row) == set(columns) for row in nested):
                candidate = {"$columns": columns, "$rows": [[row[k] for k in columns] for row in nested]}
        return candidate if len(dumps(candidate)) < len(dumps(nested)) else nested
    return value

def encode(prompt):
    """Restituisce dati per il modello e mappa locale; verifica ogni valore."""
    graph = complete_graph.encode(prompt)
    strings = list(_strings(graph))
    occupied = set(strings)
    live = graph.get("live_request", {})
    protected = {live.get("request_id"), live.get("catalog_snapshot_id")}
    aliases, counts = {}, Counter()
    for value in strings:
        if value in aliases or value in protected or not OPAQUE.fullmatch(value):
            continue
        prefix = PREFIX.get(value.split("_", 1)[0], "H")
        while True:
            counts[prefix] += 1
            alias = f"{prefix}{counts[prefix]}"
            if alias not in occupied:
                break
        aliases[value] = alias
        occupied.add(alias)
    replaced = _map(graph, aliases)
    frequency = Counter()
    def count(value):
        if isinstance(value, (dict, list)):
            if len(dumps(value)) >= 160:
                frequency[dumps(value)] += 1
            for child in (value.values() if isinstance(value, dict) else value):
                count(child)
    # Keep the live circuit and the output schema directly readable.
    compactable = [k for k in replaced if k not in ("live_request", "response_contract", "rules", "previous_validation_errors")]
    for key in compactable:
        count(replaced[key])
    for device in replaced.get("live_request", {}).get("compatible_hardware", []):
        count(device)
    pool, pool_ids = {}, {}
    def intern(value, *, allow=True):
        if not isinstance(value, (dict, list)):
            return value
        fingerprint = dumps(value)
        if allow and frequency[fingerprint] > 1:
            if fingerprint not in pool_ids:
                key = f"D{len(pool_ids)+1}"
                pool_ids[fingerprint] = key
                pool[key] = intern(value, allow=False)
            return {"$use": pool_ids[fingerprint]}
        if isinstance(value, list):
            return [intern(v) for v in value]
        return {k: intern(v) for k, v in value.items()}
    compact = copy.deepcopy(replaced)
    for key in compactable:
        # RAG examples remain an explicit list in their original order.
        if key == "retrieved_labeled_examples":
            compact[key] = [_tables(intern(v, allow=False)) for v in replaced[key]]
        else:
            compact[key] = _tables(intern(replaced[key], allow=False))
    for device in compact.get("live_request", {}).get("compatible_hardware", []):
        for key in list(device):
            device[key] = _tables(intern(device[key]))
    encoded = {"revision": REVISION, "prompt": compact,
               "shared_values": {k: _tables(v) for k, v in pool.items()},
               "aliases": {v: k for k, v in aliases.items()}}
    restored = decode(encoded)
    if restored != prompt or dumps(restored) != dumps(prompt):
        raise ValueError("Lossless prompt round-trip failed")
    return encoded

def decode(encoded):
    if encoded["revision"] != REVISION:
        raise ValueError("Unknown prompt encoding revision")
    pool = {k: unpack(v) for k, v in encoded["shared_values"].items()}
    def restore(value, active=()):
        if isinstance(value, dict):
            if set(value) == {"$use"}:
                key = value["$use"]
                if key in active or key not in pool:
                    raise ValueError("Unknown or cyclic shared value")
                return restore(pool[key], (*active, key))
            return {k: restore(v, active) for k, v in value.items()}
        if isinstance(value, list):
            return [restore(v, active) for v in value]
        return value
    result = restore(unpack(encoded["prompt"]))
    return complete_graph.decode(_map(result, encoded["aliases"]))

def model_input(encoded):
    """Gli hash lunghi restano nel registro locale, fuori dal testo al modello."""
    return {"shared_values": encoded["shared_values"], **encoded["prompt"]}

def audit(prompt, encoded=None):
    encoded = encoded or encode(prompt)
    return {"revision": REVISION, "aliases": encoded["aliases"],
            "original_sha256": hashlib.sha256(dumps(prompt).encode()).hexdigest(),
            "model_input_sha256": hashlib.sha256(dumps(model_input(encoded)).encode()).hexdigest(),
            "roundtrip_verified": True, "rag_example_count": len(prompt.get("retrieved_labeled_examples", []))}

def expand_response(raw, aliases):
    """Ripristina soltanto identità note. Non corregge scelte, claim o relazioni."""
    from prototype.quantum_assistant.schema_validation import decode_json_object
    from prototype.quantum_assistant.adapters.validation import MAX_LLM_OUTPUT_BYTES
    try:
        value = decode_json_object(raw, max_bytes=MAX_LLM_OUTPUT_BYTES) if isinstance(raw, (str, bytes)) else copy.deepcopy(raw)
    except ValueError:
        return raw  # The ordinary validator reports malformed JSON.
    if not isinstance(value, dict):
        return raw
    refs = value.get("evidence_refs")
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict):
                for key in ("record_id", "source_claim_id", "source_id"):
                    current = ref.get(key)
                    if isinstance(current, str):
                        ref[key] = aliases.get(current, current)
    return value

"""Contratto v4: fatti controllabili e ipotesi libera, senza score di valutazione."""
from __future__ import annotations
import copy
import json
import re
import time
from prototype.quantum_assistant.schema_validation import decode_json_object, load_schema, validate_instance
from .minimal import model_input, citation_context, digest
from .toon import encode_view, NOTE as TOON_NOTE

REVISION = "facts-v4-toon3-20260919"
SCHEMA = load_schema("llm_recommendation_v4.schema.json")
RULES = {
    "selected_pair_among_reported_best": "example_id required: selected_device and config_id occur together in that example's displayed top_configurations, including explicit tied_score_config_ids; not necessarily rank 1 or a unique winner.",
    "selected_device_matches_example": "example_id required: selected_device equals that example's selected_device; this says nothing about config_id.",
    "same_qubit_count_as_example": "example_id required: current and example circuits have exactly the same num_qubits; this does not establish similar topology or performance.",
    "selected_device_has_enough_qubits": "no example_id: selected device num_qubits >= current circuit num_qubits; this does not establish compilation quality.",
}
NOTE = (
    "Choose one compatible device and one allowed config_id. Return only the required JSON. "
    "Give 1 or 2 distinct facts using only the assertion types below. Facts must match the supplied data. "
    "Write a brief free hypothesis in one or two complete sentences. "
    "Use at most 1000 characters, finish every sentence, and explain both choices in ordinary language, without example IDs "
    "such as E1, record IDs or citation codes. Refer naturally to similar historical circuits when useful. "
    "Example of concise style: I propose this pair based on similarities to the retrieved circuits; its performance on the current circuit remains untested. "
    "The hypothesis is a proposal, not a verified fact: do not claim that performance on the current "
    "circuit is known or guaranteed. Historical results belong only to their original circuits. "
    "You may propose any allowed pair, including pairs absent from the historical results. "
    "Never invent historical support. Rankings apply within each example, not across different circuits. "
    "Expected fidelity is an estimate on synthetic targets, not a real hardware measurement. "
    "Check device compatibility, allowed configuration and each fact before answering."
)

def response_schema():
    return copy.deepcopy(SCHEMA)

def messages(prompt, feedback=()):
    view = model_input(prompt)
    view.pop("previous_validation_errors", None)
    schema = {k: v for k, v in SCHEMA.items() if k not in ("$schema", "$id", "title")}
    fence = chr(96) * 3
    text = NOTE + "\n" + TOON_NOTE + "\n" + fence + "toon\n" + encode_view(view) + "\n" + fence + "\n"
    text += "fact_rules: " + json.dumps(RULES, separators=(",", ":"))
    text += "\nresponse_schema: " + json.dumps(schema, separators=(",", ":"))
    if not view.get("retrieved_labeled_examples"):
        text += "\nNo historical examples are supplied. Give exactly one fact: selected_device_has_enough_qubits, without example_id. Do not invent example references or historical support.\n"
    if feedback:
        text += "\nCorrect the previous response and return the whole JSON. You may keep an allowed pair.\n"
        text += json.dumps(list(feedback), ensure_ascii=False)
    return [{"role": "user", "content": text}]

def audit(prompt):
    return {"revision": REVISION, "schema_version": "4.0.0",
            "schema_sha256": digest(SCHEMA), "model_view_sha256": digest(model_input(prompt)),
            "citation_context": citation_context(prompt).to_dict()}

def verify(raw, prompt):
    """Separate structural, choice and fact checks; never certify free prose."""
    started = time.perf_counter()
    result = {"schema_version": "4.0.0", "json_valid": False, "schema_valid": False,
              "selection_valid": False, "facts_status": "not_evaluated", "fact_checks": [],
              "issues": [], "hypothesis_status": "not_evaluated",
              "explanation_fully_verified": False, "canonical_response": None}
    def issue(code, path, message):
        result["issues"].append({"code": code, "path": path, "message": message})
    try:
        decoded = decode_json_object(raw, max_bytes=65536) if isinstance(raw, (str, bytes)) else raw
        if not isinstance(decoded, dict):
            raise ValueError("Expected a JSON object")
        json.dumps(decoded, allow_nan=False)
    except (ValueError, TypeError) as error:
        issue("JSON_INVALID", "$", str(error))
        result["validation_seconds"] = time.perf_counter() - started
        return result
    result.update(json_valid=True, canonical_response=decoded)
    schema_errors = validate_instance(SCHEMA, decoded, error_code="SCHEMA_INVALID")
    for item in schema_errors:
        issue(item.code, item.path, item.message)
    if not schema_errors and not decoded["hypothesis"].strip():
        issue("SCHEMA_INVALID", "$.hypothesis", "Write a nonempty hypothesis.")
    result["schema_valid"] = not result["issues"]
    view = model_input(prompt)
    devices = {d["id"]: d for d in view["compatible_hardware"]}
    configs = {c["config_id"] for c in view["configuration_catalog"]}
    device_id, config_id = decoded.get("selected_device"), decoded.get("config_id")
    device = devices.get(device_id) if isinstance(device_id, str) else None
    pair_valid = bool(device is not None and isinstance(config_id, str) and config_id in configs
                      and config_id in device.get("allowed_qiskit_configuration_ids", configs)
                      and device["num_qubits"] >= view["circuit"]["num_qubits"])
    result["selection_valid"] = pair_valid
    if not pair_valid:
        issue("PAIR_NOT_ALLOWED", "$.selected_device", "Choose a compatible device and a config_id allowed for it.")
    if not result["schema_valid"]:
        result["validation_seconds"] = time.perf_counter() - started
        return result
    result["hypothesis_contains_example_ids"] = bool(re.search(r"\bE[1-5]\b", decoded["hypothesis"]))
    examples = {e["id"]: e for e in view["retrieved_labeled_examples"]}
    aliases = citation_context(prompt).aliases
    for index, fact in enumerate(decoded["facts"]):
        kind, alias = fact["assertion"], fact.get("example_id")
        check = {"index": index, "assertion": kind, "example_id": alias,
                 "record_id": aliases.get(alias), "result": "unsupported", "resolved": {}}
        example = examples.get(alias)
        correct = False
        if kind == "selected_device_has_enough_qubits":
            if alias is None and device is not None:
                correct = device["num_qubits"] >= view["circuit"]["num_qubits"]
                check["resolved"] = {"device_id": device_id, "device_num_qubits": device["num_qubits"],
                                     "current_num_qubits": view["circuit"]["num_qubits"]}
        elif example is not None:
            check["resolved"]["circuit"] = example["circuit"].get("name") or example["circuit"].get("circuit_id")
            if kind == "selected_pair_among_reported_best":
                matches = [c for c in example.get("top_configurations", [])
                           if c["device_id"] == device_id and config_id in
                           [c["config_id"], *c.get("tied_score_config_ids", [])]]
                correct = bool(matches)
                check["resolved"]["historical_rows"] = matches
            elif kind == "selected_device_matches_example":
                correct = example.get("selected_device") == device_id
                check["resolved"]["historical_device"] = example.get("selected_device")
            elif kind == "same_qubit_count_as_example":
                current, historical = view["circuit"].get("num_qubits"), example["circuit"].get("num_qubits")
                correct = current is not None and historical is not None and current == historical
                check["resolved"].update(current_num_qubits=current, example_num_qubits=historical)
        check["result"] = "verified" if correct else "unsupported"
        result["fact_checks"].append(check)
        if not correct:
            issue("FACT_NOT_SUPPORTED", f"$.facts[{index}]",
                  f"Fact {index + 1} ({kind}, example_id={alias}) does not match the provided data. "
                  f"Observed data: {json.dumps(check['resolved'], ensure_ascii=False)}. Rule: {RULES[kind]} "
                  "Correct this fact; an allowed proposed pair need not change.")
    result["facts_status"] = "verified" if all(c["result"] == "verified" for c in result["fact_checks"]) else "unverified"
    result["validation_seconds"] = time.perf_counter() - started
    return result

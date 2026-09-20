"""Vista LLM essenziale. Il documento canonico e la provenienza restano esterni."""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import re

from prototype.quantum_assistant.schema_validation import load_schema

REVISION = "minimal-v3-toon1-20260919"
CONTRACT_VERSION = "3.0.0"
SCHEMA = load_schema("llm_recommendation_v3.schema.json")
NOTE = (
    "Choose one compatible device and one config_id from the catalog. "
    "Return only JSON with selected_device, config_id, claim, evidence. "
    "claim is one brief explanation of both choices; evidence lists only example IDs such as E1. "
    "Cite at least one supplied labeled example when available; otherwise use [] and state that no historical support is available. "
    "Examples are historical observations, not measurements of the current circuit. "
    "expected_fidelity is an estimate on synthetic targets, not a real hardware measurement. "
    "Configurations are ranked within each example, not across unrelated circuits. "
    "All catalog configurations are allowed unless a device lists a restriction."
)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()


@dataclass(frozen=True)
class CitationContext:
    """Identità locali vincolate alla richiesta e al registro, mai inviate al modello."""
    request_id: str
    catalog_snapshot_id: str
    record_ids: tuple[str, ...]
    registry_sha256: str
    request_sha256: str

    @property
    def aliases(self):
        return {f"E{i}": record_id for i, record_id in enumerate(self.record_ids, 1)}

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "catalog_snapshot_id": self.catalog_snapshot_id,
            "record_ids": list(self.record_ids),
            "registry_sha256": self.registry_sha256,
            "request_sha256": self.request_sha256,
        }


def citation_context(prompt):
    live = prompt["live_request"]
    ids = tuple(e["record_id"] for e in prompt.get("retrieved_labeled_examples", []))
    if len(ids) > 5 or len(ids) != len(set(ids)):
        raise ValueError("Expected at most five distinct retrieved examples")
    return CitationContext(live["request_id"], live["catalog_snapshot_id"], ids,
                           digest(prompt["allowed_evidence_registry"]),
                           digest({"qasm2": live["circuit"].get("qasm2", ""),
                                   "figure_of_merit": live["figure_of_merit"],
                                   "constraints": live.get("constraints", {}),
                                   "features": live["circuit"].get("features", {})}))


def response_schema(prompt=None):
    """Lo schema esterno ha una versione; il modello non deve ricopiarla."""
    schema = copy.deepcopy(SCHEMA)
    if prompt is not None:
        context = citation_context(prompt)
        records = {r["record_id"] for r in prompt["allowed_evidence_registry"]["records"]}
        aliases = [key for key, rid in context.aliases.items() if rid in records]
        if aliases:
            schema["properties"]["evidence"]["minItems"] = 1
            schema["properties"]["evidence"]["items"]["enum"] = aliases
        else:
            schema["properties"]["evidence"]["maxItems"] = 0
    return schema


def _circuit(source):
    # Explicit allowlist: features are copied whole, with all zeros and precision.
    fields = ("name", "circuit_id", "benchmark_family", "generator",
              "num_qubits", "depth", "size", "operation_names", "features")
    return {k: copy.deepcopy(source[k]) for k in fields if k in source}


def _hardware(device):
    fields = ("id", "num_qubits", "operation_names", "coupling_edges",
              "allowed_qiskit_configuration_ids")
    result = {k: copy.deepcopy(device[k]) for k in fields if k in device}
    metadata = device.get("metadata", {})
    if metadata.get("native_gateset_id"):
        result["native_gateset_id"] = metadata["native_gateset_id"]
    # Existing exact representation for a complete topology; no shared-value indirection.
    size, edges = device["num_qubits"], device.get("coupling_edges")
    if edges is not None and [list(pair) for pair in edges] == [[i, j] for i in range(size) for j in range(size) if i != j]:
        result["coupling_edges"] = {"topology": "fully_connected", "directed": True,
                                   "self_loops": False}
    return result


def _example(entry, alias):
    example = entry["example"]
    source = example.get("input", {})
    label = example.get("label", {})
    selected = label.get("selected_device", {})
    configurations = label.get("top_configurations", [])
    result = {
        "id": alias,
        "circuit": _circuit(source.get("circuit", {})),
        "compatible_devices": [
            d.get("device_id", d.get("id")) for d in source.get("compatible_devices", [])
        ],
    }
    if selected:
        result["selected_device"] = selected["device_id"]
        # Keep ordering, associations and ties. Raw observations stay in the registry.
        result["top_configurations"] = [
            {k: copy.deepcopy(c[k]) for k in
             ("rank", "device_id", "config_id", "median_score", "tied_score_config_ids")
             if k in c}
            for c in configurations[:3]
        ]
    else:
        result["historical_result_available"] = False
    if source.get("user_constraints"):
        result["constraints"] = copy.deepcopy(source["user_constraints"])
    return result


def feedback(issues, *, has_examples=True):
    """Una frase per tipo di errore; nessun valore arbitrario dalla risposta."""
    result = []
    for issue in issues:
        path = issue.get("path", "$")
        if path == "$.selected_device":
            message = "Dispositivo non ammesso: scegli selected_device dagli ID di compatible_hardware."
        elif path == "$.config_id":
            message = (
                "Configurazione non ammessa: scegli config_id da configuration_catalog, "
                "rispettando i vincoli del dispositivo scelto."
            )
        elif re.fullmatch(r"\$\.evidence(\[[0-9]+\])?", path):
            message = (
                "Evidence non valida: usa solo gli ID di retrieved_labeled_examples, "
                "senza duplicati e con almeno un riferimento."
                if has_examples else
                "Evidence non valida: non ci sono esempi storici; usa evidence: []."
            )
        else:
            message = "Risposta non conforme allo schema."
        if message not in result:
            result.append(message)
    return result


def model_input(prompt):
    citation_context(prompt)  # Fail early on duplicate or oversized retrieval.
    live = prompt["live_request"]
    hardware = [_hardware(d) for d in live["compatible_hardware"]]
    config_ids = [c["config_id"] for c in prompt["configuration_catalog"]["allowed_configurations"]]
    for device in hardware:
        if list(device.get("allowed_qiskit_configuration_ids", ())) == config_ids:
            del device["allowed_qiskit_configuration_ids"]
    result = {
        "figure_of_merit": live["figure_of_merit"],
        "circuit": _circuit(live["circuit"]),
        "compatible_hardware": hardware,
        "configuration_catalog": [
            {k: copy.deepcopy(c[k]) for k in
             ("config_id", "optimization_level", "layout_method", "routing_method")}
            for c in prompt["configuration_catalog"]["allowed_configurations"]
        ],
        "retrieved_labeled_examples": [
            _example(entry, f"E{i}") for i, entry in
            enumerate(prompt.get("retrieved_labeled_examples", []), 1)
        ],
    }
    if live.get("constraints"):
        result["constraints"] = copy.deepcopy(live["constraints"])
    if prompt.get("previous_validation_errors"):
        result["previous_validation_errors"] = feedback(
            prompt["previous_validation_errors"],
            has_examples=bool(prompt["allowed_evidence_registry"]["records"]))
    # Request prose can contain pasted QASM/provenance; validated constraints suffice.
    return result


def audit(prompt):
    context = citation_context(prompt)
    from .toon import encode_view, metadata
    text = encode_view(model_input(prompt))
    return {
        "serialization": metadata(), "toon_roundtrip_verified": True,
        "toon_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "revision": REVISION, "response_contract_version": CONTRACT_VERSION,
        "aliases": context.aliases, "citation_context": context.to_dict(),
        "original_sha256": digest(prompt), "model_input_sha256": digest(model_input(prompt)),
        "rag_example_count": len(context.record_ids),
        "omissions": ["qasm2", "provenance", "source_identifiers", "duplicated_evidence"],
        "roundtrip_verified": False,
    }

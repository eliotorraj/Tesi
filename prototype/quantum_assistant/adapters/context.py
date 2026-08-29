"""Prompt-safe Dataset retrieval and structured prompt construction."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

from qiskit_dataset.catalog import load_catalog

from ..models import (
    CompatibilityView,
    ParsedRequest,
    PromptEnvelope,
    RetrievedExample,
)


QISKIT_CATALOG = load_catalog()


def _feature_distance(
    query: Mapping[str, float],
    candidate: Mapping[str, Any],
) -> float | None:
    """Return a scale-tolerant mean feature distance."""
    if set(query) - set(candidate):
        return None
    distances: list[float] = []
    for name, query_value in query.items():
        try:
            candidate_value = float(candidate[name])
        except (TypeError, ValueError):
            return None
        if not math.isfinite(candidate_value):
            return None
        scale = 1.0 + max(abs(query_value), abs(candidate_value))
        distances.append(abs(query_value - candidate_value) / scale)
    return sum(distances) / len(distances) if distances else 0.0


def _compact_prompt_input(record_input: Mapping[str, Any]) -> dict[str, Any]:
    """Keep historical context compact and free of target/evaluation fields."""
    circuit = record_input.get("circuit") or {}
    features = circuit.get("features") or {}
    backends = record_input.get("compatible_backends") or []
    return {
        "objective": record_input.get("objective"),
        "circuit": {
            "name": circuit.get("name"),
            "summary": circuit.get("summary"),
            "features": {"by_name": features.get("by_name", {})},
        },
        "compatible_backends": [
            {
                "id": backend.get("id"),
                "num_qubits": backend.get("num_qubits"),
                "operation_names": backend.get("operation_names", []),
            }
            for backend in backends
            if isinstance(backend, dict)
        ],
        "user_constraints": record_input.get("user_constraints", {}),
    }


def _compact_rag_example(record: Mapping[str, Any]) -> dict[str, Any]:
    """Keep one labeled RAG example compact but evidence-complete."""
    retrieval_input = record.get("retrieval_input") or {}
    circuit = retrieval_input.get("circuit") or {}
    features = circuit.get("features") or {}
    compatible_devices = retrieval_input.get("compatible_devices") or []
    return {
        "rag_id": record.get("rag_id"),
        "view_scope": record.get("view_scope"),
        "objective": record.get("objective"),
        "input": {
            "circuit": {
                "circuit_id": circuit.get("circuit_id"),
                "benchmark_family": circuit.get("benchmark_family"),
                "generator": circuit.get("generator"),
                "num_qubits": circuit.get("num_qubits"),
                "depth": circuit.get("depth"),
                "size": circuit.get("size"),
                "source_sha256": circuit.get("source_sha256"),
                "features": {"values": features.get("values", {})},
            },
            "compatible_devices": [
                {
                    "device_id": device.get("device_id"),
                    "num_qubits": device.get("num_qubits"),
                    "operation_names": device.get("operation_names", []),
                    "target_sha256": device.get("target_sha256"),
                }
                for device in compatible_devices
                if isinstance(device, Mapping)
            ],
            "user_constraints": retrieval_input.get("user_constraints", {}),
        },
        "label": {
            "selected_device": record.get("selected_device"),
            "top_configurations": record.get("top_configurations", []),
        },
        "claims": record.get("claims", []),
        "evidence": record.get("evidence", []),
        "scientific_caveats": record.get("scientific_caveats", []),
    }


class JsonDatasetContextRetriever:
    """Nearest-example retriever for legacy JSON and labeled RAG JSONL.

    Legacy records preserve the old input-only boundary. New train-only RAG
    records intentionally expose their labeled recommendation, natural-language
    claims, structured evidence, and caveats as historical examples.
    """

    def __init__(self, dataset_path: Path, *, required: bool = False) -> None:
        self._dataset_path = Path(dataset_path)
        self._required = required
        self._records: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        if self._records is not None:
            return self._records
        if not self._dataset_path.is_file():
            if self._required:
                raise FileNotFoundError(
                    f"Dataset LLM non trovato: {self._dataset_path}"
                )
            self._records = []
            return self._records

        text = self._dataset_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            records: list[dict[str, Any]] = []
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"{self._dataset_path}:{line_number}: JSONL non valido."
                    ) from error
                if not isinstance(value, dict):
                    raise ValueError(
                        f"{self._dataset_path}:{line_number}: record non oggetto."
                    )
                records.append(value)
            self._records = records
            return records

        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            self._records = [
                item for item in payload["records"] if isinstance(item, dict)
            ]
        elif isinstance(payload, dict):
            self._records = [payload]
        elif isinstance(payload, list):
            self._records = [item for item in payload if isinstance(item, dict)]
        else:
            raise ValueError(f"Formato Dataset non supportato: {self._dataset_path}.")
        return self._records

    def retrieve(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityView,
        *,
        limit: int,
    ) -> tuple[RetrievedExample, ...]:
        if limit <= 0:
            return ()
        available = set(compatibility.available_device_ids)
        ranked: list[RetrievedExample] = []
        for record in self._load():
            if not isinstance(record, dict):
                continue
            if isinstance(record.get("retrieval_input"), dict):
                retrieval_input = record["retrieval_input"]
                objective = record.get("objective") or {}
                if objective.get("name") != request.figure_of_merit:
                    continue
                circuit = retrieval_input.get("circuit") or {}
                features = (circuit.get("features") or {}).get("values") or {}
                distance = _feature_distance(request.features, features)
                if distance is None:
                    continue
                historical_devices = {
                    str(device.get("device_id"))
                    for device in retrieval_input.get(
                        "compatible_devices", []
                    )
                    if isinstance(device, Mapping)
                }
                selected_device = (
                    record.get("selected_device") or {}
                ).get("device_id")
                if not historical_devices.intersection(available):
                    continue
                if selected_device not in available:
                    continue
                ranked.append(
                    RetrievedExample(
                        record_id=str(record.get("rag_id", "<missing>")),
                        distance=distance,
                        prompt_input=_compact_rag_example(record),
                    )
                )
                continue

            record_input = record.get("input")
            if not isinstance(record_input, dict):
                continue
            objective = record_input.get("objective") or {}
            if objective.get("name") != request.figure_of_merit:
                continue
            circuit = record_input.get("circuit") or {}
            features = (circuit.get("features") or {}).get("by_name") or {}
            distance = _feature_distance(request.features, features)
            if distance is None:
                continue
            historical_backends = {
                str(backend.get("id"))
                for backend in record_input.get("compatible_backends", [])
                if isinstance(backend, dict)
            }
            if not historical_backends.intersection(available):
                continue
            ranked.append(
                RetrievedExample(
                    record_id=str(record.get("record_id", "<missing>")),
                    distance=distance,
                    prompt_input=_compact_prompt_input(record_input),
                )
            )
        ranked.sort(key=lambda item: (item.distance, item.record_id))
        return tuple(ranked[:limit])


class StructuredPromptBuilder:
    """Build the provider-neutral payload consumed by an LLM adapter."""

    def build(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityView,
        examples: Sequence[RetrievedExample],
        *,
        validation_errors: Sequence[str] = (),
    ) -> PromptEnvelope:
        available = [
            {
                "id": profile.device_id,
                "num_qubits": profile.num_qubits,
                "operation_names": profile.operation_names,
                "coupling_edges": profile.coupling_edges,
                "metadata": profile.to_dict()["metadata"],
            }
            for profile in compatibility.available
        ]
        payload = {
            "task": (
                "Recommend one compatible quantum device and an allowlisted "
                "deterministic Qiskit compilation plan."
            ),
            "live_request": {
                "request_id": request.request_id,
                "user_text": request.user_text,
                "figure_of_merit": request.figure_of_merit,
                "constraints": request.constraints,
                "circuit": {
                    "name": request.circuit_name,
                    "format": "OpenQASM 2",
                    "qasm2": request.qasm2,
                    "num_qubits": request.num_qubits,
                    "depth": request.depth,
                    "operation_names": request.operation_names,
                    "features": dict(request.features),
                },
                "compatible_hardware": available,
                "unavailable_hardware": {
                    device_id: list(reasons)
                    for device_id, reasons in compatibility.unavailable.items()
                },
            },
            "retrieved_labeled_examples": [
                {
                    "record_id": example.record_id,
                    "distance": example.distance,
                    "example": example.prompt_input,
                }
                for example in examples
            ],
            "response_contract": {
                "selected_device": "one live_request.compatible_hardware[].id",
                "figure_of_merit": request.figure_of_merit,
                "compiler": "qiskit",
                "qiskit_plan": {
                    "optimization_level": "integer 2|3",
                    "seed_transpiler": "non-negative integer",
                    "layout_method": "null or trivial|dense|sabre",
                    "routing_method": "null or basic|lookahead|sabre",
                },
                "explanation": "non-empty user-facing text",
                "evidence": "list of references to live input or retrieved record ids",
                "warnings": "list of relevant limitations",
            },
            "allowed_qiskit_configurations": [
                configuration.to_dict()
                for configuration in QISKIT_CATALOG.configurations
            ],
            "previous_validation_errors": list(validation_errors),
            "rules": [
                "Return structured JSON only.",
                "Never select unavailable hardware.",
                "Do not invent hardware, scores, pass traces, or measurements.",
                "Historical labels and evidence are examples, not live ground truth.",
                "Cite evidence ids when a historical result supports the explanation.",
                "Respect every scientific caveat attached to retrieved examples.",
                "The final circuit will be produced only by the deterministic compiler.",
            ],
        }
        return PromptEnvelope(payload=payload)

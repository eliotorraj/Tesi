"""Prompt-safe Dataset retrieval and structured prompt construction."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

from ..models import (
    CompatibilityReport,
    ParsedRequest,
    PromptEnvelope,
    RetrievedExample,
)


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


class JsonDatasetContextRetriever:
    """Nearest-example retriever over record.input only.

    The existing Dataset contract marks expected_output as a training target and
    deterministic_ground_truth as evaluation-only. This adapter preserves that
    boundary. A future RAG adapter can implement the same port over a dedicated,
    provenance-rich knowledge index.
    """

    def __init__(self, dataset_path: Path, *, required: bool = False) -> None:
        self._dataset_path = Path(dataset_path)
        self._required = required
        self._payload: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._payload is not None:
            return self._payload
        if not self._dataset_path.is_file():
            if self._required:
                raise FileNotFoundError(
                    f"Dataset LLM non trovato: {self._dataset_path}"
                )
            self._payload = {"records": []}
            return self._payload
        self._payload = json.loads(self._dataset_path.read_text(encoding="utf-8"))
        return self._payload

    def retrieve(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityReport,
        *,
        limit: int,
    ) -> tuple[RetrievedExample, ...]:
        if limit <= 0:
            return ()
        available = set(compatibility.available_device_ids)
        ranked: list[RetrievedExample] = []
        for record in self._load().get("records", []):
            if not isinstance(record, dict):
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
        compatibility: CompatibilityReport,
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
                "metadata": profile.metadata,
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
                    "features": request.features,
                },
                "compatible_hardware": available,
                "unavailable_hardware": compatibility.unavailable,
            },
            "retrieved_dataset_inputs": [
                {
                    "record_id": example.record_id,
                    "distance": example.distance,
                    "input": example.prompt_input,
                }
                for example in examples
            ],
            "response_contract": {
                "selected_device": "one live_request.compatible_hardware[].id",
                "figure_of_merit": request.figure_of_merit,
                "compiler": "qiskit",
                "qiskit_plan": {
                    "optimization_level": "integer 0..3",
                    "seed_transpiler": "non-negative integer",
                    "layout_method": "null or trivial|dense|sabre",
                    "routing_method": "null or basic|lookahead|stochastic|sabre|none",
                },
                "explanation": "non-empty user-facing text",
                "evidence": "list of references to live input or retrieved record ids",
                "warnings": "list of relevant limitations",
            },
            "previous_validation_errors": list(validation_errors),
            "rules": [
                "Return structured JSON only.",
                "Never select unavailable hardware.",
                "Do not invent hardware, scores, pass traces, or measurements.",
                "Historical Dataset inputs are analogies, not live ground truth.",
                "The final circuit will be produced only by the deterministic compiler.",
            ],
        }
        return PromptEnvelope(payload=payload)

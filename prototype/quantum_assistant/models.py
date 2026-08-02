"""Domain models shared by the prototype layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


SUPPORTED_METRICS = ("expected_fidelity", "critical_depth")


@dataclass(frozen=True)
class UiSubmission:
    """Data received from any concrete web, desktop, or CLI UI."""

    request_id: str
    user_text: str
    qasm2: str
    circuit_name: str = "user_circuit"
    figure_of_merit: str = "expected_fidelity"
    allowed_devices: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedRequest:
    """Validated and normalized request produced by the parser."""

    request_id: str
    user_text: str
    circuit_name: str
    qasm2: str
    figure_of_merit: str
    num_qubits: int
    depth: int
    operation_names: tuple[str, ...]
    features: Mapping[str, float]
    allowed_devices: tuple[str, ...]
    constraints: Mapping[str, Any]


@dataclass(frozen=True)
class HardwareProfile:
    """Compact hardware information used before compilation."""

    device_id: str
    num_qubits: int
    operation_names: tuple[str, ...]
    coupling_edges: tuple[tuple[int, int], ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompatibilityReport:
    """Available devices plus explicit reasons for every rejected device."""

    available: tuple[HardwareProfile, ...]
    unavailable: Mapping[str, tuple[str, ...]]

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        return tuple(profile.device_id for profile in self.available)


@dataclass(frozen=True)
class RetrievedExample:
    """One prompt-safe historical example returned by a context provider."""

    record_id: str
    distance: float
    prompt_input: Mapping[str, Any]


@dataclass(frozen=True)
class PromptEnvelope:
    """Provider-neutral structured prompt."""

    payload: Mapping[str, Any]


@dataclass(frozen=True)
class QiskitCompilationPlan:
    """Allowlisted deterministic Qiskit parameters proposed by the LLM."""

    optimization_level: int
    seed_transpiler: int
    layout_method: str | None = None
    routing_method: str | None = None


@dataclass(frozen=True)
class Recommendation:
    """Validated recommendation safe to show in the UI."""

    selected_device: str
    figure_of_merit: str
    qiskit_plan: QiskitCompilationPlan
    explanation: str
    evidence: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating one structured LLM response."""

    is_valid: bool
    recommendation: Recommendation | None = None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationResult:
    """Complete recommendation transaction returned to the UI."""

    request: ParsedRequest
    compatibility: CompatibilityReport
    retrieved_examples: tuple[RetrievedExample, ...]
    recommendation: Recommendation
    attempts: int


@dataclass(frozen=True)
class ApprovedCompilation:
    """Explicit user approval for deterministic compilation."""

    recommendation_result: RecommendationResult
    user_confirmed: bool


@dataclass(frozen=True)
class CompilationArtifact:
    """Deterministic Qiskit compilation returned to the UI."""

    device_id: str
    qasm2: str
    depth: int
    size: int
    operation_counts: Mapping[str, int]
    validation: Mapping[str, Any]
    compiler_metadata: Mapping[str, Any]

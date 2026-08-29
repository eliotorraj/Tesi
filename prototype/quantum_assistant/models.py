"""Domain models shared by the prototype layers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


REQUEST_SCHEMA_VERSION = "1.0.0"
HARDWARE_CATALOG_SCHEMA_VERSION = "1.0.0"
HARDWARE_MASK_SCHEMA_VERSION = "1.0.0"
NO_ELIGIBLE_DEVICE_CODE = "NO_ELIGIBLE_DEVICE"
NO_ELIGIBLE_DEVICE_MESSAGE = (
    "Nessun device soddisfa contemporaneamente tutti i vincoli hard."
)


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _json_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_copy(item) for item in value]
    return value


@dataclass(frozen=True)
class CircuitInput:
    """Circuit fields accepted from the structured UI request."""

    source: str
    name: str = "user_circuit"
    format: str = "openqasm2"

    def to_dict(self) -> dict[str, str]:
        payload = {"format": self.format, "source": self.source}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class DeviceQubitRange:
    """Optional physical-device capacity range selected by the user."""

    minimum: int | None = None
    maximum: int | None = None

    def to_dict(self) -> dict[str, int]:
        payload: dict[str, int] = {}
        if self.minimum is not None:
            payload["min"] = self.minimum
        if self.maximum is not None:
            payload["max"] = self.maximum
        return payload


@dataclass(frozen=True)
class HardwareConstraints:
    """Closed set of hard hardware constraints supported by phase 2."""

    allowed_provider_ids: tuple[str, ...] = ()
    allowed_device_ids: tuple[str, ...] = ()
    device_qubits: DeviceQubitRange | None = None
    required_native_gate_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.allowed_provider_ids:
            payload["allowed_provider_ids"] = list(self.allowed_provider_ids)
        if self.allowed_device_ids:
            payload["allowed_device_ids"] = list(self.allowed_device_ids)
        if self.device_qubits is not None:
            payload["device_qubits"] = self.device_qubits.to_dict()
        if self.required_native_gate_ids:
            payload["required_native_gate_ids"] = list(
                self.required_native_gate_ids
            )
        return payload


@dataclass(frozen=True)
class UserRequest:
    """Syntactically valid request before QASM-derived properties are added."""

    schema_version: str
    request_id: str
    catalog_snapshot_id: str
    circuit: CircuitInput
    figure_of_merit_id: str
    hardware_constraints: HardwareConstraints = field(
        default_factory=HardwareConstraints
    )
    legacy_compatibility: bool = field(default=False, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "catalog_snapshot_id": self.catalog_snapshot_id,
            "circuit": self.circuit.to_dict(),
            "figure_of_merit_id": self.figure_of_merit_id,
            "hardware_constraints": self.hardware_constraints.to_dict(),
        }


@dataclass(frozen=True)
class UiSubmission:
    """Deprecated adapter for callers predating the structured JSON request.

    user_text is ignored and constraints must stay empty. New callers must
    submit UserRequest or a JSON object matching the request schema.
    """

    request_id: str
    user_text: str
    qasm2: str
    circuit_name: str = "user_circuit"
    figure_of_merit: str = "expected_fidelity"
    allowed_devices: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedRequest:
    """Request with deterministic properties derived from OpenQASM 2."""

    user_request: UserRequest
    num_qubits: int
    depth: int
    operation_names: tuple[str, ...]
    features: Mapping[str, float]
    source_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", _deep_freeze(self.features))

    @property
    def request_id(self) -> str:
        return self.user_request.request_id

    @property
    def schema_version(self) -> str:
        return self.user_request.schema_version

    @property
    def catalog_snapshot_id(self) -> str:
        return self.user_request.catalog_snapshot_id

    @property
    def circuit_name(self) -> str:
        return self.user_request.circuit.name

    @property
    def qasm2(self) -> str:
        return self.user_request.circuit.source

    @property
    def figure_of_merit(self) -> str:
        return self.user_request.figure_of_merit_id

    @property
    def hardware_constraints(self) -> HardwareConstraints:
        return self.user_request.hardware_constraints

    @property
    def allowed_devices(self) -> tuple[str, ...]:
        """Backward-compatible view used by the legacy retriever boundary."""
        return self.hardware_constraints.allowed_device_ids

    @property
    def constraints(self) -> Mapping[str, Any]:
        """Backward-compatible structured view; never contains free text."""
        return self.hardware_constraints.to_dict()

    @property
    def user_text(self) -> str:
        """Legacy prompt field intentionally kept empty."""
        return ""


@dataclass(frozen=True)
class NormalizedRequest(ParsedRequest):
    """Semantically validated request tied to one catalog snapshot."""


@dataclass(frozen=True)
class ValidationIssue:
    """Machine-readable validation failure."""

    code: str
    path: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }
        if self.details:
            payload["details"] = _json_copy(self.details)
        return payload


@dataclass(frozen=True)
class ValidationReport:
    """Complete syntax or semantic validation report."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ProviderProfile:
    provider_id: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
        }


@dataclass(frozen=True)
class HardwareProfile:
    """Normalized, target-derived hardware information."""

    device_id: str
    num_qubits: int
    operation_names: tuple[str, ...]
    coupling_edges: tuple[tuple[int, int], ...]
    provider_id: str = "unknown"
    native_gate_ids: tuple[str, ...] = ()
    coupling_type: str = "sparse_directed"
    target_hash: str = ""
    supported_figure_of_merit_ids: tuple[str, ...] = (
        "expected_fidelity",
    )
    allowed_qiskit_configuration_ids: tuple[str, ...] = ()
    target_available: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.device_id or not self.provider_id:
            raise ValueError("device_id e provider_id non possono essere vuoti.")
        if self.num_qubits <= 0:
            raise ValueError("num_qubits deve essere positivo.")
        for label, values in (
            ("operation_names", self.operation_names),
            ("native_gate_ids", self.native_gate_ids),
            ("coupling_edges", self.coupling_edges),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} contiene duplicati.")
        if any(
            source < 0
            or destination < 0
            or source >= self.num_qubits
            or destination >= self.num_qubits
            for source, destination in self.coupling_edges
        ):
            raise ValueError("Il coupling contiene indici di qubit non validi.")
        object.__setattr__(self, "metadata", _deep_freeze(self.metadata))

    @property
    def selectable_native_gate_ids(self) -> tuple[str, ...]:
        """Return only explicitly declared native gates; never infer them."""
        return self.native_gate_ids

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "device_id": self.device_id,
            "provider_id": self.provider_id,
            "num_qubits": self.num_qubits,
            "operation_names": list(self.operation_names),
            "native_gate_ids": list(self.selectable_native_gate_ids),
            "coupling": {
                "type": self.coupling_type,
                "edge_count": len(self.coupling_edges),
                "edges": [list(edge) for edge in self.coupling_edges],
            },
            "supported_figure_of_merit_ids": list(
                self.supported_figure_of_merit_ids
            ),
            "allowed_qiskit_configuration_ids": list(
                self.allowed_qiskit_configuration_ids
            ),
            "target_available": self.target_available,
            "metadata": _json_copy(self.metadata),
        }
        if self.target_hash:
            payload["target_hash"] = self.target_hash
        return payload


@dataclass(frozen=True)
class CompatibilityReport:
    """Legacy compatibility view retained for direct pre-phase-2 callers."""

    available: tuple[HardwareProfile, ...]
    unavailable: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "unavailable", _deep_freeze(self.unavailable))

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        return tuple(profile.device_id for profile in self.available)


@dataclass(frozen=True)
class HardwareCatalogSnapshot:
    """Immutable catalog used by UI, validation, masking, and later LLM stages."""

    schema_version: str
    catalog_snapshot_id: str
    source_kind: str
    configuration_catalog_id: str
    providers: tuple[ProviderProfile, ...]
    devices: tuple[HardwareProfile, ...]
    supported_figure_of_merit_ids: tuple[str, ...]
    qiskit_configuration_ids: tuple[str, ...]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        provider_ids = tuple(provider.provider_id for provider in self.providers)
        device_ids = tuple(device.device_id for device in self.devices)
        if (
            not provider_ids
            or any(not provider_id for provider_id in provider_ids)
            or len(provider_ids) != len(set(provider_ids))
        ):
            raise ValueError("Lo snapshot deve avere provider unici e non vuoti.")
        if (
            not device_ids
            or any(not device_id for device_id in device_ids)
            or len(device_ids) != len(set(device_ids))
        ):
            raise ValueError("Lo snapshot deve avere device unici e non vuoti.")
        if any(device.provider_id not in provider_ids for device in self.devices):
            raise ValueError("Ogni device deve riferirsi a un provider dello snapshot.")
        if (
            not self.qiskit_configuration_ids
            or any(not value for value in self.qiskit_configuration_ids)
            or len(self.qiskit_configuration_ids)
            != len(set(self.qiskit_configuration_ids))
        ):
            raise ValueError(
                "Gli ID di configurazione Qiskit devono essere unici e non vuoti."
            )
        if (
            not self.supported_figure_of_merit_ids
            or len(self.supported_figure_of_merit_ids)
            != len(set(self.supported_figure_of_merit_ids))
        ):
            raise ValueError("Le figure of merit devono essere uniche e non vuote.")
        global_configurations = set(self.qiskit_configuration_ids)
        global_metrics = set(self.supported_figure_of_merit_ids)
        if any(
            not device.allowed_qiskit_configuration_ids
            or not set(device.allowed_qiskit_configuration_ids).issubset(
                global_configurations
            )
            for device in self.devices
        ):
            raise ValueError(
                "Le configurazioni di ogni device devono essere non vuote e "
                "appartenere al catalogo globale."
            )
        if any(
            not device.supported_figure_of_merit_ids
            or not set(device.supported_figure_of_merit_ids).issubset(
                global_metrics
            )
            for device in self.devices
        ):
            raise ValueError(
                "Le figure of merit di ogni device devono appartenere al "
                "catalogo globale."
            )
        if any(
            device.target_available and not device.target_hash
            for device in self.devices
        ):
            raise ValueError("Ogni Target disponibile deve avere un target_hash.")
        if any(
            device.target_available
            and (
                not device.native_gate_ids
                or not set(device.native_gate_ids).issubset(
                    device.operation_names
                )
            )
            for device in self.devices
        ):
            raise ValueError(
                "Ogni Target disponibile deve dichiarare gate nativi "
                "espliciti presenti nelle operation_names."
            )
        object.__setattr__(self, "provenance", _deep_freeze(self.provenance))

    @property
    def device_by_id(self) -> dict[str, HardwareProfile]:
        return {device.device_id: device for device in self.devices}

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(provider.provider_id for provider in self.providers)

    @property
    def native_gate_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    gate
                    for device in self.devices
                    for gate in device.selectable_native_gate_ids
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "catalog_snapshot_id": self.catalog_snapshot_id,
            "source_kind": self.source_kind,
            "configuration_catalog_id": self.configuration_catalog_id,
            "providers": [provider.to_dict() for provider in self.providers],
            "devices": [device.to_dict() for device in self.devices],
            "supported_figure_of_merit_ids": list(
                self.supported_figure_of_merit_ids
            ),
            "qiskit_configuration_ids": list(
                self.qiskit_configuration_ids
            ),
            "provenance": _json_copy(self.provenance),
        }


class DeviceExclusionReason(StrEnum):
    PROVIDER_NOT_ALLOWED = "PROVIDER_NOT_ALLOWED"
    DEVICE_NOT_ALLOWED = "DEVICE_NOT_ALLOWED"
    INSUFFICIENT_QUBITS_FOR_CIRCUIT = "INSUFFICIENT_QUBITS_FOR_CIRCUIT"
    BELOW_USER_MIN_QUBITS = "BELOW_USER_MIN_QUBITS"
    ABOVE_USER_MAX_QUBITS = "ABOVE_USER_MAX_QUBITS"
    MISSING_REQUIRED_NATIVE_GATE = "MISSING_REQUIRED_NATIVE_GATE"
    FIGURE_OF_MERIT_NOT_SUPPORTED = "FIGURE_OF_MERIT_NOT_SUPPORTED"
    TARGET_NOT_AVAILABLE = "TARGET_NOT_AVAILABLE"


@dataclass(frozen=True)
class DeviceExclusionDiagnostic:
    device_id: str
    reason_codes: tuple[DeviceExclusionReason, ...]
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("Una diagnostica deve contenere almeno una ragione.")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("I codici di esclusione devono essere unici.")
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "device_id": self.device_id,
            "reason_codes": [reason.value for reason in self.reason_codes],
        }
        if self.details:
            payload["details"] = _json_copy(self.details)
        return payload


@dataclass(frozen=True)
class HardwareMaskResult:
    """Deterministic mask plus complete exclusion diagnostics."""

    schema_version: str
    catalog_snapshot_id: str
    ordered_device_ids: tuple[str, ...]
    mask: tuple[bool, ...]
    available: tuple[HardwareProfile, ...]
    excluded_devices: tuple[DeviceExclusionDiagnostic, ...]
    effective_min_qubits: int
    normalized_constraints: HardwareConstraints

    def __post_init__(self) -> None:
        if self.effective_min_qubits < 1:
            raise ValueError("effective_min_qubits deve essere positivo.")
        if len(self.ordered_device_ids) != len(self.mask):
            raise ValueError("Mask e ordered_device_ids devono avere pari lunghezza.")
        if any(type(value) is not bool for value in self.mask):
            raise ValueError("La maschera deve contenere soltanto booleani.")
        if len(self.ordered_device_ids) != len(set(self.ordered_device_ids)):
            raise ValueError("ordered_device_ids deve contenere ID unici.")
        true_ids = tuple(
            device_id
            for device_id, is_eligible in zip(
                self.ordered_device_ids, self.mask, strict=True
            )
            if is_eligible
        )
        available_ids = tuple(profile.device_id for profile in self.available)
        if available_ids != true_ids:
            raise ValueError("I bit true devono coincidere con i device disponibili.")
        false_ids = tuple(
            device_id
            for device_id, is_eligible in zip(
                self.ordered_device_ids, self.mask, strict=True
            )
            if not is_eligible
        )
        diagnostic_ids = tuple(
            diagnostic.device_id for diagnostic in self.excluded_devices
        )
        if diagnostic_ids != false_ids:
            raise ValueError("Ogni bit false deve avere una sola diagnostica ordinata.")

    @property
    def eligible_device_ids(self) -> tuple[str, ...]:
        return tuple(profile.device_id for profile in self.available)

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        """Backward-compatible alias used by RAG and LLM validation."""
        return self.eligible_device_ids

    @property
    def unavailable(self) -> Mapping[str, tuple[str, ...]]:
        """Historical diagnostic strings for pre-phase-2 callers only."""
        unavailable: dict[str, tuple[str, ...]] = {}
        user_filter_reasons = {
            DeviceExclusionReason.PROVIDER_NOT_ALLOWED,
            DeviceExclusionReason.DEVICE_NOT_ALLOWED,
        }
        for diagnostic in self.excluded_devices:
            rendered: list[str] = []
            for reason in diagnostic.reason_codes:
                if reason in user_filter_reasons:
                    value = "excluded_by_user"
                elif (
                    reason
                    is DeviceExclusionReason.INSUFFICIENT_QUBITS_FOR_CIRCUIT
                ):
                    circuit_qubits = diagnostic.details.get(
                        "circuit_num_qubits", "unknown"
                    )
                    device_qubits = diagnostic.details.get(
                        "device_num_qubits", "unknown"
                    )
                    value = (
                        f"insufficient_qubits:{circuit_qubits}>"
                        f"{device_qubits}"
                    )
                else:
                    value = reason.value.lower()
                if value not in rendered:
                    rendered.append(value)
            unavailable[diagnostic.device_id] = tuple(rendered)
        return unavailable

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "catalog_snapshot_id": self.catalog_snapshot_id,
            "ordered_device_ids": list(self.ordered_device_ids),
            "mask": list(self.mask),
            "eligible_device_ids": list(self.eligible_device_ids),
            "excluded_devices": [
                diagnostic.to_dict() for diagnostic in self.excluded_devices
            ],
            "effective_min_qubits": self.effective_min_qubits,
            "normalized_constraints": self.normalized_constraints.to_dict(),
        }


CompatibilityView = CompatibilityReport | HardwareMaskResult


@dataclass(frozen=True)
class PreparedRequestContext:
    """Boundary result produced before any retrieval or LLM call."""

    request: NormalizedRequest
    hardware_catalog: HardwareCatalogSnapshot
    mask_result: HardwareMaskResult

    @property
    def can_recommend(self) -> bool:
        return bool(self.mask_result.eligible_device_ids)

    @property
    def status(self) -> str:
        return "ready" if self.can_recommend else "no_eligible_device"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "can_recommend": self.can_recommend,
            "request": self.request.user_request.to_dict(),
            "derived_circuit": {
                "source_sha256": self.request.source_sha256,
                "num_qubits": self.request.num_qubits,
                "depth": self.request.depth,
                "operation_names": list(self.request.operation_names),
            },
            "mask_result": self.mask_result.to_dict(),
        }
        if not self.can_recommend:
            payload["terminal_error"] = {
                "code": NO_ELIGIBLE_DEVICE_CODE,
                "retryable": False,
                "message": NO_ELIGIBLE_DEVICE_MESSAGE,
            }
        return payload


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

    request: NormalizedRequest
    compatibility: CompatibilityView
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

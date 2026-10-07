'Domain models shared by the prototype layers.'

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


REQUEST_SCHEMA_VERSION = "1.0.0"
HARDWARE_CATALOG_SCHEMA_VERSION = "2.0.0"
HARDWARE_MASK_SCHEMA_VERSION = "1.0.0"
LLM_RECOMMENDATION_SCHEMA_VERSION = "2.0.0"
NO_ELIGIBLE_DEVICE_CODE = "NO_ELIGIBLE_DEVICE"
NO_ELIGIBLE_DEVICE_MESSAGE = (
    'No device satisfies all hard constraints.'
)


def _deep_freeze(value: Any) -> Any:
    'Recursively convert lists and mappings into immutable values.'
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _json_copy(value: Any) -> Any:
    'Create a copy containing JSON-serializable values only.'
    if isinstance(value, Mapping):
        return {str(key): _json_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_copy(item) for item in value]
    return value


@dataclass(frozen=True)
class CircuitInput:
    'Circuit fields accepted by a structured request.'

    source: str
    name: str = "user_circuit"
    format: str = "openqasm2"

    def to_dict(self) -> dict[str, str]:
        'Return the circuit in the schema-defined format.'
        payload = {"format": self.format, "source": self.source}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class DeviceQubitRange:
    'Optional user-selected range of physical qubits.'

    minimum: int | None = None
    maximum: int | None = None

    def to_dict(self) -> dict[str, int]:
        'Return only explicitly specified bounds.'
        payload: dict[str, int] = {}
        if self.minimum is not None:
            payload["min"] = self.minimum
        if self.maximum is not None:
            payload["max"] = self.maximum
        return payload


@dataclass(frozen=True)
class HardwareConstraints:
    'Hard hardware constraints supported by the prototype.'

    allowed_provider_ids: tuple[str, ...] = ()
    allowed_device_ids: tuple[str, ...] = ()
    device_qubits: DeviceQubitRange | None = None
    required_native_gate_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        'Return only user-specified constraints.'
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
    'Structurally valid request before QASM-derived data are added.'

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
        'Return the request in the schema-defined format.'
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
    """Adapter retained for callers predating the JSON request.

    ``user_text`` is ignored and ``constraints`` must remain empty. New callers
    must send ``UserRequest`` or an object conforming to the schema.
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
    'Request enriched with properties derived from OpenQASM 2.'

    user_request: UserRequest
    num_qubits: int
    depth: int
    operation_names: tuple[str, ...]
    features: Mapping[str, float]
    source_sha256: str

    def __post_init__(self) -> None:
        'Make circuit features immutable.'
        object.__setattr__(self, "features", _deep_freeze(self.features))

    @property
    def request_id(self) -> str:
        'Return the original request identifier.'
        return self.user_request.request_id

    @property
    def schema_version(self) -> str:
        'Return the request schema version.'
        return self.user_request.schema_version

    @property
    def catalog_snapshot_id(self) -> str:
        'Return the requested hardware snapshot.'
        return self.user_request.catalog_snapshot_id

    @property
    def circuit_name(self) -> str:
        'Return the assigned circuit name.'
        return self.user_request.circuit.name

    @property
    def qasm2(self) -> str:
        "Return the circuit's OpenQASM 2 source."
        return self.user_request.circuit.source

    @property
    def figure_of_merit(self) -> str:
        'Return the selected compilation evaluation metric.'
        return self.user_request.figure_of_merit_id

    @property
    def hardware_constraints(self) -> HardwareConstraints:
        "Return the request's hardware constraints."
        return self.user_request.hardware_constraints

    @property
    def allowed_devices(self) -> tuple[str, ...]:
        'Return the allowlist retained for compatibility.'
        return self.hardware_constraints.allowed_device_ids

    @property
    def constraints(self) -> Mapping[str, Any]:
        'Return the structured view retained for compatibility.'
        return self.hardware_constraints.to_dict()

    @property
    def user_text(self) -> str:
        'Return an empty legacy message text field.'
        return ""


@dataclass(frozen=True)
class NormalizedRequest(ParsedRequest):
    'Validated request tied to a specific hardware snapshot.'


@dataclass(frozen=True)
class ValidationIssue:
    'Machine-readable validation error.'

    code: str
    path: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        'Make error details immutable.'
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        'Return the error in a serializable form.'
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
    'Complete syntactic or semantic validation report.'

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        'Indicate whether no errors were found.'
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        'Return the report in serializable form.'
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ProviderProfile:
    'Describe a provider in the hardware catalog.'

    provider_id: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        'Return the provider in serializable form.'
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
        }


@dataclass(frozen=True)
class HardwareProfile:
    'Normalized hardware information extracted from the Target.'

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
        'Check profile consistency and freeze its metadata.'
        if not self.device_id or not self.provider_id:
            raise ValueError('device_id and provider_id cannot be empty.')
        if self.num_qubits <= 0:
            raise ValueError('num_qubits must be positive.')
        for label, values in (
            ("operation_names", self.operation_names),
            ("native_gate_ids", self.native_gate_ids),
            ("coupling_edges", self.coupling_edges),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f'{label} contains duplicates.')
        if any(
            source < 0
            or destination < 0
            or source >= self.num_qubits
            or destination >= self.num_qubits
            for source, destination in self.coupling_edges
        ):
            raise ValueError('Coupling contains invalid qubit indices.')
        object.__setattr__(self, "metadata", _deep_freeze(self.metadata))

    @property
    def selectable_native_gate_ids(self) -> tuple[str, ...]:
        'Return only explicitly declared native gates.'
        return self.native_gate_ids

    def to_dict(self) -> dict[str, Any]:
        'Return the hardware profile in serializable form.'
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
    'Compatibility view retained for earlier callers.'

    available: tuple[HardwareProfile, ...]
    unavailable: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        'Make excluded-device diagnostics immutable.'
        object.__setattr__(self, "unavailable", _deep_freeze(self.unavailable))

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        'Return the available device identifiers.'
        return tuple(profile.device_id for profile in self.available)


@dataclass(frozen=True)
class HardwareCatalogSnapshot:
    'Immutable catalog shared by the UI, mask and LLM stages.'

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
        'Check consistency of providers, devices and configurations.'
        provider_ids = tuple(provider.provider_id for provider in self.providers)
        device_ids = tuple(device.device_id for device in self.devices)
        if (
            not provider_ids
            or any(not provider_id for provider_id in provider_ids)
            or len(provider_ids) != len(set(provider_ids))
        ):
            raise ValueError('The snapshot must contain unique, nonempty providers.')
        if (
            not device_ids
            or any(not device_id for device_id in device_ids)
            or len(device_ids) != len(set(device_ids))
        ):
            raise ValueError('The snapshot must contain unique, nonempty devices.')
        if any(device.provider_id not in provider_ids for device in self.devices):
            raise ValueError('Each device must reference a provider in the snapshot.')
        if (
            not self.qiskit_configuration_ids
            or any(not value for value in self.qiskit_configuration_ids)
            or len(self.qiskit_configuration_ids)
            != len(set(self.qiskit_configuration_ids))
        ):
            raise ValueError(
                'Qiskit configuration IDs must be unique and nonempty.'
            )
        if (
            not self.supported_figure_of_merit_ids
            or len(self.supported_figure_of_merit_ids)
            != len(set(self.supported_figure_of_merit_ids))
        ):
            raise ValueError('Figures of merit must be unique and nonempty.')
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
                'Each device must have nonempty configurations belonging to the global catalog.'
            )
        if any(
            not device.supported_figure_of_merit_ids
            or not set(device.supported_figure_of_merit_ids).issubset(
                global_metrics
            )
            for device in self.devices
        ):
            raise ValueError(
                "Each device's figures of merit must belong to the global catalog."
            )
        if any(
            device.target_available and not device.target_hash
            for device in self.devices
        ):
            raise ValueError('Every available Target must have a target_hash.')
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
                'Every available Target must declare explicit native gates present in operation_names.'
            )
        object.__setattr__(self, "provenance", _deep_freeze(self.provenance))

    @property
    def device_by_id(self) -> dict[str, HardwareProfile]:
        'Index hardware profiles by identifier.'
        return {device.device_id: device for device in self.devices}

    @property
    def provider_ids(self) -> tuple[str, ...]:
        'Return the available provider identifiers.'
        return tuple(provider.provider_id for provider in self.providers)

    @property
    def native_gate_ids(self) -> tuple[str, ...]:
        'Collect native gates declared by devices.'
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
        'Return the hardware snapshot in a serializable form.'
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
    'Stable reasons why a device fails the mask.'

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
    'Describe why a device was excluded.'

    device_id: str
    reason_codes: tuple[DeviceExclusionReason, ...]
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        'Check reasons and make details immutable.'
        if not self.reason_codes:
            raise ValueError('A diagnostic must contain at least one reason.')
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError('Exclusion codes must be unique.')
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        'Return diagnostics in a serializable form.'
        payload: dict[str, Any] = {
            "device_id": self.device_id,
            "reason_codes": [reason.value for reason in self.reason_codes],
        }
        if self.details:
            payload["details"] = _json_copy(self.details)
        return payload


@dataclass(frozen=True)
class HardwareMaskResult:
    'Deterministic mask with exclusion diagnostics.'

    schema_version: str
    catalog_snapshot_id: str
    ordered_device_ids: tuple[str, ...]
    mask: tuple[bool, ...]
    available: tuple[HardwareProfile, ...]
    excluded_devices: tuple[DeviceExclusionDiagnostic, ...]
    effective_min_qubits: int
    normalized_constraints: HardwareConstraints

    def __post_init__(self) -> None:
        'Check that mask, profiles and diagnostics agree.'
        if self.effective_min_qubits < 1:
            raise ValueError('effective_min_qubits must be positive.')
        if len(self.ordered_device_ids) != len(self.mask):
            raise ValueError('Mask and ordered_device_ids must have equal lengths.')
        if any(type(value) is not bool for value in self.mask):
            raise ValueError('The mask must contain booleans only.')
        if len(self.ordered_device_ids) != len(set(self.ordered_device_ids)):
            raise ValueError('ordered_device_ids must contain unique IDs.')
        true_ids = tuple(
            device_id
            for device_id, is_eligible in zip(
                self.ordered_device_ids, self.mask, strict=True
            )
            if is_eligible
        )
        available_ids = tuple(profile.device_id for profile in self.available)
        if available_ids != true_ids:
            raise ValueError('True bits must match the available devices.')
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
            raise ValueError('Each false bit must have exactly one ordered diagnostic.')

    @property
    def eligible_device_ids(self) -> tuple[str, ...]:
        'Return devices satisfying every constraint.'
        return tuple(profile.device_id for profile in self.available)

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        'Retain the legacy name used by retrieval and validation.'
        return self.eligible_device_ids

    @property
    def unavailable(self) -> Mapping[str, tuple[str, ...]]:
        'Return legacy text diagnostics for compatibility.'
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
        'Return the mask and diagnostics in a serializable form.'
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
    'Result produced before retrieval and the LLM call.'

    request: NormalizedRequest
    hardware_catalog: HardwareCatalogSnapshot
    mask_result: HardwareMaskResult

    @property
    def can_recommend(self) -> bool:
        'Indicate whether at least one usable device exists.'
        return bool(self.mask_result.eligible_device_ids)

    @property
    def status(self) -> str:
        'Return a summary of preparation status.'
        return "ready" if self.can_recommend else "no_eligible_device"

    def to_dict(self) -> dict[str, Any]:
        'Return the prepared context in serializable form.'
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
    'Verified historical example returned by context retrieval.'

    record_id: str
    distance: float
    prompt_input: Mapping[str, Any]

    def __post_init__(self) -> None:
        'Make message content immutable.'
        object.__setattr__(self, "prompt_input", _deep_freeze(self.prompt_input))


class EvidenceSourceType(StrEnum):
    'Historical sources the LLM may reference.'

    HISTORICAL_RESULT = "historical_result"
    SCIENTIFIC_CAVEAT = "scientific_caveat"


class SupportedClaimType(StrEnum):
    'Claim types accepted in structured LLM output.'

    HISTORICAL_DEVICE_SUPPORT = "historical_device_support"
    HISTORICAL_CONFIGURATION_SUPPORT = "historical_configuration_support"
    LIVE_COMPATIBILITY = "live_compatibility"
    SCIENTIFIC_CAVEAT = "scientific_caveat"
    HISTORICAL_EVIDENCE_UNAVAILABLE = "historical_evidence_unavailable"


class HistoricalClaimType(StrEnum):
    'Claim types present in a labeled historical record.'

    SELECTED_DEVICE = "selected_device"
    RANKED_CONFIGURATION = "ranked_configuration"


@dataclass(frozen=True)
class HistoricalEvidence:
    'Historical outcome that can support a recommendation claim.'

    evidence_id: str
    device_id: str
    configuration_id: str
    metric: str
    value: float
    summary_id: str | None = None
    sample_count: int | None = None

    def __post_init__(self) -> None:
        'Check identifiers, metric and sample count.'
        if not all(
            value.strip()
            for value in (
                self.evidence_id,
                self.device_id,
                self.configuration_id,
                self.metric,
            )
        ):
            raise ValueError(
                'Evidence identifiers cannot be empty.'
            )
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(float(self.value))
        ):
            raise ValueError('The evidence value must be finite.')
        object.__setattr__(self, "value", float(self.value))
        if self.summary_id is not None and not self.summary_id.strip():
            raise ValueError('summary_id cannot contain only whitespace.')
        if self.sample_count is not None and (
            isinstance(self.sample_count, bool)
            or not isinstance(self.sample_count, int)
            or self.sample_count <= 0
        ):
            raise ValueError('sample_count must be a positive integer.')

    def to_dict(self) -> dict[str, Any]:
        'Return historical evidence in a serializable form.'
        payload: dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "device_id": self.device_id,
            "configuration_id": self.configuration_id,
            "metric": self.metric,
            "value": self.value,
        }
        if self.summary_id is not None:
            payload["summary_id"] = self.summary_id
        if self.sample_count is not None:
            payload["sample_count"] = self.sample_count
        return payload


@dataclass(frozen=True)
class ScientificCaveat:
    'Scientific limitation associated with a historical record.'

    caveat_id: str
    text: str

    def __post_init__(self) -> None:
        'Check that identifier and text are nonempty.'
        if not self.caveat_id.strip() or not self.text.strip():
            raise ValueError(
                'Caveat ID and text cannot be empty.'
            )

    def to_dict(self) -> dict[str, str]:
        'Return the caveat in a serializable form.'
        return {"caveat_id": self.caveat_id, "text": self.text}


@dataclass(frozen=True)
class HistoricalClaim:
    'Source claim retained in a historical Dataset record.'

    claim_id: str
    claim_type: HistoricalClaimType
    evidence_ids: tuple[str, ...]
    caveat_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        'Check the type, evidence and caveats cited by the claim.'
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "caveat_ids", tuple(self.caveat_ids))
        if not self.claim_id.strip():
            raise ValueError('Historical claim_id cannot be empty.')
        if not isinstance(self.claim_type, HistoricalClaimType):
            object.__setattr__(
                self,
                "claim_type",
                HistoricalClaimType(self.claim_type),
            )
        for label, values in (
            ("evidence_ids", self.evidence_ids),
            ("caveat_ids", self.caveat_ids),
        ):
            if not values or any(not value.strip() for value in values):
                raise ValueError(f'{label} must contain nonempty IDs.')
            if len(values) != len(set(values)):
                raise ValueError(f'{label} cannot contain duplicates.')

    def to_dict(self) -> dict[str, Any]:
        'Return the historical claim in serializable form.'
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "evidence_ids": list(self.evidence_ids),
            "caveat_ids": list(self.caveat_ids),
        }


@dataclass(frozen=True)
class HistoricalConfiguration:
    'Ranked configuration in a historical record.'

    rank: int
    device_id: str
    configuration_id: str
    claim_id: str
    evidence_id: str
    optimization_level: int
    layout_method: str | None
    routing_method: str | None
    summary_id: str
    median_score: float

    def __post_init__(self) -> None:
        'Check configuration rank, identifiers and values.'
        if self.rank <= 0:
            raise ValueError('Configuration rank must be positive.')
        if not all(
            value.strip()
            for value in (
                self.device_id,
                self.configuration_id,
                self.claim_id,
                self.evidence_id,
                self.summary_id,
            )
        ):
            raise ValueError(
                'Configuration identifiers cannot be empty.'
            )
        if self.optimization_level not in (2, 3):
            raise ValueError('Historical optimization_level must be 2 or 3.')
        if (
            isinstance(self.median_score, bool)
            or not isinstance(self.median_score, (int, float))
            or not math.isfinite(float(self.median_score))
        ):
            raise ValueError('Historical median_score must be finite.')
        object.__setattr__(self, "median_score", float(self.median_score))
        for field_name in ("layout_method", "routing_method"):
            value = getattr(self, field_name)
            if value is not None and not value.strip():
                raise ValueError(
                    f'{field_name} cannot contain only whitespace.'
                )

    def to_dict(self) -> dict[str, Any]:
        'Return the historical configuration in serializable form.'
        return {
            "rank": self.rank,
            "device_id": self.device_id,
            "configuration_id": self.configuration_id,
            "claim_id": self.claim_id,
            "evidence_id": self.evidence_id,
            "optimization_level": self.optimization_level,
            "layout_method": self.layout_method,
            "routing_method": self.routing_method,
            "summary_id": self.summary_id,
            "median_score": self.median_score,
        }


@dataclass(frozen=True)
class EvidenceRecord:
    'Evidence view for a retrieved historical circuit.'

    record_id: str
    rank: int
    distance: float
    selected_device_id: str
    source_claims: tuple[HistoricalClaim, ...]
    top_configurations: tuple[HistoricalConfiguration, ...]
    evidence: tuple[HistoricalEvidence, ...]
    caveats: tuple[ScientificCaveat, ...]

    def __post_init__(self) -> None:
        'Check record ordering, uniqueness and internal links.'
        object.__setattr__(self, "source_claims", tuple(self.source_claims))
        object.__setattr__(
            self,
            "top_configurations",
            tuple(self.top_configurations),
        )
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "caveats", tuple(self.caveats))
        if not all(
            (
                self.source_claims,
                self.top_configurations,
                self.evidence,
                self.caveats,
            )
        ):
            raise ValueError(
                'A historical record must contain claims, configurations, evidence and caveats.'
            )
        if not self.record_id.strip() or not self.selected_device_id.strip():
            raise ValueError(
                'Historical record and device cannot be empty.'
            )
        if self.rank <= 0:
            raise ValueError('Record rank must be positive.')
        if (
            isinstance(self.distance, bool)
            or not isinstance(self.distance, (int, float))
            or not math.isfinite(float(self.distance))
            or self.distance < 0
        ):
            raise ValueError(
                'Record distance must be finite and nonnegative.'
            )
        object.__setattr__(self, "distance", float(self.distance))

        identifiers = (
            ("claim_id", tuple(item.claim_id for item in self.source_claims)),
            (
                "configuration rank",
                tuple(item.rank for item in self.top_configurations),
            ),
            (
                "evidence_id",
                tuple(item.evidence_id for item in self.evidence),
            ),
            ("caveat_id", tuple(item.caveat_id for item in self.caveats)),
        )
        for label, values in identifiers:
            if len(values) != len(set(values)):
                raise ValueError(
                    f'A record cannot contain {label} duplicates.'
                )
        if tuple(
            item.rank for item in self.top_configurations
        ) != tuple(sorted(item.rank for item in self.top_configurations)):
            raise ValueError(
                'Historical configurations must follow rank order.'
            )

        evidence_ids = {item.evidence_id for item in self.evidence}
        caveat_ids = {item.caveat_id for item in self.caveats}
        claim_ids = {item.claim_id for item in self.source_claims}
        for claim in self.source_claims:
            if not set(claim.evidence_ids).issubset(evidence_ids):
                raise ValueError(
                    'A historical claim cites evidence absent from its record.'
                )
            if not set(claim.caveat_ids).issubset(caveat_ids):
                raise ValueError(
                    'A historical claim cites caveats missing from the record.'
                )
        for configuration in self.top_configurations:
            if configuration.claim_id not in claim_ids:
                raise ValueError(
                    'A historical configuration cites a missing claim.'
                )
            if configuration.evidence_id not in evidence_ids:
                raise ValueError(
                    'A historical configuration cites missing evidence.'
                )

    def to_dict(self) -> dict[str, Any]:
        'Return the evidence record in serializable form.'
        return {
            "record_id": self.record_id,
            "rank": self.rank,
            "distance": self.distance,
            "selected_device_id": self.selected_device_id,
            "source_claims": [
                claim.to_dict() for claim in self.source_claims
            ],
            "top_configurations": [
                configuration.to_dict()
                for configuration in self.top_configurations
            ],
            "evidence": [item.to_dict() for item in self.evidence],
            "caveats": [caveat.to_dict() for caveat in self.caveats],
        }

    def find_claim(self, claim_id: str) -> HistoricalClaim | None:
        'Find a source claim by identifier.'
        return next(
            (
                claim
                for claim in self.source_claims
                if claim.claim_id == claim_id
            ),
            None,
        )

    def find_configuration(
        self,
        configuration_id: str,
        *,
        device_id: str | None = None,
    ) -> HistoricalConfiguration | None:
        'Find a configuration, optionally filtering by device.'
        return next(
            (
                configuration
                for configuration in self.top_configurations
                if configuration.configuration_id == configuration_id
                and (
                    device_id is None
                    or configuration.device_id == device_id
                )
            ),
            None,
        )

    def find_evidence(self, evidence_id: str) -> HistoricalEvidence | None:
        'Find historical evidence by identifier.'
        return next(
            (
                item
                for item in self.evidence
                if item.evidence_id == evidence_id
            ),
            None,
        )

    def find_caveat(self, caveat_id: str) -> ScientificCaveat | None:
        'Find a scientific caveat by identifier.'
        return next(
            (
                item
                for item in self.caveats
                if item.caveat_id == caveat_id
            ),
            None,
        )


@dataclass(frozen=True)
class EvidenceReference:
    'LLM reference to an entry in the current registry.'

    reference_id: str
    record_id: str
    source_type: EvidenceSourceType
    source_id: str
    source_claim_id: str | None = None

    def __post_init__(self) -> None:
        'Check identifiers and normalize source type.'
        if not all(
            value.strip()
            for value in (self.reference_id, self.record_id, self.source_id)
        ):
            raise ValueError(
                'Reference identifiers cannot be empty.'
            )
        if (
            self.source_claim_id is not None
            and not self.source_claim_id.strip()
        ):
            raise ValueError(
                'source_claim_id cannot contain only whitespace.'
            )
        if not isinstance(self.source_type, EvidenceSourceType):
            object.__setattr__(
                self,
                "source_type",
                EvidenceSourceType(self.source_type),
            )

    def to_dict(self) -> dict[str, str]:
        'Return the reference in serializable form.'
        payload = {
            "reference_id": self.reference_id,
            "record_id": self.record_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
        }
        if self.source_claim_id is not None:
            payload["source_claim_id"] = self.source_claim_id
        return payload


EvidenceSource = HistoricalEvidence | ScientificCaveat


@dataclass(frozen=True)
class EvidenceRegistry:
    'Immutable registry built from the retrieved examples.'

    records: tuple[EvidenceRecord, ...] = ()

    def __post_init__(self) -> None:
        'Check uniqueness and ordering of retrieved records.'
        object.__setattr__(self, "records", tuple(self.records))
        record_ids = tuple(record.record_id for record in self.records)
        ranks = tuple(record.rank for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(
                'The registry cannot contain duplicate record_id values.'
            )
        if len(ranks) != len(set(ranks)):
            raise ValueError('The registry cannot contain duplicate ranks.')
        if ranks != tuple(sorted(ranks)):
            raise ValueError(
                'Registry records must follow rank order.'
            )

    def to_dict(self) -> dict[str, Any]:
        'Return the registry in serializable form.'
        return {
            "records": [record.to_dict() for record in self.records],
        }

    def find_record(self, record_id: str) -> EvidenceRecord | None:
        'Find a retrieved record by identifier.'
        return next(
            (
                record
                for record in self.records
                if record.record_id == record_id
            ),
            None,
        )

    def resolve(
        self,
        reference: EvidenceReference,
    ) -> EvidenceSource | None:
        'Resolve a reference to its evidence or caveat.'
        record = self.find_record(reference.record_id)
        if record is None:
            return None
        if reference.source_type is EvidenceSourceType.HISTORICAL_RESULT:
            return record.find_evidence(reference.source_id)
        if reference.source_type is EvidenceSourceType.SCIENTIFIC_CAVEAT:
            return record.find_caveat(reference.source_id)
        return None


@dataclass(frozen=True)
class ClaimParameters:
    'Optional identifiers interpreted according to claim type.'

    device_id: str | None = None
    configuration_id: str | None = None
    caveat_id: str | None = None

    def __post_init__(self) -> None:
        'Reject supplied but empty parameters.'
        for field_name in (
            "device_id",
            "configuration_id",
            "caveat_id",
        ):
            value = getattr(self, field_name)
            if value is not None and not value.strip():
                raise ValueError(
                    f'{field_name} cannot contain only whitespace.'
                )

    def to_dict(self) -> dict[str, str]:
        'Return only supplied parameters.'
        payload: dict[str, str] = {}
        for field_name in (
            "device_id",
            "configuration_id",
            "caveat_id",
        ):
            value = getattr(self, field_name)
            if value is not None:
                payload[field_name] = value
        return payload


@dataclass(frozen=True)
class SupportedClaim:
    'Structured claim verifiable without free text.'

    claim_id: str
    claim_type: SupportedClaimType
    parameters: ClaimParameters
    evidence_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        "Check the claim's type, identifier and references."
        object.__setattr__(
            self,
            "evidence_ref_ids",
            tuple(self.evidence_ref_ids),
        )
        if not self.claim_id.strip():
            raise ValueError('claim_id cannot be empty.')
        if not isinstance(self.claim_type, SupportedClaimType):
            object.__setattr__(
                self,
                "claim_type",
                SupportedClaimType(self.claim_type),
            )
        if len(self.evidence_ref_ids) != len(set(self.evidence_ref_ids)):
            raise ValueError(
                'A claim cannot repeat the same reference.'
            )
        if any(
            not reference_id.strip()
            for reference_id in self.evidence_ref_ids
        ):
            raise ValueError(
                'Reference IDs cannot be empty.'
            )

    def to_dict(self) -> dict[str, Any]:
        'Return the validated claim in serializable form.'
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "parameters": self.parameters.to_dict(),
            "evidence_ref_ids": list(self.evidence_ref_ids),
        }


@dataclass(frozen=True)
class RenderedExplanation:
    'User-facing text derived only from validated values.'

    explanation: str
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        'Make lists immutable and check the explanation.'
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if not self.explanation.strip():
            raise ValueError('The derived explanation cannot be empty.')


@dataclass(frozen=True)
class PromptEnvelope:
    'Structured message independent of the LLM provider.'

    payload: Mapping[str, Any]


LlmOutput = Mapping[str, Any] | str | bytes


@dataclass(frozen=True)
class QiskitCompilationPlan:
    'Allowed Qiskit parameters proposed by the LLM.'

    optimization_level: int
    seed_transpiler: int
    layout_method: str | None = None
    routing_method: str | None = None


@dataclass(frozen=True)
class ExampleCitation:
    'Citation resolved by the program against the request registry.'

    alias: str
    record_id: str


@dataclass(frozen=True)
class Recommendation:
    'Validated recommendation suitable for display in the UI.'

    selected_device: str
    figure_of_merit: str
    qiskit_plan: QiskitCompilationPlan
    explanation: str
    evidence: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    claims: tuple[SupportedClaim, ...] = ()
    evidence_references: tuple[EvidenceReference, ...] = ()
    schema_version: str = "2.0.0"
    config_id: str | None = None
    claim: str | None = None
    example_citations: tuple[ExampleCitation, ...] = ()
    citation_validation: str | None = None

    def __post_init__(self) -> None:
        'Make evidence, caveats, claims and references immutable.'
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "example_citations", tuple(self.example_citations))
        object.__setattr__(
            self,
            "evidence_references",
            tuple(self.evidence_references),
        )


@dataclass(frozen=True)
class ValidationResult:
    'Validation outcome for a structured LLM response.'

    is_valid: bool
    recommendation: Recommendation | None = None
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        'Check consistency between outcome, recommendation and errors.'
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.is_valid:
            if self.recommendation is None or self.issues:
                raise ValueError(
                    'A valid result requires an error-free recommendation.'
                )
        elif self.recommendation is not None or not self.issues:
            raise ValueError(
                'An invalid result requires at least one structured error.'
            )

    @property
    def errors(self) -> tuple[str, ...]:
        'Return legacy text messages retained for compatibility.'
        return tuple(issue.message for issue in self.issues)


@dataclass(frozen=True)
class RecommendationResult:
    'Complete recommendation result returned to the UI.'

    request: NormalizedRequest
    compatibility: CompatibilityView
    retrieved_examples: tuple[RetrievedExample, ...]
    evidence_registry: EvidenceRegistry
    recommendation: Recommendation
    attempts: int


@dataclass(frozen=True)
class ApprovedCompilation:
    'Explicit user confirmation before compilation.'

    recommendation_result: RecommendationResult
    user_confirmed: bool


@dataclass(frozen=True)
class CompilationArtifact:
    'Qiskit compilation result returned to the UI.'

    device_id: str
    qasm2: str
    depth: int
    size: int
    operation_counts: Mapping[str, int]
    validation: Mapping[str, Any]
    compiler_metadata: Mapping[str, Any]

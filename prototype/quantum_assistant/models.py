"""Modelli del dominio condivisi dai livelli del prototipo."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


REQUEST_SCHEMA_VERSION = "1.0.0"
HARDWARE_CATALOG_SCHEMA_VERSION = "1.0.0"
HARDWARE_MASK_SCHEMA_VERSION = "1.0.0"
LLM_RECOMMENDATION_SCHEMA_VERSION = "2.0.0"
NO_ELIGIBLE_DEVICE_CODE = "NO_ELIGIBLE_DEVICE"
NO_ELIGIBLE_DEVICE_MESSAGE = (
    "Nessun device soddisfa contemporaneamente tutti i vincoli hard."
)


def _deep_freeze(value: Any) -> Any:
    """Converte ricorsivamente liste e mappe in valori non modificabili."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _json_copy(value: Any) -> Any:
    """Crea una copia composta soltanto da valori serializzabili in JSON."""
    if isinstance(value, Mapping):
        return {str(key): _json_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_copy(item) for item in value]
    return value


@dataclass(frozen=True)
class CircuitInput:
    """Campi del circuito accettati dalla richiesta strutturata."""

    source: str
    name: str = "user_circuit"
    format: str = "openqasm2"

    def to_dict(self) -> dict[str, str]:
        """Restituisce il circuito nel formato previsto dallo schema."""
        payload = {"format": self.format, "source": self.source}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class DeviceQubitRange:
    """Intervallo facoltativo di qubit fisici scelto dall'utente."""

    minimum: int | None = None
    maximum: int | None = None

    def to_dict(self) -> dict[str, int]:
        """Restituisce soltanto i limiti effettivamente indicati."""
        payload: dict[str, int] = {}
        if self.minimum is not None:
            payload["min"] = self.minimum
        if self.maximum is not None:
            payload["max"] = self.maximum
        return payload


@dataclass(frozen=True)
class HardwareConstraints:
    """Vincoli hardware rigidi supportati dal prototipo."""

    allowed_provider_ids: tuple[str, ...] = ()
    allowed_device_ids: tuple[str, ...] = ()
    device_qubits: DeviceQubitRange | None = None
    required_native_gate_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Restituisce soltanto i vincoli impostati dall'utente."""
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
    """Richiesta valida nella forma, prima dei dati ricavati dal QASM."""

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
        """Restituisce la richiesta nel formato previsto dallo schema."""
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
    """Adattatore mantenuto per i chiamanti precedenti alla richiesta JSON.

    ``user_text`` viene ignorato e ``constraints`` deve restare vuoto. I nuovi
    chiamanti devono inviare ``UserRequest`` oppure un oggetto conforme allo
    schema.
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
    """Richiesta arricchita con proprietà ricavate da OpenQASM 2."""

    user_request: UserRequest
    num_qubits: int
    depth: int
    operation_names: tuple[str, ...]
    features: Mapping[str, float]
    source_sha256: str

    def __post_init__(self) -> None:
        """Rende non modificabili le caratteristiche del circuito."""
        object.__setattr__(self, "features", _deep_freeze(self.features))

    @property
    def request_id(self) -> str:
        """Restituisce l'identificativo della richiesta originale."""
        return self.user_request.request_id

    @property
    def schema_version(self) -> str:
        """Restituisce la versione dello schema della richiesta."""
        return self.user_request.schema_version

    @property
    def catalog_snapshot_id(self) -> str:
        """Restituisce l'istantanea hardware richiesta."""
        return self.user_request.catalog_snapshot_id

    @property
    def circuit_name(self) -> str:
        """Restituisce il nome assegnato al circuito."""
        return self.user_request.circuit.name

    @property
    def qasm2(self) -> str:
        """Restituisce il sorgente OpenQASM 2 del circuito."""
        return self.user_request.circuit.source

    @property
    def figure_of_merit(self) -> str:
        """Restituisce la misura scelta per valutare la compilazione."""
        return self.user_request.figure_of_merit_id

    @property
    def hardware_constraints(self) -> HardwareConstraints:
        """Restituisce i vincoli hardware della richiesta."""
        return self.user_request.hardware_constraints

    @property
    def allowed_devices(self) -> tuple[str, ...]:
        """Restituisce la lista ammessa mantenuta per compatibilità."""
        return self.hardware_constraints.allowed_device_ids

    @property
    def constraints(self) -> Mapping[str, Any]:
        """Restituisce la vista strutturata mantenuta per compatibilità."""
        return self.hardware_constraints.to_dict()

    @property
    def user_text(self) -> str:
        """Restituisce vuoto il vecchio campo testuale del messaggio."""
        return ""


@dataclass(frozen=True)
class NormalizedRequest(ParsedRequest):
    """Richiesta validata e legata a una precisa istantanea hardware."""


@dataclass(frozen=True)
class ValidationIssue:
    """Errore di validazione leggibile dal programma."""

    code: str
    path: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Rende non modificabili i dettagli dell'errore."""
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        """Restituisce l'errore in forma serializzabile."""
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
    """Rapporto completo della validazione sintattica o semantica."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Indica se non sono stati trovati errori."""
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il rapporto in forma serializzabile."""
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ProviderProfile:
    """Descrive un fornitore presente nel catalogo hardware."""

    provider_id: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        """Restituisce il fornitore in forma serializzabile."""
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
        }


@dataclass(frozen=True)
class HardwareProfile:
    """Informazioni hardware normalizzate e ricavate dal Target."""

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
        """Controlla la coerenza del profilo e ne blocca i metadati."""
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
        """Restituisce soltanto i gate nativi dichiarati esplicitamente."""
        return self.native_gate_ids

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il profilo hardware in forma serializzabile."""
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
    """Vista di compatibilità mantenuta per i chiamanti precedenti."""

    available: tuple[HardwareProfile, ...]
    unavailable: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        """Rende non modificabile la diagnostica dei dispositivi esclusi."""
        object.__setattr__(self, "unavailable", _deep_freeze(self.unavailable))

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        """Restituisce gli identificativi dei dispositivi disponibili."""
        return tuple(profile.device_id for profile in self.available)


@dataclass(frozen=True)
class HardwareCatalogSnapshot:
    """Catalogo immutabile condiviso da UI, maschera e fasi LLM."""

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
        """Controlla che provider, dispositivi e configurazioni siano coerenti."""
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
        """Indicizza i profili hardware per identificativo."""
        return {device.device_id: device for device in self.devices}

    @property
    def provider_ids(self) -> tuple[str, ...]:
        """Restituisce gli identificativi dei fornitori disponibili."""
        return tuple(provider.provider_id for provider in self.providers)

    @property
    def native_gate_ids(self) -> tuple[str, ...]:
        """Raccoglie i gate nativi dichiarati dai dispositivi."""
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
        """Restituisce l'istantanea hardware in forma serializzabile."""
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
    """Motivi stabili per cui un dispositivo non supera la maschera."""

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
    """Descrive perché un dispositivo è stato escluso."""

    device_id: str
    reason_codes: tuple[DeviceExclusionReason, ...]
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Controlla le ragioni e rende non modificabili i dettagli."""
        if not self.reason_codes:
            raise ValueError("Una diagnostica deve contenere almeno una ragione.")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("I codici di esclusione devono essere unici.")
        object.__setattr__(self, "details", _deep_freeze(self.details))

    def to_dict(self) -> dict[str, Any]:
        """Restituisce la diagnostica in forma serializzabile."""
        payload: dict[str, Any] = {
            "device_id": self.device_id,
            "reason_codes": [reason.value for reason in self.reason_codes],
        }
        if self.details:
            payload["details"] = _json_copy(self.details)
        return payload


@dataclass(frozen=True)
class HardwareMaskResult:
    """Maschera deterministica con la diagnostica delle esclusioni."""

    schema_version: str
    catalog_snapshot_id: str
    ordered_device_ids: tuple[str, ...]
    mask: tuple[bool, ...]
    available: tuple[HardwareProfile, ...]
    excluded_devices: tuple[DeviceExclusionDiagnostic, ...]
    effective_min_qubits: int
    normalized_constraints: HardwareConstraints

    def __post_init__(self) -> None:
        """Controlla che maschera, profili e diagnostiche coincidano."""
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
        """Restituisce i dispositivi che hanno superato tutti i vincoli."""
        return tuple(profile.device_id for profile in self.available)

    @property
    def available_device_ids(self) -> tuple[str, ...]:
        """Mantiene il vecchio nome usato da recupero e validazione."""
        return self.eligible_device_ids

    @property
    def unavailable(self) -> Mapping[str, tuple[str, ...]]:
        """Restituisce la vecchia diagnostica testuale per compatibilità."""
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
        """Restituisce maschera e diagnostiche in forma serializzabile."""
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
    """Risultato prodotto prima del recupero e della chiamata all'LLM."""

    request: NormalizedRequest
    hardware_catalog: HardwareCatalogSnapshot
    mask_result: HardwareMaskResult

    @property
    def can_recommend(self) -> bool:
        """Indica se esiste almeno un dispositivo utilizzabile."""
        return bool(self.mask_result.eligible_device_ids)

    @property
    def status(self) -> str:
        """Restituisce lo stato sintetico della preparazione."""
        return "ready" if self.can_recommend else "no_eligible_device"

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il contesto preparato in forma serializzabile."""
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
    """Esempio storico sicuro restituito dal recupero del contesto."""

    record_id: str
    distance: float
    prompt_input: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Rende non modificabile il contenuto destinato al messaggio."""
        object.__setattr__(self, "prompt_input", _deep_freeze(self.prompt_input))


class EvidenceSourceType(StrEnum):
    """Fonti storiche che l'LLM può indicare."""

    HISTORICAL_RESULT = "historical_result"
    SCIENTIFIC_CAVEAT = "scientific_caveat"


class SupportedClaimType(StrEnum):
    """Tipi di claim accettati nell'output strutturato dell'LLM."""

    HISTORICAL_DEVICE_SUPPORT = "historical_device_support"
    HISTORICAL_CONFIGURATION_SUPPORT = "historical_configuration_support"
    LIVE_COMPATIBILITY = "live_compatibility"
    SCIENTIFIC_CAVEAT = "scientific_caveat"
    HISTORICAL_EVIDENCE_UNAVAILABLE = "historical_evidence_unavailable"


class HistoricalClaimType(StrEnum):
    """Tipi di claim presenti in un record storico etichettato."""

    SELECTED_DEVICE = "selected_device"
    RANKED_CONFIGURATION = "ranked_configuration"


@dataclass(frozen=True)
class HistoricalEvidence:
    """Risultato storico che può sostenere un claim della raccomandazione."""

    evidence_id: str
    device_id: str
    configuration_id: str
    metric: str
    value: float
    summary_id: str | None = None
    sample_count: int | None = None

    def __post_init__(self) -> None:
        """Controlla identificativi, misura e quantità di campioni."""
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
                "Gli identificatori dell'evidenza non possono essere vuoti."
            )
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(float(self.value))
        ):
            raise ValueError("Il valore dell'evidenza deve essere finito.")
        object.__setattr__(self, "value", float(self.value))
        if self.summary_id is not None and not self.summary_id.strip():
            raise ValueError("summary_id non può contenere soltanto spazi.")
        if self.sample_count is not None and (
            isinstance(self.sample_count, bool)
            or not isinstance(self.sample_count, int)
            or self.sample_count <= 0
        ):
            raise ValueError("sample_count deve essere un intero positivo.")

    def to_dict(self) -> dict[str, Any]:
        """Restituisce l'evidenza storica in forma serializzabile."""
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
    """Limite scientifico associato a un record storico."""

    caveat_id: str
    text: str

    def __post_init__(self) -> None:
        """Controlla che identificativo e testo non siano vuoti."""
        if not self.caveat_id.strip() or not self.text.strip():
            raise ValueError(
                "ID e testo dell'avvertenza non possono essere vuoti."
            )

    def to_dict(self) -> dict[str, str]:
        """Restituisce l'avvertenza in forma serializzabile."""
        return {"caveat_id": self.caveat_id, "text": self.text}


@dataclass(frozen=True)
class HistoricalClaim:
    """Claim sorgente conservato in un record storico del Dataset."""

    claim_id: str
    claim_type: HistoricalClaimType
    evidence_ids: tuple[str, ...]
    caveat_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Controlla tipo, evidenze e avvertenze citate dal claim."""
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "caveat_ids", tuple(self.caveat_ids))
        if not self.claim_id.strip():
            raise ValueError("claim_id storico non può essere vuoto.")
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
                raise ValueError(f"{label} deve contenere ID non vuoti.")
            if len(values) != len(set(values)):
                raise ValueError(f"{label} non può contenere duplicati.")

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il claim storico in forma serializzabile."""
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "evidence_ids": list(self.evidence_ids),
            "caveat_ids": list(self.caveat_ids),
        }


@dataclass(frozen=True)
class HistoricalConfiguration:
    """Configurazione ordinata presente in un record storico."""

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
        """Controlla rango, identificativi e valori della configurazione."""
        if self.rank <= 0:
            raise ValueError("Il rango della configurazione deve essere positivo.")
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
                "Gli identificatori della configurazione non possono essere vuoti."
            )
        if self.optimization_level not in (2, 3):
            raise ValueError("optimization_level storico deve essere 2 oppure 3.")
        if (
            isinstance(self.median_score, bool)
            or not isinstance(self.median_score, (int, float))
            or not math.isfinite(float(self.median_score))
        ):
            raise ValueError("median_score storico deve essere finito.")
        object.__setattr__(self, "median_score", float(self.median_score))
        for field_name in ("layout_method", "routing_method"):
            value = getattr(self, field_name)
            if value is not None and not value.strip():
                raise ValueError(
                    f"{field_name} non può contenere soltanto spazi."
                )

    def to_dict(self) -> dict[str, Any]:
        """Restituisce la configurazione storica in forma serializzabile."""
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
    """Vista delle evidenze di un circuito storico recuperato."""

    record_id: str
    rank: int
    distance: float
    selected_device_id: str
    source_claims: tuple[HistoricalClaim, ...]
    top_configurations: tuple[HistoricalConfiguration, ...]
    evidence: tuple[HistoricalEvidence, ...]
    caveats: tuple[ScientificCaveat, ...]

    def __post_init__(self) -> None:
        """Controlla ordine, unicità e collegamenti interni del record."""
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
                "Un record storico deve contenere claim, configurazioni, "
                "evidenze e avvertenze."
            )
        if not self.record_id.strip() or not self.selected_device_id.strip():
            raise ValueError(
                "Record e dispositivo storico non possono essere vuoti."
            )
        if self.rank <= 0:
            raise ValueError("Il rango del record deve essere positivo.")
        if (
            isinstance(self.distance, bool)
            or not isinstance(self.distance, (int, float))
            or not math.isfinite(float(self.distance))
            or self.distance < 0
        ):
            raise ValueError(
                "La distanza del record deve essere finita e non negativa."
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
                    f"Un record non può contenere {label} duplicati."
                )
        if tuple(
            item.rank for item in self.top_configurations
        ) != tuple(sorted(item.rank for item in self.top_configurations)):
            raise ValueError(
                "Le configurazioni storiche devono rispettare il rango."
            )

        evidence_ids = {item.evidence_id for item in self.evidence}
        caveat_ids = {item.caveat_id for item in self.caveats}
        claim_ids = {item.claim_id for item in self.source_claims}
        for claim in self.source_claims:
            if not set(claim.evidence_ids).issubset(evidence_ids):
                raise ValueError(
                    "Un claim storico cita evidenze assenti dal record."
                )
            if not set(claim.caveat_ids).issubset(caveat_ids):
                raise ValueError(
                    "Un claim storico cita avvertenze assenti dal record."
                )
        for configuration in self.top_configurations:
            if configuration.claim_id not in claim_ids:
                raise ValueError(
                    "Una configurazione storica cita un claim assente."
                )
            if configuration.evidence_id not in evidence_ids:
                raise ValueError(
                    "Una configurazione storica cita un'evidenza assente."
                )

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il record di evidenze in forma serializzabile."""
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
        """Cerca un claim sorgente per identificativo."""
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
        """Cerca una configurazione, facoltativamente per dispositivo."""
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
        """Cerca un'evidenza storica per identificativo."""
        return next(
            (
                item
                for item in self.evidence
                if item.evidence_id == evidence_id
            ),
            None,
        )

    def find_caveat(self, caveat_id: str) -> ScientificCaveat | None:
        """Cerca un'avvertenza scientifica per identificativo."""
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
    """Riferimento dell'LLM a un elemento del registro corrente."""

    reference_id: str
    record_id: str
    source_type: EvidenceSourceType
    source_id: str
    source_claim_id: str | None = None

    def __post_init__(self) -> None:
        """Controlla gli identificativi e normalizza il tipo di fonte."""
        if not all(
            value.strip()
            for value in (self.reference_id, self.record_id, self.source_id)
        ):
            raise ValueError(
                "Gli identificatori del riferimento non possono essere vuoti."
            )
        if (
            self.source_claim_id is not None
            and not self.source_claim_id.strip()
        ):
            raise ValueError(
                "source_claim_id non può contenere soltanto spazi."
            )
        if not isinstance(self.source_type, EvidenceSourceType):
            object.__setattr__(
                self,
                "source_type",
                EvidenceSourceType(self.source_type),
            )

    def to_dict(self) -> dict[str, str]:
        """Restituisce il riferimento in forma serializzabile."""
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
    """Registro immutabile costruito dagli esempi appena recuperati."""

    records: tuple[EvidenceRecord, ...] = ()

    def __post_init__(self) -> None:
        """Controlla unicità e ordine dei record recuperati."""
        object.__setattr__(self, "records", tuple(self.records))
        record_ids = tuple(record.record_id for record in self.records)
        ranks = tuple(record.rank for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(
                "Il registro non può contenere record_id duplicati."
            )
        if len(ranks) != len(set(ranks)):
            raise ValueError("Il registro non può contenere ranghi duplicati.")
        if ranks != tuple(sorted(ranks)):
            raise ValueError(
                "I record del registro devono rispettare il rango."
            )

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il registro in forma serializzabile."""
        return {
            "records": [record.to_dict() for record in self.records],
        }

    def find_record(self, record_id: str) -> EvidenceRecord | None:
        """Cerca un record recuperato per identificativo."""
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
        """Risolve un riferimento nella relativa evidenza o avvertenza."""
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
    """Identificativi facoltativi interpretati in base al tipo di claim."""

    device_id: str | None = None
    configuration_id: str | None = None
    caveat_id: str | None = None

    def __post_init__(self) -> None:
        """Rifiuta i parametri presenti ma vuoti."""
        for field_name in (
            "device_id",
            "configuration_id",
            "caveat_id",
        ):
            value = getattr(self, field_name)
            if value is not None and not value.strip():
                raise ValueError(
                    f"{field_name} non può contenere soltanto spazi."
                )

    def to_dict(self) -> dict[str, str]:
        """Restituisce soltanto i parametri presenti."""
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
    """Claim strutturato che può essere verificato senza testo libero."""

    claim_id: str
    claim_type: SupportedClaimType
    parameters: ClaimParameters
    evidence_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Controlla tipo, identificativo e riferimenti del claim."""
        object.__setattr__(
            self,
            "evidence_ref_ids",
            tuple(self.evidence_ref_ids),
        )
        if not self.claim_id.strip():
            raise ValueError("claim_id non può essere vuoto.")
        if not isinstance(self.claim_type, SupportedClaimType):
            object.__setattr__(
                self,
                "claim_type",
                SupportedClaimType(self.claim_type),
            )
        if len(self.evidence_ref_ids) != len(set(self.evidence_ref_ids)):
            raise ValueError(
                "Un claim non può ripetere lo stesso riferimento."
            )
        if any(
            not reference_id.strip()
            for reference_id in self.evidence_ref_ids
        ):
            raise ValueError(
                "Gli ID dei riferimenti non possono essere vuoti."
            )

    def to_dict(self) -> dict[str, Any]:
        """Restituisce il claim validato in forma serializzabile."""
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "parameters": self.parameters.to_dict(),
            "evidence_ref_ids": list(self.evidence_ref_ids),
        }


@dataclass(frozen=True)
class RenderedExplanation:
    """Testo per l'utente ricavato soltanto da valori validati."""

    explanation: str
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Rende immutabili le liste e controlla la spiegazione."""
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if not self.explanation.strip():
            raise ValueError("La spiegazione derivata non può essere vuota.")


@dataclass(frozen=True)
class PromptEnvelope:
    """Messaggio strutturato indipendente dal fornitore dell'LLM."""

    payload: Mapping[str, Any]


LlmOutput = Mapping[str, Any] | str | bytes


@dataclass(frozen=True)
class QiskitCompilationPlan:
    """Parametri Qiskit ammessi e proposti dall'LLM."""

    optimization_level: int
    seed_transpiler: int
    layout_method: str | None = None
    routing_method: str | None = None


@dataclass(frozen=True)
class Recommendation:
    """Raccomandazione validata e sicura da mostrare nella UI."""

    selected_device: str
    figure_of_merit: str
    qiskit_plan: QiskitCompilationPlan
    explanation: str
    evidence: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    claims: tuple[SupportedClaim, ...] = ()
    evidence_references: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        """Rende immutabili evidenze, avvertenze, claim e riferimenti."""
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(
            self,
            "evidence_references",
            tuple(self.evidence_references),
        )


@dataclass(frozen=True)
class ValidationResult:
    """Esito della validazione di una risposta strutturata dell'LLM."""

    is_valid: bool
    recommendation: Recommendation | None = None
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        """Controlla la coerenza tra esito, raccomandazione ed errori."""
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.is_valid:
            if self.recommendation is None or self.issues:
                raise ValueError(
                    "Un risultato valido richiede una raccomandazione senza errori."
                )
        elif self.recommendation is not None or not self.issues:
            raise ValueError(
                "Un risultato non valido richiede almeno un errore strutturato."
            )

    @property
    def errors(self) -> tuple[str, ...]:
        """Restituisce i vecchi messaggi testuali mantenuti per compatibilità."""
        return tuple(issue.message for issue in self.issues)


@dataclass(frozen=True)
class RecommendationResult:
    """Risultato completo della raccomandazione restituito alla UI."""

    request: NormalizedRequest
    compatibility: CompatibilityView
    retrieved_examples: tuple[RetrievedExample, ...]
    evidence_registry: EvidenceRegistry
    recommendation: Recommendation
    attempts: int


@dataclass(frozen=True)
class ApprovedCompilation:
    """Conferma esplicita dell'utente prima della compilazione."""

    recommendation_result: RecommendationResult
    user_confirmed: bool


@dataclass(frozen=True)
class CompilationArtifact:
    """Risultato della compilazione Qiskit restituito alla UI."""

    device_id: str
    qasm2: str
    depth: int
    size: int
    operation_counts: Mapping[str, int]
    validation: Mapping[str, Any]
    compiler_metadata: Mapping[str, Any]

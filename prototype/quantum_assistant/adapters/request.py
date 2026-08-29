"""Structured request decoding, QASM parsing, and semantic validation."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Never

from mqt.predictor.ml.helper import create_feature_vector, get_openqasm_gates
from qiskit import QuantumCircuit, qasm2

from ..errors import RequestValidationError
from ..models import (
    REQUEST_SCHEMA_VERSION,
    CircuitInput,
    DeviceQubitRange,
    HardwareCatalogSnapshot,
    HardwareConstraints,
    NormalizedRequest,
    ParsedRequest,
    UserRequest,
    UiSubmission,
    ValidationIssue,
    ValidationReport,
)
from ..schema_validation import (
    MAX_REQUEST_BYTES,
    decode_json_object,
    load_schema,
    validate_instance,
)


REQUEST_SCHEMA = load_schema("assistant_request.schema.json")
LEGACY_CATALOG_SNAPSHOT_ID = "legacy_unspecified"
MAX_CIRCUIT_SOURCE_CHARACTERS = 2_000_000
MAX_IDENTIFIER_ITEMS = 64
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$", flags=re.ASCII)
QELIB1_INCLUDE_ROOT = Path(qasm2.__file__).resolve().parents[1] / "qasm" / "libs"
_BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", flags=re.DOTALL)
_LINE_COMMENT_PATTERN = re.compile(r"//[^\r\n]*")
_ALLOWED_INCLUDE_PATTERN = re.compile(
    r'\binclude\s+"qelib1\.inc"\s*;',
    flags=re.ASCII,
)
GATE_ALIASES = {
    "cnot": "cx",
    "i": "id",
}
FEATURE_NAMES = tuple(
    [f"gate_count_{gate}" for gate in get_openqasm_gates()]
    + [
        "num_qubits",
        "depth",
        "program_communication",
        "critical_depth",
        "entanglement_ratio",
        "parallelism",
        "liveness",
    ]
)
RequestInput = UserRequest | UiSubmission | Mapping[str, Any] | str | bytes


def normalize_gate_id(value: str) -> str:
    normalized = value.strip().lower()
    return GATE_ALIASES.get(normalized, normalized)


def _raise_issue(code: str, path: str, message: str) -> Never:
    raise RequestValidationError(
        ValidationReport((ValidationIssue(code, path, message),))
    )


def _validate_qasm_includes(source: str) -> None:
    """Allow only Qiskit's packaged qelib1; never resolve from the CWD."""
    without_comments = _BLOCK_COMMENT_PATTERN.sub("", source)
    without_comments = _LINE_COMMENT_PATTERN.sub("", without_comments)
    remainder = _ALLOWED_INCLUDE_PATTERN.sub("", without_comments)
    if re.search(r"\binclude\b", remainder, flags=re.ASCII):
        _raise_issue(
            "QASM_INCLUDE_NOT_ALLOWED",
            "$.circuit.source",
            "Sono ammessi soltanto include di qelib1.inc.",
        )


def _extract_feature_values(circuit: QuantumCircuit) -> tuple[float, ...]:
    if circuit.num_qubits < 1:
        _raise_issue(
            "CIRCUIT_HAS_NO_QUBITS",
            "$.circuit.source",
            "Il circuito deve dichiarare almeno un qubit.",
        )
    try:
        raw_values = create_feature_vector(circuit)
        feature_values = tuple(float(value) for value in raw_values)
    except Exception as exc:
        _raise_issue(
            "CIRCUIT_FEATURE_EXTRACTION_FAILED",
            "$.circuit.source",
            (
                "Impossibile estrarre le feature del circuito: "
                f"{type(exc).__name__}: {exc}"
            ),
        )
    if len(feature_values) != len(FEATURE_NAMES):
        _raise_issue(
            "CIRCUIT_FEATURE_VECTOR_SHAPE_INVALID",
            "$.circuit.source",
            (
                f"Feature vector inatteso: {len(feature_values)} valori, "
                f"attesi {len(FEATURE_NAMES)}."
            ),
        )
    if any(not math.isfinite(value) for value in feature_values):
        _raise_issue(
            "CIRCUIT_FEATURES_INVALID",
            "$.circuit.source",
            "L'estrazione ha prodotto feature non finite.",
        )
    return feature_values


def _constraints_from_mapping(raw: Mapping[str, Any]) -> HardwareConstraints:
    qubit_range_raw = raw.get("device_qubits")
    qubit_range = None
    if isinstance(qubit_range_raw, Mapping):
        qubit_range = DeviceQubitRange(
            minimum=qubit_range_raw.get("min"),
            maximum=qubit_range_raw.get("max"),
        )
    return HardwareConstraints(
        allowed_provider_ids=tuple(raw.get("allowed_provider_ids", ())),
        allowed_device_ids=tuple(raw.get("allowed_device_ids", ())),
        device_qubits=qubit_range,
        required_native_gate_ids=tuple(
            raw.get("required_native_gate_ids", ())
        ),
    )


def _user_request_from_mapping(raw: Mapping[str, Any]) -> UserRequest:
    issues = validate_instance(
        REQUEST_SCHEMA,
        raw,
        error_code="REQUEST_SCHEMA_INVALID",
    )
    if issues:
        raise RequestValidationError(ValidationReport(issues))

    circuit = raw["circuit"]
    constraints = raw["hardware_constraints"]
    return UserRequest(
        schema_version=str(raw["schema_version"]),
        request_id=str(raw["request_id"]),
        catalog_snapshot_id=str(raw["catalog_snapshot_id"]),
        circuit=CircuitInput(
            format=str(circuit["format"]),
            name=str(circuit.get("name", "user_circuit")),
            source=str(circuit["source"]),
        ),
        figure_of_merit_id=str(raw["figure_of_merit_id"]),
        hardware_constraints=_constraints_from_mapping(constraints),
    )


def _legacy_request(submission: UiSubmission) -> UserRequest:
    if submission.constraints:
        _raise_issue(
            "LEGACY_CONSTRAINT_NOT_SUPPORTED",
            "$.constraints",
            "Il vecchio campo constraints non è più supportato.",
        )
    if not isinstance(submission.request_id, str) or not submission.request_id.strip():
        _raise_issue(
            "REQUEST_SCHEMA_INVALID",
            "$.request_id",
            "request_id non può essere vuoto.",
        )
    if (
        not isinstance(submission.qasm2, str)
        or not submission.qasm2
        or len(submission.qasm2) > MAX_CIRCUIT_SOURCE_CHARACTERS
    ):
        _raise_issue(
            "REQUEST_SCHEMA_INVALID",
            "$.circuit.source",
            "Il QASM legacy è vuoto o supera il limite ammesso.",
        )
    if (
        not isinstance(submission.circuit_name, str)
        or not 1 <= len(submission.circuit_name) <= 128
    ):
        _raise_issue(
            "REQUEST_SCHEMA_INVALID",
            "$.circuit.name",
            "Il nome circuito legacy deve contenere da 1 a 128 caratteri.",
        )
    allowed_devices = tuple(submission.allowed_devices)
    if (
        len(allowed_devices) > MAX_IDENTIFIER_ITEMS
        or len(allowed_devices) != len(set(allowed_devices))
        or any(
            not isinstance(device_id, str)
            or _IDENTIFIER_PATTERN.fullmatch(device_id) is None
            for device_id in allowed_devices
        )
    ):
        _raise_issue(
            "REQUEST_SCHEMA_INVALID",
            "$.allowed_devices",
            "La allowlist legacy contiene ID non validi o duplicati.",
        )
    return UserRequest(
        schema_version=REQUEST_SCHEMA_VERSION,
        request_id=submission.request_id,
        catalog_snapshot_id=LEGACY_CATALOG_SNAPSHOT_ID,
        circuit=CircuitInput(
            source=submission.qasm2,
            name=submission.circuit_name or "user_circuit",
        ),
        figure_of_merit_id=submission.figure_of_merit,
        hardware_constraints=HardwareConstraints(
            allowed_device_ids=allowed_devices,
        ),
        legacy_compatibility=True,
    )


class QasmRequestParser:
    """Decode strict request JSON and attach deterministic QASM properties."""

    def parse(self, submission: RequestInput) -> ParsedRequest:
        if isinstance(submission, UiSubmission):
            request = _legacy_request(submission)
        elif isinstance(submission, UserRequest):
            # A caller cannot opt into the trusted legacy path by setting the
            # internal marker on a public dataclass instance.
            request = _user_request_from_mapping(submission.to_dict())
        else:
            try:
                raw = (
                    decode_json_object(submission)
                    if isinstance(submission, (str, bytes))
                    else dict(submission)
                )
            except (TypeError, ValueError) as exc:
                _raise_issue(
                    "REQUEST_JSON_INVALID",
                    "$",
                    str(exc),
                )
            request = _user_request_from_mapping(raw)

        if request.figure_of_merit_id != "expected_fidelity":
            _raise_issue(
                "FIGURE_OF_MERIT_NOT_SUPPORTED",
                "$.figure_of_merit_id",
                "Questa versione supporta soltanto expected_fidelity.",
            )
        if not request.circuit.source.strip():
            _raise_issue(
                "REQUEST_SCHEMA_INVALID",
                "$.circuit.source",
                "Il circuito OpenQASM 2 è vuoto.",
            )
        if len(request.circuit.source.encode("utf-8")) > MAX_REQUEST_BYTES:
            _raise_issue(
                "REQUEST_SCHEMA_INVALID",
                "$.circuit.source",
                (
                    "Il circuito supera il limite UTF-8 di "
                    f"{MAX_REQUEST_BYTES} byte."
                ),
            )
        _validate_qasm_includes(request.circuit.source)
        try:
            circuit = qasm2.loads(
                request.circuit.source,
                include_path=(QELIB1_INCLUDE_ROOT,),
            )
        except Exception as exc:
            _raise_issue(
                "QASM_PARSE_FAILED",
                "$.circuit.source",
                f"OpenQASM 2 non valido: {type(exc).__name__}: {exc}",
            )

        feature_values = _extract_feature_values(circuit)
        return ParsedRequest(
            user_request=request,
            num_qubits=int(circuit.num_qubits),
            depth=int(circuit.depth()),
            operation_names=tuple(sorted(map(str, circuit.count_ops()))),
            features={
                name: float(value)
                for name, value in zip(
                    FEATURE_NAMES,
                    feature_values,
                    strict=True,
                )
            },
            source_sha256=hashlib.sha256(
                request.circuit.source.encode("utf-8")
            ).hexdigest(),
        )


class RequestSemanticValidator:
    """Validate catalog-dependent rules and normalize gate aliases."""

    def normalize(
        self,
        request: ParsedRequest,
        catalog: HardwareCatalogSnapshot,
    ) -> NormalizedRequest:
        issues: list[ValidationIssue] = []
        constraints = request.hardware_constraints
        provider_ids = set(catalog.provider_ids)
        devices = catalog.device_by_id
        device_ids = set(devices)
        known_gates = set(catalog.native_gate_ids)

        if (
            not request.user_request.legacy_compatibility
            and request.catalog_snapshot_id != catalog.catalog_snapshot_id
        ):
            issues.append(
                ValidationIssue(
                    "CATALOG_SNAPSHOT_MISMATCH",
                    "$.catalog_snapshot_id",
                    "La richiesta non usa lo snapshot hardware corrente.",
                    {
                        "actual": request.catalog_snapshot_id,
                        "expected": catalog.catalog_snapshot_id,
                    },
                )
            )
        if (
            request.figure_of_merit
            not in catalog.supported_figure_of_merit_ids
        ):
            issues.append(
                ValidationIssue(
                    "FIGURE_OF_MERIT_NOT_SUPPORTED",
                    "$.figure_of_merit_id",
                    "Figure of merit non supportata dal catalogo.",
                )
            )

        for index, provider_id in enumerate(
            constraints.allowed_provider_ids
        ):
            if provider_id not in provider_ids:
                issues.append(
                    ValidationIssue(
                        "UNKNOWN_PROVIDER",
                        f"$.hardware_constraints.allowed_provider_ids[{index}]",
                        f"Provider inesistente: {provider_id!r}.",
                    )
                )

        for index, device_id in enumerate(constraints.allowed_device_ids):
            if device_id not in device_ids:
                issues.append(
                    ValidationIssue(
                        "UNKNOWN_DEVICE",
                        (
                            "$.hardware_constraints."
                            f"allowed_device_ids[{index}]"
                        ),
                        f"Device inesistente: {device_id!r}.",
                    )
                )

        normalized_gates = tuple(
            normalize_gate_id(gate)
            for gate in constraints.required_native_gate_ids
        )
        for index, gate_id in enumerate(normalized_gates):
            if gate_id not in known_gates:
                issues.append(
                    ValidationIssue(
                        "UNKNOWN_GATE",
                        (
                            "$.hardware_constraints."
                            f"required_native_gate_ids[{index}]"
                        ),
                        f"Gate nativo inesistente: {gate_id!r}.",
                    )
                )

        normalized_fields = {
            "allowed_provider_ids": tuple(
                constraints.allowed_provider_ids
            ),
            "allowed_device_ids": tuple(constraints.allowed_device_ids),
            "required_native_gate_ids": normalized_gates,
        }
        for field_name, values in normalized_fields.items():
            if len(values) != len(set(values)):
                issues.append(
                    ValidationIssue(
                        "DUPLICATE_NORMALIZED_VALUE",
                        f"$.hardware_constraints.{field_name}",
                        "Sono presenti duplicati dopo la normalizzazione.",
                    )
                )

        qubit_range = constraints.device_qubits
        if qubit_range is not None:
            if (
                qubit_range.minimum is not None
                and qubit_range.maximum is not None
                and qubit_range.minimum > qubit_range.maximum
            ):
                issues.append(
                    ValidationIssue(
                        "INVALID_QUBIT_RANGE",
                        "$.hardware_constraints.device_qubits",
                        "Il minimo non può superare il massimo.",
                    )
                )
            if (
                qubit_range.maximum is not None
                and request.num_qubits > qubit_range.maximum
            ):
                issues.append(
                    ValidationIssue(
                        "CIRCUIT_EXCEEDS_USER_MAX_QUBITS",
                        "$.hardware_constraints.device_qubits.max",
                        "Il circuito supera il massimo hardware richiesto.",
                        {
                            "circuit_num_qubits": request.num_qubits,
                            "maximum": qubit_range.maximum,
                        },
                    )
                )

        allowed_providers = set(constraints.allowed_provider_ids)
        if allowed_providers:
            for index, device_id in enumerate(
                constraints.allowed_device_ids
            ):
                device = devices.get(device_id)
                if (
                    device is not None
                    and device.provider_id not in allowed_providers
                ):
                    issues.append(
                        ValidationIssue(
                            "DEVICE_PROVIDER_CONFLICT",
                            (
                                "$.hardware_constraints."
                                f"allowed_device_ids[{index}]"
                            ),
                            (
                                f"Il device {device_id!r} non appartiene "
                                "a un provider ammesso."
                            ),
                        )
                    )

        if issues:
            raise RequestValidationError(ValidationReport(tuple(issues)))

        normalized_constraints = HardwareConstraints(
            allowed_provider_ids=tuple(
                sorted(constraints.allowed_provider_ids)
            ),
            allowed_device_ids=tuple(
                sorted(constraints.allowed_device_ids)
            ),
            device_qubits=constraints.device_qubits,
            required_native_gate_ids=tuple(sorted(normalized_gates)),
        )
        normalized_user_request = UserRequest(
            schema_version=request.schema_version,
            request_id=request.request_id,
            catalog_snapshot_id=catalog.catalog_snapshot_id,
            circuit=request.user_request.circuit,
            figure_of_merit_id=request.figure_of_merit,
            hardware_constraints=normalized_constraints,
            legacy_compatibility=request.user_request.legacy_compatibility,
        )
        return NormalizedRequest(
            user_request=normalized_user_request,
            num_qubits=request.num_qubits,
            depth=request.depth,
            operation_names=request.operation_names,
            features=request.features,
            source_sha256=request.source_sha256,
        )

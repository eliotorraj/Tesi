"""Frozen MQT Predictor protocol and target-validation helpers."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

FROZEN_DEVICES = (
    "ibm_falcon_27",
    "ibm_heron_133",
    "ibm_falcon_127",
    "ibm_heron_156",
    "quantinuum_h2_56",
)
FIGURE_OF_MERIT = "expected_fidelity"
PROTOCOL_ID = "qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2"
TARGET_FINGERPRINT_SCHEMA_VERSION = 2
LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS = frozenset(
    {
        "box",
        "break",
        "continue",
        "for_loop",
        "if_else",
        "switch_case",
        "while_loop",
    }
)

# These fingerprints are the migrated protocol targets from mqt.bench 2.2.3,
# the version locked by MQT Predictor 2.4.0.
FROZEN_TARGET_SHA256 = {
    "ibm_falcon_27": "b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104",
    "ibm_heron_133": "2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3",
    "ibm_falcon_127": "5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd",
    "ibm_heron_156": "207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003",
    "quantinuum_h2_56": "ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee",
}

# Historical qiskit_dataset fingerprints from mqt.bench 2.0.0. They are kept
# as evidence of target drift and must not be mixed into the migrated benchmark.
LEGACY_QISKIT_DATASET_TARGET_SHA256 = {
    "ibm_falcon_27": "f30536987677ef5017fe3a89b8b4ee0a3e7252a1a226cc3db95fd9b2e822d991",
    "ibm_heron_133": "804f28754ad200e42a328ba910639c9d6fd3233dff35035e7f3cb85a2fc5168a",
    "ibm_falcon_127": "225e5f6fd85af0b37a1dd7c6306dd046a8c7ca585f135dda6e6418dd16f76b48",
    "ibm_heron_156": "a30f41e65c03fb900a4b8852261a8407c56c389560f4031ecb43099c1bec5089",
    "quantinuum_h2_56": "8c5576ac2f280a98f797dceb53186f97500e901d9784cc328187e156cbbe9b8f",
}


def canonical_json(payload: Any) -> str:
    """Serialize a payload deterministically for hashing."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def finite_float(value: Any) -> float | None:
    """Return a finite float or None for unavailable calibration data."""
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return converted if math.isfinite(converted) else None


def file_sha256(path: Path) -> str:
    """Hash a file without loading large model archives into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _target_operation_name(target: Any, operation: Any) -> str:
    """Resolve Target instruction classes without serializing memory addresses."""
    raw_name = getattr(operation, "name", None)
    if isinstance(raw_name, str):
        return raw_name
    for candidate in target.operation_names:
        try:
            registered = target.operation_from_name(candidate)
        except (AttributeError, KeyError):
            continue
        if registered is operation:
            return str(candidate)
    raise ValueError(f"Operazione Target senza nome stabile: {operation!r}")


def target_payload(target: Any) -> dict[str, Any]:
    """Return the canonical Target payload used by the frozen protocol."""
    instructions: list[dict[str, Any]] = []
    for operation, qargs in target.instructions:
        operation_name = _target_operation_name(target, operation)
        properties = None
        try:
            properties = target[operation_name].get(qargs)
        except (AttributeError, KeyError, TypeError):
            pass
        instructions.append(
            {
                "name": operation_name,
                "qargs": None if qargs is None else [int(qubit) for qubit in qargs],
                "error": finite_float(getattr(properties, "error", None)),
                "duration": finite_float(getattr(properties, "duration", None)),
            }
        )
    instructions.sort(
        key=lambda item: (
            item["name"],
            canonical_json(item["qargs"]),
            -1.0 if item["error"] is None else item["error"],
            -1.0 if item["duration"] is None else item["duration"],
        )
    )
    coupling_map = target.build_coupling_map()
    edges = (
        []
        if coupling_map is None
        else sorted(
            [int(source), int(destination)]
            for source, destination in coupling_map.get_edges()
        )
    )
    return {
        "fingerprint_schema_version": TARGET_FINGERPRINT_SCHEMA_VERSION,
        "device_id": str(target.description),
        "target_type": f"{type(target).__module__}.{type(target).__qualname__}",
        "num_qubits": int(target.num_qubits),
        "operation_names": sorted(map(str, target.operation_names)),
        "coupling_edges": edges,
        "all_to_all": coupling_map is None,
        "instructions": instructions,
    }


def target_sha256(target: Any) -> str:
    """Hash a Target with the deterministic, versioned protocol schema."""
    payload = target_payload(target)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def legacy_comparable_target_sha256(target: Any) -> str:
    """Hash current native Target data with qiskit_dataset's legacy schema.

    Qiskit 2.5 adds control-flow instructions that were absent from the
    historical Target payload. Excluding them and the schema-v2 marker makes
    the remaining native gates, topology, errors, and durations directly
    comparable with the hashes stored on qiskit_dataset.
    """
    payload = target_payload(target)
    payload.pop("fingerprint_schema_version")
    payload["operation_names"] = [
        name
        for name in payload["operation_names"]
        if name not in LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS
    ]
    payload["instructions"] = [
        item
        for item in payload["instructions"]
        if item["name"] not in LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS
    ]
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def target_record(target: Any) -> dict[str, Any]:
    """Build a compact provenance record for one Target."""
    payload = target_payload(target)
    return {
        "fingerprint_schema_version": TARGET_FINGERPRINT_SCHEMA_VERSION,
        "device_id": str(target.description),
        "num_qubits": int(target.num_qubits),
        "operation_names": payload["operation_names"],
        "coupling_edge_count": len(payload["coupling_edges"]),
        "target_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "target_type": payload["target_type"],
    }


def validate_compiled_circuit(circuit: Any, target: Any) -> dict[str, Any]:
    """Check basis, connectivity, and per-instruction Target support."""
    from qiskit.transpiler.passes import CheckMap, GatesInBasis

    errors: list[str] = []
    unsupported_operations = sorted(
        set(map(str, circuit.count_ops()))
        - set(map(str, target.operation_names))
        - {"barrier"}
    )
    basis_valid: bool | None = None
    connectivity_valid: bool | None = None
    instructions_valid = True

    try:
        checker = GatesInBasis(target=target)
        checker(circuit)
        basis_valid = bool(checker.property_set["all_gates_in_basis"])
    except Exception as error:
        errors.append(f"GatesInBasis:{type(error).__name__}:{error}")

    try:
        coupling_map = target.build_coupling_map()
        if coupling_map is None:
            connectivity_valid = True
        else:
            checker = CheckMap(coupling_map=coupling_map)
            checker(circuit)
            connectivity_valid = bool(checker.property_set["is_swap_mapped"])
    except Exception as error:
        errors.append(f"CheckMap:{type(error).__name__}:{error}")

    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name == "barrier":
            continue
        qargs = tuple(circuit.find_bit(qubit).index for qubit in instruction.qubits)
        try:
            supported = target.instruction_supported(
                operation_name=operation.name,
                qargs=qargs,
                parameters=list(operation.params),
            )
        except Exception as error:
            instructions_valid = False
            errors.append(
                f"instruction_supported:{operation.name}{qargs}:"
                f"{type(error).__name__}:{error}"
            )
            continue
        if not supported:
            instructions_valid = False
            errors.append(f"unsupported_instruction:{operation.name}{qargs}")

    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "instructions_valid": instructions_valid,
        "is_executable_on_target": bool(
            basis_valid
            and connectivity_valid
            and instructions_valid
            and not unsupported_operations
            and not errors
        ),
        "unsupported_operations": unsupported_operations,
        "validation_errors": errors,
    }


def frozen_target_mismatches(devices: list[Any]) -> dict[str, dict[str, str]]:
    """Return devices whose current Target differs from the frozen protocol."""
    mismatches: dict[str, dict[str, str]] = {}
    for target in devices:
        device_name = str(target.description)
        observed = target_sha256(target)
        expected = FROZEN_TARGET_SHA256.get(device_name)
        if expected != observed:
            mismatches[device_name] = {
                "expected": expected or "<not-in-frozen-protocol>",
                "observed": observed,
            }
    return mismatches

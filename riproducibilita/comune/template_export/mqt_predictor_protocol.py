from __future__ import annotations
import json, math, hashlib
from pathlib import Path
from typing import Any
TARGET_FINGERPRINT_SCHEMA_VERSION = 2

FROZEN_TARGET_SHA256 = {
    "ibm_falcon_27": "b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104",
    "ibm_heron_133": "2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3",
    "ibm_falcon_127": "5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd",
    "ibm_heron_156": "207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003",
    "quantinuum_h2_56": "ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee",
}

EXPERIMENT_ID = "qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2"

PROTOCOL_VERSION = "2.0.0"

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

LEGACY_ROOT = Path(__file__).resolve().parents[1] / "data"

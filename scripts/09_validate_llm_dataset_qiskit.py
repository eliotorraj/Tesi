"""Validate an MQT LLM dataset using Qiskit's legacy OpenQASM 2 extensions.

MQT targets may use gates such as ``rzz`` that Qiskit's exporter writes as
legacy built-ins.  They are valid for the MQT/Qiskit pipeline but require
``LEGACY_CUSTOM_INSTRUCTIONS`` when using the strict ``qiskit.qasm2`` parser.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from qiskit.qasm2 import LEGACY_CUSTOM_INSTRUCTIONS, loads as qasm2_loads


EXPECTED_SCHEMA_VERSION = "1.0.0"
EXPECTED_FEATURE_COUNT = 49


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    return parser.parse_args()


def reject_nonstandard_number(value: str) -> Any:
    """Reject NaN and Infinity because they are not standard JSON."""
    raise ValueError(f"Non-standard JSON number: {value}")


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_qasm(qasm: str) -> Any:
    """Parse Qiskit's OpenQASM 2 output including its legacy built-in gates."""
    return qasm2_loads(
        qasm,
        custom_instructions=LEGACY_CUSTOM_INSTRUCTIONS,
    )


def validate_record(
    record: dict[str, Any],
    feature_names: list[str],
    hardware_catalog: dict[str, Any],
) -> list[str]:
    """Return semantic errors found in one record."""
    errors: list[str] = []
    record_id = record.get("record_id", "<missing>")
    prefix = f"record {record_id}"

    source = record.get("source_circuit") or {}
    source_qasm = source.get("qasm2")
    if not isinstance(source_qasm, str):
        errors.append(f"{prefix}: source QASM missing")
    else:
        if source.get("sha256") != sha256_text(source_qasm):
            errors.append(f"{prefix}: source QASM checksum mismatch")
        try:
            parsed_source = parse_qasm(source_qasm)
        except Exception as error:  # noqa: BLE001
            errors.append(f"{prefix}: source QASM parse error: {error}")
        else:
            if parsed_source.num_qubits != source.get("summary", {}).get("num_qubits"):
                errors.append(f"{prefix}: source qubit count mismatch")

    features = record.get("feature_vector") or {}
    if features.get("feature_count") != EXPECTED_FEATURE_COUNT:
        errors.append(f"{prefix}: feature count is not 49")
    if features.get("ordered_names") != feature_names:
        errors.append(f"{prefix}: feature names differ from top-level schema")
    if len(features.get("ordered_values", [])) != EXPECTED_FEATURE_COUNT:
        errors.append(f"{prefix}: feature-value length is not 49")
    if set(features.get("by_name", {})) != set(feature_names):
        errors.append(f"{prefix}: feature dictionary differs from top-level schema")

    selection = record.get("device_selection")
    if selection is not None:
        selected_device = selection.get("selected_device")
        if selected_device not in hardware_catalog:
            errors.append(f"{prefix}: selected device missing from hardware catalog")
        ranked_devices = [row.get("device") for row in selection.get("ranking", [])]
        if selected_device not in ranked_devices:
            errors.append(f"{prefix}: selected device missing from classifier ranking")

    status = record.get("status")
    if status == "success":
        compilation = record.get("compilation") or {}
        compiled = record.get("compiled_circuit") or {}
        steps = compilation.get("steps", [])
        pass_names = compilation.get("selected_pass_names", [])
        if compilation.get("step_count") != len(steps):
            errors.append(f"{prefix}: step count mismatch")
        if len(pass_names) != len(steps):
            errors.append(f"{prefix}: pass count differs from step count")
        elif any(
            step.get("selected_action", {}).get("name") != pass_name
            for step, pass_name in zip(steps, pass_names, strict=True)
        ):
            errors.append(f"{prefix}: pass list differs from step trace")
        if not pass_names or pass_names[-1] != "terminate":
            errors.append(f"{prefix}: successful trace does not end in terminate")

        compiled_qasm = compiled.get("qasm2")
        if not isinstance(compiled_qasm, str):
            errors.append(f"{prefix}: compiled QASM missing")
        else:
            if compiled.get("sha256") != sha256_text(compiled_qasm):
                errors.append(f"{prefix}: compiled QASM checksum mismatch")
            try:
                parsed_compiled = parse_qasm(compiled_qasm)
            except Exception as error:  # noqa: BLE001
                errors.append(f"{prefix}: compiled QASM parse error: {error}")
            else:
                if parsed_compiled.depth() != compiled.get("summary", {}).get("depth"):
                    errors.append(f"{prefix}: compiled depth mismatch")

        terminal_reward = compilation.get("terminal_reward_returned_by_environment")
        final_score = compilation.get("final_score_recomputed")
        if isinstance(terminal_reward, (int, float)) and isinstance(final_score, (int, float)):
            if not math.isclose(terminal_reward, final_score, rel_tol=1e-12, abs_tol=1e-12):
                errors.append(f"{prefix}: terminal reward differs from final score")
        if record.get("error") is not None:
            errors.append(f"{prefix}: successful record contains an error")
    elif status in {"error", "timeout"}:
        if not isinstance(record.get("error"), dict):
            errors.append(f"{prefix}: unsuccessful record lacks a structured error")
    else:
        errors.append(f"{prefix}: invalid status {status!r}")

    return errors


def main() -> int:
    """Validate the complete dataset and print a compact result."""
    args = parse_args()
    payload = json.loads(
        args.dataset.read_text(encoding="utf-8"),
        parse_constant=reject_nonstandard_number,
    )
    errors: list[str] = []

    if payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append("unexpected schema version")

    records = payload.get("records")
    if not isinstance(records, list):
        errors.append("records is not a list")
        records = []

    dataset = payload.get("dataset") or {}
    expected_counts = {
        "record_count": len(records),
        "successful_records": sum(record.get("status") == "success" for record in records),
        "failed_records": sum(record.get("status") == "error" for record in records),
        "timeout_records": sum(record.get("status") == "timeout" for record in records),
    }
    for field, expected in expected_counts.items():
        if dataset.get(field) != expected:
            errors.append(f"{field} mismatch: expected {expected}, found {dataset.get(field)}")

    feature_schema = payload.get("feature_schema") or {}
    feature_names = feature_schema.get("ordered_names", [])
    if feature_schema.get("feature_count") != EXPECTED_FEATURE_COUNT:
        errors.append("top-level feature count is not 49")
    if len(feature_names) != EXPECTED_FEATURE_COUNT:
        errors.append("top-level feature-name count is not 49")
    if len(set(feature_names)) != len(feature_names):
        errors.append("top-level feature names contain duplicates")

    record_ids = [record.get("record_id") for record in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("record IDs are not unique")

    hardware_catalog = payload.get("hardware_catalog") or {}
    for record in records:
        errors.extend(validate_record(record, feature_names, hardware_catalog))

    if errors:
        print(f"INVALID: {len(errors)} problem(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "VALID: "
        f"records={len(records)} "
        f"success={expected_counts['successful_records']} "
        f"errors={expected_counts['failed_records']} "
        f"timeouts={expected_counts['timeout_records']} "
        f"devices={len(hardware_catalog)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

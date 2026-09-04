"""Audit the five expected-fidelity RL models before deciding resume or restart."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_model_artifacts import (
    EXPECTED_RL_BQSKIT_PROFILE,
    rl_model_filename,
    validate_rl_archive,
)
from mqt_predictor_protocol import (
    CANONICAL_RL_MODEL_DIR_V2,
    EXPERIMENT_ROOT,
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    PROTOCOL_ID,
    file_sha256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = CANONICAL_RL_MODEL_DIR_V2
DEFAULT_MANIFEST = (
    EXPERIMENT_ROOT / "cache" / "ml" / FIGURE_OF_MERIT / "manifest.jsonl"
)
DEFAULT_LOG_DIR = EXPERIMENT_ROOT / "logs" / "rl"
DEFAULT_OUTPUT = DEFAULT_LOG_DIR / "legacy_checkpoint_audit_mqt_2_4.json"
MIN_HISTORICAL_SUCCESS_RATE = 0.95


def parse_args() -> argparse.Namespace:
    """Parse audit controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--deep-load",
        action="store_true",
        help="Carica sequenzialmente i tensori PPO con SB3 2.9.0 oltre all'audit ZIP.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Mostra il risultato senza scrivere il report JSON.",
    )
    return parser.parse_args()


def latest_manifest_records(path: Path) -> dict[str, dict[str, Any]]:
    """Return the latest terminal record for every circuit/device pair."""
    latest: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return latest
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get("key")
            if isinstance(key, str) and record.get("status") != "running":
                latest[key] = record
    return latest


def is_strict_historical_success(
    record: dict[str, Any],
    *,
    model_sha256: str | None = None,
    target_sha256: str | None = None,
) -> bool:
    """Recognize validated evidence tied to the exact policy and Target."""
    validation = record.get("target_validation")
    passes = record.get("passes")
    strict = bool(
        record.get("status") == "success"
        and record.get("mode") == "rl"
        and record.get("validation_version") == 1
        and record.get("terminated") is True
        and record.get("truncated") is False
        and record.get("termination_reason") == "terminate"
        and isinstance(passes, list)
        and passes[-1:] == ["terminate"]
        and isinstance(validation, dict)
        and validation.get("is_executable_on_target") is True
        and isinstance(record.get("qasm_sha256"), str)
    )
    if not strict:
        return False
    if model_sha256 is not None and (
        record.get("model_sha256") != model_sha256
        or record.get("mqt_predictor_version") != "2.4.0"
    ):
        return False
    if target_sha256 is not None and record.get("target_sha256") != target_sha256:
        return False
    return True


def compilation_evidence(
    records: dict[str, dict[str, Any]],
    device_name: str,
    *,
    model_sha256: str | None = None,
    target_sha256: str | None = None,
) -> dict[str, Any]:
    """Summarize the durable compilation evidence for one policy."""
    selected = [
        record
        for record in records.values()
        if record.get("device") == device_name
    ]
    statuses = Counter(str(record.get("status", "unknown")) for record in selected)
    raw_successes = statuses.get("success", 0)
    strict_successes = sum(
        is_strict_historical_success(
            record,
            model_sha256=model_sha256,
            target_sha256=target_sha256,
        )
        for record in selected
    )
    total = len(selected)
    return {
        "pairs": total,
        "raw_successes": raw_successes,
        "raw_success_rate": raw_successes / total if total else 0.0,
        "strict_successes": strict_successes,
        "strict_success_rate": strict_successes / total if total else 0.0,
        "statuses": dict(sorted(statuses.items())),
    }


def tensorboard_summary(log_dir: Path, device_name: str) -> dict[str, Any]:
    """Read the most recent useful TensorBoard scalars, when available."""
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    except ImportError:
        return {"available": False, "error": "tensorboard non installato"}

    model_dir = log_dir / f"model_{FIGURE_OF_MERIT}_{device_name}"
    tags = (
        "rollout/ep_rew_mean",
        "rollout/ep_len_mean",
        "train/explained_variance",
    )
    latest: dict[str, tuple[float, int, float]] = {}
    errors: list[str] = []
    for event_path in sorted(model_dir.rglob("events.out.tfevents.*")):
        try:
            accumulator = EventAccumulator(
                str(event_path),
                size_guidance={"scalars": 0},
            )
            accumulator.Reload()
            available = set(accumulator.Tags().get("scalars", ()))
            for tag in tags:
                if tag not in available:
                    continue
                for event in accumulator.Scalars(tag):
                    candidate = (float(event.wall_time), int(event.step), float(event.value))
                    if tag not in latest or candidate[:2] > latest[tag][:2]:
                        latest[tag] = candidate
        except Exception as error:
            errors.append(f"{event_path.name}: {type(error).__name__}: {error}")

    return {
        "available": bool(latest),
        "scalars": {
            tag: {"step": value[1], "value": value[2]}
            for tag, value in sorted(latest.items())
        },
        "errors": errors,
    }


def deep_load_model(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Load one PPO model with the active runtime and immediately release it."""
    details: dict[str, Any] = {}
    errors: list[str] = []
    try:
        from sb3_contrib import MaskablePPO

        model = MaskablePPO.load(path)
        details = {
            "num_timesteps": int(model.num_timesteps),
            "action_count": int(model.action_space.n),
            "observation_space": str(model.observation_space),
        }
        del model
        gc.collect()
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
    return details, errors


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    """Write the report atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def audit_device(
    device_name: str,
    *,
    model_dir: Path,
    log_dir: Path,
    records: dict[str, dict[str, Any]],
    deep_load: bool,
) -> dict[str, Any]:
    """Audit one canonical model and produce an evidence-based recommendation."""
    model_path = model_dir / rl_model_filename(device_name)
    model_digest = file_sha256(model_path) if model_path.is_file() else None
    archive, archive_errors = validate_rl_archive(model_path)
    evidence = compilation_evidence(
        records,
        device_name,
        model_sha256=model_digest,
        target_sha256=FROZEN_TARGET_SHA256[device_name],
    )
    training_metadata_path = model_path.with_suffix(".metadata.json")
    training_metadata: dict[str, Any] | None = None
    metadata_error: str | None = None
    if training_metadata_path.is_file():
        try:
            loaded = json.loads(training_metadata_path.read_text(encoding="utf-8"))
            training_metadata = loaded if isinstance(loaded, dict) else None
            if training_metadata is None:
                metadata_error = "metadata non rappresentati da un oggetto JSON"
        except (OSError, json.JSONDecodeError) as error:
            metadata_error = f"{type(error).__name__}: {error}"

    deep_details: dict[str, Any] = {}
    deep_errors: list[str] = []
    if deep_load and not archive_errors:
        deep_details, deep_errors = deep_load_model(model_path)

    reasons: list[str] = []
    if archive_errors:
        reasons.append("checkpoint strutturalmente non valido")
    if deep_errors:
        reasons.append("checkpoint non caricabile con il runtime 2.4.0")
    if training_metadata is None:
        reasons.append("mancano metadati che attestino un training MQT Predictor 2.4.0")
    else:
        expected_metadata = {
            "bqskit_profile": EXPECTED_RL_BQSKIT_PROFILE,
            "device": device_name,
            "figure_of_merit": FIGURE_OF_MERIT,
            "model_sha256": model_digest,
            "mqt_predictor_version": "2.4.0",
            "protocol": PROTOCOL_ID,
            "target_matches_frozen_protocol": True,
        }
        for field, expected in expected_metadata.items():
            if training_metadata.get(field) != expected:
                reasons.append(
                    f"metadato {field} incoerente: "
                    f"atteso={expected!r}, osservato={training_metadata.get(field)!r}"
                )
        target_metadata = training_metadata.get("target")
        if (
            not isinstance(target_metadata, dict)
            or target_metadata.get("target_sha256")
            != FROZEN_TARGET_SHA256[device_name]
        ):
            reasons.append("fingerprint Target dei metadati non conforme")
        if training_metadata.get("num_timesteps") != archive.get("num_timesteps"):
            reasons.append("num_timesteps dei metadati diverso dall'archivio SB3")
    if evidence["strict_success_rate"] < MIN_HISTORICAL_SUCCESS_RATE:
        reasons.append(
            "copertura di compilazioni RL rigorosamente validate inferiore al 95%"
        )
    if evidence["raw_success_rate"] < MIN_HISTORICAL_SUCCESS_RATE:
        reasons.append("tasso storico di compilazioni riuscite inferiore al 95%")

    result: dict[str, Any] = {
        "device": device_name,
        "path": str(model_path),
        "sha256": model_digest,
        "archive": archive,
        "archive_errors": archive_errors,
        "deep_load": deep_details,
        "deep_load_errors": deep_errors,
        "training_metadata": training_metadata,
        "training_metadata_error": metadata_error,
        "compilation_evidence": evidence,
        "tensorboard": tensorboard_summary(log_dir, device_name),
        "recommendation": "restart" if reasons else "resume",
        "reasons": reasons,
    }
    return result


def main() -> int:
    """Audit all five frozen policies and optionally persist the report."""
    args = parse_args()
    records = latest_manifest_records(args.manifest)
    results = [
        audit_device(
            device_name,
            model_dir=args.model_dir,
            log_dir=args.log_dir,
            records=records,
            deep_load=args.deep_load,
        )
        for device_name in FROZEN_DEVICES
    ]
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "protocol": PROTOCOL_ID,
        "figure_of_merit": FIGURE_OF_MERIT,
        "active_mqt_predictor_version": package_version("mqt.predictor"),
        "manifest": str(args.manifest),
        "minimum_historical_success_rate": MIN_HISTORICAL_SUCCESS_RATE,
        "models": results,
        "decision": (
            "restart_all"
            if all(item["recommendation"] == "restart" for item in results)
            else "review_individual_recommendations"
        ),
    }

    for item in results:
        evidence = item["compilation_evidence"]
        print(
            f"{item['device']:<22} {item['recommendation'].upper():<7} "
            f"step={item['archive'].get('num_timesteps', '?')} "
            f"successi_storici={evidence['raw_successes']}/{evidence['pairs']} "
            f"successi_strict={evidence['strict_successes']}/{evidence['pairs']}"
        )
        for reason in item["reasons"]:
            print(f"  - {reason}")

    if not args.no_write:
        atomic_json_write(args.output, report)
        print(f"Report: {args.output}")

    return 1 if any(item["recommendation"] == "restart" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

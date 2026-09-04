"""Shared validation helpers for canonical and runtime MQT model artifacts."""

from __future__ import annotations

import json
import math
import re
import zipfile
from pathlib import Path
from typing import Any

from mqt_predictor_protocol import (
    CANONICAL_MODEL_ROOT_V2,
    EXPERIMENT_ID,
    EXPECTED_PACKAGE_VERSIONS,
    EXPECTED_SPLIT_COUNTS,
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    PROTOCOL_ID,
    RL_CHECKPOINT_EVERY,
    RL_FINAL_TIMESTEPS,
    RL_ROLLOUT_STEPS,
    PROTOCOL_VERSION,
    RL_TRAINING_TIMESTEPS,
)


EXPECTED_FEATURE_COUNT = 49
EXPECTED_ACTION_COUNT = 22
EXPECTED_OBSERVATION_KEYS = frozenset(
    {
        "critical_depth",
        "depth",
        "entanglement_ratio",
        "liveness",
        "num_qubits",
        "parallelism",
        "program_communication",
    }
)
ML_MODEL_FILENAME = f"trained_clf_{FIGURE_OF_MERIT}.joblib"
REQUIRED_RL_ARCHIVE_MEMBERS = {
    "data",
    "policy.pth",
    "policy.optimizer.pth",
    "_stable_baselines3_version",
}
EXPECTED_RL_BQSKIT_PROFILE = "ci-lightweight-dynamic-synthesis"


def rl_model_filename(device_name: str) -> str:
    """Return MQT's exact runtime filename for one frozen RL policy."""
    if device_name not in FROZEN_DEVICES:
        raise ValueError(f"Device fuori protocollo: {device_name}")
    return f"model_{FIGURE_OF_MERIT}_{device_name}.zip"


def is_git_lfs_pointer(path: Path) -> bool:
    """Return whether a supposed model is only an unresolved Git LFS pointer."""
    if not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(128).startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def validate_rl_archive(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Validate one Stable-Baselines3 ZIP without loading its multi-GB tensors."""
    metadata: dict[str, Any] = {"path": str(path), "kind": "rl"}
    errors: list[str] = []
    if not path.is_file():
        return metadata, ["file mancante"]
    metadata["size_bytes"] = path.stat().st_size
    if is_git_lfs_pointer(path):
        return metadata, ["puntatore Git LFS non materializzato; esegui git lfs pull"]
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            missing_members = sorted(REQUIRED_RL_ARCHIVE_MEMBERS - names)
            if missing_members:
                errors.append("membri SB3 mancanti: " + ", ".join(missing_members))
            corrupt_member = archive.testzip()
            if corrupt_member is not None:
                errors.append(f"membro ZIP corrotto: {corrupt_member}")
            metadata["archive_members"] = len(names)
            metadata["sb3_version"] = (
                archive.read("_stable_baselines3_version").decode("utf-8").strip()
                if "_stable_baselines3_version" in names
                else None
            )
            if "data" in names:
                try:
                    saved_data = json.loads(archive.read("data"))
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    errors.append(
                        f"metadati SB3 non validi: {type(error).__name__}: {error}"
                    )
                else:
                    if not isinstance(saved_data, dict):
                        errors.append("metadati SB3 non rappresentati da un oggetto JSON")
                        saved_data = {}
                    raw_timesteps = saved_data.get("num_timesteps")
                    try:
                        num_timesteps = int(raw_timesteps)
                    except (TypeError, ValueError):
                        num_timesteps = -1
                    metadata["num_timesteps"] = num_timesteps
                    if num_timesteps <= 0:
                        errors.append(
                            f"num_timesteps non valido: {raw_timesteps!r}"
                        )

                    action_space = saved_data.get("action_space")
                    raw_action_count = (
                        action_space.get("n")
                        if isinstance(action_space, dict)
                        else None
                    )
                    try:
                        action_count = int(raw_action_count)
                    except (TypeError, ValueError):
                        action_count = -1
                    metadata["action_count"] = action_count
                    if action_count != EXPECTED_ACTION_COUNT:
                        errors.append(
                            "action space incompatibile: "
                            f"atteso={EXPECTED_ACTION_COUNT}, osservato={raw_action_count!r}"
                        )

                    observation_space = saved_data.get("observation_space")
                    spaces_repr = (
                        observation_space.get("spaces")
                        if isinstance(observation_space, dict)
                        else None
                    )
                    observed_keys = (
                        set(re.findall(r"'([^']+)'\s*:", spaces_repr))
                        if isinstance(spaces_repr, str)
                        else set()
                    )
                    metadata["observation_keys"] = sorted(observed_keys)
                    if observed_keys != EXPECTED_OBSERVATION_KEYS:
                        errors.append(
                            "observation space incompatibile: "
                            f"atteso={sorted(EXPECTED_OBSERVATION_KEYS)}, "
                            f"osservato={sorted(observed_keys)}"
                        )
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile) as error:
        errors.append(f"archivio ZIP non valido: {type(error).__name__}: {error}")
    return metadata, errors


def validate_rl_training_metadata(
    path: Path,
    *,
    device_name: str,
    model_sha256: str,
    expected_max_steps: int | None = None,
    expected_num_timesteps: int | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Validate provenance for one canonical frozen-protocol RL model."""
    metadata: dict[str, Any] = {"path": str(path), "kind": "rl_metadata"}
    errors: list[str] = []
    if device_name not in FROZEN_DEVICES:
        return metadata, [f"device fuori protocollo: {device_name}"]
    if not path.is_file():
        return metadata, ["metadati training mancanti"]

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        return metadata, [
            f"metadati training non validi: {type(error).__name__}: {error}"
        ]
    if not isinstance(loaded, dict):
        return metadata, ["metadati training non rappresentati da un oggetto JSON"]
    metadata.update(loaded)

    expected = {
        "bqskit_profile": EXPECTED_RL_BQSKIT_PROFILE,
        "checkpoint_every": RL_CHECKPOINT_EVERY,
        "device": device_name,
        "experiment_id": EXPERIMENT_ID,
        "figure_of_merit": FIGURE_OF_MERIT,
        "model_sha256": model_sha256,
        "mqt_predictor_version": "2.4.0",
        "protocol": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "target_matches_frozen_protocol": True,
        "training_circuit_count": EXPECTED_SPLIT_COUNTS["train"],
        "rollout_steps": RL_ROLLOUT_STEPS,
        "training_split": "train",
        "target_timesteps": RL_TRAINING_TIMESTEPS,
    }
    for field, expected_value in expected.items():
        if loaded.get(field) != expected_value:
            errors.append(
                f"{field} non conforme: "
                f"atteso={expected_value!r}, osservato={loaded.get(field)!r}"
            )

    target = loaded.get("target")
    if (
        not isinstance(target, dict)
        or target.get("target_sha256") != FROZEN_TARGET_SHA256[device_name]
    ):
        errors.append("fingerprint Target dei metadati non conforme")

    try:
        num_timesteps = int(loaded.get("num_timesteps"))
    except (TypeError, ValueError):
        num_timesteps = -1
    if num_timesteps <= 0:
        errors.append(f"num_timesteps non valido: {loaded.get('num_timesteps')!r}")
    if (
        expected_num_timesteps is not None
        and num_timesteps != expected_num_timesteps
    ):
        errors.append(
            "num_timesteps non conforme: "
            f"atteso={expected_num_timesteps}, osservato={num_timesteps}"
        )
    if expected_max_steps is not None and loaded.get("max_steps") != expected_max_steps:
        errors.append(
            f"max_steps non conforme: "
            f"atteso={expected_max_steps}, osservato={loaded.get('max_steps')!r}"
        )
    return metadata, errors


def validate_ml_classifier(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Load the selector and validate its feature width and frozen label set."""
    metadata: dict[str, Any] = {"path": str(path), "kind": "ml"}
    errors: list[str] = []
    if not path.is_file():
        return metadata, ["file mancante"]
    metadata["size_bytes"] = path.stat().st_size
    if is_git_lfs_pointer(path):
        return metadata, ["puntatore Git LFS non materializzato; esegui git lfs pull"]
    try:
        import joblib
        import numpy as np

        classifier = joblib.load(path)
        classes = [str(value) for value in getattr(classifier, "classes_", ())]
        feature_count = getattr(classifier, "n_features_in_", None)
        metadata.update(
            {
                "classifier_type": f"{type(classifier).__module__}.{type(classifier).__qualname__}",
                "classes": classes,
                "feature_count": int(feature_count) if feature_count is not None else None,
            }
        )
        if set(classes) != set(FROZEN_DEVICES) or len(classes) != len(FROZEN_DEVICES):
            errors.append(
                "classi non conformi al protocollo: "
                f"attese={list(FROZEN_DEVICES)}, osservate={classes}"
            )
        if feature_count != EXPECTED_FEATURE_COUNT:
            errors.append(
                f"numero feature errato: atteso={EXPECTED_FEATURE_COUNT}, osservato={feature_count}"
            )
        if not errors:
            probabilities = np.asarray(
                classifier.predict_proba(np.zeros((1, EXPECTED_FEATURE_COUNT), dtype=float)),
                dtype=float,
            )
            if probabilities.shape != (1, len(FROZEN_DEVICES)):
                errors.append(f"shape predict_proba inattesa: {probabilities.shape}")
            elif not all(math.isfinite(float(value)) for value in probabilities.flat):
                errors.append("predict_proba contiene valori non finiti")
    except Exception as error:
        errors.append(f"classificatore non caricabile: {type(error).__name__}: {error}")
    return metadata, errors


def validate_ml_training_metadata(
    path: Path,
    *,
    model_sha256: str,
) -> tuple[dict[str, Any], list[str]]:
    """Validate provenance for the v2 five-class device selector."""
    metadata: dict[str, Any] = {"path": str(path), "kind": "ml_metadata"}
    errors: list[str] = []
    if not path.is_file():
        return metadata, ["metadati training mancanti"]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        return metadata, [
            f"metadati training non validi: {type(error).__name__}: {error}"
        ]
    if not isinstance(loaded, dict):
        return metadata, ["metadati training non rappresentati da un oggetto JSON"]
    metadata.update(loaded)
    expected = {
        "experiment_id": EXPERIMENT_ID,
        "figure_of_merit": FIGURE_OF_MERIT,
        "matches_frozen_protocol": True,
        "model_sha256": model_sha256,
        "protocol": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "source_circuit_count": EXPECTED_SPLIT_COUNTS["train"],
        "training_split": "train",
    }
    for field, expected_value in expected.items():
        if loaded.get(field) != expected_value:
            errors.append(
                f"{field} non conforme: "
                f"atteso={expected_value!r}, osservato={loaded.get(field)!r}"
            )
    targets = loaded.get("targets")
    if not isinstance(targets, dict):
        errors.append("fingerprint Target mancanti")
    else:
        for device_name in FROZEN_DEVICES:
            record = targets.get(device_name)
            if (
                not isinstance(record, dict)
                or record.get("target_sha256") != FROZEN_TARGET_SHA256[device_name]
            ):
                errors.append(f"fingerprint Target non conforme: {device_name}")
    software = loaded.get("software")
    if not isinstance(software, dict):
        errors.append("versioni software mancanti")
    else:
        for distribution, expected_version in EXPECTED_PACKAGE_VERSIONS.items():
            if software.get(distribution) != expected_version:
                errors.append(
                    f"versione {distribution} non conforme: "
                    f"attesa={expected_version}, osservata={software.get(distribution)!r}"
                )
    return metadata, errors


def validate_model_set(
    *,
    expected_max_steps: int = 64,
    expected_num_timesteps: int = RL_FINAL_TIMESTEPS,
) -> tuple[dict[str, Any], list[str]]:
    """Controlla le copie canoniche/runtime e tutta la provenienza qcompile."""
    from mqt.predictor.ml.helper import get_path_training_data
    from mqt.predictor.rl.helper import get_path_trained_model
    from mqt_predictor_protocol import file_sha256

    runtime_rl = get_path_trained_model()
    runtime_ml = get_path_training_data() / "trained_model"
    report: dict[str, Any] = {}
    errors: list[str] = []
    for device_name in FROZEN_DEVICES:
        filename = rl_model_filename(device_name)
        canonical = CANONICAL_MODEL_ROOT_V2 / "rl" / filename
        runtime = runtime_rl / filename
        item: dict[str, Any] = {}
        for label, path in (("canonical", canonical), ("runtime", runtime)):
            metadata, current = validate_rl_archive(path)
            item[label] = {**metadata, "errors": current}
            errors.extend(f"{filename}:{label}:{message}" for message in current)
        if canonical.is_file() and runtime.is_file():
            canonical_hash = file_sha256(canonical)
            runtime_hash = file_sha256(runtime)
            item["canonical_sha256"] = canonical_hash
            item["runtime_sha256"] = runtime_hash
            if canonical_hash != runtime_hash:
                errors.append(f"{filename}:canonical/runtime hash mismatch")
            else:
                metadata, current = validate_rl_training_metadata(
                    canonical.with_suffix(".metadata.json"),
                    device_name=device_name,
                    model_sha256=canonical_hash,
                    expected_max_steps=expected_max_steps,
                    expected_num_timesteps=expected_num_timesteps,
                )
                item["training_metadata"] = {**metadata, "errors": current}
                errors.extend(
                    f"{filename}:metadata:{message}" for message in current
                )
                archive_timesteps = item["canonical"].get("num_timesteps")
                if archive_timesteps != metadata.get("num_timesteps"):
                    errors.append(
                        f"{filename}: num_timesteps archivio/metadati diversi"
                    )
        report[filename] = item

    canonical_ml = CANONICAL_MODEL_ROOT_V2 / "ml" / ML_MODEL_FILENAME
    runtime_ml_path = runtime_ml / ML_MODEL_FILENAME
    item = {}
    for label, path in (("canonical", canonical_ml), ("runtime", runtime_ml_path)):
        metadata, current = validate_ml_classifier(path)
        item[label] = {**metadata, "errors": current}
        errors.extend(f"{ML_MODEL_FILENAME}:{label}:{message}" for message in current)
    if canonical_ml.is_file() and runtime_ml_path.is_file():
        canonical_hash = file_sha256(canonical_ml)
        runtime_hash = file_sha256(runtime_ml_path)
        item["canonical_sha256"] = canonical_hash
        item["runtime_sha256"] = runtime_hash
        if canonical_hash != runtime_hash:
            errors.append(f"{ML_MODEL_FILENAME}:canonical/runtime hash mismatch")
        else:
            metadata, current = validate_ml_training_metadata(
                canonical_ml.with_suffix(".metadata.json"),
                model_sha256=canonical_hash,
            )
            item["training_metadata"] = {**metadata, "errors": current}
            errors.extend(
                f"{ML_MODEL_FILENAME}:metadata:{message}" for message in current
            )
    report[ML_MODEL_FILENAME] = item
    return report, errors

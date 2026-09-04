"""Synchronize the five frozen MQT models with the active Python runtime."""

from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mqt.predictor.ml.helper import get_path_training_data as get_ml_training_data
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir

from mqt_model_artifacts import (
    ML_MODEL_FILENAME,
    rl_model_filename,
    validate_ml_classifier,
    validate_ml_training_metadata,
    validate_rl_archive,
    validate_rl_training_metadata,
)
from mqt_predictor_protocol import (
    CANONICAL_MODEL_ROOT_V2,
    FROZEN_DEVICES,
    RL_FINAL_TIMESTEPS,
    file_sha256,
)


DEFAULT_STORE = CANONICAL_MODEL_ROOT_V2
ArtifactKind = Literal["rl", "ml"]


@dataclass(frozen=True)
class ArtifactPair:
    """One canonical/runtime pair required by the frozen protocol."""

    kind: ArtifactKind
    name: str
    canonical: Path
    runtime: Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "install", "verify"))
    parser.add_argument("--directory", type=Path, default=DEFAULT_STORE)
    parser.add_argument(
        "--component",
        choices=("all", "rl", "ml"),
        default="all",
        help="Limita l'operazione alle policy RL o al selettore ML.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.action == "verify" and args.overwrite:
        parser.error("--overwrite non è valido con verify.")
    return args


def artifact_pairs(store: Path, component: str) -> list[ArtifactPair]:
    """Return only the six artifacts admitted by the frozen protocol."""
    package_rl = get_rl_model_dir()
    package_ml = get_ml_training_data() / "trained_model"
    pairs: list[ArtifactPair] = []
    if component in ("all", "rl"):
        pairs.extend(
            ArtifactPair(
                kind="rl",
                name=rl_model_filename(device_name),
                canonical=store / "rl" / rl_model_filename(device_name),
                runtime=package_rl / rl_model_filename(device_name),
            )
            for device_name in FROZEN_DEVICES
        )
    if component in ("all", "ml"):
        pairs.append(
            ArtifactPair(
                kind="ml",
                name=ML_MODEL_FILENAME,
                canonical=store / "ml" / ML_MODEL_FILENAME,
                runtime=package_ml / ML_MODEL_FILENAME,
            )
        )
    return pairs


def validation_errors(path: Path, kind: ArtifactKind) -> list[str]:
    """Return structural and semantic errors for one artifact."""
    if kind == "rl":
        _metadata, errors = validate_rl_archive(path)
    else:
        _metadata, errors = validate_ml_classifier(path)
    return errors


def atomic_copy(source: Path, destination: Path, kind: ArtifactKind, overwrite: bool) -> bool:
    """Validate and atomically copy one artifact, refusing silent replacement."""
    errors = validation_errors(source, kind)
    if errors:
        raise ValueError(f"Artefatto sorgente non valido: {source}: {'; '.join(errors)}")

    source_digest = file_sha256(source)
    if destination.exists():
        destination_digest = file_sha256(destination)
        if source_digest == destination_digest:
            print(f"Identico, salto: {destination}")
            return False
        if not overwrite:
            raise FileExistsError(
                f"Artefatto diverso già presente: {destination}. Usa --overwrite."
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        shutil.copy2(source, temporary)
        if file_sha256(temporary) != source_digest:
            raise OSError(f"Hash diverso dopo la copia temporanea: {temporary}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)

    destination_errors = validation_errors(destination, kind)
    if destination_errors:
        raise ValueError(
            f"Artefatto copiato ma non valido: {destination}: "
            + "; ".join(destination_errors)
        )
    print(f"Copiato: {source} -> {destination}")
    return True


def verify_pair(pair: ArtifactPair) -> list[str]:
    """Verify validity and byte identity of one canonical/runtime pair."""
    errors: list[str] = []
    for label, path in (("canonico", pair.canonical), ("runtime", pair.runtime)):
        current = validation_errors(path, pair.kind)
        errors.extend(f"{label}: {message}" for message in current)
    if not errors:
        canonical_digest = file_sha256(pair.canonical)
        runtime_digest = file_sha256(pair.runtime)
        if canonical_digest != runtime_digest:
            errors.append(
                "hash differenti: "
                f"canonico={canonical_digest}, runtime={runtime_digest}"
            )
        elif pair.kind == "rl":
            device_name = next(
                name
                for name in FROZEN_DEVICES
                if pair.name == rl_model_filename(name)
            )
            _metadata, provenance_errors = validate_rl_training_metadata(
                pair.canonical.with_suffix(".metadata.json"),
                device_name=device_name,
                model_sha256=canonical_digest,
                expected_max_steps=64,
                expected_num_timesteps=RL_FINAL_TIMESTEPS,
            )
            errors.extend(f"metadati: {message}" for message in provenance_errors)
        else:
            _metadata, provenance_errors = validate_ml_training_metadata(
                pair.canonical.with_suffix(".metadata.json"),
                model_sha256=canonical_digest,
            )
            errors.extend(f"metadati: {message}" for message in provenance_errors)
    return errors


def canonical_provenance_errors(pair: ArtifactPair) -> list[str]:
    """Valida i metadati canonici anche quando la copia runtime è assente."""
    structural = validation_errors(pair.canonical, pair.kind)
    if structural:
        return [f"canonico: {message}" for message in structural]
    digest = file_sha256(pair.canonical)
    if pair.kind == "rl":
        device_name = next(
            name
            for name in FROZEN_DEVICES
            if pair.name == rl_model_filename(name)
        )
        _metadata, errors = validate_rl_training_metadata(
            pair.canonical.with_suffix(".metadata.json"),
            device_name=device_name,
            model_sha256=digest,
            expected_max_steps=64,
            expected_num_timesteps=RL_FINAL_TIMESTEPS,
        )
    else:
        _metadata, errors = validate_ml_training_metadata(
            pair.canonical.with_suffix(".metadata.json"),
            model_sha256=digest,
        )
    return [f"metadati: {message}" for message in errors]


def main() -> int:
    """Capture, install, or verify the exact frozen model set."""
    args = parse_args()
    pairs = artifact_pairs(args.directory, args.component)
    if args.action == "capture":
        raise SystemExit(
            "Il protocollo v2 non cattura modelli dal runtime: la copia canonica "
            "con metadati deve essere prodotta dai trainer del repository."
        )

    if args.action == "verify":
        failed = 0
        for pair in pairs:
            errors = verify_pair(pair)
            if errors:
                failed += 1
                print(f"ERRORE {pair.name}: " + "; ".join(errors))
            else:
                digest = file_sha256(pair.canonical)
                print(f"OK {pair.name}: sha256={digest}")
        if failed:
            print(f"Verifica fallita: {failed}/{len(pairs)} artefatti non conformi.")
            return 1
        print(f"Verifica completata: {len(pairs)}/{len(pairs)} artefatti conformi.")
        return 0

    copied = 0
    try:
        for pair in pairs:
            provenance_errors = canonical_provenance_errors(pair)
            if provenance_errors:
                raise ValueError(
                    f"Artefatto canonico non installabile: {pair.canonical}: "
                    + "; ".join(provenance_errors)
                )
            source, destination = (
                (pair.runtime, pair.canonical)
                if args.action == "capture"
                else (pair.canonical, pair.runtime)
            )
            copied += int(atomic_copy(source, destination, pair.kind, args.overwrite))
    except (FileExistsError, OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(
        f"Sincronizzazione {args.action} completata; "
        f"file copiati: {copied}/{len(pairs)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

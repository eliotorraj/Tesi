"""Verifica il corpus congelato e prepara solo train/validation per il protocollo v2."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_predictor_protocol import (
    EXPERIMENT_ID,
    FROZEN_DEVICES,
    SOURCE_MANIFEST_V2,
    TRAINING_CIRCUITS_V2,
    VALIDATION_CIRCUITS_V2,
    file_sha256,
    frozen_target_mismatches,
    installed_package_versions,
    package_version_mismatches,
    target_record,
    verify_circuit_directory,
    verify_source_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Legge le opzioni della preparazione senza aprire il test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-manifest",
        type=Path,
        help="Manifest 1.0 da verificare; se omesso usa quello full congelato.",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=SOURCE_MANIFEST_V2,
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Esegue tutti i controlli senza scrivere manifest o copie.",
    )
    parser.add_argument(
        "--without-validation",
        action="store_true",
        help="Materializza soltanto i 422 circuiti di training.",
    )
    return parser.parse_args()


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    """Scrive un JSON completo mediante rinomina atomica."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def materialize_split(
    manifest: dict[str, Any],
    split: str,
    destination: Path,
) -> int:
    """Copia in modo atomico uno split e rifiuta file estranei o incoerenti."""
    records = [
        record
        for record in manifest["circuits"]
        if record["split"] == split
    ]
    expected_names = {str(record["file_name"]) for record in records}
    destination.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(
        path.name
        for path in destination.glob("*.qasm")
        if path.name not in expected_names
    )
    if unexpected:
        raise RuntimeError(
            f"La directory {destination} contiene QASM fuori protocollo: {unexpected}."
        )

    for record in records:
        source = PROJECT_ROOT / str(record["source_ref"])
        target = destination / str(record["file_name"])
        expected_sha256 = str(record["source_sha256"])
        if target.exists():
            if not target.is_file() or file_sha256(target) != expected_sha256:
                raise RuntimeError(f"Copia esistente ma incoerente: {target}.")
            continue
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        try:
            shutil.copy2(source, temporary)
            if file_sha256(temporary) != expected_sha256:
                raise RuntimeError(f"Copia corrotta: {target}.")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return len(records)


def main() -> int:
    """Verifica ambiente, Target, corpus e prepara le directory consentite."""
    args = parse_args()
    version_errors = package_version_mismatches()
    if version_errors:
        raise SystemExit(
            "Versioni non conformi al lock 2.4.0:\n"
            + "\n".join(
                f"  - {name}: attesa={values['expected']}, "
                f"osservata={values['observed']}"
                for name, values in sorted(version_errors.items())
            )
        )

    from mqt.bench.targets import get_device

    targets = [get_device(name) for name in FROZEN_DEVICES]
    target_errors = frozen_target_mismatches(targets)
    if target_errors:
        raise SystemExit(
            "Target diversi dal protocollo v2:\n"
            + "\n".join(
                f"  - {name}: atteso={values['expected']}, "
                f"osservato={values['observed']}"
                for name, values in sorted(target_errors.items())
            )
        )

    verify_kwargs: dict[str, Any] = {}
    if args.source_manifest is not None:
        verify_kwargs["manifest_path"] = args.source_manifest
    manifest = verify_source_manifest(**verify_kwargs)
    manifest["software"] = installed_package_versions()
    manifest["targets"] = {
        str(target.description): target_record(target)
        for target in targets
    }

    if args.check_only:
        print(
            json.dumps(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "status": "verified",
                    "counts": manifest["counts"],
                    "corpus_sha256": manifest["corpus_sha256"],
                    "writes": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    atomic_json_write(args.output_manifest, manifest)
    train_count = materialize_split(manifest, "train", TRAINING_CIRCUITS_V2)
    validation_count = 0
    if not args.without_validation:
        validation_count = materialize_split(
            manifest,
            "validation",
            VALIDATION_CIRCUITS_V2,
        )
    train_summary = verify_circuit_directory(
        TRAINING_CIRCUITS_V2,
        allowed_splits=("train",),
        manifest_path=args.output_manifest,
    )
    result = {
        "experiment_id": EXPERIMENT_ID,
        "status": "ready_without_test",
        "manifest": str(args.output_manifest),
        "manifest_sha256": file_sha256(args.output_manifest),
        "training": train_summary,
        "materialized": {
            "train": train_count,
            "validation": validation_count,
            "test": 0,
        },
        "test_open": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

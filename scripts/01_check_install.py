"""Verify the exact MQT Predictor 2.4.0 environment and frozen protocol."""

from __future__ import annotations

import argparse
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from mqt_model_artifacts import (
    ML_MODEL_FILENAME,
    rl_model_filename,
    validate_ml_classifier,
    validate_rl_archive,
    validate_rl_training_metadata,
)
from mqt_predictor_protocol import (
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    LEGACY_QISKIT_DATASET_TARGET_SHA256,
    PROTOCOL_ID,
    TARGET_FINGERPRINT_SCHEMA_VERSION,
    file_sha256,
    target_sha256,
    legacy_comparable_target_sha256,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODEL_ROOT = PROJECT_ROOT / "artifacts" / "models"
EXPECTED_PACKAGES = {
    "mqt.predictor": "2.4.0",
    "mqt.bench": "2.2.3",
    "qiskit": "2.5.0",
    "qiskit-aer": "0.17.2",
    "qiskit-ibm-runtime": "0.47.0",
    "qiskit-qasm3-import": "0.6.0",
    "pytket": "2.18.1",
    "pytket-qiskit": "0.77.0",
    "bqskit": "1.2.1",
    "numpy": "2.5.1",
    "scikit-learn": "1.9.0",
    "sb3-contrib": "2.9.0",
    "stable-baselines3": "2.9.0",
    "gymnasium": "1.3.0",
    "torch": "2.13.0",
    "joblib": "1.5.3",
    "tensorboard": "2.21.0",
}


def parse_args() -> argparse.Namespace:
    """Parse readiness gates separately from the basic installation check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-models",
        action="store_true",
        help="Fallisce se i cinque modelli RL e il selettore ML non sono pronti e sincronizzati.",
    )
    parser.add_argument(
        "--require-frozen-targets",
        action="store_true",
        help="Fallisce se i Target differiscono dai fingerprint congelati del protocollo migrato 2.4-v2.",
    )
    return parser.parse_args()


def validate_model_pair(
    label: str,
    canonical: Path,
    runtime: Path,
    *,
    kind: str,
    device_name: str | None = None,
) -> list[str]:
    """Validate one canonical/runtime pair and return readiness problems."""
    validator = validate_rl_archive if kind == "rl" else validate_ml_classifier
    problems: list[str] = []
    canonical_digest: str | None = None
    for location, path in (("canonico", canonical), ("runtime", runtime)):
        _metadata, errors = validator(path)
        problems.extend(f"{location}: {message}" for message in errors)
    if not problems:
        canonical_digest = file_sha256(canonical)
        runtime_digest = file_sha256(runtime)
        if canonical_digest != runtime_digest:
            problems.append(
                "copia runtime diversa dal modello canonico: "
                f"{canonical_digest} != {runtime_digest}"
            )
        elif kind == "rl" and device_name is not None:
            _metadata, metadata_errors = validate_rl_training_metadata(
                canonical.with_suffix(".metadata.json"),
                device_name=device_name,
                model_sha256=canonical_digest,
            )
            problems.extend(
                f"metadati: {message}" for message in metadata_errors
            )
    if problems:
        print(f"{label:<44} NON PRONTO")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print(f"{label:<44} OK  sha256={canonical_digest}")
    return problems


def main() -> int:
    """Print diagnostics and fail only the gates requested by the caller."""
    args = parse_args()
    installation_errors: list[str] = []

    print("=== Ambiente Python ===")
    print(f"Python:      {platform.python_version()}")
    print(f"Eseguibile:  {sys.executable}")
    print(f"Sistema:     {platform.platform()}")
    if sys.version_info[:2] != (3, 12):
        installation_errors.append(
            f"Python deve essere 3.12, trovato {platform.python_version()}."
        )
    if platform.system() != "Linux":
        installation_errors.append("La pipeline robusta è supportata soltanto su Linux/WSL.")

    print("\n=== Versioni fissate da MQT Predictor 2.4.0 ===")
    packages_available = True
    for package, expected in EXPECTED_PACKAGES.items():
        try:
            observed = version(package)
        except PackageNotFoundError:
            observed = "MANCANTE"
            packages_available = False
        status = "OK" if observed == expected else f"ATTESO {expected}"
        print(f"{package:<24} {observed:<18} {status}")
        if observed != expected:
            installation_errors.append(
                f"Versione non conforme per {package}: attesa={expected}, osservata={observed}."
            )

    if not packages_available:
        print("\nInstallazione incompleta; salto Target e modelli.", file=sys.stderr)
        return 1

    from mqt.bench.targets import get_available_device_names, get_device
    from mqt.predictor.ml.helper import get_path_training_data as get_ml_training_data
    from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir

    print("\n=== Protocollo sperimentale congelato ===")
    print(f"Protocollo:       {PROTOCOL_ID}")
    print(f"Schema Target:    v{TARGET_FINGERPRINT_SCHEMA_VERSION}")
    print(f"Figure of merit: {FIGURE_OF_MERIT}")
    available_names = set(get_available_device_names())
    target_mismatches = 0
    legacy_target_drifts = 0
    for device_name in FROZEN_DEVICES:
        if device_name not in available_names:
            installation_errors.append(f"Device MQT Bench mancante: {device_name}.")
            print(f"{device_name:<24} MANCANTE")
            continue
        target = get_device(device_name)
        observed_hash = target_sha256(target)
        expected_hash = FROZEN_TARGET_SHA256[device_name]
        legacy_hash = LEGACY_QISKIT_DATASET_TARGET_SHA256[device_name]
        legacy_comparable_hash = legacy_comparable_target_sha256(target)
        matches = observed_hash == expected_hash
        target_mismatches += int(not matches)
        legacy_target_drifts += int(legacy_comparable_hash != legacy_hash)
        print(
            f"{device_name:<24} qubit={target.num_qubits:<3} "
            f"fingerprint={'OK' if matches else 'DIVERSO'}"
        )
        print(f"  protocollo 2.4-v2:       {expected_hash}")
        print(f"  ambiente corrente:       {observed_hash}")
        print(f"  legacy registrato:       {legacy_hash}")
        print(f"  corrente schema legacy:  {legacy_comparable_hash}")
        if str(target.description) != device_name:
            installation_errors.append(
                f"Descrizione Target inattesa per {device_name}: {target.description}."
            )

    if legacy_target_drifts:
        schema_only_targets = len(FROZEN_DEVICES) - legacy_target_drifts
        schema_verb = "differisce" if schema_only_targets == 1 else "differiscono"
        print(
            "\nMIGRAZIONE TARGET ATTESA: "
            f"{legacy_target_drifts}/{len(FROZEN_DEVICES)} Target MQT Bench 2.2.3 "
            "differiscono nei dati nativi dalle impronte MQT Bench 2.0.0 del branch "
            "qiskit_dataset, dopo avere normalizzato schema e control-flow. "
            f"{schema_only_targets} Target {schema_verb} "
            "soltanto per rappresentazione/schema. Poiché cambia anche la versione "
            "Qiskit, rigenera comunque per tutti i device Qiskit default/random e "
            "gli score oracle nell'ambiente 2.4.0 prima del confronto finale."
        )

    if target_mismatches:
        print(
            "\nATTENZIONE: i Target dell'ambiente corrente non coincidono con "
            "i fingerprint congelati del protocollo migrato 2.4-v2. "
            "Non produrre risultati pubblicabili finché il drift non è stato risolto."
        )
        if args.require_frozen_targets:
            installation_errors.append(
                f"{target_mismatches} Target differiscono dal protocollo migrato 2.4-v2."
            )

    print("\n=== Artefatti richiesti da qcompile ===")
    runtime_rl = get_rl_model_dir()
    runtime_ml = get_ml_training_data() / "trained_model"
    model_problems: list[str] = []
    for device_name in FROZEN_DEVICES:
        filename = rl_model_filename(device_name)
        model_problems.extend(
            validate_model_pair(
                filename,
                CANONICAL_MODEL_ROOT / "rl" / filename,
                runtime_rl / filename,
                kind="rl",
                device_name=device_name,
            )
        )
    model_problems.extend(
        validate_model_pair(
            ML_MODEL_FILENAME,
            CANONICAL_MODEL_ROOT / "ml" / ML_MODEL_FILENAME,
            runtime_ml / ML_MODEL_FILENAME,
            kind="ml",
        )
    )

    if model_problems:
        print(
            "\nI pacchetti possono essere installati correttamente anche prima del "
            "training. Per rendere obbligatori gli artefatti usa --require-models."
        )
        if args.require_models:
            installation_errors.append(
                f"Artefatti qcompile non pronti: {len(model_problems)} problemi."
            )

    if installation_errors:
        print("\n=== ESITO: NON CONFORME ===", file=sys.stderr)
        for error in installation_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    readiness = "completa" if not model_problems else "ambiente pronto, modelli da completare"
    print(f"\n=== ESITO: installazione 2.4.0 conforme ({readiness}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

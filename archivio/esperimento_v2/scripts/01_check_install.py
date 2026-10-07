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
    validate_ml_training_metadata,
    validate_rl_archive,
    validate_rl_training_metadata,
)
from mqt_predictor_protocol import (
    CANONICAL_MODEL_ROOT_V2,
    EXPECTED_PACKAGE_VERSIONS,
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    LEGACY_QISKIT_DATASET_TARGET_SHA256,
    PROTOCOL_ID,
    RL_FINAL_TIMESTEPS,
    TARGET_FINGERPRINT_SCHEMA_VERSION,
    file_sha256,
    target_sha256,
    legacy_comparable_target_sha256,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODEL_ROOT = CANONICAL_MODEL_ROOT_V2
EXPECTED_PACKAGES = EXPECTED_PACKAGE_VERSIONS


def parse_args() -> argparse.Namespace:
    """Parse readiness gates separately from the basic installation check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-models",
        action="store_true",
        help='Fail unless the five RL policies and ML selector are ready and synchronized.',
    )
    parser.add_argument(
        "--require-frozen-targets",
        action="store_true",
        help="Fail when Targets differ from the migrated 2.4-v2 protocol's frozen fingerprints.",
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
                f'runtime copy differs from canonical model: {canonical_digest} != {runtime_digest}'
            )
        elif kind == "rl" and device_name is not None:
            _metadata, metadata_errors = validate_rl_training_metadata(
                canonical.with_suffix(".metadata.json"),
                device_name=device_name,
                model_sha256=canonical_digest,
                expected_max_steps=64,
                expected_num_timesteps=RL_FINAL_TIMESTEPS,
            )
            problems.extend(
                f'metadata: {message}' for message in metadata_errors
            )
        elif kind == "ml":
            _metadata, metadata_errors = validate_ml_training_metadata(
                canonical.with_suffix(".metadata.json"),
                model_sha256=canonical_digest,
            )
            problems.extend(
                f'metadata: {message}' for message in metadata_errors
            )
    if problems:
        print(f'{label:<44} NOT READY')
        for problem in problems:
            print(f"  - {problem}")
    else:
        print(f"{label:<44} OK  sha256={canonical_digest}")
    return problems


def main() -> int:
    """Print diagnostics and fail only the gates requested by the caller."""
    args = parse_args()
    installation_errors: list[str] = []

    print('=== Python environment ===')
    print(f"Python:      {platform.python_version()}")
    print(f'Executable: {sys.executable}')
    print(f'System:     {platform.platform()}')
    if sys.version_info[:2] != (3, 12):
        installation_errors.append(
            f'Python 3.12 is required; found {platform.python_version()}.'
        )
    if platform.system() != "Linux":
        installation_errors.append('The robust pipeline supports Linux/WSL only.')

    print("""
=== Versions pinned by MQT Predictor 2.4.0 ===""")
    packages_available = True
    for package, expected in EXPECTED_PACKAGES.items():
        try:
            observed = version(package)
        except PackageNotFoundError:
            observed = 'MISSING'
            packages_available = False
        status = "OK" if observed == expected else f'EXPECTED {expected}'
        print(f"{package:<24} {observed:<18} {status}")
        if observed != expected:
            installation_errors.append(
                f'Version mismatch for {package}: expected={expected}, observed={observed}.'
            )

    if not packages_available:
        print("""
Incomplete installation; skipping Targets and models.""", file=sys.stderr)
        return 1

    from mqt.bench.targets import get_available_device_names, get_device
    from mqt.predictor.ml.helper import get_path_training_data as get_ml_training_data
    from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir

    print("""
=== Frozen experimental protocol ===""")
    print(f'Protocol:         {PROTOCOL_ID}')
    print(f'Target schema:    v{TARGET_FINGERPRINT_SCHEMA_VERSION}')
    print(f"Figure of merit: {FIGURE_OF_MERIT}")
    available_names = set(get_available_device_names())
    target_mismatches = 0
    legacy_target_drifts = 0
    for device_name in FROZEN_DEVICES:
        if device_name not in available_names:
            installation_errors.append(f'Missing MQT Bench device: {device_name}.')
            print(f'{device_name:<24} MISSING')
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
            f"{device_name:<24} qubit={target.num_qubits:<3} fingerprint={('OK' if matches else 'DIFFERENT')}"
        )
        print(f'  protocol 2.4-v2:        {expected_hash}')
        print(f'  current environment:    {observed_hash}')
        print(f'  recorded legacy:        {legacy_hash}')
        print(f'  current legacy schema:  {legacy_comparable_hash}')
        if str(target.description) != device_name:
            installation_errors.append(
                f'Unexpected Target description for {device_name}: {target.description}.'
            )

    if legacy_target_drifts:
        schema_only_targets = len(FROZEN_DEVICES) - legacy_target_drifts
        schema_verb = "differisce" if schema_only_targets == 1 else "differiscono"
        print(
            f"\nEXPECTED TARGET MIGRATION: {legacy_target_drifts}/{len(FROZEN_DEVICES)} MQT Bench 2.2.3 Targets differ in native data from the qiskit_dataset branch's MQT Bench 2.0.0 fingerprints after schema and control-flow normalization. {schema_only_targets} Target {schema_verb} only in representation/schema. Because Qiskit also changed, regenerate Qiskit default/random and oracle scores for every device in the 2.4.0 environment before the final comparison."
        )

    if target_mismatches:
        print(
            """
WARNING: current Targets differ from the migrated 2.4-v2 protocol's frozen fingerprints. Resolve drift before producing publishable results."""
        )
        if args.require_frozen_targets:
            installation_errors.append(
                f'{target_mismatches} Targets differ from migrated protocol 2.4-v2.'
            )

    print("""
=== Artifacts required by qcompile ===""")
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
            """
Packages may be installed correctly before training. Use --require-models to require trained artifacts."""
        )
        if args.require_models:
            installation_errors.append(
                f'qcompile artifacts are not ready: {len(model_problems)} problems.'
            )

    if installation_errors:
        print("""
=== OUTCOME: NONCONFORMING ===""", file=sys.stderr)
        for error in installation_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    readiness = "completa" if not model_problems else 'environment ready; models incomplete'
    print(f'\n=== OUTCOME: conforming 2.4.0 installation ({readiness}) ===')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

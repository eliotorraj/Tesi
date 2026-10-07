"""Orchestrate long MQT Predictor 2.4-v2 protocol phases.

Training, compilation and aggregation remain implemented in numbered scripts. This runner calls them with frozen parameters, keeping operational commands short without creating a second protocol implementation."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mqt_model_artifacts import (  # noqa: E402
    rl_model_filename,
    validate_rl_archive,
    validate_rl_training_metadata,
)
from mqt_predictor_protocol import (  # noqa: E402
    CANONICAL_RL_MODEL_DIR_V2,
    COMPILATION_TIMEOUT_SECONDS,
    EXPERIMENT_ROOT,
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    QISKIT_WORKERS,
    RL_CHECKPOINT_EVERY,
    RL_FINAL_TIMESTEPS,
    RL_ROLLOUT_STEPS,
    RL_TRAINING_TIMESTEPS,
    SOURCE_MANIFEST_V2,
    TRAINING_CIRCUITS_V2,
    file_sha256,
)


CATALOG_V2 = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"
RL_MAX_STEPS = 64
RL_BQSKIT_ACTION_TIMEOUT = 60
RL_SEED = 0
QISKIT_TIMEOUT_SECONDS = COMPILATION_TIMEOUT_SECONDS
ML_CANARY_CIRCUITS = 10

# These names describe only the operational division between two computers.
# These are not scientific data and do not change the model protocol.
RL_GROUPS: dict[str, tuple[str, ...]] = {
    "models": FROZEN_DEVICES,
}


def numbered_script(name: str, *arguments: object) -> list[str]:
    'Use the same Python interpreter that started the runner.'
    return [
        sys.executable,
        str(SCRIPTS_DIR / name),
        *(str(argument) for argument in arguments),
    ]


def run_checked(command: Sequence[str]) -> None:
    'Run a numbered script, preserving its output and exit code.'
    print(f"\n>>> {shlex.join(str(part) for part in command)}", flush=True)
    completed = subprocess.run(list(command), cwd=PROJECT_ROOT, check=False)
    if completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, list(command))


def rl_run_name(device_name: str) -> str:
    'Deterministic run name shared by both computers.'
    return f"v2-{device_name.replace('_', '-')}-seed{RL_SEED}"


def canonical_rl_problems(device_name: str) -> tuple[Path, list[str]]:
    'Check an existing final model before skipping it.'
    model = CANONICAL_RL_MODEL_DIR_V2 / rl_model_filename(device_name)
    metadata = model.with_suffix(".metadata.json")
    if not model.exists() and not metadata.exists():
        return model, []
    if not model.is_file():
        return model, ['canonical archive is missing but metadata is present']

    _archive_metadata, errors = validate_rl_archive(model)
    _training_metadata, metadata_errors = validate_rl_training_metadata(
        metadata,
        device_name=device_name,
        model_sha256=file_sha256(model),
        expected_max_steps=RL_MAX_STEPS,
        expected_num_timesteps=RL_FINAL_TIMESTEPS,
    )
    errors.extend(metadata_errors)
    return model, errors


def checkpoint_problems(path: Path, device_name: str) -> tuple[int, list[str]]:
    'Validate a candidate checkpoint and return completed timesteps.'
    _archive_metadata, errors = validate_rl_archive(path)
    metadata_path = path.with_suffix(".metadata.json")
    metadata, metadata_errors = validate_rl_training_metadata(
        metadata_path,
        device_name=device_name,
        model_sha256=file_sha256(path),
        expected_max_steps=RL_MAX_STEPS,
    )
    errors.extend(metadata_errors)
    if metadata.get("seed") != RL_SEED:
        errors.append(f"seed does not match: {metadata.get('seed')!r}")
    if metadata.get("target_timesteps") != RL_TRAINING_TIMESTEPS:
        errors.append(
            f"target_timesteps does not match: {metadata.get('target_timesteps')!r}"
        )
    if SOURCE_MANIFEST_V2.is_file():
        expected_manifest = file_sha256(SOURCE_MANIFEST_V2)
        if metadata.get("training_manifest_sha256") != expected_manifest:
            errors.append('train circuit manifest does not match')
    try:
        steps = int(metadata.get("num_timesteps"))
    except (TypeError, ValueError):
        steps = -1
    if "interrupted" in path.stem:
        errors.append('emergency snapshot cannot be resumed')
    if steps % RL_ROLLOUT_STEPS:
        errors.append('checkpoint is not aligned with a complete PPO rollout')
    if steps >= RL_TRAINING_TIMESTEPS:
        errors.append(
            'checkpoint already reached final timesteps: investigate the missing canonical model'
        )
    return steps, errors


def latest_valid_checkpoint(device_name: str) -> Path | None:
    'Find the most advanced compatible checkpoint in the planned run.'
    directory = (
        EXPERIMENT_ROOT
        / "checkpoints"
        / "rl"
        / device_name
        / rl_run_name(device_name)
    )
    candidates = sorted(directory.glob("*.zip")) if directory.is_dir() else []
    if not candidates:
        return None

    valid: list[tuple[int, Path]] = []
    rejected: list[str] = []
    for path in candidates:
        steps, errors = checkpoint_problems(path, device_name)
        if errors:
            rejected.append(f"{path.name}: {'; '.join(errors)}")
        else:
            valid.append((steps, path))
    if not valid:
        if rejected and all(
            'emergency snapshot cannot be resumed' in item
            for item in rejected
        ):
            print('No complete PPO rollout saved: restarting from zero.')
            return None
        details = "\n  - ".join(rejected)
        raise SystemExit(
            f'The directory {directory} contains checkpoints, but none is compatible:\n  - {details}'
        )
    valid.sort(key=lambda item: (item[0], item[1].name))
    return valid[-1][1]


def parse_resume_specs(values: Sequence[str]) -> dict[str, Path]:
    'Read repeatable DEVICE=CHECKPOINT overrides.'
    result: dict[str, Path] = {}
    for value in values:
        device_name, separator, raw_path = value.partition("=")
        if not separator or not device_name or not raw_path:
            raise SystemExit(
                '--resume-from requires DEVICE=CHECKPOINT_PATH.zip'
            )
        if device_name not in FROZEN_DEVICES:
            raise SystemExit(f'Device outside the protocol: {device_name}')
        if device_name in result:
            raise SystemExit(f'Duplicate --resume-from for {device_name}')
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.is_file():
            raise SystemExit(f'Checkpoint not found: {path}')
        result[device_name] = path.resolve()
    return result


def selected_rl_devices(args: argparse.Namespace) -> tuple[str, ...]:
    'Resolve a named group or explicit sequence.'
    devices = RL_GROUPS[args.group] if args.group else tuple(args.devices)
    if len(set(devices)) != len(devices):
        raise SystemExit('RL selection contains duplicate devices.')
    return devices


def rl_training_command(device_name: str, resume_from: Path | None) -> list[str]:
    'Build the RL command with every frozen parameter explicit.'
    command = numbered_script(
        "03_train_rl_model.py",
        "--device",
        device_name,
        "--metric",
        FIGURE_OF_MERIT,
        "--training-circuits",
        TRAINING_CIRCUITS_V2,
        "--source-manifest",
        SOURCE_MANIFEST_V2,
        "--timesteps",
        RL_TRAINING_TIMESTEPS,
        "--checkpoint-every",
        RL_CHECKPOINT_EVERY,
        "--max-steps",
        RL_MAX_STEPS,
        "--bqskit-action-timeout",
        RL_BQSKIT_ACTION_TIMEOUT,
        "--seed",
        RL_SEED,
        "--run-name",
        rl_run_name(device_name),
    )
    if resume_from is not None:
        command.extend(("--resume-from", str(resume_from)))
    return command


def run_rl(args: argparse.Namespace) -> None:
    'Train a group sequentially, safely skipping or resuming work.'
    if not TRAINING_CIRCUITS_V2.is_dir() or not SOURCE_MANIFEST_V2.is_file():
        raise SystemExit(
            'v2 sources are not prepared. Run the prepare subcommand first.'
        )
    devices = selected_rl_devices(args)
    explicit_resumes = parse_resume_specs(args.resume_from)
    unused = sorted(set(explicit_resumes) - set(devices))
    if unused:
        raise SystemExit(
            '--resume-from supplied for unselected devices: '
            + ", ".join(unused)
        )

    print('Selected RL devices: ' + ", ".join(devices))
    for device_name in devices:
        model, problems = canonical_rl_problems(device_name)
        if problems:
            raise SystemExit(
                f'Canonical artifact exists but does not match: {model}\n  - '
                + "\n  - ".join(problems)
            )
        if model.exists():
            print(f'\nAlready complete and conforming; skipping: {device_name}')
            continue

        resume_from = explicit_resumes.get(device_name)
        if resume_from is None and not args.no_auto_resume:
            resume_from = latest_valid_checkpoint(device_name)
            if resume_from is not None:
                print(f'Automatic resume of {device_name} da {resume_from}')
        run_checked(rl_training_command(device_name, resume_from))


def run_prepare(_args: argparse.Namespace) -> None:
    'Check the environment and prepare sources through idempotent scripts.'
    commands = (
        numbered_script("01_check_install.py", "--require-frozen-targets"),
        numbered_script("06_prepare_experiment_v2.py", "--check-only"),
        numbered_script("06_prepare_experiment_v2.py"),
        numbered_script("11_freeze_method_plan_v2.py", "--split", "validation"),
        numbered_script("11_freeze_method_plan_v2.py", "--split", "test"),
    )
    for command in commands:
        run_checked(command)


def run_ml_canary(args: argparse.Namespace) -> None:
    'Compile a reusable train batch to calibrate the ML timeout.'
    commands = (
        numbered_script(
            "05_sync_models.py", "install", "--component", "rl", "--overwrite"
        ),
        numbered_script("05_sync_models.py", "verify", "--component", "rl"),
        numbered_script(
            "04_train_device_selector.py",
            "--timeout",
            args.timeout,
            "--startup-timeout",
            args.startup_timeout,
            "--rl-max-steps",
            RL_MAX_STEPS,
            "--seed",
            RL_SEED,
            "--num-workers",
            args.num_workers,
            "--max-attempts",
            args.max_attempts,
            "--rf-workers",
            1,
            "--limit-circuits",
            args.limit_circuits,
            "--compile-only",
        ),
    )
    for command in commands:
        run_checked(command)


def run_ml(args: argparse.Namespace) -> None:
    'Install policies, build the Training set, train ML and check qcompile.'
    commands = (
        numbered_script(
            "05_sync_models.py", "install", "--component", "rl", "--overwrite"
        ),
        numbered_script("05_sync_models.py", "verify", "--component", "rl"),
        numbered_script(
            "04_train_device_selector.py",
            "--timeout",
            args.timeout,
            "--startup-timeout",
            args.startup_timeout,
            "--rl-max-steps",
            RL_MAX_STEPS,
            "--seed",
            RL_SEED,
            "--num-workers",
            args.num_workers,
            "--max-attempts",
            args.max_attempts,
            "--rf-workers",
            args.rf_workers,
        ),
        numbered_script(
            "05_sync_models.py", "install", "--component", "ml", "--overwrite"
        ),
        numbered_script("05_sync_models.py", "verify"),
        numbered_script(
            "01_check_install.py",
            "--require-frozen-targets",
            "--require-models",
        ),
        numbered_script(
            "07_validate_qcompile.py",
            "--timeout",
            args.timeout,
            "--max-steps",
            RL_MAX_STEPS,
        ),
    )
    for command in commands:
        run_checked(command)


def qiskit_prepare_command(device_name: str) -> list[str]:
    'Full preparation command for one device.'
    return numbered_script(
        "07_prepare_qiskit_dataset.py",
        "--scope",
        "full",
        "--catalog",
        CATALOG_V2,
        "--device",
        device_name,
    )


def qiskit_generate_command(
    device_name: str,
    split: str,
    *,
    workers: int,
    timeout_seconds: int,
    limit_runs: int | None = None,
) -> list[str]:
    'Generation command; this runner forbids the Test split.'
    if split not in ("train", "validation"):
        raise ValueError(f'Split is not allowed by the orchestrator: {split}')
    command = numbered_script(
        "08_generate_qiskit_dataset.py",
        "--scope",
        "full",
        "--split",
        split,
        "--catalog",
        CATALOG_V2,
        "--device",
        device_name,
        "--workers",
        workers,
        "--timeout-seconds",
        timeout_seconds,
    )
    if limit_runs is not None:
        command.extend(("--limit-runs", str(limit_runs)))
    return command


def qiskit_view_command(device_name: str) -> list[str]:
    "Command for a device's full views."
    return numbered_script(
        "09_build_qiskit_dataset_views.py",
        "--scope",
        "full",
        "--catalog",
        CATALOG_V2,
        "--device",
        device_name,
        "--top-k",
        3,
    )


def qiskit_aggregate_command() -> list[str]:
    'Strict aggregation command for the five mini-Datasets.'
    return numbered_script(
        "10_aggregate_qiskit_dataset.py",
        "--scope",
        "full",
        "--catalog",
        CATALOG_V2,
        "--top-k",
        3,
        "--require-all-supported",
    )


def run_qiskit_canary(args: argparse.Namespace) -> None:
    'Run one missing train attempt per device.'
    for device_name in FROZEN_DEVICES:
        run_checked(qiskit_prepare_command(device_name))
        run_checked(
            qiskit_generate_command(
                device_name,
                "train",
                workers=args.workers,
                timeout_seconds=args.timeout_seconds,
                limit_runs=1,
            )
        )


def run_qiskit_full(args: argparse.Namespace) -> None:
    'Populate train and validation, create views and aggregate devices.'
    for device_name in FROZEN_DEVICES:
        run_checked(qiskit_prepare_command(device_name))
        for split in ("train", "validation"):
            run_checked(
                qiskit_generate_command(
                    device_name,
                    split,
                    workers=args.workers,
                    timeout_seconds=args.timeout_seconds,
                )
            )
        run_checked(qiskit_view_command(device_name))
    run_checked(qiskit_aggregate_command())


def print_plan(_args: argparse.Namespace) -> None:
    'Show groups and main paths without modifying files.'
    payload = {
        "rl_groups": {name: list(devices) for name, devices in RL_GROUPS.items()},
        "canonical_rl_models": str(CANONICAL_RL_MODEL_DIR_V2),
        "parallel_roles": {
            "dataset_pc": ["qiskit-canary", "qiskit-full"],
            "models_pc": ["rl --group models", "ml-canary", "ml"],
        },
        "rl_checkpoint_every": RL_CHECKPOINT_EVERY,
        "rl_rollout_steps": RL_ROLLOUT_STEPS,
        "rl_requested_timesteps": RL_TRAINING_TIMESTEPS,
        "rl_expected_final_timesteps": RL_FINAL_TIMESTEPS,
        "training_circuits": str(TRAINING_CIRCUITS_V2),
        "source_manifest": str(SOURCE_MANIFEST_V2),
        "qiskit_catalog": str(CATALOG_V2),
        "test_included": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def positive_int(value: str) -> int:
    'argparse type for positive-integer checks.'
    converted = int(value)
    if converted <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return converted


def add_qiskit_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workers", type=positive_int, default=QISKIT_WORKERS)
    parser.add_argument(
        "--timeout-seconds",
        type=positive_int,
        default=QISKIT_TIMEOUT_SECONDS,
    )


def build_parser() -> argparse.ArgumentParser:
    'Build the subcommand interface.'
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="phase", required=True)

    plan = subparsers.add_parser("plan", help='Show groups and paths.')
    plan.set_defaults(handler=print_plan)

    prepare = subparsers.add_parser(
        "prepare",
        help='Check the environment and prepare v2 sources.',
    )
    prepare.set_defaults(handler=run_prepare)

    rl = subparsers.add_parser(
        "rl",
        help='Train an RL group and resume checkpoints.',
    )
    selection = rl.add_mutually_exclusive_group(required=True)
    selection.add_argument("--group", choices=tuple(RL_GROUPS))
    selection.add_argument("--devices", nargs="+", choices=FROZEN_DEVICES)
    rl.add_argument(
        "--resume-from",
        action="append",
        default=[],
        metavar="DEVICE=CHECKPOINT.zip",
        help='Repeatable override; normally rerunning the command is sufficient.',
    )
    rl.add_argument(
        "--no-auto-resume",
        action="store_true",
        help='Do not search automatically for the most advanced checkpoint.',
    )
    rl.set_defaults(handler=run_rl)

    ml_canary = subparsers.add_parser(
        "ml-canary",
        help='Create reusable train checkpoints to calibrate the ML timeout.',
    )
    ml_canary.add_argument("--timeout", type=positive_int, default=COMPILATION_TIMEOUT_SECONDS)
    ml_canary.add_argument("--startup-timeout", type=positive_int, default=240)
    ml_canary.add_argument("--num-workers", type=positive_int, default=1)
    ml_canary.add_argument("--max-attempts", type=positive_int, default=1)
    ml_canary.add_argument(
        "--limit-circuits",
        type=positive_int,
        default=ML_CANARY_CIRCUITS,
    )
    ml_canary.set_defaults(handler=run_ml_canary)

    ml = subparsers.add_parser(
        "ml",
        help='Build the Training set, train ML and validate qcompile.',
    )
    ml.add_argument("--timeout", type=positive_int, default=COMPILATION_TIMEOUT_SECONDS)
    ml.add_argument("--startup-timeout", type=positive_int, default=240)
    ml.add_argument("--num-workers", type=positive_int, default=1)
    ml.add_argument("--max-attempts", type=positive_int, default=3)
    ml.add_argument("--rf-workers", type=positive_int, default=1)
    ml.set_defaults(handler=run_ml)

    qiskit_canary = subparsers.add_parser(
        "qiskit-canary",
        help='Run one missing train attempt for each device.',
    )
    add_qiskit_runtime_options(qiskit_canary)
    qiskit_canary.set_defaults(handler=run_qiskit_canary)

    qiskit_full = subparsers.add_parser(
        "qiskit-full",
        help='Populate train/validation and aggregate the full Dataset.',
    )
    add_qiskit_runtime_options(qiskit_full)
    qiskit_full.set_defaults(handler=run_qiskit_full)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    'Run a phase and report resumable stops concisely.'
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except subprocess.CalledProcessError as error:
        print(
            f'\nPhase stopped: numbered script exited with code {error.returncode}. Fix the cause and rerun the same command; valid durable outputs will be reused.',
            file=sys.stderr,
        )
        return int(error.returncode) or 1
    except KeyboardInterrupt:
        print(
            """
Interruption requested. Wait for the checkpoint-save message, then rerun the same command.""",
            file=sys.stderr,
        )
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

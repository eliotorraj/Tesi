"""Orchestra le fasi lunghe del protocollo MQT Predictor 2.4-v2.

Training, compilazione e aggregazione restano implementati negli script
numerati. Questo file li richiama con i parametri congelati, così i comandi
operativi sono brevi senza creare una seconda implementazione del protocollo.
"""

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
QISKIT_TIMEOUT_SECONDS = 300
ML_CANARY_CIRCUITS = 10

# Questi nomi descrivono soltanto la ripartizione operativa tra due computer.
# Non sono dati scientifici e non cambiano il protocollo dei modelli.
RL_GROUPS: dict[str, tuple[str, ...]] = {
    "models": FROZEN_DEVICES,
}


def numbered_script(name: str, *arguments: object) -> list[str]:
    """Usa lo stesso interprete Python con cui è stato avviato il runner."""
    return [
        sys.executable,
        str(SCRIPTS_DIR / name),
        *(str(argument) for argument in arguments),
    ]


def run_checked(command: Sequence[str]) -> None:
    """Esegue uno script numerato preservandone output e codice di uscita."""
    print(f"\n>>> {shlex.join(str(part) for part in command)}", flush=True)
    completed = subprocess.run(list(command), cwd=PROJECT_ROOT, check=False)
    if completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, list(command))


def rl_run_name(device_name: str) -> str:
    """Nome deterministico della run condiviso dai due computer."""
    return f"v2-{device_name.replace('_', '-')}-seed{RL_SEED}"


def canonical_rl_problems(device_name: str) -> tuple[Path, list[str]]:
    """Controlla un modello finale esistente prima di saltarlo."""
    model = CANONICAL_RL_MODEL_DIR_V2 / rl_model_filename(device_name)
    metadata = model.with_suffix(".metadata.json")
    if not model.exists() and not metadata.exists():
        return model, []
    if not model.is_file():
        return model, ["archivio canonico mancante ma metadati presenti"]

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
    """Valida un checkpoint candidato e restituisce gli step completati."""
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
        errors.append(f"seed non conforme: {metadata.get('seed')!r}")
    if metadata.get("target_timesteps") != RL_TRAINING_TIMESTEPS:
        errors.append(
            "target_timesteps non conforme: "
            f"{metadata.get('target_timesteps')!r}"
        )
    if SOURCE_MANIFEST_V2.is_file():
        expected_manifest = file_sha256(SOURCE_MANIFEST_V2)
        if metadata.get("training_manifest_sha256") != expected_manifest:
            errors.append("manifest dei circuiti train non conforme")
    try:
        steps = int(metadata.get("num_timesteps"))
    except (TypeError, ValueError):
        steps = -1
    if "interrupted" in path.stem:
        errors.append("snapshot di emergenza non riprendibile")
    if steps % RL_ROLLOUT_STEPS:
        errors.append("checkpoint non allineato a un rollout PPO completo")
    if steps >= RL_TRAINING_TIMESTEPS:
        errors.append(
            "checkpoint già al target finale: controlla perché manca "
            "il modello canonico"
        )
    return steps, errors


def latest_valid_checkpoint(device_name: str) -> Path | None:
    """Trova il checkpoint compatibile più avanzato nella run prevista."""
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
            "snapshot di emergenza non riprendibile" in item
            for item in rejected
        ):
            print("Nessun rollout PPO completo salvato: ripartenza da zero.")
            return None
        details = "\n  - ".join(rejected)
        raise SystemExit(
            f"La directory {directory} contiene checkpoint, ma nessuno è "
            f"compatibile:\n  - {details}"
        )
    valid.sort(key=lambda item: (item[0], item[1].name))
    return valid[-1][1]


def parse_resume_specs(values: Sequence[str]) -> dict[str, Path]:
    """Legge gli override ripetibili DEVICE=CHECKPOINT."""
    result: dict[str, Path] = {}
    for value in values:
        device_name, separator, raw_path = value.partition("=")
        if not separator or not device_name or not raw_path:
            raise SystemExit(
                "--resume-from richiede DEVICE=PERCORSO_DEL_CHECKPOINT.zip"
            )
        if device_name not in FROZEN_DEVICES:
            raise SystemExit(f"Device fuori protocollo: {device_name}")
        if device_name in result:
            raise SystemExit(f"--resume-from duplicato per {device_name}")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.is_file():
            raise SystemExit(f"Checkpoint non trovato: {path}")
        result[device_name] = path.resolve()
    return result


def selected_rl_devices(args: argparse.Namespace) -> tuple[str, ...]:
    """Risolve un gruppo nominato oppure una sequenza esplicita."""
    devices = RL_GROUPS[args.group] if args.group else tuple(args.devices)
    if len(set(devices)) != len(devices):
        raise SystemExit("La selezione RL contiene device duplicati.")
    return devices


def rl_training_command(device_name: str, resume_from: Path | None) -> list[str]:
    """Costruisce il comando RL con tutti i parametri congelati espliciti."""
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
    """Allena un gruppo in sequenza, saltando o riprendendo in sicurezza."""
    if not TRAINING_CIRCUITS_V2.is_dir() or not SOURCE_MANIFEST_V2.is_file():
        raise SystemExit(
            "Sorgenti v2 non preparate. Esegui prima il sottocomando prepare."
        )
    devices = selected_rl_devices(args)
    explicit_resumes = parse_resume_specs(args.resume_from)
    unused = sorted(set(explicit_resumes) - set(devices))
    if unused:
        raise SystemExit(
            "--resume-from indicato per device non selezionati: "
            + ", ".join(unused)
        )

    print("Device RL selezionati: " + ", ".join(devices))
    for device_name in devices:
        model, problems = canonical_rl_problems(device_name)
        if problems:
            raise SystemExit(
                f"Artefatto canonico presente ma non conforme: {model}\n  - "
                + "\n  - ".join(problems)
            )
        if model.exists():
            print(f"\nGià completo e conforme, salto: {device_name}")
            continue

        resume_from = explicit_resumes.get(device_name)
        if resume_from is None and not args.no_auto_resume:
            resume_from = latest_valid_checkpoint(device_name)
            if resume_from is not None:
                print(f"Ripresa automatica di {device_name} da {resume_from}")
        run_checked(rl_training_command(device_name, resume_from))


def run_prepare(_args: argparse.Namespace) -> None:
    """Controlla ambiente e prepara le sorgenti con script idempotenti."""
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
    """Compila un lotto train riutilizzabile per calibrare il timeout ML."""
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
    """Installa le policy, crea il Training set, allena ML e prova qcompile."""
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
    """Comando di preparazione full per un device."""
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
    """Comando di generazione; questo runner vieta lo split test."""
    if split not in ("train", "validation"):
        raise ValueError(f"Split non ammesso dall'orchestratore: {split}")
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
    """Comando per le viste full di un device."""
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
    """Comando di aggregazione stretta dei cinque mini-Dataset."""
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
    """Esegue un tentativo train mancante per ciascun device."""
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
    """Popola train e validation, crea le viste e aggrega i device."""
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
    """Mostra gruppi e percorsi principali senza modificare file."""
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
    """Tipo argparse per controlli interi positivi."""
    converted = int(value)
    if converted <= 0:
        raise argparse.ArgumentTypeError("deve essere un intero positivo")
    return converted


def add_qiskit_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workers", type=positive_int, default=QISKIT_WORKERS)
    parser.add_argument(
        "--timeout-seconds",
        type=positive_int,
        default=QISKIT_TIMEOUT_SECONDS,
    )


def build_parser() -> argparse.ArgumentParser:
    """Costruisce l'interfaccia a sottocomandi."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="phase", required=True)

    plan = subparsers.add_parser("plan", help="Mostra gruppi e percorsi.")
    plan.set_defaults(handler=print_plan)

    prepare = subparsers.add_parser(
        "prepare",
        help="Controlla ambiente e prepara le sorgenti v2.",
    )
    prepare.set_defaults(handler=run_prepare)

    rl = subparsers.add_parser(
        "rl",
        help="Allena un gruppo RL e riprende i checkpoint.",
    )
    selection = rl.add_mutually_exclusive_group(required=True)
    selection.add_argument("--group", choices=tuple(RL_GROUPS))
    selection.add_argument("--devices", nargs="+", choices=FROZEN_DEVICES)
    rl.add_argument(
        "--resume-from",
        action="append",
        default=[],
        metavar="DEVICE=CHECKPOINT.zip",
        help="Override ripetibile; di norma basta rilanciare il comando.",
    )
    rl.add_argument(
        "--no-auto-resume",
        action="store_true",
        help="Non cercare automaticamente il checkpoint più avanzato.",
    )
    rl.set_defaults(handler=run_rl)

    ml_canary = subparsers.add_parser(
        "ml-canary",
        help="Crea checkpoint train riutilizzabili per calibrare il timeout ML.",
    )
    ml_canary.add_argument("--timeout", type=positive_int, default=300)
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
        help="Crea il Training set, allena ML e valida qcompile.",
    )
    ml.add_argument("--timeout", type=positive_int, default=300)
    ml.add_argument("--startup-timeout", type=positive_int, default=240)
    ml.add_argument("--num-workers", type=positive_int, default=1)
    ml.add_argument("--max-attempts", type=positive_int, default=3)
    ml.add_argument("--rf-workers", type=positive_int, default=1)
    ml.set_defaults(handler=run_ml)

    qiskit_canary = subparsers.add_parser(
        "qiskit-canary",
        help="Esegue un tentativo train mancante per ogni device.",
    )
    add_qiskit_runtime_options(qiskit_canary)
    qiskit_canary.set_defaults(handler=run_qiskit_canary)

    qiskit_full = subparsers.add_parser(
        "qiskit-full",
        help="Popola train+validation e aggrega il Dataset full.",
    )
    add_qiskit_runtime_options(qiskit_full)
    qiskit_full.set_defaults(handler=run_qiskit_full)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Esegue una fase e rende concisa una fermata riprendibile."""
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except subprocess.CalledProcessError as error:
        print(
            f"\nFase fermata: lo script numerato è uscito con codice "
            f"{error.returncode}. Correggi la causa e rilancia lo stesso "
            "comando; gli output durevoli validi saranno riutilizzati.",
            file=sys.stderr,
        )
        return int(error.returncode) or 1
    except KeyboardInterrupt:
        print(
            "\nInterruzione richiesta. Attendi il messaggio di salvataggio "
            "del checkpoint, poi rilancia lo stesso comando.",
            file=sys.stderr,
        )
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

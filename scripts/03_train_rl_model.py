"""Train a non-smoke RL compiler for one device and figure of merit."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shutil
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Callable, Iterator

# Keep the expensive BQSKit passes tractable. The project override below uses
# max_synthesis_size 2 for ordinary circuits and raises it to 3 only when a
# circuit actually contains a synthesizable three-qubit gate.
os.environ.setdefault("GITHUB_ACTIONS", "true")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_predictor_protocol import FROZEN_DEVICES
from mqt_predictor_protocol import FROZEN_TARGET_SHA256
from mqt_predictor_protocol import FIGURE_OF_MERIT as FROZEN_FIGURE_OF_MERIT
from mqt_predictor_protocol import CANONICAL_RL_MODEL_DIR_V2
from mqt_predictor_protocol import EXPERIMENT_ID
from mqt_predictor_protocol import EXPERIMENT_ROOT
from mqt_predictor_protocol import PROTOCOL_ID
from mqt_predictor_protocol import PROTOCOL_VERSION
from mqt_predictor_protocol import SOURCE_MANIFEST_V2
from mqt_predictor_protocol import RL_CHECKPOINT_EVERY
from mqt_predictor_protocol import RL_ROLLOUT_STEPS
from mqt_predictor_protocol import RL_TRAINING_TIMESTEPS
from mqt_predictor_protocol import TRAINING_CIRCUITS_V2
from mqt_predictor_protocol import file_sha256
from mqt_predictor_protocol import package_version_mismatches
from mqt_predictor_protocol import target_record
from mqt_predictor_protocol import verify_circuit_directory

from bqskit.ir.circuit import Circuit
from bqskit.ir.gates.barrier import BarrierPlaceholder
from bqskit.ir.gates.measure import MeasurementPlaceholder
from mqt.predictor.rl.actions import bqskit_actions as predictor_bqskit_actions
from mqt.bench.targets import get_device
from mqt.predictor.rl import Predictor
from mqt.predictor.rl.helper import get_path_trained_model
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODEL_DIR = CANONICAL_RL_MODEL_DIR_V2
_ORIGINAL_BQSKIT_COMPILE = predictor_bqskit_actions.bqskit_compile


class AtomicCheckpointCallback(BaseCallback):
    """Salva checkpoint e provenienza senza esporre file parziali."""

    def __init__(
        self,
        *,
        save_freq: int,
        save_dir: Path,
        name_prefix: str,
        metadata_factory: Callable[[Path, int], dict[str, Any]],
    ) -> None:
        super().__init__(verbose=0)
        self.save_freq = save_freq
        self.save_dir = save_dir
        self.name_prefix = name_prefix
        self.metadata_factory = metadata_factory

    def _save(self, path: Path, num_timesteps: int) -> Path:
        saved = save_model_atomically(self.model, path)
        write_training_metadata(
            saved.with_suffix(".metadata.json"),
            self.metadata_factory(saved, num_timesteps),
        )
        return saved

    def _on_rollout_start(self) -> None:
        # This hook runs after the previous PPO update. Saving from _on_step
        # would capture a partially collected rollout that SB3 does not
        # serialize, making an apparently aligned resume scientifically wrong.
        num_timesteps = int(self.model.num_timesteps)
        if num_timesteps <= 0:
            return
        rolling = self.save_dir / f"{self.name_prefix}_latest_rollout.zip"
        saved_rolling = self._save(rolling, num_timesteps)
        print(
            f"Snapshot di ripresa aggiornato ({num_timesteps} step): "
            f"{saved_rolling}",
            flush=True,
        )
        if num_timesteps % self.save_freq == 0:
            checkpoint = (
                self.save_dir
                / f"{self.name_prefix}_{num_timesteps}_steps.zip"
            )
            saved_checkpoint = self._save(checkpoint, num_timesteps)
            print(f"Checkpoint periodico: {saved_checkpoint}", flush=True)

    def _on_step(self) -> bool:
        return True


def _contains_three_qubit_gate(circuit: Circuit) -> bool:
    """Return whether ``circuit`` contains a synthesizable three-qubit gate."""
    ignored_gate_types = (BarrierPlaceholder, MeasurementPlaceholder)
    return any(
        gate.num_qudits == 3 and not isinstance(gate, ignored_gate_types)
        for gate in circuit.gate_set_no_blocks
    )


class BQSKitActionTimeoutError(TimeoutError):
    """Raised when one BQSKit action exceeds the bounded training budget."""


@contextmanager
def bqskit_action_timeout(seconds: float) -> Iterator[None]:
    """Bound one BQSKit action so a PPO rollout cannot hang indefinitely."""
    if seconds <= 0 or not hasattr(signal, "setitimer"):
        yield
        return

    def on_alarm(signum: int, frame: Any) -> None:
        del signum, frame
        raise BQSKitActionTimeoutError(
            f"Azione BQSKit interrotta dopo {seconds:.1f}s."
        )

    previous_handler = signal.signal(signal.SIGALRM, on_alarm)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


def configure_bqskit_runtime(seed: int = 0, action_timeout: float = 60.0) -> None:
    """Select MQT's BQSKit synthesis limit from each input circuit.

    MQT's lightweight profile is useful for local training, but it sets
    ``max_synthesis_size=2``. The bundled corpus contains ``ccx`` and
    ``cswap`` gates acting on three qubits, so a BQSKit action otherwise
    aborts PPO on those circuits. Using 3 for every circuit is unnecessarily
    expensive, so this override uses 3 only when a three-qubit gate is
    present and 2 otherwise. The action lambdas resolve ``bqskit_compile``
    when executed; replacing that module-level symbol keeps the 22 action IDs
    and the other lightweight settings unchanged and does not modify
    ``.venv``.
    """

    def compile_with_project_limit(circuit: Circuit, *args: Any, **kwargs: Any) -> Any:
        kwargs["max_synthesis_size"] = 3 if _contains_three_qubit_gate(circuit) else 2
        kwargs["seed"] = seed
        with bqskit_action_timeout(action_timeout):
            return _ORIGINAL_BQSKIT_COMPILE(circuit, *args, **kwargs)

    predictor_bqskit_actions.bqskit_compile = compile_with_project_limit


def load_model_or_exit(checkpoint: Path, **kwargs: Any) -> MaskablePPO:
    """Load a PPO checkpoint and explain common partial-save corruption."""
    try:
        return MaskablePPO.load(checkpoint, **kwargs)
    except RuntimeError as error:
        if "PytorchStreamReader failed locating file" in str(error):
            raise SystemExit(
                "Checkpoint non caricabile, probabilmente per salvataggio interrotto o incompleto:\n"
                f"  {checkpoint}\n"
                "Riprendi da un checkpoint periodico precedente *_steps.zip.\n"
                f"Dettaglio PyTorch: {error}"
            ) from error
        raise


def save_model_atomically(model: MaskablePPO, final_path: Path) -> Path:
    """Avoid leaving a corrupt final checkpoint when saving is interrupted."""
    final_zip = final_path.with_suffix(".zip") if final_path.suffix != ".zip" else final_path
    final_zip.parent.mkdir(parents=True, exist_ok=True)
    temp_path = final_zip.with_name(f".{final_zip.stem}.{os.getpid()}.tmp.zip")
    temp_path.unlink(missing_ok=True)
    model.save(temp_path)
    temp_path.replace(final_zip)
    return final_zip


def install_model_atomically(source: Path, destination: Path) -> None:
    """Install the canonical model into MQT's environment-owned runtime path."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copy2(source, temp)
    os.replace(temp, destination)


def write_training_metadata(path: Path, metadata: dict[str, Any]) -> None:
    """Write reproducibility metadata next to the canonical model."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Per esempio ibm_falcon_27.")
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default="expected_fidelity")
    parser.add_argument("--timesteps", type=int, default=RL_TRAINING_TIMESTEPS)
    parser.add_argument(
        "--training-circuits",
        type=Path,
        default=TRAINING_CIRCUITS_V2,
        help="Directory contenente esattamente i 422 circuiti train congelati.",
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=SOURCE_MANIFEST_V2,
        help="Manifest v2 usato per provare split e hash dei circuiti.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=RL_CHECKPOINT_EVERY,
        help="Salva un checkpoint ogni N step.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=64,
        help="Numero massimo di azioni per episodio RL; evita policy che non terminano.",
    )
    parser.add_argument(
        "--bqskit-action-timeout",
        type=float,
        default=60.0,
        help="Timeout in secondi per una singola azione BQSKit durante il training.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed condiviso da PPO, ambiente e BQSKit per run riproducibili.",
    )
    parser.add_argument(
        "--run-name",
        help=(
            "Identificatore della run usato per isolare checkpoint e log; "
            "se omesso viene generato da timestamp UTC e seed."
        ),
    )
    parser.add_argument(
        "--allow-target-drift",
        action="store_true",
        help="Consenti un Target diverso dal fingerprint congelato del protocollo 2.4-v2.",
    )
    parser.add_argument("--resume-from", type=Path, help="Checkpoint .zip da cui riprendere il training.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Consenti di sovrascrivere un modello esistente.")
    return parser.parse_args()


def main() -> int:
    """Train the RL policy using MQT Predictor's production PPO settings."""
    args = parse_args()
    if args.timesteps <= 0:
        raise SystemExit("--timesteps deve essere positivo.")
    if args.checkpoint_every <= 0:
        raise SystemExit("--checkpoint-every deve essere positivo.")
    if args.checkpoint_every % RL_ROLLOUT_STEPS:
        raise SystemExit(
            "--checkpoint-every deve essere un multiplo del rollout PPO "
            f"({RL_ROLLOUT_STEPS})."
        )
    if args.max_steps <= 0:
        raise SystemExit("--max-steps deve essere positivo.")
    if args.bqskit_action_timeout <= 0:
        raise SystemExit("--bqskit-action-timeout deve essere positivo.")
    expected_final_timesteps = (
        (args.timesteps + RL_ROLLOUT_STEPS - 1)
        // RL_ROLLOUT_STEPS
        * RL_ROLLOUT_STEPS
    )
    if args.run_name and re.fullmatch(r"[A-Za-z0-9_.-]+", args.run_name) is None:
        raise SystemExit(
            "--run-name può contenere soltanto lettere, numeri, punto, trattino e underscore."
        )
    if args.training_circuits and not args.training_circuits.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {args.training_circuits}")
    if args.resume_from and not args.resume_from.is_file():
        raise SystemExit(f"Checkpoint non trovato: {args.resume_from}")

    version_errors = package_version_mismatches()
    if version_errors:
        raise SystemExit(f"Versioni non conformi al protocollo v2: {version_errors}.")
    try:
        training_partition = verify_circuit_directory(
            args.training_circuits,
            allowed_splits=("train",),
            manifest_path=args.source_manifest,
        )
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Training set RL rifiutato: {error}") from error

    device = get_device(args.device)
    current_target = target_record(device)
    uses_frozen_protocol = bool(
        device.description in FROZEN_DEVICES
        and args.metric == FROZEN_FIGURE_OF_MERIT
    )
    target_matches_frozen_protocol = False
    if uses_frozen_protocol:
        expected_target_hash = FROZEN_TARGET_SHA256[device.description]
        observed_target_hash = str(current_target["target_sha256"])
        target_matches_frozen_protocol = observed_target_hash == expected_target_hash
        if not target_matches_frozen_protocol and not args.allow_target_drift:
            raise SystemExit(
                "Target diverso dal protocollo migrato 2.4-v2: "
                f"atteso={expected_target_hash}, osservato={observed_target_hash}. "
                "Usa --allow-target-drift soltanto come bypass temporaneo del gate."
            )
    if uses_frozen_protocol and not target_matches_frozen_protocol:
        print("ATTENZIONE: il modello risultante sarà marcato come fuori protocollo.")
    started_at = datetime.now(UTC)
    run_name = args.run_name or started_at.strftime("%Y%m%dT%H%M%SZ") + f"-seed{args.seed}"
    model_name = f"model_{args.metric}_{device.description}"
    filename = f"model_{args.metric}_{device.description}.zip"
    if args.resume_from:
        resume_name = args.resume_from.name
        compatible_name = (
            resume_name == filename or resume_name.startswith(f"{model_name}_")
        )
        if not compatible_name:
            raise SystemExit(
                f"Checkpoint incompatibile con device/metrica richiesti: {resume_name}"
            )
        metadata_path = args.resume_from.with_suffix(".metadata.json")
        from mqt_model_artifacts import validate_rl_training_metadata

        resume_metadata, metadata_errors = validate_rl_training_metadata(
            metadata_path,
            device_name=str(device.description),
            model_sha256=file_sha256(args.resume_from),
            expected_max_steps=args.max_steps,
        )
        try:
            resume_timesteps = int(resume_metadata.get("num_timesteps"))
        except (TypeError, ValueError):
            resume_timesteps = -1
        if resume_metadata.get("training_manifest_sha256") != training_partition["manifest_sha256"]:
            metadata_errors.append("manifest dei circuiti di training diverso")
        if resume_metadata.get("training_split") != "train":
            metadata_errors.append("checkpoint non legato esclusivamente allo split train")
        if resume_metadata.get("seed") != args.seed:
            metadata_errors.append("seed del checkpoint diverso dalla run richiesta")
        if "interrupted" in args.resume_from.stem:
            metadata_errors.append("snapshot di emergenza non riprendibile")
        if resume_timesteps % RL_ROLLOUT_STEPS:
            metadata_errors.append("checkpoint non allineato a un rollout PPO completo")
        if metadata_errors:
            raise SystemExit(
                "Checkpoint di ripresa privo di provenienza v2 compatibile:\n  - "
                + "\n  - ".join(metadata_errors)
            )
    canonical_model = CANONICAL_MODEL_DIR / filename
    runtime_model = get_path_trained_model() / filename
    if canonical_model.exists() and not args.allow_overwrite:
        raise SystemExit(
            f"Il modello canonico esiste gia: {canonical_model}\n"
            "Usa --allow-overwrite solo se vuoi davvero sostituirlo."
        )

    checkpoint_dir = (
        EXPERIMENT_ROOT
        / "checkpoints"
        / "rl"
        / device.description
        / run_name
    )
    if args.run_name and checkpoint_dir.exists() and not args.resume_from:
        existing_names = {path.name for path in checkpoint_dir.iterdir()}
        restart_safe_names = {
            f"{model_name}_interrupted.zip",
            f"{model_name}_interrupted.metadata.json",
        }
        unexpected_names = sorted(existing_names - restart_safe_names)
        if unexpected_names:
            raise SystemExit(
                f"La directory della run contiene già file: {checkpoint_dir}\n"
                "Scegli un altro --run-name oppure usa --resume-from."
            )
        if existing_names:
            print("Nessun rollout completo disponibile: la run riparte da zero.")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    tensorboard_dir = EXPERIMENT_ROOT / "logs" / "rl" / model_name / run_name
    tensorboard_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Training RL: device={device.description}, metrica={args.metric}, "
        f"target={args.timesteps} step, max_steps={args.max_steps}, seed={args.seed}, "
        f"bqskit_action_timeout={args.bqskit_action_timeout}s, "
        f"contatore finale atteso={expected_final_timesteps}"
    )
    print(f"Run: {run_name}")
    print(f"Checkpoint: {checkpoint_dir} (ogni {args.checkpoint_every} step)")
    set_random_seed(args.seed)
    configure_bqskit_runtime(args.seed, args.bqskit_action_timeout)
    print(
        "BQSKit: profilo locale leggero, "
        "max_synthesis_size=3 con gate a tre qubit, altrimenti 2 "
        f"(override runtime, seed={args.seed}, timeout={args.bqskit_action_timeout}s)"
    )
    predictor = Predictor(
        device=device,
        figure_of_merit=args.metric,
        path_training_circuits=args.training_circuits,
        max_steps=args.max_steps,
    )

    monitor_csv = tensorboard_dir / "monitor.csv"
    predictor.env = Monitor(predictor.env, filename=str(monitor_csv))

    if args.resume_from:
        model = load_model_or_exit(
            args.resume_from,
            env=predictor.env,
            tensorboard_log=str(tensorboard_dir),
        )
        model.set_random_seed(args.seed)
        completed_timesteps = model.num_timesteps
        remaining_timesteps = args.timesteps - completed_timesteps
        if remaining_timesteps <= 0:
            raise SystemExit(
                f"Il checkpoint contiene gia {completed_timesteps} step, almeno quanto il target {args.timesteps}."
            )
        print(f"Ripresa da {args.resume_from}: completati={completed_timesteps}, restanti={remaining_timesteps}")
    else:
        model = MaskablePPO(
            MaskableMultiInputActorCriticPolicy,
            predictor.env,
            verbose=2,
            tensorboard_log=str(tensorboard_dir),
            gamma=0.98,
            n_steps=RL_ROLLOUT_STEPS,
            batch_size=64,
            n_epochs=10,
            seed=args.seed,
        )
        remaining_timesteps = args.timesteps

    def metadata_for(saved_path: Path, num_timesteps: int) -> dict[str, Any]:
        return {
            "checkpoint_every": args.checkpoint_every,
            "bqskit_action_timeout_seconds": args.bqskit_action_timeout,
            "bqskit_profile": "ci-lightweight-dynamic-synthesis",
            "device": str(device.description),
            "experiment_id": EXPERIMENT_ID,
            "figure_of_merit": args.metric,
            "max_steps": args.max_steps,
            "model_sha256": file_sha256(saved_path),
            "mqt_predictor_version": package_version("mqt.predictor"),
            "num_timesteps": num_timesteps,
            "protocol": PROTOCOL_ID if target_matches_frozen_protocol else None,
            "protocol_version": PROTOCOL_VERSION,
            "target_matches_frozen_protocol": target_matches_frozen_protocol,
            "resume_from": str(args.resume_from.resolve()) if args.resume_from else None,
            "run_name": run_name,
            "seed": args.seed,
            "rollout_steps": RL_ROLLOUT_STEPS,
            "started_at": started_at.isoformat(),
            "software": {
                distribution: package_version(distribution)
                for distribution in (
                    "mqt.predictor",
                    "mqt.bench",
                    "bqskit",
                    "qiskit",
                    "sb3-contrib",
                    "stable-baselines3",
                )
            },
            "target": current_target,
            "target_timesteps": args.timesteps,
            "training_circuits": str(args.training_circuits.resolve()),
            "training_circuit_count": training_partition["circuit_count"],
            "training_manifest_sha256": training_partition["manifest_sha256"],
            "training_split": "train",
        }

    checkpoint_callback = AtomicCheckpointCallback(
        save_freq=args.checkpoint_every,
        save_dir=checkpoint_dir,
        name_prefix=model_name,
        metadata_factory=metadata_for,
    )

    try:
        model.learn(
            total_timesteps=remaining_timesteps,
            reset_num_timesteps=args.resume_from is None,
            callback=checkpoint_callback,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        interrupted_path = checkpoint_dir / f"{model_name}_interrupted.zip"
        saved_path = save_model_atomically(model, interrupted_path)
        write_training_metadata(
            saved_path.with_suffix(".metadata.json"),
            metadata_for(saved_path, int(model.num_timesteps)),
        )
        print(
            "\nTraining interrotto. Snapshot diagnostico di emergenza "
            f"(non usato per la ripresa): {saved_path}"
        )
        return 130

    # The workspace copy is authoritative. qcompile also requires a runtime
    # mirror with this exact filename inside the installed package.
    saved_path = save_model_atomically(model, canonical_model)
    install_model_atomically(saved_path, runtime_model)
    metadata_path = saved_path.with_suffix(".metadata.json")
    write_training_metadata(
        metadata_path,
        metadata_for(saved_path, int(model.num_timesteps)),
    )
    print(f"Modello canonico: {saved_path}")
    print(f"Copia runtime installata: {runtime_model}")
    print(f"Metadati training: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

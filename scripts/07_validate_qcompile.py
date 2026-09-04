"""Run strict per-device RL canaries and one end-to-end qcompile canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import sys
import time
import traceback
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from multiprocessing import get_context
from pathlib import Path
from typing import Any

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
    COMPILATION_TIMEOUT_SECONDS,
    EXPERIMENT_ID,
    EXPERIMENT_ROOT,
    FIGURE_OF_MERIT,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    LEGACY_QISKIT_DATASET_TARGET_SHA256,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    RL_FINAL_TIMESTEPS,
    SOURCE_MANIFEST_V2,
    TARGET_FINGERPRINT_SCHEMA_VERSION,
    file_sha256,
    legacy_comparable_target_sha256,
    target_sha256,
    TRAINING_CIRCUITS_V2,
    package_version_mismatches,
    verify_circuit_directory,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = EXPERIMENT_ROOT / "logs" / "qcompile" / "validation_report.json"


def parse_args() -> argparse.Namespace:
    """Parse canary controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circuit", type=Path, help="QASM2 canary appartenente allo split train; usa il primo train se omesso.")
    parser.add_argument("--source-manifest", type=Path, default=SOURCE_MANIFEST_V2)
    parser.add_argument(
        "--timeout",
        type=int,
        default=COMPILATION_TIMEOUT_SECONDS,
        help="Timeout totale per ciascun processo.",
    )
    parser.add_argument("--max-steps", type=int, default=64, help="Limite azioni per i canary RL diretti.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-qcompile", action="store_true", help="Esegue solo i cinque canary RL diretti.")
    parser.add_argument(
        "--allow-target-drift",
        action="store_true",
        help="Esegue i canary anche se i Target differiscono dal protocollo migrato 2.4-v2.",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout deve essere positivo.")
    if args.timeout != COMPILATION_TIMEOUT_SECONDS:
        parser.error(
            "il protocollo v2 richiede "
            f"--timeout {COMPILATION_TIMEOUT_SECONDS}."
        )
    if args.max_steps <= 0:
        parser.error("--max-steps deve essere positivo.")
    if args.circuit is not None and not args.circuit.is_file():
        parser.error(f"Circuito non trovato: {args.circuit}")
    return args


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    """Persist the audit even when one or more canaries fail."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def training_qasm(path: Path | None, manifest_path: Path) -> tuple[str, str]:
    """Load only a circuit whose SHA-256 belongs to the frozen train split."""
    verify_circuit_directory(
        TRAINING_CIRCUITS_V2,
        allowed_splits=("train",),
        manifest_path=manifest_path,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    allowed_hashes = {
        str(record["source_sha256"])
        for record in manifest["circuits"]
        if record["split"] == "train"
    }
    chosen = path or sorted(TRAINING_CIRCUITS_V2.glob("*.qasm"))[0]
    observed_hash = file_sha256(chosen)
    if observed_hash not in allowed_hashes:
        raise ValueError(
            f"Il canary non appartiene allo split train congelato: {chosen}"
        )
    return chosen.name, chosen.read_text(encoding="utf-8")


def strict_result_problems(result: dict[str, Any]) -> list[str]:
    """Return reasons why a canary is not a successful MQT RL compilation."""
    problems: list[str] = []
    if result.get("status") != "success":
        problems.append(str(result.get("error", result.get("status", "esito mancante"))))
        return problems
    device_name = result.get("device")
    if device_name not in FROZEN_DEVICES:
        problems.append(f"device fuori protocollo: {device_name}")
    passes = result.get("passes")
    if not isinstance(passes, list) or not passes:
        problems.append("trace azioni vuoto")
    elif passes[-1] != "terminate":
        problems.append("trace non terminato da terminate")
    if result.get("mode") == "rl":
        if result.get("terminated") is not True:
            problems.append("episodio RL non terminato")
        if result.get("truncated") is not False:
            problems.append("episodio RL troncato")
    validation = result.get("validation")
    if not isinstance(validation, dict) or not validation.get("is_executable_on_target"):
        problems.append("circuito non eseguibile sul Target")
    score = result.get("expected_fidelity")
    if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
        problems.append("expected_fidelity non finita")
    return problems


def _canary_worker(
    mode: str,
    qasm: str,
    device_name: str | None,
    max_steps: int,
    connection: Any,
) -> None:
    """Execute one model load and compilation in a disposable process group."""
    os.setsid()
    os.environ.setdefault("GITHUB_ACTIONS", "true")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")
    started = time.monotonic()
    try:
        from mqt.bench.targets import get_device
        from mqt.predictor.reward import expected_fidelity
        from qiskit import QuantumCircuit
        from stable_baselines3.common.utils import set_random_seed

        set_random_seed(0)
        source = QuantumCircuit.from_qasm_str(qasm)
        if mode == "rl":
            assert device_name is not None
            from mqt.predictor.rl import Predictor
            from mqt.predictor.rl.predictor import load_model
            from sb3_contrib.common.maskable.utils import get_action_masks
            import numpy as np

            target = get_device(device_name)
            predictor = Predictor(
                figure_of_merit=FIGURE_OF_MERIT,
                device=target,
                max_steps=max_steps,
            )
            model = load_model(f"model_{FIGURE_OF_MERIT}_{device_name}")
            environment = predictor.env
            observation, _ = environment.reset(source, seed=0)
            passes = []
            terminated = False
            truncated = False
            info: dict[str, Any] = {}
            while not (terminated or truncated):
                action, _ = model.predict(
                    observation,
                    action_masks=get_action_masks(environment),
                    deterministic=True,
                )
                action_index = int(np.asarray(action).item())
                passes.append(str(environment.action_set[action_index].name))
                observation, _reward, terminated, truncated, info = environment.step(
                    action_index
                )
            if environment.error_occurred:
                raise RuntimeError(
                    str(info.get("Truncated because of error") or "errore RL")
                )
            compiled = environment.state
            selected_device = device_name
        elif mode == "qcompile":
            from mqt.predictor.qcompile import qcompile

            compiled, passes, selected_device = qcompile(
                source,
                figure_of_merit=FIGURE_OF_MERIT,
            )
            target = get_device(selected_device)
        else:
            raise ValueError(f"Modalità sconosciuta: {mode}")

        from mqt_predictor_protocol import validate_compiled_circuit

        validation = validate_compiled_circuit(compiled, target)
        score = float(expected_fidelity(compiled, target))
        result = {
            "status": "success",
            "mode": mode,
            "device": str(selected_device),
            "passes": [str(value) for value in passes],
            "expected_fidelity": score,
            "validation": validation,
            "compiled": {
                "num_qubits": int(compiled.num_qubits),
                "depth": int(compiled.depth()),
                "size": int(compiled.size()),
            },
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        if mode == "rl":
            result.update(
                {
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "termination_reason": (
                        "terminate"
                        if terminated and not truncated and passes[-1:] == ["terminate"]
                        else str(info.get("truncation_reason") or "truncated")
                    ),
                }
            )
    except BaseException as error:
        result = {
            "status": "failed",
            "mode": mode,
            "device": device_name,
            "error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(limit=20)[-8000:],
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    try:
        connection.send(result)
    except (BrokenPipeError, EOFError, OSError):
        pass
    finally:
        connection.close()


def terminate_process_group(process: Any) -> None:
    """Terminate the worker and BQSKit descendants without touching the parent."""
    if not process.is_alive():
        return
    try:
        process_group = os.getpgid(process.pid)
    except ProcessLookupError:
        return
    if process_group == process.pid:
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            pass
    else:
        process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        try:
            if process_group == process.pid:
                os.killpg(process_group, signal.SIGKILL)
            else:
                process.kill()
        except ProcessLookupError:
            pass
        process.join(timeout=5)


def run_isolated_canary(
    mode: str,
    qasm: str,
    *,
    device_name: str | None,
    max_steps: int,
    timeout: int,
) -> dict[str, Any]:
    """Run one canary with a hard wall-clock timeout."""
    context = get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(
        target=_canary_worker,
        args=(mode, qasm, device_name, max_steps, send),
        name=f"mqt-canary-{mode}-{device_name or 'selector'}",
    )
    started = time.monotonic()
    process.start()
    send.close()
    result: dict[str, Any] | None = None
    deadline = started + timeout
    try:
        while time.monotonic() < deadline:
            if receive.poll(0.2):
                try:
                    result = receive.recv()
                except EOFError:
                    result = None
                break
            if not process.is_alive():
                break
        if result is None and process.is_alive():
            terminate_process_group(process)
            result = {
                "status": "timeout",
                "mode": mode,
                "device": device_name,
                "error": f"superato timeout totale di {timeout}s",
            }
        elif result is None:
            process.join(timeout=1)
            result = {
                "status": "failed",
                "mode": mode,
                "device": device_name,
                "error": f"processo terminato senza risultato (exit code {process.exitcode})",
            }
    finally:
        receive.close()
        terminate_process_group(process)
        process.join(timeout=1)
    result.setdefault("duration_seconds", round(time.monotonic() - started, 3))
    result["problems"] = strict_result_problems(result)
    result["strict_success"] = not result["problems"]
    return result


def artifact_readiness(expected_max_steps: int) -> tuple[dict[str, Any], list[str]]:
    """Verify exact canonical/runtime model identity before expensive canaries."""
    from mqt.predictor.ml.helper import get_path_training_data
    from mqt.predictor.rl.helper import get_path_trained_model

    canonical_root = CANONICAL_MODEL_ROOT_V2
    runtime_rl = get_path_trained_model()
    runtime_ml = get_path_training_data() / "trained_model"
    report: dict[str, Any] = {}
    problems: list[str] = []

    for device_name in FROZEN_DEVICES:
        filename = rl_model_filename(device_name)
        canonical = canonical_root / "rl" / filename
        runtime = runtime_rl / filename
        item: dict[str, Any] = {}
        for location, path in (("canonical", canonical), ("runtime", runtime)):
            metadata, errors = validate_rl_archive(path)
            item[location] = {**metadata, "errors": errors}
            problems.extend(f"{filename}:{location}:{error}" for error in errors)
        if canonical.is_file() and runtime.is_file():
            item["canonical_sha256"] = file_sha256(canonical)
            item["runtime_sha256"] = file_sha256(runtime)
            if item["canonical_sha256"] != item["runtime_sha256"]:
                problems.append(f"{filename}:canonical/runtime hash mismatch")
            else:
                metadata, errors = validate_rl_training_metadata(
                    canonical.with_suffix(".metadata.json"),
                    device_name=device_name,
                    model_sha256=item["canonical_sha256"],
                    expected_max_steps=expected_max_steps,
                    expected_num_timesteps=RL_FINAL_TIMESTEPS,
                )
                item["training_metadata"] = {**metadata, "errors": errors}
                problems.extend(
                    f"{filename}:metadata:{error}" for error in errors
                )
        report[filename] = item

    canonical_ml = canonical_root / "ml" / ML_MODEL_FILENAME
    runtime_ml_path = runtime_ml / ML_MODEL_FILENAME
    item = {}
    for location, path in (("canonical", canonical_ml), ("runtime", runtime_ml_path)):
        metadata, errors = validate_ml_classifier(path)
        item[location] = {**metadata, "errors": errors}
        problems.extend(f"{ML_MODEL_FILENAME}:{location}:{error}" for error in errors)
    if canonical_ml.is_file() and runtime_ml_path.is_file():
        item["canonical_sha256"] = file_sha256(canonical_ml)
        item["runtime_sha256"] = file_sha256(runtime_ml_path)
        if item["canonical_sha256"] != item["runtime_sha256"]:
            problems.append(f"{ML_MODEL_FILENAME}:canonical/runtime hash mismatch")
        else:
            metadata, errors = validate_ml_training_metadata(
                canonical_ml.with_suffix(".metadata.json"),
                model_sha256=item["canonical_sha256"],
            )
            item["training_metadata"] = {**metadata, "errors": errors}
            problems.extend(
                f"{ML_MODEL_FILENAME}:metadata:{error}" for error in errors
            )
    report[ML_MODEL_FILENAME] = item
    return report, problems


def package_versions() -> dict[str, str | None]:
    """Capture the minimal runtime provenance of the canary."""
    result: dict[str, str | None] = {}
    for name in ("mqt.predictor", "mqt.bench", "qiskit", "sb3-contrib", "stable-baselines3", "torch"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def main() -> int:
    """Run readiness gates followed by five direct RL and one qcompile canary."""
    args = parse_args()
    if os.name != "posix":
        raise SystemExit("Il canary isolato richiede Linux/WSL.")

    version_errors = package_version_mismatches()
    if version_errors:
        raise SystemExit(f"Versioni non conformi al protocollo v2: {version_errors}.")
    try:
        circuit_name, qasm = training_qasm(args.circuit, args.source_manifest)
    except (FileNotFoundError, IndexError, KeyError, ValueError) as error:
        raise SystemExit(f"Canary rifiutato: {error}") from error
    from mqt.bench.targets import get_device

    targets = {name: get_device(name) for name in FROZEN_DEVICES}
    fingerprints: dict[str, dict[str, Any]] = {}
    for name, target in targets.items():
        observed = target_sha256(target)
        legacy_comparable = legacy_comparable_target_sha256(target)
        fingerprints[name] = {
            "expected": FROZEN_TARGET_SHA256[name],
            "observed": observed,
            "matches_frozen": observed == FROZEN_TARGET_SHA256[name],
            "legacy_qiskit_dataset": LEGACY_QISKIT_DATASET_TARGET_SHA256[name],
            "legacy_comparable_observed": legacy_comparable,
            "differs_from_legacy_native_data": legacy_comparable
            != LEGACY_QISKIT_DATASET_TARGET_SHA256[name],
        }
    target_drift = [name for name, record in fingerprints.items() if not record["matches_frozen"]]
    artifacts, artifact_problems = artifact_readiness(args.max_steps)

    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "figure_of_merit": FIGURE_OF_MERIT,
        "experiment_id": EXPERIMENT_ID,
        "protocol": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "target_fingerprint_schema_version": TARGET_FINGERPRINT_SCHEMA_VERSION,
        "frozen_devices": list(FROZEN_DEVICES),
        "packages": package_versions(),
        "source_circuit": {
            "name": circuit_name,
            "sha256": hashlib.sha256(qasm.encode("utf-8")).hexdigest(),
        },
        "limits": {"max_steps": args.max_steps, "timeout_seconds": args.timeout},
        "target_fingerprints": fingerprints,
        "artifacts": artifacts,
        "artifact_problems": artifact_problems,
        "results": [],
    }

    if artifact_problems or (target_drift and not args.allow_target_drift):
        report["status"] = "blocked_before_canary"
        report["target_drift"] = target_drift
        atomic_json_write(args.output, report)
        print(f"Verifica bloccata; report: {args.output}")
        if artifact_problems:
            print("Artefatti non pronti:")
            for problem in artifact_problems:
                print(f"  - {problem}")
        if target_drift and not args.allow_target_drift:
            print(
                "Target diversi dal protocollo: "
                + ", ".join(target_drift)
                + ". Usa --allow-target-drift solo dopo aver deciso come riallineare i competitor."
            )
        return 1

    for device_name in FROZEN_DEVICES:
        print(f"Canary RL diretto: {device_name}")
        result = run_isolated_canary(
            "rl",
            qasm,
            device_name=device_name,
            max_steps=args.max_steps,
            timeout=args.timeout,
        )
        report["results"].append(result)
        print("  OK" if result["strict_success"] else "  FALLITO: " + "; ".join(result["problems"]))

    if not args.skip_qcompile:
        print("Canary end-to-end: qcompile")
        result = run_isolated_canary(
            "qcompile",
            qasm,
            device_name=None,
            max_steps=args.max_steps,
            timeout=args.timeout,
        )
        report["results"].append(result)
        print("  OK" if result["strict_success"] else "  FALLITO: " + "; ".join(result["problems"]))

    report["status"] = (
        "success"
        if report["results"] and all(item["strict_success"] for item in report["results"])
        else "failed"
    )
    atomic_json_write(args.output, report)
    print(f"Report canary: {args.output}")
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

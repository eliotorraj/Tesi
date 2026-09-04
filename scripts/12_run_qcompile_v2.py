"""Esegue qcompile tre volte per circuito con timeout e ripresa rigorosa."""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
import traceback
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_model_artifacts import validate_model_set
from mqt_predictor_protocol import (
    COMPILATION_TIMEOUT_SECONDS,
    EXPERIMENT_ID,
    FROZEN_TARGET_SHA256,
    METHOD_RESULTS_DIR_V2,
    PROTOCOL_VERSION,
    SOURCE_MANIFEST_V2,
    file_sha256,
    installed_package_versions,
    package_version_mismatches,
    target_sha256,
    validate_compiled_circuit,
    validate_test_release_record,
)
from qiskit_dataset.experiment_v2 import (
    QCOMPILE_METHOD_ID,
    atomic_jsonl_write,
    source_manifest,
    split_circuits,
    stable_sha256,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument(
        "--timeout",
        type=int,
        default=COMPILATION_TIMEOUT_SECONDS,
    )
    parser.add_argument("--limit-circuits", type=int)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _worker(qasm: str, connection: Any) -> None:
    """Esegue una singola invocazione qcompile in un nuovo process group."""
    os.setsid()
    os.environ.setdefault("GITHUB_ACTIONS", "true")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")
    started = time.monotonic()
    try:
        from mqt.bench.targets import get_device
        from mqt.predictor.qcompile import qcompile
        from mqt.predictor.reward import expected_fidelity
        from qiskit import QuantumCircuit

        source = QuantumCircuit.from_qasm_str(qasm)
        compiled, passes, selected_device = qcompile(
            source,
            figure_of_merit="expected_fidelity",
        )
        normalized_passes = [str(value) for value in passes]
        if not normalized_passes or normalized_passes[-1] != "terminate":
            raise RuntimeError(
                "Trace qcompile vuota o non conclusa dall'azione terminate."
            )
        target = get_device(selected_device)
        observed_target = target_sha256(target)
        if observed_target != FROZEN_TARGET_SHA256[selected_device]:
            raise RuntimeError(
                f"Target drift per {selected_device}: {observed_target}."
            )
        validation = validate_compiled_circuit(compiled, target)
        if not validation["is_executable_on_target"]:
            raise RuntimeError(f"Circuito qcompile non valido: {validation}.")
        score = float(expected_fidelity(compiled, target))
        if not math.isfinite(score):
            raise RuntimeError(f"Score qcompile non finito: {score!r}.")
        result = {
            "status": "success",
            "selected_device_id": str(selected_device),
            "target_sha256": observed_target,
            "passes": normalized_passes,
            "score": score,
            "target_validation": validation,
            "compiled_circuit": {
                "num_qubits": int(compiled.num_qubits),
                "depth": int(compiled.depth()),
                "size": int(compiled.size()),
            },
            "failure": None,
        }
    except BaseException as error:
        result = {
            "status": "failure",
            "selected_device_id": None,
            "target_sha256": None,
            "passes": [],
            "score": None,
            "target_validation": None,
            "compiled_circuit": None,
            "failure": {
                "category": "mqt_predictor_error",
                "exception_type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(limit=20)[-8000:],
            },
        }
    result["duration_seconds"] = round(time.monotonic() - started, 6)
    try:
        connection.send(result)
    except (BrokenPipeError, EOFError, OSError):
        pass
    finally:
        connection.close()


def _terminate(process: Any) -> None:
    if not process.is_alive():
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()


def run_once(qasm: str, timeout: int) -> dict[str, Any]:
    """Applica un timeout reale all'intero processo e ai discendenti."""
    context = get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(qasm, send))
    process.start()
    send.close()
    result: dict[str, Any] | None = None
    started = time.monotonic()
    try:
        if receive.poll(timeout):
            result = receive.recv()
        else:
            _terminate(process)
            result = {
                "status": "timeout",
                "selected_device_id": None,
                "target_sha256": None,
                "passes": [],
                "score": None,
                "target_validation": None,
                "compiled_circuit": None,
                "duration_seconds": round(time.monotonic() - started, 6),
                "failure": {
                    "category": "compilation_timeout",
                    "exception_type": "TimeoutError",
                    "message": f"qcompile ha superato {timeout} secondi.",
                    "traceback": None,
                },
            }
    finally:
        receive.close()
        _terminate(process)
        process.join(timeout=1)
    assert result is not None
    return result


def _load_existing(
    path: Path,
    expected: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Accetta solo checkpoint terminali con identità ancora valida."""
    if not path.is_file():
        return {}
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: JSON non valido.") from error
            run_id = str(record.get("run_id", ""))
            reference = expected.get(run_id)
            if (
                reference is None
                or record.get("status") not in {"success", "failure", "timeout"}
                or record.get("experiment_id") != EXPERIMENT_ID
                or record.get("protocol_version") != PROTOCOL_VERSION
                or record.get("method_id") != QCOMPILE_METHOD_ID
                or record.get("split") != reference["split"]
                or record.get("circuit_id") != reference["circuit_id"]
                or record.get("source_sha256") != reference["source_sha256"]
                or record.get("repetition_index") != reference["repetition_index"]
                or record.get("provenance", {}).get("model_set_sha256")
                != reference["model_set_sha256"]
                or record.get("provenance", {}).get("source_manifest_sha256")
                != file_sha256(SOURCE_MANIFEST_V2)
                or record.get("provenance", {}).get("software")
                != installed_package_versions()
                or record.get("provenance", {}).get("timeout_seconds")
                != COMPILATION_TIMEOUT_SECONDS
            ):
                raise ValueError(
                    f"{path}:{line_number}: checkpoint qcompile fuori contratto."
                )
            if run_id in records:
                raise ValueError(f"{path}:{line_number}: run_id duplicato.")
            records[run_id] = record
    return records


def main() -> int:
    args = parse_args()
    if os.name != "posix":
        raise SystemExit("Il runner qcompile richiede Linux/WSL.")
    if args.timeout <= 0:
        raise SystemExit("--timeout deve essere positivo.")
    if args.timeout != COMPILATION_TIMEOUT_SECONDS:
        raise SystemExit(
            "Il protocollo v2 richiede "
            f"--timeout {COMPILATION_TIMEOUT_SECONDS}."
        )
    if args.limit_circuits is not None and args.limit_circuits <= 0:
        raise SystemExit("--limit-circuits deve essere positivo.")
    if args.split == "test":
        validate_test_release_record()
    version_errors = package_version_mismatches()
    if version_errors:
        raise SystemExit(f"Versioni non conformi al protocollo v2: {version_errors}.")
    model_report, model_errors = validate_model_set(expected_max_steps=64)
    if model_errors:
        raise SystemExit(
            "qcompile non è pronto; modelli canonici/runtime non conformi:\n  - "
            + "\n  - ".join(model_errors)
        )
    model_hashes = {
        name: item["canonical_sha256"]
        for name, item in model_report.items()
    }
    model_set_sha256 = stable_sha256(model_hashes)
    manifest = source_manifest()
    circuits = split_circuits(args.split, manifest)
    expected: dict[str, dict[str, Any]] = {}
    ordered_jobs: list[tuple[dict[str, Any], int, str]] = []
    for circuit in circuits:
        for repetition_index in range(3):
            identity = {
                "experiment_id": EXPERIMENT_ID,
                "protocol_version": PROTOCOL_VERSION,
                "method_id": QCOMPILE_METHOD_ID,
                "split": args.split,
                "circuit_id": circuit["circuit_id"],
                "source_sha256": circuit["source_sha256"],
                "repetition_index": repetition_index,
                "model_set_sha256": model_set_sha256,
            }
            run_id = "mqt_run_" + stable_sha256(identity)
            expected[run_id] = {**identity, "run_id": run_id}
            ordered_jobs.append((circuit, repetition_index, run_id))

    output = args.output or (
        METHOD_RESULTS_DIR_V2 / args.split / "mqt_qcompile_runs.jsonl"
    )
    try:
        completed = _load_existing(output, expected)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    pending_circuit_hashes = []
    for circuit in circuits:
        source_hash = str(circuit["source_sha256"])
        if any(
            run_id not in completed
            for item, _repetition, run_id in ordered_jobs
            if item["source_sha256"] == source_hash
        ):
            pending_circuit_hashes.append(source_hash)
    if args.limit_circuits is not None:
        allowed_hashes = set(pending_circuit_hashes[: args.limit_circuits])
    else:
        allowed_hashes = set(pending_circuit_hashes)

    packages = installed_package_versions()
    for circuit, repetition_index, run_id in ordered_jobs:
        if run_id in completed or circuit["source_sha256"] not in allowed_hashes:
            continue
        source_path = (PROJECT_ROOT / str(circuit["source_ref"])).resolve()
        try:
            source_path.relative_to(PROJECT_ROOT.resolve())
        except ValueError as error:
            raise SystemExit(f"source_ref fuori repository: {source_path}") from error
        if not source_path.is_file() or file_sha256(source_path) != circuit["source_sha256"]:
            raise SystemExit(f"Circuito sorgente mancante o modificato: {source_path}")
        print(
            f"qcompile {circuit['circuit_id']} "
            f"ripetizione {repetition_index + 1}/3",
            flush=True,
        )
        result = run_once(source_path.read_text(encoding="utf-8"), args.timeout)
        record = {
            "schema_version": "1.0.0",
            "experiment_id": EXPERIMENT_ID,
            "protocol_version": PROTOCOL_VERSION,
            "method_id": QCOMPILE_METHOD_ID,
            "split": args.split,
            "run_id": run_id,
            "circuit_id": circuit["circuit_id"],
            "source_sha256": circuit["source_sha256"],
            "repetition_index": repetition_index,
            **result,
            "provenance": {
                "source_manifest_sha256": file_sha256(SOURCE_MANIFEST_V2),
                "model_set_sha256": model_set_sha256,
                "model_hashes": model_hashes,
                "software": packages,
                "controlled_seed": None,
                "repetition_semantics": "fresh_process_without_exposed_seed",
                "timeout_seconds": args.timeout,
            },
        }
        completed[run_id] = record
        atomic_jsonl_write(
            output,
            [
                completed[item_run_id]
                for _item, _repetition, item_run_id in ordered_jobs
                if item_run_id in completed
            ],
        )
        print(f"  {record['status']}", flush=True)

    print(
        f"Checkpoint qcompile: {output} "
        f"({len(completed)}/{len(expected)} ripetizioni terminali)"
    )
    if args.limit_circuits is not None:
        selected_run_ids = {
            run_id
            for circuit, _repetition, run_id in ordered_jobs
            if circuit["source_sha256"] in allowed_hashes
        }
        return 0 if selected_run_ids.issubset(completed) else 2
    return 0 if len(completed) == len(expected) else 2


if __name__ == "__main__":
    raise SystemExit(main())

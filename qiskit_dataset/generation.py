"""Esegue e riprende i tentativi di compilazione diretta con Qiskit."""

from __future__ import annotations

import json
import math
import multiprocessing
import re
import signal
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import contextmanager
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Iterator, Mapping

from .catalog import ConfigurationCatalog
from .core import (
    PROJECT_ROOT,
    SCHEMA_VERSION,
    atomic_json_write,
    atomic_jsonl_write,
    atomic_text_write,
    canonical_json,
    dataset_scope_root,
    expand_attempts,
    finite_float,
    load_manifest,
    package_versions,
    resolve_circuit_source,
    sha256_bytes,
)


CACHE_ROOT = PROJECT_ROOT / "artifacts" / "qiskit_dataset_cache"


class AttemptTimeoutError(TimeoutError):
    """Segnala che un tentativo Qiskit ha superato il tempo massimo."""


class TargetValidationError(RuntimeError):
    """Segnala che il circuito compilato non rispetta il dispositivo."""


_TIMEOUT_LIMITATIONS = (
    "Il callback pubblico di Qiskit viene eseguito dopo ogni pass: "
    "last_completed_pass non identifica necessariamente il pass interrotto.",
    "Lo stack indica dove SIGALRM è stato osservato, non dimostra quale pass, "
    "configurazione, circuito o hardware abbia causato il timeout.",
    "Un'attribuzione causale richiede confronti controllati tra circuiti, "
    "configurazioni e device.",
)
_TRACEBACK_FRAME_RE = re.compile(
    r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<function>[^\n]+)$',
    re.MULTILINE,
)
_STAGE_MARKERS_QISKIT_2_1_1 = (
    ("qiskit/transpiler/passes/layout/vf2_post_layout.py", "optimization"),
    ("qiskit/transpiler/passes/routing/lookahead_swap.py", "routing"),
    ("qiskit/transpiler/passes/routing/sabre_swap.py", "routing"),
    ("qiskit/transpiler/passes/routing/basic_swap.py", "routing"),
    ("qiskit/transpiler/passes/routing/stochastic_swap.py", "routing"),
    ("qiskit/transpiler/passes/layout/sabre_layout.py", "layout"),
    ("qiskit/transpiler/passes/layout/dense_layout.py", "layout"),
    ("qiskit/transpiler/passes/layout/trivial_layout.py", "layout"),
    ("qiskit/transpiler/passes/layout/vf2_layout.py", "layout"),
)


def _pass_identity(pass_: Any) -> tuple[str, str]:
    """Ricava nome e classe di un passaggio interno di Qiskit."""
    pass_class = f"{type(pass_).__module__}.{type(pass_).__qualname__}"
    try:
        candidate = pass_.name()
    except Exception:
        candidate = type(pass_).__name__
    return str(candidate or type(pass_).__name__), pass_class


def _capture_completed_pass(
    progress: dict[str, Any],
    transpilation_started: float,
    callback_data: Mapping[str, Any],
) -> None:
    """Registra soltanto i dati forniti da Qiskit dopo ogni passaggio."""
    pass_ = callback_data.get("pass_")
    if pass_ is None:
        return
    pass_name, pass_class = _pass_identity(pass_)
    raw_index = callback_data.get("count")
    try:
        pass_index = None if raw_index is None else int(raw_index)
    except (TypeError, ValueError):
        pass_index = None
    try:
        pass_duration = finite_float(callback_data.get("time"))
    except (TypeError, ValueError, OverflowError):
        pass_duration = None
    progress["completed_pass_count"] = (
        pass_index + 1
        if pass_index is not None
        else int(progress.get("completed_pass_count", 0)) + 1
    )
    progress["last_completed_pass"] = {
        "name": pass_name,
        "class": pass_class,
        "index": pass_index,
        "qiskit_reported_duration_seconds": pass_duration,
        "wall_elapsed_seconds": time.perf_counter() - transpilation_started,
    }


def _portable_frame_file(filename: str) -> str:
    """Rende portabile il percorso di un file presente nello stack."""
    normalized = str(filename).replace("\\", "/")
    for marker in ("/site-packages/", "/dist-packages/"):
        if marker in normalized:
            return normalized.split(marker, 1)[1]
    return normalized


def _qiskit_stack_frames(traceback_text: str) -> list[dict[str, Any]]:
    """Estrae dallo stack soltanto i passaggi interni a Qiskit o MQT."""
    frames: list[dict[str, Any]] = []
    for match in _TRACEBACK_FRAME_RE.finditer(traceback_text):
        filename = _portable_frame_file(match.group("file"))
        normalized = "/" + filename.replace("\\", "/").lower()
        if "/qiskit/" not in normalized and "/mqt/" not in normalized:
            continue
        frames.append(
            {
                "file": filename,
                "function": match.group("function").strip(),
                "line": int(match.group("line")),
            }
        )
    return frames


def _timeout_inference(
    interrupted_frame: Mapping[str, Any] | None,
    configuration: Mapping[str, Any],
    qiskit_version: str | None,
) -> dict[str, Any]:
    """Formula una diagnosi prudente sul punto in cui è avvenuto il timeout."""
    filename = (
        ""
        if interrupted_frame is None
        else str(interrupted_frame.get("file", "")).replace("\\", "/").lower()
    )
    marker = stage = None
    if qiskit_version == "2.1.1":
        for candidate_marker, candidate_stage in _STAGE_MARKERS_QISKIT_2_1_1:
            if candidate_marker in filename:
                marker, stage = candidate_marker, candidate_stage
                break
    component = None
    if stage == "routing" and configuration.get("routing_method") is not None:
        component = {
            "name": "routing_method",
            "value": configuration["routing_method"],
        }
    elif stage == "layout" and configuration.get("layout_method") is not None:
        component = {
            "name": "layout_method",
            "value": configuration["layout_method"],
        }
    elif stage == "optimization":
        component = {
            "name": "optimization_level",
            "value": configuration.get("optimization_level"),
        }
    if marker is None:
        basis = [
            "Nessun mapping di stage verificato per il frame e la versione "
            "Qiskit osservati."
        ]
        confidence = "none"
    else:
        basis = [
            f"Lo stack interrotto contiene {marker!r}.",
            "Lo stage è inferito dalla pipeline preset fissata a Qiskit 2.1.1; "
            "non è un segnale runtime né una causa dimostrata.",
        ]
        if component is not None:
            basis.append(
                f"La configurazione usa {component['name']}="
                f"{component['value']!r}."
            )
        confidence = "medium" if component is not None else "low"
    return {
        "qiskit_stage": stage,
        "configuration_component": component,
        "confidence": confidence,
        "basis": basis,
        "causal_attribution_supported": False,
    }


def build_timeout_diagnostics(
    *,
    traceback_text: str,
    phase: str,
    timeout_seconds: Any,
    elapsed_seconds: Any,
    configuration: Mapping[str, Any],
    qiskit_version: str | None,
    progress: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Raccoglie i fatti osservati sul timeout e separa le ipotesi."""
    progress = progress or {}
    frames = _qiskit_stack_frames(traceback_text)
    pass_frames = [
        frame
        for frame in frames
        if "/qiskit/transpiler/passes/"
        in ("/" + str(frame["file"]).replace("\\", "/").lower())
    ]
    interrupted_frame = (
        pass_frames[-1] if pass_frames else (frames[-1] if frames else None)
    )
    has_callback_observation = bool(
        progress.get("last_completed_pass")
        or progress.get("completed_pass_count")
    )
    return {
        "observation_method": (
            "qiskit_post_pass_callback_and_sigalrm_traceback"
            if has_callback_observation
            else "sigalrm_traceback"
        ),
        "observed_phase": phase,
        "timeout_seconds": finite_float(timeout_seconds),
        "elapsed_seconds": finite_float(elapsed_seconds),
        "completed_pass_count": int(progress.get("completed_pass_count", 0)),
        "last_completed_pass": progress.get("last_completed_pass"),
        "interrupted_stack_frame": interrupted_frame,
        "inference": _timeout_inference(
            interrupted_frame,
            configuration,
            qiskit_version,
        ),
        "limitations": list(_TIMEOUT_LIMITATIONS),
    }


def _target_payload(target: Any) -> dict[str, Any]:
    """Converte il dispositivo Qiskit nei dati usati per la sua impronta."""
    instructions: list[dict[str, Any]] = []
    for operation, qargs in target.instructions:
        properties = None
        try:
            properties = target[operation.name].get(qargs)
        except (AttributeError, KeyError, TypeError):
            pass
        instructions.append(
            {
                "name": str(operation.name),
                "qargs": (
                    None
                    if qargs is None
                    else [int(qubit) for qubit in qargs]
                ),
                "error": finite_float(getattr(properties, "error", None)),
                "duration": finite_float(getattr(properties, "duration", None)),
            }
        )
    instructions.sort(
        key=lambda item: (
            item["name"],
            canonical_json(item["qargs"]),
            -1.0 if item["error"] is None else item["error"],
            -1.0 if item["duration"] is None else item["duration"],
        )
    )
    coupling_map = target.build_coupling_map()
    edges = (
        []
        if coupling_map is None
        else sorted(
            [int(source), int(destination)]
            for source, destination in coupling_map.get_edges()
        )
    )
    return {
        "device_id": str(target.description),
        "target_type": f"{type(target).__module__}.{type(target).__qualname__}",
        "num_qubits": int(target.num_qubits),
        "operation_names": sorted(map(str, target.operation_names)),
        "coupling_edges": edges,
        "all_to_all": coupling_map is None,
        "instructions": instructions,
    }


def build_target_record(device_id: str) -> dict[str, Any]:
    """Crea il record stabile che descrive il dispositivo selezionato."""
    from mqt.bench.targets import get_device

    target = get_device(device_id)
    payload = _target_payload(target)
    target_sha256 = sha256_bytes(canonical_json(payload).encode("utf-8"))
    return {
        "device_id": device_id,
        "description": str(target.description),
        "num_qubits": int(target.num_qubits),
        "target_sha256": target_sha256,
        "target_type": payload["target_type"],
        "operation_names": payload["operation_names"],
        "coupling_edge_count": len(payload["coupling_edges"]),
        "provenance": {
            "provider": "mqt.bench.targets.get_device",
            "calibration_kind": "synthetic_deterministic_target",
            "live_hardware_data": False,
        },
    }


@lru_cache(maxsize=2)
def _worker_target(device_id: str) -> Any:
    """Carica una sola volta il dispositivo usato da ciascun processo."""
    from mqt.bench.targets import get_device

    return get_device(device_id)


@contextmanager
def _hard_timeout(seconds: float) -> Iterator[None]:
    """Interrompe il blocco quando supera il tempo massimo disponibile."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def on_alarm(signum: int, frame: Any) -> None:
        """Trasforma il segnale del sistema nell'errore previsto dal flusso."""
        del signum, frame
        raise AttemptTimeoutError(
            f"Tentativo interrotto dopo {seconds:.1f} secondi."
        )

    previous_handler = signal.signal(signal.SIGALRM, on_alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def validate_compiled_circuit(circuit: Any, target: Any) -> dict[str, Any]:
    """Controlla porte e collegamenti del circuito compilato sul dispositivo."""
    from qiskit.transpiler.passes import CheckMap, GatesInBasis

    errors: list[str] = []
    unsupported = sorted(
        set(map(str, circuit.count_ops()))
        - set(map(str, target.operation_names))
        - {"barrier"}
    )
    basis_valid: bool | None = None
    connectivity_valid: bool | None = None
    try:
        checker = GatesInBasis(target=target)
        checker(circuit)
        basis_valid = bool(checker.property_set["all_gates_in_basis"])
    except Exception as error:
        errors.append(f"GatesInBasis:{type(error).__name__}:{error}")
    try:
        coupling_map = target.build_coupling_map()
        if coupling_map is None:
            connectivity_valid = True
        else:
            checker = CheckMap(coupling_map=coupling_map)
            checker(circuit)
            connectivity_valid = bool(checker.property_set["is_swap_mapped"])
    except Exception as error:
        errors.append(f"CheckMap:{type(error).__name__}:{error}")
    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "unsupported_operations": unsupported,
        "validation_errors": errors,
        "is_executable_on_target": bool(
            basis_valid
            and connectivity_valid
            and not unsupported
            and not errors
        ),
    }


def _clean_circuit_record(circuit: Mapping[str, Any]) -> dict[str, Any]:
    """Rimuove dal record del circuito i campi usati soltanto internamente."""
    return {
        key: value
        for key, value in circuit.items()
        if not str(key).startswith("_")
    }


def _base_record(task: Mapping[str, Any]) -> dict[str, Any]:
    """Prepara il record comune a tutti gli esiti di un tentativo."""
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": task["run_id"],
        "dataset_scope": task["dataset_scope"],
        "split": task["split"],
        "objective": dict(task["objective"]),
        "circuit": _clean_circuit_record(task["circuit"]),
        "device": dict(task["target_record"]),
        "configuration": {
            **dict(task["configuration"]),
            "catalog_id": task["catalog_id"],
        },
        "seed_transpiler": int(task["seed_transpiler"]),
        "status": None,
        "phase": "planned",
        "score": None,
        "target_validation": None,
        "compiled_circuit": None,
        "timings_seconds": {
            "source_loading": None,
            "target_loading": None,
            "transpilation": None,
            "target_validation": None,
            "scoring": None,
            "serialization": None,
            "total": None,
        },
        "failure": None,
        "provenance": {
            "versions": dict(task["versions"]),
            "compiler": "qiskit.transpile",
            "fixed_transpile_options": dict(task["fixed_transpile_options"]),
            "generator": "qiskit_dataset.generation",
        },
    }


def _failure_category(error: BaseException, phase: str) -> str:
    """Classifica un errore in base al tipo e alla fase raggiunta."""
    if isinstance(error, AttemptTimeoutError):
        return "timeout"
    if isinstance(error, TargetValidationError):
        return "target_invalid"
    return {
        "source_loading": "source_error",
        "target_loading": "hardware_error",
        "transpilation": "transpiler_error",
        "target_validation": "validation_error",
        "scoring": "scoring_error",
        "serialization": "serialization_error",
    }.get(phase, "unexpected_error")


def execute_attempt(task: Mapping[str, Any]) -> dict[str, Any]:
    """Esegue un tentativo e restituisce sempre un record completo."""
    from mqt.predictor.reward import expected_fidelity
    from qiskit import QuantumCircuit, transpile
    from qiskit.qasm2 import dump as qasm_dump

    record = _base_record(task)
    phase = "source_loading"
    total_started = time.perf_counter()
    phase_started = total_started
    transpiler_progress: dict[str, Any] = {
        "completed_pass_count": 0,
        "last_completed_pass": None,
    }
    validation: dict[str, Any] | None = None
    try:
        with _hard_timeout(float(task["timeout_seconds"])):
            started = phase_started = time.perf_counter()
            circuit = QuantumCircuit.from_qasm_file(str(task["source_path"]))
            record["timings_seconds"][phase] = time.perf_counter() - started

            phase = "target_loading"
            started = phase_started = time.perf_counter()
            target = _worker_target(str(task["device_id"]))
            record["timings_seconds"][phase] = time.perf_counter() - started
            if int(circuit.num_qubits) > int(target.num_qubits):
                raise ValueError(
                    f"Il circuito usa {circuit.num_qubits} qubit, "
                    f"il target ne supporta {target.num_qubits}."
                )

            phase = "transpilation"
            started = phase_started = time.perf_counter()
            configuration = task["configuration"]
            kwargs: dict[str, Any] = {
                "target": target,
                "optimization_level": int(
                    configuration["optimization_level"]
                ),
                "seed_transpiler": int(task["seed_transpiler"]),
                **dict(task["fixed_transpile_options"]),
            }
            if configuration.get("layout_method") is not None:
                kwargs["layout_method"] = configuration["layout_method"]
            if configuration.get("routing_method") is not None:
                kwargs["routing_method"] = configuration["routing_method"]
            kwargs["callback"] = lambda **callback_data: _capture_completed_pass(
                transpiler_progress,
                started,
                callback_data,
            )
            compiled = transpile(circuit, **kwargs)
            record["timings_seconds"][phase] = time.perf_counter() - started

            phase = "target_validation"
            started = phase_started = time.perf_counter()
            validation = validate_compiled_circuit(compiled, target)
            record["target_validation"] = validation
            record["timings_seconds"][phase] = time.perf_counter() - started
            if not validation["is_executable_on_target"]:
                raise TargetValidationError(canonical_json(validation))

            phase = "scoring"
            started = phase_started = time.perf_counter()
            score = float(expected_fidelity(compiled, target))
            record["timings_seconds"][phase] = time.perf_counter() - started
            if not math.isfinite(score):
                raise ValueError(f"Score non finito: {score!r}.")

            phase = "serialization"
            started = phase_started = time.perf_counter()
            stream = StringIO()
            qasm_dump(compiled, stream)
            compiled_qasm = stream.getvalue()
            operation_counts = {
                str(name): int(count)
                for name, count in sorted(compiled.count_ops().items())
            }
            two_qubit_count = sum(
                1
                for instruction in compiled.data
                if int(instruction.operation.num_qubits) == 2
                and str(instruction.operation.name) != "barrier"
            )
            record["compiled_circuit"] = {
                "format": "OpenQASM 2",
                "qasm_sha256": sha256_bytes(compiled_qasm.encode("utf-8")),
                "artifact_ref": None,
                "num_qubits": int(compiled.num_qubits),
                "depth": int(compiled.depth()),
                "size": int(compiled.size()),
                "two_qubit_gate_count": int(two_qubit_count),
                "operation_counts": operation_counts,
            }
            record["timings_seconds"][phase] = time.perf_counter() - started
            record["status"] = "success"
            record["phase"] = "completed"
            record["score"] = score
            record["_compiled_qasm2"] = compiled_qasm
    except Exception as error:
        elapsed_total = time.perf_counter() - total_started
        if (
            phase in record["timings_seconds"]
            and record["timings_seconds"][phase] is None
        ):
            record["timings_seconds"][phase] = (
                time.perf_counter() - phase_started
            )
        traceback_text = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        status = "timeout" if isinstance(error, AttemptTimeoutError) else "failure"
        record["status"] = status
        record["phase"] = phase
        record["score"] = None
        record["target_validation"] = validation
        record["compiled_circuit"] = None
        failure = {
            "phase": phase,
            "category": _failure_category(error, phase),
            "exception_type": type(error).__name__,
            "message": str(error)[:4000],
            "traceback": traceback_text[-8000:],
            "retryable": isinstance(error, AttemptTimeoutError),
            "timeout_seconds": (
                float(task["timeout_seconds"])
                if isinstance(error, AttemptTimeoutError)
                else None
            ),
        }
        if isinstance(error, AttemptTimeoutError):
            failure["timeout_diagnostics"] = build_timeout_diagnostics(
                traceback_text=traceback_text,
                phase=phase,
                timeout_seconds=task["timeout_seconds"],
                elapsed_seconds=elapsed_total,
                configuration=task["configuration"],
                qiskit_version=str(task["versions"].get("qiskit", "")),
                progress=transpiler_progress,
            )
        record["failure"] = failure
    record["timings_seconds"]["total"] = time.perf_counter() - total_started
    return record


def _cache_paths(objective: str, run_id: str) -> tuple[Path, Path]:
    """Individua i file di cache di un tentativo e del circuito compilato."""
    root = CACHE_ROOT / objective
    return (
        root / "runs" / f"{run_id}.json",
        root / "compiled_qasm" / f"{run_id}.qasm",
    )


def _load_cached_record(
    objective: str,
    run_id: str,
) -> dict[str, Any] | None:
    """Recupera dalla cache un record completo e riconoscibile."""
    record_path, _ = _cache_paths(objective, run_id)
    if not record_path.is_file():
        return None
    try:
        with record_path.open(encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if record.get("run_id") != run_id:
        return None
    if record.get("status") not in {"success", "failure", "timeout"}:
        return None
    return record


def _persist_record(record: dict[str, Any], objective: str) -> None:
    """Salva in cache il record e l'eventuale circuito compilato."""
    run_id = str(record["run_id"])
    record_path, qasm_path = _cache_paths(objective, run_id)
    compiled_qasm = record.pop("_compiled_qasm2", None)
    if compiled_qasm is not None:
        atomic_text_write(qasm_path, str(compiled_qasm))
        record["compiled_circuit"]["artifact_ref"] = str(
            qasm_path.relative_to(PROJECT_ROOT).as_posix()
        )
    atomic_json_write(record_path, record)


def _worker_crash_record(
    task: Mapping[str, Any],
    error: BaseException,
) -> dict[str, Any]:
    """Crea un record di errore quando un processo termina in modo inatteso."""
    record = _base_record(task)
    record["status"] = "failure"
    record["phase"] = "worker"
    record["failure"] = {
        "phase": "worker",
        "category": "worker_crash",
        "exception_type": type(error).__name__,
        "message": str(error)[:4000],
        "traceback": "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )[-8000:],
        "retryable": True,
        "timeout_seconds": None,
    }
    return record


def _normalize_for_scope(
    record: Mapping[str, Any],
    task: Mapping[str, Any],
) -> dict[str, Any]:
    """Allinea un record recuperato allo scope e al circuito correnti."""
    normalized = json.loads(canonical_json(record))
    normalized["dataset_scope"] = task["dataset_scope"]
    normalized["split"] = task["split"]
    normalized["circuit"] = _clean_circuit_record(task["circuit"])
    return normalized


def _report_progress(
    scope: str,
    completed: int,
    total: int,
    statuses: Mapping[str, int],
) -> None:
    """Mostra periodicamente quanti tentativi sono stati completati."""
    if completed == 1 or completed == total or completed % 25 == 0:
        status_text = ", ".join(
            f"{name}={count}" for name, count in sorted(statuses.items())
        )
        print(
            f"[{scope}] {completed}/{total} tentativi eseguiti"
            f" ({status_text})",
            file=sys.stderr,
            flush=True,
        )


def generate_dataset(
    scope: str,
    catalog: ConfigurationCatalog,
    *,
    workers: int = 1,
    timeout_seconds: float = 900.0,
    limit_runs: int | None = None,
    retry_failures: bool = False,
    force: bool = False,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Esegue i tentativi mancanti e ricostruisce il JSONL ordinato."""
    if workers <= 0:
        raise ValueError("workers deve essere positivo.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds deve essere positivo.")
    if limit_runs is not None and limit_runs <= 0:
        raise ValueError("limit_runs deve essere positivo.")

    generation_started = time.perf_counter()
    objective_name = str(catalog.objective["name"])
    selected_device_id = catalog.require_device(device_id)
    output_root = dataset_scope_root(
        objective_name,
        scope,
        selected_device_id,
    )
    manifest = load_manifest(scope, objective_name, selected_device_id)
    target_record = build_target_record(selected_device_id)
    versions = package_versions()
    attempts = expand_attempts(
        manifest,
        catalog,
        target_sha256=str(target_record["target_sha256"]),
        versions=versions,
        device_id=selected_device_id,
    )
    pending: list[dict[str, Any]] = []
    records_by_id: dict[str, dict[str, Any]] = {}
    cache_hits = 0

    for attempt in attempts:
        attempt["target_record"] = target_record
        attempt["timeout_seconds"] = float(timeout_seconds)
        attempt["source_path"] = str(
            resolve_circuit_source(
                objective_name,
                scope,
                str(attempt["circuit"]["source_ref"]),
            )
        )
        cached = None if force else _load_cached_record(
            objective_name,
            str(attempt["run_id"]),
        )
        if (
            cached is not None
            and not (
                retry_failures
                and cached.get("status") in {"failure", "timeout"}
            )
        ):
            records_by_id[str(attempt["run_id"])] = _normalize_for_scope(
                cached,
                attempt,
            )
            cache_hits += 1
        else:
            pending.append(attempt)

    if limit_runs is not None:
        pending = pending[:limit_runs]

    execution_total = len(pending)
    if execution_total:
        print(
            f"[{scope}/{selected_device_id}] cache_hit={cache_hits}; "
            f"da_eseguire={execution_total}; workers={workers}",
            file=sys.stderr,
            flush=True,
        )

    completed_now = 0
    status_now: Counter[str] = Counter()
    if workers == 1:
        for task in pending:
            record = execute_attempt(task)
            _persist_record(record, objective_name)
            records_by_id[str(task["run_id"])] = _normalize_for_scope(
                record,
                task,
            )
            completed_now += 1
            status_now[str(record["status"])] += 1
            _report_progress(
                f"{scope}/{selected_device_id}",
                completed_now,
                execution_total,
                status_now,
            )
    elif pending:
        context = multiprocessing.get_context("spawn")
        task_iterator = iter(pending)
        max_in_flight = workers * 2
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
        ) as executor:
            future_to_task = {}
            for _ in range(min(max_in_flight, len(pending))):
                task = next(task_iterator)
                future_to_task[executor.submit(execute_attempt, task)] = task

            while future_to_task:
                done, _ = wait(
                    future_to_task,
                    return_when=FIRST_COMPLETED,
                )
                for future in done:
                    task = future_to_task.pop(future)
                    try:
                        record = future.result()
                    except Exception as error:
                        record = _worker_crash_record(task, error)
                    _persist_record(record, objective_name)
                    records_by_id[str(task["run_id"])] = _normalize_for_scope(
                        record,
                        task,
                    )
                    completed_now += 1
                    status_now[str(record["status"])] += 1
                    _report_progress(
                        f"{scope}/{selected_device_id}",
                        completed_now,
                        execution_total,
                        status_now,
                    )
                    try:
                        next_task = next(task_iterator)
                    except StopIteration:
                        continue
                    future_to_task[
                        executor.submit(execute_attempt, next_task)
                    ] = next_task

    ordered_records = [
        records_by_id[str(attempt["run_id"])]
        for attempt in attempts
        if str(attempt["run_id"]) in records_by_id
    ]
    atomic_jsonl_write(output_root / "qiskit_runs.jsonl", ordered_records)
    observed_status = Counter(str(record["status"]) for record in ordered_records)
    status = {
        "schema_version": SCHEMA_VERSION,
        "dataset_scope": scope,
        "objective": objective_name,
        "device_id": selected_device_id,
        "planned_attempts": len(attempts),
        "available_attempts": len(ordered_records),
        "missing_attempts": len(attempts) - len(ordered_records),
        "cache_hits": cache_hits,
        "executed_now": completed_now,
        "executed_status": dict(sorted(status_now.items())),
        "available_status": dict(sorted(observed_status.items())),
        "complete": len(ordered_records) == len(attempts),
        "execution_policy": {
            "workers": workers,
            "timeout_seconds": float(timeout_seconds),
            "wall_clock_seconds_this_invocation": (
                time.perf_counter() - generation_started
            ),
        },
        "output": "qiskit_runs.jsonl",
        "cache_root": str(
            (CACHE_ROOT / objective_name).relative_to(PROJECT_ROOT).as_posix()
        ),
        "target": target_record,
    }
    atomic_json_write(output_root / "generation_status.json", status)
    return status

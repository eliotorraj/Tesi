"""Compile resumably and train the supervised MQT device selector.

The expensive part of device-selector training is not fitting the Random
Forest. It is compiling every source circuit with every compatible RL model.
This runner therefore treats each ``circuit x device`` compilation as an
independent, durable checkpoint.

All workspace outputs live below the explicit v2 experiment roots. Runtime
copies inside the installed package are mirrors, never the authoritative
artifacts.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import time
import traceback
import zipfile
from collections import Counter, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from importlib.metadata import version as package_version
from multiprocessing import get_context
from pathlib import Path
from typing import Any

# Keep BQSKit runs tractable and deterministic. MQT reads this variable while
# importing its action catalogue, so it must be set before importing MQT.
os.environ.setdefault("GITHUB_ACTIONS", "true")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mqt_model_artifacts import validate_rl_training_metadata
from mqt_predictor_protocol import CANONICAL_ML_MODEL_DIR_V2
from mqt_predictor_protocol import CANONICAL_RL_MODEL_DIR_V2
from mqt_predictor_protocol import EXPERIMENT_ID
from mqt_predictor_protocol import EXPERIMENT_ROOT
from mqt_predictor_protocol import FROZEN_DEVICES
from mqt_predictor_protocol import FIGURE_OF_MERIT as FROZEN_FIGURE_OF_MERIT
from mqt_predictor_protocol import MQT_TRAINING_SET_V2
from mqt_predictor_protocol import PROTOCOL_ID
from mqt_predictor_protocol import PROTOCOL_VERSION
from mqt_predictor_protocol import RL_FINAL_TIMESTEPS
from mqt_predictor_protocol import SOURCE_MANIFEST_V2
from mqt_predictor_protocol import TRAINING_CIRCUITS_V2
from mqt_predictor_protocol import file_sha256
from mqt_predictor_protocol import frozen_target_mismatches
from mqt_predictor_protocol import installed_package_versions
from mqt_predictor_protocol import package_version_mismatches
from mqt_predictor_protocol import target_record
from mqt_predictor_protocol import validate_compiled_circuit
from mqt_predictor_protocol import verify_circuit_directory

import numpy as np
from joblib import Parallel, delayed
from joblib import dump as joblib_dump
from joblib import load as joblib_load
from mqt.bench.targets import get_device
from mqt.predictor.ml import Predictor
from mqt.predictor.ml.helper import create_feature_vector
from mqt.predictor.ml.helper import get_openqasm_gates
from mqt.predictor.ml.helper import get_path_trained_model as get_ml_model_path
from mqt.predictor.ml.helper import get_path_training_circuits as get_ml_training_circuits
from mqt.predictor.ml.helper import get_path_training_circuits_compiled as get_ml_compiled_circuits
from mqt.predictor.ml.helper import get_path_training_data as get_ml_training_data
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir
from mqt.predictor.reward import crit_depth, expected_fidelity
from qiskit import QuantumCircuit
from qiskit import transpile as qiskit_transpile
from qiskit.qasm2 import dump as qasm_dump
from sb3_contrib.common.maskable.utils import get_action_masks
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODELS_DIR = CANONICAL_ML_MODEL_DIR_V2
DEFAULT_CACHE_ROOT = EXPERIMENT_ROOT / "cache" / "ml"
CANONICAL_RL_MODELS_DIR = CANONICAL_RL_MODEL_DIR_V2
DEFAULT_LOG_ROOT = EXPERIMENT_ROOT / "logs" / "ml"
DEFAULT_WORKERS = 1
ESTIMATED_RL_WORKER_GIB = 2.2
WORKER_WATCHDOG_GRACE_SECONDS = 30
WORST_SCORE = -1.0
RL_SUCCESS_STATUSES = {"success"}
SUCCESS_STATUSES = RL_SUCCESS_STATUSES | {"success_fallback"}
VALIDATION_VERSION = 1
NON_ATTEMPT_STATUSES = {
    "rl_model_load_failed",
    "rl_model_startup_timeout",
    "rl_runtime_unavailable",
}


@dataclass(frozen=True)
class CompilationJob:
    """One durable circuit/device compilation."""

    source: Path
    output: Path
    circuit_name: str
    device_name: str
    num_qubits: int

    @property
    def key(self) -> str:
        """Return a stable manifest key."""
        return f"{self.circuit_name}|{self.device_name}"


@dataclass
class WorkerState:
    """Parent-side state for one persistent device worker."""

    device_name: str
    process: Any
    launched_at: float
    ready: bool = False
    current_job: CompilationJob | None = None
    current_started_at: float | None = None
    current_attempt: int | None = None
    current_phase: str | None = None
    current_output_version: tuple[int, int] | None = None


def utc_now() -> str:
    """Return an ISO-8601 timestamp."""
    return datetime.now(UTC).isoformat()


def atomic_json_write(path: Path, payload: Any) -> None:
    """Write JSON via an atomic rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def append_manifest(path: Path, record: dict[str, Any]) -> None:
    """Append one parent-owned JSONL checkpoint record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_manifest(path: Path) -> tuple[dict[str, int], dict[str, str]]:
    """Load attempts and last status, tolerating an interrupted last line.

    A failure to start the shared runtime is infrastructure-wide and does not
    represent a compilation attempt for every queued circuit/device pair.
    Ignore those records when reconstructing the per-job retry budget.
    """
    attempts: dict[str, int] = {}
    statuses: dict[str, str] = {}
    if not path.exists():
        return attempts, statuses

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Manifest: riga incompleta ignorata ({line_number}).")
                continue
            key = record.get("key")
            if not isinstance(key, str):
                continue
            status = record.get("status")
            attempt = record.get("attempt")
            if isinstance(attempt, int) and status not in NON_ATTEMPT_STATUSES:
                attempts[key] = max(attempts.get(key, 0), attempt)
            if isinstance(status, str):
                statuses[key] = status
    return attempts, statuses


def is_valid_qasm(path: Path) -> bool:
    """Return whether a non-empty QASM file can be parsed by Qiskit."""
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        QuantumCircuit.from_qasm_file(path)
    except Exception:
        return False
    return True


def file_version(path: Path) -> tuple[int, int] | None:
    """Return a cheap version marker used to reject stale cached outputs."""
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return stat.st_mtime_ns, stat.st_size


def output_changed(path: Path, previous_version: tuple[int, int] | None) -> bool:
    """Return whether a worker produced or replaced an output in this attempt."""
    return file_version(path) != previous_version and is_valid_qasm(path)


def ensure_training_circuits(path: Path) -> None:
    """Extract the trusted bundled training archive when necessary."""
    if any(path.glob("*.qasm")):
        return
    archive = path / "training_data_device_selection.zip"
    if not archive.is_file():
        raise SystemExit(f"Nessun circuito QASM e archivio non trovato: {path}")
    with zipfile.ZipFile(archive) as zip_ref:
        zip_ref.extractall(path)


def build_jobs(
    source_dir: Path,
    compiled_dir: Path,
    device_names: list[str],
    metric: str,
) -> tuple[list[CompilationJob], dict[str, Path]]:
    """Build all compatible compilation jobs and retain source paths."""
    devices = {name: get_device(name) for name in device_names}
    source_paths: dict[str, Path] = {}
    jobs: list[CompilationJob] = []

    circuit_info: list[tuple[int, str, Path]] = []
    for source in source_dir.glob("*.qasm"):
        circuit = QuantumCircuit.from_qasm_file(source)
        circuit_info.append((circuit.num_qubits, source.stem, source))
        source_paths[source.stem] = source

    for num_qubits, circuit_name, source in sorted(circuit_info):
        for device_name in sorted(device_names):
            device = devices[device_name]
            if num_qubits > device.num_qubits:
                continue
            filename = f"{circuit_name}_{metric}-{device_name}.qasm"
            jobs.append(
                CompilationJob(
                    source=source,
                    output=compiled_dir / filename,
                    circuit_name=circuit_name,
                    device_name=device_name,
                    num_qubits=num_qubits,
                )
            )
    return jobs, source_paths


def import_legacy_checkpoints(
    jobs: list[CompilationJob],
    legacy_dir: Path,
    *,
    dry_run: bool,
) -> int:
    """Copy valid package-local checkpoints to the durable artifact folder."""
    imported = 0
    if not legacy_dir.is_dir():
        return imported

    for job in jobs:
        if is_valid_qasm(job.output):
            continue
        legacy = legacy_dir / job.output.name
        if not is_valid_qasm(legacy):
            continue
        imported += 1
        if dry_run:
            continue
        job.output.parent.mkdir(parents=True, exist_ok=True)
        temp = job.output.with_name(f".{job.output.name}.legacy.tmp")
        shutil.copy2(legacy, temp)
        os.replace(temp, job.output)
    return imported


def _set_parent_death_signal() -> None:
    """Create a process group and ask Linux to terminate it with its parent."""
    os.setsid()
    libc = ctypes.CDLL("libc.so.6")
    pr_set_pdeathsig = 1
    libc.prctl(pr_set_pdeathsig, signal.SIGTERM)


def _terminate_process_group(process: Any, grace: float = 5.0) -> None:
    """Terminate a process and all descendants in its dedicated group."""
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=grace)


def _terminate_worker_process(process: Any, grace: float = 5.0) -> None:
    """Terminate a multiprocessing worker and its descendants."""
    if process is None or not process.is_alive():
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
    process.join(timeout=grace)
    if process.is_alive():
        if process_group == process.pid:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.join(timeout=grace)


def _free_tcp_ports(count: int) -> list[int]:
    """Ask the kernel for currently free localhost TCP ports."""
    import socket

    sockets: list[socket.socket] = []
    ports: list[int] = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
            ports.append(int(sock.getsockname()[1]))
    finally:
        for sock in sockets:
            sock.close()
    return ports


class BQSKitRuntime:
    """Official detached BQSKit runtime shared by parallel RL workers."""

    def __init__(self, num_workers: int, log_dir: Path) -> None:
        self.num_workers = num_workers
        self.log_dir = log_dir
        self.manager_process: subprocess.Popen[str] | None = None
        self.server_process: subprocess.Popen[str] | None = None
        self.manager_log: Any = None
        self.server_log: Any = None
        self.manager_port, self.worker_port, self.server_port = _free_tcp_ports(3)

    def start(self) -> None:
        """Start and validate the manager/server pair."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        executable_dir = Path(sys.prefix) / "bin"
        manager_command = executable_dir / "bqskit-manager"
        server_command = executable_dir / "bqskit-server"
        if not manager_command.is_file() or not server_command.is_file():
            raise RuntimeError("Comandi bqskit-manager/bqskit-server non trovati nella virtualenv.")

        self.manager_log = (self.log_dir / "bqskit_manager.log").open("a", encoding="utf-8")
        self.server_log = (self.log_dir / "bqskit_server.log").open("a", encoding="utf-8")
        self.manager_log.write(f"\n--- start {utc_now()} ---\n")
        self.server_log.write(f"\n--- start {utc_now()} ---\n")
        self.manager_log.flush()
        self.server_log.flush()

        self.manager_process = subprocess.Popen(
            [
                str(manager_command),
                "--num-workers",
                str(self.num_workers),
                "--port",
                str(self.manager_port),
                "--worker-port",
                str(self.worker_port),
            ],
            stdout=self.manager_log,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=_set_parent_death_signal,
        )
        time.sleep(0.8)
        if self.manager_process.poll() is not None:
            raise RuntimeError("Il manager BQSKit non è partito; controlla bqskit_manager.log.")

        self.server_process = subprocess.Popen(
            [
                str(server_command),
                "--port",
                str(self.server_port),
                f"localhost:{self.manager_port}",
            ],
            stdout=self.server_log,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=_set_parent_death_signal,
        )
        time.sleep(1.2)
        if self.server_process.poll() is not None:
            raise RuntimeError("Il server BQSKit non è partito; controlla bqskit_server.log.")

        from bqskit.compiler import Compiler

        compiler = Compiler(ip="localhost", port=self.server_port)
        compiler.close()

    def is_alive(self) -> bool:
        """Return whether both runtime processes are alive."""
        return (
            self.manager_process is not None
            and self.server_process is not None
            and self.manager_process.poll() is None
            and self.server_process.poll() is None
        )

    def stop(self) -> None:
        """Stop the detached runtime and close its logs."""
        _terminate_process_group(self.server_process)
        _terminate_process_group(self.manager_process)
        if self.server_log is not None:
            self.server_log.close()
        if self.manager_log is not None:
            self.manager_log.close()


def configure_shared_bqskit_runtime(server_port: int, seed: int) -> Any:
    """Route MQT BQSKit actions to the shared detached runtime."""
    from bqskit.compiler import Compiler
    from mqt.predictor.rl.actions import bqskit_actions as actions_module

    original_compile = actions_module.bqskit_compile
    shared_compiler = Compiler(ip="localhost", port=server_port)

    def shared_compile(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("num_workers", None)
        kwargs.pop("ip", None)
        kwargs.pop("port", None)
        kwargs["compiler"] = shared_compiler
        kwargs["seed"] = seed
        return original_compile(*args, **kwargs)

    actions_module.bqskit_compile = shared_compile
    return shared_compiler


def run_rl_policy(
    predictor: Any,
    cached_model: Any,
    circuit: QuantumCircuit,
    seed: int,
) -> tuple[QuantumCircuit, list[str], bool, bool, dict[str, Any]]:
    """Run one deterministic policy episode while preserving truncation state."""
    environment = predictor.env
    observation, _ = environment.reset(circuit, seed=seed)
    passes: list[str] = []
    terminated = False
    truncated = False
    info: dict[str, Any] = {}

    while not (terminated or truncated):
        action_masks = get_action_masks(environment)
        action, _ = cached_model.predict(
            observation,
            action_masks=action_masks,
            deterministic=True,
        )
        action_index = int(np.asarray(action).item())
        action_name = environment.action_set[action_index].name
        print(f"azione_RL={action_name}", flush=True)
        passes.append(action_name)
        observation, _reward, terminated, truncated, info = environment.step(action_index)

    return environment.state, passes, terminated, truncated, info


def validate_rl_compilation(
    predictor: Any,
    compiled: QuantumCircuit,
    passes: list[str],
    terminated: bool,
    truncated: bool,
    info: dict[str, Any],
    device: Any,
) -> dict[str, Any]:
    """Prove that a policy terminated with a circuit executable on its Target."""
    environment = predictor.env
    native = bool(environment.is_circuit_synthesized(compiled))
    laid_out = bool(
        environment.layout is not None
        and environment.is_circuit_laid_out(compiled, environment.layout)
    )
    coupling_map = device.build_coupling_map()
    routed = bool(
        laid_out
        and (
            coupling_map is None
            or environment.is_circuit_routed(compiled, coupling_map)
        )
    )
    target_validation = validate_compiled_circuit(compiled, device)
    terminated_by_policy = bool(
        terminated
        and not truncated
        and passes
        and passes[-1] == "terminate"
        and not environment.error_occurred
    )
    valid = bool(
        terminated_by_policy
        and native
        and laid_out
        and routed
        and target_validation["is_executable_on_target"]
    )
    if terminated_by_policy:
        termination_reason = "terminate"
    elif truncated:
        termination_reason = str(
            info.get("truncation_reason")
            or info.get("Truncated because of error")
            or "truncated"
        )
    else:
        termination_reason = "invalid_termination"

    return {
        "laid_out": laid_out,
        "native": native,
        "num_steps": int(environment.num_steps),
        "routed": routed,
        "target_validation": target_validation,
        "terminated": bool(terminated),
        "termination_reason": termination_reason,
        "truncated": bool(truncated),
        "valid": valid,
        "validation_version": VALIDATION_VERSION,
    }


def _compile_job_process(
    job: CompilationJob,
    device: Any,
    predictor: Any,
    cached_model: Any,
    server_port: int,
    mode: str,
    fallback_optimization_level: int,
    seed: int,
    model_sha256: str,
    target_sha256: str,
    result_connection: Any,
) -> None:
    """Compile one job in a disposable process forked after PPO loading."""
    _set_parent_death_signal()
    started = time.monotonic()
    shared_compiler = None
    temp_output = job.output.with_name(f".{job.output.name}.{os.getpid()}.tmp")
    result: dict[str, Any]
    validation: dict[str, Any] = {}
    try:
        circuit = QuantumCircuit.from_qasm_file(job.source)
        if mode == "rl":
            shared_compiler = configure_shared_bqskit_runtime(server_port, seed)
            compiled, passes, terminated, truncated, info = run_rl_policy(
                predictor,
                cached_model,
                circuit,
                seed,
            )
            validation = validate_rl_compilation(
                predictor,
                compiled,
                passes,
                terminated,
                truncated,
                info,
                device,
            )
        elif mode == "fallback":
            print(
                f"job={job.key} fallback=QiskitO{fallback_optimization_level}",
                flush=True,
            )
            compiled = qiskit_transpile(
                circuit,
                target=device,
                optimization_level=fallback_optimization_level,
                seed_transpiler=seed,
            )
            passes = [f"fallback:qiskit_transpile_o{fallback_optimization_level}"]
        else:
            raise ValueError(f"Modalità di compilazione sconosciuta: {mode}")

        provenance = {
            "model_sha256": model_sha256,
            "mqt_predictor_version": package_version("mqt.predictor"),
            "rl_max_steps": predictor.env.max_steps,
            "seed": seed,
            "target_sha256": target_sha256,
        }
        if mode == "rl" and not validation["valid"]:
            temp_output.unlink(missing_ok=True)
            result = {
                "status": "truncated" if validation["truncated"] else "invalid_compilation",
                "mode": mode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "error": (
                    "episodio RL troncato o circuito non eseguibile: "
                    f"{validation['termination_reason']}"
                ),
                "passes": passes,
                **provenance,
                **validation,
            }
        else:
            temp_output.parent.mkdir(parents=True, exist_ok=True)
            with temp_output.open("w", encoding="utf-8") as handle:
                qasm_dump(compiled, handle)
                handle.flush()
                os.fsync(handle.fileno())
            QuantumCircuit.from_qasm_file(temp_output)
            qasm_sha256 = file_sha256(temp_output)
            os.replace(temp_output, job.output)
            result = {
                "status": "success",
                "mode": mode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "passes": passes,
                "qasm_sha256": qasm_sha256,
                **provenance,
                **validation,
            }
    except BaseException as exc:
        temp_output.unlink(missing_ok=True)
        result = {
            "status": "failed",
            "mode": mode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=20)[-8000:],
            "model_sha256": model_sha256,
            "mqt_predictor_version": package_version("mqt.predictor"),
            "rl_max_steps": predictor.env.max_steps,
            "seed": seed,
            "target_sha256": target_sha256,
            **validation,
        }

    try:
        result_connection.send(result)
    except (BrokenPipeError, EOFError, OSError):
        pass
    finally:
        result_connection.close()
        if shared_compiler is not None:
            shared_compiler.close()


def _compile_fallback_process(
    job: CompilationJob,
    device_name: str,
    fallback_optimization_level: int,
    result_connection: Any,
) -> None:
    """Run Qiskit fallback in a clean spawned process without PyTorch state."""
    _set_parent_death_signal()
    started = time.monotonic()
    temp_output = job.output.with_name(f".{job.output.name}.{os.getpid()}.tmp")
    try:
        print(
            f"job={job.key} fallback=QiskitO{fallback_optimization_level}",
            flush=True,
        )
        circuit = QuantumCircuit.from_qasm_file(job.source)
        device = get_device(device_name)
        compiled = qiskit_transpile(
            circuit,
            target=device,
            optimization_level=fallback_optimization_level,
            seed_transpiler=0,
        )
        temp_output.parent.mkdir(parents=True, exist_ok=True)
        with temp_output.open("w", encoding="utf-8") as handle:
            qasm_dump(compiled, handle)
            handle.flush()
            os.fsync(handle.fileno())
        QuantumCircuit.from_qasm_file(temp_output)
        os.replace(temp_output, job.output)
        result = {
            "status": "success",
            "mode": "fallback",
            "duration_seconds": round(time.monotonic() - started, 3),
            "passes": [f"fallback:qiskit_transpile_o{fallback_optimization_level}"],
        }
    except BaseException as exc:
        temp_output.unlink(missing_ok=True)
        result = {
            "status": "failed",
            "mode": "fallback",
            "duration_seconds": round(time.monotonic() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=20)[-8000:],
        }

    try:
        result_connection.send(result)
    except (BrokenPipeError, EOFError, OSError):
        pass
    finally:
        result_connection.close()


def _run_isolated_job(
    job: CompilationJob,
    device: Any,
    predictor: Any,
    cached_model: Any,
    server_port: int,
    mode: str,
    timeout: int,
    fallback_optimization_level: int,
    seed: int,
    model_sha256: str,
    target_sha256: str,
) -> dict[str, Any]:
    """Run one compilation with a hard timeout without killing the PPO owner."""
    if mode == "fallback":
        process_context = get_context("forkserver")
        receive_connection, send_connection = process_context.Pipe(duplex=False)
        process = process_context.Process(
            target=_compile_fallback_process,
            args=(job, str(device.description), fallback_optimization_level, send_connection),
            name=f"mqt-{mode}-{job.device_name}",
        )
    else:
        process_context = get_context("fork")
        receive_connection, send_connection = process_context.Pipe(duplex=False)
        process = process_context.Process(
            target=_compile_job_process,
            args=(
                job,
                device,
                predictor,
                cached_model,
                server_port,
                mode,
                fallback_optimization_level,
                seed,
                model_sha256,
                target_sha256,
                send_connection,
            ),
            name=f"mqt-{mode}-{job.device_name}",
        )
    started = time.monotonic()
    previous_output_version = file_version(job.output)
    process.start()
    send_connection.close()
    result: dict[str, Any] | None = None
    deadline = started + timeout
    try:
        while time.monotonic() < deadline:
            if receive_connection.poll(0.1):
                try:
                    result = receive_connection.recv()
                except EOFError:
                    result = None
                break
            if not process.is_alive():
                break

        if result is None and process.is_alive() and time.monotonic() >= deadline:
            _terminate_worker_process(process)
            unverified_output = output_changed(job.output, previous_output_version)
            if unverified_output:
                job.output.unlink(missing_ok=True)
            result = {
                "status": "timeout",
                "mode": mode,
                "error": (
                    f"superato limite {mode} di {timeout}s"
                    + ("; output non verificato rimosso" if unverified_output else "")
                ),
            }
        elif result is None:
            process.join(timeout=1)
            if receive_connection.poll():
                try:
                    result = receive_connection.recv()
                except EOFError:
                    result = None
            if result is None:
                unverified_output = output_changed(job.output, previous_output_version)
                if unverified_output:
                    job.output.unlink(missing_ok=True)
                result = {
                    "status": "failed",
                    "mode": mode,
                    "error": (
                        f"processo {mode} terminato con exit code {process.exitcode}"
                        + ("; output non verificato rimosso" if unverified_output else "")
                    ),
                }
    finally:
        receive_connection.close()
        if process.is_alive():
            _terminate_worker_process(process)
        process.join(timeout=1)
        if process.pid is not None:
            job.output.with_name(f".{job.output.name}.{process.pid}.tmp").unlink(missing_ok=True)

    assert result is not None
    result.setdefault("duration_seconds", round(time.monotonic() - started, 3))
    return result


def _compile_fallback_inline(
    job: CompilationJob,
    device: Any,
    fallback_optimization_level: int,
) -> dict[str, Any]:
    """Compile a deterministic fallback in the persistent worker."""
    started = time.monotonic()
    temp_output = job.output.with_name(f".{job.output.name}.{os.getpid()}.tmp")
    try:
        print(
            f"job={job.key} fallback=QiskitO{fallback_optimization_level}",
            flush=True,
        )
        circuit = QuantumCircuit.from_qasm_file(job.source)
        compiled = qiskit_transpile(
            circuit,
            target=device,
            optimization_level=fallback_optimization_level,
            seed_transpiler=0,
        )
        temp_output.parent.mkdir(parents=True, exist_ok=True)
        with temp_output.open("w", encoding="utf-8") as handle:
            qasm_dump(compiled, handle)
            handle.flush()
            os.fsync(handle.fileno())
        QuantumCircuit.from_qasm_file(temp_output)
        os.replace(temp_output, job.output)
        return {
            "status": "success",
            "mode": "fallback",
            "duration_seconds": round(time.monotonic() - started, 3),
            "passes": [f"fallback:qiskit_transpile_o{fallback_optimization_level}"],
        }
    except BaseException as exc:
        temp_output.unlink(missing_ok=True)
        return {
            "status": "failed",
            "mode": "fallback",
            "duration_seconds": round(time.monotonic() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=20)[-8000:],
        }

def device_worker(
    device_name: str,
    metric: str,
    jobs: list[CompilationJob],
    server_port: int,
    result_queue: Any,
    log_path: Path,
    timeout: int,
    fallback_timeout: int,
    fallback_enabled: bool,
    fallback_optimization_level: int,
    rl_max_steps: int,
    seed: int,
    model_sha256: str,
    target_sha256: str,
) -> None:
    """Keep one PPO resident and isolate each compilation in a forked child."""
    _set_parent_death_signal()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", buffering=1) as log_handle:
        os.dup2(log_handle.fileno(), sys.stdout.fileno())
        os.dup2(log_handle.fileno(), sys.stderr.fileno())
        print(f"\n--- robust worker start {utc_now()} pid={os.getpid()} device={device_name} ---", flush=True)
        try:
            import mqt.predictor.rl.predictor as rl_predictor_module

            device = get_device(device_name)
            predictor = rl_predictor_module.Predictor(
                figure_of_merit=metric,
                device=device,
                max_steps=rl_max_steps,
            )
            model_name = f"model_{metric}_{device_name}"
            cached_model = rl_predictor_module.load_model(model_name)
            result_queue.put({"type": "ready", "device": device_name, "pid": os.getpid()})

            for job in jobs:
                total_started = time.monotonic()
                result_queue.put({"type": "started", "device": device_name, "pid": os.getpid(), "key": job.key})
                result_queue.put(
                    {"type": "phase", "device": device_name, "pid": os.getpid(), "key": job.key, "phase": "rl"}
                )
                rl_result = _run_isolated_job(
                    job,
                    device,
                    predictor,
                    cached_model,
                    server_port,
                    "rl",
                    timeout,
                    fallback_optimization_level,
                    seed,
                    model_sha256,
                    target_sha256,
                )
                final_result = rl_result

                if rl_result["status"] not in SUCCESS_STATUSES and fallback_enabled:
                    result_queue.put(
                        {
                            "type": "phase",
                            "device": device_name,
                            "pid": os.getpid(),
                            "key": job.key,
                            "phase": "fallback",
                        }
                    )
                    fallback_result = _compile_fallback_inline(
                        job,
                        device,
                        fallback_optimization_level,
                    )
                    if fallback_result["status"] in SUCCESS_STATUSES:
                        final_result = fallback_result
                        final_result["status"] = "success_fallback"
                        final_result["fallback_reason"] = rl_result.get("error", rl_result["status"])
                        final_result["rl_status"] = rl_result["status"]
                    else:
                        final_result = fallback_result
                        final_result["error"] = (
                            f"RL: {rl_result.get('error', rl_result['status'])}; "
                            f"fallback: {fallback_result.get('error', fallback_result['status'])}"
                        )

                final_result.update(
                    {
                        "type": "result",
                        "device": device_name,
                        "pid": os.getpid(),
                        "key": job.key,
                        "duration_seconds": round(time.monotonic() - total_started, 3),
                    }
                )
                result_queue.put(final_result)

            result_queue.put({"type": "done", "device": device_name, "pid": os.getpid()})
        except BaseException:
            print(traceback.format_exc(), flush=True)
            raise


def warn_about_memory(num_workers: int) -> None:
    """Warn when requested workers are likely to exceed local RAM."""
    try:
        import psutil

        available_gib = psutil.virtual_memory().available / 1024**3
    except Exception:
        available_gib = 0.0
    estimated = num_workers * ESTIMATED_RL_WORKER_GIB
    if num_workers > 2 or (available_gib and estimated > available_gib * 0.75):
        print(
            "ATTENZIONE: ogni modello RL residente usa circa "
            f"{ESTIMATED_RL_WORKER_GIB:.1f} GiB. "
            f"{num_workers} worker richiedono almeno ~{estimated:.1f} GiB, "
            "oltre alla RAM del runtime BQSKit."
        )


def select_compile_jobs(
    all_jobs: list[CompilationJob],
    limit_circuits: int | None,
) -> list[CompilationJob]:
    """Apply a deterministic circuit limit for canary runs."""
    if limit_circuits is None:
        return all_jobs
    selected_names: list[str] = []
    for job in all_jobs:
        if job.circuit_name not in selected_names:
            selected_names.append(job.circuit_name)
        if len(selected_names) >= limit_circuits:
            break
    selected = set(selected_names)
    return [job for job in all_jobs if job.circuit_name in selected]


def group_pending_jobs(
    jobs: list[CompilationJob],
    attempts: dict[str, int],
    max_attempts: int,
    valid_job_keys: set[str],
) -> dict[str, list[CompilationJob]]:
    """Group missing jobs that still have attempts available."""
    grouped: dict[str, list[CompilationJob]] = {}
    for job in jobs:
        if job.key in valid_job_keys:
            continue
        if attempts.get(job.key, 0) >= max_attempts:
            continue
        grouped.setdefault(job.device_name, []).append(job)
    return grouped


def record_matches_run_configuration(
    record: dict[str, Any] | None,
    *,
    rl_max_steps: int,
    seed: int,
    model_sha256: str,
    target_sha256: str,
) -> bool:
    """Return whether a record belongs to the current reproducible RL run."""
    if record is None:
        return False
    return bool(
        record.get("mqt_predictor_version") == package_version("mqt.predictor")
        and record.get("rl_max_steps") == rl_max_steps
        and record.get("seed") == seed
        and record.get("model_sha256") == model_sha256
        and record.get("target_sha256") == target_sha256
    )


def is_strict_rl_success(
    record: dict[str, Any] | None,
    *,
    rl_max_steps: int | None = None,
    seed: int | None = None,
    model_sha256: str | None = None,
    target_sha256: str | None = None,
) -> bool:
    """Return whether a manifest record proves a complete RL compilation."""
    if record is None:
        return False
    target_validation = record.get("target_validation")
    strict = bool(
        record.get("status") == "success"
        and record.get("mode") == "rl"
        and "fallback_reason" not in record
        and record.get("validation_version") == VALIDATION_VERSION
        and record.get("terminated") is True
        and record.get("truncated") is False
        and record.get("termination_reason") == "terminate"
        and record.get("native") is True
        and record.get("laid_out") is True
        and record.get("routed") is True
        and isinstance(record.get("passes"), list)
        and bool(record["passes"])
        and record["passes"][-1] == "terminate"
        and isinstance(record.get("qasm_sha256"), str)
        and isinstance(target_validation, dict)
        and target_validation.get("is_executable_on_target") is True
    )
    if not strict:
        return False
    if None not in (rl_max_steps, seed, model_sha256, target_sha256):
        return record_matches_run_configuration(
            record,
            rl_max_steps=int(rl_max_steps),
            seed=int(seed),
            model_sha256=str(model_sha256),
            target_sha256=str(target_sha256),
        )
    return True


def strict_rl_success_keys(
    jobs: list[CompilationJob],
    manifest_path: Path,
    *,
    rl_max_steps: int | None = None,
    seed: int | None = None,
    model_sha256_by_device: dict[str, str] | None = None,
    target_sha256_by_device: dict[str, str] | None = None,
) -> set[str]:
    """Return jobs backed by provenance, validation, and an unchanged QASM."""
    latest = latest_manifest_records(manifest_path)
    valid: set[str] = set()
    for job in jobs:
        record = latest.get(job.key)
        model_sha256 = (
            model_sha256_by_device.get(job.device_name)
            if model_sha256_by_device is not None
            else None
        )
        target_sha256 = (
            target_sha256_by_device.get(job.device_name)
            if target_sha256_by_device is not None
            else None
        )
        if not is_strict_rl_success(
            record,
            rl_max_steps=rl_max_steps,
            seed=seed,
            model_sha256=model_sha256,
            target_sha256=target_sha256,
        ):
            continue
        if not is_valid_qasm(job.output):
            continue
        if file_sha256(job.output) != record["qasm_sha256"]:
            continue
        valid.add(job.key)
    return valid


def compile_resumably(
    jobs: list[CompilationJob],
    *,
    metric: str,
    rl_max_steps: int,
    seed: int,
    model_sha256_by_device: dict[str, str],
    target_sha256_by_device: dict[str, str],
    num_workers: int,
    timeout: int,
    startup_timeout: int,
    fallback_timeout: int,
    fallback_enabled: bool,
    fallback_optimization_level: int,
    max_attempts: int,
    manifest_path: Path,
    log_dir: Path,
    progress_every: int,
) -> None:
    """Compile with persistent device workers, retries, and a parent watchdog."""
    if fallback_enabled:
        raise ValueError("Il fallback non e ammesso nella generazione del Training set.")
    attempts, _statuses = load_manifest(manifest_path)
    latest = latest_manifest_records(manifest_path)
    for job in jobs:
        if not record_matches_run_configuration(
            latest.get(job.key),
            rl_max_steps=rl_max_steps,
            seed=seed,
            model_sha256=model_sha256_by_device[job.device_name],
            target_sha256=target_sha256_by_device[job.device_name],
        ):
            attempts[job.key] = 0
    valid_job_keys = strict_rl_success_keys(
        jobs,
        manifest_path,
        rl_max_steps=rl_max_steps,
        seed=seed,
        model_sha256_by_device=model_sha256_by_device,
        target_sha256_by_device=target_sha256_by_device,
    )
    initial_valid = len(valid_job_keys)
    print(f"Checkpoint RL validi: {initial_valid}/{len(jobs)}")
    warn_about_memory(num_workers)

    result_context = get_context("spawn")
    result_queue = result_context.Queue()
    runtime = BQSKitRuntime(num_workers=num_workers, log_dir=log_dir)
    try:
        runtime.start()
    except Exception as exc:
        runtime.stop()
        result_queue.close()
        error = f"{type(exc).__name__}: {exc}"
        for job in jobs:
            if job.key in valid_job_keys:
                continue
            append_manifest(
                manifest_path,
                {
                    "timestamp": utc_now(),
                    "key": job.key,
                    "circuit": job.circuit_name,
                    "device": job.device_name,
                    "attempt": attempts.get(job.key, 0),
                    "status": "rl_runtime_unavailable",
                    "mode": "rl",
                    "model_sha256": model_sha256_by_device[job.device_name],
                    "mqt_predictor_version": package_version("mqt.predictor"),
                    "rl_max_steps": rl_max_steps,
                    "seed": seed,
                    "target_sha256": target_sha256_by_device[job.device_name],
                    "error": error,
                },
            )
        raise RuntimeError(f"Runtime RL non disponibile: {error}") from exc
    print(
        f"Runtime BQSKit condiviso avviato: {num_workers} worker; "
        f"porta client {runtime.server_port}."
    )

    active: dict[str, WorkerState] = {}
    device_queue: deque[str] = deque()
    completed_devices: set[str] = set()
    processed_results = 0
    successful_results = initial_valid
    durations: list[float] = []
    job_lookup = {job.key: job for job in jobs}

    def refresh_device_queue() -> None:
        grouped = group_pending_jobs(jobs, attempts, max_attempts, valid_job_keys)
        queued = set(device_queue)
        for device_name in sorted(grouped):
            if device_name in active or device_name in completed_devices or device_name in queued:
                continue
            device_queue.append(device_name)

    def launch_available_workers() -> None:
        grouped = group_pending_jobs(jobs, attempts, max_attempts, valid_job_keys)
        while len(active) < num_workers and device_queue:
            device_name = device_queue.popleft()
            pending = grouped.get(device_name, [])
            if not pending:
                completed_devices.add(device_name)
                continue
            log_path = log_dir / f"worker_{device_name}.log"
            process = result_context.Process(
                target=device_worker,
                args=(
                    device_name,
                    metric,
                    pending,
                    runtime.server_port,
                    result_queue,
                    log_path,
                    timeout,
                    fallback_timeout,
                    fallback_enabled,
                    fallback_optimization_level,
                    rl_max_steps,
                    seed,
                    model_sha256_by_device[device_name],
                    target_sha256_by_device[device_name],
                ),
                name=f"mqt-selector-{device_name}",
            )
            process.start()
            active[device_name] = WorkerState(
                device_name=device_name,
                process=process,
                launched_at=time.monotonic(),
            )
            print(f"Worker avviato: {device_name} ({len(pending)} job, pid={process.pid})")

    def record_failure(state: WorkerState, status: str, error: str) -> None:
        nonlocal processed_results
        job = state.current_job
        if job is None or state.current_attempt is None:
            return
        record = {
            "timestamp": utc_now(),
            "key": job.key,
            "circuit": job.circuit_name,
            "device": job.device_name,
            "attempt": state.current_attempt,
            "status": status,
            "mode": "rl",
            "model_sha256": model_sha256_by_device[job.device_name],
            "mqt_predictor_version": package_version("mqt.predictor"),
            "rl_max_steps": rl_max_steps,
            "seed": seed,
            "target_sha256": target_sha256_by_device[job.device_name],
            "error": error,
        }
        append_manifest(manifest_path, record)
        processed_results += 1

    def record_unavailable_device(device_name: str, status: str, error: str) -> None:
        """Mark every pending job for an unloadable RL model as failed."""
        nonlocal processed_results
        for job in jobs:
            if job.device_name != device_name or job.key in valid_job_keys:
                continue
            attempt = max(max_attempts, attempts.get(job.key, 0) + 1)
            attempts[job.key] = attempt
            append_manifest(
                manifest_path,
                {
                    "timestamp": utc_now(),
                    "key": job.key,
                    "circuit": job.circuit_name,
                    "device": job.device_name,
                    "attempt": attempt,
                    "status": status,
                    "mode": "rl",
                    "model_sha256": model_sha256_by_device[job.device_name],
                    "mqt_predictor_version": package_version("mqt.predictor"),
                    "rl_max_steps": rl_max_steps,
                    "seed": seed,
                    "target_sha256": target_sha256_by_device[job.device_name],
                    "error": error,
                },
            )
            processed_results += 1
        print(f"Modello RL {device_name} non disponibile: {error}.")

    try:
        refresh_device_queue()
        launch_available_workers()
        while active or device_queue:
            try:
                message = result_queue.get(timeout=0.5)
            except queue.Empty:
                message = None

            if message is not None:
                device_name = message.get("device")
                state = active.get(device_name)
                if state is not None and message.get("pid") == state.process.pid:
                    message_type = message.get("type")
                    if message_type == "ready":
                        state.ready = True
                    elif message_type == "started":
                        job = job_lookup[message["key"]]
                        attempt = attempts.get(job.key, 0) + 1
                        attempts[job.key] = attempt
                        state.current_job = job
                        state.current_started_at = time.monotonic()
                        state.current_attempt = attempt
                        state.current_phase = "rl"
                        state.current_output_version = file_version(job.output)
                        append_manifest(
                            manifest_path,
                            {
                                "timestamp": utc_now(),
                                "key": job.key,
                                "circuit": job.circuit_name,
                                "device": job.device_name,
                                "attempt": attempt,
                                "status": "running",
                                "mode": "rl",
                                "model_sha256": model_sha256_by_device[job.device_name],
                                "mqt_predictor_version": package_version("mqt.predictor"),
                                "rl_max_steps": rl_max_steps,
                                "seed": seed,
                                "target_sha256": target_sha256_by_device[job.device_name],
                                "pid": state.process.pid,
                            },
                        )
                    elif message_type == "phase":
                        state.current_phase = str(message.get("phase", "unknown"))
                        state.current_started_at = time.monotonic()
                        if state.current_phase == "fallback":
                            print(f"Fallback Qiskit: {message['key']}")
                    elif message_type == "result":
                        job = state.current_job
                        if job is not None and state.current_attempt is not None:
                            status = str(message["status"])
                            record = {
                                "timestamp": utc_now(),
                                "key": job.key,
                                "circuit": job.circuit_name,
                                "device": job.device_name,
                                "attempt": state.current_attempt,
                                "status": status,
                                "duration_seconds": message.get("duration_seconds"),
                            }
                            for field in (
                                "error",
                                "fallback_reason",
                                "laid_out",
                                "mode",
                                "model_sha256",
                                "mqt_predictor_version",
                                "native",
                                "num_steps",
                                "passes",
                                "qasm_sha256",
                                "rl_max_steps",
                                "rl_status",
                                "routed",
                                "seed",
                                "target_sha256",
                                "target_validation",
                                "terminated",
                                "termination_reason",
                                "traceback",
                                "truncated",
                                "validation_version",
                            ):
                                if field in message:
                                    record[field] = message[field]
                            if is_strict_rl_success(
                                record,
                                rl_max_steps=rl_max_steps,
                                seed=seed,
                                model_sha256=model_sha256_by_device[job.device_name],
                                target_sha256=target_sha256_by_device[job.device_name],
                            ):
                                valid_job_keys.add(job.key)
                                successful_results = len(valid_job_keys)
                            else:
                                record.setdefault("error", "errore sconosciuto")
                                record.setdefault("traceback", "")
                                print(f"Fallito {job.key}: {record['error']}")
                            append_manifest(manifest_path, record)
                            duration = message.get("duration_seconds")
                            if isinstance(duration, int | float):
                                durations.append(float(duration))
                            processed_results += 1
                            if (
                                processed_results % progress_every == 0
                                or status != "success"
                            ):
                                average = sum(durations) / len(durations) if durations else 0.0
                                print(
                                    f"Progresso: {successful_results}/{len(jobs)} checkpoint validi; "
                                    f"durata media tentativi {average:.1f}s."
                                )
                        state.current_job = None
                        state.current_started_at = None
                        state.current_attempt = None
                        state.current_phase = None
                        state.current_output_version = None

            now = time.monotonic()
            finished_devices: list[str] = []
            for device_name, state in list(active.items()):
                phase_timeout = fallback_timeout if state.current_phase == "fallback" else timeout
                watchdog_timeout = phase_timeout + WORKER_WATCHDOG_GRACE_SECONDS
                if (
                    state.current_job is not None
                    and state.current_started_at is not None
                    and now - state.current_started_at > watchdog_timeout
                ):
                    job_key = state.current_job.key
                    print(
                        f"Watchdog worker ({watchdog_timeout}s, fase={state.current_phase}): "
                        f"{job_key}; riavvio worker."
                    )
                    _terminate_worker_process(state.process)
                    unverified_output = output_changed(
                        state.current_job.output,
                        state.current_output_version,
                    )
                    if unverified_output:
                        state.current_job.output.unlink(missing_ok=True)
                    record_failure(
                        state,
                        "worker_watchdog_timeout",
                        f"worker senza risposta in fase {state.current_phase}"
                        + ("; output non verificato rimosso" if unverified_output else ""),
                    )
                    finished_devices.append(device_name)
                    continue

                if not state.ready and now - state.launched_at > startup_timeout:
                    print(f"Timeout caricamento modello: {device_name}.")
                    _terminate_worker_process(state.process)
                    if state.current_job is not None:
                        record_failure(state, "worker_startup_timeout", "worker non pronto")
                    else:
                        record_unavailable_device(
                            device_name,
                            "rl_model_startup_timeout",
                            f"modello non caricato entro {startup_timeout}s",
                        )
                    finished_devices.append(device_name)
                    continue

                if not state.process.is_alive():
                    state.process.join(timeout=1)
                    if state.current_job is not None:
                        unverified_output = output_changed(
                            state.current_job.output,
                            state.current_output_version,
                        )
                        if unverified_output:
                            state.current_job.output.unlink(missing_ok=True)
                        record_failure(
                            state,
                            "worker_crash",
                            f"worker terminato con exit code {state.process.exitcode}"
                            + ("; output non verificato rimosso" if unverified_output else ""),
                        )
                    elif not state.ready:
                        record_unavailable_device(
                            device_name,
                            "rl_model_load_failed",
                            f"worker terminato con exit code {state.process.exitcode}",
                        )
                    finished_devices.append(device_name)

            for device_name in finished_devices:
                state = active.pop(device_name)
                _terminate_worker_process(state.process)
                pending = group_pending_jobs(jobs, attempts, max_attempts, valid_job_keys).get(device_name, [])
                if pending:
                    device_queue.append(device_name)
                else:
                    completed_devices.add(device_name)

            if not runtime.is_alive():
                raise RuntimeError(
                    "Il runtime BQSKit condiviso si è arrestato; il run è stato "
                    "interrotto senza convertire compilazioni mancanti in score minimo. "
                    f"Controlla {log_dir / 'bqskit_server.log'}."
                )

            refresh_device_queue()
            launch_available_workers()
    except KeyboardInterrupt:
        print("Interruzione richiesta: termino i worker; i checkpoint validi restano salvati.")
        raise
    finally:
        for state in active.values():
            _terminate_worker_process(state.process)
        runtime.stop()
        result_queue.close()


def coverage_report(
    jobs: list[CompilationJob],
    source_paths: dict[str, Path],
    successful_job_keys: set[str],
) -> tuple[list[Path], list[CompilationJob]]:
    """Return circuits with complete RL coverage and failed RL jobs."""
    missing = [job for job in jobs if job.key not in successful_job_keys]
    missing_keys = {(job.circuit_name, job.device_name) for job in missing}
    devices_by_circuit: dict[str, set[str]] = {}
    for job in jobs:
        devices_by_circuit.setdefault(job.circuit_name, set()).add(job.device_name)

    complete_sources: list[Path] = []
    for circuit_name, source in sorted(source_paths.items()):
        required = devices_by_circuit.get(circuit_name, set())
        if required and not any((circuit_name, device) in missing_keys for device in required):
            complete_sources.append(source)
    return complete_sources, missing


def atomic_numpy_save(path: Path, data: np.ndarray) -> None:
    """Save a NumPy array atomically without suffix surprises."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temp.open("wb") as handle:
        np.save(handle, data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def score_compiled_circuit(
    circuit: QuantumCircuit,
    device: Any,
    metric: str,
) -> float:
    """Evaluate one successfully compiled RL circuit."""
    if metric == "critical_depth":
        return float(crit_depth(circuit))
    if metric == "expected_fidelity":
        return float(expected_fidelity(circuit, device))
    raise ValueError(f"Figure of merit non supportata: {metric}")


def choose_best_device(
    device_names: list[str],
    scores: list[float],
) -> str | None:
    """Choose the highest-scoring device, ignoring failed candidates."""
    if len(device_names) != len(scores):
        raise ValueError("Dispositivi e score hanno lunghezze diverse.")
    valid_indices = [
        index
        for index, score in enumerate(scores)
        if np.isfinite(score) and score > WORST_SCORE
    ]
    if not valid_indices:
        return None
    winner_index = max(valid_indices, key=scores.__getitem__)
    return device_names[winner_index]


@lru_cache(maxsize=None)
def scoring_device(device_name: str) -> Any:
    """Reuse immutable Target descriptions while scoring many circuits."""
    return get_device(device_name)


def generate_training_sample(
    source: Path,
    compiled_dir: Path,
    metric: str,
    device_names: list[str],
    successful_rl_keys: set[str],
) -> tuple[tuple[list[Any], str] | None, str, list[float]]:
    """Score every RL candidate and choose the best successful device."""
    source_circuit = QuantumCircuit.from_qasm_file(source)
    scores: list[float] = []

    for device_name in device_names:
        device = scoring_device(device_name)
        key = f"{source.stem}|{device_name}"
        score = WORST_SCORE
        if source_circuit.num_qubits <= device.num_qubits and key in successful_rl_keys:
            compiled_path = compiled_dir / f"{source.stem}_{metric}-{device_name}.qasm"
            try:
                compiled_circuit = QuantumCircuit.from_qasm_file(compiled_path)
                score = score_compiled_circuit(compiled_circuit, device, metric)
                if not np.isfinite(score) or score <= WORST_SCORE:
                    score = WORST_SCORE
            except Exception as exc:
                print(
                    f"Score fallito per {key}: {type(exc).__name__}: {exc}; "
                    f"assegno {WORST_SCORE}."
                )
        scores.append(score)

    target_label = choose_best_device(device_names, scores)
    if target_label is None:
        return None, source.stem, scores
    training_sample = (create_feature_vector(source_circuit), target_label)
    return training_sample, source.stem, scores


def generate_training_arrays(
    predictor: Predictor,
    sources: list[Path],
    compiled_dir: Path,
    output_dir: Path,
    metric: str,
    num_workers: int,
    successful_rl_keys: set[str],
) -> None:
    """Score all RL candidates, select each winner, and save selector arrays."""
    if not sources:
        raise SystemExit("Nessun circuito sorgente; training annullato.")
    device_names = [device.description for device in predictor.devices]
    ordered_sources = sorted(sources)
    if num_workers == 1:
        results = []
        for index, source in enumerate(ordered_sources, start=1):
            results.append(
                generate_training_sample(
                    source,
                    compiled_dir,
                    metric,
                    device_names,
                    successful_rl_keys,
                )
            )
            if index % 10 == 0 or index == len(ordered_sources):
                print(f"Scoring ML: {index}/{len(ordered_sources)} circuiti.")
    else:
        results = Parallel(n_jobs=num_workers, verbose=10)(
            delayed(generate_training_sample)(
                source,
                compiled_dir,
                metric,
                device_names,
                successful_rl_keys,
            )
            for source in ordered_sources
        )
    training_data = []
    names_list = []
    scores_list = []
    all_failed = 0
    for training_sample, circuit_name, scores in results:
        if training_sample is None:
            all_failed += 1
            print(
                f"Nessun RL valido per {circuit_name}: tutti gli score sono "
                f"{WORST_SCORE}; circuito escluso dal fit."
            )
            continue
        training_data.append(training_sample)
        names_list.append(circuit_name)
        scores_list.append(scores)

    if not training_data:
        raise SystemExit("Tutte le compilazioni RL sono fallite; nessuna label addestrabile.")
    failed_scores = sum(score == WORST_SCORE for row in scores_list for score in row)
    print(
        f"Score completati: {len(training_data)} circuiti addestrabili; "
        f"{failed_scores} candidati con score minimo; {all_failed} circuiti senza vincitore."
    )

    atomic_numpy_save(
        output_dir / f"training_data_{metric}.npy",
        np.asarray(training_data, dtype=object),
    )
    atomic_numpy_save(
        output_dir / f"names_list_{metric}.npy",
        np.asarray(names_list, dtype=str),
    )
    atomic_numpy_save(
        output_dir / f"scores_list_{metric}.npy",
        np.asarray(scores_list, dtype=np.float64),
    )


def load_generated_training_arrays(
    metric: str,
    training_data_dir: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Load staged features and labels."""
    path = training_data_dir / f"training_data_{metric}.npy"
    training_data = np.load(path, allow_pickle=True)
    if len(training_data) == 0:
        raise SystemExit(f"Nessun campione generato per {metric}: {path}")
    x_list, y_list = zip(*training_data, strict=False)
    return np.asarray(x_list, dtype=np.float64), np.asarray(y_list, dtype=str)


def latest_manifest_records(path: Path) -> dict[str, dict[str, Any]]:
    """Return the latest terminal record for every circuit/device pair."""
    latest: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return latest
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("status") == "running":
                continue
            key = record.get("key")
            if isinstance(key, str):
                latest[key] = record
    return latest


def project_path(path: Path) -> str:
    """Render workspace paths as portable relative paths when possible."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def export_dataset_json(
    metric: str,
    training_data_dir: Path,
    compiled_dir: Path,
    manifest_path: Path,
    device_names: list[str],
    output_path: Path,
    strict_rl_keys: set[str],
    run_metadata: dict[str, Any],
) -> None:
    """Write the single, human-readable device-selector dataset."""
    training_data = np.load(
        training_data_dir / f"training_data_{metric}.npy",
        allow_pickle=True,
    )
    names = np.load(training_data_dir / f"names_list_{metric}.npy", allow_pickle=True)
    scores = np.load(training_data_dir / f"scores_list_{metric}.npy", allow_pickle=True)
    if len({len(training_data), len(names), len(scores)}) != 1:
        raise SystemExit("Array intermedi incoerenti: training_data, names e scores hanno lunghezze diverse.")
    if scores.ndim != 2 or scores.shape[1] != len(device_names):
        raise SystemExit(
            f"Colonne score incoerenti: {scores.shape}; dispositivi={device_names}."
        )

    feature_names = [f"gate_count_{gate}" for gate in get_openqasm_gates()] + [
        "num_qubits",
        "depth",
        "program_communication",
        "critical_depth",
        "entanglement_ratio",
        "parallelism",
        "liveness",
    ]
    latest = latest_manifest_records(manifest_path)
    label_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []

    for index, (name_value, sample, score_values) in enumerate(
        zip(names, training_data, scores, strict=True)
    ):
        name = str(name_value)
        features, label_value = sample
        label = str(label_value)
        label_counts[label] += 1
        feature_values = [float(value) for value in features]
        source_num_qubits = int(feature_values[feature_names.index("num_qubits")])
        score_by_device: dict[str, float] = {}
        compilations: dict[str, dict[str, Any]] = {}

        for device_name, raw_score in zip(device_names, score_values, strict=True):
            score = float(raw_score)
            score_by_device[device_name] = score
            compiled_path = compiled_dir / f"{name}_{metric}-{device_name}.qasm"
            checkpoint = latest.get(f"{name}|{device_name}")
            strict_rl = (
                f"{name}|{device_name}" in strict_rl_keys
                and is_strict_rl_success(checkpoint)
                and is_valid_qasm(compiled_path)
            )
            if score > WORST_SCORE and not strict_rl:
                raise SystemExit(
                    f"Score non-RL rilevato per {name}|{device_name}. "
                    "Rigenera gli array con --finalize-only prima di esportare il JSON."
                )
            device = get_device(device_name)
            if source_num_qubits > device.num_qubits:
                mode = "rl"
                status = "incompatible_num_qubits"
            elif checkpoint is None:
                mode = "rl"
                status = "missing"
            else:
                status = str(checkpoint.get("status", "unknown"))
                mode = str(checkpoint.get("mode") or ("rl" if status == "success" else "unknown"))
            passes = [str(value) for value in checkpoint.get("passes", [])] if checkpoint else []
            error = checkpoint.get("error") if checkpoint else None
            provenance_counts[mode] += 1
            compilations[device_name] = {
                "mode": mode,
                "status": status,
                "qasm": project_path(compiled_path) if strict_rl else None,
                "passes": passes,
                "error": error,
                "used_for_score": strict_rl and score > WORST_SCORE,
            }

        expected_label = choose_best_device(device_names, list(score_by_device.values()))
        if expected_label != label:
            raise SystemExit(
                f"Label/score incoerenti per {name}: label={label}, argmax={expected_label}."
            )
        records.append(
            {
                "index": index,
                "circuit": name,
                "source_qasm": f"{name}.qasm",
                "label_device": label,
                "scores": score_by_device,
                "features": dict(zip(feature_names, feature_values, strict=True)),
                "compiled_circuits": compilations,
            }
        )

    payload: dict[str, Any] = {
        "schema_version": 2,
        "worst_score": WORST_SCORE,
        "generated_at": utc_now(),
        "metric": metric,
        "source_corpus": (
            "circuiti device-selection inclusi in "
            f"mqt.predictor {package_version('mqt.predictor')}"
        ),
        "sample_count": len(records),
        "feature_count": len(feature_names),
        "devices": device_names,
        "label_distribution": dict(label_counts),
        "compilation_provenance": dict(provenance_counts),
        "feature_names": feature_names,
        "run": run_metadata,
        "records": records,
    }
    atomic_json_write(output_path, payload)
    print(f"Dataset JSON canonico: {output_path} ({len(records)} circuiti)")


def train_selector_model(
    metric: str,
    training_data_dir: Path,
    model_path: Path,
    rf_workers: int,
    seed: int,
    expected_devices: list[str] | None,
) -> None:
    """Select hyperparameters on a holdout, then refit on every sample."""
    x, y = load_generated_training_arrays(metric, training_data_dir)
    label_counts = Counter(y)
    smallest_class = min(label_counts.values())

    if len(y) < 20 or smallest_class < 2:
        classifier: Any = RandomForestClassifier(
            n_estimators=200,
            random_state=seed,
            class_weight="balanced",
        )
        classifier.fit(x, y)
        print("Dataset piccolo/sbilanciato: uso Random Forest compatta senza GridSearchCV.")
    else:
        x_train, _x_test, y_train, _y_test = train_test_split(
            x,
            y,
            test_size=0.3,
            random_state=seed,
            stratify=y,
        )
        train_counts = Counter(y_train)
        num_cv = min(5, min(train_counts.values()))
        if num_cv < 2:
            classifier = RandomForestClassifier(
                n_estimators=500,
                random_state=seed,
                class_weight="balanced",
            )
            classifier.fit(x_train, y_train)
        else:
            tree_param = [
                {
                    "n_estimators": [100, 200, 500],
                    "max_depth": list(range(8, 30, 6)),
                    "min_samples_split": list(range(2, 20, 6)),
                    "min_samples_leaf": list(range(2, 20, 6)),
                    "bootstrap": [True, False],
                }
            ]
            classifier = GridSearchCV(
                RandomForestClassifier(random_state=seed, class_weight="balanced"),
                tree_param,
                cv=num_cv,
                n_jobs=rf_workers,
                verbose=1,
            ).fit(x_train, y_train)

        if isinstance(classifier, GridSearchCV):
            print(
                f"Migliori iperparametri: {classifier.best_params_}; "
                f"accuracy CV={classifier.best_score_:.4f}."
            )
            classifier = RandomForestClassifier(
                random_state=seed,
                class_weight="balanced",
                **classifier.best_params_,
            )
        classifier.fit(x, y)
        print(f"Refit finale completato su tutti i {len(y)} circuiti.")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temp = model_path.with_name(f".{model_path.name}.{os.getpid()}.tmp")
    joblib_dump(classifier, temp)
    loaded = joblib_load(temp)
    loaded.predict_proba(x[:1])
    learned_devices = set(map(str, loaded.classes_))
    if expected_devices is not None and learned_devices != set(expected_devices):
        temp.unlink(missing_ok=True)
        missing = sorted(set(expected_devices) - learned_devices)
        unexpected = sorted(learned_devices - set(expected_devices))
        raise SystemExit(
            "Il classificatore non copre esattamente i cinque device congelati. "
            f"Mancanti={missing}; inattesi={unexpected}. "
            "Il modello canonico non è stato aggiornato."
        )
    os.replace(temp, model_path)
    print("Classi apprese: " + ", ".join(sorted(learned_devices)))
    print("Distribuzione label: " + ", ".join(f"{label}={count}" for label, count in label_counts.items()))


def deploy_selector_artifacts(
    metric: str,
    training_data_dir: Path,
    staged_model: Path,
    run_metadata: dict[str, Any],
) -> None:
    """Install runtime files and update the sole canonical workspace model."""
    target_data_dir = get_ml_training_data() / "training_data_aggregated"
    target_model = get_ml_model_path(metric)
    canonical_model = CANONICAL_MODELS_DIR / target_model.name

    filenames = [
        f"training_data_{metric}.npy",
        f"names_list_{metric}.npy",
        f"scores_list_{metric}.npy",
    ]
    for filename in filenames:
        source = training_data_dir / filename
        target = target_data_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        shutil.copy2(source, temp)
        os.replace(temp, target)

    canonical_model.parent.mkdir(parents=True, exist_ok=True)
    canonical_temp = canonical_model.with_name(f".{canonical_model.name}.{os.getpid()}.tmp")
    shutil.copy2(staged_model, canonical_temp)
    os.replace(canonical_temp, canonical_model)

    runtime_temp = target_model.with_name(f".{target_model.name}.{os.getpid()}.tmp")
    shutil.copy2(canonical_model, runtime_temp)
    os.replace(runtime_temp, target_model)
    atomic_json_write(
        canonical_model.with_suffix(".metadata.json"),
        {
            **run_metadata,
            "kind": "mqt-device-selector",
            "model_sha256": file_sha256(canonical_model),
            "training_split": "train",
        },
    )
    print(f"Device selector canonico: {canonical_model}")
    print(f"Copia runtime installata: {target_model}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--devices",
        nargs="+",
        default=list(FROZEN_DEVICES),
        help="Device con un modello RL già addestrato; default: i cinque del protocollo.",
    )
    parser.add_argument(
        "--metric",
        choices=("expected_fidelity", "critical_depth"),
        default="expected_fidelity",
    )
    parser.add_argument(
        "--uncompiled-circuits",
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
    parser.add_argument("--compiled-circuits", type=Path, help="Cache QASM compilati personalizzata.")
    parser.add_argument("--cache-dir", type=Path, help="Directory di cache per manifest e QASM intermedi.")
    parser.add_argument("--log-dir", type=Path, help="Directory dei log del device selector.")
    parser.add_argument("--dataset-json", type=Path, help="Percorso del dataset JSON finale.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout della compilazione RL per coppia circuito/device.")
    parser.add_argument(
        "--rl-max-steps",
        type=int,
        default=64,
        help="Numero massimo di azioni per episodio RL; distinto dal timeout in secondi.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed condiviso da policy RL, BQSKit e training del classificatore.",
    )
    parser.add_argument("--startup-timeout", type=int, default=240, help="Timeout per caricare un modello RL.")
    parser.add_argument(
        "--fallback-timeout",
        type=int,
        default=60,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--fallback-optimization-level",
        type=int,
        choices=(0, 1, 2, 3),
        default=2,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Modelli RL residenti e compilazioni parallele; con circa 8 GiB usa 1 worker.",
    )
    parser.add_argument("--max-attempts", type=int, default=3, help="Tentativi totali per coppia circuito/device.")
    parser.add_argument("--rf-workers", type=int, default=4, help="Worker usati dal GridSearchCV finale.")
    parser.add_argument("--progress-every", type=int, default=10, help="Frequenza del riepilogo di avanzamento.")
    parser.add_argument("--limit-circuits", type=int, help="Canary deterministico sui primi N circuiti.")
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Salta il canary automatico di un circuito per device.",
    )
    parser.add_argument(
        "--allow-target-drift",
        action="store_true",
        help="Consenti Target diversi dai fingerprint congelati; richiede rigenerare i competitor.",
    )
    parser.add_argument("--compile-only", action="store_true", help="Crea checkpoint QASM senza generare dataset/modello.")
    parser.add_argument("--finalize-only", action="store_true", help="Genera dataset/modello dai checkpoint esistenti.")
    parser.add_argument(
        "--export-json-only",
        action="store_true",
        help="Rigenera soltanto il JSON dagli array runtime già installati.",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Modalità esplorativa: usa solo circuiti con copertura completa e non pubblica il modello.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Mostra piano e copertura senza compilare o scrivere.")
    return parser.parse_args()


def main() -> int:
    """Run resumable compilation and, when complete, deploy the selector."""
    args = parse_args()
    exclusive_modes = (args.compile_only, args.finalize_only, args.export_json_only)
    if sum(bool(mode) for mode in exclusive_modes) > 1:
        raise SystemExit(
            "--compile-only, --finalize-only e --export-json-only sono mutuamente esclusivi."
        )
    for name in (
        "timeout",
        "startup_timeout",
        "fallback_timeout",
        "rl_max_steps",
        "num_workers",
        "max_attempts",
        "rf_workers",
        "progress_every",
    ):
        if getattr(args, name) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} deve essere positivo.")
    if args.limit_circuits is not None and args.limit_circuits <= 0:
        raise SystemExit("--limit-circuits deve essere positivo.")
    if os.name != "posix":
        raise SystemExit("Il runner robusto richiede Linux/WSL per process group e parent-death signal.")
    np.random.seed(args.seed)

    version_errors = package_version_mismatches()
    if version_errors:
        raise SystemExit(f"Versioni non conformi al protocollo v2: {version_errors}.")

    source_dir = args.uncompiled_circuits
    if not source_dir.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {source_dir}")
    try:
        training_partition = verify_circuit_directory(
            source_dir,
            allowed_splits=("train",),
            manifest_path=args.source_manifest,
        )
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Training set ML rifiutato: {error}") from error

    cache_dir = args.cache_dir or (DEFAULT_CACHE_ROOT / args.metric)
    compiled_dir = args.compiled_circuits or (cache_dir / "compiled")
    manifest_path = cache_dir / "manifest.jsonl"
    log_dir = args.log_dir or (DEFAULT_LOG_ROOT / args.metric)
    staging_dir = cache_dir / ".staging"
    staging_data_dir = staging_dir / "training_data"
    staged_model = staging_dir / f"trained_clf_{args.metric}.joblib"
    dataset_json = args.dataset_json or MQT_TRAINING_SET_V2

    devices = [get_device(name) for name in args.devices]
    device_names = [device.description for device in devices]
    if len(set(device_names)) != len(device_names):
        raise SystemExit("La lista --devices contiene duplicati.")
    if not args.compile_only and not args.dry_run:
        if tuple(device_names) != FROZEN_DEVICES or args.metric != FROZEN_FIGURE_OF_MERIT:
            raise SystemExit(
                "La finalizzazione pubblicabile richiede esattamente i cinque device "
                "nell'ordine congelato e la metrica expected_fidelity."
            )

    target_records = {
        device.description: target_record(device)
        for device in devices
    }
    target_sha256_by_device = {
        name: str(record["target_sha256"])
        for name, record in target_records.items()
    }
    target_mismatches = frozen_target_mismatches(devices)
    if target_mismatches:
        details = "\n".join(
            f"  - {name}: atteso={values['expected']}, osservato={values['observed']}"
            for name, values in sorted(target_mismatches.items())
        )
        message = (
            "I Target MQT correnti differiscono dai fingerprint congelati "
            "del protocollo migrato 2.4-v2:\n"
            + details
            + "\nPer confronti omogenei rigenera i competitor nello stesso ambiente. "
            "Usa --allow-target-drift soltanto come bypass temporaneo del gate."
        )
        if not args.allow_target_drift:
            raise SystemExit(message)
        print("ATTENZIONE: " + message)
    matches_frozen_protocol = bool(
        tuple(device_names) == FROZEN_DEVICES
        and args.metric == FROZEN_FIGURE_OF_MERIT
        and not target_mismatches
    )

    runtime_model_paths: dict[str, Path] = {}
    missing_models: list[Path] = []
    for device in devices:
        path = get_rl_model_dir() / f"model_{args.metric}_{device.description}.zip"
        runtime_model_paths[device.description] = path
        if not path.is_file():
            missing_models.append(path)
    if missing_models:
        formatted = "\n".join(f"  - {path}" for path in missing_models)
        raise SystemExit("Modelli RL mancanti:\n" + formatted)
    model_sha256_by_device = {
        name: file_sha256(path)
        for name, path in runtime_model_paths.items()
    }
    if matches_frozen_protocol:
        metadata_problems: list[str] = []
        for device_name in device_names:
            metadata_path = (
                CANONICAL_RL_MODELS_DIR
                / runtime_model_paths[device_name].name
            ).with_suffix(".metadata.json")
            _metadata, errors = validate_rl_training_metadata(
                metadata_path,
                device_name=device_name,
                model_sha256=model_sha256_by_device[device_name],
                expected_max_steps=args.rl_max_steps,
                expected_num_timesteps=RL_FINAL_TIMESTEPS,
            )
            metadata_problems.extend(
                f"{device_name}: {error}" for error in errors
            )
        if metadata_problems:
            formatted = "\n".join(f"  - {error}" for error in metadata_problems)
            raise SystemExit(
                "Le policy RL non attestano un training conforme a MQT Predictor "
                "2.4.0 e al protocollo congelato:\n"
                + formatted
                + "\nCompleta prima scripts/03_train_rl_model.py per tutti i device."
            )


    all_jobs, source_paths = build_jobs(source_dir, compiled_dir, device_names, args.metric)
    compile_jobs = select_compile_jobs(all_jobs, args.limit_circuits)
    run_metadata: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "protocol": PROTOCOL_ID if matches_frozen_protocol else None,
        "protocol_version": PROTOCOL_VERSION,
        "matches_frozen_protocol": matches_frozen_protocol,
        "devices": device_names,
        "figure_of_merit": args.metric,
        "seed": args.seed,
        "timeout_seconds": args.timeout,
        "rl_max_steps": args.rl_max_steps,
        "max_attempts": args.max_attempts,
        "allow_target_drift": args.allow_target_drift,
        "software": installed_package_versions(),
        "targets": target_records,
        "rl_models": {
            name: {
                "path": project_path(runtime_model_paths[name]),
                "sha256": model_sha256_by_device[name],
            }
            for name in device_names
        },
        "source_circuit_count": len(source_paths),
        "source_manifest_sha256": training_partition["manifest_sha256"],
        "training_split": "train",
        "compatible_compilation_count": len(all_jobs),
    }
    strict_before = strict_rl_success_keys(
        compile_jobs,
        manifest_path,
        rl_max_steps=args.rl_max_steps,
        seed=args.seed,
        model_sha256_by_device=model_sha256_by_device,
        target_sha256_by_device=target_sha256_by_device,
    )
    valid_before = len(strict_before)

    per_device = Counter(job.device_name for job in all_jobs)
    print(f"Circuiti sorgente: {len(source_paths)}")
    print(f"Compilazioni compatibili totali: {len(all_jobs)}")
    print("Per device: " + ", ".join(f"{name}={per_device[name]}" for name in sorted(per_device)))
    if args.limit_circuits:
        print(f"Canary: {args.limit_circuits} circuiti, {len(compile_jobs)} compilazioni.")
    print(f"Checkpoint RL già validi nella directory durevole: {valid_before}")
    print(f"Cache compilazioni: {cache_dir}")
    print(f"Log: {log_dir}")
    print(f"Dataset JSON: {dataset_json}")

    if args.dry_run:
        strict_keys = strict_rl_success_keys(
            all_jobs,
            manifest_path,
            rl_max_steps=args.rl_max_steps,
            seed=args.seed,
            model_sha256_by_device=model_sha256_by_device,
            target_sha256_by_device=target_sha256_by_device,
        )
        _complete, missing = coverage_report(all_jobs, source_paths, strict_keys)
        print(f"Copertura RL corrente: {len(all_jobs) - len(missing)}/{len(all_jobs)}")
        return 0

    cache_dir.mkdir(parents=True, exist_ok=True)
    compiled_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.export_json_only:
        runtime_data = get_ml_training_data() / "training_data_aggregated"
        strict_keys = strict_rl_success_keys(
            all_jobs,
            manifest_path,
            rl_max_steps=args.rl_max_steps,
            seed=args.seed,
            model_sha256_by_device=model_sha256_by_device,
            target_sha256_by_device=target_sha256_by_device,
        )
        _complete, missing = coverage_report(all_jobs, source_paths, strict_keys)
        if missing:
            raise SystemExit(
                "--export-json-only richiede copertura RL completa per la "
                f"configurazione corrente; mancano {len(missing)} compilazioni."
            )
        predictor = Predictor(devices=devices, figure_of_merit=args.metric)
        export_dataset_json(
            args.metric,
            runtime_data,
            compiled_dir,
            manifest_path,
            [device.description for device in predictor.devices],
            dataset_json,
            strict_keys,
            run_metadata,
        )
        return 0

    if not args.finalize_only:
        if args.limit_circuits is None and not args.skip_preflight:
            preflight_jobs = []
            seen_devices: set[str] = set()
            for job in compile_jobs:
                if job.device_name in seen_devices:
                    continue
                seen_devices.add(job.device_name)
                preflight_jobs.append(job)
            print(
                "Preflight automatico: una compilazione per ciascun device "
                "prima del run completo."
            )
            compile_resumably(
                preflight_jobs,
                metric=args.metric,
                rl_max_steps=args.rl_max_steps,
                seed=args.seed,
                model_sha256_by_device=model_sha256_by_device,
                target_sha256_by_device=target_sha256_by_device,
                num_workers=args.num_workers,
                timeout=args.timeout,
                startup_timeout=args.startup_timeout,
                fallback_timeout=args.fallback_timeout,
                fallback_enabled=False,
                fallback_optimization_level=args.fallback_optimization_level,
                max_attempts=args.max_attempts,
                manifest_path=manifest_path,
                log_dir=log_dir,
                progress_every=1,
            )
            preflight_successes = strict_rl_success_keys(
                preflight_jobs,
                manifest_path,
                rl_max_steps=args.rl_max_steps,
                seed=args.seed,
                model_sha256_by_device=model_sha256_by_device,
                target_sha256_by_device=target_sha256_by_device,
            )
            failed_preflight = [job for job in preflight_jobs if job.key not in preflight_successes]
            if failed_preflight:
                failed_names = ", ".join(job.device_name for job in failed_preflight)
                raise SystemExit(
                    f"Preflight RL fallito per {failed_names}. "
                    "Il run completo non è stato avviato; i checkpoint validi restano salvati."
                )
        compile_resumably(
            compile_jobs,
            metric=args.metric,
            rl_max_steps=args.rl_max_steps,
            seed=args.seed,
            model_sha256_by_device=model_sha256_by_device,
            target_sha256_by_device=target_sha256_by_device,
            num_workers=args.num_workers,
            timeout=args.timeout,
            startup_timeout=args.startup_timeout,
            fallback_timeout=args.fallback_timeout,
            fallback_enabled=False,
            fallback_optimization_level=args.fallback_optimization_level,
            max_attempts=args.max_attempts,
            manifest_path=manifest_path,
            log_dir=log_dir,
            progress_every=args.progress_every,
        )
        if args.compile_only:
            successful_rl_keys = strict_rl_success_keys(
                all_jobs,
                manifest_path,
                rl_max_steps=args.rl_max_steps,
                seed=args.seed,
                model_sha256_by_device=model_sha256_by_device,
                target_sha256_by_device=target_sha256_by_device,
            )
            complete_sources, missing = coverage_report(
                all_jobs,
                source_paths,
                successful_rl_keys,
            )
            print(
                f"Compile-only terminato: {len(all_jobs) - len(missing)}/{len(all_jobs)} "
                f"compilazioni RL, {len(complete_sources)}/{len(source_paths)} circuiti completi. "
                "La finalizzazione pubblicabile resterà bloccata finché la copertura "
                "non sarà completa."
            )
            return 0

    successful_rl_keys = strict_rl_success_keys(
        all_jobs,
        manifest_path,
        rl_max_steps=args.rl_max_steps,
        seed=args.seed,
        model_sha256_by_device=model_sha256_by_device,
        target_sha256_by_device=target_sha256_by_device,
    )
    complete_sources, missing = coverage_report(
        all_jobs,
        source_paths,
        successful_rl_keys,
    )
    production_ready = not missing
    missing_counts = Counter(job.device_name for job in missing)
    run_metadata["coverage"] = {
        "strict_successes": len(successful_rl_keys),
        "required_compilations": len(all_jobs),
        "complete_source_circuits": len(complete_sources),
        "source_circuit_count": len(source_paths),
        "missing_by_device": dict(sorted(missing_counts.items())),
    }
    run_metadata["publication_status"] = (
        "production" if production_ready else "exploratory-incomplete"
    )

    if missing:
        summary = (
            f"Compilazioni RL fallite o mancanti: {len(missing)}; "
            f"copertura completa per {len(complete_sources)}/{len(source_paths)} circuiti. "
            "Mancanti per device: "
            + ", ".join(
                f"{device}={count}"
                for device, count in sorted(missing_counts.items())
            )
            + "."
        )
        if not args.allow_incomplete:
            raise SystemExit(
                summary
                + " Finalizzazione annullata: completa i checkpoint RL oppure usa "
                "--allow-incomplete soltanto per un artefatto esplorativo non pubblicato."
            )
        if not complete_sources:
            raise SystemExit(summary + " Nessun circuito completo da usare in modalità esplorativa.")
        print(
            "MODALITÀ ESPLORATIVA: "
            + summary
            + " Uso soltanto i circuiti a copertura completa e non aggiorno gli artefatti canonici."
        )
        selected_sources = complete_sources
    else:
        selected_sources = list(source_paths.values())

    predictor = Predictor(devices=devices, figure_of_merit=args.metric)
    generate_training_arrays(
        predictor,
        selected_sources,
        compiled_dir,
        staging_data_dir,
        args.metric,
        min(args.num_workers, 4),
        successful_rl_keys,
    )
    train_selector_model(
        args.metric,
        staging_data_dir,
        staged_model,
        args.rf_workers,
        args.seed,
        device_names if production_ready else None,
    )
    staged_dataset = staging_dir / dataset_json.name
    export_dataset_json(
        args.metric,
        staging_data_dir,
        compiled_dir,
        manifest_path,
        [device.description for device in predictor.devices],
        staged_dataset,
        successful_rl_keys,
        run_metadata,
    )

    if not production_ready:
        print(f"Artefatto esplorativo: {staged_model}")
        print(f"Dataset esplorativo: {staged_dataset}")
        print("Gli artefatti canonici e runtime non sono stati modificati.")
        return 0

    deploy_selector_artifacts(
        args.metric,
        staging_data_dir,
        staged_model,
        run_metadata,
    )
    dataset_json.parent.mkdir(parents=True, exist_ok=True)
    dataset_temp = dataset_json.with_name(f".{dataset_json.name}.{os.getpid()}.tmp")
    shutil.copy2(staged_dataset, dataset_temp)
    os.replace(dataset_temp, dataset_json)
    shutil.rmtree(staging_dir, ignore_errors=True)
    print("Pipeline conclusa: JSON e modello canonico sono aggiornati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

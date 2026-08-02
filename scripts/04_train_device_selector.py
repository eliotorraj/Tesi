"""Compile resumably and train the supervised MQT device selector.

The expensive part of device-selector training is not fitting the Random
Forest. It is compiling every source circuit with every compatible RL model.
This runner therefore treats each ``circuit x device`` compilation as an
independent, durable checkpoint.

Canonical outputs:
- readable dataset: ``datasets/device_selector_<metric>.json``;
- final model: ``artifacts/models/ml/``;
- reusable compiled-QASM cache: ``artifacts/cache/ml/``;
- runtime logs: ``artifacts/logs/ml/``.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DATASETS_DIR = PROJECT_ROOT / "datasets"
CANONICAL_MODELS_DIR = PROJECT_ROOT / "artifacts" / "models" / "ml"
DEFAULT_CACHE_ROOT = PROJECT_ROOT / "artifacts" / "cache" / "ml"
DEFAULT_LOG_ROOT = PROJECT_ROOT / "artifacts" / "logs" / "ml"
DEFAULT_WORKERS = 2
ESTIMATED_RL_WORKER_GIB = 2.2
WORKER_WATCHDOG_GRACE_SECONDS = 30
WORST_SCORE = -1.0
RL_SUCCESS_STATUSES = {"success", "success_recovered_after_timeout"}
SUCCESS_STATUSES = RL_SUCCESS_STATUSES | {"success_fallback"}


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
    """Load attempts and last status, tolerating an interrupted last line."""
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
            attempt = record.get("attempt")
            if isinstance(attempt, int):
                attempts[key] = max(attempts.get(key, 0), attempt)
            status = record.get("status")
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

        # BQSKit 1.2.0 has a bug in DetachedServer.handle_disconnect: it
        # appends an out-of-scope ``task_id`` instead of the key currently
        # iterated. Patch only this subprocess; do not modify site-packages.
        server_bootstrap = """
from bqskit.runtime.base import ServerBase
from bqskit.runtime.detached import DetachedServer, start_server

def fixed_handle_disconnect(self, conn):
    ServerBase.handle_disconnect(self, conn)
    tasks = self.clients.pop(conn, set())
    for task_id in tasks:
        self.handle_cancel_comp_task(task_id)
    tasks_to_pop = []
    for task_id, (tid, other_conn) in list(self.tasks.items()):
        if other_conn == conn:
            tasks_to_pop.append((task_id, tid))
    for task_id, tid in tasks_to_pop:
        self.tasks.pop(task_id, None)
        self.mailbox_to_task_dict.pop(tid, None)

DetachedServer.handle_disconnect = fixed_handle_disconnect
start_server()
"""
        self.server_process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                server_bootstrap,
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


def configure_shared_bqskit_runtime(server_port: int) -> Any:
    """Route MQT BQSKit actions to the shared detached runtime."""
    import mqt.predictor.rl.actions as actions_module
    from bqskit.compiler import Compiler

    original_compile = actions_module.bqskit_compile
    shared_compiler = Compiler(ip="localhost", port=server_port)

    def shared_compile(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("num_workers", None)
        kwargs.pop("ip", None)
        kwargs.pop("port", None)
        kwargs["compiler"] = shared_compiler
        return original_compile(*args, **kwargs)

    actions_module.bqskit_compile = shared_compile
    return shared_compiler


def legacy_device_worker(
    device_name: str,
    metric: str,
    jobs: list[CompilationJob],
    server_port: int,
    result_queue: Any,
    log_path: Path,
) -> None:
    """Load one RL policy once, then compile all assigned circuits."""
    _set_parent_death_signal()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", buffering=1) as log_handle:
        os.dup2(log_handle.fileno(), sys.stdout.fileno())
        os.dup2(log_handle.fileno(), sys.stderr.fileno())
        print(f"\n--- worker start {utc_now()} pid={os.getpid()} device={device_name} ---", flush=True)

        shared_compiler = None
        try:
            shared_compiler = configure_shared_bqskit_runtime(server_port)
            import mqt.predictor.rl.predictor as rl_predictor_module

            device = get_device(device_name)
            predictor = rl_predictor_module.Predictor(figure_of_merit=metric, device=device)
            model_name = f"model_{metric}_{device_name}"
            cached_model = rl_predictor_module.load_model(model_name)

            # MQT 2.3.0 loads the same multi-GB PPO archive on every call.
            # Keep it resident for the lifetime of this device worker.
            rl_predictor_module.load_model = lambda _name: cached_model
            result_queue.put({"type": "ready", "device": device_name, "pid": os.getpid()})

            for job in jobs:
                result_queue.put(
                    {
                        "type": "started",
                        "device": device_name,
                        "pid": os.getpid(),
                        "key": job.key,
                    }
                )
                started = time.monotonic()
                temp_output = job.output.with_name(f".{job.output.name}.{os.getpid()}.tmp")
                try:
                    circuit = QuantumCircuit.from_qasm_file(job.source)
                    compiled, passes = predictor.compile_as_predicted(circuit)
                    temp_output.parent.mkdir(parents=True, exist_ok=True)
                    with temp_output.open("w", encoding="utf-8") as handle:
                        qasm_dump(compiled, handle)
                        handle.flush()
                        os.fsync(handle.fileno())
                    QuantumCircuit.from_qasm_file(temp_output)
                    os.replace(temp_output, job.output)
                    result_queue.put(
                        {
                            "type": "result",
                            "status": "success",
                            "device": device_name,
                            "pid": os.getpid(),
                            "key": job.key,
                            "duration_seconds": round(time.monotonic() - started, 3),
                            "passes": passes,
                        }
                    )
                except Exception as exc:
                    if temp_output.exists():
                        temp_output.unlink()
                    result_queue.put(
                        {
                            "type": "result",
                            "status": "failed",
                            "device": device_name,
                            "pid": os.getpid(),
                            "key": job.key,
                            "duration_seconds": round(time.monotonic() - started, 3),
                            "error": f"{type(exc).__name__}: {exc}",
                            "traceback": traceback.format_exc(limit=20)[-8000:],
                        }
                    )

            result_queue.put({"type": "done", "device": device_name, "pid": os.getpid()})
        except BaseException:
            print(traceback.format_exc(), flush=True)
            raise
        finally:
            if shared_compiler is not None:
                shared_compiler.close()


def _compile_job_process(
    job: CompilationJob,
    device: Any,
    predictor: Any,
    cached_model: Any,
    server_port: int,
    mode: str,
    fallback_optimization_level: int,
    result_connection: Any,
) -> None:
    """Compile one job in a disposable process forked after PPO loading."""
    _set_parent_death_signal()
    started = time.monotonic()
    shared_compiler = None
    temp_output = job.output.with_name(f".{job.output.name}.{os.getpid()}.tmp")
    result: dict[str, Any]
    try:
        circuit = QuantumCircuit.from_qasm_file(job.source)
        if mode == "rl":
            shared_compiler = configure_shared_bqskit_runtime(server_port)
            import mqt.predictor.rl.predictor as rl_predictor_module

            rl_predictor_module.load_model = lambda _name: cached_model
            original_step = predictor.env.step

            def logged_step(action: int) -> Any:
                action_name = predictor.env.action_set[int(action)].name
                print(f"job={job.key} azione_RL={action_name}", flush=True)
                return original_step(action)

            predictor.env.step = logged_step
            compiled, passes = predictor.compile_as_predicted(circuit)
        elif mode == "fallback":
            print(
                f"job={job.key} fallback=QiskitO{fallback_optimization_level}",
                flush=True,
            )
            compiled = qiskit_transpile(
                circuit,
                target=device,
                optimization_level=fallback_optimization_level,
                seed_transpiler=0,
            )
            passes = [f"fallback:qiskit_transpile_o{fallback_optimization_level}"]
        else:
            raise ValueError(f"Modalità di compilazione sconosciuta: {mode}")

        temp_output.parent.mkdir(parents=True, exist_ok=True)
        with temp_output.open("w", encoding="utf-8") as handle:
            qasm_dump(compiled, handle)
            handle.flush()
            os.fsync(handle.fileno())
        QuantumCircuit.from_qasm_file(temp_output)
        os.replace(temp_output, job.output)
        result = {
            "status": "success",
            "mode": mode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "passes": passes,
        }
    except BaseException as exc:
        temp_output.unlink(missing_ok=True)
        result = {
            "status": "failed",
            "mode": mode,
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
            if output_changed(job.output, previous_output_version):
                result = {
                    "status": "success_recovered_after_timeout",
                    "mode": mode,
                    "passes": [],
                }
            else:
                result = {
                    "status": "timeout",
                    "mode": mode,
                    "error": f"superato limite {mode} di {timeout}s",
                }
        elif result is None:
            process.join(timeout=1)
            if receive_connection.poll():
                try:
                    result = receive_connection.recv()
                except EOFError:
                    result = None
            if result is None and output_changed(job.output, previous_output_version):
                result = {
                    "status": "success_recovered_after_timeout",
                    "mode": mode,
                    "passes": [],
                }
            elif result is None:
                result = {
                    "status": "failed",
                    "mode": mode,
                    "error": f"processo {mode} terminato con exit code {process.exitcode}",
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
            predictor = rl_predictor_module.Predictor(figure_of_merit=metric, device=device)
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


def is_strict_rl_success(record: dict[str, Any] | None) -> bool:
    """Return whether a manifest record proves a usable RL compilation."""
    if record is None:
        return False
    status = record.get("status")
    mode = record.get("mode")
    if status == "success":
        return mode in (None, "rl") and "fallback_reason" not in record
    if status == "success_recovered_after_timeout":
        return mode == "rl" or record.get("phase") == "rl"
    return False


def strict_rl_success_keys(
    jobs: list[CompilationJob],
    manifest_path: Path,
) -> set[str]:
    """Return jobs backed by both RL provenance and a valid compiled QASM."""
    latest = latest_manifest_records(manifest_path)
    return {
        job.key
        for job in jobs
        if is_strict_rl_success(latest.get(job.key)) and is_valid_qasm(job.output)
    }



def compile_resumably(
    jobs: list[CompilationJob],
    *,
    metric: str,
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
    valid_job_keys = strict_rl_success_keys(jobs, manifest_path)
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
            attempt = max(max_attempts, attempts.get(job.key, 0) + 1)
            append_manifest(
                manifest_path,
                {
                    "timestamp": utc_now(),
                    "key": job.key,
                    "circuit": job.circuit_name,
                    "device": job.device_name,
                    "attempt": attempt,
                    "status": "rl_runtime_unavailable",
                    "mode": "rl",
                    "error": error,
                },
            )
        print(f"Runtime RL non disponibile: {error}. Assegno lo score minimo e continuo.")
        return
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
    runtime_failure_reported = False

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
                    "error": error,
                },
            )
            processed_results += 1
        print(
            f"Modello RL {device_name} non disponibile: {error}. "
            f"Tutte le sue coppie riceveranno lo score {WORST_SCORE}."
        )

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
                                "passes",
                                "mode",
                                "fallback_reason",
                                "rl_status",
                                "error",
                                "traceback",
                            ):
                                if field in message:
                                    record[field] = message[field]
                            if is_strict_rl_success(record):
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
                    if (
                        state.current_phase == "rl"
                        and output_changed(state.current_job.output, state.current_output_version)
                    ):
                        valid_job_keys.add(state.current_job.key)
                        successful_results = len(valid_job_keys)
                        append_manifest(
                            manifest_path,
                            {
                                "timestamp": utc_now(),
                                "key": state.current_job.key,
                                "circuit": state.current_job.circuit_name,
                                "device": state.current_job.device_name,
                                "attempt": state.current_attempt,
                                "status": "success_recovered_after_timeout",
                                "phase": state.current_phase,
                            },
                        )
                    else:
                        record_failure(
                            state,
                            "worker_watchdog_timeout",
                            f"worker senza risposta in fase {state.current_phase}",
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
                        if (
                            state.current_phase == "rl"
                            and output_changed(state.current_job.output, state.current_output_version)
                        ):
                            valid_job_keys.add(state.current_job.key)
                            successful_results = len(valid_job_keys)
                            append_manifest(
                                manifest_path,
                                {
                                    "timestamp": utc_now(),
                                    "key": state.current_job.key,
                                    "circuit": state.current_job.circuit_name,
                                    "device": state.current_job.device_name,
                                    "attempt": state.current_attempt,
                                    "status": "success_recovered_after_timeout",
                                    "phase": state.current_phase,
                                },
                            )
                        else:
                            record_failure(
                                state,
                                "worker_crash",
                                f"worker terminato con exit code {state.process.exitcode}",
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

            if not runtime.is_alive() and not runtime_failure_reported:
                print(
                    "ATTENZIONE: il runtime BQSKit condiviso si è arrestato; "
                    "continuo senza interrompere il run. Le compilazioni RL "
                    "falliranno rapidamente, riceveranno lo score minimo e il run "
                    "proseguira con le altre coppie. "
                    f"Dettagli: {log_dir / 'bqskit_server.log'}."
                )
                runtime_failure_reported = True

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
        device = get_device(device_name)
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
    results = Parallel(n_jobs=num_workers, verbose=10)(
        delayed(generate_training_sample)(
            source,
            compiled_dir,
            metric,
            device_names,
            successful_rl_keys,
        )
        for source in sorted(sources)
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
            strict_rl = is_strict_rl_success(checkpoint) and is_valid_qasm(compiled_path)
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
        "source_corpus": "600 circuiti device-selection inclusi in mqt.predictor 2.3.0",
        "sample_count": len(records),
        "feature_count": len(feature_names),
        "devices": device_names,
        "label_distribution": dict(label_counts),
        "compilation_provenance": dict(provenance_counts),
        "feature_names": feature_names,
        "records": records,
    }
    atomic_json_write(output_path, payload)
    print(f"Dataset JSON canonico: {output_path} ({len(records)} circuiti)")


def train_selector_model(
    metric: str,
    training_data_dir: Path,
    model_path: Path,
    rf_workers: int,
) -> None:
    """Select hyperparameters on a holdout, then refit on every sample."""
    x, y = load_generated_training_arrays(metric, training_data_dir)
    label_counts = Counter(y)
    smallest_class = min(label_counts.values())

    if len(y) < 20 or smallest_class < 2:
        classifier: Any = RandomForestClassifier(
            n_estimators=200,
            random_state=0,
            class_weight="balanced",
        )
        classifier.fit(x, y)
        print("Dataset piccolo/sbilanciato: uso Random Forest compatta senza GridSearchCV.")
    else:
        x_train, _x_test, y_train, _y_test = train_test_split(
            x,
            y,
            test_size=0.3,
            random_state=5,
            stratify=y,
        )
        train_counts = Counter(y_train)
        num_cv = min(5, min(train_counts.values()))
        if num_cv < 2:
            classifier = RandomForestClassifier(
                n_estimators=500,
                random_state=0,
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
                RandomForestClassifier(random_state=0, class_weight="balanced"),
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
                random_state=0,
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
    os.replace(temp, model_path)
    print("Distribuzione label: " + ", ".join(f"{label}={count}" for label, count in label_counts.items()))


def deploy_selector_artifacts(
    metric: str,
    training_data_dir: Path,
    staged_model: Path,
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
    print(f"Device selector canonico: {canonical_model}")
    print(f"Copia runtime installata: {target_model}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--devices", nargs="+", required=True, help="Device con un modello RL già addestrato.")
    parser.add_argument(
        "--metric",
        choices=("expected_fidelity", "critical_depth"),
        default="expected_fidelity",
    )
    parser.add_argument("--uncompiled-circuits", type=Path, help="Directory QASM; usa i 600 circuiti inclusi se omessa.")
    parser.add_argument("--compiled-circuits", type=Path, help="Cache QASM compilati personalizzata.")
    parser.add_argument("--cache-dir", type=Path, help="Directory di cache per manifest e QASM intermedi.")
    parser.add_argument("--log-dir", type=Path, help="Directory dei log del device selector.")
    parser.add_argument("--dataset-json", type=Path, help="Percorso del dataset JSON finale.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout della compilazione RL per coppia circuito/device.")
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
        help="Modelli RL residenti e compilazioni parallele; 2 è sicuro con circa 8 GiB di RAM.",
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
        help=argparse.SUPPRESS,
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
    for name in ("timeout", "startup_timeout", "fallback_timeout", "num_workers", "max_attempts", "rf_workers", "progress_every"):
        if getattr(args, name) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} deve essere positivo.")
    if args.limit_circuits is not None and args.limit_circuits <= 0:
        raise SystemExit("--limit-circuits deve essere positivo.")
    if os.name != "posix":
        raise SystemExit("Il runner robusto richiede Linux/WSL per process group e parent-death signal.")

    source_dir = args.uncompiled_circuits or get_ml_training_circuits()
    if not source_dir.is_dir():
        raise SystemExit(f"Directory QASM non trovata: {source_dir}")
    ensure_training_circuits(source_dir)

    cache_dir = args.cache_dir or (DEFAULT_CACHE_ROOT / args.metric)
    compiled_dir = args.compiled_circuits or (cache_dir / "compiled")
    manifest_path = cache_dir / "manifest.jsonl"
    log_dir = args.log_dir or (DEFAULT_LOG_ROOT / args.metric)
    staging_dir = cache_dir / ".staging"
    staging_data_dir = staging_dir / "training_data"
    staged_model = staging_dir / f"trained_clf_{args.metric}.joblib"
    dataset_json = args.dataset_json or (
        CANONICAL_DATASETS_DIR / f"device_selector_{args.metric}.json"
    )

    devices = [get_device(name) for name in args.devices]
    device_names = [device.description for device in devices]
    if len(set(device_names)) != len(device_names):
        raise SystemExit("La lista --devices contiene duplicati.")

    missing_models = []
    for device in devices:
        path = get_rl_model_dir() / f"model_{args.metric}_{device.description}.zip"
        if not path.exists():
            missing_models.append(path)
    if missing_models:
        formatted = "\n".join(f"  - {path}" for path in missing_models)
        print("Modelli RL mancanti; le relative coppie riceveranno lo score minimo:\n" + formatted)

    all_jobs, source_paths = build_jobs(source_dir, compiled_dir, device_names, args.metric)
    compile_jobs = select_compile_jobs(all_jobs, args.limit_circuits)
    strict_before = strict_rl_success_keys(compile_jobs, manifest_path)
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
        strict_keys = strict_rl_success_keys(all_jobs, manifest_path)
        _complete, missing = coverage_report(all_jobs, source_paths, strict_keys)
        print(f"Copertura RL corrente: {len(all_jobs) - len(missing)}/{len(all_jobs)}")
        return 0

    cache_dir.mkdir(parents=True, exist_ok=True)
    compiled_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.export_json_only:
        runtime_data = get_ml_training_data() / "training_data_aggregated"
        predictor = Predictor(devices=devices, figure_of_merit=args.metric)
        export_dataset_json(
            args.metric,
            runtime_data,
            compiled_dir,
            manifest_path,
            [device.description for device in predictor.devices],
            dataset_json,
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
            preflight_successes = strict_rl_success_keys(preflight_jobs, manifest_path)
            failed_preflight = [job for job in preflight_jobs if job.key not in preflight_successes]
            if failed_preflight:
                failed_names = ", ".join(job.device_name for job in failed_preflight)
                print(
                    "Preflight RL fallito per "
                    f"{failed_names}: assegnero lo score minimo e continuero il run completo."
                )
        compile_resumably(
            compile_jobs,
            metric=args.metric,
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
            successful_rl_keys = strict_rl_success_keys(all_jobs, manifest_path)
            complete_sources, missing = coverage_report(
                all_jobs,
                source_paths,
                successful_rl_keys,
            )
            print(
                f"Compile-only terminato: {len(all_jobs) - len(missing)}/{len(all_jobs)} "
                f"compilazioni RL, {len(complete_sources)}/{len(source_paths)} circuiti completi. "
                "Le coppie fallite riceveranno lo score minimo durante la finalizzazione."
            )
            return 0

    successful_rl_keys = strict_rl_success_keys(all_jobs, manifest_path)
    complete_sources, missing = coverage_report(
        all_jobs,
        source_paths,
        successful_rl_keys,
    )
    if missing:
        missing_counts = Counter(job.device_name for job in missing)
        print(
            f"Compilazioni RL fallite o mancanti: {len(missing)}; "
            f"copertura completa per {len(complete_sources)}/{len(source_paths)} circuiti."
        )
        print(
            "Score minimo per device: "
            + ", ".join(f"{device}={count}" for device, count in sorted(missing_counts.items()))
            + ". Il training prosegue."
        )

    predictor = Predictor(devices=devices, figure_of_merit=args.metric)
    generate_training_arrays(
        predictor,
        list(source_paths.values()),
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
    )
    export_dataset_json(
        args.metric,
        staging_data_dir,
        compiled_dir,
        manifest_path,
        [device.description for device in predictor.devices],
        dataset_json,
    )
    deploy_selector_artifacts(
        args.metric,
        staging_data_dir,
        staged_model,
    )
    shutil.rmtree(staging_dir, ignore_errors=True)
    print("Pipeline conclusa: JSON e modello canonico sono aggiornati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

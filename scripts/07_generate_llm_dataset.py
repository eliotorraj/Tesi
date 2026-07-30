"""Generate an LLM-oriented JSON dataset from the complete MQT Predictor pipeline.

The generator records:

* the target-independent source circuit and its QASM;
* the 49-value feature vector used by the supervised device selector;
* the selected figure of merit;
* the full device-selector probability ranking;
* optional offline scores/labels from MQT's aggregated training data;
* the valid actions and action selected at every RL compilation step;
* the final compiled circuit, QASM, score, and target-validity checks.

The output is checkpointed after every record, so a long run can be resumed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import signal
import subprocess
import sys
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from typing import Any

# Keep BQSKit runs tractable and avoid Matplotlib cache warnings.
os.environ.setdefault("GITHUB_ACTIONS", "true")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")

import numpy as np
from joblib import load as joblib_load
from mqt.bench.targets import get_device
from mqt.predictor.ml.helper import (
    create_feature_vector,
    get_openqasm_gates,
    get_path_trained_model as get_ml_model_path,
    get_path_training_data as get_ml_training_data_path,
)
from mqt.predictor.reward import crit_depth, expected_fidelity
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir
from mqt.predictor.rl.predictor import load_model
from mqt.predictor.rl.predictorenv import PredictorEnv
from mqt.predictor.utils import calc_supermarq_features
from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm2_dumps
from qiskit.transpiler.passes import CheckMap, GatesInBasis
from sb3_contrib.common.maskable.utils import get_action_masks
from stable_baselines3.common.utils import set_random_seed


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
DATASET_NAME = "mqt_predictor_llm_pipeline"
SUPPORTED_METRICS = ("expected_fidelity", "critical_depth")

FEATURE_NAMES = (
    [f"gate_count_{gate}" for gate in get_openqasm_gates()]
    + [
        "num_qubits",
        "depth",
        "program_communication",
        "critical_depth",
        "entanglement_ratio",
        "parallelism",
        "liveness",
    ]
)

FEATURE_DESCRIPTIONS = {
    "num_qubits": "Number of logical qubits in the target-independent circuit.",
    "depth": "Circuit depth before hardware-specific compilation.",
    "program_communication": "Normalized connectivity density of logical two-qubit interactions.",
    "critical_depth": "Fraction of two-qubit gates lying on the circuit critical path.",
    "entanglement_ratio": "Ratio of two-qubit gates to all circuit gates.",
    "parallelism": "Normalized estimate of operations that can be executed in parallel.",
    "liveness": "Fraction of the qubit-by-depth activity matrix that is occupied.",
}

METRIC_METADATA = {
    "expected_fidelity": {
        "name": "expected_fidelity",
        "optimization_direction": "maximize",
        "implementation": "mqt.predictor.reward.expected_fidelity",
        "description": (
            "Product of the fidelities associated with the operations in the "
            "compiled circuit according to the selected Qiskit Target."
        ),
        "interpretation": "Higher is better; this is an estimate, not an execution on quantum hardware.",
    },
    "critical_depth": {
        "name": "critical_depth",
        "optimization_direction": "maximize",
        "implementation": "mqt.predictor.reward.crit_depth",
        "description": (
            "MQT Predictor reward equal to 1 minus the SupermarQ critical-depth "
            "feature of the compiled circuit."
        ),
        "interpretation": "Higher is better and indicates a more parallel compiled circuit.",
    },
}


class CompilationTimeoutError(TimeoutError):
    """Raised when one instrumented RL compilation exceeds its timeout."""


def utc_now() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(UTC).isoformat()


def finite_float(value: Any) -> float | None:
    """Convert numeric values to JSON-safe finite floats."""
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def json_value(value: Any) -> Any:
    """Recursively convert NumPy and enum-like values to JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return [json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_value(item) for item in value]
    if isinstance(value, float):
        return finite_float(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return json_value(value.value)
    return value


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 digest of a bytes object."""
    return hashlib.sha256(data).hexdigest()


def path_for_json(path: Path) -> str:
    """Prefer a project-relative path when possible."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def file_metadata(path: Path) -> dict[str, Any]:
    """Describe an artifact without hashing very large model files."""
    stat = path.stat()
    return {
        "path": path_for_json(path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
    }


def package_versions() -> dict[str, str | None]:
    """Return the versions that materially affect dataset generation."""
    distributions = [
        "mqt.predictor",
        "mqt.bench",
        "qiskit",
        "qiskit-aer",
        "pytket",
        "pytket-qiskit",
        "bqskit",
        "scikit-learn",
        "stable-baselines3",
        "sb3-contrib",
        "numpy",
    ]
    result: dict[str, str | None] = {}
    for distribution in distributions:
        try:
            result[distribution] = version(distribution)
        except PackageNotFoundError:
            result[distribution] = None
    return result


def git_metadata() -> dict[str, Any]:
    """Describe the source revision used to generate the dataset."""

    def run_git(*args: str) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return completed.stdout.strip()

    status = run_git("status", "--porcelain")
    return {
        "commit": run_git("rev-parse", "HEAD"),
        "branch": run_git("branch", "--show-current"),
        "dirty": bool(status) if status is not None else None,
    }


def circuit_summary(circuit: QuantumCircuit) -> dict[str, Any]:
    """Return compact, LLM-readable circuit metrics."""
    features = calc_supermarq_features(circuit)
    return {
        "num_qubits": int(circuit.num_qubits),
        "num_clbits": int(circuit.num_clbits),
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "operation_counts": {
            str(name): int(count) for name, count in sorted(dict(circuit.count_ops()).items())
        },
        "num_parameters": len(circuit.parameters),
        "supermarq_features": {
            "program_communication": finite_float(features.program_communication),
            "critical_depth": finite_float(features.critical_depth),
            "entanglement_ratio": finite_float(features.entanglement_ratio),
            "parallelism": finite_float(features.parallelism),
            "liveness": finite_float(features.liveness),
        },
        "has_layout": circuit.layout is not None,
    }


def source_feature_vector(circuit: QuantumCircuit) -> dict[str, Any]:
    """Serialize the exact feature vector used by MQT's device selector."""
    values = [finite_float(value) for value in create_feature_vector(circuit)]
    if len(values) != len(FEATURE_NAMES):
        raise RuntimeError(
            f"Unexpected MQT feature-vector length: {len(values)} instead of {len(FEATURE_NAMES)}."
        )
    return {
        "extractor": "mqt.predictor.ml.helper.create_feature_vector",
        "feature_count": len(values),
        "ordered_names": FEATURE_NAMES,
        "ordered_values": values,
        "by_name": dict(zip(FEATURE_NAMES, values, strict=True)),
    }


def coupling_edges(target: Any) -> list[list[int]]:
    """Serialize a target coupling map."""
    coupling_map = target.build_coupling_map()
    if coupling_map is None:
        return []
    edges: Iterable[tuple[int, int]]
    if hasattr(coupling_map, "get_edges"):
        edges = coupling_map.get_edges()
    else:
        edges = coupling_map
    return sorted([[int(source), int(destination)] for source, destination in edges])


def serialize_target(target: Any) -> dict[str, Any]:
    """Serialize the hardware information relevant to selection and scoring."""
    instruction_rows = []
    for operation, qargs in target.instructions:
        qubits = None if qargs is None else [int(qubit) for qubit in qargs]
        properties = None
        try:
            properties = target[operation.name].get(qargs)
        except (AttributeError, KeyError, TypeError):
            properties = None
        instruction_rows.append({
            "name": operation.name,
            "num_qubits": int(operation.num_qubits),
            "qubits": qubits,
            "error": finite_float(getattr(properties, "error", None)),
            "duration_seconds": finite_float(getattr(properties, "duration", None)),
        })

    qubit_properties = []
    for index, properties in enumerate(target.qubit_properties or []):
        qubit_properties.append({
            "qubit": index,
            "t1_seconds": finite_float(getattr(properties, "t1", None)),
            "t2_seconds": finite_float(getattr(properties, "t2", None)),
            "frequency_hz": finite_float(getattr(properties, "frequency", None)),
        })

    return {
        "description": target.description,
        "type": f"{type(target).__module__}.{type(target).__qualname__}",
        "num_qubits": int(target.num_qubits),
        "operation_names": sorted(str(name) for name in target.operation_names),
        "coupling_map": coupling_edges(target),
        "dt_seconds": finite_float(getattr(target, "dt", None)),
        "qubit_properties": qubit_properties,
        "instructions": instruction_rows,
        "notes": (
            "This is the Qiskit Target used by MQT Predictor. Error and duration "
            "values are model metadata, not measurements collected during this run."
        ),
    }


def action_metadata(index: int, action: Any) -> dict[str, Any]:
    """Serialize one MQT compilation action."""
    return {
        "index": int(index),
        "name": str(action.name),
        "origin": str(action.origin.value),
        "pass_type": str(action.pass_type.value),
    }


def valid_action_metadata(env: PredictorEnv, mask: Iterable[bool]) -> list[dict[str, Any]]:
    """Return action metadata for actions allowed in the current state."""
    return [
        action_metadata(index, env.action_set[index])
        for index, is_valid in enumerate(mask)
        if bool(is_valid)
    ]


def evaluate_metric(circuit: QuantumCircuit, target: Any, metric: str) -> float:
    """Evaluate a compiled circuit with the same implementation used by MQT."""
    if metric == "expected_fidelity":
        return expected_fidelity(circuit, target)
    if metric == "critical_depth":
        return crit_depth(circuit)
    raise ValueError(f"Unsupported metric: {metric}")


def validate_compiled_circuit(circuit: QuantumCircuit, target: Any) -> dict[str, Any]:
    """Check whether the final circuit respects target gates and connectivity."""
    unsupported_operations = sorted(
        set(str(name) for name in circuit.count_ops())
        - set(str(name) for name in target.operation_names)
        - {"barrier"}
    )
    basis_valid: bool | None = None
    connectivity_valid: bool | None = None
    validation_errors: list[str] = []

    try:
        gates_in_basis = GatesInBasis(target=target)
        gates_in_basis(circuit)
        basis_valid = bool(gates_in_basis.property_set["all_gates_in_basis"])
    except Exception as error:  # noqa: BLE001 - validation must be recorded, not abort generation
        validation_errors.append(f"GatesInBasis: {type(error).__name__}: {error}")

    try:
        coupling_map = target.build_coupling_map()
        if coupling_map is None:
            connectivity_valid = True
        else:
            check_map = CheckMap(coupling_map=coupling_map)
            check_map(circuit)
            connectivity_valid = bool(check_map.property_set["is_swap_mapped"])
    except Exception as error:  # noqa: BLE001 - validation must be recorded, not abort generation
        validation_errors.append(f"CheckMap: {type(error).__name__}: {error}")

    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "layout_present": circuit.layout is not None,
        "unsupported_operations": unsupported_operations,
        "is_executable_on_target": bool(
            basis_valid and connectivity_valid and not unsupported_operations
        ),
        "validation_errors": validation_errors,
    }


def run_with_timeout(function: Callable[[], Any], timeout_seconds: int) -> Any:
    """Run a function with a SIGALRM timeout on POSIX systems."""
    if sys.platform == "win32":
        return function()

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise CompilationTimeoutError(f"Compilation exceeded {timeout_seconds} seconds.")

    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        return function()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def traced_rl_compile(
    circuit: QuantumCircuit,
    target: Any,
    metric: str,
    model: Any,
    *,
    deterministic: bool,
    seed: int,
    max_steps: int,
    include_intermediate_qasm: bool,
    trace: list[dict[str, Any]],
) -> tuple[QuantumCircuit, float]:
    """Mirror MQT's RL compilation loop while recording every decision."""
    set_random_seed(seed)
    env = PredictorEnv(reward_function=metric, device=target)
    observation, _ = env.reset(circuit, seed=seed)

    terminated = False
    truncated = False
    terminal_reward = 0.0
    while not (terminated or truncated):
        if len(trace) >= max_steps:
            raise RuntimeError(f"Compilation exceeded the configured maximum of {max_steps} actions.")

        mask = get_action_masks(env)
        state_before = env.state
        before_summary = circuit_summary(state_before)
        observation_before = json_value(observation)
        valid_actions = valid_action_metadata(env, mask)

        action_index_raw, _ = model.predict(
            observation,
            action_masks=mask,
            deterministic=deterministic,
        )
        action_index = int(action_index_raw)
        action = env.action_set[action_index]

        step_started = perf_counter()
        observation, reward, terminated, truncated, info = env.step(action_index)
        step_elapsed = perf_counter() - step_started

        step_record = {
            "step_index": len(trace),
            "observation_before": observation_before,
            "state_before": before_summary,
            "valid_actions_before": valid_actions,
            "selected_action": action_metadata(action_index, action),
            "reward": finite_float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "elapsed_seconds": step_elapsed,
            "state_after": circuit_summary(env.state),
            "observation_after": json_value(observation),
            "environment_info": json_value(info),
        }
        if include_intermediate_qasm:
            step_record["qasm2_after"] = qasm2_dumps(env.state)
        trace.append(step_record)
        terminal_reward = float(reward)

    if env.error_occurred:
        raise RuntimeError("MQT Predictor reported an error during RL compilation.")
    return env.state, terminal_reward


class DeviceSelector:
    """Expose MQT's classifier ranking instead of returning only the winning Target."""

    def __init__(self, metric: str) -> None:
        self.metric = metric
        self.model_path = get_ml_model_path(metric)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Device-selector model not found for '{metric}': {self.model_path}"
            )
        self.classifier = joblib_load(self.model_path)

    def select(self, circuit: QuantumCircuit, feature_values: list[float | None]) -> tuple[Any, dict[str, Any]]:
        """Return the first compatible target and the complete probability ranking."""
        probabilities = self.classifier.predict_proba([feature_values])[0]
        class_labels = self.classifier.classes_
        ranked_pairs = sorted(
            zip(probabilities, class_labels, strict=True),
            reverse=True,
        )

        ranking = []
        selected_target = None
        for rank, (probability, label) in enumerate(ranked_pairs, start=1):
            target = get_device(str(label))
            compatible = int(target.num_qubits) >= int(circuit.num_qubits)
            ranking.append({
                "rank": rank,
                "device": str(label),
                "probability": finite_float(probability),
                "num_qubits": int(target.num_qubits),
                "compatible_with_circuit_width": compatible,
            })
            if selected_target is None and compatible:
                selected_target = target

        if selected_target is None:
            raise ValueError(
                f"No classifier candidate supports a {circuit.num_qubits}-qubit circuit."
            )

        return selected_target, {
            "method": "supervised_random_forest_classifier",
            "implementation": "instrumented equivalent of mqt.predictor.ml.predict_device_for_figure_of_merit",
            "model": file_metadata(self.model_path),
            "candidate_count": len(ranking),
            "ranking": ranking,
            "selected_device": selected_target.description,
            "selection_rule": (
                "Sort predict_proba results in descending order and select the "
                "first device whose width supports the source circuit."
            ),
        }


def discover_score_device_order(
    metric: str,
    compiled_circuit_dirs: list[Path],
    score_width: int,
    classifier_classes: Iterable[str],
) -> tuple[list[str] | None, str | None]:
    """Infer the sorted device order used by MQT's aggregated scores arrays."""
    device_names: set[str] = set()
    marker = f"_{metric}-"
    for directory in compiled_circuit_dirs:
        if not directory.is_dir():
            continue
        for path in directory.glob(f"*{marker}*.qasm"):
            device_names.add(path.stem.rsplit("-", maxsplit=1)[-1])
    if len(device_names) == score_width:
        return sorted(device_names), "sorted device names discovered from compiled QASM filenames"

    class_names = sorted(str(label) for label in classifier_classes)
    if len(class_names) == score_width:
        return class_names, "sorted classifier classes (fallback because score width matches)"
    return None, None


def load_offline_ground_truth(
    metric: str,
    selector: DeviceSelector,
    aggregated_data_dir: Path,
    compiled_circuit_dirs: list[Path],
) -> dict[str, dict[str, Any]]:
    """Load optional score/label evidence generated before classifier training."""
    training_path = aggregated_data_dir / f"training_data_{metric}.npy"
    names_path = aggregated_data_dir / f"names_list_{metric}.npy"
    scores_path = aggregated_data_dir / f"scores_list_{metric}.npy"
    if not all(path.exists() for path in (training_path, names_path, scores_path)):
        return {}

    training_data = np.load(training_path, allow_pickle=True)
    names = np.load(names_path, allow_pickle=True)
    scores = np.load(scores_path, allow_pickle=True)
    if not (len(training_data) == len(names) == len(scores)):
        raise ValueError("Aggregated MQT arrays have inconsistent lengths.")

    score_width = max((len(list(row)) for row in scores), default=0)
    device_order, mapping_basis = discover_score_device_order(
        metric,
        compiled_circuit_dirs,
        score_width,
        selector.classifier.classes_,
    )

    result = {}
    for training_row, name, score_row in zip(training_data, names, scores, strict=True):
        label = str(training_row[1])
        values = [finite_float(value) for value in list(score_row)]
        mapped_scores = (
            dict(zip(device_order, values, strict=True))
            if device_order is not None and len(device_order) == len(values)
            else None
        )
        result[str(name)] = {
            "available": True,
            "best_device_label": label,
            "device_scores": mapped_scores,
            "raw_score_values": values,
            "score_device_order": device_order,
            "score_mapping_basis": mapping_basis,
            "source_files": {
                "training_data": path_for_json(training_path),
                "names": path_for_json(names_path),
                "scores": path_for_json(scores_path),
            },
            "meaning": (
                "Offline ground truth generated by compiling the source circuit "
                "for every candidate device and maximizing the selected figure of merit."
            ),
        }
    return result


def empty_offline_ground_truth() -> dict[str, Any]:
    """Describe the absence of an offline label for a source circuit."""
    return {
        "available": False,
        "best_device_label": None,
        "device_scores": None,
        "meaning": (
            "No matching row was found in the local aggregated MQT device-selector dataset. "
            "The classifier prediction is still available, but it is not an offline ground-truth label."
        ),
    }


def build_record_id(source_sha256: str, metric: str, repetition: int, seed: int) -> str:
    """Build a stable identifier for resumable generation."""
    identity = f"{source_sha256}|{metric}|{repetition}|{seed}".encode()
    return sha256_bytes(identity)[:24]


def initial_payload(args: argparse.Namespace, output_path: Path) -> dict[str, Any]:
    """Create a new dataset document."""
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": {
            "name": DATASET_NAME,
            "description": (
                "End-to-end MQT Predictor records prepared for LLM training, "
                "retrieval, analysis, and reproducible evaluation."
            ),
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "output_path": path_for_json(output_path),
            "figure_of_merit": args.metric,
            "record_count": 0,
            "successful_records": 0,
            "failed_records": 0,
            "timeout_records": 0,
            "generation_configuration": {
                "input_dir": path_for_json(args.input_dir),
                "pattern": args.pattern,
                "timeout_seconds": args.timeout,
                "max_steps": args.max_steps,
                "repetitions": args.repetitions,
                "base_seed": args.seed,
                "deterministic_policy": args.deterministic,
                "include_intermediate_qasm": args.include_intermediate_qasm,
                "max_circuits": args.max_circuits,
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "packages": package_versions(),
                "git": git_metadata(),
            },
        },
        "feature_schema": {
            "feature_count": len(FEATURE_NAMES),
            "ordered_names": FEATURE_NAMES,
            "descriptions": {
                **{
                    name: f"Count of '{name.removeprefix('gate_count_')}' gates in the source circuit."
                    for name in FEATURE_NAMES
                    if name.startswith("gate_count_")
                },
                **FEATURE_DESCRIPTIONS,
            },
        },
        "figure_of_merit": METRIC_METADATA[args.metric],
        "hardware_catalog": {},
        "records": [],
    }


def refresh_dataset_counts(payload: dict[str, Any]) -> None:
    """Update top-level counts after adding records."""
    records = payload["records"]
    payload["dataset"]["record_count"] = len(records)
    payload["dataset"]["successful_records"] = sum(
        record["status"] == "success" for record in records
    )
    payload["dataset"]["failed_records"] = sum(
        record["status"] == "error" for record in records
    )
    payload["dataset"]["timeout_records"] = sum(
        record["status"] == "timeout" for record in records
    )
    payload["dataset"]["updated_at"] = utc_now()


def write_payload_atomic(payload: dict[str, Any], output_path: Path) -> None:
    """Checkpoint a standards-compliant JSON document atomically."""
    refresh_dataset_counts(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    temporary_path.replace(output_path)


def load_or_initialize_payload(
    args: argparse.Namespace,
    output_path: Path,
) -> dict[str, Any]:
    """Create, resume, or overwrite a dataset according to explicit flags."""
    if not output_path.exists():
        return initial_payload(args, output_path)
    if args.overwrite:
        return initial_payload(args, output_path)
    if not args.resume:
        raise SystemExit(
            f"Output already exists: {output_path}. Use --resume or --overwrite explicitly."
        )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(
            f"Cannot resume schema {payload.get('schema_version')}; expected {SCHEMA_VERSION}."
        )
    if payload.get("dataset", {}).get("figure_of_merit") != args.metric:
        raise SystemExit("Cannot resume a dataset generated for a different figure of merit.")
    return payload


def collect_input_paths(input_dir: Path, pattern: str, max_circuits: int | None) -> list[Path]:
    """Collect source QASM files deterministically."""
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")
    paths = sorted(path for path in input_dir.glob(pattern) if path.is_file())
    if max_circuits is not None:
        paths = paths[:max_circuits]
    if not paths:
        raise SystemExit(f"No files matching '{pattern}' found in {input_dir}.")
    return paths


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "mini-trainingset" / "uncompiled_circuit",
        help="Directory containing target-independent OpenQASM 2 circuit files.",
    )
    parser.add_argument("--pattern", default="*.qasm", help="Glob pattern within --input-dir.")
    parser.add_argument(
        "--metric",
        choices=SUPPORTED_METRICS,
        default="expected_fidelity",
        help="Figure of merit used by both device selection and RL compilation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path. Defaults to output/llm_dataset/mqt_pipeline_<metric>.json.",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per RL compilation.")
    parser.add_argument("--max-steps", type=int, default=100, help="Maximum RL actions per trace.")
    parser.add_argument("--max-circuits", type=int, help="Limit source circuits for a pilot run.")
    parser.add_argument("--repetitions", type=int, default=1, help="Traces generated per source circuit.")
    parser.add_argument("--seed", type=int, default=0, help="Base random seed; repetition index is added.")
    parser.add_argument(
        "--deterministic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use deterministic PPO inference (default: true).",
    )
    parser.add_argument(
        "--include-intermediate-qasm",
        action="store_true",
        help="Embed the full QASM after every RL action; substantially increases dataset size.",
    )
    parser.add_argument(
        "--aggregated-data-dir",
        type=Path,
        default=get_ml_training_data_path() / "training_data_aggregated",
        help="Optional MQT aggregated .npy directory for offline scores and labels.",
    )
    parser.add_argument(
        "--compiled-circuits-dir",
        action="append",
        type=Path,
        dest="compiled_circuit_dirs",
        help="Directory used to infer offline score-column device names; repeatable.",
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--resume", action="store_true", help="Resume an existing JSON dataset.")
    output_mode.add_argument("--overwrite", action="store_true", help="Replace an existing JSON dataset.")
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be positive.")
    if args.max_steps <= 0:
        parser.error("--max-steps must be positive.")
    if args.max_circuits is not None and args.max_circuits <= 0:
        parser.error("--max-circuits must be positive.")
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive.")
    return args


def main() -> int:
    """Generate and checkpoint the end-to-end dataset."""
    args = parse_args()
    output_path = args.output or (
        PROJECT_ROOT / "output" / "llm_dataset" / f"mqt_pipeline_{args.metric}.json"
    )
    output_path = output_path.resolve()
    input_paths = collect_input_paths(args.input_dir, args.pattern, args.max_circuits)
    payload = load_or_initialize_payload(args, output_path)

    selector = DeviceSelector(args.metric)
    compiled_circuit_dirs = args.compiled_circuit_dirs or [
        PROJECT_ROOT / "mini-trainingset" / "compiled_circuit",
        get_ml_training_data_path() / "training_circuits_compiled",
    ]
    offline_ground_truth = load_offline_ground_truth(
        args.metric,
        selector,
        args.aggregated_data_dir,
        compiled_circuit_dirs,
    )
    existing_record_ids = {record["record_id"] for record in payload["records"]}
    model_cache: dict[str, Any] = {}

    print(f"Input circuits: {len(input_paths)}")
    print(f"Metric:         {args.metric}")
    print(f"Output:         {output_path}")
    print(f"Repetitions:    {args.repetitions}")

    for source_path in input_paths:
        source_bytes = source_path.read_bytes()
        source_sha256 = sha256_bytes(source_bytes)
        source_qasm = source_bytes.decode("utf-8")
        source_circuit = QuantumCircuit.from_qasm_file(str(source_path))
        feature_vector = source_feature_vector(source_circuit)

        for repetition in range(args.repetitions):
            seed = args.seed + repetition
            record_id = build_record_id(source_sha256, args.metric, repetition, seed)
            if record_id in existing_record_ids:
                print(f"SKIP {source_path.name} repetition={repetition}: already present")
                continue

            record_started = perf_counter()
            record: dict[str, Any] = {
                "record_id": record_id,
                "status": "running",
                "created_at": utc_now(),
                "repetition": repetition,
                "seed": seed,
                "source_circuit": {
                    "name": source_path.stem,
                    "path": path_for_json(source_path),
                    "format": "OpenQASM 2",
                    "sha256": source_sha256,
                    "qasm2": source_qasm,
                    "summary": circuit_summary(source_circuit),
                },
                "feature_vector": feature_vector,
                "figure_of_merit": METRIC_METADATA[args.metric],
                "device_selection": None,
                "compilation": None,
                "compiled_circuit": None,
                "error": None,
            }

            trace: list[dict[str, Any]] = []
            try:
                selected_target, selection = selector.select(
                    source_circuit,
                    feature_vector["ordered_values"],
                )
                offline = offline_ground_truth.get(
                    source_path.stem,
                    empty_offline_ground_truth(),
                )
                selection["offline_ground_truth"] = offline
                selection["prediction_matches_offline_label"] = (
                    selection["selected_device"] == offline["best_device_label"]
                    if offline["available"]
                    else None
                )
                record["device_selection"] = selection

                for candidate in selection["ranking"]:
                    candidate_name = candidate["device"]
                    if candidate_name not in payload["hardware_catalog"]:
                        payload["hardware_catalog"][candidate_name] = serialize_target(
                            get_device(candidate_name)
                        )

                model_key = f"{args.metric}:{selected_target.description}"
                if model_key not in model_cache:
                    model_cache[model_key] = load_model(
                        f"model_{args.metric}_{selected_target.description}"
                    )
                rl_model = model_cache[model_key]
                rl_model_path = (
                    get_rl_model_dir()
                    / f"model_{args.metric}_{selected_target.description}.zip"
                )

                compilation_started = perf_counter()
                compiled_circuit, terminal_reward = run_with_timeout(
                    lambda: traced_rl_compile(
                        source_circuit,
                        selected_target,
                        args.metric,
                        rl_model,
                        deterministic=args.deterministic,
                        seed=seed,
                        max_steps=args.max_steps,
                        include_intermediate_qasm=args.include_intermediate_qasm,
                        trace=trace,
                    ),
                    args.timeout,
                )
                compilation_elapsed = perf_counter() - compilation_started
                compiled_qasm = qasm2_dumps(compiled_circuit)
                final_score = evaluate_metric(compiled_circuit, selected_target, args.metric)

                record["compilation"] = {
                    "method": "MQT Predictor device-specific MaskablePPO policy",
                    "policy_model": file_metadata(rl_model_path),
                    "policy_inference": {
                        "deterministic": args.deterministic,
                        "seed": seed,
                        "timeout_seconds": args.timeout,
                        "maximum_actions": args.max_steps,
                    },
                    "action_catalog": [
                        action_metadata(index, action)
                        for index, action in PredictorEnv(
                            reward_function=args.metric,
                            device=selected_target,
                        ).action_set.items()
                    ],
                    "selected_pass_names": [
                        step["selected_action"]["name"] for step in trace
                    ],
                    "step_count": len(trace),
                    "steps": trace,
                    "terminal_reward_returned_by_environment": finite_float(terminal_reward),
                    "final_score_recomputed": finite_float(final_score),
                    "elapsed_seconds": compilation_elapsed,
                }
                record["compiled_circuit"] = {
                    "format": "OpenQASM 2",
                    "sha256": sha256_bytes(compiled_qasm.encode("utf-8")),
                    "qasm2": compiled_qasm,
                    "summary": circuit_summary(compiled_circuit),
                    "figure_of_merit_score": finite_float(final_score),
                    "validation": validate_compiled_circuit(
                        compiled_circuit,
                        selected_target,
                    ),
                }
                record["status"] = "success"

            except CompilationTimeoutError as error:
                record["status"] = "timeout"
                record["compilation"] = {
                    "method": "MQT Predictor device-specific MaskablePPO policy",
                    "step_count_before_timeout": len(trace),
                    "steps_before_timeout": trace,
                    "timeout_seconds": args.timeout,
                }
                record["error"] = {
                    "stage": "rl_compilation",
                    "type": type(error).__name__,
                    "message": str(error),
                }
            except Exception as error:  # noqa: BLE001 - failures are dataset evidence
                record["status"] = "error"
                if trace and record["compilation"] is None:
                    record["compilation"] = {
                        "method": "MQT Predictor device-specific MaskablePPO policy",
                        "step_count_before_error": len(trace),
                        "steps_before_error": trace,
                    }
                record["error"] = {
                    "stage": (
                        "rl_compilation"
                        if record["device_selection"] is not None
                        else "device_selection"
                    ),
                    "type": type(error).__name__,
                    "message": str(error),
                }

            record["total_elapsed_seconds"] = perf_counter() - record_started
            payload["records"].append(record)
            existing_record_ids.add(record_id)
            write_payload_atomic(payload, output_path)
            print(
                f"{record['status'].upper():7} {source_path.name} "
                f"repetition={repetition} elapsed={record['total_elapsed_seconds']:.2f}s"
            )

    print(
        "Completed: "
        f"records={payload['dataset']['record_count']} "
        f"success={payload['dataset']['successful_records']} "
        f"errors={payload['dataset']['failed_records']} "
        f"timeouts={payload['dataset']['timeout_records']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

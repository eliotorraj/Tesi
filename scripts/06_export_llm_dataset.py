"""Export strict full-pipeline MQT examples for an LLM.

An example is eligible only when every width-compatible backend was compiled
successfully by its MQT RL policy. Fallback and legacy artifacts are excluded.
The output separates prompt input, supervised output, and deterministic ground
truth to prevent score/QASM leakage into the model input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import zipfile
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version as package_version
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

os.environ.setdefault("GITHUB_ACTIONS", "true")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")

from mqt.bench.targets import get_device
from mqt.predictor.ml.helper import get_path_training_circuits
from mqt.predictor.reward import crit_depth, expected_fidelity
from mqt.predictor.rl.predictorenv import PredictorEnv
from qiskit import QuantumCircuit
from qiskit.transpiler.passes import CheckMap, GatesInBasis


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "datasets" / "device_selector_expected_fidelity.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "datasets" / "llm_mqt_full_pipeline_expected_fidelity.json"
SCHEMA_VERSION = "1.0.0"

METRIC_METADATA = {
    "expected_fidelity": {
        "name": "expected_fidelity",
        "direction": "maximize",
        "implementation": "mqt.predictor.reward.expected_fidelity",
        "interpretation": (
            "Estimated product of instruction and readout fidelities from the "
            "Qiskit Target; it is not a measurement from quantum hardware."
        ),
    },
    "critical_depth": {
        "name": "critical_depth",
        "direction": "maximize",
        "implementation": "mqt.predictor.reward.crit_depth",
        "interpretation": "MQT reward 1 - critical_depth; higher is better.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-circuits", type=Path)
    parser.add_argument(
        "--balance", choices=("none", "cap-ratio", "undersample"), default="cap-ratio"
    )
    parser.add_argument("--max-label-ratio", type=float, default=3.0)
    parser.add_argument("--minimum-per-device", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.max_label_ratio < 1:
        parser.error("--max-label-ratio deve essere almeno 1.")
    if args.minimum_per_device < 0:
        parser.error("--minimum-per-device non può essere negativo.")
    if args.max_records is not None and args.max_records <= 0:
        parser.error("--max-records deve essere positivo.")
    return args


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def atomic_json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def ensure_source_circuits(path: Path) -> None:
    if any(path.glob("*.qasm")):
        return
    archive = path / "training_data_device_selection.zip"
    if not archive.is_file():
        raise SystemExit(f"Nessun QASM sorgente o archivio trovato in {path}.")
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(path)


def coupling_edges(target: Any) -> list[list[int]]:
    coupling_map = target.build_coupling_map()
    if coupling_map is None:
        return []
    edges: Iterable[tuple[int, int]] = (
        coupling_map.get_edges() if hasattr(coupling_map, "get_edges") else coupling_map
    )
    return sorted([[int(source), int(destination)] for source, destination in edges])


def summarize_numbers(values: Iterable[Any]) -> dict[str, float | int | None]:
    finite = [value for raw in values if (value := finite_float(raw)) is not None]
    if not finite:
        return {"count": 0, "min": None, "mean": None, "max": None}
    return {"count": len(finite), "min": min(finite), "mean": fmean(finite), "max": max(finite)}


def action_catalog(target: Any, metric: str) -> list[dict[str, Any]]:
    environment = PredictorEnv(reward_function=metric, device=target)
    return [
        {
            "index": int(index),
            "name": str(action.name),
            "origin": str(action.origin.value),
            "pass_type": str(action.pass_type.value),
        }
        for index, action in environment.action_set.items()
    ]


def serialize_target(target: Any, metric: str) -> dict[str, Any]:
    instructions: list[dict[str, Any]] = []
    errors_by_operation: dict[str, list[float]] = {}
    durations_by_operation: dict[str, list[float]] = {}
    for operation, qargs in target.instructions:
        properties = None
        try:
            properties = target[operation.name].get(qargs)
        except (AttributeError, KeyError, TypeError):
            pass
        error = finite_float(getattr(properties, "error", None))
        duration = finite_float(getattr(properties, "duration", None))
        if error is not None:
            errors_by_operation.setdefault(str(operation.name), []).append(error)
        if duration is not None:
            durations_by_operation.setdefault(str(operation.name), []).append(duration)
        instructions.append(
            {
                "name": str(operation.name),
                "num_qubits": int(operation.num_qubits),
                "qubits": None if qargs is None else [int(qubit) for qubit in qargs],
                "error": error,
                "duration_seconds": duration,
            }
        )
    qubit_properties = [
        {
            "qubit": index,
            "t1_seconds": finite_float(getattr(properties, "t1", None)),
            "t2_seconds": finite_float(getattr(properties, "t2", None)),
            "frequency_hz": finite_float(getattr(properties, "frequency", None)),
        }
        for index, properties in enumerate(target.qubit_properties or [])
    ]
    edges = coupling_edges(target)
    return {
        "id": str(target.description),
        "type": f"{type(target).__module__}.{type(target).__qualname__}",
        "num_qubits": int(target.num_qubits),
        "operation_names": sorted(str(name) for name in target.operation_names),
        "coupling_map": {
            "directed_edges": edges,
            "edge_count": len(edges),
            "all_to_all": target.build_coupling_map() is None,
        },
        "dt_seconds": finite_float(getattr(target, "dt", None)),
        "qubit_properties": qubit_properties,
        "instructions": instructions,
        "instruction_error_summary": {
            name: summarize_numbers(values) for name, values in sorted(errors_by_operation.items())
        },
        "instruction_duration_summary": {
            name: summarize_numbers(values)
            for name, values in sorted(durations_by_operation.items())
        },
        "allowed_compilation_actions": action_catalog(target, metric),
        "provenance": "Qiskit Target returned by mqt.bench.targets.get_device",
    }


def circuit_summary(circuit: QuantumCircuit) -> dict[str, Any]:
    return {
        "num_qubits": int(circuit.num_qubits),
        "num_clbits": int(circuit.num_clbits),
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "operation_counts": {
            str(name): int(count) for name, count in sorted(circuit.count_ops().items())
        },
        "num_parameters": len(circuit.parameters),
    }


def validate_compiled_circuit(circuit: QuantumCircuit, target: Any) -> dict[str, Any]:
    """Validate basis and connectivity with deterministic Qiskit passes."""
    errors: list[str] = []
    unsupported = sorted(
        set(map(str, circuit.count_ops())) - set(map(str, target.operation_names)) - {"barrier"}
    )
    basis_valid: bool | None = None
    connectivity_valid: bool | None = None
    try:
        checker = GatesInBasis(target=target)
        checker(circuit)
        basis_valid = bool(checker.property_set["all_gates_in_basis"])
    except Exception as error:
        errors.append(f"GatesInBasis: {type(error).__name__}: {error}")
    try:
        coupling_map = target.build_coupling_map()
        if coupling_map is None:
            connectivity_valid = True
        else:
            checker = CheckMap(coupling_map=coupling_map)
            checker(circuit)
            connectivity_valid = bool(checker.property_set["is_swap_mapped"])
    except Exception as error:
        errors.append(f"CheckMap: {type(error).__name__}: {error}")
    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "unsupported_operations": unsupported,
        "is_executable_on_target": bool(basis_valid and connectivity_valid and not unsupported),
        "validation_errors": errors,
    }


def evaluate_metric(circuit: QuantumCircuit, target: Any, metric: str) -> float:
    if metric == "expected_fidelity":
        return float(expected_fidelity(circuit, target))
    if metric == "critical_depth":
        return float(crit_depth(circuit))
    raise ValueError(f"Metrica non supportata: {metric}")


def pure_rl_problem(compilation: Any) -> str | None:
    """Explain why an artifact is not a successful full MQT RL trace."""
    if not isinstance(compilation, dict):
        return "missing_compilation"
    if compilation.get("mode") != "rl":
        return f"mode_{compilation.get('mode', 'missing')}"
    if compilation.get("status") != "success":
        return f"status_{compilation.get('status', 'missing')}"
    passes = compilation.get("passes")
    if not isinstance(passes, list) or not passes:
        return "empty_pass_trace"
    if any(str(value).startswith("fallback:") for value in passes):
        return "fallback_pass_in_trace"
    if passes[-1] != "terminate":
        return "trace_without_terminal_action"
    return None


def compact_backend_profile(hardware: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": hardware["id"],
        "num_qubits": hardware["num_qubits"],
        "operation_names": hardware["operation_names"],
        "coupling_map": hardware["coupling_map"],
        "instruction_error_summary": hardware["instruction_error_summary"],
        "instruction_duration_summary": hardware["instruction_duration_summary"],
        "allowed_compilation_actions": hardware["allowed_compilation_actions"],
        "hardware_catalog_reference": f"/hardware_catalog/{hardware['id']}",
    }


def build_candidate(device_name: str, compilation: dict[str, Any], stored_score: float, target: Any, metric: str) -> dict[str, Any]:
    """Load and deterministically verify one cached RL result."""
    compiled_path = Path(str(compilation["qasm"]))
    if not compiled_path.is_absolute():
        compiled_path = PROJECT_ROOT / compiled_path
    if not compiled_path.is_file():
        raise ValueError(f"compiled_qasm_missing:{device_name}")
    qasm = compiled_path.read_text(encoding="utf-8")
    try:
        circuit = QuantumCircuit.from_qasm_str(qasm)
    except Exception as error:
        raise ValueError(f"compiled_qasm_invalid:{device_name}:{error}") from error
    validation = validate_compiled_circuit(circuit, target)
    if not validation["is_executable_on_target"]:
        raise ValueError(f"compiled_circuit_not_target_valid:{device_name}")
    recomputed_score = evaluate_metric(circuit, target, metric)
    if not math.isclose(recomputed_score, stored_score, rel_tol=1e-8, abs_tol=1e-10):
        raise ValueError(f"score_mismatch:{device_name}")
    return {
        "device": device_name,
        "figure_of_merit_score": recomputed_score,
        "compilation": {
            "compiler": "mqt_predictor_rl",
            "policy_scope": f"{device_name} x {metric}",
            "passes": list(map(str, compilation["passes"])),
            "step_count": len(compilation["passes"]),
            "provenance": "rl",
        },
        "compiled_circuit": {
            "format": "OpenQASM 2",
            "sha256": sha256_text(qasm),
            "qasm2": qasm,
            "summary": circuit_summary(circuit),
            "validation": validation,
        },
    }


def build_record(source_record: dict[str, Any], source_dir: Path, hardware_catalog: dict[str, Any], targets: dict[str, Any], feature_names: list[str], metric: str) -> dict[str, Any]:
    """Create one leakage-separated LLM example."""
    circuit_name = str(source_record["circuit"])
    source_path = source_dir / str(source_record["source_qasm"])
    if not source_path.is_file():
        raise ValueError("source_qasm_missing")
    source_qasm = source_path.read_text(encoding="utf-8")
    try:
        source_circuit = QuantumCircuit.from_qasm_str(source_qasm)
    except Exception as error:
        raise ValueError(f"source_qasm_invalid:{error}") from error
    features = source_record.get("features")
    if not isinstance(features, dict) or set(features) != set(feature_names):
        raise ValueError("feature_schema_mismatch")
    feature_values = [finite_float(features[name]) for name in feature_names]
    if any(value is None for value in feature_values):
        raise ValueError("non_finite_feature")
    if int(float(features["num_qubits"])) != source_circuit.num_qubits:
        raise ValueError("feature_qasm_width_mismatch")

    raw_scores = source_record.get("scores") or {}
    compatible_devices = [name for name in hardware_catalog if raw_scores.get(name) is not None]
    if not compatible_devices:
        raise ValueError("no_compatible_device")
    outcomes: list[dict[str, Any]] = []
    compilations = source_record.get("compiled_circuits") or {}
    for device_name in compatible_devices:
        problem = pure_rl_problem(compilations.get(device_name))
        if problem:
            raise ValueError(f"{device_name}:{problem}")
        outcomes.append(build_candidate(device_name, compilations[device_name], float(raw_scores[device_name]), targets[device_name], metric))
    ranking = sorted(outcomes, key=lambda item: (-item["figure_of_merit_score"], item["device"]))
    selected = ranking[0]
    if source_record.get("label_device") != selected["device"]:
        raise ValueError("label_argmax_mismatch")
    ranked_rows = [
        {"rank": index, "device": row["device"], "figure_of_merit_score": row["figure_of_merit_score"]}
        for index, row in enumerate(ranking, start=1)
    ]
    second_score = ranking[1]["figure_of_merit_score"] if len(ranking) > 1 else None
    margin = selected["figure_of_merit_score"] - second_score if second_score is not None else None
    record_id = sha256_text(f"{metric}:{circuit_name}:{sha256_text(source_qasm)}")[:24]
    return {
        "record_id": record_id,
        "input": {
            "objective": METRIC_METADATA[metric],
            "user_constraints": {},
            "circuit": {
                "name": circuit_name, "format": "OpenQASM 2", "sha256": sha256_text(source_qasm),
                "qasm2": source_qasm, "summary": circuit_summary(source_circuit),
                "features": {
                    "extractor": (
                        f"MQT Predictor {package_version('mqt.predictor')} "
                        "device-selector feature vector"
                    ),
                    "feature_count": len(feature_names), "ordered_names": feature_names,
                    "ordered_values": feature_values, "by_name": {name: features[name] for name in feature_names},
                },
            },
            "compatible_backends": [compact_backend_profile(hardware_catalog[name]) for name in compatible_devices],
            "response_contract": {
                "selected_device": "one compatible_backends[].id", "compiler": "mqt_predictor_rl",
                "compilation_passes": "ordered names from the selected backend allowlist",
                "reasons": "structured claim/evidence pairs", "warnings": "limitations relevant to the recommendation",
            },
        },
        "expected_output": {
            "selected_device": selected["device"], "compiler": "mqt_predictor_rl",
            "compilation_passes": selected["compilation"]["passes"],
            "reasons": [
                {"claim": "The selected backend supports the circuit width.", "evidence": ["input.circuit.summary.num_qubits", f"input.compatible_backends[id={selected['device']}].num_qubits"]},
                {"claim": f"The selected backend maximized offline {metric} among candidates.", "evidence": ["deterministic_ground_truth.device_ranking", "deterministic_ground_truth.selection_margin"]},
                {"claim": "The pass sequence was produced by the selected RL policy.", "evidence": [f"deterministic_ground_truth.candidate_outcomes[device={selected['device']}].compilation"]},
            ],
            "warnings": [METRIC_METADATA[metric]["interpretation"]],
        },
        "deterministic_ground_truth": {
            "selection_rule": f"argmax({metric}) over width-compatible backends",
            "device_ranking": ranked_rows, "selection_margin": margin, "candidate_outcomes": outcomes,
            "all_candidates_used_full_mqt_rl_pipeline": True, "fallback_examples_included": False,
        },
    }


def stable_key(record: dict[str, Any], seed: int) -> str:
    return sha256_text(f"{seed}:{record['record_id']}")


def balance_records(records: list[dict[str, Any]], strategy: str, ratio: float, seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Cap winner classes without synthetic oversampling."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(record["expected_output"]["selected_device"], []).append(record)
    before = {name: len(values) for name, values in sorted(groups.items())}
    if not groups or strategy == "none":
        return records, {"strategy": strategy, "before": before, "after": before}
    smallest = min(map(len, groups.values()))
    limit = smallest if strategy == "undersample" else max(1, math.floor(smallest * ratio))
    selected_ids = {record["record_id"] for values in groups.values() for record in sorted(values, key=lambda item: stable_key(item, seed))[:limit]}
    selected = [record for record in records if record["record_id"] in selected_ids]
    after = Counter(record["expected_output"]["selected_device"] for record in selected)
    return selected, {
        "strategy": strategy, "max_label_ratio": ratio if strategy == "cap-ratio" else None,
        "seed": seed, "before": before, "after": dict(sorted(after.items())),
        "discarded_for_balance": len(records) - len(selected),
    }


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Dataset device selector non trovato: {args.input}")
    if args.output.exists() and not args.overwrite and not args.audit_only:
        raise SystemExit(f"Output già esistente: {args.output}. Usa --overwrite.")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    metric = str(payload.get("metric"))
    if metric not in METRIC_METADATA:
        raise SystemExit(f"Metrica non supportata: {metric}")
    feature_names = list(map(str, payload.get("feature_names", [])))
    if len(feature_names) != 49 or len(set(feature_names)) != 49:
        raise SystemExit("Il dataset sorgente non dichiara 49 feature univoche.")
    device_names = list(map(str, payload.get("devices", [])))
    if not device_names:
        raise SystemExit("Il dataset sorgente non dichiara device.")
    source_dir = args.source_circuits or get_path_training_circuits()
    ensure_source_circuits(source_dir)
    targets = {name: get_device(name) for name in device_names}
    hardware_catalog = {name: serialize_target(targets[name], metric) for name in device_names}

    eligible: list[dict[str, Any]] = []
    rejection_reasons: Counter[str] = Counter()
    rejection_examples: dict[str, list[str]] = {}
    for source_record in payload.get("records", []):
        name = str(source_record.get("circuit", "<missing>"))
        try:
            eligible.append(build_record(source_record, source_dir, hardware_catalog, targets, feature_names, metric))
        except (KeyError, TypeError, ValueError) as error:
            reason = str(error)
            rejection_reasons[reason] += 1
            if len(rejection_examples.setdefault(reason, [])) < 5:
                rejection_examples[reason].append(name)
    distribution = Counter(record["expected_output"]["selected_device"] for record in eligible)
    print(f"Circuiti sorgente: {len(payload.get('records', []))}")
    print(f"Circuiti strict full-pipeline RL: {len(eligible)}")
    print("Distribuzione strict: " + ", ".join(f"{k}={v}" for k, v in sorted(distribution.items())))
    print("Scarti: " + ", ".join(f"{k}={v}" for k, v in rejection_reasons.most_common()))
    insufficient = {name: distribution.get(name, 0) for name in device_names if distribution.get(name, 0) < args.minimum_per_device}
    if insufficient:
        raise SystemExit("Copertura hardware insufficiente: " + ", ".join(f"{k}={v}" for k, v in insufficient.items()))
    if args.audit_only:
        return 0

    balanced, balance_report = balance_records(eligible, args.balance, args.max_label_ratio, args.seed)
    if args.max_records is not None and len(balanced) > args.max_records:
        ids = {record["record_id"] for record in sorted(balanced, key=lambda item: stable_key(item, args.seed))[:args.max_records]}
        balanced = [record for record in balanced if record["record_id"] in ids]
    final_distribution = Counter(record["expected_output"]["selected_device"] for record in balanced)
    output = {
        "schema_version": SCHEMA_VERSION, "generated_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "name": "mqt_predictor_llm_full_pipeline", "source": str(args.input),
            "source_sample_count": len(payload.get("records", [])), "strict_eligible_count": len(eligible),
            "exported_record_count": len(balanced),
            "eligibility_rule": "All compatible backends must have successful RL traces ending in terminate, target-valid QASM, and reproducible scores.",
            "balance": balance_report, "label_distribution": dict(sorted(final_distribution.items())),
            "rejection_counts": dict(rejection_reasons), "rejection_examples": rejection_examples,
            "important_usage_rule": "Only record.input is prompt input; expected_output is the target and deterministic_ground_truth is evaluation-only.",
        },
        "feature_schema": {"feature_count": 49, "ordered_names": feature_names},
        "figure_of_merit": METRIC_METADATA[metric], "hardware_catalog": hardware_catalog,
        "records": balanced,
    }
    atomic_json_write(args.output, output)
    print(f"Dataset LLM scritto: {args.output} ({len(balanced)} record)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

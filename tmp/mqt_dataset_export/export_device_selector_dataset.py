from __future__ import annotations

import json
import os
from argparse import ArgumentParser, Namespace
from collections import Counter
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mqt-predictor-matplotlib")

from qiskit import QuantumCircuit

from mqt.predictor.ml.helper import get_openqasm_gates


DEFAULT_METRIC = "expected_fidelity"
DEFAULT_BASE = Path(".venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_data_aggregated")
DEFAULT_QASM_CANDIDATES = [
    Path("mini-trainingset/uncompiled_circuit"),
    Path(".venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_circuits"),
]
DEFAULT_COMPILED_QASM_CANDIDATES = [
    Path("mini-trainingset/compiled_circuit"),
    Path("compiled_circuit"),
    Path(".venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_circuits_compiled"),
]
DEFAULT_OUTPUT_DIR = Path("tmp/mqt_dataset_export")


def as_float_list(values: object) -> list[float]:
    return [float(v) for v in list(values)]


def find_qasm(name: str, qasm_candidates: list[Path]) -> Path | None:
    for directory in qasm_candidates:
        path = directory / f"{name}.qasm"
        if path.exists():
            return path
    return None


def find_compiled_qasm(name: str, metric: str, compiled_qasm_candidates: list[Path]) -> dict[str, str]:
    compiled_paths: dict[str, str] = {}
    pattern = f"{name}_{metric}-*.qasm"
    for directory in compiled_qasm_candidates:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(pattern)):
            device = path.stem.rsplit("-", maxsplit=1)[-1]
            compiled_paths.setdefault(device, str(path))
    return compiled_paths


def metric_files_exist(base: Path, metric: str) -> bool:
    return all(
        (base / f"{prefix}_{metric}.npy").exists()
        for prefix in ("training_data", "names_list", "scores_list")
    )


def load_metric_arrays(base: Path, metric: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    training_data = np.load(base / f"training_data_{metric}.npy", allow_pickle=True)
    names = np.load(base / f"names_list_{metric}.npy", allow_pickle=True)
    scores = np.load(base / f"scores_list_{metric}.npy", allow_pickle=True)

    lengths = (len(training_data), len(names), len(scores))
    if len(set(lengths)) != 1:
        raise ValueError(
            f"Metric '{metric}' has inconsistent array lengths: "
            f"training_data={lengths[0]}, names={lengths[1]}, scores={lengths[2]}"
        )
    return training_data, names, scores


def metric_sample_count(base: Path, metric: str) -> int:
    training_data, names, scores = load_metric_arrays(base, metric)
    if len(training_data) == 0:
        return 0
    if len(names) == 0 or len(scores) == 0:
        return 0
    return len(training_data)


def available_metrics(base: Path) -> list[str]:
    metrics = []
    for path in sorted(base.glob("training_data_*.npy")):
        metric = path.stem.removeprefix("training_data_")
        if not metric_files_exist(base, metric):
            continue
        try:
            sample_count = metric_sample_count(base, metric)
        except ValueError as exc:
            print(f"Skipping metric '{metric}': {exc}")
            continue
        if sample_count == 0:
            print(f"Skipping metric '{metric}': dataset is empty.")
            continue
        if sample_count > 0:
            metrics.append(metric)
    return metrics


def make_score_columns(rows: list[dict[str, object]]) -> list[str]:
    max_score_count = max((len(row["score_values"]) for row in rows), default=0)
    compiled_devices = sorted(
        {
            str(device)
            for row in rows
            for device in (row.get("compiled_qasm_paths") or {})
        }
    )
    if len(compiled_devices) == max_score_count:
        return [f"score_{device}" for device in compiled_devices]
    if max_score_count <= 1:
        return ["score"]
    return [f"score_{idx}" for idx in range(max_score_count)]


def export_metric(
    metric: str,
    base: Path,
    output_dir: Path,
    qasm_candidates: list[Path],
    compiled_qasm_candidates: list[Path],
) -> Path:
    training_data, names, scores = load_metric_arrays(base, metric)
    if len(training_data) == 0:
        raise ValueError(f"Metric '{metric}' has no samples in {base}")

    feature_names = (
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

    x_list, y_list = zip(*training_data, strict=False)
    rows = []
    for idx, (name, x, y, score_list) in enumerate(zip(names, x_list, y_list, scores, strict=False)):
        feature_values = as_float_list(x)
        row = {
            "index": idx,
            "name": str(name),
            "label_device": str(y),
            "score_values": as_float_list(score_list),
            "feature_values": feature_values,
            "features": dict(zip(feature_names, feature_values, strict=False)),
            "qasm_found": False,
            "qasm_path": "",
            "source_num_qubits": None,
            "source_depth": None,
            "source_operations": {},
        }

        qasm_path = find_qasm(str(name), qasm_candidates)
        if qasm_path is not None:
            qc = QuantumCircuit.from_qasm_file(str(qasm_path))
            row["qasm_found"] = True
            row["qasm_path"] = str(qasm_path)
            row["source_num_qubits"] = int(qc.num_qubits)
            row["source_depth"] = int(qc.depth())
            row["source_operations"] = {str(k): int(v) for k, v in dict(qc.count_ops()).items()}

        compiled_qasm_paths = find_compiled_qasm(str(name), metric, compiled_qasm_candidates)
        row["compiled_qasm_count"] = len(compiled_qasm_paths)
        row["compiled_qasm_devices"] = sorted(compiled_qasm_paths)
        row["compiled_qasm_paths"] = compiled_qasm_paths

        rows.append(row)

    payload = {
        "metric": metric,
        "sample_count": len(rows),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "label_distribution": dict(Counter(str(y) for y in y_list)),
        "score_columns": make_score_columns(rows),
        "notes": [
            "Each row is one source circuit.",
            "X is the feature vector extracted from the target-independent circuit.",
            "y is the best device label according to the selected figure of merit.",
            f"This export comes from the current local generated training_data_{metric}.npy files.",
            "Source and compiled QASM paths are resolved from the configured local candidate directories.",
        ],
        "rows": rows,
    }

    output_path = output_dir / f"device_selector_dataset_{metric}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(output_path)
    print(f"rows={len(rows)} features={len(feature_names)}")
    return output_path


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Export MQT Predictor device selector .npy data to JSON.")
    parser.add_argument("--metric", default=DEFAULT_METRIC, help="Figure of merit to export.")
    parser.add_argument(
        "--all-available",
        action="store_true",
        help="Export one JSON for every metric with matching training_data/names/scores .npy files.",
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Directory containing the aggregated .npy files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for generated JSON files.")
    parser.add_argument(
        "--qasm-candidate",
        action="append",
        type=Path,
        dest="qasm_candidates",
        help="Directory that may contain source QASM files. Can be passed multiple times.",
    )
    parser.add_argument(
        "--compiled-qasm-candidate",
        action="append",
        type=Path,
        dest="compiled_qasm_candidates",
        help="Directory that may contain compiled QASM files. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = available_metrics(args.base) if args.all_available else [args.metric]
    if not metrics:
        raise SystemExit(f"No complete metric datasets found in {args.base}")

    qasm_candidates = args.qasm_candidates or DEFAULT_QASM_CANDIDATES
    compiled_qasm_candidates = args.compiled_qasm_candidates or DEFAULT_COMPILED_QASM_CANDIDATES
    for metric in metrics:
        if not metric_files_exist(args.base, metric):
            raise SystemExit(f"Missing one or more .npy files for metric '{metric}' in {args.base}")
        try:
            export_metric(metric, args.base, args.output_dir, qasm_candidates, compiled_qasm_candidates)
        except ValueError as exc:
            if args.all_available:
                print(f"Skipping metric '{metric}': {exc}")
                continue
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

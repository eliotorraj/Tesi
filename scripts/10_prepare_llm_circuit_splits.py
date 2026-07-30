"""Select and copy a leakage-aware subset of MQT's bundled circuits.

The resulting split is designed for the first larger LLM-trace dataset:

* 56 training circuits;
* 12 validation circuits;
* 12 test circuits;
* all circuits are target-independent, parseable OpenQASM 2, and 2-30 qubits;
* related algorithm families are kept in one split;
* Qiskit- and TKET-generated sources and multiple width bands are represented.

The script also compares MQT Predictor's RL and ML circuit corpora, writes CSV
and JSON manifests, and validates hashes and split isolation after copying.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from mqt.predictor.utils import calc_supermarq_features
from qiskit import QuantumCircuit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREDICTOR_ROOT = (
    PROJECT_ROOT
    / ".venv"
    / "lib"
    / "python3.12"
    / "site-packages"
    / "mqt"
    / "predictor"
)
DEFAULT_RL_SOURCE = PREDICTOR_ROOT / "rl" / "training_data" / "training_circuits"
DEFAULT_ML_SOURCE = PREDICTOR_ROOT / "ml" / "training_data" / "training_circuits"
DEFAULT_DATASET_ROOT = PROJECT_ROOT / "datasets"

FILENAME_PATTERN = re.compile(
    r"^(?P<family>.+)_indep_(?P<generator>qiskit|tket)_(?P<qubits>\d+)\.qasm$"
)

# Related variants remain in one split to prevent algorithm-family leakage.
LEAKAGE_GROUPS = {
    "ae": "ae",
    "dj": "dj",
    "graphstate": "graphstate",
    "groundstate_medium": "groundstate",
    "groundstate_small": "groundstate",
    "portfolioqaoa": "portfolio",
    "portfoliovqe": "portfolio",
    "pricingcall": "pricing",
    "pricingput": "pricing",
    "qaoa": "qaoa",
    "qft": "qft",
    "qftentangled": "qft",
    "qnn": "qnn",
    "qpeexact": "qpe",
    "qpeinexact": "qpe",
    "random": "random_ansatz",
    "realamprandom": "random_ansatz",
    "routing": "routing",
    "su2random": "random_ansatz",
    "tsp": "tsp",
    "twolocalrandom": "random_ansatz",
    "vqe": "vqe",
    "wstate": "wstate",
}

# Exact 70/15/15 allocation over 80 selected source circuits.
SPLIT_FAMILY_QUOTAS: dict[str, dict[str, int]] = {
    "train": {
        "graphstate": 8,
        "ae": 4,
        "groundstate_small": 2,
        "groundstate_medium": 2,
        "portfolioqaoa": 3,
        "portfoliovqe": 3,
        "pricingcall": 3,
        "pricingput": 3,
        "qaoa": 5,
        "qnn": 3,
        "random": 3,
        "realamprandom": 3,
        "routing": 3,
        "su2random": 3,
        "twolocalrandom": 3,
        "vqe": 5,
    },
    "validation": {
        "dj": 6,
        "qft": 3,
        "qftentangled": 3,
    },
    "test": {
        "wstate": 5,
        "qpeexact": 2,
        "qpeinexact": 2,
        "tsp": 3,
    },
}

SPLIT_TARGET_DIRS = {
    "train": Path("llm_train") / "uncompiled",
    "validation": Path("llm_validation") / "uncompiled",
    "test": Path("llm_test") / "uncompiled",
}


@dataclass(frozen=True)
class CircuitMetadata:
    """Metadata used for selection and written to the manifest."""

    filename: str
    family: str
    leakage_group: str
    generator: str
    filename_qubits: int
    num_qubits: int
    num_clbits: int
    depth: int
    size: int
    gate_count: int
    size_band: str
    program_communication: float
    critical_depth: float
    entanglement_ratio: float
    parallelism: float
    liveness: float
    sha256: str
    source_path: str


def utc_now() -> str:
    """Return a UTC timestamp."""
    return datetime.now(UTC).isoformat()


def path_for_manifest(path: Path) -> str:
    """Prefer project-relative paths in portable manifests."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def sha256_file(path: Path) -> str:
    """Return a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def size_band(num_qubits: int) -> str:
    """Map the RL training range to three declared width bands."""
    if num_qubits <= 7:
        return "small_2_7"
    if num_qubits <= 15:
        return "medium_8_15"
    return "large_16_30"


def inspect_circuit(path: Path) -> CircuitMetadata:
    """Parse and characterize one MQT target-independent circuit."""
    match = FILENAME_PATTERN.match(path.name)
    if match is None:
        raise ValueError(f"Unexpected MQT circuit filename: {path.name}")

    circuit = QuantumCircuit.from_qasm_file(str(path))
    filename_qubits = int(match.group("qubits"))
    if circuit.num_qubits != filename_qubits:
        raise ValueError(
            f"Qubit mismatch for {path.name}: filename={filename_qubits}, circuit={circuit.num_qubits}"
        )
    if not 2 <= circuit.num_qubits <= 30:
        raise ValueError(f"RL source circuit outside the expected 2-30 range: {path.name}")

    family = match.group("family")
    if family not in LEAKAGE_GROUPS:
        raise ValueError(f"Missing leakage-group mapping for family: {family}")

    features = calc_supermarq_features(circuit)
    return CircuitMetadata(
        filename=path.name,
        family=family,
        leakage_group=LEAKAGE_GROUPS[family],
        generator=match.group("generator"),
        filename_qubits=filename_qubits,
        num_qubits=int(circuit.num_qubits),
        num_clbits=int(circuit.num_clbits),
        depth=int(circuit.depth()),
        size=int(circuit.size()),
        gate_count=int(sum(circuit.count_ops().values())),
        size_band=size_band(int(circuit.num_qubits)),
        program_communication=float(features.program_communication),
        critical_depth=float(features.critical_depth),
        entanglement_ratio=float(features.entanglement_ratio),
        parallelism=float(features.parallelism),
        liveness=float(features.liveness),
        sha256=sha256_file(path),
        source_path=path_for_manifest(path),
    )


def stable_generator_offset(family: str) -> int:
    """Alternate starting generator deterministically across families."""
    return sum(family.encode("utf-8")) % 2


def select_family_representatives(
    candidates: list[CircuitMetadata],
    quota: int,
) -> list[tuple[CircuitMetadata, dict[str, Any]]]:
    """Select circuits spread across width while alternating source generators."""
    if quota > len(candidates):
        raise ValueError(
            f"Quota {quota} exceeds {len(candidates)} candidates for family {candidates[0].family}."
        )

    candidates = sorted(
        candidates,
        key=lambda item: (item.num_qubits, item.generator, item.depth, item.filename),
    )
    minimum = min(item.num_qubits for item in candidates)
    maximum = max(item.num_qubits for item in candidates)
    selected: list[tuple[CircuitMetadata, dict[str, Any]]] = []
    used_filenames: set[str] = set()
    used_qubits: Counter[int] = Counter()
    used_bands: Counter[str] = Counter()
    generator_offset = stable_generator_offset(candidates[0].family)

    for slot in range(quota):
        quantile = 0.5 if quota == 1 else slot / (quota - 1)
        target_qubits = minimum + quantile * (maximum - minimum)
        preferred_generator = ("qiskit", "tket")[(slot + generator_offset) % 2]

        def selection_key(item: CircuitMetadata) -> tuple[float, float, int, int, str]:
            width_range = max(maximum - minimum, 1)
            width_distance = abs(item.num_qubits - target_qubits) / width_range
            generator_penalty = 0.16 if item.generator != preferred_generator else 0.0
            repeated_band_penalty = 0.08 * used_bands[item.size_band]
            repeated_width_penalty = 0.04 * used_qubits[item.num_qubits]
            score = (
                width_distance
                + generator_penalty
                + repeated_band_penalty
                + repeated_width_penalty
            )
            return (
                score,
                abs(item.depth),
                item.num_qubits,
                0 if item.generator == "qiskit" else 1,
                item.filename,
            )

        available = [item for item in candidates if item.filename not in used_filenames]
        chosen = min(available, key=selection_key)
        used_filenames.add(chosen.filename)
        used_qubits[chosen.num_qubits] += 1
        used_bands[chosen.size_band] += 1
        selected.append((
            chosen,
            {
                "selection_rank_within_family": slot,
                "target_qubits": round(target_qubits, 4),
                "preferred_generator": preferred_generator,
                "selection_rule": (
                    "nearest width quantile with penalties for repeated width/band "
                    "and for not alternating Qiskit/TKET source generation"
                ),
            },
        ))
    return selected


def compare_rl_and_ml_corpora(rl_source: Path, ml_source: Path) -> dict[str, Any]:
    """Confirm corpus overlap and characterize the ML-only extension."""
    rl_paths = {path.name: path for path in rl_source.glob("*.qasm")}
    ml_paths = {path.name: path for path in ml_source.glob("*.qasm")}
    shared_names = sorted(set(rl_paths) & set(ml_paths))
    mismatched_hashes = [
        name
        for name in shared_names
        if sha256_file(rl_paths[name]) != sha256_file(ml_paths[name])
    ]
    if mismatched_hashes:
        raise ValueError(
            f"RL/ML corpus files share names but not contents: {mismatched_hashes[:5]}"
        )

    ml_only = sorted(set(ml_paths) - set(rl_paths))
    ml_only_qubits = []
    for name in ml_only:
        match = FILENAME_PATTERN.match(name)
        if match is None:
            raise ValueError(f"Unexpected ML-only filename: {name}")
        ml_only_qubits.append(int(match.group("qubits")))

    return {
        "rl_qasm_count": len(rl_paths),
        "ml_qasm_count": len(ml_paths),
        "shared_filename_and_hash_count": len(shared_names),
        "rl_only_count": len(set(rl_paths) - set(ml_paths)),
        "ml_only_count": len(ml_only),
        "ml_only_min_qubits": min(ml_only_qubits) if ml_only_qubits else None,
        "ml_only_max_qubits": max(ml_only_qubits) if ml_only_qubits else None,
        "selection_source": "RL corpus",
        "selection_rationale": (
            "The 500 RL circuits are the in-distribution 2-30-qubit corpus used "
            "for device-specific policy training. The 100 ML-only circuits are "
            "larger (up to 90 qubits) and are reserved for a future OOD study."
        ),
    }


def split_group_assignment() -> dict[str, str]:
    """Return and validate a one-to-one leakage-group assignment."""
    assignments: dict[str, str] = {}
    for split, family_quotas in SPLIT_FAMILY_QUOTAS.items():
        for family in family_quotas:
            group = LEAKAGE_GROUPS[family]
            existing = assignments.get(group)
            if existing is not None and existing != split:
                raise ValueError(
                    f"Leakage group '{group}' assigned to both {existing} and {split}."
                )
            assignments[group] = split
    return assignments


def target_directories(dataset_root: Path) -> dict[str, Path]:
    """Resolve declared split output directories."""
    return {
        split: dataset_root / relative_path
        for split, relative_path in SPLIT_TARGET_DIRS.items()
    }


def ensure_targets_are_ready(targets: dict[str, Path], overwrite: bool) -> None:
    """Create split directories and protect pre-existing QASM by default."""
    for target in targets.values():
        target.mkdir(parents=True, exist_ok=True)
        existing = sorted(target.glob("*.qasm"))
        if existing and not overwrite:
            raise FileExistsError(
                f"{target} already contains {len(existing)} QASM files. "
                "Use --overwrite only if replacing this generated split is intentional."
            )
        if overwrite:
            for path in existing:
                path.unlink()


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build machine-readable split statistics."""
    result: dict[str, Any] = {}
    for split in SPLIT_FAMILY_QUOTAS:
        split_rows = [row for row in rows if row["split"] == split]
        result[split] = {
            "circuit_count": len(split_rows),
            "family_count": len({row["family"] for row in split_rows}),
            "leakage_group_count": len({row["leakage_group"] for row in split_rows}),
            "generator_counts": dict(sorted(Counter(row["generator"] for row in split_rows).items())),
            "size_band_counts": dict(sorted(Counter(row["size_band"] for row in split_rows).items())),
            "min_qubits": min(row["num_qubits"] for row in split_rows),
            "max_qubits": max(row["num_qubits"] for row in split_rows),
            "families": dict(sorted(Counter(row["family"] for row in split_rows).items())),
        }
    return result


def write_csv_manifest(rows: list[dict[str, Any]], path: Path) -> None:
    """Write one flat row per selected source circuit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json_manifest(payload: dict[str, Any], path: Path) -> None:
    """Write the split provenance and summary document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


def validate_copied_splits(
    rows: list[dict[str, Any]],
    targets: dict[str, Path],
) -> dict[str, Any]:
    """Validate copied files, hashes, parsing, and split isolation."""
    expected_counts = {
        split: sum(family_quotas.values())
        for split, family_quotas in SPLIT_FAMILY_QUOTAS.items()
    }
    filenames_by_split: dict[str, set[str]] = defaultdict(set)
    hashes_by_split: dict[str, set[str]] = defaultdict(set)
    groups_by_split: dict[str, set[str]] = defaultdict(set)

    for split, target in targets.items():
        copied_paths = sorted(target.glob("*.qasm"))
        if len(copied_paths) != expected_counts[split]:
            raise ValueError(
                f"{split}: expected {expected_counts[split]} files, found {len(copied_paths)}."
            )
        for path in copied_paths:
            circuit = QuantumCircuit.from_qasm_file(str(path))
            if not 2 <= circuit.num_qubits <= 30:
                raise ValueError(f"Copied circuit outside 2-30 qubits: {path}")
            filenames_by_split[split].add(path.name)
            hashes_by_split[split].add(sha256_file(path))

    for row in rows:
        split = row["split"]
        copied_path = targets[split] / row["filename"]
        if sha256_file(copied_path) != row["sha256"]:
            raise ValueError(f"Hash mismatch after copying: {copied_path}")
        groups_by_split[split].add(row["leakage_group"])

    split_names = list(SPLIT_FAMILY_QUOTAS)
    overlap_report = {}
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            key = f"{left}__{right}"
            filename_overlap = filenames_by_split[left] & filenames_by_split[right]
            hash_overlap = hashes_by_split[left] & hashes_by_split[right]
            group_overlap = groups_by_split[left] & groups_by_split[right]
            overlap_report[key] = {
                "filename_overlap_count": len(filename_overlap),
                "hash_overlap_count": len(hash_overlap),
                "leakage_group_overlap_count": len(group_overlap),
            }
            if filename_overlap or hash_overlap or group_overlap:
                raise ValueError(
                    f"Split overlap between {left} and {right}: "
                    f"filenames={filename_overlap}, hashes={hash_overlap}, groups={group_overlap}"
                )

    return {
        "status": "valid",
        "validated_at": utc_now(),
        "expected_counts": expected_counts,
        "overlaps": overlap_report,
        "all_qasm_parseable": True,
        "all_hashes_match_manifest": True,
        "all_circuits_within_2_30_qubits": True,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rl-source", type=Path, default=DEFAULT_RL_SOURCE)
    parser.add_argument("--ml-source", type=Path, default=DEFAULT_ML_SOURCE)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace QASM files previously generated in the three uncompiled split directories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and select without copying circuits or writing manifests.",
    )
    return parser.parse_args()


def main() -> int:
    """Prepare and validate the selected circuit split."""
    args = parse_args()
    if not args.rl_source.is_dir():
        raise SystemExit(f"RL source directory not found: {args.rl_source}")
    if not args.ml_source.is_dir():
        raise SystemExit(f"ML source directory not found: {args.ml_source}")

    corpus_comparison = compare_rl_and_ml_corpora(args.rl_source, args.ml_source)
    assignments = split_group_assignment()
    inventory = [
        inspect_circuit(path)
        for path in sorted(args.rl_source.glob("*.qasm"))
    ]
    if len(inventory) != corpus_comparison["rl_qasm_count"]:
        raise ValueError("RL inventory count changed while preparing the split.")

    by_family: dict[str, list[CircuitMetadata]] = defaultdict(list)
    for item in inventory:
        by_family[item.family].append(item)

    rows: list[dict[str, Any]] = []
    for split, family_quotas in SPLIT_FAMILY_QUOTAS.items():
        for family, quota in family_quotas.items():
            if family not in by_family:
                raise ValueError(f"Family missing from RL corpus: {family}")
            for metadata, selection in select_family_representatives(
                by_family[family],
                quota,
            ):
                row = {
                    "split": split,
                    **asdict(metadata),
                    **selection,
                    "source_corpus": "mqt.predictor.rl.training_data.training_circuits",
                    "also_present_in_ml_corpus": True,
                    "destination_path": path_for_manifest(
                        args.dataset_root
                        / SPLIT_TARGET_DIRS[split]
                        / metadata.filename
                    ),
                }
                rows.append(row)

    selected_filenames = [row["filename"] for row in rows]
    selected_hashes = [row["sha256"] for row in rows]
    if len(selected_filenames) != len(set(selected_filenames)):
        raise ValueError("Selected filenames are not unique.")
    if len(selected_hashes) != len(set(selected_hashes)):
        raise ValueError("Selected circuit contents are not unique.")

    summary = summarize_rows(rows)
    print("Corpus comparison:")
    print(json.dumps(corpus_comparison, indent=2))
    print("Selected split:")
    print(json.dumps(summary, indent=2))

    if args.dry_run:
        print("Dry run: no files copied and no manifests written.")
        return 0

    targets = target_directories(args.dataset_root)
    ensure_targets_are_ready(targets, args.overwrite)
    inventory_by_filename = {item.filename: item for item in inventory}
    for row in rows:
        source = args.rl_source / row["filename"]
        destination = targets[row["split"]] / row["filename"]
        shutil.copy2(source, destination)
        if inventory_by_filename[row["filename"]].sha256 != sha256_file(destination):
            raise ValueError(f"Copy verification failed: {destination}")

    validation = validate_copied_splits(rows, targets)
    csv_path = args.dataset_root / "split_manifest.csv"
    json_path = args.dataset_root / "split_manifest.json"
    write_csv_manifest(rows, csv_path)
    write_json_manifest(
        {
            "schema_version": "1.0.0",
            "created_at": utc_now(),
            "purpose": (
                "Leakage-aware source-circuit split for generating MQT Predictor "
                "end-to-end JSON traces for an LLM."
            ),
            "mqt_predictor_version": version("mqt.predictor"),
            "source_corpora": {
                "rl": path_for_manifest(args.rl_source),
                "ml": path_for_manifest(args.ml_source),
            },
            "corpus_comparison": corpus_comparison,
            "split_ratio": {
                "train": 0.70,
                "validation": 0.15,
                "test": 0.15,
            },
            "selection_criteria": [
                "Use the 2-30-qubit RL corpus as the in-distribution source.",
                "Keep related algorithm variants in the same leakage group and split.",
                "Represent small (2-7), medium (8-15), and large (16-30) widths.",
                "Alternate Qiskit- and TKET-generated source circuits.",
                "Select width quantiles within each family.",
                "Reject duplicate filenames and duplicate QASM hashes.",
                "Reserve the 100 ML-only larger circuits for a future OOD study.",
            ],
            "leakage_group_assignments": assignments,
            "family_quotas": SPLIT_FAMILY_QUOTAS,
            "summary": summary,
            "validation": validation,
            "manifest_csv": path_for_manifest(csv_path),
            "records": rows,
        },
        json_path,
    )

    print(f"Copied {len(rows)} circuits.")
    print(f"CSV manifest:  {csv_path}")
    print(f"JSON manifest: {json_path}")
    print("Validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Circuit inventory, deterministic splits, and common Dataset I/O."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable, Mapping

from .catalog import ConfigurationCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS_ROOT = PROJECT_ROOT / "datasets"
SCHEMA_VERSION = "1.0.0"
MANIFEST_SCHEMA_VERSION = "2.0.0"
FILENAME_PATTERN = re.compile(
    r"^(?P<family>.+)_indep_(?P<generator>qiskit|tket)_(?P<qubits>\d+)\.qasm$"
)
SPLIT_ORDER = {"train": 0, "validation": 1, "test": 2}

FAMILY_TO_GROUP = {
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
GROUP_TO_SPLIT = {
    "ae": "train",
    "dj": "train",
    "graphstate": "train",
    "portfolio": "train",
    "qaoa": "train",
    "qnn": "train",
    "random_ansatz": "train",
    "vqe": "train",
    "wstate": "train",
    "qft": "validation",
    "pricing": "validation",
    "qpe": "test",
    "tsp": "test",
    "routing": "test",
    "groundstate": "test",
}
PILOT_FILENAMES = (
    "ae_indep_qiskit_2.qasm",
    "qaoa_indep_tket_7.qasm",
    "graphstate_indep_qiskit_14.qasm",
    "vqe_indep_tket_16.qasm",
    "random_indep_qiskit_30.qasm",
    "wstate_indep_tket_90.qasm",
    "pricingcall_indep_qiskit_5.qasm",
    "qft_indep_tket_40.qasm",
    "routing_indep_qiskit_12.qasm",
    "qpeexact_indep_tket_60.qasm",
)


def dataset_scope_root(
    objective: str,
    scope: str,
    device_id: str | None = None,
) -> Path:
    """Return the legacy scope root or an isolated per-device root."""
    root = DATASETS_ROOT / objective / scope
    if device_id is None:
        return root
    if Path(device_id).name != device_id or device_id in {".", ".."}:
        raise ValueError(f"device_id non valido per un path: {device_id!r}.")
    return root / device_id


def dataset_circuits_root(objective: str, scope: str) -> Path:
    """Return the single shared circuit store for one objective and scope."""
    return dataset_scope_root(objective, scope) / "circuits"


def resolve_circuit_source(
    objective: str,
    scope: str,
    source_ref: str,
) -> Path:
    """Resolve a manifest circuit reference inside its shared scope root."""
    scope_root = dataset_scope_root(objective, scope).resolve()
    candidate = (scope_root / source_ref).resolve()
    try:
        candidate.relative_to(scope_root)
    except ValueError as error:
        raise ValueError(
            f"source_ref fuori dallo scope Dataset: {source_ref!r}."
        ) from error
    return candidate


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def atomic_json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_jsonl_write(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    lines: list[str] = []
    for record in records:
        lines.append(canonical_json(record))
    atomic_text_write(path, "".join(f"{line}\n" for line in lines))
    return len(lines)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.is_file():
        return records
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record JSONL non oggetto.")
            records.append(value)
    return records


def package_versions() -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ("mqt.predictor", "mqt.bench", "qiskit"):
        try:
            result[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result[name] = "not-installed"
    return result


def feature_names() -> tuple[str, ...]:
    from mqt.predictor.ml.helper import get_openqasm_gates

    return tuple(
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


def ensure_training_circuits(source: Path | None = None) -> Path:
    from mqt.predictor.ml.helper import get_path_training_circuits

    path = Path(get_path_training_circuits()) if source is None else source
    if any(path.glob("*.qasm")):
        return path
    archive = path / "training_data_device_selection.zip"
    if not archive.is_file():
        raise FileNotFoundError(
            f"Nessun QASM e nessun archivio del corpus MQT in {path}."
        )
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(path)
    return path


def _extract_features(path: Path) -> tuple[dict[str, float], dict[str, Any]]:
    from mqt.predictor.ml.helper import create_feature_vector
    from qiskit import QuantumCircuit

    circuit = QuantumCircuit.from_qasm_file(str(path))
    names = feature_names()
    values = create_feature_vector(circuit)
    if len(names) != 49 or len(values) != len(names):
        raise RuntimeError(
            f"Feature inattese per {path.name}: {len(values)} valori, "
            f"{len(names)} nomi."
        )
    features = {
        name: float(value)
        for name, value in zip(names, values, strict=True)
    }
    metadata_record = {
        "num_qubits": int(circuit.num_qubits),
        "num_clbits": int(circuit.num_clbits),
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "operation_counts": {
            str(name): int(count)
            for name, count in sorted(circuit.count_ops().items())
        },
    }
    return features, metadata_record


def _base_inventory(source: Path) -> list[dict[str, Any]]:
    paths = sorted(source.glob("*.qasm"), key=lambda item: item.name)
    if len(paths) != 600:
        raise ValueError(f"Corpus MQT inatteso: trovati {len(paths)} QASM, attesi 600.")

    hashes = {path.name: sha256_file(path) for path in paths}
    names_by_hash: dict[str, list[str]] = defaultdict(list)
    for name, digest in hashes.items():
        names_by_hash[digest].append(name)

    inventory: list[dict[str, Any]] = []
    for path in paths:
        match = FILENAME_PATTERN.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Nome QASM MQT non riconosciuto: {path.name}.")
        family = match.group("family")
        if family not in FAMILY_TO_GROUP:
            raise ValueError(f"Famiglia MQT non classificata: {family}.")
        group = FAMILY_TO_GROUP[family]
        split = GROUP_TO_SPLIT[group]
        features, circuit_metadata = _extract_features(path)
        digest = hashes[path.name]
        duplicate_names = sorted(names_by_hash[digest])
        canonical_name = duplicate_names[0]
        declared_num_qubits = int(match.group("qubits"))
        if circuit_metadata["num_qubits"] != declared_num_qubits:
            raise ValueError(
                f"Larghezza incoerente per {path.name}: "
                f"{declared_num_qubits} nel nome, "
                f"{circuit_metadata['num_qubits']} nel QASM."
            )
        inventory.append(
            {
                "circuit_id": path.stem,
                "file_name": path.name,
                "benchmark_family": family,
                "leakage_group": group,
                "generator": match.group("generator"),
                "declared_num_qubits": declared_num_qubits,
                **circuit_metadata,
                "source_sha256": digest,
                "canonical_circuit_id": Path(canonical_name).stem,
                "duplicate_group_size": len(duplicate_names),
                "is_exact_duplicate": len(duplicate_names) > 1,
                "is_duplicate_alias": path.name != canonical_name,
                "split": split,
                "features": {
                    "extractor": "mqt.predictor.ml.helper.create_feature_vector",
                    "dimension": len(features),
                    "values": features,
                },
                "_source_path": path,
            }
        )
    return inventory


def _validate_split(records: list[dict[str, Any]], scope: str) -> None:
    expected = {
        "pilot": {"train": 6, "validation": 2, "test": 2},
        "full": {"train": 422, "validation": 88, "test": 90},
    }[scope]
    observed = Counter(str(record["split"]) for record in records)
    if dict(observed) != expected:
        raise ValueError(f"Split {scope} inatteso: {dict(observed)}, atteso {expected}.")

    split_by_hash: dict[str, set[str]] = defaultdict(set)
    for record in records:
        split_by_hash[str(record["source_sha256"])].add(str(record["split"]))
    leaked = {
        digest: sorted(splits)
        for digest, splits in split_by_hash.items()
        if len(splits) > 1
    }
    if leaked:
        raise ValueError(f"Hash QASM presenti in split diversi: {leaked}.")


def _ensure_circuit_copy(
    source: Path,
    destination: Path,
    expected_sha256: str,
) -> None:
    """Create one integrity-checked shared QASM copy without overwriting it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or sha256_file(destination) != expected_sha256:
            raise RuntimeError(
                f"QASM condiviso esistente ma incoerente: {destination}."
            )
        return

    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        shutil.copy2(source, temporary)
        if sha256_file(temporary) != expected_sha256:
            raise RuntimeError(f"Copia QASM corrotta: {destination}.")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_dataset(
    scope: str,
    catalog: ConfigurationCatalog,
    *,
    source: Path | None = None,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Create circuit copies and a deterministic split manifest."""
    if scope not in {"pilot", "full"}:
        raise ValueError("scope deve essere pilot oppure full.")
    from mqt.bench.targets import get_device

    selected_device_id = catalog.require_device(device_id)
    device_num_qubits = int(get_device(selected_device_id).num_qubits)
    source_path = ensure_training_circuits(source)
    all_records = _base_inventory(source_path)
    if scope == "pilot":
        by_name = {str(record["file_name"]): record for record in all_records}
        missing = sorted(set(PILOT_FILENAMES) - set(by_name))
        if missing:
            raise ValueError(f"Circuiti pilota mancanti: {missing}.")
        records = [by_name[name] for name in PILOT_FILENAMES]
    else:
        records = all_records

    records.sort(
        key=lambda record: (
            SPLIT_ORDER[str(record["split"])],
            str(record["file_name"]),
        )
    )
    _validate_split(records, scope)

    objective_name = str(catalog.objective["name"])
    output_root = dataset_scope_root(
        objective_name,
        scope,
        selected_device_id,
    )
    circuits_root = dataset_circuits_root(objective_name, scope)
    for record in records:
        compatible = int(record["num_qubits"]) <= device_num_qubits
        record["device_compatibility"] = {
            "compatible": compatible,
            "device_num_qubits": device_num_qubits,
            "reason": (
                None
                if compatible
                else (
                    f"circuit_width_{record['num_qubits']}_exceeds_"
                    f"device_width_{device_num_qubits}"
                )
            ),
        }
        relative_path = (
            Path("circuits")
            / str(record["split"])
            / str(record["file_name"])
        )
        destination = circuits_root / Path(*relative_path.parts[1:])
        _ensure_circuit_copy(
            Path(record["_source_path"]),
            destination,
            str(record["source_sha256"]),
        )
        record["source_ref"] = relative_path.as_posix()
        record.pop("_source_path", None)

    split_counts = Counter(str(record["split"]) for record in records)
    family_counts = Counter(str(record["benchmark_family"]) for record in records)
    generator_counts = Counter(str(record["generator"]) for record in records)
    compatible_count = sum(
        bool(record["device_compatibility"]["compatible"]) for record in records
    )
    duplicate_hashes = {
        str(record["source_sha256"])
        for record in records
        if bool(record["is_exact_duplicate"])
    }
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "dataset_scope": scope,
        "objective": dict(catalog.objective),
        "device_id": selected_device_id,
        "device_num_qubits": device_num_qubits,
        "catalog_id": catalog.catalog_id,
        "seeds": list(catalog.seeds),
        "circuit_storage": {
            "layout": "shared_scope_root",
            "root_ref": "circuits",
            "source_ref_base": "scope_root",
            "integrity_field": "source_sha256",
        },
        "split_policy": {
            "type": "family_group_holdout",
            "group_to_split": dict(sorted(GROUP_TO_SPLIT.items())),
            "claim": "generalizzazione a famiglie di circuiti non viste",
            "limitation": (
                "validation e test arrivano a 70 qubit; i circuiti da 80/90 "
                "qubit sono presenti soltanto nel train"
            ),
        },
        "counts": {
            "circuits": len(records),
            "compatible_circuits": compatible_count,
            "incompatible_circuits": len(records) - compatible_count,
            "attempts_planned": (
                compatible_count
                * len(catalog.configurations)
                * len(catalog.seeds)
            ),
            "by_split": dict(sorted(split_counts.items())),
            "by_family": dict(sorted(family_counts.items())),
            "by_generator": dict(sorted(generator_counts.items())),
            "unique_source_hashes": len(
                {str(record["source_sha256"]) for record in records}
            ),
            "duplicate_hash_groups": len(duplicate_hashes),
        },
        "feature_contract": {
            "extractor": "mqt.predictor.ml.helper.create_feature_vector",
            "names": list(feature_names()),
            "dimension": len(feature_names()),
            "source_circuit_only": True,
        },
        "provenance": {
            "corpus": "MQT Predictor ML device-selector training circuits",
            "corpus_locator": "mqt.predictor.ml.helper.get_path_training_circuits",
            "versions": package_versions(),
        },
        "circuits": records,
    }
    manifest["manifest_id"] = stable_id("manifest", manifest)
    atomic_json_write(output_root / "split_manifest.json", manifest)
    return manifest


def load_manifest(
    scope: str,
    objective: str = "expected_fidelity",
    device_id: str | None = None,
) -> dict[str, Any]:
    path = dataset_scope_root(objective, scope, device_id) / "split_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Manifest assente: {path}. Eseguire prima 07_prepare_qiskit_dataset.py."
        )
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("dataset_scope") != scope:
        raise ValueError(f"Scope incoerente nel manifest {path}.")
    if device_id is not None and manifest.get("device_id") != device_id:
        raise ValueError(
            f"Device incoerente nel manifest {path}: {manifest.get('device_id')!r}."
        )
    return manifest


def make_run_id(
    circuit: Mapping[str, Any],
    configuration: Mapping[str, Any],
    seed: int,
    *,
    device_id: str,
    target_sha256: str,
    objective: Mapping[str, Any],
    versions: Mapping[str, str],
) -> str:
    identity = {
        "circuit_id": circuit["circuit_id"],
        "source_sha256": circuit["source_sha256"],
        "device_id": device_id,
        "target_sha256": target_sha256,
        "configuration": {
            "config_id": configuration["config_id"],
            "optimization_level": configuration["optimization_level"],
            "layout_method": configuration.get("layout_method"),
            "routing_method": configuration.get("routing_method"),
        },
        "seed_transpiler": seed,
        "objective": {
            "name": objective["name"],
            "implementation": objective["implementation"],
        },
        "versions": dict(versions),
    }
    return stable_id("run", identity)


def expand_attempts(
    manifest: Mapping[str, Any],
    catalog: ConfigurationCatalog,
    *,
    target_sha256: str,
    versions: Mapping[str, str] | None = None,
    device_id: str | None = None,
) -> list[dict[str, Any]]:
    selected_device_id = catalog.require_device(
        device_id or str(manifest.get("device_id", catalog.default_device_id))
    )
    if manifest.get("device_id") not in {None, selected_device_id}:
        raise ValueError("Device del manifest incoerente con il piano.")
    version_map = package_versions() if versions is None else dict(versions)
    attempts: list[dict[str, Any]] = []
    configuration_order = {
        configuration.config_id: index
        for index, configuration in enumerate(catalog.configurations)
    }
    for circuit in manifest["circuits"]:
        if circuit.get("device_compatibility", {}).get("compatible") is False:
            continue
        for configuration in catalog.configurations:
            configuration_record = configuration.to_dict()
            for seed in catalog.seeds:
                attempts.append(
                    {
                        "run_id": make_run_id(
                            circuit,
                            configuration_record,
                            seed,
                            device_id=selected_device_id,
                            target_sha256=target_sha256,
                            objective=catalog.objective,
                            versions=version_map,
                        ),
                        "dataset_scope": manifest["dataset_scope"],
                        "split": circuit["split"],
                        "circuit": circuit,
                        "configuration": configuration_record,
                        "configuration_order": configuration_order[
                            configuration.config_id
                        ],
                        "seed_transpiler": seed,
                        "device_id": selected_device_id,
                        "target_sha256": target_sha256,
                        "objective": dict(catalog.objective),
                        "versions": version_map,
                        "fixed_transpile_options": dict(
                            catalog.fixed_transpile_options
                        ),
                        "catalog_id": catalog.catalog_id,
                    }
                )
    attempts.sort(
        key=lambda item: (
            SPLIT_ORDER[str(item["split"])],
            str(item["circuit"]["circuit_id"]),
            int(item["configuration_order"]),
            int(item["seed_transpiler"]),
        )
    )
    identifiers = [str(attempt["run_id"]) for attempt in attempts]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("run_id duplicati nel piano di esecuzione.")
    return attempts

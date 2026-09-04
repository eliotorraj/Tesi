"""Frozen MQT Predictor protocol and target-validation helpers."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any, Iterable, Mapping

FROZEN_DEVICES = (
    "ibm_falcon_27",
    "ibm_heron_133",
    "ibm_falcon_127",
    "ibm_heron_156",
    "quantinuum_h2_56",
)
FIGURE_OF_MERIT = "expected_fidelity"
COMPILATION_TIMEOUT_SECONDS = 300
QISKIT_WORKERS = 2
RL_TRAINING_TIMESTEPS = 100_000
RL_ROLLOUT_STEPS = 2_048
RL_CHECKPOINT_EVERY = 5 * RL_ROLLOUT_STEPS
# Stable-Baselines3 completa sempre il rollout corrente. Il target richiesto
# resta 100000, mentre il contatore finale attestato è quindi 49 * 2048.
RL_FINAL_TIMESTEPS = (
    (RL_TRAINING_TIMESTEPS + RL_ROLLOUT_STEPS - 1)
    // RL_ROLLOUT_STEPS
    * RL_ROLLOUT_STEPS
)
PROTOCOL_ID = "qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2"
TARGET_FINGERPRINT_SCHEMA_VERSION = 2
LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS = frozenset(
    {
        "box",
        "break",
        "continue",
        "for_loop",
        "if_else",
        "switch_case",
        "while_loop",
    }
)

# These fingerprints are the migrated protocol targets from mqt.bench 2.2.3,
# the version locked by MQT Predictor 2.4.0.
FROZEN_TARGET_SHA256 = {
    "ibm_falcon_27": "b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104",
    "ibm_heron_133": "2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3",
    "ibm_falcon_127": "5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd",
    "ibm_heron_156": "207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003",
    "quantinuum_h2_56": "ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee",
}

# Historical qiskit_dataset fingerprints from mqt.bench 2.0.0. They are kept
# as evidence of target drift and must not be mixed into the migrated benchmark.
LEGACY_QISKIT_DATASET_TARGET_SHA256 = {
    "ibm_falcon_27": "f30536987677ef5017fe3a89b8b4ee0a3e7252a1a226cc3db95fd9b2e822d991",
    "ibm_heron_133": "804f28754ad200e42a328ba910639c9d6fd3233dff35035e7f3cb85a2fc5168a",
    "ibm_falcon_127": "225e5f6fd85af0b37a1dd7c6306dd046a8c7ca585f135dda6e6418dd16f76b48",
    "ibm_heron_156": "a30f41e65c03fb900a4b8852261a8407c56c389560f4031ecb43099c1bec5089",
    "quantinuum_h2_56": "8c5576ac2f280a98f797dceb53186f97500e901d9784cc328187e156cbbe9b8f",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = PROTOCOL_ID
PROTOCOL_VERSION = "2.0.0"
EXPECTED_SPLIT_COUNTS = {"train": 422, "validation": 88, "test": 90}
LEGACY_SOURCE_MANIFEST = (
    PROJECT_ROOT / "datasets" / "expected_fidelity" / "full" / "split_manifest.json"
)
LEGACY_SOURCE_MANIFEST_SHA256 = (
    "9037e08f529e6598f69cc8ffa524f593335d0e65757db771ce28b285479529ed"
)
EXPERIMENT_ROOT = PROJECT_ROOT / "artifacts" / "experiments" / EXPERIMENT_ID
SOURCE_MANIFEST_V2 = EXPERIMENT_ROOT / "manifests" / "source_circuits_v2.json"
TRAINING_CIRCUITS_V2 = EXPERIMENT_ROOT / "sources" / "train"
VALIDATION_CIRCUITS_V2 = EXPERIMENT_ROOT / "sources" / "validation"
TEST_RELEASE_RECORD = EXPERIMENT_ROOT / "manifests" / "test_release.json"
METHOD_CONFIG_V2 = PROJECT_ROOT / "configs" / "experiment_methods_v2.json"
METHOD_PLAN_DIR_V2 = EXPERIMENT_ROOT / "plans"
METHOD_RESULTS_DIR_V2 = EXPERIMENT_ROOT / "method_results"
CANONICAL_MODEL_ROOT_V2 = EXPERIMENT_ROOT / "models"
CANONICAL_RL_MODEL_DIR_V2 = CANONICAL_MODEL_ROOT_V2 / "rl"
CANONICAL_ML_MODEL_DIR_V2 = CANONICAL_MODEL_ROOT_V2 / "ml"
MQT_TRAINING_SET_V2 = (
    PROJECT_ROOT
    / "datasets"
    / "experiments"
    / EXPERIMENT_ID
    / "training_set"
    / f"device_selector_{FIGURE_OF_MERIT}.json"
)
EXPECTED_PACKAGE_VERSIONS = {
    "mqt.predictor": "2.4.0",
    "mqt.bench": "2.2.3",
    "qiskit": "2.5.0",
    "qiskit-aer": "0.17.2",
    "qiskit-ibm-runtime": "0.47.0",
    "qiskit-qasm3-import": "0.6.0",
    "pytket": "2.18.1",
    "pytket-qiskit": "0.77.0",
    "bqskit": "1.2.1",
    "numpy": "2.5.1",
    "scikit-learn": "1.9.0",
    "sb3-contrib": "2.9.0",
    "stable-baselines3": "2.9.0",
    "gymnasium": "1.3.0",
    "torch": "2.13.0",
    "joblib": "1.5.3",
    "tensorboard": "2.21.0",
}


def canonical_json(payload: Any) -> str:
    """Serialize a payload deterministically for hashing."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def finite_float(value: Any) -> float | None:
    """Return a finite float or None for unavailable calibration data."""
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return converted if math.isfinite(converted) else None


def file_sha256(path: Path) -> str:
    """Hash a file without loading large model archives into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _target_operation_name(target: Any, operation: Any) -> str:
    """Resolve Target instruction classes without serializing memory addresses."""
    raw_name = getattr(operation, "name", None)
    if isinstance(raw_name, str):
        return raw_name
    for candidate in target.operation_names:
        try:
            registered = target.operation_from_name(candidate)
        except (AttributeError, KeyError):
            continue
        if registered is operation:
            return str(candidate)
    raise ValueError(f"Operazione Target senza nome stabile: {operation!r}")


def target_payload(target: Any) -> dict[str, Any]:
    """Return the canonical Target payload used by the frozen protocol."""
    instructions: list[dict[str, Any]] = []
    for operation, qargs in target.instructions:
        operation_name = _target_operation_name(target, operation)
        properties = None
        try:
            properties = target[operation_name].get(qargs)
        except (AttributeError, KeyError, TypeError):
            pass
        instructions.append(
            {
                "name": operation_name,
                "qargs": None if qargs is None else [int(qubit) for qubit in qargs],
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
        "fingerprint_schema_version": TARGET_FINGERPRINT_SCHEMA_VERSION,
        "device_id": str(target.description),
        "target_type": f"{type(target).__module__}.{type(target).__qualname__}",
        "num_qubits": int(target.num_qubits),
        "operation_names": sorted(map(str, target.operation_names)),
        "coupling_edges": edges,
        "all_to_all": coupling_map is None,
        "instructions": instructions,
    }


def target_sha256(target: Any) -> str:
    """Hash a Target with the deterministic, versioned protocol schema."""
    payload = target_payload(target)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def legacy_comparable_target_sha256(target: Any) -> str:
    """Hash current native Target data with qiskit_dataset's legacy schema.

    Qiskit 2.5 adds control-flow instructions that were absent from the
    historical Target payload. Excluding them and the schema-v2 marker makes
    the remaining native gates, topology, errors, and durations directly
    comparable with the hashes stored on qiskit_dataset.
    """
    payload = target_payload(target)
    payload.pop("fingerprint_schema_version")
    payload["operation_names"] = [
        name
        for name in payload["operation_names"]
        if name not in LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS
    ]
    payload["instructions"] = [
        item
        for item in payload["instructions"]
        if item["name"] not in LEGACY_IGNORED_CONTROL_FLOW_OPERATIONS
    ]
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def target_record(target: Any) -> dict[str, Any]:
    """Build a compact provenance record for one Target."""
    payload = target_payload(target)
    return {
        "fingerprint_schema_version": TARGET_FINGERPRINT_SCHEMA_VERSION,
        "device_id": str(target.description),
        "num_qubits": int(target.num_qubits),
        "operation_names": payload["operation_names"],
        "coupling_edge_count": len(payload["coupling_edges"]),
        "target_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "target_type": payload["target_type"],
    }


def validate_compiled_circuit(circuit: Any, target: Any) -> dict[str, Any]:
    """Check basis, connectivity, and per-instruction Target support."""
    from qiskit.transpiler.passes import CheckMap, GatesInBasis

    errors: list[str] = []
    unsupported_operations = sorted(
        set(map(str, circuit.count_ops()))
        - set(map(str, target.operation_names))
        - {"barrier"}
    )
    basis_valid: bool | None = None
    connectivity_valid: bool | None = None
    instructions_valid = True

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

    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name == "barrier":
            continue
        qargs = tuple(circuit.find_bit(qubit).index for qubit in instruction.qubits)
        try:
            supported = target.instruction_supported(
                operation_name=operation.name,
                qargs=qargs,
                parameters=list(operation.params),
            )
        except Exception as error:
            instructions_valid = False
            errors.append(
                f"instruction_supported:{operation.name}{qargs}:"
                f"{type(error).__name__}:{error}"
            )
            continue
        if not supported:
            instructions_valid = False
            errors.append(f"unsupported_instruction:{operation.name}{qargs}")

    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "instructions_valid": instructions_valid,
        "is_executable_on_target": bool(
            basis_valid
            and connectivity_valid
            and instructions_valid
            and not unsupported_operations
            and not errors
        ),
        "unsupported_operations": unsupported_operations,
        "validation_errors": errors,
    }


def frozen_target_mismatches(devices: list[Any]) -> dict[str, dict[str, str]]:
    """Return devices whose current Target differs from the frozen protocol."""
    mismatches: dict[str, dict[str, str]] = {}
    for target in devices:
        device_name = str(target.description)
        observed = target_sha256(target)
        expected = FROZEN_TARGET_SHA256.get(device_name)
        if expected != observed:
            mismatches[device_name] = {
                "expected": expected or "<not-in-frozen-protocol>",
                "observed": observed,
            }
    return mismatches


def installed_package_versions() -> dict[str, str]:
    """Return every package version frozen by protocol v2."""
    versions: dict[str, str] = {}
    for distribution in EXPECTED_PACKAGE_VERSIONS:
        try:
            versions[distribution] = package_version(distribution)
        except PackageNotFoundError:
            versions[distribution] = "not-installed"
    return versions


def package_version_mismatches(
    observed: Mapping[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    """Return packages whose installed version differs from the v2 lock."""
    current = installed_package_versions() if observed is None else dict(observed)
    return {
        name: {
            "expected": expected,
            "observed": current.get(name, "not-installed"),
        }
        for name, expected in EXPECTED_PACKAGE_VERSIONS.items()
        if current.get(name) != expected
    }


def _canonical_parameter(value: Any) -> int | float | str:
    """Normalize a Qiskit instruction parameter without unstable repr data."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError):
        return str(value)
    if not math.isfinite(converted):
        return str(value)
    return float(format(converted, ".15g"))


def semantic_circuit_payload(circuit: Any) -> dict[str, Any]:
    """Build a serializer-independent instruction stream for leakage checks.

    Barriers and register names are deliberately ignored. This catches exact
    circuits emitted by different QASM serializers while retaining operations,
    parameters, qubit positions, classical bits, and global phase.
    """
    instructions: list[dict[str, Any]] = []
    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name == "barrier":
            continue
        instructions.append(
            {
                "name": str(operation.name),
                "params": [
                    _canonical_parameter(parameter)
                    for parameter in operation.params
                ],
                "qubits": [
                    int(circuit.find_bit(qubit).index)
                    for qubit in instruction.qubits
                ],
                "clbits": [
                    int(circuit.find_bit(clbit).index)
                    for clbit in instruction.clbits
                ],
            }
        )
    return {
        "schema": "mqt-experiment-circuit-semantic/1",
        "num_qubits": int(circuit.num_qubits),
        "num_clbits": int(circuit.num_clbits),
        "global_phase": _canonical_parameter(circuit.global_phase),
        "instructions": instructions,
    }


def semantic_circuit_sha256(path: Path) -> str:
    """Hash the normalized meaning-relevant content of an OpenQASM 2 file."""
    from qiskit import QuantumCircuit

    circuit = QuantumCircuit.from_qasm_file(str(path))
    payload = semantic_circuit_payload(circuit)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _safe_source_path(manifest_path: Path, source_ref: str) -> Path:
    """Resolve one source reference without allowing traversal."""
    root = manifest_path.parent.resolve()
    candidate = (root / source_ref).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"source_ref fuori dal corpus: {source_ref!r}") from error
    return candidate


def verify_source_manifest(
    manifest_path: Path = LEGACY_SOURCE_MANIFEST,
    *,
    require_frozen_file_hash: bool = True,
) -> dict[str, Any]:
    """Validate the frozen 600-circuit source corpus without compiling tests."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest sorgente mancante: {manifest_path}")
    observed_manifest_sha256 = file_sha256(manifest_path)
    if (
        require_frozen_file_hash
        and manifest_path.resolve() == LEGACY_SOURCE_MANIFEST.resolve()
        and observed_manifest_sha256 != LEGACY_SOURCE_MANIFEST_SHA256
    ):
        raise ValueError(
            "Il manifest sorgente legacy è cambiato: "
            f"atteso={LEGACY_SOURCE_MANIFEST_SHA256}, "
            f"osservato={observed_manifest_sha256}."
        )
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not isinstance(loaded.get("circuits"), list):
        raise ValueError("Manifest sorgente non valido.")
    circuits = loaded["circuits"]
    counts = Counter(str(record.get("split")) for record in circuits)
    if dict(counts) != EXPECTED_SPLIT_COUNTS:
        raise ValueError(
            f"Split sorgente inattesi: {dict(counts)}; "
            f"attesi={EXPECTED_SPLIT_COUNTS}."
        )
    if len(circuits) != sum(EXPECTED_SPLIT_COUNTS.values()):
        raise ValueError(f"Numero circuiti inatteso: {len(circuits)}.")

    source_splits: dict[str, set[str]] = defaultdict(set)
    semantic_splits: dict[str, set[str]] = defaultdict(set)
    group_splits: dict[str, set[str]] = defaultdict(set)
    verified: list[dict[str, Any]] = []
    for raw_record in circuits:
        if not isinstance(raw_record, dict):
            raise ValueError("Record circuito non rappresentato da un oggetto.")
        split = str(raw_record.get("split"))
        source_ref = str(raw_record.get("source_ref"))
        path = _safe_source_path(manifest_path, source_ref)
        if not path.is_file():
            raise FileNotFoundError(f"Circuito sorgente mancante: {path}")
        expected_sha256 = str(raw_record.get("source_sha256"))
        observed_sha256 = file_sha256(path)
        if observed_sha256 != expected_sha256:
            raise ValueError(
                f"Hash sorgente diverso per {source_ref}: "
                f"atteso={expected_sha256}, osservato={observed_sha256}."
            )
        semantic_sha256 = semantic_circuit_sha256(path)
        leakage_group = str(raw_record.get("leakage_group"))
        source_splits[observed_sha256].add(split)
        semantic_splits[semantic_sha256].add(split)
        group_splits[leakage_group].add(split)
        verified.append(
            {
                "circuit_id": str(raw_record.get("circuit_id")),
                "file_name": str(raw_record.get("file_name", path.name)),
                "source_ref": (
                    path.relative_to(PROJECT_ROOT).as_posix()
                    if path.is_relative_to(PROJECT_ROOT)
                    else path.as_posix()
                ),
                "source_sha256": observed_sha256,
                "semantic_sha256": semantic_sha256,
                "split": split,
                "leakage_group": leakage_group,
                "num_qubits": int(raw_record.get("num_qubits")),
            }
        )

    def leaked(values: Mapping[str, set[str]]) -> dict[str, list[str]]:
        return {
            digest: sorted(splits)
            for digest, splits in values.items()
            if len(splits) > 1
        }

    source_leaks = leaked(source_splits)
    semantic_leaks = leaked(semantic_splits)
    group_leaks = leaked(group_splits)
    if source_leaks or semantic_leaks or group_leaks:
        raise ValueError(
            "Leakage tra split rilevato: "
            f"source_sha256={source_leaks}; "
            f"semantic_sha256={semantic_leaks}; "
            f"leakage_group={group_leaks}."
        )

    verified.sort(key=lambda record: (record["split"], record["file_name"]))
    corpus_sha256 = hashlib.sha256(
        canonical_json(
            [
                {
                    "file_name": record["file_name"],
                    "source_sha256": record["source_sha256"],
                    "semantic_sha256": record["semantic_sha256"],
                    "split": record["split"],
                }
                for record in verified
            ]
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "2.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
        "source_manifest": (
            manifest_path.relative_to(PROJECT_ROOT).as_posix()
            if manifest_path.is_relative_to(PROJECT_ROOT)
            else manifest_path.resolve().as_posix()
        ),
        "source_manifest_sha256": observed_manifest_sha256,
        "source_manifest_id": loaded.get("manifest_id"),
        "counts": {
            "circuits": len(verified),
            "by_split": dict(counts),
            "unique_source_sha256": len(source_splits),
            "unique_semantic_sha256": len(semantic_splits),
            "leakage_groups": len(group_splits),
        },
        "corpus_sha256": corpus_sha256,
        "circuits": verified,
    }


def verify_circuit_directory(
    directory: Path,
    *,
    allowed_splits: Iterable[str] = ("train",),
    manifest_path: Path = SOURCE_MANIFEST_V2,
) -> dict[str, Any]:
    """Require a directory to contain exactly the allowed frozen circuits."""
    allowed = frozenset(map(str, allowed_splits))
    if not allowed or not allowed.issubset(EXPECTED_SPLIT_COUNTS):
        raise ValueError(f"Split ammessi non validi: {sorted(allowed)}.")
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Manifest v2 mancante: {manifest_path}. "
            "Eseguire prima scripts/06_prepare_experiment_v2.py."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("Il manifest dei circuiti non appartiene all'esperimento v2.")
    records = [
        record
        for record in manifest.get("circuits", [])
        if record.get("split") in allowed
    ]
    expected = {str(record["file_name"]): record for record in records}
    observed = {
        path.name: path
        for path in directory.glob("*.qasm")
        if path.is_file()
    }
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    if missing or unexpected:
        raise ValueError(
            f"Directory circuiti non conforme: mancanti={missing}; "
            f"non previsti={unexpected}."
        )
    for name, record in expected.items():
        path = observed[name]
        if file_sha256(path) != record["source_sha256"]:
            raise ValueError(f"Hash sorgente non conforme nella directory: {name}.")
        if semantic_circuit_sha256(path) != record["semantic_sha256"]:
            raise ValueError(f"Hash semantico non conforme nella directory: {name}.")
    return {
        "experiment_id": EXPERIMENT_ID,
        "manifest_sha256": file_sha256(manifest_path),
        "splits": sorted(allowed),
        "circuit_count": len(records),
        "directory": str(directory.resolve()),
    }


def assert_records_belong_to_split(
    records: Iterable[Mapping[str, Any]],
    *,
    allowed_split: str,
    manifest: Mapping[str, Any],
) -> None:
    """Reject Dataset/Training-set records that refer to another split."""
    allowed_hashes = {
        str(record["source_sha256"])
        for record in manifest.get("circuits", [])
        if record.get("split") == allowed_split
    }
    forbidden_hashes = {
        str(record["source_sha256"])
        for record in manifest.get("circuits", [])
        if record.get("split") != allowed_split
    }
    for index, record in enumerate(records):
        split = record.get("split")
        circuit = record.get("circuit")
        source_sha256 = record.get("source_sha256")
        retrieval_input = record.get("retrieval_input")
        if isinstance(retrieval_input, Mapping):
            retrieval_circuit = retrieval_input.get("circuit")
            if isinstance(retrieval_circuit, Mapping):
                circuit = retrieval_circuit
        if isinstance(circuit, Mapping):
            split = circuit.get("split", split)
            source_sha256 = circuit.get("source_sha256", source_sha256)
        if split != allowed_split:
            raise ValueError(
                f"Record {index} fuori split: {split!r}; atteso={allowed_split!r}."
            )
        if source_sha256 not in allowed_hashes or source_sha256 in forbidden_hashes:
            raise ValueError(
                f"Record {index} con source_sha256 non ammesso: {source_sha256!r}."
            )


def validate_test_release_record(
    path: Path = TEST_RELEASE_RECORD,
) -> dict[str, Any]:
    """Validate the immutable evidence required before touching test circuits."""
    if not path.is_file():
        raise FileNotFoundError(
            "Lo split test è sigillato: record di apertura mancante."
        )
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Record di apertura test non valido: {error}") from error
    if not isinstance(record, dict):
        raise ValueError("Il record di apertura test deve essere un oggetto JSON.")
    expected = {
        "schema_version": "1.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "status": "released",
        "source_manifest_sha256": (
            file_sha256(SOURCE_MANIFEST_V2)
            if SOURCE_MANIFEST_V2.is_file()
            else None
        ),
        "target_sha256": FROZEN_TARGET_SHA256,
        "software": EXPECTED_PACKAGE_VERSIONS,
    }
    errors: list[str] = []
    for field, expected_value in expected.items():
        if record.get(field) != expected_value:
            errors.append(
                f"{field} non conforme: "
                f"atteso={expected_value!r}, osservato={record.get(field)!r}"
            )
    gates = record.get("gates")
    if (
        not isinstance(gates, dict)
        or not gates
        or any(value is not True for value in gates.values())
    ):
        errors.append("i gate di apertura non sono tutti esplicitamente superati")
    frozen_files = record.get("frozen_files")
    if not isinstance(frozen_files, dict) or not frozen_files:
        errors.append("elenco dei file congelati mancante")
    else:
        for relative_name, expected_digest in frozen_files.items():
            candidate = (PROJECT_ROOT / str(relative_name)).resolve()
            try:
                candidate.relative_to(PROJECT_ROOT.resolve())
            except ValueError:
                errors.append(f"file congelato fuori repository: {relative_name!r}")
                continue
            if not candidate.is_file():
                errors.append(f"file congelato mancante: {relative_name}")
            elif file_sha256(candidate) != expected_digest:
                errors.append(f"file congelato modificato: {relative_name}")
    if errors:
        raise ValueError(
            "Record di apertura test rifiutato:\n  - " + "\n  - ".join(errors)
        )
    return record

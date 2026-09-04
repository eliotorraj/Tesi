"""Contratti deterministici per piani, decisioni e valutazione del protocollo v2."""

from __future__ import annotations

import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from scripts.mqt_predictor_protocol import (
    COMPILATION_TIMEOUT_SECONDS,
    EXPERIMENT_ID,
    EXPECTED_PACKAGE_VERSIONS,
    EXPECTED_SPLIT_COUNTS,
    FROZEN_DEVICES,
    FROZEN_TARGET_SHA256,
    METHOD_CONFIG_V2,
    PROTOCOL_VERSION,
    SOURCE_MANIFEST_V2,
    canonical_json,
    file_sha256,
)

from .catalog import ConfigurationCatalog
from .core import SCHEMA_VERSION, make_run_id, stable_id
from .views import AGGREGATE_SCHEMA_VERSION


LLM_METHOD_IDS = ("llm_rag", "llm_no_rag", "frontier_llm")
QISKIT_DEFAULT_CONFIG_IDS = ("o2_default_default", "o3_default_default")
RANDOM_METHOD_ID = "qiskit_random"
ORACLE_METHOD_ID = "oracle_exhaustive"
QCOMPILE_METHOD_ID = "mqt_qcompile"
RANDOM_SELECTION_SEED = 20260901
RESULT_SCHEMA_VERSION = "1.0.0"


def stable_sha256(payload: Any) -> str:
    """Calcola l'impronta di un oggetto JSON canonico."""
    import hashlib

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    """Legge un oggetto JSON senza tollerare formati ambigui."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} non contiene un oggetto JSON.")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Legge un JSONL completo e segnala anche una singola riga non valida."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: JSON non valido.") from error
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record non oggetto.")
            records.append(value)
    return records


def atomic_json_write(path: Path, payload: Any) -> None:
    """Scrive JSON mediante rinomina atomica."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_jsonl_write(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    """Scrive un JSONL completo mediante rinomina atomica."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(canonical_json(dict(record)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def source_manifest(path: Path = SOURCE_MANIFEST_V2) -> dict[str, Any]:
    """Carica il corpus v2 già verificato."""
    manifest = load_json(path)
    if manifest.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("Manifest sorgente appartenente a un altro esperimento.")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("Versione del protocollo sorgente non conforme.")
    circuits = manifest.get("circuits")
    if not isinstance(circuits, list):
        raise ValueError("Manifest sorgente senza lista circuits.")
    counts = Counter(str(record.get("split")) for record in circuits)
    if dict(counts) != EXPECTED_SPLIT_COUNTS:
        raise ValueError(f"Conteggi split non conformi: {dict(counts)}.")
    return manifest


def split_circuits(
    split: str,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Restituisce l'universo ordinato di uno split."""
    if split not in {"validation", "test"}:
        raise ValueError("Il confronto confermativo ammette validation oppure test.")
    records = [
        dict(record)
        for record in manifest.get("circuits", [])
        if record.get("split") == split
    ]
    records.sort(key=lambda item: (str(item["circuit_id"]), str(item["source_sha256"])))
    if len(records) != EXPECTED_SPLIT_COUNTS[split]:
        raise ValueError(f"Numero circuiti {split} non conforme: {len(records)}.")
    identities = [(item["circuit_id"], item["source_sha256"]) for item in records]
    if len(identities) != len(set(identities)):
        raise ValueError(f"Identità duplicate nello split {split}.")
    circuit_ids = [str(item["circuit_id"]) for item in records]
    source_hashes = [str(item["source_sha256"]) for item in records]
    if len(circuit_ids) != len(set(circuit_ids)):
        raise ValueError(f"circuit_id duplicati nello split {split}.")
    if len(source_hashes) != len(set(source_hashes)):
        raise ValueError(f"source_sha256 duplicati nello split {split}.")
    return records


def device_capacities() -> dict[str, int]:
    """Legge capacità e fingerprint dai Target congelati."""
    from mqt.bench.targets import get_device
    from scripts.mqt_predictor_protocol import target_sha256

    result: dict[str, int] = {}
    for device_id in FROZEN_DEVICES:
        target = get_device(device_id)
        observed = target_sha256(target)
        if observed != FROZEN_TARGET_SHA256[device_id]:
            raise ValueError(
                f"Target drift per {device_id}: "
                f"atteso={FROZEN_TARGET_SHA256[device_id]}, osservato={observed}."
            )
        result[device_id] = int(target.num_qubits)
    return result


def validate_method_configuration(
    path: Path = METHOD_CONFIG_V2,
    *,
    require_frozen: bool,
) -> dict[str, Any]:
    """Valida i parametri dei tre metodi LLM senza inventare modelli."""
    config = load_json(path)
    expected = {
        "schema_version": "1.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
    }
    for field, value in expected.items():
        if config.get(field) != value:
            raise ValueError(f"{field} della configurazione metodi non conforme.")
    if require_frozen and config.get("status") != "frozen":
        raise ValueError(
            "I modelli LLM non sono ancora congelati: impostare status='frozen' "
            "solo dopo avere compilato provider, modello, revisione, prompt, "
            "temperatura e budget."
        )
    random_config = config.get("random_selection")
    if not isinstance(random_config, dict):
        raise ValueError("Configurazione della baseline casuale mancante.")
    if random_config.get("seed") != RANDOM_SELECTION_SEED:
        raise ValueError("Seed della baseline casuale non conforme.")
    if random_config.get("algorithm") != "python_random_v3_mt19937_randrange":
        raise ValueError("Algoritmo della baseline casuale non conforme.")

    methods = config.get("methods")
    if not isinstance(methods, dict) or set(methods) != set(LLM_METHOD_IDS):
        raise ValueError("La configurazione deve contenere esattamente i tre metodi LLM.")
    for method_id in LLM_METHOD_IDS:
        record = methods[method_id]
        if not isinstance(record, dict):
            raise ValueError(f"Configurazione non valida per {method_id}.")
        expected_attempts = 1 if method_id == "frontier_llm" else 3
        expected_rag = method_id == "llm_rag"
        if record.get("max_attempts") != expected_attempts:
            raise ValueError(f"max_attempts non conforme per {method_id}.")
        if record.get("rag_enabled") is not expected_rag:
            raise ValueError(f"rag_enabled non conforme per {method_id}.")
        if require_frozen:
            for field in ("provider", "model_id", "model_revision", "prompt_version"):
                value = record.get(field)
                if (
                    not isinstance(value, str)
                    or not value.strip()
                    or "replace" in value.lower()
                ):
                    raise ValueError(f"{method_id}.{field} non è congelato.")
            prompt_sha256 = record.get("prompt_sha256")
            if (
                not isinstance(prompt_sha256, str)
                or len(prompt_sha256) != 64
                or any(character not in "0123456789abcdef" for character in prompt_sha256)
            ):
                raise ValueError(f"{method_id}.prompt_sha256 non è valido.")
            temperature = record.get("temperature")
            if (
                isinstance(temperature, bool)
                or not isinstance(temperature, (int, float))
                or not math.isfinite(float(temperature))
                or not 0 <= float(temperature) <= 2
            ):
                raise ValueError(f"{method_id}.temperature non è valida.")
            request_timeout = record.get("request_timeout_seconds")
            if (
                isinstance(request_timeout, bool)
                or not isinstance(request_timeout, (int, float))
                or not math.isfinite(float(request_timeout))
                or request_timeout <= 0
            ):
                raise ValueError(
                    f"{method_id}.request_timeout_seconds non è valido."
                )
            max_output_tokens = record.get("max_output_tokens")
            if (
                isinstance(max_output_tokens, bool)
                or not isinstance(max_output_tokens, int)
                or max_output_tokens <= 0
            ):
                raise ValueError(
                    f"{method_id}.max_output_tokens non è valido."
                )
    if require_frozen:
        compared_fields = (
            "provider",
            "model_id",
            "model_revision",
            "temperature",
            "request_timeout_seconds",
            "max_output_tokens",
        )
        selected = {
            field: methods["llm_rag"].get(field) for field in compared_fields
        }
        without_rag = {
            field: methods["llm_no_rag"].get(field) for field in compared_fields
        }
        if selected != without_rag:
            raise ValueError("LLM + RAG e LLM senza RAG devono usare lo stesso modello.")
    return config


def build_method_plan(
    split: str,
    catalog: ConfigurationCatalog,
    *,
    manifest: Mapping[str, Any],
    capacities: Mapping[str, int],
    random_seed: int = RANDOM_SELECTION_SEED,
) -> dict[str, Any]:
    """Congela richieste e tre estrazioni casuali senza leggere alcuno score."""
    circuits = split_circuits(split, manifest)
    generator = random.Random(random_seed)
    configuration_ids = [
        configuration.config_id for configuration in catalog.configurations
    ]
    random_rows: list[dict[str, Any]] = []
    for circuit in circuits:
        compatible_devices = [
            device_id
            for device_id in catalog.supported_device_ids
            if int(circuit["num_qubits"]) <= int(capacities[device_id])
        ]
        candidates = [
            (device_id, config_id)
            for device_id in compatible_devices
            for config_id in configuration_ids
        ]
        if not candidates:
            raise ValueError(f"Nessun candidato per {circuit['circuit_id']}.")
        repetitions = []
        for repetition_index, qiskit_seed in enumerate(catalog.seeds):
            selected_device, selected_config = candidates[
                generator.randrange(len(candidates))
            ]
            repetitions.append(
                {
                    "repetition_index": repetition_index,
                    "qiskit_seed": int(qiskit_seed),
                    "selected_device_id": selected_device,
                    "selected_config_id": selected_config,
                }
            )
        random_rows.append(
            {
                "circuit_id": circuit["circuit_id"],
                "source_sha256": circuit["source_sha256"],
                "split": split,
                "compatible_device_ids": compatible_devices,
                "repetitions": repetitions,
            }
        )
    core = {
        "schema_version": "1.0.0",
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
        "split": split,
        "circuit_count": len(circuits),
        "device_order": list(catalog.supported_device_ids),
        "configuration_order": configuration_ids,
        "qiskit_seeds": list(catalog.seeds),
        "qiskit_execution_policy": dict(catalog.execution_policy),
        "random_selection": {
            "algorithm": "python_random_v3_mt19937_randrange",
            "seed": random_seed,
            "rows": random_rows,
        },
        "required_llm_methods": list(LLM_METHOD_IDS),
        "qcompile_repetition_indices": list(range(3)),
        "source_manifest_content_sha256": stable_sha256(dict(manifest)),
    }
    return {**core, "plan_sha256": stable_sha256(core)}


def validate_method_plan(
    plan: Mapping[str, Any],
    *,
    split: str,
    catalog: ConfigurationCatalog,
    manifest: Mapping[str, Any],
    capacities: Mapping[str, int],
) -> None:
    """Ricalcola il piano per impedire modifiche alle estrazioni."""
    expected = build_method_plan(
        split,
        catalog,
        manifest=manifest,
        capacities=capacities,
    )
    if dict(plan) != expected:
        raise ValueError("Il piano dei metodi non coincide con il piano congelato.")


def validate_llm_decisions(
    records: Sequence[Mapping[str, Any]],
    *,
    method_id: str,
    split: str,
    catalog: ConfigurationCatalog,
    manifest: Mapping[str, Any],
    capacities: Mapping[str, int],
    method_config: Mapping[str, Any],
    method_config_sha256: str,
) -> list[dict[str, Any]]:
    """Accetta una sola decisione terminale per ogni circuito."""
    if method_id not in LLM_METHOD_IDS:
        raise ValueError(f"Metodo LLM sconosciuto: {method_id}.")
    circuits = split_circuits(split, manifest)
    expected = {
        (str(item["circuit_id"]), str(item["source_sha256"])): item
        for item in circuits
    }
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    max_attempts = int(method_config["methods"][method_id]["max_attempts"])
    required = {
        "schema_version",
        "experiment_id",
        "protocol_version",
        "method_id",
        "method_config_sha256",
        "split",
        "circuit_id",
        "source_sha256",
        "status",
        "selected_device_id",
        "selected_config_id",
        "attempt_count",
        "raw_response_sha256",
        "timings_seconds",
        "usage",
        "failure",
    }
    for index, raw in enumerate(records):
        record = dict(raw)
        if set(record) != required:
            raise ValueError(
                f"Decisione {index}: campi mancanti/inattesi: "
                f"{sorted(required - set(record))}/{sorted(set(record) - required)}."
            )
        if (
            record["schema_version"] != "1.0.0"
            or record["experiment_id"] != EXPERIMENT_ID
            or record["protocol_version"] != PROTOCOL_VERSION
            or record["method_id"] != method_id
            or record["method_config_sha256"] != method_config_sha256
            or record["split"] != split
        ):
            raise ValueError(f"Decisione {index}: identità del protocollo non conforme.")
        key = (str(record["circuit_id"]), str(record["source_sha256"]))
        circuit = expected.get(key)
        if circuit is None or key in by_key:
            raise ValueError(f"Decisione {index}: circuito fuori piano o duplicato.")
        attempts = record["attempt_count"]
        if (
            isinstance(attempts, bool)
            or not isinstance(attempts, int)
            or not 1 <= attempts <= max_attempts
        ):
            raise ValueError(f"Decisione {index}: attempt_count non valido.")
        status = record["status"]
        if status == "success":
            device_id = record["selected_device_id"]
            config_id = record["selected_config_id"]
            if device_id not in catalog.supported_device_ids:
                raise ValueError(f"Decisione {index}: device fuori catalogo.")
            if config_id not in catalog.by_id:
                raise ValueError(f"Decisione {index}: configurazione fuori catalogo.")
            if int(circuit["num_qubits"]) > int(capacities[str(device_id)]):
                raise ValueError(f"Decisione {index}: device incompatibile.")
            if record["failure"] is not None:
                raise ValueError(f"Decisione {index}: failure presente su success.")
        elif status in {"failure", "timeout"}:
            if (
                record["selected_device_id"] is not None
                or record["selected_config_id"] is not None
                or not isinstance(record["failure"], dict)
            ):
                raise ValueError(f"Decisione {index}: fallimento incoerente.")
        else:
            raise ValueError(f"Decisione {index}: status non valido.")
        by_key[key] = record
    if set(by_key) != set(expected):
        missing = sorted(set(expected) - set(by_key))
        raise ValueError(f"Decisioni incomplete per {method_id}: {len(missing)} mancanti.")
    return [by_key[key] for key in sorted(by_key)]


def validate_qcompile_runs(
    records: Sequence[Mapping[str, Any]],
    *,
    split: str,
    manifest: Mapping[str, Any],
    expected_model_set_sha256: str | None = None,
) -> list[dict[str, Any]]:
    """Richiede tre esiti qcompile terminali e attestati per circuito."""
    circuits = split_circuits(split, manifest)
    expected = {
        (str(item["circuit_id"]), str(item["source_sha256"])): item
        for item in circuits
    }
    grouped: dict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
    for index, raw in enumerate(records):
        record = dict(raw)
        if (
            record.get("schema_version") != "1.0.0"
            or record.get("experiment_id") != EXPERIMENT_ID
            or record.get("protocol_version") != PROTOCOL_VERSION
            or record.get("method_id") != QCOMPILE_METHOD_ID
            or record.get("split") != split
        ):
            raise ValueError(f"qcompile {index}: identità del protocollo non conforme.")
        key = (str(record.get("circuit_id")), str(record.get("source_sha256")))
        if key not in expected:
            raise ValueError(f"qcompile {index}: circuito fuori split.")
        repetition = record.get("repetition_index")
        if isinstance(repetition, bool) or repetition not in {0, 1, 2}:
            raise ValueError(f"qcompile {index}: ripetizione non valida.")
        if repetition in grouped[key]:
            raise ValueError(f"qcompile {index}: ripetizione duplicata.")
        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            raise ValueError(f"qcompile {index}: provenienza mancante.")
        model_hashes = provenance.get("model_hashes")
        if (
            provenance.get("source_manifest_sha256")
            != (
                file_sha256(SOURCE_MANIFEST_V2)
                if SOURCE_MANIFEST_V2.is_file()
                else None
            )
            or provenance.get("software") != EXPECTED_PACKAGE_VERSIONS
            or provenance.get("controlled_seed") is not None
            or provenance.get("repetition_semantics")
            != "fresh_process_without_exposed_seed"
            or provenance.get("timeout_seconds")
            != COMPILATION_TIMEOUT_SECONDS
            or not isinstance(model_hashes, dict)
            or len(model_hashes) != 6
            or any(
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
                for digest in model_hashes.values()
            )
            or provenance.get("model_set_sha256") != stable_sha256(model_hashes)
            or (
                expected_model_set_sha256 is not None
                and provenance.get("model_set_sha256")
                != expected_model_set_sha256
            )
        ):
            raise ValueError(f"qcompile {index}: provenienza non conforme.")
        expected_run_id = "mqt_run_" + stable_sha256(
            {
                "experiment_id": EXPERIMENT_ID,
                "protocol_version": PROTOCOL_VERSION,
                "method_id": QCOMPILE_METHOD_ID,
                "split": split,
                "circuit_id": record["circuit_id"],
                "source_sha256": record["source_sha256"],
                "repetition_index": repetition,
                "model_set_sha256": provenance["model_set_sha256"],
            }
        )
        if record.get("run_id") != expected_run_id:
            raise ValueError(f"qcompile {index}: run_id non conforme.")
        status = record.get("status")
        if status == "success":
            device_id = record.get("selected_device_id")
            score = record.get("score")
            validation = record.get("target_validation")
            passes = record.get("passes")
            if (
                device_id not in FROZEN_DEVICES
                or not isinstance(score, (int, float))
                or not math.isfinite(float(score))
                or not isinstance(validation, dict)
                or validation.get("is_executable_on_target") is not True
                or record.get("target_sha256") != FROZEN_TARGET_SHA256[device_id]
                or not isinstance(passes, list)
                or not passes
                or passes[-1] != "terminate"
                or record.get("failure") is not None
            ):
                raise ValueError(f"qcompile {index}: successo non attestato.")
        elif status in {"failure", "timeout"}:
            failure = record.get("failure")
            if (
                record.get("selected_device_id") is not None
                or record.get("target_sha256") is not None
                or record.get("score") is not None
                or not isinstance(failure, dict)
                or (
                    status == "timeout"
                    and failure.get("category") != "compilation_timeout"
                )
            ):
                raise ValueError(f"qcompile {index}: esito negativo incoerente.")
        else:
            raise ValueError(f"qcompile {index}: status non terminale.")
        grouped[key][int(repetition)] = record
    for key in expected:
        if set(grouped.get(key, {})) != {0, 1, 2}:
            raise ValueError(f"qcompile incompleto per {key[0]}.")
    return [
        grouped[key][repetition]
        for key in sorted(grouped)
        for repetition in range(3)
    ]


def validate_qiskit_matrix(
    runs: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
    *,
    split: str,
    catalog: ConfigurationCatalog,
    manifest: Mapping[str, Any],
    capacities: Mapping[str, int],
) -> tuple[
    dict[tuple[str, str, str, int], dict[str, Any]],
    dict[tuple[str, str, str], dict[str, Any]],
]:
    """Ricalcola matrice e aggregati Qiskit, rifiutando provenienza legacy."""
    circuits = split_circuits(split, manifest)
    circuit_by_hash = {
        str(item["source_sha256"]): item for item in circuits
    }
    if (
        catalog.experiment_id != EXPERIMENT_ID
        or catalog.protocol_version != PROTOCOL_VERSION
        or dict(catalog.required_versions) != EXPECTED_PACKAGE_VERSIONS
    ):
        raise ValueError("Catalogo Qiskit non conforme al protocollo v2.")
    expected_configurations = {
        configuration.config_id: {
            **configuration.to_dict(),
            "catalog_id": catalog.catalog_id,
        }
        for configuration in catalog.configurations
    }
    expected_summaries: set[tuple[str, str, str]] = set()
    expected_runs: set[tuple[str, str, str, int]] = set()
    for circuit in circuits:
        source_hash = str(circuit["source_sha256"])
        for device_id in catalog.supported_device_ids:
            if int(circuit["num_qubits"]) > int(capacities[device_id]):
                continue
            for configuration in catalog.configurations:
                summary_key = (source_hash, device_id, configuration.config_id)
                expected_summaries.add(summary_key)
                for seed in catalog.seeds:
                    expected_runs.add((*summary_key, int(seed)))

    summary_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in summaries:
        if raw.get("split") != split:
            continue
        circuit = raw.get("circuit") or {}
        device = raw.get("device") or {}
        configuration = raw.get("configuration") or {}
        key = (
            str(circuit.get("source_sha256")),
            str(device.get("device_id")),
            str(configuration.get("config_id")),
        )
        expected_circuit = circuit_by_hash.get(key[0])
        expected_configuration = expected_configurations.get(key[2])
        expected_summary_id = None
        if (
            key in expected_summaries
            and expected_circuit is not None
            and expected_configuration is not None
        ):
            expected_summary_id = stable_id(
                "summary",
                {
                    "circuit_id": expected_circuit["circuit_id"],
                    "source_sha256": expected_circuit["source_sha256"],
                    "device_id": key[1],
                    "configuration": catalog.by_id[key[2]].to_dict(),
                    "objective": catalog.objective["name"],
                    "catalog_id": catalog.catalog_id,
                },
            )
        if (
            raw.get("schema_version") != AGGREGATE_SCHEMA_VERSION
            or raw.get("experiment_id") != EXPERIMENT_ID
            or raw.get("protocol_version") != PROTOCOL_VERSION
            or raw.get("dataset_scope") != "full"
            or raw.get("objective") != dict(catalog.objective)
            or key not in expected_summaries
            or key in summary_index
            or expected_circuit is None
            or any(
                circuit.get(field) != expected_circuit.get(field)
                for field in (
                    "circuit_id",
                    "source_sha256",
                    "split",
                    "num_qubits",
                )
            )
            or device.get("target_sha256") != FROZEN_TARGET_SHA256.get(key[1])
            or device.get("num_qubits") != capacities.get(key[1])
            or configuration != expected_configuration
            or raw.get("summary_id") != expected_summary_id
            or raw.get("ranking_metric")
            != "median_expected_fidelity_across_seeds"
        ):
            raise ValueError(f"Aggregato Qiskit v2 non conforme: {key}.")
        summary_index[key] = dict(raw)

    run_index: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for raw in runs:
        if raw.get("split") != split:
            continue
        circuit = raw.get("circuit") or {}
        device = raw.get("device") or {}
        configuration = raw.get("configuration") or {}
        seed = raw.get("seed_transpiler")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("Tentativo Qiskit v2 con seed non intero.")
        key = (
            str(circuit.get("source_sha256")),
            str(device.get("device_id")),
            str(configuration.get("config_id")),
            seed,
        )
        provenance = raw.get("provenance") or {}
        expected_circuit = circuit_by_hash.get(key[0])
        expected_configuration = expected_configurations.get(key[2])
        expected_run_id = None
        if (
            key in expected_runs
            and expected_circuit is not None
            and expected_configuration is not None
        ):
            expected_run_id = make_run_id(
                expected_circuit,
                catalog.by_id[key[2]].to_dict(),
                seed,
                device_id=key[1],
                target_sha256=FROZEN_TARGET_SHA256[key[1]],
                objective=catalog.objective,
                versions=EXPECTED_PACKAGE_VERSIONS,
                catalog_id=catalog.catalog_id,
                experiment_id=EXPERIMENT_ID,
                protocol_version=PROTOCOL_VERSION,
                fixed_transpile_options=catalog.fixed_transpile_options,
                execution_policy=catalog.execution_policy,
            )
        if (
            raw.get("schema_version") != SCHEMA_VERSION
            or raw.get("experiment_id") != EXPERIMENT_ID
            or raw.get("protocol_version") != PROTOCOL_VERSION
            or raw.get("dataset_scope") != "full"
            or raw.get("objective") != dict(catalog.objective)
            or key not in expected_runs
            or key in run_index
            or expected_circuit is None
            or any(
                circuit.get(field) != expected_circuit.get(field)
                for field in (
                    "circuit_id",
                    "source_sha256",
                    "split",
                    "num_qubits",
                )
            )
            or device.get("target_sha256") != FROZEN_TARGET_SHA256.get(key[1])
            or device.get("num_qubits") != capacities.get(key[1])
            or configuration != expected_configuration
            or raw.get("run_id") != expected_run_id
            or provenance.get("resume_contract_sha256")
            != str(expected_run_id).removeprefix("run_")
            or provenance.get("versions") != EXPECTED_PACKAGE_VERSIONS
            or provenance.get("compiler") != "qiskit.transpile"
            or provenance.get("fixed_transpile_options")
            != dict(catalog.fixed_transpile_options)
            or provenance.get("execution_policy")
            != dict(catalog.execution_policy)
            or provenance.get("generator") != "qiskit_dataset.generation"
        ):
            raise ValueError(f"Tentativo Qiskit v2 non conforme: {key}.")
        status = raw.get("status")
        score = raw.get("score")
        failure = raw.get("failure")
        if status == "success":
            validation = raw.get("target_validation")
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(float(score))
                or raw.get("phase") != "completed"
                or not isinstance(validation, dict)
                or validation.get("is_executable_on_target") is not True
                or not isinstance(raw.get("compiled_circuit"), dict)
                or failure is not None
            ):
                raise ValueError(f"Tentativo Qiskit v2 incoerente: {key}.")
        elif status in {"failure", "timeout"}:
            if (
                score is not None
                or raw.get("compiled_circuit") is not None
                or not isinstance(failure, dict)
                or not isinstance(failure.get("category"), str)
                or not failure["category"]
                or (
                    status == "timeout"
                    and (
                        failure.get("category") != "timeout"
                        or failure.get("timeout_seconds")
                        != COMPILATION_TIMEOUT_SECONDS
                    )
                )
                or (
                    status == "failure"
                    and failure.get("category") == "timeout"
                )
            ):
                raise ValueError(f"Tentativo Qiskit v2 incoerente: {key}.")
        else:
            raise ValueError(
                f"Tentativo Qiskit v2 con stato non terminale: {key}."
            )
        run_index[key] = dict(raw)
    if set(summary_index) != expected_summaries:
        raise ValueError(
            f"Matrice aggregata incompleta: {len(summary_index)}/{len(expected_summaries)}."
        )
    if set(run_index) != expected_runs:
        raise ValueError(f"Matrice raw incompleta: {len(run_index)}/{len(expected_runs)}.")
    for key, summary in summary_index.items():
        linked_runs = [
            run_index[(*key, int(seed))]
            for seed in catalog.seeds
        ]
        successes = [run for run in linked_runs if run["status"] == "success"]
        failures = [run for run in linked_runs if run["status"] == "failure"]
        timeouts = [run for run in linked_runs if run["status"] == "timeout"]
        expected_run_ids = [str(run["run_id"]) for run in linked_runs]
        expected_observations = [
            {
                "run_id": str(run["run_id"]),
                "seed_transpiler": int(run["seed_transpiler"]),
                "score": float(run["score"]),
            }
            for run in successes
        ]
        expected_seeds = {
            "expected": list(catalog.seeds),
            "observed": list(catalog.seeds),
            "successful": [
                int(run["seed_transpiler"]) for run in successes
            ],
            "failed": [int(run["seed_transpiler"]) for run in failures],
            "timed_out": [int(run["seed_transpiler"]) for run in timeouts],
        }
        attempts = summary.get("attempts") or {}
        expected_attempt_fields = {
            "expected_count": len(catalog.seeds),
            "observed_count": len(linked_runs),
            "success_count": len(successes),
            "failure_count": len(failures),
            "timeout_count": len(timeouts),
            "complete": True,
            "success_rate": len(successes) / len(linked_runs),
        }
        scores = [float(run["score"]) for run in successes]
        expected_ranking_score = median(scores) if scores else None
        observed_ranking_score = summary.get("ranking_score")
        score_matches = (
            observed_ranking_score is None
            if expected_ranking_score is None
            else (
                not isinstance(observed_ranking_score, bool)
                and isinstance(observed_ranking_score, (int, float))
                and math.isfinite(float(observed_ranking_score))
                and float(observed_ranking_score) == expected_ranking_score
            )
        )
        if (
            summary.get("run_ids") != expected_run_ids
            or summary.get("score_observations") != expected_observations
            or summary.get("seeds") != expected_seeds
            or any(
                attempts.get(field) != value
                for field, value in expected_attempt_fields.items()
            )
            or summary.get("eligible_for_ranking")
            is not (len(successes) == len(linked_runs))
            or not score_matches
        ):
            raise ValueError(
                f"Aggregato Qiskit non allineato ai raw run: {key}."
            )
    return run_index, summary_index


def _result(
    *,
    method_id: str,
    split: str,
    circuit: Mapping[str, Any],
    status: str,
    device_id: str | None,
    config_id: str | None,
    repetitions: Sequence[Mapping[str, Any]],
    score: float | None,
    failure_category: str | None,
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Crea il record condiviso da tutti i metodi."""
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
        "method_id": method_id,
        "split": split,
        "circuit_id": circuit["circuit_id"],
        "source_sha256": circuit["source_sha256"],
        "status": status,
        "selected_device_id": device_id,
        "selected_config_id": config_id,
        "repetitions": [dict(item) for item in repetitions],
        "score": score,
        "oracle_score": None,
        "regret_absolute": None,
        "regret_relative": None,
        "failure_category": failure_category,
        "provenance": dict(provenance),
    }


def _qiskit_repetitions(
    run_index: Mapping[tuple[str, str, str, int], Mapping[str, Any]],
    *,
    source_hash: str,
    device_id: str,
    config_id: str,
    seeds: Sequence[int],
) -> list[dict[str, Any]]:
    """Rende omogenee le tre ripetizioni Qiskit di una coppia."""
    result = []
    for repetition_index, seed in enumerate(seeds):
        run = run_index[(source_hash, device_id, config_id, int(seed))]
        result.append(
            {
                "repetition_index": repetition_index,
                "qiskit_seed": int(seed),
                "status": run["status"],
                "score": run["score"],
                "run_id": run["run_id"],
            }
        )
    return result


def _incomplete_status(
    repetitions: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
    """Distingue un timeout osservato da un altro fallimento terminale."""
    if any(item.get("status") == "timeout" for item in repetitions):
        return "timeout", "compilation_timeout"
    return "failure", "compilation_failure"


def evaluate_common_methods(
    *,
    split: str,
    catalog: ConfigurationCatalog,
    manifest: Mapping[str, Any],
    plan: Mapping[str, Any],
    capacities: Mapping[str, int],
    qiskit_runs: Sequence[Mapping[str, Any]],
    qiskit_summaries: Sequence[Mapping[str, Any]],
    llm_decisions: Mapping[str, Sequence[Mapping[str, Any]]],
    qcompile_runs: Sequence[Mapping[str, Any]],
    method_config_sha256: str,
) -> list[dict[str, Any]]:
    """Produce record omogenei senza eliminare fallimenti."""
    run_index, summary_index = validate_qiskit_matrix(
        qiskit_runs,
        qiskit_summaries,
        split=split,
        catalog=catalog,
        manifest=manifest,
        capacities=capacities,
    )
    circuits = split_circuits(split, manifest)
    by_hash = {str(item["source_sha256"]): item for item in circuits}
    device_order = {
        device_id: index for index, device_id in enumerate(catalog.supported_device_ids)
    }
    config_order = {
        item.config_id: index for index, item in enumerate(catalog.configurations)
    }
    results: list[dict[str, Any]] = []
    oracle_by_hash: dict[str, dict[str, Any]] = {}

    for circuit in circuits:
        source_hash = str(circuit["source_sha256"])
        source_runs = [
            run
            for key, run in run_index.items()
            if key[0] == source_hash
        ]
        eligible = [
            summary
            for key, summary in summary_index.items()
            if key[0] == source_hash
            and summary.get("eligible_for_ranking") is True
            and isinstance(summary.get("ranking_score"), (int, float))
        ]
        eligible.sort(
            key=lambda item: (
                -float(item["ranking_score"]),
                device_order[str(item["device"]["device_id"])],
                config_order[str(item["configuration"]["config_id"])],
                str(item["device"]["device_id"]),
                str(item["configuration"]["config_id"]),
            )
        )
        oracle_matrix_complete = bool(source_runs) and all(
            run.get("status") == "success" for run in source_runs
        )
        if eligible and oracle_matrix_complete:
            winner = eligible[0]
            oracle = _result(
                method_id=ORACLE_METHOD_ID,
                split=split,
                circuit=circuit,
                status="success",
                device_id=str(winner["device"]["device_id"]),
                config_id=str(winner["configuration"]["config_id"]),
                repetitions=[
                    {
                        "repetition_index": index,
                        "qiskit_seed": observation["seed_transpiler"],
                        "status": "success",
                        "score": observation["score"],
                        "run_id": observation["run_id"],
                    }
                    for index, observation in enumerate(
                        winner["score_observations"]
                    )
                ],
                score=float(winner["ranking_score"]),
                failure_category=None,
                provenance={"summary_id": winner["summary_id"]},
            )
        else:
            oracle_status, _ = _incomplete_status(source_runs)
            oracle = _result(
                method_id=ORACLE_METHOD_ID,
                split=split,
                circuit=circuit,
                status=oracle_status,
                device_id=None,
                config_id=None,
                repetitions=[],
                score=None,
                failure_category=(
                    "oracle_timeout"
                    if oracle_status == "timeout"
                    else "oracle_incomplete"
                ),
                provenance={},
            )
        oracle_by_hash[source_hash] = oracle
        results.append(oracle)

    for config_id in QISKIT_DEFAULT_CONFIG_IDS:
        for device_id in catalog.supported_device_ids:
            method_id = f"qiskit_{config_id}__{device_id}"
            for circuit in circuits:
                source_hash = str(circuit["source_sha256"])
                if int(circuit["num_qubits"]) > int(capacities[device_id]):
                    results.append(
                        _result(
                            method_id=method_id,
                            split=split,
                            circuit=circuit,
                            status="not_applicable",
                            device_id=device_id,
                            config_id=config_id,
                            repetitions=[],
                            score=None,
                            failure_category="not_applicable_width",
                            provenance={},
                        )
                    )
                    continue
                summary = summary_index[(source_hash, device_id, config_id)]
                success = summary.get("eligible_for_ranking") is True
                repetitions = _qiskit_repetitions(
                    run_index,
                    source_hash=source_hash,
                    device_id=device_id,
                    config_id=config_id,
                    seeds=catalog.seeds,
                )
                status, failure_category = (
                    ("success", None)
                    if success
                    else _incomplete_status(repetitions)
                )
                results.append(
                    _result(
                        method_id=method_id,
                        split=split,
                        circuit=circuit,
                        status=status,
                        device_id=device_id,
                        config_id=config_id,
                        repetitions=repetitions,
                        score=float(summary["ranking_score"]) if success else None,
                        failure_category=failure_category,
                        provenance={"summary_id": summary["summary_id"]},
                    )
                )

    random_rows = {
        str(row["source_sha256"]): row
        for row in plan["random_selection"]["rows"]
    }
    for circuit in circuits:
        source_hash = str(circuit["source_sha256"])
        repetitions = []
        scores = []
        for choice in random_rows[source_hash]["repetitions"]:
            key = (
                source_hash,
                str(choice["selected_device_id"]),
                str(choice["selected_config_id"]),
                int(choice["qiskit_seed"]),
            )
            run = run_index[key]
            repetitions.append(
                {
                    **dict(choice),
                    "status": run["status"],
                    "score": run["score"],
                    "run_id": run["run_id"],
                }
            )
            if run["status"] == "success":
                scores.append(float(run["score"]))
        success = len(scores) == 3
        status, failure_category = (
            ("success", None)
            if success
            else _incomplete_status(repetitions)
        )
        results.append(
            _result(
                method_id=RANDOM_METHOD_ID,
                split=split,
                circuit=circuit,
                status=status,
                device_id=None,
                config_id=None,
                repetitions=repetitions,
                score=median(scores) if success else None,
                failure_category=failure_category,
                provenance={
                    "plan_sha256": plan["plan_sha256"],
                    "selection_seed": RANDOM_SELECTION_SEED,
                },
            )
        )

    for method_id in LLM_METHOD_IDS:
        decisions = {
            str(record["source_sha256"]): record
            for record in llm_decisions[method_id]
        }
        for circuit in circuits:
            source_hash = str(circuit["source_sha256"])
            decision = decisions[source_hash]
            if decision["status"] != "success":
                results.append(
                    _result(
                        method_id=method_id,
                        split=split,
                        circuit=circuit,
                        status=str(decision["status"]),
                        device_id=None,
                        config_id=None,
                        repetitions=[],
                        score=None,
                        failure_category=str(
                            decision["failure"].get("category", "llm_failure")
                        ),
                        provenance={
                            "attempt_count": decision["attempt_count"],
                            "raw_response_sha256": decision["raw_response_sha256"],
                            "method_config_sha256": method_config_sha256,
                        },
                    )
                )
                continue
            device_id = str(decision["selected_device_id"])
            config_id = str(decision["selected_config_id"])
            summary = summary_index[(source_hash, device_id, config_id)]
            success = summary.get("eligible_for_ranking") is True
            repetitions = _qiskit_repetitions(
                run_index,
                source_hash=source_hash,
                device_id=device_id,
                config_id=config_id,
                seeds=catalog.seeds,
            )
            status, failure_category = (
                ("success", None)
                if success
                else _incomplete_status(repetitions)
            )
            results.append(
                _result(
                    method_id=method_id,
                    split=split,
                    circuit=circuit,
                    status=status,
                    device_id=device_id,
                    config_id=config_id,
                    repetitions=repetitions,
                    score=float(summary["ranking_score"]) if success else None,
                    failure_category=failure_category,
                    provenance={
                        "attempt_count": decision["attempt_count"],
                        "raw_response_sha256": decision["raw_response_sha256"],
                        "method_config_sha256": method_config_sha256,
                        "summary_id": summary["summary_id"],
                    },
                )
            )

    grouped_qcompile: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in qcompile_runs:
        grouped_qcompile[str(record["source_sha256"])].append(record)
    for source_hash, circuit in by_hash.items():
        repetitions = sorted(
            grouped_qcompile[source_hash],
            key=lambda item: int(item["repetition_index"]),
        )
        scores = [
            float(item["score"])
            for item in repetitions
            if item["status"] == "success"
        ]
        success = len(scores) == 3
        status, failure_category = (
            ("success", None)
            if success
            else _incomplete_status(repetitions)
        )
        selected_devices = {
            str(item["selected_device_id"])
            for item in repetitions
            if item["status"] == "success"
        }
        results.append(
            _result(
                method_id=QCOMPILE_METHOD_ID,
                split=split,
                circuit=circuit,
                status=status,
                device_id=(
                    next(iter(selected_devices))
                    if success and len(selected_devices) == 1
                    else None
                ),
                config_id=None,
                repetitions=repetitions,
                score=median(scores) if success else None,
                failure_category=failure_category,
                provenance={"policy_deterministic": False, "controlled_seed": None},
            )
        )

    for result in results:
        oracle = oracle_by_hash[str(result["source_sha256"])]
        oracle_score = oracle["score"]
        result["oracle_score"] = oracle_score
        if result["score"] is not None and oracle_score is not None:
            absolute = float(oracle_score) - float(result["score"])
            result["regret_absolute"] = absolute
            result["regret_relative"] = (
                absolute / float(oracle_score)
                if float(oracle_score) != 0.0
                else None
            )
        if result["method_id"] == ORACLE_METHOD_ID and result["score"] is not None:
            result["regret_absolute"] = 0.0
            result["regret_relative"] = (
                0.0 if float(result["score"]) != 0.0 else None
            )

    method_order = {
        ORACLE_METHOD_ID: 0,
        RANDOM_METHOD_ID: 1,
        **{method_id: index + 2 for index, method_id in enumerate(LLM_METHOD_IDS)},
        QCOMPILE_METHOD_ID: 5,
    }
    results.sort(
        key=lambda item: (
            str(item["circuit_id"]),
            method_order.get(str(item["method_id"]), 10),
            str(item["method_id"]),
        )
    )
    return results


def summarize_results(
    results: Sequence[Mapping[str, Any]],
    *,
    split: str,
    input_fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    """Mantiene visibili fallimenti, non applicabilità e denominatori."""
    by_method: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in results:
        by_method[str(record["method_id"])].append(record)
    methods: dict[str, Any] = {}
    for method_id, records in sorted(by_method.items()):
        applicable = [item for item in records if item["status"] != "not_applicable"]
        successes = [item for item in applicable if item["status"] == "success"]
        regrets = [
            float(item["regret_absolute"])
            for item in successes
            if item.get("regret_absolute") is not None
        ]
        methods[method_id] = {
            "records": len(records),
            "applicable": len(applicable),
            "successes": len(successes),
            "failures": sum(item["status"] == "failure" for item in applicable),
            "timeouts": sum(item["status"] == "timeout" for item in applicable),
            "not_applicable": sum(
                item["status"] == "not_applicable" for item in records
            ),
            "success_rate": len(successes) / len(applicable) if applicable else None,
            "median_regret_absolute": median(regrets) if regrets else None,
            "failure_categories": dict(
                sorted(
                    Counter(
                        str(item["failure_category"])
                        for item in records
                        if item.get("failure_category") is not None
                    ).items()
                )
            ),
        }
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "protocol_version": PROTOCOL_VERSION,
        "split": split,
        "status": "complete",
        "circuit_count": EXPECTED_SPLIT_COUNTS[split],
        "methods": methods,
        "input_fingerprints": dict(sorted(input_fingerprints.items())),
    }

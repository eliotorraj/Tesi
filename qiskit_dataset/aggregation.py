"""Riunisce le viste dei singoli dispositivi senza modificarle."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .catalog import ConfigurationCatalog
from .core import (
    SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    SPLIT_ORDER,
    atomic_json_write,
    atomic_jsonl_write,
    canonical_json,
    dataset_scope_root,
    read_jsonl,
    resolve_circuit_source,
    sha256_file,
)
from .reporting import write_failure_csv
from .views import (
    AGGREGATE_SCHEMA_VERSION,
    RAG_SCHEMA_VERSION,
    build_rag_examples,
)


GLOBAL_VIEW_DIRECTORY = "global"
REQUIRED_DEVICE_FILES = (
    "split_manifest.json",
    "qiskit_runs.jsonl",
    "qiskit_configuration_aggregates.jsonl",
)


def _load_json(path: Path) -> dict[str, Any]:
    """Legge un file JSON richiesto e controlla che contenga un oggetto."""
    import json

    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} non contiene un oggetto JSON.")
    return value


def _shared_circuit_identity(circuit: Mapping[str, Any]) -> str:
    """Rappresenta un circuito senza la compatibilità specifica del device."""
    return canonical_json(
        {
            key: value
            for key, value in circuit.items()
            if key != "device_compatibility"
        }
    )


def _available_devices(
    scope_root: Path,
    catalog: ConfigurationCatalog,
) -> list[str]:
    """Elenca i dispositivi per cui sono presenti tutti i file necessari."""
    return [
        device_id
        for device_id in catalog.supported_device_ids
        if all(
            (scope_root / device_id / file_name).is_file()
            for file_name in REQUIRED_DEVICE_FILES
        )
    ]


def _validate_manifest(
    manifest: Mapping[str, Any],
    *,
    device_id: str,
    scope: str,
    catalog: ConfigurationCatalog,
) -> dict[str, str]:
    """Controlla un manifest e i circuiti condivisi a cui fa riferimento."""
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"Versione schema inattesa nel manifest di {device_id}.")
    if manifest.get("device_id") != device_id:
        raise ValueError(f"Device incoerente nel manifest di {device_id}.")
    if manifest.get("dataset_scope") != scope:
        raise ValueError(f"Scope incoerente nel manifest di {device_id}.")
    if manifest.get("catalog_id") != catalog.catalog_id:
        raise ValueError(f"Catalogo incoerente nel manifest di {device_id}.")
    if manifest.get("experiment_id") != catalog.experiment_id:
        raise ValueError(f"Esperimento incoerente nel manifest di {device_id}.")
    if manifest.get("objective") != catalog.objective:
        raise ValueError(f"Objective incoerente nel manifest di {device_id}.")
    if list(manifest.get("seeds", [])) != list(catalog.seeds):
        raise ValueError(f"Seed incoerenti nel manifest di {device_id}.")
    storage = manifest.get("circuit_storage") or {}
    if (
        storage.get("layout") != "shared_scope_root"
        or storage.get("root_ref") != "circuits"
        or storage.get("source_ref_base") != "scope_root"
        or storage.get("integrity_field") != "source_sha256"
    ):
        raise ValueError(
            f"Storage circuiti non condiviso o non riconosciuto per {device_id}."
        )

    device_num_qubits = int(manifest["device_num_qubits"])
    identities: dict[str, str] = {}
    for circuit in manifest.get("circuits", []):
        circuit_id = str(circuit.get("circuit_id", ""))
        if not circuit_id or circuit_id in identities:
            raise ValueError(f"circuit_id mancante o duplicato per {device_id}.")
        source_ref = str(circuit.get("source_ref", ""))
        source_path = resolve_circuit_source(
            str(catalog.objective["name"]),
            scope,
            source_ref,
            catalog.experiment_id,
        )
        if not source_path.is_file():
            raise FileNotFoundError(f"Circuito condiviso mancante: {source_path}.")
        if sha256_file(source_path) != circuit.get("source_sha256"):
            raise ValueError(f"SHA-256 circuito incoerente: {source_path}.")
        compatibility = circuit.get("device_compatibility") or {}
        expected_compatible = int(circuit["num_qubits"]) <= device_num_qubits
        if (
            compatibility.get("compatible") is not expected_compatible
            or compatibility.get("device_num_qubits") != device_num_qubits
        ):
            raise ValueError(
                f"Compatibilità incoerente per {device_id}/{circuit_id}."
            )
        identities[circuit_id] = _shared_circuit_identity(circuit)
    if not identities:
        raise ValueError(f"Manifest senza circuiti per {device_id}.")
    return identities


def _validate_device_records(
    records: Sequence[Mapping[str, Any]],
    *,
    device_id: str,
    scope: str,
    objective_name: str,
    record_kind: str,
    catalog: ConfigurationCatalog,
    expected_schema_version: str,
) -> None:
    """Controlla i campi comuni dei tentativi o degli aggregati di un device."""
    for index, record in enumerate(records, start=1):
        location = f"{device_id}/{record_kind}:{index}"
        if record.get("schema_version") != expected_schema_version:
            raise ValueError(f"{location}: versione schema incoerente.")
        if record.get("dataset_scope") != scope:
            raise ValueError(f"{location}: scope incoerente.")
        objective = record.get("objective") or {}
        if (
            objective.get("name") != objective_name
            or objective.get("direction") != catalog.objective.get("direction")
        ):
            raise ValueError(f"{location}: objective incoerente.")
        device = record.get("device") or {}
        if device.get("device_id") != device_id:
            raise ValueError(f"{location}: device incoerente.")
        configuration = record.get("configuration") or {}
        if configuration.get("catalog_id") != catalog.catalog_id:
            raise ValueError(f"{location}: catalog_id incoerente.")
        try:
            allowed = catalog.require_allowed(
                int(configuration["optimization_level"]),
                configuration.get("layout_method"),
                configuration.get("routing_method"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{location}: configurazione non valida.") from error
        if configuration.get("config_id") != allowed.config_id:
            raise ValueError(f"{location}: config_id incoerente.")
        if record_kind == "runs":
            if record.get("status") not in {"success", "failure", "timeout"}:
                raise ValueError(f"{location}: stato non valido.")
            if record.get("seed_transpiler") not in catalog.seeds:
                raise ValueError(f"{location}: seed fuori catalogo.")
        elif record_kind == "aggregates":
            if record.get("ranking_metric") != (
                "median_expected_fidelity_across_seeds"
            ):
                raise ValueError(f"{location}: metrica di ranking incoerente.")
        else:
            raise ValueError(f"Tipo record non supportato: {record_kind!r}.")


def _validate_records_against_manifest(
    records: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    *,
    device_id: str,
) -> None:
    """Verifica che i record descrivano ancora i circuiti del manifest."""
    circuits = {
        str(circuit["circuit_id"]): circuit
        for circuit in manifest.get("circuits", [])
    }
    target_identity: str | None = None
    for index, record in enumerate(records, start=1):
        circuit = record.get("circuit") or {}
        circuit_id = str(circuit.get("circuit_id", ""))
        expected = circuits.get(circuit_id)
        if expected is None:
            raise ValueError(
                f"{device_id}:{index}: circuito fuori manifest: {circuit_id!r}."
            )
        expected_identity = _shared_circuit_identity(expected)
        observed_identity = _shared_circuit_identity(circuit)
        if observed_identity != expected_identity:
            raise ValueError(
                f"{device_id}:{index}: metadati incoerenti per {circuit_id}."
            )
        if record.get("split") != expected.get("split"):
            raise ValueError(f"{device_id}:{index}: split incoerente.")

        device = record.get("device") or {}
        if device.get("num_qubits") != manifest.get("device_num_qubits"):
            raise ValueError(f"{device_id}:{index}: larghezza target incoerente.")
        current_target_identity = canonical_json(device)
        if target_identity is None:
            target_identity = current_target_identity
        elif current_target_identity != target_identity:
            raise ValueError(
                f"{device_id}:{index}: snapshot del target non uniforme."
            )


def _ensure_unique(
    records: Sequence[Mapping[str, Any]],
    identifier: str,
) -> None:
    """Controlla che ogni record abbia un identificatore unico e non vuoto."""
    raw_values = [record.get(identifier) for record in records]
    if any(not isinstance(value, str) or not value for value in raw_values):
        raise ValueError(f"{identifier} mancante nella vista globale.")
    values = [str(value) for value in raw_values]
    if len(values) != len(set(values)):
        duplicates = sorted(
            value
            for value, count in Counter(values).items()
            if count > 1
        )
        raise ValueError(f"{identifier} duplicati nella vista globale: {duplicates}.")


def _validate_circuit_identity(
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Verifica che ogni circuito conservi gli stessi dati tra i device."""
    by_circuit: dict[str, str] = {}
    for summary in summaries:
        circuit = summary.get("circuit") or {}
        circuit_id = str(circuit.get("circuit_id"))
        identity = canonical_json(
            {
                "source_sha256": circuit.get("source_sha256"),
                "split": circuit.get("split"),
                "benchmark_family": circuit.get("benchmark_family"),
                "generator": circuit.get("generator"),
                "num_qubits": circuit.get("num_qubits"),
                "features": circuit.get("features"),
            }
        )
        previous = by_circuit.setdefault(circuit_id, identity)
        if previous != identity:
            raise ValueError(
                f"Metadati circuito incoerenti tra device: {circuit_id}."
            )


def _record_key(record: Mapping[str, Any]) -> tuple[str, str, str]:
    """Costruisce la chiave formata da circuito, dispositivo e configurazione."""
    circuit = record.get("circuit") or {}
    device = record.get("device") or {}
    configuration = record.get("configuration") or {}
    return (
        str(circuit.get("circuit_id", "")),
        str(device.get("device_id", "")),
        str(configuration.get("config_id", "")),
    )


def _validate_summary_run_links(
    runs: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Controlla che ogni aggregato rappresenti esattamente i suoi tentativi."""
    runs_by_key: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    run_by_id: dict[str, Mapping[str, Any]] = {}
    for run in runs:
        run_id = str(run["run_id"])
        run_by_id[run_id] = run
        runs_by_key[_record_key(run)].append(run)

    seen_summary_keys: set[tuple[str, str, str]] = set()
    linked_run_ids: set[str] = set()
    for summary in summaries:
        key = _record_key(summary)
        if not all(key) or key in seen_summary_keys:
            raise ValueError(f"Aggregato mancante o duplicato per la chiave {key}.")
        seen_summary_keys.add(key)
        expected_runs = runs_by_key.get(key, [])
        expected_ids = {str(run["run_id"]) for run in expected_runs}
        raw_summary_ids = summary.get("run_ids")
        if not isinstance(raw_summary_ids, list):
            raise ValueError(f"run_ids non validi per l'aggregato {key}.")
        summary_ids = [str(run_id) for run_id in raw_summary_ids]
        if len(summary_ids) != len(set(summary_ids)):
            raise ValueError(f"run_ids duplicati per l'aggregato {key}.")
        if set(summary_ids) != expected_ids:
            raise ValueError(f"Aggregato non allineato ai raw run per {key}.")
        linked_run_ids.update(summary_ids)

        successful = {
            str(run["run_id"]): run
            for run in expected_runs
            if run.get("status") == "success"
        }
        observations = summary.get("score_observations")
        if not isinstance(observations, list):
            raise ValueError(f"score_observations mancanti per {key}.")
        observed_ids = [str(item.get("run_id", "")) for item in observations]
        if len(observed_ids) != len(set(observed_ids)):
            raise ValueError(f"Osservazioni score duplicate per {key}.")
        if set(observed_ids) != set(successful):
            raise ValueError(f"Osservazioni score non allineate ai success per {key}.")
        for observation in observations:
            run = run_by_id[str(observation["run_id"])]
            if (
                int(observation["seed_transpiler"])
                != int(run["seed_transpiler"])
                or float(observation["score"]) != float(run["score"])
            ):
                raise ValueError(f"Evidence score incoerente per {key}.")

        statuses = Counter(str(run.get("status")) for run in expected_runs)
        attempts = summary.get("attempts") or {}
        expected_counts = {
            "observed_count": len(expected_runs),
            "success_count": statuses["success"],
            "failure_count": statuses["failure"],
            "timeout_count": statuses["timeout"],
        }
        for field, expected in expected_counts.items():
            if attempts.get(field) != expected:
                raise ValueError(f"{field} incoerente per l'aggregato {key}.")

    if linked_run_ids != set(run_by_id):
        raise ValueError("Esistono raw run non rappresentati dagli aggregati.")


def aggregate_device_datasets(
    scope: str,
    catalog: ConfigurationCatalog,
    *,
    top_k: int = 3,
    device_ids: Sequence[str] | None = None,
    require_all_supported: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Riunisce i mini-Dataset selezionati senza modificarne i file."""
    if scope not in {"pilot", "full"}:
        raise ValueError("scope deve essere pilot oppure full.")
    if top_k <= 0:
        raise ValueError("top_k deve essere positivo.")

    objective_name = str(catalog.objective["name"])
    scope_root = dataset_scope_root(
        objective_name,
        scope,
        experiment_id=catalog.experiment_id,
    )
    available = _available_devices(scope_root, catalog)
    if device_ids is None:
        selected_devices = available
    else:
        selected_devices = [catalog.require_device(item) for item in device_ids]
        if len(selected_devices) != len(set(selected_devices)):
            raise ValueError("La lista device contiene duplicati.")
        missing_requested = [
            item for item in selected_devices if item not in available
        ]
        if missing_requested:
            raise FileNotFoundError(
                "Mini-Dataset incompleti o assenti: "
                + ", ".join(missing_requested)
            )
    if not selected_devices:
        raise FileNotFoundError(
            f"Nessun mini-Dataset completo disponibile in {scope_root}."
        )

    missing_supported = [
        item
        for item in catalog.supported_device_ids
        if item not in available
    ]
    if require_all_supported and missing_supported:
        raise FileNotFoundError(
            "Mancano mini-Dataset per i device supportati: "
            + ", ".join(missing_supported)
        )

    all_runs: list[dict[str, Any]] = []
    all_summaries: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    shared_circuit_identities: dict[str, str] | None = None
    for device_id in selected_devices:
        device_root = scope_root / device_id
        manifest_path = device_root / "split_manifest.json"
        runs_path = device_root / "qiskit_runs.jsonl"
        summaries_path = (
            device_root / "qiskit_configuration_aggregates.jsonl"
        )
        manifest = _load_json(manifest_path)
        circuit_identities = _validate_manifest(
            manifest,
            device_id=device_id,
            scope=scope,
            catalog=catalog,
        )
        if shared_circuit_identities is None:
            shared_circuit_identities = circuit_identities
        elif circuit_identities != shared_circuit_identities:
            raise ValueError(
                f"Inventario circuiti incoerente tra i manifest: {device_id}."
            )
        runs = read_jsonl(runs_path)
        summaries = read_jsonl(summaries_path)
        _validate_device_records(
            runs,
            device_id=device_id,
            scope=scope,
            objective_name=objective_name,
            record_kind="runs",
            catalog=catalog,
            expected_schema_version=SCHEMA_VERSION,
        )
        _validate_device_records(
            summaries,
            device_id=device_id,
            scope=scope,
            objective_name=objective_name,
            record_kind="aggregates",
            catalog=catalog,
            expected_schema_version=AGGREGATE_SCHEMA_VERSION,
        )
        _validate_records_against_manifest(
            [*runs, *summaries],
            manifest,
            device_id=device_id,
        )
        _ensure_unique(runs, "run_id")
        _ensure_unique(summaries, "summary_id")
        _validate_summary_run_links(runs, summaries)
        all_runs.extend(runs)
        all_summaries.extend(summaries)
        sources.append(
            {
                "device_id": device_id,
                "manifest_id": manifest.get("manifest_id"),
                "runs": len(runs),
                "configuration_aggregates": len(summaries),
                "files": {
                    "manifest": {
                        "path": str(manifest_path.relative_to(scope_root)),
                        "sha256": sha256_file(manifest_path),
                    },
                    "runs": {
                        "path": str(runs_path.relative_to(scope_root)),
                        "sha256": sha256_file(runs_path),
                    },
                    "configuration_aggregates": {
                        "path": str(summaries_path.relative_to(scope_root)),
                        "sha256": sha256_file(summaries_path),
                    },
                },
            }
        )

    _ensure_unique(all_runs, "run_id")
    _ensure_unique(all_summaries, "summary_id")
    _validate_circuit_identity(all_summaries)

    device_order = {
        device_id: index
        for index, device_id in enumerate(catalog.supported_device_ids)
    }
    configuration_order = {
        configuration.config_id: index
        for index, configuration in enumerate(catalog.configurations)
    }
    all_runs.sort(
        key=lambda run: (
            SPLIT_ORDER[str(run["split"])],
            str(run["circuit"]["circuit_id"]),
            device_order[str(run["device"]["device_id"])],
            configuration_order[str(run["configuration"]["config_id"])],
            int(run["seed_transpiler"]),
        )
    )
    all_summaries.sort(
        key=lambda summary: (
            SPLIT_ORDER[str(summary["split"])],
            str(summary["circuit"]["circuit_id"]),
            device_order[str(summary["device"]["device_id"])],
            configuration_order[
                str(summary["configuration"]["config_id"])
            ],
        )
    )
    rag_examples = build_rag_examples(
        all_summaries,
        top_k=top_k,
        device_order=catalog.supported_device_ids,
    )
    if catalog.experiment_id is not None:
        from scripts.mqt_predictor_protocol import assert_records_belong_to_split

        manifest_for_partition = _load_json(
            scope_root / selected_devices[0] / "split_manifest.json"
        )
        assert_records_belong_to_split(
            rag_examples,
            allowed_split="train",
            manifest=manifest_for_partition,
        )

    output_root = scope_root / GLOBAL_VIEW_DIRECTORY
    runs_output = output_root / "qiskit_runs.jsonl"
    summaries_output = output_root / "qiskit_configuration_aggregates.jsonl"
    rag_output = output_root / "rag_examples.jsonl"
    failure_output = output_root / "reports" / "failure_details.csv"
    status_counts = Counter(str(run["status"]) for run in all_runs)
    statistics: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": catalog.experiment_id,
        "protocol_version": catalog.protocol_version,
        "dataset_scope": scope,
        "objective": objective_name,
        "view_type": "global_multi_device",
        "record_schema_versions": {
            "manifest": MANIFEST_SCHEMA_VERSION,
            "run": SCHEMA_VERSION,
            "configuration_aggregate": AGGREGATE_SCHEMA_VERSION,
            "rag_example": RAG_SCHEMA_VERSION,
        },
        "aggregation_policy": {
            "input_mode": "read_only_per_device_views",
            "device_order": list(catalog.supported_device_ids),
            "configuration_order": [
                configuration.config_id
                for configuration in catalog.configurations
            ],
            "ranking_metric": "median_expected_fidelity_across_seeds",
            "device_label": (
                "device whose best eligible configuration has the highest "
                "ranking score; catalog order breaks exact ties"
            ),
            "configuration_label": (
                "top configurations restricted to the selected device"
            ),
            "configuration_tie_break": (
                "catalog order; claims explicitly deny superiority at equal score"
            ),
            "top_k": top_k,
        },
        "source_device_ids": selected_devices,
        "available_device_ids": available,
        "missing_supported_device_ids": missing_supported,
        "counts": {
            "unique_circuits": len(
                {
                    str(summary["circuit"]["circuit_id"])
                    for summary in all_summaries
                }
            ),
            "runs": len(all_runs),
            "runs_by_status": dict(sorted(status_counts.items())),
            "configuration_aggregates": len(all_summaries),
            "eligible_configuration_aggregates": sum(
                bool(summary.get("eligible_for_ranking"))
                for summary in all_summaries
            ),
            "rag_examples": len(rag_examples),
            "failure_rows": sum(
                run.get("status") != "success" for run in all_runs
            ),
        },
        "sources": sources,
        "outputs": {
            "runs": str(runs_output.relative_to(scope_root)),
            "configuration_aggregates": str(
                summaries_output.relative_to(scope_root)
            ),
            "rag": str(rag_output.relative_to(scope_root)),
            "failure_details": str(failure_output.relative_to(scope_root)),
        },
        "mini_datasets_modified": False,
    }
    if write:
        atomic_jsonl_write(runs_output, all_runs)
        atomic_jsonl_write(summaries_output, all_summaries)
        atomic_jsonl_write(rag_output, rag_examples)
        write_failure_csv(failure_output, all_runs)
        atomic_json_write(output_root / "dataset_statistics.json", statistics)
    return statistics

'Combine individual device views without changing them.'

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
    'Read a required JSON file and check that it contains an object.'
    import json

    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f'{path} does not contain a JSON object.')
    return value


def _shared_circuit_identity(circuit: Mapping[str, Any]) -> str:
    'Represent a circuit independently of device-specific compatibility.'
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
    'List devices for which all required files exist.'
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
    'Check a manifest and the shared circuits it references.'
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f'Unexpected schema version in the manifest for {device_id}.')
    if manifest.get("device_id") != device_id:
        raise ValueError(f'Inconsistent device in the manifest for {device_id}.')
    if manifest.get("dataset_scope") != scope:
        raise ValueError(f'Inconsistent scope in the manifest for {device_id}.')
    if manifest.get("catalog_id") != catalog.catalog_id:
        raise ValueError(f'Inconsistent catalog in the manifest for {device_id}.')
    if manifest.get("experiment_id") != catalog.experiment_id:
        raise ValueError(f'Inconsistent experiment in the manifest for {device_id}.')
    if manifest.get("objective") != catalog.objective:
        raise ValueError(f'Inconsistent objective in the manifest for {device_id}.')
    if list(manifest.get("seeds", [])) != list(catalog.seeds):
        raise ValueError(f'Inconsistent seeds in the manifest for {device_id}.')
    storage = manifest.get("circuit_storage") or {}
    if (
        storage.get("layout") != "shared_scope_root"
        or storage.get("root_ref") != "circuits"
        or storage.get("source_ref_base") != "scope_root"
        or storage.get("integrity_field") != "source_sha256"
    ):
        raise ValueError(
            f'Circuit storage is not shared or recognized for {device_id}.'
        )

    device_num_qubits = int(manifest["device_num_qubits"])
    identities: dict[str, str] = {}
    for circuit in manifest.get("circuits", []):
        circuit_id = str(circuit.get("circuit_id", ""))
        if not circuit_id or circuit_id in identities:
            raise ValueError(f'Missing or duplicate circuit_id for {device_id}.')
        source_ref = str(circuit.get("source_ref", ""))
        source_path = resolve_circuit_source(
            str(catalog.objective["name"]),
            scope,
            source_ref,
            catalog.experiment_id,
        )
        if not source_path.is_file():
            raise FileNotFoundError(f'Missing shared circuit: {source_path}.')
        if sha256_file(source_path) != circuit.get("source_sha256"):
            raise ValueError(f'Inconsistent circuit SHA-256: {source_path}.')
        compatibility = circuit.get("device_compatibility") or {}
        expected_compatible = int(circuit["num_qubits"]) <= device_num_qubits
        if (
            compatibility.get("compatible") is not expected_compatible
            or compatibility.get("device_num_qubits") != device_num_qubits
        ):
            raise ValueError(
                f'Inconsistent compatibility for {device_id}/{circuit_id}.'
            )
        identities[circuit_id] = _shared_circuit_identity(circuit)
    if not identities:
        raise ValueError(f'Manifest has no circuits for {device_id}.')
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
    "Check common fields in a device's attempts or aggregates."
    for index, record in enumerate(records, start=1):
        location = f"{device_id}/{record_kind}:{index}"
        if record.get("schema_version") != expected_schema_version:
            raise ValueError(f'{location}: inconsistent schema version.')
        if record.get("dataset_scope") != scope:
            raise ValueError(f'{location}: inconsistent scope.')
        objective = record.get("objective") or {}
        if (
            objective.get("name") != objective_name
            or objective.get("direction") != catalog.objective.get("direction")
        ):
            raise ValueError(f'{location}: inconsistent objective.')
        device = record.get("device") or {}
        if device.get("device_id") != device_id:
            raise ValueError(f'{location}: inconsistent device.')
        configuration = record.get("configuration") or {}
        if configuration.get("catalog_id") != catalog.catalog_id:
            raise ValueError(f'{location}: inconsistent catalog_id.')
        try:
            allowed = catalog.require_allowed(
                int(configuration["optimization_level"]),
                configuration.get("layout_method"),
                configuration.get("routing_method"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f'{location}: invalid configuration.') from error
        if configuration.get("config_id") != allowed.config_id:
            raise ValueError(f'{location}: inconsistent config_id.')
        if record_kind == "runs":
            if record.get("status") not in {"success", "failure", "timeout"}:
                raise ValueError(f'{location}: invalid status.')
            if record.get("seed_transpiler") not in catalog.seeds:
                raise ValueError(f'{location}: seed outside the catalog.')
        elif record_kind == "aggregates":
            if record.get("ranking_metric") != (
                "median_expected_fidelity_across_seeds"
            ):
                raise ValueError(f'{location}: inconsistent ranking metric.')
        else:
            raise ValueError(f'Unsupported record type: {record_kind!r}.')


def _validate_records_against_manifest(
    records: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    *,
    device_id: str,
) -> None:
    'Check that records still describe the manifest circuits.'
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
                f'{device_id}:{index}: circuit outside the manifest: {circuit_id!r}.'
            )
        expected_identity = _shared_circuit_identity(expected)
        observed_identity = _shared_circuit_identity(circuit)
        if observed_identity != expected_identity:
            raise ValueError(
                f'{device_id}:{index}: inconsistent metadata for {circuit_id}.'
            )
        if record.get("split") != expected.get("split"):
            raise ValueError(f'{device_id}:{index}: inconsistent split.')

        device = record.get("device") or {}
        if device.get("num_qubits") != manifest.get("device_num_qubits"):
            raise ValueError(f'{device_id}:{index}: inconsistent target width.')
        current_target_identity = canonical_json(device)
        if target_identity is None:
            target_identity = current_target_identity
        elif current_target_identity != target_identity:
            raise ValueError(
                f'{device_id}:{index}: inconsistent Target snapshot.'
            )


def _ensure_unique(
    records: Sequence[Mapping[str, Any]],
    identifier: str,
) -> None:
    'Check that every record has a unique, nonempty identifier.'
    raw_values = [record.get(identifier) for record in records]
    if any(not isinstance(value, str) or not value for value in raw_values):
        raise ValueError(f'{identifier} missing from the global view.')
    values = [str(value) for value in raw_values]
    if len(values) != len(set(values)):
        duplicates = sorted(
            value
            for value, count in Counter(values).items()
            if count > 1
        )
        raise ValueError(f'{identifier} duplicates in the global view: {duplicates}.')


def _validate_circuit_identity(
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    'Check that circuit data remain consistent across devices.'
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
                f'Circuit metadata differ across devices: {circuit_id}.'
            )


def _record_key(record: Mapping[str, Any]) -> tuple[str, str, str]:
    'Build the circuit/device/configuration key.'
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
    'Check that each aggregate exactly represents its attempts.'
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
            raise ValueError(f'Missing or duplicate aggregate for key {key}.')
        seen_summary_keys.add(key)
        expected_runs = runs_by_key.get(key, [])
        expected_ids = {str(run["run_id"]) for run in expected_runs}
        raw_summary_ids = summary.get("run_ids")
        if not isinstance(raw_summary_ids, list):
            raise ValueError(f'Invalid run_ids for aggregate {key}.')
        summary_ids = [str(run_id) for run_id in raw_summary_ids]
        if len(summary_ids) != len(set(summary_ids)):
            raise ValueError(f'Duplicate run_ids for aggregate {key}.')
        if set(summary_ids) != expected_ids:
            raise ValueError(f'Aggregate does not match raw runs for {key}.')
        linked_run_ids.update(summary_ids)

        successful = {
            str(run["run_id"]): run
            for run in expected_runs
            if run.get("status") == "success"
        }
        observations = summary.get("score_observations")
        if not isinstance(observations, list):
            raise ValueError(f'Missing score_observations for {key}.')
        observed_ids = [str(item.get("run_id", "")) for item in observations]
        if len(observed_ids) != len(set(observed_ids)):
            raise ValueError(f'Duplicate score observations for {key}.')
        if set(observed_ids) != set(successful):
            raise ValueError(f'Score observations do not match successful runs for {key}.')
        for observation in observations:
            run = run_by_id[str(observation["run_id"])]
            if (
                int(observation["seed_transpiler"])
                != int(run["seed_transpiler"])
                or float(observation["score"]) != float(run["score"])
            ):
                raise ValueError(f'Inconsistent evidence score for {key}.')

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
                raise ValueError(f'{field} inconsistent for aggregate {key}.')

    if linked_run_ids != set(run_by_id):
        raise ValueError('Some raw runs are not represented by aggregates.')


def aggregate_device_datasets(
    scope: str,
    catalog: ConfigurationCatalog,
    *,
    top_k: int = 3,
    device_ids: Sequence[str] | None = None,
    require_all_supported: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    'Combine selected mini-Datasets without modifying their files.'
    if scope not in {"pilot", "full"}:
        raise ValueError('scope must be pilot or full.')
    if top_k <= 0:
        raise ValueError('top_k must be positive.')

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
            raise ValueError('The device list contains duplicates.')
        missing_requested = [
            item for item in selected_devices if item not in available
        ]
        if missing_requested:
            raise FileNotFoundError(
                'Incomplete or missing mini-Datasets: '
                + ", ".join(missing_requested)
            )
    if not selected_devices:
        raise FileNotFoundError(
            f'No complete mini-Dataset available in {scope_root}.'
        )

    missing_supported = [
        item
        for item in catalog.supported_device_ids
        if item not in available
    ]
    if require_all_supported and missing_supported:
        raise FileNotFoundError(
            'Missing mini-Datasets for supported devices: '
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
                f'Inconsistent circuit inventory across manifests: {device_id}.'
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
        from .reporting import build_device_comparison

        comparison = build_device_comparison(
            scope_root,
            scope=scope,
            device_ids=selected_devices,
            catalog=catalog,
            output_root=output_root / "reports",
        )
        statistics["device_comparison"] = comparison
        statistics["outputs"].update({
            "device_comparison_csv": str((output_root / "reports" / "device_comparison.csv").relative_to(scope_root)),
            "device_comparison_markdown": str((output_root / "reports" / "device_comparison.md").relative_to(scope_root)),
        })
        atomic_json_write(output_root / "dataset_statistics.json", statistics)
    return statistics

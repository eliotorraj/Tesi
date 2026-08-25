"""Aggregate seed replicates and export train-only RAG examples."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median, pstdev
from typing import Any, Iterable, Mapping

from .catalog import ConfigurationCatalog, QiskitConfiguration
from .core import (
    DATASETS_ROOT,
    SCHEMA_VERSION,
    atomic_json_write,
    atomic_jsonl_write,
    canonical_json,
    load_manifest,
    read_jsonl,
    stable_id,
)


def _number_statistics(values: Iterable[float]) -> dict[str, float | int | None]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std_population": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(finite),
        "mean": fmean(finite),
        "median": median(finite),
        "std_population": pstdev(finite),
        "min": min(finite),
        "max": max(finite),
    }


def _validate_run(
    run: Mapping[str, Any],
    catalog: ConfigurationCatalog,
) -> None:
    status = run.get("status")
    if status not in {"success", "failure", "timeout"}:
        raise ValueError(f"Stato tentativo non valido: {status!r}.")
    objective = run.get("objective")
    if (
        not isinstance(objective, Mapping)
        or objective.get("name") != catalog.objective["name"]
    ):
        raise ValueError("Figure of merit del tentativo non coerente.")
    device = run.get("device")
    if (
        not isinstance(device, Mapping)
        or device.get("device_id") != catalog.device_id
    ):
        raise ValueError("Hardware del tentativo fuori catalogo.")
    configuration = run.get("configuration")
    if not isinstance(configuration, Mapping):
        raise ValueError("Configurazione assente nel tentativo.")
    allowed = catalog.require_allowed(
        int(configuration["optimization_level"]),
        configuration.get("layout_method"),
        configuration.get("routing_method"),
    )
    if allowed.config_id != configuration.get("config_id"):
        raise ValueError("config_id non coerente con la tupla Qiskit.")
    if configuration.get("catalog_id") != catalog.catalog_id:
        raise ValueError("catalog_id del tentativo non coerente.")
    if run.get("seed_transpiler") not in catalog.seeds:
        raise ValueError("Seed del tentativo fuori dal piano sperimentale.")
    if status == "success":
        score = run.get("score")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
        ):
            raise ValueError("Tentativo success senza score finito.")
        validation = run.get("target_validation")
        if (
            not isinstance(validation, Mapping)
            or validation.get("is_executable_on_target") is not True
        ):
            raise ValueError("Tentativo success senza validazione target positiva.")
        if run.get("failure") is not None:
            raise ValueError("Tentativo success con oggetto failure.")
    else:
        if run.get("score") is not None:
            raise ValueError("Tentativo fallito con score valorizzato.")
        if not isinstance(run.get("failure"), Mapping):
            raise ValueError("Tentativo fallito senza dettagli failure.")


def _failure_breakdown(runs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for run in runs:
        if run.get("status") == "success":
            continue
        failure = run.get("failure") or {}
        counts[
            (
                str(failure.get("phase", run.get("phase", "unknown"))),
                str(failure.get("category", "unknown")),
                str(failure.get("exception_type", "unknown")),
            )
        ] += 1
    return [
        {
            "phase": phase,
            "category": category,
            "exception_type": exception_type,
            "count": count,
        }
        for (phase, category, exception_type), count in sorted(counts.items())
    ]


def _summary_record(
    circuit: Mapping[str, Any],
    configuration: QiskitConfiguration,
    runs: list[Mapping[str, Any]],
    catalog: ConfigurationCatalog,
    target_record: Mapping[str, Any],
    scope: str,
) -> dict[str, Any]:
    runs = sorted(runs, key=lambda run: int(run["seed_transpiler"]))
    observed_seeds = [int(run["seed_transpiler"]) for run in runs]
    if len(observed_seeds) != len(set(observed_seeds)):
        raise ValueError(
            f"Seed duplicati per {circuit['circuit_id']}/{configuration.config_id}."
        )
    successes = [run for run in runs if run["status"] == "success"]
    failures = [run for run in runs if run["status"] == "failure"]
    timeouts = [run for run in runs if run["status"] == "timeout"]
    expected_seeds = list(catalog.seeds)
    complete = (
        sorted(observed_seeds) == sorted(expected_seeds)
        and len(runs) == len(expected_seeds)
    )
    scores = [float(run["score"]) for run in successes]
    total_times = [
        float(run["timings_seconds"]["total"])
        for run in runs
        if run.get("timings_seconds", {}).get("total") is not None
    ]
    transpile_times = [
        float(run["timings_seconds"]["transpilation"])
        for run in runs
        if run.get("timings_seconds", {}).get("transpilation") is not None
    ]
    summary_id = stable_id(
        "summary",
        {
            "circuit_id": circuit["circuit_id"],
            "source_sha256": circuit["source_sha256"],
            "device_id": catalog.device_id,
            "configuration": configuration.to_dict(),
            "objective": catalog.objective["name"],
            "catalog_id": catalog.catalog_id,
        },
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "summary_id": summary_id,
        "dataset_scope": scope,
        "split": circuit["split"],
        "objective": dict(catalog.objective),
        "circuit": dict(circuit),
        "device": dict(target_record),
        "configuration": {
            **configuration.to_dict(),
            "catalog_id": catalog.catalog_id,
        },
        "seeds": {
            "expected": expected_seeds,
            "observed": observed_seeds,
            "successful": [
                int(run["seed_transpiler"]) for run in successes
            ],
            "failed": [int(run["seed_transpiler"]) for run in failures],
            "timed_out": [int(run["seed_transpiler"]) for run in timeouts],
        },
        "attempts": {
            "expected_count": len(expected_seeds),
            "observed_count": len(runs),
            "success_count": len(successes),
            "failure_count": len(failures),
            "timeout_count": len(timeouts),
            "complete": complete,
            "success_rate": (
                len(successes) / len(runs) if runs else None
            ),
        },
        "score_statistics": _number_statistics(scores),
        "timing_statistics_seconds": {
            "total": _number_statistics(total_times),
            "transpilation": _number_statistics(transpile_times),
        },
        "failure_breakdown": _failure_breakdown(runs),
        "eligible_for_ranking": (
            complete and len(successes) == len(expected_seeds)
        ),
        "ranking_metric": "median_expected_fidelity_across_seeds",
        "ranking_score": median(scores) if scores else None,
        "rank": None,
        "regret": None,
        "run_ids": [str(run["run_id"]) for run in runs],
    }


def aggregate_runs(
    manifest: Mapping[str, Any],
    runs: list[dict[str, Any]],
    catalog: ConfigurationCatalog,
    target_record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    identifiers = [str(run.get("run_id")) for run in runs]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("run_id duplicati nel JSONL dei tentativi.")
    circuits_by_id = {
        str(circuit["circuit_id"]): circuit
        for circuit in manifest["circuits"]
    }
    for run in runs:
        _validate_run(run, catalog)
        circuit_id = str(run["circuit"]["circuit_id"])
        expected_circuit = circuits_by_id.get(circuit_id)
        if expected_circuit is None:
            raise ValueError(
                f"Tentativo riferito a circuito fuori manifest: {circuit_id}."
            )
        if run.get("dataset_scope") != manifest["dataset_scope"]:
            raise ValueError("Scope del tentativo non coerente con il manifest.")
        if run.get("split") != expected_circuit["split"]:
            raise ValueError("Split del tentativo non coerente con il manifest.")
        if (
            run["circuit"].get("source_sha256")
            != expected_circuit["source_sha256"]
        ):
            raise ValueError("Hash sorgente del tentativo non coerente.")

    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[
            (
                str(run["circuit"]["circuit_id"]),
                str(run["configuration"]["config_id"]),
            )
        ].append(run)

    summaries: list[dict[str, Any]] = []
    for circuit in manifest["circuits"]:
        for configuration in catalog.configurations:
            summaries.append(
                _summary_record(
                    circuit,
                    configuration,
                    grouped.get(
                        (
                            str(circuit["circuit_id"]),
                            configuration.config_id,
                        ),
                        [],
                    ),
                    catalog,
                    target_record,
                    str(manifest["dataset_scope"]),
                )
            )

    order_by_config = {
        configuration.config_id: index
        for index, configuration in enumerate(catalog.configurations)
    }
    by_circuit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        by_circuit[str(summary["circuit"]["circuit_id"])].append(summary)
    for circuit_summaries in by_circuit.values():
        eligible = [
            summary
            for summary in circuit_summaries
            if summary["eligible_for_ranking"]
        ]
        eligible.sort(
            key=lambda summary: (
                -float(summary["ranking_score"]),
                order_by_config[str(summary["configuration"]["config_id"])],
            )
        )
        if not eligible:
            continue
        best = float(eligible[0]["ranking_score"])
        for rank, summary in enumerate(eligible, start=1):
            summary["rank"] = rank
            summary["regret"] = best - float(summary["ranking_score"])

    summaries.sort(
        key=lambda summary: (
            str(summary["split"]),
            str(summary["circuit"]["circuit_id"]),
            order_by_config[str(summary["configuration"]["config_id"])],
        )
    )
    return summaries


def _retrieval_text(
    circuit: Mapping[str, Any],
    device_id: str,
    objective_name: str,
) -> str:
    features = circuit["features"]["values"]
    feature_text = "; ".join(
        f"{name}={features[name]:.12g}" for name in sorted(features)
    )
    return (
        f"objective={objective_name}; device={device_id}; "
        f"family={circuit['benchmark_family']}; "
        f"generator={circuit['generator']}; "
        f"num_qubits={circuit['num_qubits']}; {feature_text}"
    )


def build_rag_examples(
    summaries: list[dict[str, Any]],
    *,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("top_k deve essere positivo.")
    by_circuit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        circuit = summary["circuit"]
        if summary["split"] != "train":
            continue
        if circuit.get("is_duplicate_alias"):
            continue
        by_circuit[str(circuit["circuit_id"])].append(summary)

    examples: list[dict[str, Any]] = []
    for circuit_id, circuit_summaries in sorted(by_circuit.items()):
        eligible = sorted(
            (
                summary
                for summary in circuit_summaries
                if summary["eligible_for_ranking"]
            ),
            key=lambda summary: int(summary["rank"]),
        )
        if not eligible:
            continue
        first = eligible[0]
        circuit = first["circuit"]
        device = first["device"]
        selected = eligible[:top_k]
        rag_id = stable_id(
            "rag",
            {
                "circuit_id": circuit_id,
                "source_sha256": circuit["source_sha256"],
                "device_id": device["device_id"],
                "objective": first["objective"]["name"],
                "catalog_id": first["configuration"]["catalog_id"],
            },
        )
        examples.append(
            {
                "schema_version": SCHEMA_VERSION,
                "rag_id": rag_id,
                "split": "train",
                "objective": dict(first["objective"]),
                "retrieval_input": {
                    "circuit": {
                        "circuit_id": circuit_id,
                        "benchmark_family": circuit["benchmark_family"],
                        "generator": circuit["generator"],
                        "num_qubits": circuit["num_qubits"],
                        "depth": circuit["depth"],
                        "size": circuit["size"],
                        "source_sha256": circuit["source_sha256"],
                        "features": circuit["features"],
                    },
                    "device": dict(device),
                    "retrieval_text": _retrieval_text(
                        circuit,
                        str(device["device_id"]),
                        str(first["objective"]["name"]),
                    ),
                },
                "ranking": {
                    "metric": "median_expected_fidelity_across_seeds",
                    "top_k_requested": top_k,
                    "evaluated_configuration_count": len(
                        circuit_summaries
                    ),
                    "eligible_configuration_count": len(eligible),
                    "returned_configuration_count": len(selected),
                    "complete_top_k": len(selected) == top_k,
                },
                "top_configurations": [
                    {
                        "rank": summary["rank"],
                        "summary_id": summary["summary_id"],
                        "config_id": summary["configuration"]["config_id"],
                        "optimization_level": summary["configuration"][
                            "optimization_level"
                        ],
                        "layout_method": summary["configuration"][
                            "layout_method"
                        ],
                        "routing_method": summary["configuration"][
                            "routing_method"
                        ],
                        "median_score": summary["score_statistics"]["median"],
                        "mean_score": summary["score_statistics"]["mean"],
                        "score_std_population": summary[
                            "score_statistics"
                        ]["std_population"],
                        "success_rate": summary["attempts"]["success_rate"],
                        "regret": summary["regret"],
                    }
                    for summary in selected
                ],
            }
        )
    return examples


def _load_target_record(
    output_root: Path,
    runs: list[Mapping[str, Any]],
    catalog: ConfigurationCatalog,
) -> dict[str, Any]:
    if runs:
        device = runs[0].get("device")
        if isinstance(device, Mapping):
            return dict(device)
    status_path = output_root / "generation_status.json"
    if status_path.is_file():
        with status_path.open(encoding="utf-8") as handle:
            status = json.load(handle)
        target = status.get("target")
        if isinstance(target, Mapping):
            return dict(target)
    return {
        "device_id": catalog.device_id,
        "description": catalog.device_id,
        "num_qubits": 127,
        "target_sha256": None,
        "provenance": {
            "provider": "mqt.bench.targets.get_device",
            "calibration_kind": "synthetic_deterministic_target",
            "live_hardware_data": False,
        },
    }


def build_dataset_views(
    scope: str,
    catalog: ConfigurationCatalog,
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    objective_name = str(catalog.objective["name"])
    output_root = DATASETS_ROOT / objective_name / scope
    manifest = load_manifest(scope, objective_name)
    runs_path = output_root / "qiskit_runs.jsonl"
    runs = read_jsonl(runs_path)
    target_record = _load_target_record(output_root, runs, catalog)
    summaries = aggregate_runs(manifest, runs, catalog, target_record)
    rag_examples = build_rag_examples(summaries, top_k=top_k)

    aggregate_path = output_root / "qiskit_configuration_aggregates.jsonl"
    rag_path = output_root / "rag_examples.jsonl"
    atomic_jsonl_write(aggregate_path, summaries)
    atomic_jsonl_write(rag_path, rag_examples)

    summary_status = Counter(
        (
            "eligible"
            if summary["eligible_for_ranking"]
            else "ineligible"
        )
        for summary in summaries
    )
    statistics = {
        "schema_version": SCHEMA_VERSION,
        "dataset_scope": scope,
        "objective": objective_name,
        "circuits": len(manifest["circuits"]),
        "attempts_available": len(runs),
        "configuration_aggregates": len(summaries),
        "aggregate_status": dict(sorted(summary_status.items())),
        "rag_examples": len(rag_examples),
        "rag_split": "train_only",
        "rag_top_k": top_k,
        "duplicate_aliases_excluded_from_rag": sum(
            1
            for circuit in manifest["circuits"]
            if circuit["split"] == "train"
            and circuit.get("is_duplicate_alias")
        ),
        "outputs": {
            "attempts": runs_path.name,
            "configuration_aggregates": aggregate_path.name,
            "rag": rag_path.name,
        },
    }
    atomic_json_write(output_root / "dataset_statistics.json", statistics)
    return statistics

"""Aggregate seed replicates and export train-only RAG examples."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median, pstdev
from typing import Any, Iterable, Mapping, Sequence

from .catalog import ConfigurationCatalog, QiskitConfiguration
from .core import (
    MANIFEST_SCHEMA_VERSION,
    SCHEMA_VERSION,
    atomic_json_write,
    atomic_jsonl_write,
    canonical_json,
    dataset_scope_root,
    load_manifest,
    read_jsonl,
    stable_id,
)

RAG_SCHEMA_VERSION = "2.0.0"
AGGREGATE_SCHEMA_VERSION = "2.0.0"
MAX_RAG_CONFIGURATIONS = 3
SCIENTIFIC_CAVEATS = (
    {
        "caveat_id": "expected_fidelity_is_estimate",
        "text": (
            "Expected fidelity è una stima offline calcolata dal Target "
            "sintetico MQT Bench, non una misura ottenuta su hardware reale."
        ),
    },
    {
        "caveat_id": "ranking_is_not_causal",
        "text": (
            "Il ranking descrive risultati osservati con catalogo, versioni e "
            "seed fissati; non dimostra che una feature del circuito abbia "
            "causato la scelta."
        ),
    },
    {
        "caveat_id": "closed_candidate_set",
        "text": (
            "L'etichetta vale soltanto tra device compatibili e configurazioni "
            "effettivamente valutati in questo protocollo."
        ),
    },
    {
        "caveat_id": "constraints_not_applied",
        "text": (
            "Gli esempi offline non applicano vincoli utente; al retrieval i "
            "vincoli devono filtrare candidati e configurazioni senza "
            "riscrivere la ground truth."
        ),
    },
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
    expected_device_id: str,
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
        or device.get("device_id") != expected_device_id
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
            "device_id": target_record["device_id"],
            "configuration": configuration.to_dict(),
            "objective": catalog.objective["name"],
            "catalog_id": catalog.catalog_id,
        },
    )
    return {
        "schema_version": AGGREGATE_SCHEMA_VERSION,
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
        "score_observations": [
            {
                "run_id": str(run["run_id"]),
                "seed_transpiler": int(run["seed_transpiler"]),
                "score": float(run["score"]),
            }
            for run in successes
        ],
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
    expected_device_id = str(target_record["device_id"])
    if manifest.get("catalog_id") != catalog.catalog_id:
        raise ValueError("Catalogo del manifest non coerente con quello caricato.")
    if list(manifest.get("seeds", [])) != list(catalog.seeds):
        raise ValueError("Seed del manifest non coerenti con il catalogo.")
    if manifest.get("objective") != catalog.objective:
        raise ValueError("Objective del manifest non coerente con il catalogo.")
    if manifest.get("device_id") not in {None, expected_device_id}:
        raise ValueError(
            "Device del target incoerente con quello dichiarato nel manifest."
        )
    circuits_by_id = {
        str(circuit["circuit_id"]): circuit
        for circuit in manifest["circuits"]
    }
    for run in runs:
        _validate_run(run, catalog, expected_device_id)
        device = run.get("device") or {}
        for field in ("num_qubits", "target_sha256"):
            expected = target_record.get(field)
            if expected is not None and device.get(field) != expected:
                raise ValueError(
                    f"{field} del target non coerente tra i tentativi."
                )
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
        if circuit.get("device_compatibility", {}).get("compatible") is False:
            continue
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
    device_ids: Sequence[str],
    objective_name: str,
) -> str:
    features = circuit["features"]["values"]
    feature_text = "; ".join(
        f"{name}={features[name]:.12g}" for name in sorted(features)
    )
    return (
        f"objective={objective_name}; "
        f"compatible_devices={','.join(device_ids)}; "
        f"family={circuit['benchmark_family']}; "
        f"generator={circuit['generator']}; "
        f"num_qubits={circuit['num_qubits']}; {feature_text}"
    )


def _device_order_map(device_order: Sequence[str] | None) -> dict[str, int]:
    return {
        str(device_id): index
        for index, device_id in enumerate(device_order or ())
    }


def _global_summary_key(
    summary: Mapping[str, Any],
    order: Mapping[str, int],
) -> tuple[Any, ...]:
    device_id = str(summary["device"]["device_id"])
    rank = summary.get("rank")
    return (
        -float(summary["ranking_score"]),
        order.get(device_id, len(order)),
        device_id,
        int(rank) if rank is not None else 10**9,
        str(summary["configuration"]["config_id"]),
    )


def _evidence_record(
    summary: Mapping[str, Any],
    selected_best: Mapping[str, Any],
    rank_within_selected_device: int | None,
) -> dict[str, Any]:
    summary_id = str(summary["summary_id"])
    score = float(summary["ranking_score"])
    selected_score = float(selected_best["ranking_score"])
    evidence_id = stable_id(
        "evidence",
        {
            "summary_id": summary_id,
            "selected_best_summary_id": selected_best["summary_id"],
        },
    )
    observations = [
        {
            "run_id": str(item["run_id"]),
            "seed_transpiler": int(item["seed_transpiler"]),
            "score": float(item["score"]),
        }
        for item in summary.get("score_observations", [])
    ]
    statistics = summary["score_statistics"]
    return {
        "evidence_id": evidence_id,
        "evidence_type": "offline_seed_aggregate",
        "summary_id": summary_id,
        "run_ids": list(summary["run_ids"]),
        "device_id": summary["device"]["device_id"],
        "config_id": summary["configuration"]["config_id"],
        "metric": summary["ranking_metric"],
        "aggregation": {
            "method": "median",
            "value": score,
            "sample_count": statistics["count"],
        },
        "comparison_with_selected_best": {
            "reference_summary_id": selected_best["summary_id"],
            "reference_value": selected_score,
            "absolute_regret": selected_score - score,
            "tied_with_selected_best": math.isclose(
                score,
                selected_score,
                rel_tol=1e-12,
                abs_tol=1e-15,
            ),
        },
        "stability": {
            "expected_seeds": list(summary["seeds"]["expected"]),
            "successful_seeds": list(summary["seeds"]["successful"]),
            "success_rate": summary["attempts"]["success_rate"],
            "score_std_population": statistics["std_population"],
            "score_min": statistics["min"],
            "score_max": statistics["max"],
            "observations": observations,
        },
        "rank_within_selected_device": rank_within_selected_device,
        "provenance": {
            "dataset_scope": summary["dataset_scope"],
            "catalog_id": summary["configuration"]["catalog_id"],
            "source_sha256": summary["circuit"]["source_sha256"],
            "target_sha256": summary["device"].get("target_sha256"),
            "measurement_context": "offline_qiskit_transpilation",
        },
    }


def build_rag_label(
    circuit_summaries: list[dict[str, Any]],
    *,
    top_k: int = 3,
    device_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build one evidence-backed label across every evaluated device."""
    if not 1 <= top_k <= MAX_RAG_CONFIGURATIONS:
        raise ValueError(
            f"top_k deve essere compreso tra 1 e {MAX_RAG_CONFIGURATIONS}."
        )
    eligible = [
        summary
        for summary in circuit_summaries
        if summary.get("eligible_for_ranking")
        and summary.get("ranking_score") is not None
    ]
    if not eligible:
        raise ValueError("Nessun aggregato eleggibile per l'esempio RAG.")

    order = _device_order_map(device_order)
    eligible.sort(key=lambda item: _global_summary_key(item, order))
    selected_best = eligible[0]
    selected_device_id = str(selected_best["device"]["device_id"])
    selected_device_summaries = sorted(
        (
            summary
            for summary in eligible
            if str(summary["device"]["device_id"]) == selected_device_id
        ),
        key=lambda item: (
            int(item["rank"]) if item.get("rank") is not None else 10**9,
            str(item["configuration"]["config_id"]),
        ),
    )
    selected = selected_device_summaries[:top_k]
    tied_best_config_ids = [
        str(summary["configuration"]["config_id"])
        for summary in selected_device_summaries
        if math.isclose(
            float(summary["ranking_score"]),
            float(selected_best["ranking_score"]),
            rel_tol=1e-12,
            abs_tol=1e-15,
        )
    ]

    best_by_device: dict[str, dict[str, Any]] = {}
    for summary in eligible:
        device_id = str(summary["device"]["device_id"])
        best_by_device.setdefault(device_id, summary)
    ordered_device_bests = sorted(
        best_by_device.values(),
        key=lambda item: _global_summary_key(item, order),
    )
    best_score = float(selected_best["ranking_score"])
    evaluated_device_ids = sorted(
        {
            str(summary["device"]["device_id"])
            for summary in circuit_summaries
        },
        key=lambda item: (order.get(item, len(order)), item),
    )
    eligible_device_ids = [
        str(summary["device"]["device_id"])
        for summary in ordered_device_bests
    ]
    ineligible_device_ids = [
        device_id
        for device_id in evaluated_device_ids
        if device_id not in best_by_device
    ]
    tied_device_ids = [
        str(summary["device"]["device_id"])
        for summary in ordered_device_bests
        if math.isclose(
            float(summary["ranking_score"]),
            best_score,
            rel_tol=1e-12,
            abs_tol=1e-15,
        )
    ]

    evidence_summaries: dict[str, Mapping[str, Any]] = {
        str(summary["summary_id"]): summary
        for summary in [*ordered_device_bests, *selected]
    }
    selected_rank_by_summary = {
        str(summary["summary_id"]): index
        for index, summary in enumerate(selected, start=1)
    }
    evidence = [
        _evidence_record(
            summary,
            selected_best,
            selected_rank_by_summary.get(str(summary["summary_id"])),
        )
        for summary in evidence_summaries.values()
    ]
    evidence_id_by_summary = {
        str(item["summary_id"]): str(item["evidence_id"])
        for item in evidence
    }

    device_claim_id = stable_id(
        "claim",
        {
            "type": "selected_device",
            "summary_id": selected_best["summary_id"],
            "candidate_devices": sorted(best_by_device),
        },
    )
    if len(evaluated_device_ids) == 1:
        selection_reason = "device_specific_configuration_ranking"
        comparison_margin = None
        device_claim_text = (
            f"Nel mini-Dataset device-specifico {selected_device_id} è l'unico "
            "hardware candidato: l'etichetta device non è un confronto tra "
            f"hardware. La migliore configurazione è "
            f"{selected_best['configuration']['config_id']} con mediana "
            f"{best_score:.12g}."
        )
    elif len(best_by_device) == 1:
        selection_reason = "only_eligible_device"
        comparison_margin = None
        device_claim_text = (
            f"Tra {len(evaluated_device_ids)} device compatibili valutati, "
            f"{selected_device_id} è l'unico con almeno una configurazione "
            "completa ed eleggibile secondo il protocollo; non è quindi "
            "possibile un confronto di score con gli altri device. La sua "
            f"migliore configurazione è "
            f"{selected_best['configuration']['config_id']} con mediana "
            f"{best_score:.12g}."
        )
    elif len(tied_device_ids) > 1:
        selection_reason = "tie_break_catalog_order"
        comparison_margin = 0.0
        device_claim_text = (
            f"{selected_device_id} è l'etichetta deterministica dopo una "
            f"parità a mediana {best_score:.12g} tra "
            f"{', '.join(tied_device_ids)}; il tie-break segue l'ordine del "
            "catalogo e i dati non dimostrano superiorità tra i device a pari "
            "score."
        )
    else:
        selection_reason = "best_observed_median"
        runner_up = ordered_device_bests[1]
        runner_score = float(runner_up["ranking_score"])
        comparison_margin = best_score - runner_score
        device_claim_text = (
            f"{selected_device_id} è l'etichetta tra i device compatibili: "
            f"{selected_best['configuration']['config_id']} ottiene mediana "
            f"{best_score:.12g}, contro {runner_score:.12g} del miglior "
            f"candidato {runner_up['device']['device_id']} "
            f"({runner_up['configuration']['config_id']}), con margine "
            f"{comparison_margin:.12g}."
        )
    claims = [
        {
            "claim_id": device_claim_id,
            "claim_type": "selected_device",
            "text": device_claim_text,
            "evidence_ids": [
                evidence_id_by_summary[str(summary["summary_id"])]
                for summary in ordered_device_bests
            ],
            "caveat_ids": [
                "expected_fidelity_is_estimate",
                "ranking_is_not_causal",
                "closed_candidate_set",
            ],
        }
    ]

    top_configurations: list[dict[str, Any]] = []
    for rank, summary in enumerate(selected, start=1):
        summary_id = str(summary["summary_id"])
        claim_id = stable_id(
            "claim",
            {
                "type": "ranked_configuration",
                "summary_id": summary_id,
                "rank": rank,
            },
        )
        evidence_id = evidence_id_by_summary[summary_id]
        score = float(summary["ranking_score"])
        tied_score_config_ids = [
            str(candidate["configuration"]["config_id"])
            for candidate in selected_device_summaries
            if math.isclose(
                float(candidate["ranking_score"]),
                score,
                rel_tol=1e-12,
                abs_tol=1e-15,
            )
        ]
        other_tied_config_ids = [
            config_id
            for config_id in tied_score_config_ids
            if config_id != summary["configuration"]["config_id"]
        ]
        if len(tied_score_config_ids) > 1:
            configuration_claim_text = (
                f"Per {selected_device_id}, "
                f"{summary['configuration']['config_id']} è la "
                f"configurazione in posizione {rank}: mediana "
                f"{score:.12g}, regret {best_score - score:.12g}. "
                f"Condivide lo stesso score con "
                f"{', '.join(other_tied_config_ids)}; la posizione segue "
                "l'ordine deterministico del catalogo e non dimostra "
                "superiorità tra le configurazioni a pari score."
            )
        else:
            configuration_claim_text = (
                f"Per {selected_device_id}, "
                f"{summary['configuration']['config_id']} è la "
                f"configurazione in posizione {rank}: mediana "
                f"{score:.12g}, regret {best_score - score:.12g} rispetto "
                "alla migliore etichettata."
            )
        claims.append(
            {
                "claim_id": claim_id,
                "claim_type": "ranked_configuration",
                "text": configuration_claim_text,
                "evidence_ids": [evidence_id],
                "caveat_ids": [
                    "expected_fidelity_is_estimate",
                    "ranking_is_not_causal",
                ],
            }
        )
        top_configurations.append(
            {
                "rank": rank,
                "device_id": selected_device_id,
                "summary_id": summary_id,
                "config_id": summary["configuration"]["config_id"],
                "optimization_level": summary["configuration"][
                    "optimization_level"
                ],
                "layout_method": summary["configuration"]["layout_method"],
                "routing_method": summary["configuration"]["routing_method"],
                "median_score": summary["score_statistics"]["median"],
                "mean_score": summary["score_statistics"]["mean"],
                "score_std_population": summary["score_statistics"][
                    "std_population"
                ],
                "success_rate": summary["attempts"]["success_rate"],
                "regret": best_score - score,
                "tied_score_config_ids": tied_score_config_ids,
                "claim_id": claim_id,
                "evidence_id": evidence_id,
            }
        )

    return {
        "view_scope": (
            "global_multi_device"
            if len(evaluated_device_ids) > 1
            else "device_specific"
        ),
        "selected_device": {
            "device_id": selected_device_id,
            "best_summary_id": selected_best["summary_id"],
            "best_config_id": selected_best["configuration"]["config_id"],
            "median_score": best_score,
            "tied_best_device_ids": tied_device_ids,
            "tied_best_config_ids": tied_best_config_ids,
            "eligible_device_ids": eligible_device_ids,
            "ineligible_device_ids": ineligible_device_ids,
            "selection_reason": selection_reason,
            "comparison_margin": comparison_margin,
        },
        "top_configurations": top_configurations,
        "claims": claims,
        "evidence": evidence,
        "scientific_caveats": [dict(item) for item in SCIENTIFIC_CAVEATS],
        "eligible_configuration_count": len(eligible),
        "evaluated_device_count": len(evaluated_device_ids),
        "eligible_device_count": len(best_by_device),
    }


def build_rag_examples(
    summaries: list[dict[str, Any]],
    *,
    top_k: int = 3,
    device_order: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    if not 1 <= top_k <= MAX_RAG_CONFIGURATIONS:
        raise ValueError(
            f"top_k deve essere compreso tra 1 e {MAX_RAG_CONFIGURATIONS}."
        )
    by_circuit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        circuit = summary["circuit"]
        if summary["split"] != "train" or circuit.get("is_duplicate_alias"):
            continue
        by_circuit[str(circuit["circuit_id"])].append(summary)

    examples: list[dict[str, Any]] = []
    for circuit_id, circuit_summaries in sorted(by_circuit.items()):
        if not any(item.get("eligible_for_ranking") for item in circuit_summaries):
            continue
        label = build_rag_label(
            circuit_summaries,
            top_k=top_k,
            device_order=device_order,
        )
        eligible = [
            item
            for item in circuit_summaries
            if item.get("eligible_for_ranking")
        ]
        first = eligible[0]
        circuit = first["circuit"]
        devices_by_id = {
            str(summary["device"]["device_id"]): dict(summary["device"])
            for summary in circuit_summaries
        }
        order = _device_order_map(device_order)
        device_ids = sorted(
            devices_by_id,
            key=lambda item: (order.get(item, len(order)), item),
        )
        compatible_devices = [
            devices_by_id[device_id] for device_id in device_ids
        ]
        retrieval_text = _retrieval_text(
            circuit,
            device_ids,
            str(first["objective"]["name"]),
        )
        rag_id = stable_id(
            "rag",
            {
                "circuit_id": circuit_id,
                "source_sha256": circuit["source_sha256"],
                "device_ids": device_ids,
                "objective": first["objective"]["name"],
                "catalog_id": first["configuration"]["catalog_id"],
                "schema_version": RAG_SCHEMA_VERSION,
                "top_k": top_k,
            },
        )
        claims_text = " ".join(
            str(claim["text"]) for claim in label["claims"]
        )
        examples.append(
            {
                "schema_version": RAG_SCHEMA_VERSION,
                "rag_id": rag_id,
                "split": "train",
                "view_scope": label["view_scope"],
                "task": {
                    "name": "select_device_and_qiskit_configurations",
                    "input_fields": [
                        "circuit",
                        "circuit.features",
                        "objective",
                        "compatible_devices",
                        "user_constraints",
                    ],
                    "label_fields": [
                        "selected_device",
                        "top_configurations",
                        "claims",
                        "evidence",
                    ],
                    "label_semantics": (
                        "Device con la migliore configurazione eleggibile, poi "
                        "top configurazioni sul device selezionato."
                    ),
                },
                "objective": dict(first["objective"]),
                "retrieval_input": {
                    "circuit": {
                        "circuit_id": circuit_id,
                        "benchmark_family": circuit["benchmark_family"],
                        "generator": circuit["generator"],
                        "num_qubits": circuit["num_qubits"],
                        "depth": circuit["depth"],
                        "size": circuit["size"],
                        "source_ref": circuit.get("source_ref"),
                        "source_sha256": circuit["source_sha256"],
                        "features": circuit["features"],
                    },
                    "compatible_devices": compatible_devices,
                    "selection_scope": {
                        "catalog_id": first["configuration"]["catalog_id"],
                        "evaluated_device_ids": device_ids,
                        "evaluated_configuration_count": len(circuit_summaries),
                        "eligible_configuration_count": label[
                            "eligible_configuration_count"
                        ],
                    },
                    "user_constraints": {
                        "schema_version": "0.1.0",
                        "constraint_set_id": None,
                        "status": "not_applied_offline",
                        "hard_constraints": [],
                        "preferences": [],
                    },
                    "retrieval_text": retrieval_text,
                },
                "ranking": {
                    "metric": "median_expected_fidelity_across_seeds",
                    "top_k_requested": top_k,
                    "evaluated_device_count": label["evaluated_device_count"],
                    "eligible_device_count": label["eligible_device_count"],
                    "evaluated_configuration_count": len(circuit_summaries),
                    "eligible_configuration_count": label[
                        "eligible_configuration_count"
                    ],
                    "returned_configuration_count": len(
                        label["top_configurations"]
                    ),
                    "complete_top_k": (
                        len(label["top_configurations"]) == top_k
                    ),
                },
                "selected_device": label["selected_device"],
                "top_configurations": label["top_configurations"],
                "claims": label["claims"],
                "evidence": label["evidence"],
                "scientific_caveats": label["scientific_caveats"],
                "retrieval_document": (
                    f"{retrieval_text} Esempio empirico etichettato: "
                    f"{claims_text}"
                ),
            }
        )
    return examples


def _load_target_record(
    output_root: Path,
    runs: list[Mapping[str, Any]],
    device_id: str,
    manifest: Mapping[str, Any],
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
        "device_id": device_id,
        "description": device_id,
        "num_qubits": manifest.get("device_num_qubits"),
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
    device_id: str | None = None,
) -> dict[str, Any]:
    objective_name = str(catalog.objective["name"])
    selected_device_id = catalog.require_device(device_id)
    output_root = dataset_scope_root(
        objective_name,
        scope,
        selected_device_id,
    )
    manifest = load_manifest(scope, objective_name, selected_device_id)
    runs_path = output_root / "qiskit_runs.jsonl"
    runs = read_jsonl(runs_path)
    target_record = _load_target_record(
        output_root,
        runs,
        selected_device_id,
        manifest,
    )
    summaries = aggregate_runs(manifest, runs, catalog, target_record)
    rag_examples = build_rag_examples(
        summaries,
        top_k=top_k,
        device_order=catalog.supported_device_ids,
    )

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
        "record_schema_versions": {
            "manifest": MANIFEST_SCHEMA_VERSION,
            "run": SCHEMA_VERSION,
            "configuration_aggregate": AGGREGATE_SCHEMA_VERSION,
            "rag_example": RAG_SCHEMA_VERSION,
        },
        "dataset_scope": scope,
        "objective": objective_name,
        "device_id": selected_device_id,
        "circuits": len(manifest["circuits"]),
        "compatible_circuits": manifest["counts"].get(
            "compatible_circuits",
            len(manifest["circuits"]),
        ),
        "incompatible_circuits": manifest["counts"].get(
            "incompatible_circuits",
            0,
        ),
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
    if scope == "pilot":
        from .reporting import build_pilot_report

        report = build_pilot_report(output_root, catalog)
        statistics["outputs"].update(
            {
                "pilot_report": "reports/pilot_report.md",
                "pilot_summary": "reports/pilot_summary.json",
                "configuration_statistics": "reports/configuration_statistics.csv",
                "circuit_statistics": "reports/circuit_statistics.csv",
                "failure_details": "reports/failure_details.csv",
            }
        )
        statistics["device_comparison"] = report["comparison"]
    atomic_json_write(output_root / "dataset_statistics.json", statistics)
    return statistics

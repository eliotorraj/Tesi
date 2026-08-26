"""Readable, reproducible statistics for per-device Qiskit pilots."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path
from statistics import fmean, median
from typing import Any, Iterable, Mapping, Sequence

from .catalog import ConfigurationCatalog
from .core import SCHEMA_VERSION, atomic_json_write, atomic_text_write, read_jsonl
from .generation import build_timeout_diagnostics


CONFIG_FIELDS = """
device_id study config_id optimization_level layout_method routing_method
attempts_expected attempts_observed success_count failure_count timeout_count
success_rate circuits_expected circuits_complete circuits_eligible
transpile_success_n transpile_min_s transpile_median_s transpile_mean_s
transpile_p95_s transpile_max_s rank1_count co_winner_count top3_count
""".split()
CIRCUIT_FIELDS = """
device_id circuit_id split family generator num_qubits depth size
attempts_expected attempts_observed success_count failure_count timeout_count
success_rate transpile_success_n transpile_median_s transpile_mean_s
transpile_p95_s transpile_max_s eligible_configurations best_config_id
best_median_score
""".split()
FAILURE_FIELDS = """
device_id device_num_qubits target_sha256 run_id circuit_id family generator
num_qubits depth size config_id optimization_level layout_method routing_method
seed status phase category exception_type timeout_seconds observed_total_seconds
message diagnostic_method observed_phase completed_pass_count
last_completed_pass_name last_completed_pass_class last_completed_pass_index
last_completed_pass_duration_seconds last_completed_pass_wall_elapsed_seconds
interrupted_pass_file interrupted_pass_function interrupted_pass_line
inferred_qiskit_stage inferred_configuration_component
inferred_configuration_value inference_confidence
causal_attribution_supported diagnostic_limitations last_relevant_qiskit_frame
""".split()
COMPARISON_FIELDS = """
device_id device_num_qubits workers timeout_seconds compatible_circuits incompatible_circuits
attempts_planned attempts_observed success_count failure_count timeout_count
success_rate transpile_median_s transpile_mean_s transpile_p95_s transpile_max_s
eligible_aggregates ineligible_aggregates common_circuits
common_attempts_observed common_success_count common_failure_count
common_timeout_count common_success_rate common_transpile_median_s
common_transpile_mean_s common_transpile_p95_s common_transpile_max_s
""".split()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} non contiene un oggetto JSON.")
    return value


def _finite(values: Iterable[Any]) -> list[float]:
    result: list[float] = []
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        number = float(value)
        if math.isfinite(number):
            result.append(number)
    return result


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _stats(values: Iterable[Any]) -> dict[str, Any]:
    finite = _finite(values)
    if not finite:
        return dict.fromkeys(("min", "median", "mean", "p95", "max"), None) | {
            "count": 0
        }
    return {
        "count": len(finite),
        "min": min(finite),
        "median": median(finite),
        "mean": fmean(finite),
        "p95": _percentile(finite, 0.95),
        "max": max(finite),
    }


def _success_times(runs: Iterable[Mapping[str, Any]]) -> list[float]:
    return _finite(
        run.get("timings_seconds", {}).get("transpilation")
        for run in runs
        if run.get("status") == "success"
    )


def _statuses(runs: Iterable[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(run.get("status", "unknown")) for run in runs)


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _num(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    number = float(value)
    return "-" if not math.isfinite(number) else f"{number:.{digits}f}"


def _pct(value: Any) -> str:
    return "-" if value is None else f"{100 * float(value):.1f}%"


def _table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(map(clean, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines += [
        "| " + " | ".join(map(clean, row)) + " |"
        for row in rows
    ]
    return "\n".join(lines)


def _csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(fields),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {field: "" if row.get(field) is None else row.get(field) for field in fields}
        )
    atomic_text_write(path, stream.getvalue())


def _configuration_rows(
    catalog: ConfigurationCatalog,
    device_id: str,
    compatible_circuits: int,
    runs: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_config: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    summary_by_config: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    eligible_by_circuit: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for run in runs:
        by_config[str(run["configuration"]["config_id"])].append(run)
    for summary in summaries:
        config_id = str(summary["configuration"]["config_id"])
        summary_by_config[config_id].append(summary)
        if summary.get("eligible_for_ranking"):
            eligible_by_circuit[str(summary["circuit"]["circuit_id"])].append(summary)

    co_winners: Counter[str] = Counter()
    for items in eligible_by_circuit.values():
        best = max(float(item["ranking_score"]) for item in items)
        for item in items:
            if math.isclose(
                float(item["ranking_score"]), best, rel_tol=1e-12, abs_tol=1e-15
            ):
                co_winners[str(item["configuration"]["config_id"])] += 1

    rows: list[dict[str, Any]] = []
    attempts_expected = compatible_circuits * len(catalog.seeds)
    for config in catalog.configurations:
        config_runs = by_config[config.config_id]
        config_summaries = summary_by_config[config.config_id]
        status = _statuses(config_runs)
        timing = _stats(_success_times(config_runs))
        observed = len(config_runs)
        success = status["success"]
        rows.append(
            {
                "device_id": device_id,
                "study": config.study,
                "config_id": config.config_id,
                "optimization_level": config.optimization_level,
                "layout_method": config.layout_method,
                "routing_method": config.routing_method,
                "attempts_expected": attempts_expected,
                "attempts_observed": observed,
                "success_count": success,
                "failure_count": status["failure"],
                "timeout_count": status["timeout"],
                "success_rate": _rate(success, observed),
                "circuits_expected": compatible_circuits,
                "circuits_complete": sum(
                    bool(item["attempts"]["complete"]) for item in config_summaries
                ),
                "circuits_eligible": sum(
                    bool(item["eligible_for_ranking"]) for item in config_summaries
                ),
                "transpile_success_n": timing["count"],
                "transpile_min_s": timing["min"],
                "transpile_median_s": timing["median"],
                "transpile_mean_s": timing["mean"],
                "transpile_p95_s": timing["p95"],
                "transpile_max_s": timing["max"],
                "rank1_count": sum(item.get("rank") == 1 for item in config_summaries),
                "co_winner_count": co_winners[config.config_id],
                "top3_count": sum(
                    item.get("rank") is not None and int(item["rank"]) <= 3
                    for item in config_summaries
                ),
            }
        )
    return rows


def _circuit_rows(
    catalog: ConfigurationCatalog,
    device_id: str,
    manifest: Mapping[str, Any],
    runs: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_circuit: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    summary_by_circuit: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for run in runs:
        by_circuit[str(run["circuit"]["circuit_id"])].append(run)
    for summary in summaries:
        summary_by_circuit[str(summary["circuit"]["circuit_id"])].append(summary)

    rows: list[dict[str, Any]] = []
    attempts_expected = len(catalog.configurations) * len(catalog.seeds)
    for circuit in manifest["circuits"]:
        if circuit.get("device_compatibility", {}).get("compatible") is False:
            continue
        circuit_id = str(circuit["circuit_id"])
        circuit_runs = by_circuit[circuit_id]
        circuit_summaries = summary_by_circuit[circuit_id]
        status = _statuses(circuit_runs)
        timing = _stats(_success_times(circuit_runs))
        eligible = [
            item for item in circuit_summaries if item.get("eligible_for_ranking")
        ]
        best = next((item for item in eligible if item.get("rank") == 1), None)
        observed, success = len(circuit_runs), status["success"]
        rows.append(
            {
                "device_id": device_id,
                "circuit_id": circuit_id,
                "split": circuit["split"],
                "family": circuit["benchmark_family"],
                "generator": circuit["generator"],
                "num_qubits": circuit["num_qubits"],
                "depth": circuit["depth"],
                "size": circuit["size"],
                "attempts_expected": attempts_expected,
                "attempts_observed": observed,
                "success_count": success,
                "failure_count": status["failure"],
                "timeout_count": status["timeout"],
                "success_rate": _rate(success, observed),
                "transpile_success_n": timing["count"],
                "transpile_median_s": timing["median"],
                "transpile_mean_s": timing["mean"],
                "transpile_p95_s": timing["p95"],
                "transpile_max_s": timing["max"],
                "eligible_configurations": len(eligible),
                "best_config_id": (
                    best["configuration"]["config_id"] if best else None
                ),
                "best_median_score": (
                    best["score_statistics"]["median"] if best else None
                ),
            }
        )
    return rows


def _timeout_diagnostics(
    run: Mapping[str, Any],
    failure: Mapping[str, Any],
) -> Mapping[str, Any]:
    existing = failure.get("timeout_diagnostics")
    if isinstance(existing, Mapping):
        return existing
    if run.get("status") != "timeout":
        return {}
    provenance = run.get("provenance") or {}
    versions = provenance.get("versions") or {}
    return build_timeout_diagnostics(
        traceback_text=str(failure.get("traceback", "")),
        phase=str(failure.get("phase", run.get("phase", "unknown"))),
        timeout_seconds=failure.get("timeout_seconds"),
        elapsed_seconds=(run.get("timings_seconds") or {}).get("total"),
        configuration=run.get("configuration") or {},
        qiskit_version=str(versions.get("qiskit", "")),
    )


def failure_detail_rows(
    runs: Sequence[Mapping[str, Any]],
    device_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return backward-compatible, evidence-qualified failure CSV rows."""
    rows: list[dict[str, Any]] = []
    for run in runs:
        if run.get("status") == "success":
            continue
        failure = run.get("failure") or {}
        circuit = run.get("circuit") or {}
        device = run.get("device") or {}
        configuration = run.get("configuration") or {}
        diagnostics = _timeout_diagnostics(run, failure)
        last_pass = diagnostics.get("last_completed_pass") or {}
        interrupted = diagnostics.get("interrupted_stack_frame") or {}
        inference = diagnostics.get("inference") or {}
        component = inference.get("configuration_component") or {}
        limitations = diagnostics.get("limitations") or []
        interrupted_text = None
        if interrupted:
            interrupted_text = (
                f"{interrupted.get('file')}:{interrupted.get('line')}:"
                f"{interrupted.get('function')}"
            )
        rows.append(
            {
                "device_id": device_id or device.get("device_id"),
                "device_num_qubits": device.get("num_qubits"),
                "target_sha256": device.get("target_sha256"),
                "run_id": run.get("run_id"),
                "circuit_id": circuit.get("circuit_id"),
                "family": circuit.get("benchmark_family"),
                "generator": circuit.get("generator"),
                "num_qubits": circuit.get("num_qubits"),
                "depth": circuit.get("depth"),
                "size": circuit.get("size"),
                "config_id": configuration.get("config_id"),
                "optimization_level": configuration.get("optimization_level"),
                "layout_method": configuration.get("layout_method"),
                "routing_method": configuration.get("routing_method"),
                "seed": run.get("seed_transpiler"),
                "status": run.get("status"),
                "phase": failure.get("phase", run.get("phase")),
                "category": failure.get("category"),
                "exception_type": failure.get("exception_type"),
                "timeout_seconds": failure.get("timeout_seconds"),
                "observed_total_seconds": run.get("timings_seconds", {}).get("total"),
                "message": failure.get("message"),
                "diagnostic_method": diagnostics.get("observation_method"),
                "observed_phase": diagnostics.get("observed_phase"),
                "completed_pass_count": diagnostics.get("completed_pass_count"),
                "last_completed_pass_name": last_pass.get("name"),
                "last_completed_pass_class": last_pass.get("class"),
                "last_completed_pass_index": last_pass.get("index"),
                "last_completed_pass_duration_seconds": last_pass.get(
                    "qiskit_reported_duration_seconds"
                ),
                "last_completed_pass_wall_elapsed_seconds": last_pass.get(
                    "wall_elapsed_seconds"
                ),
                "interrupted_pass_file": interrupted.get("file"),
                "interrupted_pass_function": interrupted.get("function"),
                "interrupted_pass_line": interrupted.get("line"),
                "inferred_qiskit_stage": inference.get("qiskit_stage"),
                "inferred_configuration_component": component.get("name"),
                "inferred_configuration_value": component.get("value"),
                "inference_confidence": inference.get("confidence"),
                "causal_attribution_supported": inference.get(
                    "causal_attribution_supported"
                ),
                "diagnostic_limitations": " | ".join(map(str, limitations)),
                "last_relevant_qiskit_frame": interrupted_text,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["status"]),
            str(row["config_id"]),
            str(row["circuit_id"]),
            int(row["seed"] or 0),
        ),
    )


def write_failure_csv(
    path: Path,
    runs: Sequence[Mapping[str, Any]],
    device_id: str | None = None,
) -> int:
    """Write the canonical failure view and return its number of rows."""
    rows = failure_detail_rows(runs, device_id)
    _csv(path, rows, FAILURE_FIELDS)
    return len(rows)


def _failure_breakdown(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        (
            str(row.get("phase") or "unknown"),
            str(row.get("category") or "unknown"),
            str(row.get("exception_type") or "unknown"),
        )
        for row in rows
    )
    return [
        {
            "phase": phase,
            "category": category,
            "exception_type": exception_type,
            "count": count,
        }
        for (phase, category, exception_type), count in sorted(counts.items())
    ]


def _timeout_sensitivity(runs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    totals = _finite(
        run.get("timings_seconds", {}).get("total")
        for run in runs
        if run.get("status") == "success"
    )
    observed_timeouts = sum(run.get("status") == "timeout" for run in runs)
    return [
        {
            "threshold_seconds": threshold,
            "successful_runs_above_threshold": sum(total > threshold for total in totals),
            "actual_timeouts_already_observed": observed_timeouts,
            "lower_bound_timeouts_if_threshold_used": observed_timeouts
            + sum(total > threshold for total in totals),
        }
        for threshold in (30, 60, 100, 120, 300, 600, 900)
    ]


def _pilot_markdown(summary: Mapping[str, Any]) -> str:
    coverage = summary["circuit_coverage"]
    execution = summary["execution"]
    attempts = summary["attempts"]
    timing = summary["successful_transpilation_seconds"]
    ranking = summary["ranking"]
    versions = summary["provenance"]["versions"]
    lines = [
        f"# Pilot Qiskit — {summary['device']['device_id']}",
        "",
        (
            "Scheda generata automaticamente dagli artefatti del pilot. I tempi "
            "descrivono soltanto i tentativi riusciti e sono censurati dai timeout."
        ),
        "",
        "## Impostazione",
        "",
        _table(
            ("Campo", "Valore"),
            (
                ("Figure of merit", summary["objective"]),
                ("Qubit device", summary["device"].get("num_qubits")),
                ("Hash target", summary["device"].get("target_sha256")),
                ("Qiskit", versions.get("qiskit", "-")),
                ("MQT Bench", versions.get("mqt.bench", "-")),
                ("MQT Predictor", versions.get("mqt.predictor", "-")),
                ("Circuiti totali", coverage["total"]),
                ("Circuiti compatibili", coverage["compatible"]),
                ("Circuiti incompatibili", coverage["incompatible"]),
                ("Configurazioni", summary["configuration_count"]),
                ("Seed", ", ".join(map(str, summary["seeds"]))),
                ("Worker", execution.get("workers", "-")),
                ("Timeout richiesto", _num(execution.get("timeout_seconds")) + " s"),
                ("Cache hit", execution.get("cache_hits", "-")),
                (
                    "Durata invocazione",
                    _num(execution.get("wall_clock_seconds_this_invocation")) + " s",
                ),
            ),
        ),
        "",
        (
            "La durata invocazione riguarda il comando corrente. Se Cache hit "
            "è maggiore di zero, i record conservano i tempi delle esecuzioni "
            "originali e non sono stati ricompilati."
        ),
        "",
        "## Esito complessivo",
        "",
        _table(
            ("Tentativi", "N", "Percentuale su osservati"),
            (
                ("Pianificati", attempts["planned"], "-"),
                ("Osservati", attempts["observed"], "100.0%"),
                ("Mancanti", attempts["missing"], "-"),
                ("Successi", attempts["success"], _pct(attempts["success_rate"])),
                (
                    "Failure",
                    attempts["failure"],
                    _pct(_rate(attempts["failure"], attempts["observed"])),
                ),
                (
                    "Timeout",
                    attempts["timeout"],
                    _pct(_rate(attempts["timeout"], attempts["observed"])),
                ),
            ),
        ),
        "",
        "## Tempi di transpilation dei successi",
        "",
        _table(
            ("Gruppo", "N", "Min s", "Mediana s", "Media s", "P95 s", "Max s"),
            (
                (
                    label,
                    values["count"],
                    _num(values["min"]),
                    _num(values["median"]),
                    _num(values["mean"]),
                    _num(values["p95"]),
                    _num(values["max"]),
                )
                for label, values in (
                    ("Tutti", timing["all"]),
                    ("Non-lookahead", timing["non_lookahead"]),
                    ("Lookahead", timing["lookahead"]),
                )
            ),
        ),
        "",
        (
            "I timeout non hanno un tempo di transpilation concluso e non entrano "
            "nella tabella: il timeout rate va sempre letto insieme ai tempi."
        ),
        "",
        "## Configurazioni",
        "",
        _table(
            (
                "Config",
                "Studio",
                "O",
                "Layout",
                "Routing",
                "Ok/Obs",
                "Timeout",
                "Mediana s",
                "P95 s",
                "Max s",
                "Eleggibili",
                "Vittorie",
                "Co-vittorie",
                "Top 3",
            ),
            (
                (
                    row["config_id"],
                    row["study"],
                    row["optimization_level"],
                    row["layout_method"] or "default",
                    row["routing_method"] or "default",
                    f"{row['success_count']}/{row['attempts_observed']}",
                    row["timeout_count"],
                    _num(row["transpile_median_s"]),
                    _num(row["transpile_p95_s"]),
                    _num(row["transpile_max_s"]),
                    row["circuits_eligible"],
                    row["rank1_count"],
                    row["co_winner_count"],
                    row["top3_count"],
                )
                for row in summary["configurations"]
            ),
        ),
        "",
        (
            "Le vittorie applicano il tie-break del catalogo; le co-vittorie "
            "considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15."
        ),
        "",
        "## Circuiti",
        "",
        _table(
            (
                "Circuito",
                "Split",
                "Qubit",
                "Ok/Obs",
                "Timeout",
                "Mediana s",
                "P95 s",
                "Max s",
                "Config eleggibili",
                "Migliore",
            ),
            (
                (
                    row["circuit_id"],
                    row["split"],
                    row["num_qubits"],
                    f"{row['success_count']}/{row['attempts_observed']}",
                    row["timeout_count"],
                    _num(row["transpile_median_s"]),
                    _num(row["transpile_p95_s"]),
                    _num(row["transpile_max_s"]),
                    row["eligible_configurations"],
                    row["best_config_id"] or "-",
                )
                for row in summary["circuits"]
            ),
        ),
        "",
        "## Failure e timeout",
        "",
    ]
    if summary["failure_breakdown"]:
        lines.append(
            _table(
                ("Fase", "Categoria", "Eccezione", "N"),
                (
                    (
                        row["phase"],
                        row["category"],
                        row["exception_type"],
                        row["count"],
                    )
                    for row in summary["failure_breakdown"]
                ),
            )
        )
    else:
        lines.append("Nessun failure o timeout osservato.")
    lines += [
        "",
        "## Sensibilità a soglie alternative",
        "",
        _table(
            (
                "Soglia s",
                "Successi sopra soglia",
                "Timeout già osservati",
                "Lower bound timeout",
            ),
            (
                (
                    row["threshold_seconds"],
                    row["successful_runs_above_threshold"],
                    row["actual_timeouts_already_observed"],
                    row["lower_bound_timeouts_if_threshold_used"],
                )
                for row in summary["timeout_sensitivity"]
            ),
        ),
        "",
        (
            "La stima è conservativa: un run già interrotto è censurato e non "
            "rivela se sarebbe terminato con una soglia più alta."
        ),
        "",
        "## Copertura ranking",
        "",
        _table(
            ("Aggregati", "N"),
            (
                ("Eleggibili", ranking["eligible_aggregates"]),
                ("Non eleggibili", ranking["ineligible_aggregates"]),
                ("Esempi RAG", ranking["rag_examples"]),
            ),
        ),
        "",
        (
            "La expected_fidelity è una stima deterministica sul Target sintetico "
            "di MQT Bench, non una misura raccolta su hardware quantistico reale."
        ),
        "",
    ]
    return "\n".join(lines)


def build_device_comparison(pilot_root: Path) -> dict[str, Any]:
    paths = sorted(pilot_root.glob("*/reports/pilot_summary.json"))
    pairs = [(path, _json(path)) for path in paths if path.is_file()]
    pairs = [(path, summary) for path, summary in pairs if summary]
    if not pairs:
        return {"devices": 0, "outputs": {}}

    compatible_sets = [
        {str(row["circuit_id"]) for row in summary["circuits"]}
        for _, summary in pairs
    ]
    common = set.intersection(*compatible_sets)
    rows: list[dict[str, Any]] = []
    for path, summary in pairs:
        runs = read_jsonl(path.parents[1] / "qiskit_runs.jsonl")
        common_runs = [
            run for run in runs if str(run["circuit"]["circuit_id"]) in common
        ]
        common_status = _statuses(common_runs)
        common_timing = _stats(_success_times(common_runs))
        attempts = summary["attempts"]
        timing = summary["successful_transpilation_seconds"]["all"]
        ranking = summary["ranking"]
        rows.append(
            {
                "device_id": summary["device"]["device_id"],
                "device_num_qubits": summary["device"].get("num_qubits"),
                "workers": summary["execution"].get("workers"),
                "timeout_seconds": summary["execution"].get("timeout_seconds"),
                "compatible_circuits": summary["circuit_coverage"]["compatible"],
                "incompatible_circuits": summary["circuit_coverage"]["incompatible"],
                "attempts_planned": attempts["planned"],
                "attempts_observed": attempts["observed"],
                "success_count": attempts["success"],
                "failure_count": attempts["failure"],
                "timeout_count": attempts["timeout"],
                "success_rate": attempts["success_rate"],
                "transpile_median_s": timing["median"],
                "transpile_mean_s": timing["mean"],
                "transpile_p95_s": timing["p95"],
                "transpile_max_s": timing["max"],
                "eligible_aggregates": ranking["eligible_aggregates"],
                "ineligible_aggregates": ranking["ineligible_aggregates"],
                "common_circuits": len(common),
                "common_attempts_observed": len(common_runs),
                "common_success_count": common_status["success"],
                "common_failure_count": common_status["failure"],
                "common_timeout_count": common_status["timeout"],
                "common_success_rate": _rate(common_status["success"], len(common_runs)),
                "common_transpile_median_s": common_timing["median"],
                "common_transpile_mean_s": common_timing["mean"],
                "common_transpile_p95_s": common_timing["p95"],
                "common_transpile_max_s": common_timing["max"],
            }
        )
    rows.sort(key=lambda row: str(row["device_id"]))
    csv_path = pilot_root / "device_comparison.csv"
    markdown_path = pilot_root / "device_comparison.md"
    _csv(csv_path, rows, COMPARISON_FIELDS)
    markdown = "\n".join(
        [
            "# Confronto pilot per device",
            "",
            (
                "La prima tabella usa tutti i circuiti compatibili con ciascun "
                "device. La seconda usa soltanto l'intersezione comune di "
                f"{len(common)} circuiti."
            ),
            "",
            "## Tutti i circuiti compatibili",
            "",
            _table(
                (
                    "Device",
                    "Qubit",
                    "Worker",
                    "Timeout s",
                    "Circuiti",
                    "Ok/Obs",
                    "Timeout",
                    "Successo",
                    "Mediana s",
                    "P95 s",
                    "Max s",
                    "Aggregati eleggibili",
                ),
                (
                    (
                        row["device_id"],
                        row["device_num_qubits"],
                        row["workers"],
                        _num(row["timeout_seconds"]),
                        row["compatible_circuits"],
                        f"{row['success_count']}/{row['attempts_observed']}",
                        row["timeout_count"],
                        _pct(row["success_rate"]),
                        _num(row["transpile_median_s"]),
                        _num(row["transpile_p95_s"]),
                        _num(row["transpile_max_s"]),
                        row["eligible_aggregates"],
                    )
                    for row in rows
                ),
            ),
            "",
            "## Sottoinsieme comune",
            "",
            _table(
                (
                    "Device",
                    "Circuiti",
                    "Ok/Obs",
                    "Failure",
                    "Timeout",
                    "Successo",
                    "Mediana s",
                    "P95 s",
                    "Max s",
                ),
                (
                    (
                        row["device_id"],
                        row["common_circuits"],
                        (
                            f"{row['common_success_count']}/"
                            f"{row['common_attempts_observed']}"
                        ),
                        row["common_failure_count"],
                        row["common_timeout_count"],
                        _pct(row["common_success_rate"]),
                        _num(row["common_transpile_median_s"]),
                        _num(row["common_transpile_p95_s"]),
                        _num(row["common_transpile_max_s"]),
                    )
                    for row in rows
                ),
            ),
            "",
            (
                "Per tempi confrontabili, usare lo stesso timeout e numero di "
                "worker ed eseguire i pilot senza altri pilot concorrenti."
            ),
            "",
        ]
    )
    atomic_text_write(markdown_path, markdown)
    return {
        "devices": len(rows),
        "common_circuit_ids": sorted(common),
        "outputs": {"markdown": str(markdown_path), "csv": str(csv_path)},
    }


def build_pilot_report(
    output_root: Path, catalog: ConfigurationCatalog
) -> dict[str, Any]:
    manifest = _json(output_root / "split_manifest.json")
    if not manifest:
        raise FileNotFoundError(output_root / "split_manifest.json")
    if manifest.get("dataset_scope") != "pilot":
        raise ValueError("Il report pilot richiede un manifest scope=pilot.")

    runs = read_jsonl(output_root / "qiskit_runs.jsonl")
    summaries = read_jsonl(
        output_root / "qiskit_configuration_aggregates.jsonl"
    )
    status = _json(output_root / "generation_status.json")
    device_id = catalog.require_device(str(manifest["device_id"]))
    compatible = int(
        manifest["counts"].get("compatible_circuits", len(manifest["circuits"]))
    )
    incompatible = int(manifest["counts"].get("incompatible_circuits", 0))
    run_status = _statuses(runs)
    configuration_rows = _configuration_rows(
        catalog, device_id, compatible, runs, summaries
    )
    circuit_rows = _circuit_rows(
        catalog, device_id, manifest, runs, summaries
    )
    failure_rows = failure_detail_rows(runs, device_id)
    eligible = sum(bool(item.get("eligible_for_ranking")) for item in summaries)
    policy = status.get("execution_policy") or {}
    observed = len(runs)
    planned = int(
        manifest["counts"].get(
            "attempts_planned",
            compatible * len(catalog.configurations) * len(catalog.seeds),
        )
    )
    execution = {
        "workers": policy.get("workers"),
        "timeout_seconds": policy.get("timeout_seconds"),
        "wall_clock_seconds_this_invocation": policy.get(
            "wall_clock_seconds_this_invocation"
        ),
        "cache_hits": status.get("cache_hits"),
        "executed_now": status.get("executed_now"),
        "observed_timeout_seconds": sorted(
            {
                float(row["timeout_seconds"])
                for row in failure_rows
                if row.get("timeout_seconds") is not None
            }
        ),
    }
    lookahead = [
        run
        for run in runs
        if run.get("configuration", {}).get("routing_method") == "lookahead"
    ]
    non_lookahead = [
        run
        for run in runs
        if run.get("configuration", {}).get("routing_method") != "lookahead"
    ]
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "qiskit_pilot",
        "objective": manifest["objective"]["name"],
        "device": {
            "device_id": device_id,
            "num_qubits": manifest.get(
                "device_num_qubits", status.get("target", {}).get("num_qubits")
            ),
            "target_sha256": status.get("target", {}).get("target_sha256"),
        },
        "catalog_id": catalog.catalog_id,
        "configuration_count": len(catalog.configurations),
        "seeds": list(catalog.seeds),
        "circuit_coverage": {
            "total": len(manifest["circuits"]),
            "compatible": compatible,
            "incompatible": incompatible,
            "incompatible_circuit_ids": [
                circuit["circuit_id"]
                for circuit in manifest["circuits"]
                if circuit.get("device_compatibility", {}).get("compatible") is False
            ],
        },
        "execution": execution,
        "attempts": {
            "planned": planned,
            "observed": observed,
            "missing": max(0, planned - observed),
            "success": run_status["success"],
            "failure": run_status["failure"],
            "timeout": run_status["timeout"],
            "success_rate": _rate(run_status["success"], observed),
        },
        "successful_transpilation_seconds": {
            "all": _stats(_success_times(runs)),
            "non_lookahead": _stats(_success_times(non_lookahead)),
            "lookahead": _stats(_success_times(lookahead)),
        },
        "ranking": {
            "eligible_aggregates": eligible,
            "ineligible_aggregates": len(summaries) - eligible,
            "rag_examples": len(read_jsonl(output_root / "rag_examples.jsonl")),
        },
        "configurations": configuration_rows,
        "circuits": circuit_rows,
        "failure_breakdown": _failure_breakdown(failure_rows),
        "timeout_sensitivity": _timeout_sensitivity(runs),
        "provenance": {
            "manifest_id": manifest.get("manifest_id"),
            "versions": manifest.get("provenance", {}).get("versions", {}),
        },
    }

    report_root = output_root / "reports"
    paths = {
        "markdown": report_root / "pilot_report.md",
        "summary_json": report_root / "pilot_summary.json",
        "configuration_csv": report_root / "configuration_statistics.csv",
        "circuit_csv": report_root / "circuit_statistics.csv",
        "failure_csv": report_root / "failure_details.csv",
    }
    atomic_json_write(paths["summary_json"], summary)
    atomic_text_write(paths["markdown"], _pilot_markdown(summary))
    _csv(paths["configuration_csv"], configuration_rows, CONFIG_FIELDS)
    _csv(paths["circuit_csv"], circuit_rows, CIRCUIT_FIELDS)
    write_failure_csv(paths["failure_csv"], runs, device_id)
    comparison = build_device_comparison(output_root.parent)
    return {
        "device_id": device_id,
        "outputs": {name: str(path) for name, path in paths.items()},
        "comparison": comparison,
    }

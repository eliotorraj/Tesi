"""Analisi post-sigillo: riferimento osservato sugli 88 circuiti."""
from __future__ import annotations
from collections import defaultdict, Counter
from statistics import median
from pathlib import Path
from llm_selection.common import ROOT, read_json, write_json, digest
from llm_selection.study import immutable_json, verify_hashes
from llm_selection.evaluate import episode_data, attach_resources, complete_sum, write_csv
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import dataset_scope_root
from qiskit_dataset.experiment_v2 import (
    source_manifest, device_capacities, load_jsonl, evaluate_common_methods,
    validate_llm_decisions, validate_method_plan, ORACLE_METHOD_ID)
from scripts.mqt_predictor_protocol import EXPERIMENT_ID, METHOD_PLAN_DIR_V2, file_sha256
from .settings import study_root, MODEL_KEYS
from .study import require_sealed

def matrix_paths():
    base = dataset_scope_root("expected_fidelity", "full", experiment_id=EXPERIMENT_ID) / "global"
    return base / "qiskit_runs.jsonl", base / "qiskit_configuration_aggregates.jsonl"

def observed_references(aggregates):
    grouped = defaultdict(list)
    for item in aggregates:
        if item["split"] == "validation":
            grouped[item["circuit"]["source_sha256"]].append(item)
    result = {}
    for source, rows in grouped.items():
        eligible = [r for r in rows if r["eligible_for_ranking"]
                    and r["attempts"]["success_count"] == 3 and r["attempts"]["observed_count"] == 3
                    and {s["seed_transpiler"] for s in r["score_observations"]} == {0, 1, 2}
                    and isinstance(r["ranking_score"], (int, float))]
        best = max((r["ranking_score"] for r in eligible), default=None)
        result[source] = {
            "source_sha256": source, "circuit_id": rows[0]["circuit"]["circuit_id"],
            "reference_kind": "best_observed_successful_median", "score": best,
            "eligible_pairs": len(eligible), "total_pairs": len(rows),
            "matrix_complete": len(eligible) == len(rows),
            "best_pairs": [{"device_id": r["device"]["device_id"], "config_id": r["configuration"]["config_id"]}
                           for r in eligible if r["ranking_score"] == best],
        }
    return result

def enrich_costs(row, folder):
    attempts = [read_json(p) for p in sorted(folder.glob("attempt_*/summary.json"))]
    physical = [a.get("response") for a in attempts if a.get("llm_calls")]
    for path in sorted((folder / "interrupted").glob("attempt_*/*")):
        if not (path / "call/request.json").exists():
            continue
        response = read_json(path / "call/response.json") if (path / "call/response.json").exists() else None
        physical.append(response)
        start = read_json(path / "started.json") if (path / "started.json").exists() else {}
        if response and response.get("started_at") and response.get("ended_at") and start.get("resource_run_key"):
            row["attempt_windows"].append((start["resource_run_key"], response["started_at"], response["ended_at"]))
    for key, usage_key in (("total_input_tokens", "prompt_tokens"), ("total_output_tokens", "completion_tokens")):
        values = [(r.get("usage") or {}).get(usage_key) if r else None for r in physical]
        row[key] = complete_sum(values)
        row[key + "_observed"] = sum(v for v in values if v is not None)
    row["total_call_seconds"] = complete_sum([r.get("elapsed_seconds") if r else None for r in physical])
    row["physical_calls"] = len(physical)
    row["first_attempt_facts_verified"] = attempts[0].get("facts_status") == "verified"
    row["fact_validation_seconds"] = sum(a.get("validation_seconds", 0) for a in attempts)
    row["facts_checked"] = sum(len(a.get("fact_checks", [])) for a in attempts)
    row["facts_verified"] = sum(c["result"] == "verified" for a in attempts for c in a.get("fact_checks", []))
    row["hypothesis_contains_example_ids"] = attempts[-1].get("hypothesis_contains_example_ids", False)
    row["schema_version"] = "study-results-v2"
    return attempts

def summarize(rows):
    regrets = [r["regret_absolute"] for r in rows if r["regret_absolute"] is not None]
    return {"circuits": len(rows), "valid_and_compilable": sum(r["status"] == "success" for r in rows),
            "regret_available": len(regrets), "median_regret_absolute": median(regrets) if regrets else None,
            "regret_source_hashes": sorted(r["source_sha256"] for r in rows if r["regret_absolute"] is not None),
            "first_attempt_facts_verified": sum(r["first_attempt_facts_verified"] for r in rows),
            "final_facts_verified": sum(r["facts_status"] == "verified" for r in rows),
            "accepted_unverified_facts": sum(r["accepted_with_unverified_facts"] for r in rows),
            "repairs": sum(r["repair_count"] for r in rows),
            "physical_calls": sum(r["physical_calls"] for r in rows),
            "interruptions": sum(r["transport_retries"] for r in rows),
            "total_call_seconds": complete_sum([r["total_call_seconds"] for r in rows]),
            "total_output_tokens": complete_sum([r["total_output_tokens"] for r in rows]),
            "facts_checked": sum(r["facts_checked"] for r in rows),
            "facts_verified": sum(r["facts_verified"] for r in rows),
            "failures": dict(Counter(r["failure_category"] for r in rows if r["failure_category"]))}

def choose(trials):
    summaries = {k: summarize(v) for k, v in trials.items()}
    eligible, steps = sorted(trials), []
    best = max(summaries[k]["valid_and_compilable"] for k in eligible)
    if best == 0:
        return {"winner": None, "summaries": summaries, "steps": [], "reason": "No compilable decision"}
    eligible = [k for k in eligible if summaries[k]["valid_and_compilable"] == best]
    steps.append({"criterion": "valid_and_compilable", "best": best, "remaining": eligible[:]})
    common = set.intersection(*[{r["source_sha256"] for r in trials[k] if r["regret_absolute"] is not None} for k in eligible])
    if len(eligible) > 1 and common:
        values = {k: median(r["regret_absolute"] for r in trials[k] if r["source_sha256"] in common) for k in eligible}
        best_value = min(values.values())
        eligible = [k for k in eligible if values[k] == best_value]
        steps.append({"criterion": "median_observed_regret_common", "values": values,
                      "source_hashes": sorted(common), "n": len(common), "remaining": eligible[:]})
    else:
        steps.append({"criterion": "median_observed_regret_common", "applied": False,
                      "common_count": len(common), "reason": "single candidate" if len(eligible) == 1 else "no common evaluable circuit"})
    for field in ("repairs", "physical_calls", "total_call_seconds", "total_output_tokens"):
        if len(eligible) == 1:
            break
        values = {k: summaries[k][field] for k in eligible}
        if any(v is None for v in values.values()):
            steps.append({"criterion": field, "applied": False, "reason": "incomplete measurement", "values": values})
            continue
        best_value = min(values.values())
        eligible = [k for k in eligible if values[k] == best_value]
        steps.append({"criterion": field, "values": values, "remaining": eligible[:]})
    if len(eligible) > 1:
        steps.append({"criterion": "lexicographic", "remaining": eligible[:]})
    return {"winner": min(eligible), "summaries": summaries, "steps": steps,
            "regret_common_source_hashes": sorted(common)}

def evaluate(study_id):
    study = require_sealed(study_id)  # Mandatory gate before reading any matrix scores.
    root = study_root(study_id)
    out = root / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    catalog, manifest, capacities = load_catalog(), source_manifest(), device_capacities()
    plan = read_json(METHOD_PLAN_DIR_V2 / "validation_method_plan.json")
    validate_method_plan(plan, split="validation", catalog=catalog, manifest=manifest, capacities=capacities)
    prepared, facts = {}, []
    for model in MODEL_KEYS:
        for config in study["configurations"]:
            trial = model + "/" + config["id"]
            rows, records = [], []
            descriptor = {"study_sha256": digest(study), "model": model, "configuration": config}
            for p in sorted((root / model / config["id"]).glob("*/decision.json")):
                row, record = episode_data(p.parent, trial)
                attempts = enrich_costs(row, p.parent)
                record["method_config_sha256"] = digest(descriptor)
                record["usage"].update(input_tokens=row["total_input_tokens"], output_tokens=row["total_output_tokens"])
                record["timings_seconds"]["llm_calls"] = row["total_call_seconds"]
                rows.append(row)
                records.append(record)
                for attempt in attempts:
                    for fact in attempt.get("fact_checks", []):
                        facts.append({"trial_id": trial, "circuit_id": row["circuit_id"],
                                      "attempt": attempt["attempt"], **fact})
            valid = validate_llm_decisions(records, method_id="llm_rag", split="validation",
                       catalog=catalog, manifest=manifest, capacities=capacities,
                       method_config={"methods": {"llm_rag": {"max_attempts": study["max_attempts"]}}},
                       method_config_sha256=digest(descriptor))
            prepared[trial] = rows, valid, descriptor
    run_path, aggregate_path = matrix_paths()
    verify_hashes(ROOT, study["evaluation_input_hashes"])
    runs, aggregates = load_jsonl(run_path), load_jsonl(aggregate_path)
    if any(r["split"] == "test" for r in [*runs, *aggregates]):
        raise ValueError("Unexpected test scores")
    references = observed_references(aggregates)
    expected = {r["source_sha256"] for r in manifest["circuits"] if r["split"] == "validation"}
    if set(references) != expected or any(r["score"] is None for r in references.values()):
        raise ValueError("Observed reference does not cover exactly all 88 circuits")
    trials, baselines = {}, None
    for trial, (rows, records, descriptor) in prepared.items():
        results = evaluate_common_methods(split="validation", catalog=catalog, manifest=manifest,
                    plan=plan, capacities=capacities, qiskit_runs=runs, qiskit_summaries=aggregates,
                    llm_decisions={"llm_rag": records}, qcompile_runs=[],
                    method_config_sha256=digest(descriptor), llm_method_ids=("llm_rag",), include_qcompile=False)
        if baselines is None:
            baselines = [r for r in results if r["method_id"] != "llm_rag"]
        scored = {r["source_sha256"]: r for r in results if r["method_id"] == "llm_rag"}
        for row in rows:
            old = scored[row["source_sha256"]]
            row["decision_status"] = row["status"]
            row.update(old)
            row["trial_id"] = trial
            row["regret_exhaustive_absolute"] = old["regret_absolute"]
            row["reference_score_observed"] = references[row["source_sha256"]]["score"]
            row["reference_kind"] = "best_observed_successful_median"
            row["regret_absolute"] = row["reference_score_observed"] - row["score"] if row["score"] is not None else None
            row["regret_relative"] = row["regret_absolute"] / row["reference_score_observed"] if row["regret_absolute"] is not None and row["reference_score_observed"] else None
            row["regret_unavailable_reason"] = None if row["regret_absolute"] is not None else row.get("failure_category")
            row["matrix_complete"] = references[row["source_sha256"]]["matrix_complete"]
        trials[trial] = rows
    all_rows = [r for rows in trials.values() for r in rows]
    attach_resources(all_rows)
    selection = choose(trials)
    for name, value in (("episode_results.json", all_rows), ("baseline_results_exhaustive.json", baselines),
                        ("selection.json", selection)):
        immutable_json(out / name, value)
    for name, records in (("reference_scores.jsonl", list(references.values())), ("fact_checks.jsonl", facts)):
        content = "".join(__import__("json").dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)
        path = out / name
        if path.exists() and path.read_text() != content:
            raise ValueError("Analysis inputs changed")
        path.write_text(content)
    write_csv(out / "episodes.csv", all_rows)
    write_csv(out / "trials.csv", [{"trial_id": k, **v} for k, v in selection["summaries"].items()])
    immutable_json(out / "input_fingerprints.json", {
        "study": file_sha256(root / "frozen_study.json"), "matrix": study["evaluation_input_hashes"],
        "server_resources": {k: v for r in all_rows for k, v in r.get("server_resource_sources", {}).items()}})
    if selection["winner"]:
        model, config_id = selection["winner"].split("/")
        final = {"schema_version": "2.0.0", "study_id": study_id, "winner": selection["winner"],
                 "configuration": next(c for c in study["configurations"] if c["id"] == config_id),
                 "profile": study["models"][model], "fixed": study["fixed"], "policy": study["policy"],
                 "study_sha256": digest(study), "selection_sha256": digest(selection), "test_released": False}
        immutable_json(root / "final_configuration.json", final)
        immutable_json(root / "selection_complete.json", {
            "study_id": study_id, "winner": selection["winner"], "test_released": False,
            "files": {str(p.relative_to(ROOT)): file_sha256(p) for p in
                      [root / "final_configuration.json", root / "all_decisions_sealed.json", *sorted(out.glob("*.json")), *sorted(out.glob("*.jsonl"))]}})
    return selection

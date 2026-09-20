"""Episodi v4. Le interruzioni fisiche non consumano tentativi logici."""
from __future__ import annotations
import argparse
import fcntl
import time
from pathlib import Path
from uuid import uuid4
from llm_selection.common import ROOT, OUTPUT, read_json, write_json, digest, now
from llm_selection.gateway import audit_tokens, generate, native_payload
from llm_selection.run import prepare_context
from llm_selection.provenance import code_hashes, capture
from llm_selection.study import verify_launch
from prototype.prompting.facts import audit, verify as verify_facts, REVISION
from .settings import CONFIGURATIONS, TIMEOUT_SECONDS, MAX_ATTEMPTS, payload, study_root
from .study import verify, prompt_files, seal_model

class RetryableInterruption(RuntimeError):
    pass

def archive_interrupted(directory, attempt, reason):
    """Move within this episode only; retain every byte and physical-call provenance."""
    directory, attempt = Path(directory).resolve(), Path(attempt).resolve()
    if attempt.parent != directory or not attempt.name.startswith("attempt_"):
        raise ValueError("Archive source outside episode")
    parent = directory / "interrupted" / attempt.name
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / uuid4().hex
    attempt.rename(destination)
    write_json(destination / "interruption.json",
               {"at": now(), "logical_attempt": int(attempt.name.split("_")[-1]),
                "reason": reason, "consumes_attempt": False,
                "physical_generation_dispatched": (destination / "call/request.json").exists()})
    return destination

def resource_interruption(launch):
    root = Path(launch["run_directory"])
    return any((root / f).exists() for f in ("resource_abort.json", "monitor_error.json"))

def assess(response, prompt, number, input_tokens):
    result = {"attempt": number, "input_tokens": input_tokens, "response": response, "llm_calls": 1}
    if not response.get("transport_success"):
        result.update(status="timeout" if response.get("curl_exit_code") == 28 else "transport_failure",
                      issues=[], failure={"category": "timeout" if response.get("curl_exit_code") == 28 else "transport_failure"})
        return result
    checked = verify_facts(response["content"], prompt)
    result.update(checked)
    result["status"] = "success" if checked["schema_valid"] and checked["selection_valid"] and checked["facts_status"] == "verified" else "invalid_output"
    if checked["selection_valid"]:
        result["selected_device_id"] = checked["canonical_response"]["selected_device"]
        result["selected_config_id"] = checked["canonical_response"]["config_id"]
    return result

def eligible_fallback(summary):
    return (summary.get("response", {}).get("transport_success") is True
            and summary.get("schema_valid") is True and summary.get("selection_valid") is True
            and summary.get("facts_status") == "unverified")

def episode(directory, saved, configuration, launch, *, runtime_hashes=None, context_seconds=0):
    directory = Path(directory)
    request_hash = digest(payload(saved["prompt"], configuration))
    hashes = runtime_hashes if runtime_hashes is not None else code_hashes()
    header = {"circuit_id": saved["circuit_id"], "source_sha256": saved["source_sha256"],
              "split": saved["circuit_metadata"]["split"], "circuit_metadata": saved["circuit_metadata"],
              "configuration": configuration, "code_hashes": hashes,
              "initial_request_sha256": request_hash, "input_prompt_sha256": saved["prompt_sha256"],
              "prompt_encoding_revision": REVISION, "max_attempts": MAX_ATTEMPTS,
              "timeout_seconds": TIMEOUT_SECONDS, "launch": launch,
              "retrieval_and_context_seconds": context_seconds}
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "begin.json").exists():
        previous = read_json(directory / "begin.json")
        for key in ("code_hashes", "initial_request_sha256", "input_prompt_sha256", "configuration", "max_attempts", "timeout_seconds"):
            if previous[key] != header[key]:
                raise ValueError(f"Cannot reuse episode with changed {key}")
    else:
        write_json(directory / "begin.json", {**header, "created_at": now()})
    if (directory / "decision.json").exists():
        return read_json(directory / "decision.json")
    summaries, feedback = [], []
    for number in range(1, MAX_ATTEMPTS + 1):
        folder = directory / f"attempt_{number}"
        summary_file = folder / "summary.json"
        if summary_file.exists():
            summary = read_json(summary_file)
            if summary["status"] in ("transport_failure", "interrupted"):
                archive_interrupted(directory, folder, summary["status"])
                raise RetryableInterruption("Incomplete call archived; repeat same logical attempt")
        elif folder.exists() and (folder / "call/response.json").exists():
            try:
                response = read_json(folder / "call/response.json")
                if not response.get("transport_success"):
                    if response.get("curl_exit_code") != 28 or resource_interruption(launch):
                        archive_interrupted(directory, folder, "recovered_transport_interruption")
                        raise RetryableInterruption("Recovered interrupted call")
                if read_json(folder / "encoding.json") != audit(saved["prompt"]):
                    raise ValueError("Recorded context changed")
                token_path = folder / "audit/tokenizer/response.json"
                count = len(read_json(token_path)["tokens"]) if token_path.exists() else None
                summary = assess(response, saved["prompt"], number, count)
                summary["recovered_completed_response"] = True
            except (ValueError, KeyError):
                archive_interrupted(directory, folder, "incomplete_persisted_response")
                raise RetryableInterruption("Incomplete persisted response") from None
        elif folder.exists():
            archive_interrupted(directory, folder, "process_interrupted_before_durable_response")
            raise RetryableInterruption("Interrupted call archived")
        else:
            folder.mkdir()
            write_json(folder / "prompt.json", saved["prompt"])
            write_json(folder / "encoding.json", audit(saved["prompt"]))
            write_json(folder / "started.json", {"at": now(), "attempt": number,
                       "resource_run_key": launch["process_start_time"], "server_run_directory": launch["run_directory"]})
            if feedback:
                write_json(folder / "repair_feedback.json", feedback)
            request = payload(saved["prompt"], configuration, feedback)
            try:
                count = audit_tokens(request, folder / "audit")
                if count + request["max_tokens"] > int(launch["context"]):
                    summary = {"attempt": number, "status": "context_failure", "input_tokens": count,
                               "issues": [], "llm_calls": 0, "failure": {"category": "full_prompt_exceeds_context"}}
                else:
                    response = generate(native_payload(request, folder / "audit"), folder / "call", timeout=TIMEOUT_SECONDS)
                    summary = assess(response, saved["prompt"], number, count)
                    if summary["status"] == "transport_failure" or (summary["status"] == "timeout" and resource_interruption(launch)):
                        write_json(summary_file, summary)
                        archive_interrupted(directory, folder, "resource_interruption" if resource_interruption(launch) else "transport_failure")
                        raise RetryableInterruption("Call interrupted; logical attempt remains pending")
            except RetryableInterruption:
                raise
            except (KeyboardInterrupt, SystemExit):
                # Preserve a complete durable response if it already arrived.
                if not (folder / "call/response.json").exists():
                    archive_interrupted(directory, folder, "user_or_process_interruption")
                raise
            except Exception as error:
                write_json(folder / "infrastructure_error.json", {"at": now(), "type": type(error).__name__, "message": str(error)})
                if not (folder / "call/response.json").exists():
                    archive_interrupted(directory, folder, "infrastructure_interruption")
                raise RetryableInterruption(str(error)) from error
        start = read_json(folder / "started.json") if (folder / "started.json").exists() else {}
        summary["resource_run_key"] = start.get("resource_run_key", launch["process_start_time"])
        summary["server_run_directory"] = start.get("server_run_directory", launch["run_directory"])
        if "fact_checks" in summary:
            write_json(folder / "fact_validation.json", {k: v for k, v in summary.items()
                       if k in ("schema_version", "json_valid", "schema_valid", "selection_valid", "facts_status",
                                "fact_checks", "hypothesis_status", "explanation_fully_verified",
                                "hypothesis_contains_example_ids", "issues", "validation_seconds")})
        if number == MAX_ATTEMPTS and eligible_fallback(summary):
            summary["status"] = "success"
            summary["accepted_with_unverified_facts"] = True
        write_json(summary_file, summary)
        summaries.append(summary)
        if summary["status"] == "success" or summary["status"] != "invalid_output":
            break
        feedback = summary.get("issues", [])
    last = summaries[-1]
    success = last["status"] == "success"
    interrupted = sorted((directory / "interrupted").glob("attempt_*/*"))
    physical = [s.get("response") for s in summaries if s.get("llm_calls")]
    for folder in interrupted:
        if (folder / "call/request.json").exists():
            physical.append(read_json(folder / "call/response.json") if (folder / "call/response.json").exists() else None)
    complete_times = [r.get("elapsed_seconds") if r else None for r in physical]
    decision = {"status": "success" if success else ("timeout" if last["status"] == "timeout" else "failure"),
                "selected_device_id": last.get("selected_device_id") if success else None,
                "selected_config_id": last.get("selected_config_id") if success else None,
                "failure": None if success else last.get("failure", {"category": "invalid_output"}),
                "circuit_id": saved["circuit_id"], "source_sha256": saved["source_sha256"],
                "split": saved["circuit_metadata"]["split"], "configuration_id": configuration["id"],
                "attempt_count": len(summaries), "llm_calls": len(physical),
                "repair_count": max(0, len(summaries) - 1), "transport_retries": len(interrupted),
                "facts_status": last.get("facts_status", "not_evaluated"),
                "accepted_with_unverified_facts": last.get("accepted_with_unverified_facts", False),
                "hypothesis_status": "not_evaluated", "ended_at": now(),
                "measured_call_seconds": sum(complete_times) if all(t is not None for t in complete_times) else None,
                "measured_call_seconds_observed": sum(t for t in complete_times if t is not None),
                "attempts_sha256": digest(summaries), "input_prompt_sha256": saved["prompt_sha256"]}
    write_json(directory / "decision.json", decision)
    print(f'{configuration["id"]} {saved["circuit_id"]}: {decision["status"]}, facts={decision["facts_status"]}, attempts={len(summaries)}', flush=True)
    return decision

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True)
    parser.add_argument("--model", required=True, choices=("qwen", "phi", "gemma"))
    parser.add_argument("--server-run", required=True, type=Path)
    parser.add_argument("--technical", action="store_true")
    args = parser.parse_args()
    from scripts.mqt_predictor_protocol import TEST_RELEASE_RECORD, FROZEN_DEVICES
    if TEST_RELEASE_RECORD.exists():
        raise ValueError("Test already released")
    root = study_root(args.study)
    if args.technical and (root / "frozen_study.json").exists():
        raise ValueError("Technical phase closed after freeze")
    profiles = read_json(root / "profiles_to_freeze.json") if args.technical else verify(args.study)["models"]
    launch = read_json(args.server_run / "launch.json")
    launch["run_directory"] = str(args.server_run.resolve())
    verify_launch({"models": profiles}, args.model, launch)
    if args.model not in launch["model_path"].replace("\\", "/").split("/"):
        raise ValueError("Wrong model family")
    output = root / "technical" / args.model if args.technical else root / args.model
    lock = (OUTPUT / "execution.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    from prototype.quantum_assistant.factory import build_default_service
    from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
    service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway(), retrieval_limit=5)
    hashes = code_hashes()
    capture(output / "invocations" / now().replace(":", "-"))
    for index, path in enumerate(prompt_files(root, "train" if args.technical else "validation")):
        if (root / "stop_requested.json").exists() or (OUTPUT / "stop_requested.json").exists():
            raise SystemExit(75)
        saved = read_json(path)
        _, _, seconds = prepare_context(service, saved)
        configs = CONFIGURATIONS[index % 3:] + CONFIGURATIONS[:index % 3]
        for config in configs:
            episode(output / config["id"] / path.stem, saved, config, launch,
                    runtime_hashes=hashes, context_seconds=seconds)
    if not args.technical:
        seal_model(args.study, args.model)

if __name__ == "__main__":
    try:
        main()
    except RetryableInterruption as error:
        print(str(error), flush=True)
        raise SystemExit(76) from None

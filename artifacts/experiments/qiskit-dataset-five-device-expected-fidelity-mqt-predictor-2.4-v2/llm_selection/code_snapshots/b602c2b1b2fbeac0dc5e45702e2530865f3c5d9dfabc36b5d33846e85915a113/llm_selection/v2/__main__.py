"""Comandi per preparare, provare sul train e avviare uno studio esplicito."""
from __future__ import annotations
import argparse
import fcntl
import json
import subprocess
import sys
import time
from datetime import datetime
from llm_selection.common import OUTPUT, ROOT, now, read_json, write_json, append_jsonl
from llm_selection.controller import launch, stop, wait_runner, ps_command, ExperimentStopped
from llm_selection.provenance import code_hashes
from llm_selection.hardware import server_arguments
from llm_selection.study import verify_hashes
from scripts.mqt_predictor_protocol import TEST_RELEASE_RECORD
from .settings import study_root, MODEL_KEYS, POLICY
from .study import prepare, freeze, verify, require_sealed, verify_predecessor

def resources_ready(sample, guards):
    sensors = [s for s in sample.get("gpu_sensors", [])
               if s.get("hotspot_c") is not None and s.get("edge_c") is not None]
    return (bool(sensors)
            and sample.get("system_available_bytes", 0) >= guards["minimum_available_bytes"]
            and all(s["hotspot_c"] <= guards["resume_hotspot_c"]
                    and s["edge_c"] < guards["maximum_edge_c"] - 3 for s in sensors))

def wait_resources(root, profile, events):
    good = 0
    next_update = 0.0
    while good < 3:
        if (root / "stop_requested.json").exists() or (OUTPUT / "stop_requested.json").exists():
            raise KeyboardInterrupt
        result = subprocess.run(ps_command("resource_probe.ps1"), capture_output=True, text=True, timeout=25)
        try:
            if result.returncode:
                raise ValueError(result.stderr)
            sample = json.loads(result.stdout.lstrip("\ufeff"))
        except ValueError as error:
            append_jsonl(events, {"at": now(), "event": "resource_probe_error", "error": str(error)[:500]})
            good = 0
        else:
            ready = resources_ready(sample, profile["guards"])
            if time.monotonic() >= next_update:
                available = sample.get("system_available_bytes", 0) / 1024**3
                print(f"Risorse: RAM disponibile {available:.2f} GiB; recupero {good}/3 campioni.", flush=True)
                next_update = time.monotonic() + 30
            append_jsonl(events, {"at": now(), "event": "resource_recovery_sample", "ready": ready, **sample})
            good = good + 1 if ready else 0
        if good < 3:
            time.sleep(5)

def completed_model(root, model, technical):
    from .study import prompt_files
    from .settings import CONFIGURATIONS
    output = root / "technical" / model if technical else root / model
    if not technical:
        if not (output / "sealed.json").exists():
            return False
        seal = read_json(output / "sealed.json")
        verify_hashes(ROOT, seal["files"])
        return True
    hashes = code_hashes()
    for config in CONFIGURATIONS:
        for p in prompt_files(root, "train"):
            folder = output / config["id"] / p.stem
            if not (folder / "decision.json").exists():
                return False
            if read_json(folder / "begin.json")["code_hashes"] != hashes:
                raise ValueError("Technical code changed: preserve previous study and use a new study ID")
    return True

def supervise(study_id, *, technical):
    if TEST_RELEASE_RECORD.exists():
        raise ValueError("Test already released")
    root = study_root(study_id)
    if technical and (root / "frozen_study.json").exists():
        raise ValueError("Study already frozen")
    study = None if technical else verify(study_id)
    profiles = read_json(root / "profiles_to_freeze.json") if technical else study["models"]
    label = datetime.now().strftime("%Y%m%d-%H%M%S")
    directory = root / "controllers" / label
    directory.mkdir(parents=True, exist_ok=False)
    events = directory / "events.jsonl"
    lock = (OUTPUT / "controller.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    write_json(directory / "request.json", {"study": study_id, "technical": technical, "at": now()})
    for model in MODEL_KEYS:
        if completed_model(root, model, technical):
            print(model + ": episodi già completati e verificati.", flush=True)
            continue
        profile = profiles[model]
        server_arguments(profile)
        unexplained, recovery = 0, 0
        while True:
            if (root / "stop_requested.json").exists() or (OUTPUT / "stop_requested.json").exists():
                return
            wait_resources(root, profile, events)
            server_dir = OUTPUT / "servers" / f"{study_id}-{label}-{model}-{recovery}"
            monitor = None
            code = None
            with (directory / f"{model}-{recovery}.log").open("w") as log:
                try:
                    monitor = launch(model, profile, server_dir, log, events)
                    command = [sys.executable, "-m", "llm_selection.v2.run",
                               "--study", study_id, "--model", model, "--server-run", str(server_dir)]
                    if technical:
                        command.append("--technical")
                    code = wait_runner(command, log, server_dir)
                except ExperimentStopped:
                    if not (server_dir / "resource_abort.json").exists():
                        raise
                    code = 76
                finally:
                    stop(server_dir, "v2_controller_cycle_finished", log)
                    if monitor is not None:
                        monitor.wait(timeout=30)
            append_jsonl(events, {"at": now(), "event": "runner_ended", "model": model,
                                 "exit_code": code, "server_run": str(server_dir), "recovery": recovery})
            if code == 0:
                break
            if code == 75:
                return
            if code != 76:
                raise ExperimentStopped(f"Errore applicativo: controllare {directory / (model + '-' + str(recovery) + '.log')}")
            known = (server_dir / "resource_abort.json").exists()
            if not known:
                unexplained += 1
                if unexplained >= POLICY["unexplained_transport_restarts"]:
                    raise ExperimentStopped("Tre interruzioni senza causa di risorse accertata. Episodio sospeso e riprendibile; consultare " + str(directory))
            else:
                unexplained = 0
            recovery += 1
            print(model + ": chiamata interrotta archiviata. Attendo le risorse e ripeto lo stesso tentativo.", flush=True)
    if technical:
        rows = [read_json(p) for p in sorted((root / "technical").glob("*/*/*/decision.json"))]
        write_json(root / "technical_summary.json", {"episodes": len(rows),
                   "success": sum(r["status"] == "success" for r in rows),
                   "verified_facts": sum(r["facts_status"] == "verified" for r in rows),
                   "accepted_unverified_facts": sum(r["accepted_with_unverified_facts"] for r in rows),
                   "logical_attempts": sum(r["attempt_count"] for r in rows),
                   "physical_calls": sum(r["llm_calls"] for r in rows),
                   "repairs": sum(r["repair_count"] for r in rows),
                   "interruptions": sum(r["transport_retries"] for r in rows)})
        verify_predecessor(study_id)
        print(json.dumps(read_json(root / "technical_summary.json"), indent=2), flush=True)
    else:
        require_sealed(study_id)
        from .evaluate import evaluate
        from .report import build_report
        evaluate(study_id)
        build_report(study_id)
    write_json(directory / "finished.json", {"at": now(), "technical": technical})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "train", "freeze", "verify", "validate", "report"))
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.study))
    elif args.command == "train":
        supervise(args.study, technical=True)
    elif args.command == "freeze":
        print("Congelato:", freeze(args.study)["study_id"])
    elif args.command == "verify":
        print("Verificato:", verify(args.study)["study_id"])
        verify_predecessor(args.study)
    elif args.command == "validate":
        supervise(args.study, technical=False)
    else:
        from .report import build_report
        print(build_report(args.study))

if __name__ == "__main__":
    try:
        main()
    except ExperimentStopped as error:
        print(str(error), file=sys.stderr, flush=True)
        raise SystemExit(1) from None

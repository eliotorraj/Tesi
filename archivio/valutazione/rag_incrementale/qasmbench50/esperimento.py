'Sequential campaign on 50 QASMBench circuits; no inference without --esegui.'
from __future__ import annotations
import argparse
import platform
from comune import *
from registro import replay, finish_step, recover_interruption, export_memory


def preflight():
    from gates import software_targets
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    from common import STUDY
    # Check the selected artifacts actually used. Earlier validation prompts
    # are not dependencies of this new campaign.
    selected = read(STUDY / "final_configuration.json")
    current = read(PROTOTIPO / "config.json")
    if current.get("source_sha256") != sha(STUDY / "final_configuration.json"):
        raise ValueError('Selected configuration provenance changed.')
    for key in ("study_id", "winner", "configuration", "fixed"):
        if current[key] != selected[key]:
            raise ValueError('Configuration differs from selection: ' + key)
    for key, value in current["profile"].items():
        if selected["profile"].get(key) != value:
            raise ValueError('Profile differs from selection: ' + key)
    if current["winner"] != "qwen/p0_t0":
        raise ValueError('This campaign requires selected Qwen at temperature zero.')
    plan = read(BASE / "piano.json")
    fixed = {"metric": "expected_fidelity", "initial_examples": 396, "circuits": 50,
             "k": 5, "qiskit_seed": 0, "max_completed_llm_attempts": 3,
             "temperature": 0, "context": 60000, "order_ids": list(ORDERS)}
    if any(plan.get(key) != value for key, value in fixed.items()):
        raise ValueError('The plan declares settings unsupported by this procedure.')
    for key in ("llm_timeout_seconds", "compilation_timeout_seconds"):
        if type(plan.get(key)) is not int or plan[key] <= 0:
            raise ValueError('Invalid timeout: ' + key)
    targets = software_targets()
    rows = test_rows()
    corpus = load_corpus(verify_features=True)
    baseline = baseline_files(rows)
    check = {"ready": True, "at": now(), "checks": {
        "software_targets": {"ok": True, "details": targets},
        "selected_configuration": {"ok": True, "sha256": current["source_sha256"]},
        "train": {"ok": True, "records": len(corpus.records)},
        "test": {"ok": True, "circuits": len(rows)}}}
    # Neither this module nor the adapter opens oracle outcomes.
    return check, rows, corpus, baseline


def contract_for(experiment_id, order, rows, corpus, baseline, check):
    return {
        "revision": "qasmbench50-rag-incrementale-v1", "experiment_id": experiment_id, "order": order,
        "kind": "sequential_evaluation_on_previously_evaluated_qasmbench50",
        "rows": order_rows(rows, order), "order_seed": ORDERS[order],
        "plan": read(BASE / "piano.json"), "files": frozen_files(), "baseline_files": baseline,
        "initial_source_hashes": sorted(r["retrieval_input"]["circuit"]["source_sha256"] for r in corpus.records),
        "train_count": len(corpus.records), "transform": corpus.transform_artifact,
        "targets": check["checks"]["software_targets"]["details"]["targets"],
        "versions": check["checks"]["software_targets"]["details"]["versions"],
        "model": read(PROTOTIPO / "config.json"),
        "python": platform.python_version(),
    }


def prepare_campaign(experiment_id, order, rows, corpus, baseline, check):
    base = campaign_path(experiment_id, order)
    base.mkdir(parents=True, exist_ok=True)
    contract = contract_for(experiment_id, order, rows, corpus, baseline, check)
    if (base / "contratto.json").exists():
        check_contract(base, contract)
    else:
        save(base / "contratto.json", contract)
    (base / "memoria_incrementale/records").mkdir(parents=True, exist_ok=True)
    save(base / "verifiche" / (uuid4().hex + ".json"), check)
    return base, contract


def run_campaign(base, contract, corpus, args, *, evaluator=None):
    from adattatore import evaluate
    import app
    evaluator = evaluator or evaluate
    records, commits, previous = replay(base, contract)
    for position, row in enumerate(contract["rows"], 1):
        if position <= len(commits):
            continue
        folder = step_folder(base, position, row)
        if (folder / "esito.json").exists():
            pass  # Outcome published before interruption: complete admission only.
        elif folder.exists():
            recover_interruption(folder, row, position)
        else:
            pending = None
            try:
                evaluator(row, folder, corpus=corpus, observations=tuple(records), position=position,
                          url=args.url, transport=args.transport, plan=contract["plan"])
            except BaseException as exc:
                pending = exc
            if not (folder / "esito.json").exists():
                if pending:
                    raise pending
                raise ValueError('Evaluator ended without an outcome.')
            records, previous = finish_step(base, contract, position, row, records, previous)
            print(f"{contract['order']} {position}/{len(contract['rows'])}: {row['circuit_id']} {read(folder / 'esito.json')['status']}; memory={len(records)}", flush=True)
            if pending:
                raise pending
            continue
        records, previous = finish_step(base, contract, position, row, records, previous)
    export_memory(base, records)
    return {"completed": len(contract["rows"]), "memory_records": len(records), "memory_sha256": memory_digest(records)}


def verify_server(args):
    'Verify GGUF and context using the same transport as LLM requests.'
    import subprocess
    import urllib.request
    from pathlib import PureWindowsPath
    from app import CONFIG, PROFILES, Http
    model = args.model_path
    if model is None or not model.is_file():
        raise ValueError('--model-path must identify the GGUF served by the server.')
    artifact = CONFIG["profile"]["artifact"]
    if model.stat().st_size != artifact["size_bytes"] or sha(model) != artifact["gguf_sha256"]:
        raise ValueError('GGUF does not match the selected model.')
    http = Http(args.url, timeout=20, transport=args.transport)
    if http.transport == "windows":
        process = subprocess.run(
            ["curl.exe", "--silent", "--show-error", "--fail", "--max-time", "20", http.url + "/props"],
            capture_output=True, check=True, timeout=30)
        props = json.loads(process.stdout)
    else:
        with urllib.request.urlopen(http.url + "/props", timeout=20) as response:
            props = json.load(response)
    context = props.get("default_generation_settings", {}).get("n_ctx", props.get("n_ctx"))
    requested = PROFILES["desktop"]
    allocated = ((requested + 255) // 256) * 256
    if type(context) is not int or context not in (requested, allocated):
        raise ValueError(f'Server context differs from {requested} ({allocated} after alignment): {context}')
    served = props.get("model_path", "")
    if PureWindowsPath(served).name != model.name and Path(served).name != model.name:
        raise ValueError('Served model name differs from the supplied GGUF.')
    served_path = Path(served)
    if os.name == "posix" and PureWindowsPath(served).drive:
        win = PureWindowsPath(served)
        served_path = Path("/mnt") / win.drive[0].lower() / Path(*win.parts[1:])
    if not served_path.is_file() or sha(served_path) != artifact["gguf_sha256"]:
        raise ValueError("Cannot verify the server's declared GGUF: " + served)
    return {"model_sha256": artifact["gguf_sha256"], "props": props, "url": http.url,
            "context_requested": requested, "context_reported": context, "transport": http.transport}


def cli(argv=None, default_order=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verifica", action="store_true", help='Offline checks without inference')
    mode.add_argument("--prepara", action="store_true", help='Freeze four orderings and empty memories')
    mode.add_argument("--esegui", action="store_true", help='Start or resume new decisions')
    parser.add_argument("--ordine", choices=ORDERS, default=default_order)
    parser.add_argument("--tutti", action="store_true", help='Run the four orderings sequentially')
    parser.add_argument("--experiment-id", default=DEFAULT_ID)
    parser.add_argument("--url", default="http://127.0.0.1:8089")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--transport", choices=("auto", "native", "windows"), default="auto")
    args = parser.parse_args(argv)
    import signal
    def stop(signum, frame):
        raise KeyboardInterrupt('SIGTERM stop requested; outcomes preserved.')
    signal.signal(signal.SIGTERM, stop)
    if args.ordine and args.tutti:
        parser.error('Choose --ordine or --tutti.')
    if args.esegui and not (args.ordine or args.tutti):
        parser.error('--esegui requires --ordine or --tutti.')
    if not args.url.startswith(("http://127.0.0.1:", "http://localhost:")):
        parser.error('A local server is required.')
    selected = [args.ordine] if args.ordine else list(ORDERS)
    for order in selected:
        campaign_path(args.experiment_id, order)
    import portalocker
    # Concurrent launches must not share the server or timing measurements.
    with portalocker.Lock(str(BASE / ".campaign.lock"), timeout=0):
        check, rows, corpus, baseline = preflight()
        if args.verifica:
            print(json.dumps({"ready": True, "circuits": len(rows), "train": len(corpus.records),
                              "orders": selected, "baseline_results": len(baseline)-1,
                              "llm_called": False}, ensure_ascii=False, indent=2))
            return 0
        prepared = [prepare_campaign(args.experiment_id, order, rows, corpus, baseline, check) for order in selected]
        if args.prepara:
            print("\n".join(str(base) for base, _ in prepared))
            return 0
        server_id = uuid4().hex
        try:
            server = verify_server(args)
        except BaseException as exc:
            for base, _ in prepared:
                save(base / "verifiche" / (server_id + "_server.json"), {
                    "at": now(), "ok": False, "error": type(exc).__name__, "message": str(exc)})
            raise
        for base, _ in prepared:
            save(base / "verifiche" / (server_id + "_server.json"), {"at": now(), "ok": True, "server": server})
        for base, contract in prepared:
            session = uuid4().hex
            save(base / "sessioni" / (session + "_inizio.json"), {
                "at": now(), "server": server, "transport": args.transport,
                "platform": platform.platform(), "cpu_count": os.cpu_count(),
                "memory_energy_measurements": "not_collected"})
            try:
                result = run_campaign(base, contract, corpus, args)
            except BaseException as exc:
                save(base / "sessioni" / (session + "_fine.json"), {
                    "at": now(), "status": "stopped", "error": type(exc).__name__, "message": str(exc)})
                raise
            save(base / "sessioni" / (session + "_fine.json"), {"at": now(), "status": "completed", **result})
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

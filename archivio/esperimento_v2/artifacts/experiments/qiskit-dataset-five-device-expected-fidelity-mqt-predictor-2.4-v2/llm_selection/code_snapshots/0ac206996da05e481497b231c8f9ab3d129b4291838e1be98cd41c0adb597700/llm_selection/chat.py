"""Avvia la chat locale senza avviare episodi di validation o richieste LLM."""
from __future__ import annotations
import argparse
import fcntl
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from .common import OUTPUT, ROOT, append_jsonl, now, read_json, write_json
from .hardware import server_arguments
from .controller import launch, stop, health, failure_message
from .provenance import capture

REFERENCE = OUTPUT / "servers/qwen-prova-07-qwen/launch.json"

def profile_from_reference():
    reference = read_json(REFERENCE)
    return {
        "weight_precision": "Q8_0",
        **{key: reference[key] for key in
           ("context", "cache_type", "gpu_layers", "batch", "micro_batch", "guards")},
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default=None, help="Nome nuovo; predefinito con data e ora UTC.")
    parser.add_argument("--check", action="store_true", help="Controlla file e profilo senza caricare il modello.")
    args = parser.parse_args()
    label = args.label or datetime.now(timezone.utc).strftime("qwen-chat-%Y%m%d-%H%M%S")
    if not re.fullmatch(r"[a-z0-9_-]+", label):
        parser.error("Il nome deve contenere solo lettere minuscole, cifre, - e _.")
    profile = profile_from_reference()
    server_arguments(profile)
    required = [
        OUTPUT / "models/qwen/Q8_0_manifest.json",
        OUTPUT / "runtime/b10930/llama-server.exe",
        ROOT / "llm_selection/serve.ps1",
        ROOT / "llm_selection/stop.ps1",
    ]
    manifest = read_json(required[0])
    required.append(Path(manifest["local_path"]))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("\n".join(missing))
    if args.check:
        print("File e profilo presenti. Qwen Q8_0; contesto", profile["context"])
        print("Nessun server avviato, nessuna inferenza. SHA-256 verificato al vero avvio.")
        return
    session = OUTPUT / "manual_chats" / label
    server_dir = OUTPUT / "servers" / label
    if session.exists() or server_dir.exists() or server_dir.is_symlink():
        raise FileExistsError("Nome già usato: scegliere un nuovo --label.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if health() is not None:
            raise RuntimeError("Un server risponde già sulla porta 8089; chiuderlo prima.")
        session.mkdir(parents=True, exist_ok=False)
        write_json(session / "request.json", {
            "at": now(), "phase": "train_manual_chat", "model": "qwen",
            "profile": profile, "reference_launch": str(REFERENCE),
            "note": "Server e risorse registrati. Esportare dalla chat messaggi e impostazioni: non sono catturati automaticamente da questo avvio.",
        })
        capture(session)
        events = session / "events.jsonl"
        with (session / "server.log").open("x") as log:
            process = None
            try:
                process = launch("qwen", profile, server_dir, log, events)
                print("\nApri nel browser Windows: http://127.0.0.1:8089", flush=True)
                print("Per spegnere il server: Ctrl+C in questo terminale.", flush=True)
                print("Registri della sessione:", session, flush=True)
                print("Esporta messaggi e impostazioni della chat prima di chiuderla.", flush=True)
                while process.poll() is None:
                    time.sleep(1)
                if (server_dir / "resource_abort.json").exists() or (server_dir / "monitor_error.json").exists():
                    raise RuntimeError(failure_message(server_dir, Path(log.name)))
                if process.returncode:
                    raise RuntimeError("Il server si è fermato: consultare " + str(log.name))
            except KeyboardInterrupt:
                print("\nChiusura della chat locale...", flush=True)
            finally:
                if process is not None:
                    stop(server_dir, "manual_chat_closed", log)
                    process.wait(timeout=30)
                append_jsonl(events, {"at": now(), "event": "manual_chat_session_ended"})
        fcntl.flock(lock, fcntl.LOCK_UN)

if __name__ == "__main__":
    main()

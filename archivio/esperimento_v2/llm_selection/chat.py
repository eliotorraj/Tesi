'Start a local Qwen, Phi or Gemma chat, separate from experimental runs.'
from __future__ import annotations

import argparse
import fcntl
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .common import OUTPUT, ROOT, append_jsonl, now, read_json, write_json
from .controller import failure_message, health, launch, stop
from .hardware import DEFAULT_BATCH, DEFAULT_GUARDS, DEFAULT_MICRO_BATCH, server_arguments
from .provenance import capture
from .study import MODEL_KEYS, NATIVE_CONTEXT

# Initial chat profiles do not establish model quality or resource feasibility.
# Qwen retains the settings from the earlier qwen-prova-07 launch.
CHAT_DEFAULTS = {
    "qwen": {"context": 147456, "cache_type": "q8_0"},
    "phi": {"context": 114688, "cache_type": "q4_0"},
    "gemma": {"context": 131072, "cache_type": "q4_0"},
}
PROFILE_REVISION = "manual-chat-defaults-v1"


def profile_for_model(model, *, precision="Q8_0", context=None, cache_type=None):
    'Build an explicit profile without relying on old records.'
    if model not in MODEL_KEYS:
        raise ValueError("Unknown chat model")
    if precision not in ("BF16", "Q8_0"):
        raise ValueError("Unsupported weight precision")
    defaults = CHAT_DEFAULTS[model]
    profile = {
        "weight_precision": precision,
        "context": defaults["context"] if context is None else context,
        "cache_type": defaults["cache_type"] if cache_type is None else cache_type,
        "gpu_layers": "all",
        "batch": DEFAULT_BATCH,
        "micro_batch": DEFAULT_MICRO_BATCH,
        "guards": dict(DEFAULT_GUARDS),
    }
    if not 0 < profile["context"] <= NATIVE_CONTEXT[model]:
        raise ValueError("Context exceeds native limit or is not positive")
    if profile["cache_type"] not in ("f16", "q8_0", "q4_0"):
        raise ValueError("Unsupported cache type")
    server_arguments(profile)
    return profile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_KEYS, default="qwen",
                        help='Chat model; default: qwen.')
    parser.add_argument("--label", default=None, help='New name; defaults to model and UTC timestamp.')
    parser.add_argument("--precision", choices=("BF16", "Q8_0"), default="Q8_0")
    parser.add_argument("--context", type=int, help='Context; model-specific default.')
    parser.add_argument("--cache-type", choices=("f16", "q8_0", "q4_0"),
                        help='Cache precision; model-specific default.')
    parser.add_argument("--check", action="store_true", help='Check files and profile without loading the model.')
    args = parser.parse_args(argv)
    label = args.label or args.model + "-chat-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if not re.fullmatch(r"[a-z0-9_-]+", label):
        parser.error('The name may contain only lowercase letters, digits, - and _.')
    try:
        profile = profile_for_model(args.model, precision=args.precision,
                                    context=args.context, cache_type=args.cache_type)
    except ValueError as error:
        parser.error(str(error))
    required = [
        OUTPUT / "models" / args.model / (profile["weight_precision"] + "_manifest.json"),
        OUTPUT / "runtime/b10930/llama-server.exe",
        ROOT / "llm_selection/serve.ps1",
        ROOT / "llm_selection/stop.ps1",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("\n".join(missing))
    manifest = read_json(required[0])
    model_path = Path(manifest["local_path"])
    if not model_path.is_file():
        raise FileNotFoundError(str(model_path))
    if args.check:
        print(f"File and profile found. {args.model}: weights {profile['weight_precision']}; context {profile['context']}; cache {profile['cache_type']}.")
        print('No server started or inference performed. SHA-256 is checked at actual startup.')
        return
    session = OUTPUT / "manual_chats" / label
    server_dir = OUTPUT / "servers" / label
    if session.exists() or server_dir.exists() or server_dir.is_symlink():
        raise FileExistsError('Name already used: choose a new --label.')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if health() is not None:
            raise RuntimeError('A server already responds on port 8089; stop it first.')
        session.mkdir(parents=True, exist_ok=False)
        write_json(session / "request.json", {
            "at": now(), "phase": "train_manual_chat", "model": args.model,
            "profile": profile, "profile_revision": PROFILE_REVISION,
            "note": 'Server and resources recorded. Export chat messages and settings: this launcher does not capture them automatically.',
        })
        capture(session)
        events = session / "events.jsonl"
        with (session / "server.log").open("x") as log:
            process = None
            try:
                process = launch(args.model, profile, server_dir, log, events)
                print(f'\nChat {args.model}. Open in the Windows browser: http://127.0.0.1:8089', flush=True)
                print('To stop the server: Ctrl+C in this terminal.', flush=True)
                print('Session records:', session, flush=True)
                print('Export chat messages and settings before closing it.', flush=True)
                while process.poll() is None:
                    time.sleep(1)
                if (server_dir / "resource_abort.json").exists() or (server_dir / "monitor_error.json").exists():
                    raise RuntimeError(failure_message(server_dir, Path(log.name)))
                if process.returncode:
                    raise RuntimeError('The server stopped: consult ' + str(log.name))
            except KeyboardInterrupt:
                print("""
Closing local chat...""", flush=True)
            finally:
                if process is not None:
                    stop(server_dir, "manual_chat_closed", log)
                    process.wait(timeout=30)
                append_jsonl(events, {"at": now(), "event": "manual_chat_session_ended"})
        fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    main()

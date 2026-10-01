"""Avvio Linux di Qwen: CPU o GPU riconosciute da llama.cpp, senza dipendenze Windows."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import socket
import subprocess
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
PROFILES = {"cpu": (16384, 128, 64), "gpu": (16384, 128, 64), "desktop": (60000, 512, 128)}
GIB = 1024 ** 3


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def available_memory():
    """RAM disponibile vista dal kernel Linux, senza contare lo swap."""
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MemAvailable non disponibile: impossibile verificare il margine RAM")


def check_model(path):
    artifact = json.loads((ROOT / "config.json").read_text())["profile"]["artifact"]
    if not path.is_file():
        raise ValueError("GGUF assente: seguire docs/guida_passo_passo.md")
    if path.stat().st_size != artifact["size_bytes"] or sha256(path) != artifact["gguf_sha256"]:
        raise ValueError("Dimensione o SHA-256 del GGUF diversi da config.json")
    return artifact["gguf_sha256"]


def command_for(args, executable, model):
    context, batch, micro_batch = PROFILES[args.profile]
    layers = "0" if args.profile == "cpu" else args.gpu_layers
    command = [executable, "--model", str(model), "--host", "127.0.0.1", "--port", str(args.port),
               "--ctx-size", str(context), "--parallel", "1", "--n-gpu-layers", layers,
               "--flash-attn", "on", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
               "--threads", str(args.threads), "--threads-batch", str(args.threads),
               "--batch-size", str(batch), "--ubatch-size", str(micro_batch), "--jinja",
               "--no-context-shift", "--cache-ram", "0", "--metrics", "--fit", "off", "--load-mode", "none"]
    if args.profile == "cpu":
        command += ["--device", "none"]
    elif args.device:
        command += ["--device", args.device]
    return command


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--bin", default="llama-server", help="Eseguibile compilato per Linux")
    parser.add_argument("--profile", choices=PROFILES, default="cpu")
    parser.add_argument("--device", help="Identificativo restituito da --list-devices; non il nome di un Target quantistico")
    parser.add_argument("--gpu-layers", default="all", help="all oppure numero di strati, per gpu/desktop")
    parser.add_argument("--threads", type=int, default=min(6, os.cpu_count() or 1))
    parser.add_argument("--port", type=int, default=8089)
    parser.add_argument("--list-devices", action="store_true", help="Mostra i dispositivi di questo eseguibile senza caricare pesi")
    parser.add_argument("--dry-run", action="store_true", help="Verifica pesi e RAM, stampa il comando senza avviare il modello")
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("Usare Linux/WSL; sul fisso Windows restano disponibili gli avviatori .ps1")
    executable = shutil.which(args.bin)
    if not executable:
        parser.error("llama-server non trovato: passare --bin /percorso/llama-server")
    executable = str(Path(executable).resolve())
    if args.list_devices:
        return subprocess.run([executable, "--list-devices"]).returncode
    if args.model is None:
        parser.error("Specificare --model /percorso/Qwen3.5-4B-Q8_0.gguf")
    if args.threads < 1 or not 1 <= args.port <= 65535:
        parser.error("Thread positivi e porta fra 1 e 65535 richiesti")
    if args.profile == "cpu" and (args.device or args.gpu_layers != "all"):
        parser.error("Il profilo cpu impone device=none e zero strati GPU; usare gpu o desktop per accelerare")
    if args.gpu_layers != "all" and (not args.gpu_layers.isdigit() or int(args.gpu_layers) < 1):
        parser.error("Per GPU usare all oppure un numero positivo di strati")
    model = args.model.expanduser().resolve()
    print("Verifica completa del GGUF; può richiedere tempo...", flush=True)
    model_hash = check_model(model)
    free = available_memory()
    minimum = (9 if args.profile == "cpu" else 2) * GIB
    if free < minimum:
        raise RuntimeError(f"RAM disponibile {free/GIB:.1f} GiB; richiesti {minimum/GIB:.0f} GiB liberi prima dell'avvio")
    revision = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True, timeout=30)
    devices = subprocess.run([executable, "--list-devices"], capture_output=True, text=True, check=True, timeout=30)
    command = command_for(args, executable, model)
    print(shlex.join(command), flush=True)
    if args.dry_run:
        return 0
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError as error:
            raise RuntimeError("Porta occupata: verificare il server già presente oppure cambiare --port") from error
    folder = ROOT / "runtime" / "server-runs" / (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8])
    folder.mkdir(parents=True)
    write_json(folder / "launch.json", {"command": command, "profile": args.profile,
               "context": PROFILES[args.profile][0], "model_sha256": model_hash,
               "binary_sha256": sha256(executable), "version": revision.stdout + revision.stderr,
               "available_devices": devices.stdout + devices.stderr, "platform": platform.platform(),
               "available_before_bytes": free, "gpu_temperature_monitor": False,
               "note": "Rilevamento del backend; temperatura GPU, memoria GPU ed energia non misurate"})
    print(f"Registri server: {folder}\nAttendere /health con status=ok. Ctrl+C arresta questo server.", flush=True)
    proc = None
    reason = "launch_failure"
    try:
        with (folder / "stdout.log").open("w") as out, (folder / "stderr.log").open("w") as err, (folder / "resources.jsonl").open("w") as log:
            proc = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
            low = 0
            reason = "process_exit"
            while proc.poll() is None:
                free = available_memory()
                log.write(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "available_bytes": free}) + "\n")
                log.flush()
                low = low + 1 if free < (2 if args.profile == "cpu" else 1) * GIB else 0
                if low >= 3:
                    reason = "low_available_ram"
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        reason = "user_interrupt"
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        write_json(folder / "exit.json", {"reason": reason, "returncode": proc.returncode if proc else None})
    return 130 if reason == "user_interrupt" else (proc.returncode or (1 if reason != "process_exit" else 0))


if __name__ == "__main__":
    raise SystemExit(main())

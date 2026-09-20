"""Installa Node e TOON nelle cartelle del progetto, senza cambiare l'ambiente MQT."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tarfile
import urllib.request
from .common import OUTPUT, ROOT

def install():
    package = ROOT / "prototype/prompting/toon_runtime"
    lock = json.loads((package / "node-lock.json").read_text())
    runtime = OUTPUT / "runtime/toon"
    runtime.mkdir(parents=True, exist_ok=True)
    name = "node-" + lock["version"] + "-linux-x64"
    node = runtime / name / "bin/node"
    if not node.exists():
        archive = runtime / (name + ".tar.xz")
        data = archive.read_bytes() if archive.exists() else urllib.request.urlopen(lock["url"], timeout=60).read()
        if hashlib.sha256(data).hexdigest() != lock["archive_sha256"]:
            raise ValueError("Node archive checksum mismatch")
        archive.write_bytes(data)
        with tarfile.open(archive) as bundle:
            bundle.extractall(runtime, filter="data")
    if hashlib.sha256(node.read_bytes()).hexdigest() != lock["node_sha256"]:
        raise ValueError("Node executable checksum mismatch")
    npm = runtime / name / "lib/node_modules/npm/bin/npm-cli.js"
    env = dict(os.environ, PATH=str(node.parent) + os.pathsep + os.environ.get("PATH", ""))
    subprocess.run([str(node), str(npm), "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                   cwd=package, env=env, check=True)
    print("TOON 4.1.1 installed; MQT environment unchanged.")

if __name__ == "__main__":
    install()

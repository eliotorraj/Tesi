"""Verifica i pesi sul percorso Windows senza leggerli nella cache WSL."""
import json
import subprocess
from pathlib import Path
from .common import windows_path, write_json

def verify_weights(artifact, record_path=None):
    from .controller import ps_command
    command=ps_command("verify_weights.ps1","-ModelPath",windows_path(Path(artifact["local_path"])),
                       "-ExpectedSha256",artifact["gguf_sha256"],"-ExpectedSize",artifact["size_bytes"])
    result=subprocess.run(command,capture_output=True,text=True)
    if result.returncode:
        raise ValueError("Model weight verification failed: "+(result.stderr or result.stdout)[-2000:])
    record=json.loads(result.stdout.lstrip("\ufeff"))
    if (record.get("valid") is not True or record.get("sha256")!=artifact["gguf_sha256"]
            or record.get("size_bytes")!=artifact["size_bytes"]):
        raise ValueError("Model weight verification returned inconsistent metadata")
    if record_path is not None: write_json(record_path,record)
    return record

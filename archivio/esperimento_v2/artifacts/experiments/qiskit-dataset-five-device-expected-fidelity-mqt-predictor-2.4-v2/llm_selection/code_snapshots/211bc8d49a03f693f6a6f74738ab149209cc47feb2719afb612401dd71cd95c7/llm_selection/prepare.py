"""Inventario e prompt train/validation; non legge punteggi di validation."""
from __future__ import annotations
import json
import platform
import subprocess
from pathlib import Path
from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
from prototype.quantum_assistant.adapters.rag_checks import prepare_prompt
from prototype.quantum_assistant.factory import build_default_service
from qiskit_dataset.experiment_v2 import source_manifest
from scripts.mqt_predictor_protocol import (
    FROZEN_DEVICES, TRAINING_CIRCUITS_V2, VALIDATION_CIRCUITS_V2,
    TEST_RELEASE_RECORD, file_sha256, verify_circuit_directory,
)
from .common import OUTPUT, ROOT, now, write_json, read_json

def inventory():
    manifest = source_manifest()
    info = {"created_at": now(), "test_release_present": TEST_RELEASE_RECORD.exists(),
            "platform": platform.platform(), "python": platform.python_version(),
            "uv_lock_sha256": file_sha256(ROOT / "uv.lock"),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "meminfo": Path("/proc/meminfo").read_text(), "splits": {}}
    for split, directory in (("train", TRAINING_CIRCUITS_V2), ("validation", VALIDATION_CIRCUITS_V2)):
        rows = []
        for record in manifest["circuits"]:
            if record["split"] != split:
                continue
            path = directory / record["file_name"]
            rows.append({**record, "bytes": path.stat().st_size})
        info["splits"][split] = rows
    path = OUTPUT / "preparation" / "initial_inventory.json"
    if not path.exists():
        write_json(path, info)
    print(json.dumps({s: {"count": len(rs), "largest": sorted([(r["bytes"], r["circuit_id"]) for r in rs], reverse=True)[:5]} for s, rs in info["splits"].items()}, indent=2))
    return info

def prepare():
    info = inventory()
    service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway())
    train = sorted(info["splits"]["train"], key=lambda r: (r["bytes"], r["circuit_id"]))
    probes = {r["circuit_id"]: r for r in [train[0], train[len(train)//2], *train[-3:]]}
    for split, records, directory in (("train", list(probes.values()), TRAINING_CIRCUITS_V2),
                                      ("validation", info["splits"]["validation"], VALIDATION_CIRCUITS_V2)):
        verify_circuit_directory(directory, allowed_splits=(split,))
        for index, row in enumerate(sorted(records, key=lambda r: r["circuit_id"]), 1):
            destination = OUTPUT / "prompts" / split / (row["circuit_id"] + ".json")
            if destination.exists():
                saved = read_json(destination)
                if saved["source_sha256"] != row["source_sha256"]:
                    raise ValueError("Prompt esistente di un altro circuito.")
                continue
            prepared = prepare_prompt(service, directory / row["file_name"])
            prepared["circuit_metadata"] = row
            prepared["created_at"] = now()
            prepared["prompt_characters"] = len(json.dumps(prepared["prompt"], ensure_ascii=False, separators=(",", ":")))
            write_json(destination, prepared)
            print(f"prompt {split} {index}/{len(records)} {row['circuit_id']} chars={prepared['prompt_characters']}", flush=True)

if __name__ == "__main__":
    import sys
    prepare() if "--prompts" in sys.argv else inventory()

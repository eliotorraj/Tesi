"""TOON ufficiale: vista reversibile, valori controllati dopo la decodifica."""
from __future__ import annotations
import copy
from functools import lru_cache
import hashlib
import json
import subprocess
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).with_name("toon_runtime")
NOTE = (
    "Input uses TOON: [N] is row count and {fields} names columns. "
    "circuit_features columns current and E1-E5 describe the current circuit and supplied examples. "
    "coupling_adjacency maps each source qubit to its ordered target qubits. Return JSON, not TOON."
)
OPTIONS = {"indentSize": 2, "delimiter": ","}


@lru_cache(maxsize=1)
def node_path():
    candidate=os.environ.get("PROTOTIPO_NODE") or str(ROOT/("runtime/node/node.exe" if os.name == "nt" else "runtime/node/bin/node"))
    if not Path(candidate).is_file():
        candidate=shutil.which("node")
    if not candidate:
        raise RuntimeError("Installare Node.js 22 o indicare PROTOTIPO_NODE.")
    result=subprocess.run([str(candidate),"--version"],capture_output=True,text=True,check=True)
    if not result.stdout.strip().startswith("v22."):
        raise RuntimeError("Richiesto Node.js 22 per TOON; versione osservata "+result.stdout.strip())
    return Path(candidate)


def _codec(job):
    result = subprocess.run([str(node_path()), str(PACKAGE / "codec.mjs")],
                            input=json.dumps(job, ensure_ascii=False, allow_nan=False),
                            text=True, encoding="utf-8", capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError("TOON codec failed: " + result.stderr[-1500:])
    return json.loads(result.stdout)


def project(view):
    """Raggruppa solo forme ricostruibili esattamente; nessuna feature è scartata."""
    value = copy.deepcopy(view)
    for device in value.get("compatible_hardware", []):
        edges = device.get("coupling_edges")
        if isinstance(edges, list):
            adjacent = {}
            for source, target in edges:
                adjacent.setdefault(str(source), []).append(target)
            # Grouping is used only when it preserves the original edge order.
            restored = [[int(source), target] for source, targets in adjacent.items() for target in targets]
            if restored == edges and list(adjacent) == sorted(adjacent, key=int):
                device["coupling_adjacency"] = adjacent
                del device["coupling_edges"]
    current = value.get("circuit", {}).get("features")
    examples = value.get("retrieved_labeled_examples", [])
    uniform = isinstance(current, dict) and bool(current) and all(
        isinstance(n, (int, float)) and not isinstance(n, bool) for n in current.values())
    for example in examples:
        features = example.get("circuit", {}).get("features", {})
        uniform = uniform and set(features) == {"values"} and isinstance(features.get("values"), dict)
        if not uniform or set(features["values"]) != set(current):
            uniform = False
            break
    if uniform:
        value["circuit_features"] = {
            key: {"current": number, **{e["id"]: e["circuit"]["features"]["values"][key] for e in examples}}
            for key, number in current.items()}
        del value["circuit"]["features"]
        for example in examples:
            del example["circuit"]["features"]
    return value


def restore(value):
    """Ricostruisce la vista JSON minima, compreso l'ordine degli archi."""
    value = copy.deepcopy(value)
    for device in value.get("compatible_hardware", []):
        if "coupling_adjacency" in device:
            device["coupling_edges"] = [
                [int(source), target] for source, targets in device.pop("coupling_adjacency").items()
                for target in targets]
    if "circuit_features" in value:
        features = value.pop("circuit_features")
        value["circuit"]["features"] = {key: row["current"] for key, row in features.items()}
        for example in value.get("retrieved_labeled_examples", []):
            example["circuit"]["features"] = {"values": {key: row[example["id"]] for key, row in features.items()}}
    return value


@lru_cache(maxsize=16)
def _encode(document):
    view = json.loads(document)
    projected = project(view)
    encoded = _codec({"operation": "encode", "value": projected, "delimiter": OPTIONS["delimiter"]})
    if encoded["decoded"] != projected or restore(encoded["decoded"]) != view:
        raise ValueError("TOON would change input values; request not sent")
    return encoded["text"]


def encode_view(view):
    return _encode(json.dumps(view, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


def decode_view(text):
    return restore(_codec({"operation": "decode", "text": text}))


def metadata():
    lock = json.loads((PACKAGE / "node-lock.json").read_text())
    return {"format": "TOON", "package": "@toon-format/toon", "version": "4.1.1",
            "options": OPTIONS, "node_version": subprocess.check_output([str(node_path()), "--version"], text=True).strip(),
            "original_node_version": lock["version"],
            "projection": "feature_rows_and_ordered_adjacency_v1"}

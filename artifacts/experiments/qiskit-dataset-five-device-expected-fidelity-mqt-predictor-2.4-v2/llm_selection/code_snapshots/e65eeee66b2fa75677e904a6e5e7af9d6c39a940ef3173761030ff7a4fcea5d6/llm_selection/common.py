"""Percorsi e scritture durevoli, separati dagli artefatti MQT."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from scripts.mqt_predictor_protocol import EXPERIMENT_ROOT
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = EXPERIMENT_ROOT / "llm_selection"

def json_ready(value):
    """Serializza dataclass e MappingProxyType senza deepcopy/pickle."""
    from collections.abc import Mapping
    from dataclasses import fields, is_dataclass
    from enum import Enum
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value

def now():
    return datetime.now(UTC).isoformat()

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)

def append_jsonl(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())

def windows_path(path):
    """Percorso del medesimo file WSL per gli eseguibili Windows."""
    path = Path(path).resolve()
    parts = path.parts
    if len(parts) >= 3 and parts[1] == "mnt" and len(parts[2]) == 1:
        return parts[2].upper() + ":\\" + "\\".join(parts[3:])
    return "\\\\wsl.localhost\\Ubuntu" + str(path).replace("/", "\\")

"""Percorsi, scritture atomiche e identita del Test indipendente."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
ARCHIVE = REPO / "archivio/esperimento_v2"
AREA = ROOT / "test"
EXPERIMENT = ARCHIVE / "artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2"
STUDY = EXPERIMENT / "llm_selection/studies/local-llm-v2"
SOURCE = EXPERIMENT / "manifests/source_circuits_v2.json"
METHODS = ("llm_rag", "llm_senza_rag", "mqt_predictor", "random")
PLAN = AREA / "piano.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def save(path, value):
    """Un record pubblicato non viene mai sovrascritto."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + "." + uuid4().hex + ".tmp")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(tmp, path)
    finally:
        tmp.unlink()

def contained(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError("Percorso esterno alla fonte: " + str(name))
    return p

def source_path(record):
    # I riferimenti logici originali rimangono immutati.
    return contained(ARCHIVE / "archivio/protocollo_v1", record["source_ref"])

def code_files():
    paths = [ROOT / "config.json", PLAN, ROOT / "requirements.txt", ROOT / "docs/protocollo_sperimentale.md"]
    for folder in ("prototype", "qiskit_dataset", "scripts", "schemas", "test/strumenti", "test/verifiche", "addestramento/mqt"):
        paths.extend((ROOT / folder).rglob("*.py"))
        paths.extend((ROOT / folder).rglob("*.json"))
    paths += list(AREA.glob("*.py"))
    paths += [ROOT / "app.py", ROOT / "portable_features.py"]
    paths += list((ROOT / "runtime/toon").rglob("*.js"))
    paths += list((ROOT / "runtime/toon").rglob("*.mjs"))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths)) if p.is_file()}

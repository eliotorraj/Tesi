'Paths, atomic writes and identity of the independent Test.'
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

AREA = Path(__file__).resolve().parents[1]
EVALUATION = AREA.parent
REPO = EVALUATION.parents[1]
ROOT = REPO / "prototipo"
ARCHIVE = REPO / "archivio/esperimento_v2"
EXPERIMENT = ARCHIVE / "artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2"
STUDY = EXPERIMENT / "llm_selection/studies/local-llm-v2"
SOURCE = AREA / "manifest.json"
METHODS = ("llm_rag", "mqt_predictor")
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
    'Never overwrite a published record.'
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
        raise ValueError('Path outside the source: ' + str(name))
    return p

def source_path(record):
    # QASMBench references are relative to the external collection only.
    return contained(AREA / "circuiti", record["source_ref"])

def code_files():
    paths=[ROOT/"config.json",ROOT/"requirements.txt",ROOT/"app.py",ROOT/"portable_features.py",
           ROOT/"docs/protocollo_sperimentale.md",PLAN,SOURCE,ARCHIVE/"uv.lock"]
    for folder in ("prototype","qiskit_dataset","scripts","schemas","runtime/toon"):
        paths += [p for p in (ROOT/folder).rglob("*") if p.suffix in (".py",".json",".js",".mjs")]
    paths += list(AREA.glob("*.py"))+list((AREA/"strumenti").glob("*.py"))
    for folder in (ARCHIVE/"scripts",EVALUATION/"addestramento/mqt"):
        paths += list(folder.glob("*.py"))
    return {p.relative_to(REPO).as_posix():sha(p) for p in sorted(set(paths)) if p.is_file()}

'Paths and records for the incremental campaign only.'
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from uuid import uuid4

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
REPO = BASE.parents[4]
K1_ROOT = BASE.parent
sys.path.insert(0, str(K1_ROOT))
PROTOTIPO = REPO / "prototipo"
STRUMENTI = REPO / "archivio/valutazione/test/strumenti"
for path in (STRUMENTI, PROTOTIPO):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from common import SOURCE, source_path, sha, digest, save, read, now

ORDERS = {
    "01_manifest": None,
    "02_inverso": None,
    "03_casuale_20261002": 20261002,
    "04_casuale_20261003": 20261003,
}
FIXED = "00_rag_fisso"
SYSTEMS = {FIXED: None, **ORDERS}
BENCHMARK = "mqtbench90"
DEFAULT_ID = "mqtbench90_rag_k1_v1"
HISTORICAL_BASELINE = REPO / "archivio/valutazione/test/risultati/llm_rag"
ORACLE = REPO / "archivio/valutazione/oracle_test/confronto_llm_rag_k5/risultati/dati.json"


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_score(row):
    value = row.get("score")
    return row.get("status") == "success" and finite(value) and 0 <= value <= 1


def campaign_path(experiment_id, order):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", experiment_id):
        raise ValueError('Invalid experiment ID.')
    if order not in SYSTEMS:
        raise ValueError('Unknown ordering.')
    path = ((BASE / "rag_fisso") if order == FIXED else (BASE / "ordinamenti" / order)) / "campagne" / experiment_id
    if not path.resolve().is_relative_to(BASE.resolve()):
        raise ValueError('The campaign must remain in the new archive area.')
    return path


def order_rows(rows, order):
    import random
    result = [dict(row) for row in rows]
    if order == "02_inverso":
        result.reverse()
    elif order in ORDERS and ORDERS[order] is not None:
        random.Random(ORDERS[order]).shuffle(result)
    elif order not in ("01_manifest", FIXED):
        raise ValueError('Unknown ordering.')
    return result


def test_rows():
    if sha(SOURCE) != "c599eab17b6f64528067016e3d175cbfed597334f779ef8e515cf8787a788f53":
        raise ValueError('Original corpus manifest was modified.')
    rows = [r for r in read(SOURCE)["circuits"] if r["split"] == "test"]
    if len(rows) != 90 or len({r["circuit_id"] for r in rows}) != 90:
        raise ValueError("Expected the manifest's 90 Test IDs.")
    for row in rows:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", row["circuit_id"]):
            raise ValueError('Unsafe circuit ID.')
        if sha(source_path(row)) != row["source_sha256"]:
            raise ValueError('Original circuit was modified: ' + row["circuit_id"])
    return rows


def memory_digest(records):
    return digest(records)


def step_folder(base, position, row):
    return base / "circuiti" / f"{position:03d}_{row['circuit_id']}"


def frozen_files():
    'Hashes of sources actually reused; no future results.'
    paths = [SOURCE, PROTOTIPO / "config.json", PROTOTIPO / "requirements.txt",
             PROTOTIPO / "app.py", PROTOTIPO / "portable_features.py",
             REPO / "archivio/valutazione/test/piano.json", BASE / "piano.json"]
    paths += [BASE / name for name in ("comune.py", "memoria.py", "adattatore.py", "registro.py", "esperimento.py")]
    paths += list(STRUMENTI.glob("*.py"))
    paths += list((K1_ROOT / "prompt_k1").glob("*.py"))
    paths += [K1_ROOT / ("avvia_" + BENCHMARK + ".py")]
    for folder in ("prototype", "qiskit_dataset", "scripts", "schemas", "configs"):
        for pattern in ("*.py", "*.json", "*.mjs", "*.js"):
            paths += list((PROTOTIPO / folder).rglob(pattern))
    paths += list((PROTOTIPO / "runtime/toon").glob("*.mjs"))
    seal = PROTOTIPO / "data/seal.json"
    paths += [seal] + [PROTOTIPO / p for p in read(seal)["files"]]
    return {str(p.relative_to(REPO)): sha(p) for p in sorted(set(paths))}


def verify_hashes(files):
    for relative, expected in files.items():
        path = (REPO / relative).resolve()
        if not path.is_relative_to(REPO.resolve()) or sha(path) != expected:
            raise ValueError('Source changed: ' + relative)


def check_contract(base, expected=None, *, verify_runtime=True):
    path = base / "contratto.json"
    contract = read(path)
    if expected is not None and contract != expected:
        raise ValueError('Incompatible contract. Use a new --experiment-id.')
    if contract.get("revision") != "mqtbench90-rag-k1-v1":
        raise ValueError('Unsupported campaign revision.')
    if verify_runtime:
        verify_hashes(contract["files"])
    if contract.get("benchmark") != BENCHMARK or contract.get("plan", {}).get("k") != 1:
        raise ValueError('Contract does not belong to this k=1 experiment.')
    order = contract.get("order")
    if order not in SYSTEMS or contract.get("strategy") != strategy_for(order):
        raise ValueError('Invalid contract strategy.')
    return contract


def path_hashes(base, folder):
    return {str(p.relative_to(base)): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name != "commit.json" and not p.name.startswith(".")}


def validate_relative_file(base, relative, expected):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or sha(path) != expected:
        raise ValueError('Modified record or external path: ' + relative)
    return path


def strategy_for(order):
    if order not in SYSTEMS:
        raise ValueError('Unknown system.')
    return "fixed" if order == FIXED else "incremental"


def method_for(strategy):
    if strategy not in ("fixed", "incremental"):
        raise ValueError('Unknown strategy.')
    return "llm_rag_fisso_k1" if strategy == "fixed" else "llm_rag_incrementale_k1"

"""Percorsi e registri della sola campagna incrementale."""
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
REPO = BASE.parents[3]
PROTOTIPO = REPO / "prototipo"
STRUMENTI = BASE.parent.parent / "test_qasmbench/strumenti"
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
DEFAULT_ID = "qasmbench50_incrementale_v1"
BASELINE = BASE.parent.parent / "test_qasmbench/risultati/llm_rag"
ORACLE = Path.home() / "oracoli_qasmbench_test/qasmbench50_max3_v1/analisi/20261001T200715_e284d5b5/confronto_llm_rag_k5/risultati/dati.json"


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_score(row):
    value = row.get("score")
    return row.get("status") == "success" and finite(value) and 0 <= value <= 1


def campaign_path(experiment_id, order):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", experiment_id):
        raise ValueError("Identificativo esperimento non valido.")
    if order not in ORDERS:
        raise ValueError("Ordinamento sconosciuto.")
    path = BASE / "ordinamenti" / order / "campagne" / experiment_id
    if not path.resolve().is_relative_to(BASE.resolve()):
        raise ValueError("La campagna deve restare nella nuova area di archivio.")
    return path


def order_rows(rows, order):
    import random
    result = [dict(row) for row in rows]
    if order == "02_inverso":
        result.reverse()
    elif order in ORDERS and ORDERS[order] is not None:
        random.Random(ORDERS[order]).shuffle(result)
    elif order != "01_manifest":
        raise ValueError("Ordinamento sconosciuto.")
    return result


def test_rows():
    if sha(SOURCE) != "04ade5a7a666c401d590f60480446bf78e046044adbc7f710e6a353e115517f1":
        raise ValueError("Manifest originale del corpus modificato.")
    rows = [r for r in read(SOURCE)["circuits"] if r["split"] == "external_test"]
    if len(rows) != 50 or len({r["circuit_id"] for r in rows}) != 50:
        raise ValueError("Attesi i 50 identificativi Test QASMBench del manifest.")
    from collections import Counter
    if Counter(r["size_group"] for r in rows) != {"small": 30, "medium": 15, "large": 5}:
        raise ValueError("Distribuzione QASMBench diversa da 30/15/5.")
    for row in rows:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", row["circuit_id"]):
            raise ValueError("Identificativo circuito non sicuro.")
        if sha(source_path(row)) != row["source_sha256"]:
            raise ValueError("Circuito originale modificato: " + row["circuit_id"])
    return rows


def memory_digest(records):
    return digest(records)


def step_folder(base, position, row):
    return base / "circuiti" / f"{position:03d}_{row['circuit_id']}"


def frozen_files():
    """Impronte dei sorgenti effettivamente riutilizzati; nessun risultato futuro."""
    paths = [SOURCE, PROTOTIPO / "config.json", PROTOTIPO / "requirements.txt",
             PROTOTIPO / "app.py", PROTOTIPO / "portable_features.py",
             BASE.parent.parent / "test_qasmbench/piano.json", BASE / "piano.json"]
    paths += [BASE / name for name in ("comune.py", "memoria.py", "adattatore.py", "registro.py", "esperimento.py")]
    paths += list(STRUMENTI.glob("*.py"))
    for folder in ("prototype", "qiskit_dataset", "scripts", "schemas", "configs"):
        for pattern in ("*.py", "*.json", "*.mjs", "*.js"):
            paths += list((PROTOTIPO / folder).rglob(pattern))
    paths += list((PROTOTIPO / "runtime/toon").glob("*.mjs"))
    seal = PROTOTIPO / "data/seal.json"
    paths += [seal] + [PROTOTIPO / p for p in read(seal)["files"]]
    return {str(p.relative_to(REPO)): sha(p) for p in sorted(set(paths))}


def baseline_files(rows):
    """Valida il controllo storico; restituisce soltanto impronte al runner."""
    identity = read(BASELINE / "esecuzione.json")
    if identity.get("server", {}).get("model_sha256") != read(PROTOTIPO / "config.json")["profile"]["artifact"]["gguf_sha256"]:
        raise ValueError("Il controllo storico usa un diverso modello LLM.")
    files = {str((BASELINE / "esecuzione.json").relative_to(REPO)):
             sha(BASELINE / "esecuzione.json")}
    for row in rows:
        path = BASELINE / "circuiti" / row["circuit_id"] / "esito.json"
        result = read(path)
        if (result.get("circuit_id") != row["circuit_id"]
                or result.get("source_sha256") != row["source_sha256"]
                or result.get("method") != "llm_rag"):
            raise ValueError("Controllo storico incoerente: " + row["circuit_id"])
        if result.get("status") == "success" and not valid_score(result):
            raise ValueError("Score storico non valido.")
        files[str(path.relative_to(REPO))] = sha(path)
    return files


def verify_hashes(files):
    for relative, expected in files.items():
        path = (REPO / relative).resolve()
        if not path.is_relative_to(REPO.resolve()) or sha(path) != expected:
            raise ValueError("Fonte cambiata: " + relative)


def check_contract(base, expected=None, *, verify_runtime=True):
    path = base / "contratto.json"
    contract = read(path)
    if expected is not None and contract != expected:
        raise ValueError("Contratto incompatibile. Usare un nuovo --experiment-id.")
    if contract.get("revision") != "qasmbench50-rag-incrementale-v1":
        raise ValueError("Revisione della campagna non supportata.")
    if verify_runtime:
        verify_hashes(contract["files"])
    verify_hashes(contract["baseline_files"])
    return contract


def path_hashes(base, folder):
    return {str(p.relative_to(base)): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name != "commit.json" and not p.name.startswith(".")}


def validate_relative_file(base, relative, expected):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or sha(path) != expected:
        raise ValueError("Registro alterato o percorso esterno: " + relative)
    return path

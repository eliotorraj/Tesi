"""Controlla le impronte e la copertura registrata della revisione, senza eseguire esperimenti.

Uso dalla radice: python3 archivio/riorganizzazione_2026_09_21/revisione_script/verifica_copertura.py
Il controllo verifica la tracciabilita del rapporto; non puo dimostrare da solo
che una lettura umana sia stata corretta o che il programma sia privo di difetti.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify() -> dict:
    directory = Path(__file__).resolve().parent
    root = directory.parents[2]
    inventory = json.loads((directory / "inventario_completo.json").read_text(encoding="utf-8"))
    baseline = json.loads((root / "archivio/riorganizzazione_2026_09_20/revisione_script/inventario_operativo.json").read_text(encoding="utf-8"))
    expected = {entry["current_path"]: entry for entry in baseline["files"]}
    seen = set()
    errors = []
    lines = 0
    for entry in inventory["files"]:
        name = entry["current_path"]
        if name in seen:
            errors.append({"path": name, "error": "duplicate"})
        seen.add(name)
        if name not in expected:
            errors.append({"path": name, "error": "not_in_original_scope"})
            continue
        path = root / name
        if not path.is_file():
            errors.append({"path": name, "error": "missing_file"})
            continue
        content = path.read_bytes()
        count = len(content.decode("utf-8-sig").splitlines())
        lines += count
        digest = hashlib.sha256(content).hexdigest()
        frozen = expected[name].get("current_sha256", expected[name]["sha256"])
        if digest != entry["sha256"] or digest != frozen:
            errors.append({"path": name, "error": "sha256_mismatch"})
        if count != entry["lines"]:
            errors.append({"path": name, "error": "line_count_mismatch"})
        # Unione degli intervalli: copertura esplicita, niente buchi o righe esterne.
        covered = set()
        for first, last in entry["manual_ranges"]:
            if first < 1 or last < first or last > count:
                errors.append({"path": name, "error": "invalid_range", "range": [first, last]})
            covered.update(range(first, last + 1))
        if covered != set(range(1, count + 1)):
            errors.append({"path": name, "error": "incomplete_manual_range"})
        if entry["manual_or_static"] != "manual_full":
            errors.append({"path": name, "error": "manual_review_not_complete"})
    for name in sorted(set(expected) - seen):
        errors.append({"path": name, "error": "missing_review"})
    return {"files_expected": len(expected), "files_reviewed": len(seen),
            "current_lines": lines, "errors": errors, "passed": not errors,
            "experiment_or_model_executed": False}


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)

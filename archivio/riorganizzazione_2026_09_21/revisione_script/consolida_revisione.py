'Combine the new review records and 14 prior reads, then check fingerprints and coverage.'
from __future__ import annotations

import copy
import json
from pathlib import Path
from verifica_copertura import verify

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
OLD_PATH = ROOT / "archivio/riorganizzazione_2026_09_20/revisione_script/inventario_operativo.json"


def main() -> None:
    previous = json.loads(OLD_PATH.read_text(encoding="utf-8"))
    added = {}
    for name in ("scripts.json", "prototype_data.json", "llm_tests.json"):
        report = json.loads((DIRECTORY / name).read_text(encoding="utf-8"))
        rows = report if isinstance(report, list) else report["files"]
        definitions = {} if isinstance(report, list) else {f["id"]: f for f in report.get("findings", [])}
        for row in rows:
            path = row["current_path"]
            if path in added or row.get("manual_or_static") != "manual_full":
                raise ValueError(f'Duplicate review record or incomplete reading: {path}')
            row = copy.deepcopy(row)
            row["findings"] = [copy.deepcopy(definitions[f]) if isinstance(f, str) else f for f in row.get("findings", [])]
            row["review_source"] = name
            row["review_date"] = "2026-09-21"
            added[path] = row
    if len(added) != 133:
        raise ValueError(f'Expected 133 new reads; found {len(added)}')
    rows = []
    for old in previous["files"]:
        path = old["current_path"]
        if old["manual_or_static"] == "manual_full_plus_static":
            if path in added:
                raise ValueError(f'Unexpected assignment of an already complete review record: {path}')
            row = copy.deepcopy(old)
            row["sha256"] = old.get("current_sha256", old["sha256"])
            row["manual_or_static"] = "manual_full"
            row["review_source"] = str(OLD_PATH.relative_to(ROOT))
            row["review_date"] = "2026-09-20"
            row["findings"] = [dict(previous["findings"][key], id=key) if isinstance(key, str) else key for key in old["findings"]]
        else:
            row = added.pop(path)
        rows.append(row)
    if added:
        raise ValueError(f'File outside the original scope: {sorted(added)}')
    result = {"scope": '147 operational scripts inventoried on 20 September, excluding distinct historical copies',
              "previous_complete": 14, "new_complete": 133,
              "method": 'Complete reading and manual analysis; prior syntax checks; documented isolated reproductions',
              "files": rows}
    (DIRECTORY / "inventario_completo.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verification = verify()
    (DIRECTORY / "verifica_copertura.json").write_text(json.dumps(verification, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not verification["passed"]:
        raise ValueError(verification["errors"])
    lines = ['# Complete review of 147 scripts', "", 'Each row references the inspected source. Details, invariants, dependencies and findings are in JSON review records and the three group reports.', "", 'The 14 reviews from 20 September are retained; the remaining 133 are dated 21 September. Current hashes match the frozen reference.', "", '| File | Lines read | Purpose | Findings |', "| --- | ---: | --- | --- |"]
    for row in rows:
        path = row["current_path"]
        label = path.removeprefix("archivio/esperimento_v2/")
        purpose = str(row.get("purpose", "")).replace("|", "/").replace("\n", " ")
        findings = ", ".join(str(f.get("id", f.get("title", "rilievo"))) if isinstance(f, dict) else str(f) for f in row.get("findings", [])) or 'No new demonstrated defect'
        lines.append(f"| [{label}](../../../{path}) | {row['lines']} | {purpose} | {findings} |")
    (DIRECTORY / "rassegna_147_script.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()

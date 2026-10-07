"""Verify official-study hashes without inference, scoring or Test opening.

Use standard Python from any directory. Manifest paths remain relative to the experiment root. --output never overwrites files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "esperimento_v2"
    studies = list(root.glob("artifacts/experiments/*/llm_selection/studies/local-llm-v2"))
    if len(studies) != 1:
        raise SystemExit('Cannot identify exactly one local-llm-v2 study.')
    study = studies[0]
    frozen = json.loads((study / "frozen_study.json").read_text())
    groups = {"code": frozen["code_hashes"], "inputs": frozen["input_hashes"]}
    for model, profile in frozen["models"].items():
        groups[f"technical/{model}"] = profile["technical_evidence_hashes"]
        groups[f"validation/{model}"] = json.loads((study / model / "sealed.json").read_text())["files"]
    groups["selection"] = json.loads((study / "selection_complete.json").read_text())["files"]
    failures, cache, counts, external = [], {}, {}, {}
    for group, files in groups.items():
        counts[group] = len(files)
        for name, expected in files.items():
            logical = Path(name)
            if logical.is_absolute() or ".." in logical.parts:
                failures.append({"group": group, "file": name, "reason": "invalid_reference"})
                continue
            path = (root / logical).resolve()
            # I modelli storici possono essere collegamenti allo spazio esterno.
            # Read only explicitly listed files protected by SHA256.
            if not path.is_relative_to(root.resolve()):
                external[name] = str(path)
            if name not in cache:
                if not path.is_file():
                    cache[name] = None
                else:
                    # Stream large aggregates in chunks rather than loading them into RAM.
                    with path.open("rb") as handle:
                        cache[name] = hashlib.file_digest(handle, "sha256").hexdigest()
            if cache[name] != expected:
                failures.append({"group": group, "file": name, "reason": "missing_or_changed"})
    result = {"study": "local-llm-v2", "ok": not failures, "groups": counts,
              "unique_files_checked": len(cache), "failures": failures, "external_dependencies": external,
              "scope": "file hashes only; no Test release, inference, scoring or model loading"}
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

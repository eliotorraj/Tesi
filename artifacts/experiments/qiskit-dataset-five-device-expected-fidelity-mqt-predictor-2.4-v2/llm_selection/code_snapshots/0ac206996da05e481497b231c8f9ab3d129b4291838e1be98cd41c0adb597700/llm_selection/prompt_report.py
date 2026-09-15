"""Riepilogo riproducibile dei prompt e di una prova tecnica train, senza nuovi score."""
from __future__ import annotations
import argparse
import hashlib
import statistics
from pathlib import Path
from .common import ROOT, OUTPUT, read_json, write_json

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(audit_label, run_label=None):
    audit_path = OUTPUT/"prompt_audits"/audit_label/"report.json"
    audit = read_json(audit_path)
    rows = audit["rows"]
    result = {"audit": str(audit_path.relative_to(ROOT)), "audit_sha256": sha(audit_path),
              "encoding_revision": audit["revision"], "token_method": audit["token_method"],
              "tokenizer_sha256": audit["tokenizer_sha256"],
              "prompt_count": len(rows), "roundtrip_passed": sum(r["roundtrip_verified"] for r in rows),
              "rag_example_counts": sorted({r["rag_examples"] for r in rows}), "splits": {}, "train": []}
    for split in ("train", "validation"):
        selected = [r for r in rows if r["split"] == split]
        if selected:
            result["splits"][split] = {"count": len(selected),
                "compact_tokens_min": min(r["compact_tokens"] for r in selected),
                "compact_tokens_max": max(r["compact_tokens"] for r in selected),
                "compact_tokens_median": statistics.median(r["compact_tokens"] for r in selected),
                "token_reduction_percent_median": statistics.median(r["token_reduction_percent"] for r in selected)}
    for row in rows:
        if row["split"] == "train":
            result["train"].append({k: row[k] for k in ("circuit_id", "source_sha256", "original_prompt_sha256",
                  "clarified_tokens", "compact_tokens", "token_reduction_percent",
                  "retrieval_reexecuted_and_verified", "train_self_check")})
    originals_path = OUTPUT/"analyses/qwen-prova-07/source_hashes.json"
    if originals_path.exists():
        originals = read_json(originals_path)
        changed = [path for path, expected in originals.items() if sha(ROOT/path) != expected]
        if changed:
            raise ValueError("Historical artifacts changed: "+repr(changed))
        result["previous_run_artifacts_unchanged"] = {"count": len(originals), "manifest_sha256": sha(originals_path)}
    if run_label:
        directory = OUTPUT/"technical_episodes"/run_label/"qwen/p1_t0/dj_indep_tket_2"
        decision = read_json(directory/"decision.json")
        if decision["split"] != "train":
            raise ValueError("This report accepts a technical train case only")
        result["qwen_dj"] = {"directory": str(directory.relative_to(ROOT)), "decision": decision,
                            "decision_sha256": sha(directory/"decision.json"), "attempts": []}
        for path in sorted(directory.glob("attempt_*/summary.json")):
            summary = read_json(path)
            response = summary.get("response", {})
            request_path = path.parent/"call/request.json"
            request = read_json(request_path) if request_path.exists() else {}
            item = {k: summary.get(k) for k in ("attempt", "status", "json_valid", "schema_valid", "issues",
                                                    "input_tokens", "train_self_check")}
            item.update(response_path=str((path.parent/"call/response.json").relative_to(ROOT)),
                        response_sha256=sha(path.parent/"call/response.json") if response else None,
                        usage=response.get("usage"), timings=response.get("timings"),
                        elapsed_seconds=response.get("elapsed_seconds"), finish_reason=response.get("finish_reason"),
                        max_output_tokens=request.get("n_predict"))
            result["qwen_dj"]["attempts"].append(item)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--run")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for label in (args.audit, args.run):
        if label and (Path(label).name != label or label in (".", "..")):
            raise ValueError("Use a plain label")
    result = build(args.audit, args.run)
    if args.output.exists() and read_json(args.output) != result:
        raise ValueError("Different report already exists; choose a new output path")
    write_json(args.output, result)
    print(args.output)

if __name__ == "__main__":
    main()

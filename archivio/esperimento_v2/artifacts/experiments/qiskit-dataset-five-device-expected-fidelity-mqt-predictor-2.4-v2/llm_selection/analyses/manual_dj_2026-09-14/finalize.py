"""Verifica conservazione delle fonti e crea il manifest dell'analisi."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
ROOT = Path.cwd()
DEST = Path(__file__).resolve().parent
OUTPUT = DEST.parent.parent
def read(path):
    return json.loads(path.read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
old_sources = read(OUTPUT/"analyses/qwen-prova-07/source_hashes.json")
changed = [path for path, expected in old_sources.items() if sha(ROOT/path) != expected]
assert not changed, changed
provenance = read(DEST/"provenance.json")
assert all(sha(Path(path)) == expected for path, expected in provenance["source_sha256"].items())
assert sha(DEST/"reasoning_utente.txt") == provenance["source_sha256"][provenance["reasoning_origin"]]
assert read(DEST/"preliminary.json")["schema_valid"]
diagnostic = read(DEST/"validation_all_issues.json")
assert diagnostic["is_valid"] is False and diagnostic["issue_count"] == 21
attempts_path = DEST/"analysis_attempts.json"
attempts = read(attempts_path)
attempts.append({"attempt": 2, "status": "completed", "schema_valid": True, "semantic_valid": False, "diagnostic_issue_count": 21})
attempts_path.write_text(json.dumps(attempts, ensure_ascii=False, indent=2)+"\n")
resources = [json.loads(line) for line in (DEST/"server.resources.snapshot.jsonl").read_text().splitlines() if line.strip()]
resource_summary = {
    "scope": "Intero intervallo copiato del server, comprende fasi inattive; non media della sola inferenza.",
    "samples": len(resources),
    "from_utc": resources[0]["utc"], "to_utc": resources[-1]["utc"],
    "gpu_dedicated_peak_bytes": max(r.get("gpu_dedicated_bytes") or 0 for r in resources),
    "gpu_shared_peak_bytes": max(r.get("gpu_shared_bytes") or 0 for r in resources),
    "thermal_pause_count_max": max(r.get("thermal_pause_count") or 0 for r in resources),
    "available_windows_ram_min_bytes": min(r["system_available_bytes"] for r in resources if r.get("system_available_bytes")),
    "hotspot_max_c": max(s["hotspot_c"] for r in resources for s in r.get("gpu_sensors", []) if s.get("hotspot_c") is not None),
}
with (DEST/"resource_summary.json").open("x") as f:
    json.dump(resource_summary, f, ensure_ascii=False, indent=2)
    f.write("\n")
files = sorted(p for p in DEST.iterdir() if p.is_file() and p.name != "manifest.json")
manifest = {"created_at": datetime.now(timezone.utc).isoformat(),
    "old_source_files_verified_unchanged": len(old_sources), "analysis_source_hashes_verified": True,
    "reasoning_copy_verified": True,
    "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in files}}
with (DEST/"manifest.json").open("x") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("Originali invariati:", len(old_sources), "file analisi:", len(files))
print("Risorse:", json.dumps(resource_summary, ensure_ascii=False))

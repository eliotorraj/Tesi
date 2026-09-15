from pathlib import Path
import hashlib,json
root=Path.cwd()
audit=root/"artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/rag/audit"
before=json.loads((audit/"protected_before.json").read_text())
after={}
for folder in ("datasets","artifacts","archivio","configs"):
 for p in sorted((root/folder).rglob("*")):
  if not p.is_file() or audit.parent in p.parents: continue
  with p.open("rb") as f: after[str(p.relative_to(root))]=hashlib.file_digest(f,"sha256").hexdigest()
changed=[name for name,digest in before.items() if after.get(name)!=digest]
added=sorted(set(after)-set(before))
report={"protected_files":len(before),"changed_or_missing":changed,"added_outside_rag":added,"unchanged":not changed and not added}
(audit/"integrity_comparison.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report),flush=True)
assert report["unchanged"], report

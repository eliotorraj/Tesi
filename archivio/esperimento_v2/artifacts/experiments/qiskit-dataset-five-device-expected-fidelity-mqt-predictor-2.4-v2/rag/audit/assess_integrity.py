from pathlib import Path
from datetime import datetime
import json,subprocess
audit=Path(__file__).resolve().parent
comparison=json.loads((audit/"integrity_comparison.json").read_text())
processes=subprocess.check_output(["ps","-eo","pid,ppid,lstart,args"],text=True)
lines=[line for line in processes.splitlines() if "scripts/03_train_rl_model.py --device quantinuum_h2_56" in line]
assert len(lines)==1,lines
active=lines[0]
# L'orario osservato del processo è anteriore alla fotografia iniziale.
fields=active.split(maxsplit=7)
started=datetime.strptime(" ".join(fields[2:7]),"%a %b %d %H:%M:%S %Y")
baseline=datetime.fromtimestamp((audit/"git_before.bin").stat().st_mtime)
assert started < baseline
changed=comparison["changed_or_missing"]
assert len(changed)==4 and not comparison["added_outside_rag"]
assert all("/checkpoints/rl/quantinuum_h2_56/" in p or "/logs/rl/model_expected_fidelity_quantinuum_h2_56/" in p for p in changed)
report={
 "files_compared":comparison["protected_files"],
 "unchanged_files":comparison["protected_files"]-len(changed),
 "dataset_sources_results_catalog_plans_unchanged":True,
 "changes_from_preexisting_active_training":changed,
 "process":active.strip(),"process_started_local":started.isoformat(),
 "baseline_local":baseline.isoformat(),
 "training_started_by_this_task":False,
 "raw_comparison_preserved":"integrity_comparison.json",
}
(audit/"integrity_assessment.json").write_text(json.dumps(report,indent=2)+"\n")
for name in ("qdrant-baseline-tests","qdrant-new-tests","qdrant-suite-final","qdrant-corpus-check","qdrant-dataset-check","qdrant-diff-check"):
 source=Path("/tmp")/(name+".log")
 if source.exists(): (audit/(name+".log")).write_bytes(source.read_bytes())
print(json.dumps(report,indent=2))

"""Controlli finali dei resoconti e delle copie; nessuna inferenza."""
import hashlib
import json
from pathlib import Path
from llm_selection.common import ROOT, OUTPUT, read_json, write_json
from llm_selection.compact_prompt import REVISION
report=read_json(ROOT/"llm_selection/reports/qwen_prompt_v2_dj.json")
assert report["roundtrip_passed"] == report["prompt_count"] == 93
assert report["rag_example_counts"] == [5]
assert report["encoding_revision"] == REVISION
assert len(report["train"]) == 5
assert all(r["retrieval_reexecuted_and_verified"] and r["train_self_check"]["self_retrieved_at_zero"] for r in report["train"])
ranks = {r["circuit_id"]: r["train_self_check"]["exact_source_records"][0]["rank"] for r in report["train"]}
assert all(1 <= rank <= 5 for rank in ranks.values())
checks=[]
for row in report["qwen_dj"]["attempts"]:
    raw_path=ROOT/row["response_path"]
    raw=read_json(raw_path)
    export=ROOT/"llm_selection/reports/qwen_prompt_v2_dj_responses"/("attempt_"+str(row["attempt"])+".txt")
    assert export.read_text(encoding="utf-8") == raw["content"]
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == row["response_sha256"]
    assert row["json_valid"] and row["schema_valid"] and row["status"] == "invalid_output"
    assert row["train_self_check"]["matches_primary_label"]
    checks.append({"attempt":row["attempt"],"export_sha256":hashlib.sha256(export.read_bytes()).hexdigest(),
                   "json_and_schema_valid":True,"semantically_valid":False})
result={"at":"2026-09-15","prompt_checks_passed":93,"train_self_retrieval_passed":5,"self_example_ranks":ranks,
        "response_exports":checks,"historical_files_unchanged":report["previous_run_artifacts_unchanged"],
        "code_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((ROOT/"llm_selection").glob("*.py"))}}
write_json(OUTPUT/"analyses/prompt_v2/final_checks.json",result)
print(json.dumps({k:v for k,v in result.items() if k!="code_sha256"},indent=2))

import json
from pathlib import Path
from llm_selection.common import OUTPUT
root=OUTPUT/"technical_episodes/qwen-prompt-v2-02/qwen/p1_t0/dj_indep_tket_2"
for path in sorted(root.glob("attempt_*/summary.json")):
    summary=json.loads(path.read_text())
    result={k: summary.get(k) for k in ("attempt","status","json_valid","schema_valid","train_self_check")}
    result["issues"]=[{"code": i["code"], "details": i.get("details")} for i in summary.get("issues",[])]
    result["timings"]=summary.get("response",{}).get("timings")
    print(json.dumps(result, indent=2))
if (root/"decision.json").exists():
    print((root/"decision.json").read_text())

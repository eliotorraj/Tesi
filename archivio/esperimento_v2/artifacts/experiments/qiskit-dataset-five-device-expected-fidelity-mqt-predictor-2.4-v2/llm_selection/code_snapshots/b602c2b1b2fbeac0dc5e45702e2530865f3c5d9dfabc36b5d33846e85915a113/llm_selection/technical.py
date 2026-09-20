"""Riepilogo delle prove train e degli arresti, senza score di validation."""
from collections import Counter
from pathlib import Path
from .common import OUTPUT, ROOT, read_json

def technical_summary():
    episodes=[]
    for begin_path in sorted((OUTPUT/"technical_episodes").glob("*/*/*/*/begin.json")):
        begin=read_json(begin_path);directory=begin_path.parent
        decision=read_json(directory/"decision.json") if (directory/"decision.json").exists() else {}
        launch=begin["launch"]
        episodes.append({"label":directory.parents[2].name,"model":directory.parents[1].name,
            "configuration":directory.parent.name,"circuit_id":begin["circuit_id"],"split":begin["split"],
            "status":decision.get("status","interrupted_or_pending"),
            "failure_category":(decision.get("failure") or {}).get("category"),
            "llm_calls":decision.get("llm_calls"),"repair_count":decision.get("repair_count"),
            "precision":Path(launch["model_path"].replace("\\","/")).stem,
            "context":launch["context"],"cache_type":launch.get("cache_type"),
            "directory":str(directory.relative_to(ROOT))})
    servers=[]
    for path in sorted((OUTPUT/"servers").glob("*/launch.json")):
        launch=read_json(path)
        request_path=OUTPUT/"controllers"/path.parent.name.rsplit("-",1)[0]/"request.json"
        request=read_json(request_path) if request_path.exists() else {}
        phase=("train_technical" if request["technical"] else "validation") if "technical" in request else "historical_unknown"
        end=read_json(path.parent/"exit.json") if (path.parent/"exit.json").exists() else {}
        abort=read_json(path.parent/"resource_abort.json") if (path.parent/"resource_abort.json").exists() else {}
        servers.append({"server_label":path.parent.name,"phase":phase,"precision":Path(launch["model_path"].replace("\\","/")).stem,
            "context":launch["context"],"cache_type":launch.get("cache_type"),"batch":launch.get("batch"),
            "micro_batch":launch.get("micro_batch"),"recorded_exit":bool(end),
            "abort_reason":abort.get("reason",end.get("abort_reason")),
            "pause_count":end.get("thermal_pause_count"),"paused_seconds":end.get("thermal_paused_seconds"),
            "directory":str(path.parent.relative_to(ROOT))})
    return {"episodes":episodes,"servers":servers,
            "episode_status_counts":dict(Counter(r["status"] for r in episodes)),
            "note":"Incomplete episodes are not automatically rerun. Historical exploratory logs also remain in technical/ and incidents/."}

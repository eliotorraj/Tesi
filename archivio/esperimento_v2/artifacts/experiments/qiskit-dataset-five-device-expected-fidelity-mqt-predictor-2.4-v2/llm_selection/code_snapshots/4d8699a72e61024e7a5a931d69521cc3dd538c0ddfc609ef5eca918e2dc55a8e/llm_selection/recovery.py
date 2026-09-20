"""Ispezione delle scritture interrotte; conserva sempre i file originali."""
import json
from pathlib import Path
from .common import OUTPUT, now, write_json

def valid_prefix(path):
    data=Path(path).read_bytes()
    rows=[]
    offset=0
    for line in data.splitlines(keepends=True):
        if not line.strip():
            offset+=len(line)
            continue
        try:
            row=json.loads(line)
        except (ValueError,UnicodeDecodeError):
            break
        rows.append(row)
        offset+=len(line)
    return rows, {"file":str(path),"valid_records":len(rows),"valid_prefix_bytes":offset,
                  "unreadable_tail_bytes":len(data)-offset,"file_bytes":len(data)}

def main():
    report={"at":now(),"kind":"unexpected_host_shutdown","files":[],"episodes":[],"sources":[]}
    for path in sorted((OUTPUT/"technical").glob("*/*resources.jsonl")):
        rows,info=valid_prefix(path)
        info["last_observed"]=rows[-1] if rows else None
        if "gpu_" not in path.name and rows:
            info["min_available_ram_bytes"]=min(r["system_available_bytes"] for r in rows)
            info["peak_working_set_bytes"]=max(r["peak_working_set_bytes"] for r in rows)
        report["files"].append(info)
    for path in sorted((OUTPUT/"technical_episodes").glob("*/*/*/*/begin.json")):
        episode=path.parent
        if (episode/"decision.json").exists(): continue
        attempts=[]
        for attempt in sorted(episode.glob("attempt_*")):
            stream=attempt/"call"/"stream.jsonl"
            info={"attempt":attempt.name,"request_present":(attempt/"call"/"request.json").exists(),
                  "response_present":(attempt/"call"/"response.json").exists()}
            if stream.exists():
                rows,details=valid_prefix(stream)
                info.update(stream=details,last_observed=rows[-1] if rows else None)
            attempts.append(info)
        report["episodes"].append({"directory":str(episode),"status":"interrupted_without_terminal_response","attempts":attempts})
    for path in sorted((OUTPUT/"prompts").glob("*/*.json")):
        data=json.loads(path.read_text())
        from qiskit_dataset.experiment_v2 import stable_sha256
        if stable_sha256(data["prompt"])!=data["prompt_sha256"]: raise ValueError(f"Changed prompt: {path}")
        report["sources"].append({"circuit_id":path.stem,"split":path.parent.name,"prompt_verified":True})
    destination=OUTPUT/"incidents"/"2026-09-13-unexpected-shutdown"/"recovery_audit.json"
    if destination.exists(): raise ValueError("Audit already exists; do not overwrite")
    write_json(destination,report)
    print(json.dumps({"verified_prompts":len(report["sources"]),"interrupted_episodes":len(report["episodes"]),
                      "resources":[{k:v for k,v in r.items() if k!="last_observed"} for r in report["files"]]},indent=2))
if __name__=="__main__": main()

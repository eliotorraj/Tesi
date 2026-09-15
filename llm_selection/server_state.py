"""Accerta un arresto senza inventare ora o codice di uscita."""
import json
import subprocess
from .common import read_json, write_json

def ensure_stopped(directory):
    if (directory/"exit.json").exists(): return read_json(directory/"exit.json")
    if (directory/"recovery_closed.json").exists(): return read_json(directory/"recovery_closed.json")
    from .controller import ps_command
    from .common import windows_path
    result=subprocess.run(ps_command("inspect_server.ps1","-RunDirectory",windows_path(directory)),
                          capture_output=True,text=True,check=True,timeout=20)
    observed=json.loads(result.stdout.lstrip("\ufeff"))
    if observed["owned_process_running"]: raise ValueError("Stop inference server before final evaluation")
    record={**observed,"status":"observed_stopped_after_interruption",
            "ended_at":None,"exit_code":None,"missing_reason":"Monitor did not persist a normal exit record"}
    write_json(directory/"recovery_closed.json",record)
    return record

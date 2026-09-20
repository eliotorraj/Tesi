"""Registri del server Windows su D; percorso logico del progetto conservato."""
from pathlib import Path
from .common import OUTPUT, append_jsonl, now, windows_path

NATIVE_SERVER_ROOT=Path("/mnt/d/Tesi-mqt/llm-selection")/OUTPUT.parent.name/"server_logs"

def allocate_server_directory(logical_directory, events, *, native_root=None):
    logical_directory=Path(logical_directory)
    if native_root is None:
        if not Path("/mnt/d").is_mount():
            raise ValueError("Disco D non montato in /mnt/d; nessun modello avviato")
        native_root=NATIVE_SERVER_ROOT
    native_root=Path(native_root).resolve()
    name=logical_directory.name
    if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name):
        raise ValueError("Invalid server log directory name")
    native_directory=native_root/name
    if logical_directory.exists() or logical_directory.is_symlink():
        raise ValueError("Server logs already exist; use a new label")
    if native_directory.exists() or native_directory.is_symlink():
        raise ValueError("Native server logs already exist; use a new label")
    native_root.mkdir(parents=True,exist_ok=True)
    logical_directory.parent.mkdir(parents=True,exist_ok=True)
    # The target remains absent until serve.ps1 creates it with its no-overwrite check.
    logical_directory.symlink_to(native_directory,target_is_directory=True)
    record={"at":now(),"event":"server_log_storage_allocated",
            "logical_directory":str(logical_directory),"native_directory":str(native_directory),
            "windows_directory":windows_path(native_directory),
            "reason":"Windows durable flush uses a native Windows directory instead of the WSL UNC share"}
    append_jsonl(events,record)
    return record

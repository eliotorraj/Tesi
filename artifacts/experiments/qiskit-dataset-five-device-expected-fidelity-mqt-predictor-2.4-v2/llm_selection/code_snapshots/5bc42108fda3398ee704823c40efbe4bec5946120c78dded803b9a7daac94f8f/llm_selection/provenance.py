"""Provenienza leggibile e copie del codice; nessuna variabile segreta salvata."""
import importlib.metadata
import platform
import subprocess
from pathlib import Path
from scripts.mqt_predictor_protocol import file_sha256
from .common import ROOT, OUTPUT, digest, now, write_json

def code_files():
    paths=[]
    for folder in ("prototype/quantum_assistant","qiskit_dataset","llm_selection"):
        paths.extend((ROOT/folder).rglob("*.py"))
    paths.extend([ROOT/"scripts/mqt_predictor_protocol.py",ROOT/"llm_selection/serve.ps1",ROOT/"llm_selection/gpu_monitor.ps1"])
    return sorted(set(paths))

def code_hashes():
    return {str(p.relative_to(ROOT)):file_sha256(p) for p in code_files()}

def capture(directory):
    hashes=code_hashes()
    snapshot=OUTPUT/"code_snapshots"/digest(hashes)
    for relative,sha in hashes.items():
        target=snapshot/relative
        if target.exists():
            if file_sha256(target)!=sha: raise ValueError("Code snapshot changed")
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/relative).read_bytes())
    metadata={"at":now(),"code_hashes":hashes,"code_snapshot":str(snapshot),
              "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
              "git_status":subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
              "python":platform.python_version(),"platform":platform.platform(),
              "dependencies":sorted((d.metadata.get("Name",""),d.version) for d in importlib.metadata.distributions()),
              "uv_lock_sha256":file_sha256(ROOT/"uv.lock"),
              "meminfo":Path("/proc/meminfo").read_text(),
              "cpuinfo":Path("/proc/cpuinfo").read_text(),
              "test_content_accessed":False}
    write_json(Path(directory)/"provenance.json",metadata)
    return metadata

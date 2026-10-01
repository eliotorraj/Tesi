"""Processi isolati, risultati durevoli e ripresa dei soli tentativi non iniziati."""
import json, os, signal, subprocess, sys, time
from pathlib import Path
import settings as s

def stop(process):
    if process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()

def execute(folder,job,timeout):
    folder=Path(folder);result=folder/"result.json"
    if (folder/"job.json").exists() and s.read(folder/"job.json")!=job:raise ValueError("Ingressi diversi per un tentativo già registrato")
    if result.exists():return s.read(result)
    if (folder/"job.json").exists():
        # Una precedente interruzione resta terminale, senza duplicare lavoro.
        value={"status":"interrupted","score":None,"error":"Tentativo iniziato senza esito durevole"}
        s.save(result,value);return value
    s.save(folder/"job.json",job)
    start=time.perf_counter()
    with (folder/"stdout.txt").open("w") as stdout,(folder/"stderr.txt").open("w") as stderr:
        proc=subprocess.Popen([sys.executable,"-B",str(s.KIT/"worker.py"),str(folder/"job.json")],
             stdout=stdout,stderr=stderr,start_new_session=True)
        try:
            proc.wait(timeout=timeout)
            if result.exists():return s.read(result)
            value={"status":"failure","score":None,"error":"worker_exit_"+str(proc.returncode)}
        except subprocess.TimeoutExpired:
            stop(proc)
            # Il risultato completo pubblicato prima del timeout viene conservato.
            if result.exists():return s.read(result)
            value={"status":"timeout","score":None,"error":"process_timeout"}
        except BaseException:
            stop(proc)
            if not result.exists():s.save(result,{"status":"interrupted","score":None})
            raise
    value["process_seconds"]=time.perf_counter()-start
    s.save(result,value);return value

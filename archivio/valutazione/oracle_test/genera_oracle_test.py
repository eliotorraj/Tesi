'Private Test matrix: 90 circuits, 5 Targets, 12 configurations, seeds 0/1/2.'
from __future__ import annotations
import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4
sys.dont_write_bytecode=True
from oracle_core import *

def kill(process):
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait()

def conclude(folder,job,process,started,forced=None):
    if forced:
        status,reason=forced;r=terminal(job,status,reason)
        if (folder/"worker_result.json").exists():r["worker_result_preserved"]=True
    elif (folder/"worker_result.json").exists():
        r=validate_result(job,read(folder/"worker_result.json"),folder)
    else:
        r=terminal(job,"failure","worker_without_result",returncode=process.returncode)
    r={**r,"process_seconds":time.monotonic()-started}
    publish(folder/"esito.json",r)
    return r

def run(out,identity):
    work=list(jobs(identity));active={};cursor=0;counts=Counter();session=uuid4().hex
    publish(out/"sessioni"/(session+"_inizio.json"),{"at":now(),"pid":os.getpid(),"cpu_count":os.cpu_count(),
          "platform":platform.platform(),"python":sys.version,"workers":identity["workers"],"thread_environment":THREAD_ENV})
    stopped=False
    def interrupt(*_):raise KeyboardInterrupt()
    old_handler=signal.signal(signal.SIGTERM,interrupt)
    try:
        while cursor<len(work) or active:
            while cursor<len(work) and len(active)<identity["workers"]:
                job=work[cursor];cursor+=1
                folder=out/"tentativi"/job["job_id"]
                previous=resolve_existing(folder,job)
                if previous is not None:
                    counts[previous["status"]]+=1;continue
                publish(folder/"inizio.json",{"at":now(),"session":session,"supervisor_pid":os.getpid(),"job":job})
                if not job["compatible"]:
                    publish(folder/"esito.json",terminal(job,"incompatible",'Qubit count exceeds device capacity.'))
                    counts["incompatible"]+=1;continue
                stdout=(folder/"stdout.txt").open("xb");stderr=(folder/"stderr.txt").open("xb")
                try:
                    started=time.monotonic()
                    process=subprocess.Popen([sys.executable,"-B",str(HERE/"oracle_worker.py"),str(folder)],
                        cwd=out,env={**os.environ,**THREAD_ENV},stdout=stdout,stderr=stderr,start_new_session=True)
                except Exception as exc:
                    publish(folder/"esito.json",terminal(job,"failure","worker_start_error",message=str(exc)))
                    counts["failure"]+=1
                else:active[process.pid]=(process,job,folder,started)
                finally:stdout.close();stderr.close()
            for pid,(process,job,folder,started) in list(active.items()):
                forced=None
                if process.poll() is None:
                    ready=folder/"ready.json"
                    if ready.exists():
                        if time.monotonic()-read(ready)["started_monotonic"]>identity["timeout_seconds"]+1:
                            forced=("timeout",'watchdog: over 100 s; 1 s tolerance only to save the timeout')
                    elif time.monotonic()-started>identity["startup_watchdog_seconds"]:
                        forced=("failure","worker_startup_watchdog")
                    if forced is None:continue
                kill(process)
                r=conclude(folder,job,process,started,forced)
                counts[r["status"]]+=1;del active[pid]
                done=sum(counts.values())
                if done%50==0 or done==len(work):print(f'Completed {done}/{len(work)}: '+str(dict(counts)),flush=True)
            if active:time.sleep(.1)
    except BaseException:
        stopped=True
        for process,job,folder,started in list(active.values()):
            kill(process)
            if not (folder/"esito.json").exists():
                if (folder/"worker_result.json").exists():conclude(folder,job,process,started)
                else:conclude(folder,job,process,started,("interrupted",'Interruption requested or supervisor error.'))
        raise
    finally:
        signal.signal(signal.SIGTERM,old_handler)
        publish(out/"sessioni"/(session+"_fine.json"),{"at":now(),"interrupted":stopped,"terminal_statuses_seen":dict(counts)})

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--verifica",action="store_true",help='Checks and counts without writes or compilation.')
    group.add_argument("--prepara",action="store_true",help='Freeze the plan and QASM copies externally without compilation.')
    group.add_argument("--esegui",action="store_true",help='Generate/resume the matrix without repeating terminal attempts.')
    group.add_argument("--analizza",action="store_true",help='Create a new result summary without compilation.')
    ap.add_argument("--output",type=Path,default=Path.home()/"oracoli_mqt_test/test_max3_v1")
    ap.add_argument("--workers",type=int,default=6,help='External processes, from 1 to 6; frozen in the contract.')
    args=ap.parse_args();out=external_path(args.output)
    if args.analizza:
        if not (out/"contratto.json").is_file():ap.error('Contract missing from the external directory.')
        contract=read(out/"contratto.json");identity=contract["identity"]
        if digest(identity)!=contract["identity_sha256"]:raise ValueError('Contract changed.')
    else:identity=preflight(args.workers)
    if args.verifica:
        print(json.dumps({"ready":True,"output":str(out),"plan":plan_counts(identity),
              "label":'MAX over seeds 0,1,2; maximum across all compatible pairs',"identity_sha256":digest(identity)},indent=2))
        return 0
    out.mkdir(parents=True,exist_ok=True)
    with (out/".lock").open("a+") as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('Another process is using this campaign.') from exc
        if not args.analizza:prepare(out,identity)
        if args.prepara:
            print('Plan ready; no compilation performed: '+str(out));return 0
        try:
            if args.esegui:run(out,identity)
        except KeyboardInterrupt:
            dest,summary=analyze(out,identity)
            print('Interruption preserved. Resume with the same command; analysis: '+str(dest));return 130
        dest,summary=analyze(out,identity)
        print(json.dumps(summary,indent=2));print('External analysis: '+str(dest))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

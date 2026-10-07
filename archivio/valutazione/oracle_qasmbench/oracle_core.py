'Separate Test oracle: identity, persistence, matrix and aggregation.'
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4
import csv
import hashlib
import json
import math
import os
import platform
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
KIT=REPO/"riproducibilita"
PROTO=KIT/"comune/framework"
TEST_TOOLS=KIT/"test"
SOURCE=KIT/"circuiti/esterni/qasmbench/manifest.json"
SOURCE_SHA="04ade5a7a666c401d590f60480446bf78e046044adbc7f710e6a353e115517f1"
CATALOG=HERE/"catalogo.json"
CATALOG_SHA="6677a3838d9d0721095e7838313451eb5039601f357a19ec2fb7d0a2dbd2dc5f"
sys.dont_write_bytecode=True
sys.path[:0]=[str(HERE),str(PROTO),str(KIT/"comune"),str(TEST_TOOLS)]

def source_path(row):
    path=(SOURCE.parent/row["source_ref"]).resolve()
    if not path.is_relative_to(SOURCE.parent.resolve()):
        raise ValueError('Source is outside the QASMBench selection.')
    return path

SEEDS=[0,1,2]
TERMINAL={"success","failure","timeout","interrupted","incompatible"}
THREAD_ENV={"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
            "NUMEXPR_NUM_THREADS":"1","GITHUB_ACTIONS":"true","PYTHONDONTWRITEBYTECODE":"1"}

def now():
    return datetime.now(timezone.utc).isoformat()

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()

def publish(path,value):
    'Publish atomically without overwriting existing data.'
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name("."+path.name+"."+uuid4().hex+".tmp")
    try:
        with temp.open("x",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
            f.write("\n");f.flush();os.fsync(f.fileno())
        os.link(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def publish_bytes(path,content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name("."+path.name+"."+uuid4().hex+".tmp")
    try:
        with temp.open("xb") as f:
            f.write(content);f.flush();os.fsync(f.fileno())
        os.link(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def external_path(value):
    path=Path(value).expanduser().resolve()
    if path.is_relative_to(REPO) or REPO.is_relative_to(path):
        raise ValueError('Output must be outside the project and cannot be its ancestor.')
    for parent in (path,*path.parents):
        if (parent/".git").exists() or ((parent/"prototipo").is_dir() and (parent/"archivio").is_dir()):
            raise ValueError('Do not save the oracle inside another repository.')
    return path

def preflight(workers=6):
    if sys.platform!="linux" or sys.version_info[:2]!=(3,12):
        raise ValueError('Run on Linux/WSL with Python 3.12.')
    if not 1<=workers<=6:raise ValueError('Between 1 and 6 external workers are allowed.')
    from qiskit import QuantumCircuit
    from scripts.mqt_predictor_protocol import target_payload
    from mqt.bench.targets import get_device
    if sha(CATALOG)!=CATALOG_SHA:raise ValueError('Frozen catalog changed.')
    catalog=read(CATALOG)
    versions={n:version(n) for n in ("qiskit","mqt.bench","numpy","mqt.predictor")}
    expected={**catalog["required_versions"],"mqt.predictor":"2.4.0"}
    if versions!=expected:raise ValueError(f'Versions differ from the catalog: {versions}; requested {expected}')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('QASMBench manifest changed.')
    manifest=read(SOURCE)
    rows=sorted(({**r,"num_qubits":r["qubits"]} for r in manifest["circuits"]),key=lambda r:r["circuit_id"])
    if len(rows)!=50 or len({r["circuit_id"] for r in rows})!=50:raise ValueError('Exactly 50 QASMBench circuits expected.')
    if any(r["split"]!="external_test" for r in rows):raise ValueError('Unexpected split.')
    if Counter(r["size_group"] for r in rows)!={"small":30,"medium":15,"large":5}:
        raise ValueError('QASMBench size groups differ from the fixed selection.')
    devices={}
    for name in catalog["supported_device_ids"]:
        target=get_device(name);fingerprint=digest(target_payload(target))
        if fingerprint!=catalog["target_sha256"][name]:raise ValueError('Target changed: '+name)
        devices[name]={"num_qubits":target.num_qubits,"sha256":fingerprint}
    for row in rows:
        if sha(source_path(row))!=row["source_sha256"]:raise ValueError('QASM changed: '+row["circuit_id"])
        if QuantumCircuit.from_qasm_file(str(source_path(row))).num_qubits!=row["num_qubits"]:
            raise ValueError('Inconsistent qubit count.')
    code=[HERE/"genera_oracle_test.py",HERE/"oracle_core.py",HERE/"oracle_worker.py",CATALOG,SOURCE,
          TEST_TOOLS/"score.py",KIT/"comune/scripts/__init__.py",KIT/"comune/scripts/mqt_predictor_protocol.py",
          KIT/"comune/settings.py",KIT/"configurazioni/esperimento.json",
          PROTO/"prototype/__init__.py",PROTO/"prototype/quantum_assistant/__init__.py",
          PROTO/"prototype/quantum_assistant/adapters/__init__.py",
          PROTO/"prototype/quantum_assistant/adapters/compilation.py",PROTO/"prototype/quantum_assistant/models.py"]
    return {"schema":"qasmbench50-oracle-max3-v1","split":"external_test","source_manifest_sha256":sha(SOURCE),
            "catalog_sha256":sha(CATALOG),"catalog":catalog,"source_revision":manifest["revision"],
            "versions":versions,"python":platform.python_version(),"circuits":rows,"devices":devices,
            "configurations":catalog["configurations"],"seeds":SEEDS,
            "workers":workers,"timeout_seconds":100,"startup_watchdog_seconds":60,"num_processes":1,
            "thread_environment":THREAD_ENV,
            "aggregation":"max successful seed score per pair; max over pairs; partial references flagged",
            "retry_policy":"no retry of success, error, timeout or interrupted jobs; resume only unstarted jobs",
            "code_sha256":{str(p.relative_to(REPO)):sha(p) for p in code},
            "isolation":"external directory; no system reader or automatic import"}


def jobs(identity):
    for row in identity["circuits"]:
        for device,target in identity["devices"].items():
            for config in identity["configurations"]:
                for seed in identity["seeds"]:
                    key={"circuit_id":row["circuit_id"],"source_sha256":row["source_sha256"],
                         "device":device,"target_sha256":target["sha256"],"config_id":config["config_id"],"seed":seed}
                    yield {**key,"job_id":digest(key),"split":"external_test","source":f"sorgenti/{row['circuit_id']}.qasm",
                           "compatible":row["num_qubits"]<=target["num_qubits"],"configuration":config,
                           "fixed_options":identity["catalog"]["fixed_transpile_options"],"timeout_seconds":identity["timeout_seconds"]}

def plan_counts(identity):
    js=list(jobs(identity))
    return {"circuits":len(identity["circuits"]),"devices":len(identity["devices"]),
            "configurations":len(identity["configurations"]),"seeds":identity["seeds"],
            "matrix_cells":len(js),"compilations":sum(j["compatible"] for j in js),
            "incompatible_cells":sum(not j["compatible"] for j in js),
            "compilations_by_device":{d:sum(j["compatible"] for j in js if j["device"]==d) for d in identity["devices"]}}

def prepare(out,identity):
    path=out/"contratto.json"
    if path.exists():
        old=read(path)
        if old["identity"]!=identity or old["identity_sha256"]!=digest(identity):
            raise ValueError('Incompatible resume: preserve this campaign and choose a new directory.')
    else:
        if any(p.name!=".lock" for p in out.iterdir()):raise ValueError('Directory is non-empty and has no contract.')
        publish(path,{"at":now(),"identity_sha256":digest(identity),"identity":identity,"plan":plan_counts(identity),
                      "host":platform.platform(),"cpu_count":os.cpu_count(),"memory_measurement":"not collected"})
    for row in identity["circuits"]:
        dest=out/"sorgenti"/(row["circuit_id"]+".qasm")
        if not dest.exists():publish_bytes(dest,source_path(row).read_bytes())
        if sha(dest)!=row["source_sha256"]:raise ValueError('Oracle QASM copy changed.')
    for rel,expected in identity["code_sha256"].items():
        dest=out/"provenienza"/rel
        if not dest.exists():publish_bytes(dest,(REPO/rel).read_bytes())
        if sha(dest)!=expected:raise ValueError('Invalid source copy.')
    return read(path)

def validate_result(job,result,folder=None):
    if result.get("job_id")!=job["job_id"] or result.get("status") not in TERMINAL:
        raise ValueError('Outcome has an invalid identity/status.')
    for key in ("circuit_id","source_sha256","target_sha256","seed","config_id","device","split"):
        if result.get(key)!=job[key]:raise ValueError('Invalid outcome identity: '+key)
    if not job["compatible"] and result["status"]!="incompatible":
        raise ValueError('Status is incompatible with Target capacity.')
    if result["status"]=="incompatible" and job["compatible"]:raise ValueError('Exclusion is incompatible with the plan.')
    if result["status"]=="success":
        score=result.get("score")
        if not job["compatible"] or isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError('Invalid score.')
        for key in ("source_sha256","target_sha256","seed","config_id","device"):
            if result.get(key)!=job[key]:raise ValueError('Invalid outcome provenance/configuration.')
        if not result.get("validation",{}).get("is_executable_on_target"):raise ValueError('Target was not validated.')
        if result.get("timings",{}).get("total",math.inf)>job["timeout_seconds"]:raise ValueError('Result exceeds the limit.')
        if folder is not None and sha(folder/"compiled.qasm")!=result["compiled_sha256"]:
            raise ValueError('Compiled circuit was modified.')
    elif result.get("score") is not None:raise ValueError('An unsuccessful outcome must have a null score.')
    return result

def terminal(job,status,reason,**extra):
    return {**{k:job[k] for k in ("job_id","circuit_id","source_sha256","device","target_sha256","config_id","seed")},
            "split":"external_test","status":status,"score":None,"at":now(),"reason":reason,**extra}

def resolve_existing(folder,job):
    result_path=folder/"esito.json"
    if result_path.exists():
        result=validate_result(job,read(result_path),folder)
        if (folder/"inizio.json").exists() and read(folder/"inizio.json")["job"]!=job:
            raise ValueError('Attempt plan changed.')
        return result
    if not (folder/"inizio.json").exists():return None
    if read(folder/"inizio.json")["job"]!=job:raise ValueError('Interrupted attempt has a different plan.')
    if (folder/"worker_result.json").exists():
        result={**validate_result(job,read(folder/"worker_result.json"),folder),"recovered_persisted_result":True}
    else:
        result=terminal(job,"interrupted",'Previous interruption; no automatic retry.')
    publish(result_path,result)
    return result

def aggregate_rows(identity,records):
    'A missing/failed cell never becomes a zero score.'
    all_jobs=list(jobs(identity))
    if set(records)-{j["job_id"] for j in all_jobs}:raise ValueError('Outcomes do not belong to the plan.')
    grouped={}
    for job in all_jobs:
        r=records.get(job["job_id"])
        if r is not None:validate_result(job,r)
        grouped.setdefault((job["circuit_id"],job["device"],job["config_id"]),[]).append((job,r))
    pairs=[]
    for (cid,device,config),items in grouped.items():
        success=[(j,r) for j,r in items if r is not None and r["status"]=="success"]
        maximum=max((r["score"] for _,r in success),default=None)
        pairs.append({"circuit_id":cid,"device":device,"config_id":config,"compatible":items[0][0]["compatible"],
                      "seed_scores":{str(j["seed"]):r["score"] if r else None for j,r in items},
                      "seed_statuses":{str(j["seed"]):r["status"] if r else "pending" for j,r in items},
                      "successful_seeds":[j["seed"] for j,r in success],"max_score":maximum,
                      "best_seeds":[j["seed"] for j,r in success if r["score"]==maximum],
                      "all_three_successful":len(success)==3,"all_terminal":all(r is not None for _,r in items)})
    refs=[]
    for c in identity["circuits"]:
        ps=[p for p in pairs if p["circuit_id"]==c["circuit_id"] and p["compatible"]]
        valid=[p for p in ps if p["max_score"] is not None]
        best=max((p["max_score"] for p in valid),default=None)
        seed0=max((p["seed_scores"]["0"] for p in ps if p["seed_statuses"]["0"]=="success"),default=None)
        refs.append({"circuit_id":c["circuit_id"],"source_sha256":c["source_sha256"],"split":"external_test",
            "reference_score":best,"criterion":"max over successful seeds 0,1,2, then max over device/config",
            "best_pairs":[{"device":p["device"],"config_id":p["config_id"],"best_seeds":p["best_seeds"]} for p in valid if p["max_score"]==best],
            "reference_is_exhaustive":bool(ps) and all(p["all_three_successful"] for p in ps),
            "all_attempts_terminal":all(p["all_terminal"] for p in ps),"compatible_pairs":len(ps),
            "pairs_with_any_success":len(valid),"pairs_with_three_successes":sum(p["all_three_successful"] for p in ps),
            "best_seed0_score":seed0,"seed0_reference_is_exhaustive":bool(ps) and all(p["seed_statuses"]["0"]=="success" for p in ps)})
    return pairs,refs

def analyze(out,identity):
    records={};hashes={}
    for job in jobs(identity):
        p=out/"tentativi"/job["job_id"]/"esito.json"
        if p.exists():
            records[job["job_id"]]=validate_result(job,read(p),p.parent)
            hashes[str(p.relative_to(out))]=sha(p)
    pairs,refs=aggregate_rows(identity,records)
    summary={"at":now(),"identity_sha256":digest(identity),"analysis_code_sha256":sha(Path(__file__)),"plan":plan_counts(identity),
             "terminal":len(records),"pending":len(list(jobs(identity)))-len(records),
             "statuses":dict(Counter(r["status"] for r in records.values())),
             "circuits_with_reference":sum(r["reference_score"] is not None for r in refs),
             "circuits_with_exhaustive_reference":sum(r["reference_is_exhaustive"] for r in refs),
             "complete":len(records)==len(list(jobs(identity))),
             "label":"maximum observed score; errors/timeouts/interrupted are missing, not zero",
             "comparison_note":"signed gap = reference_score - system_score; do not clip negative values. MQT uses RL outside this finite Qiskit grid."}
    dest=out/"analisi"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True)
    for name,value in [("riepilogo",summary),("oracle_test",refs),("configurazioni",pairs),("provenienza",hashes)]:
        publish(dest/(name+".json"),value)
    with (dest/"oracle_test.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["circuit_id","reference_score","reference_is_exhaustive","compatible_pairs",
             "pairs_with_any_success","pairs_with_three_successes","best_seed0_score"],extrasaction="ignore")
        w.writeheader();w.writerows(refs)
    with (dest/"tentativi.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["circuit_id","device","config_id","seed","compatible","status","score","job_id"])
        for j in jobs(identity):
            r=records.get(j["job_id"])
            w.writerow([j["circuit_id"],j["device"],j["config_id"],j["seed"],j["compatible"],
                        r["status"] if r else "pending",r["score"] if r else None,j["job_id"]])
    return dest,summary

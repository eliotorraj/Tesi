"""Controlli v2 comuni e requisiti distinti per metodo; nessuna apertura v1."""
from __future__ import annotations
import sys
from pathlib import Path
from common import *
sys.path.insert(0, str(ROOT))
from importlib.metadata import version
from collections import Counter

def verify_files(root, values):
    for name, expected in values.items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Riferimento non valido: " + name)
        if sha(root / name) != expected:
            raise ValueError("Impronta cambiata: " + name)
    return len(values)

def selection_v2():
    final = read(STUDY / "final_configuration.json")
    proof = read(STUDY / "selection_complete.json")
    study = read(STUDY / "frozen_study.json")
    seals = read(STUDY / "all_decisions_sealed.json")
    if final.get("study_id") != "local-llm-v2" or final.get("winner") != "qwen/p0_t0":
        raise ValueError("Serve la selezione ufficiale local-llm-v2 qwen/p0_t0.")
    if proof.get("study_id") != final["study_id"] or proof.get("winner") != final["winner"]:
        raise ValueError("Prova di selezione incoerente.")
    if final["study_sha256"] != digest(study) or seals["study_sha256"] != digest(study):
        raise ValueError("Sigillo dello studio non valido.")
    if final["selection_sha256"] != digest(read(STUDY / "analysis/selection.json")):
        raise ValueError("Selezione analitica cambiata.")
    n = verify_files(ARCHIVE, proof["files"])
    for field in ("input_hashes", "evaluation_input_hashes", "code_hashes"):
        n += verify_files(ARCHIVE, study[field])
    for model, expected in seals["models"].items():
        seal = read(STUDY / model / "sealed.json")
        if digest(seal) != expected or seal["study_sha256"] != digest(study):
            raise ValueError("Sigillo modello non valido: " + model)
        n += verify_files(ARCHIVE, seal["files"])
        n += verify_files(ARCHIVE, study["models"][model]["technical_evidence_hashes"])
    current = read(ROOT / "config.json")
    for field in ("study_id", "winner", "configuration", "fixed", "policy", "study_sha256", "selection_sha256"):
        if current[field] != final[field]:
            raise ValueError("Configurazione prototipo diversa dalla selezione: " + field)
    if current["source_sha256"] != sha(STUDY / "final_configuration.json"):
        raise ValueError("Provenienza della configurazione cambiata.")
    for field in ("context", "cache_type", "gpu_layers", "batch", "micro_batch", "weight_precision", "artifact"):
        if current["profile"][field] != final["profile"][field]:
            raise ValueError("Profilo diverso dalla selezione: " + field)
    return {"study_id": final["study_id"], "winner": final["winner"], "verified_files": n,
            "final_sha256": sha(STUDY / "final_configuration.json")}

def corpus():
    manifest=read(SOURCE)
    if sha(SOURCE)!=read(PLAN)["manifest_sha256"]:
        raise ValueError("Manifest QASMBench cambiato.")
    rows=manifest["circuits"]
    if len(rows)!=50 or Counter(r["size_group"] for r in rows)!={"small":30,"medium":15,"large":5}:
        raise ValueError("Richiesti 30 piccoli, 15 medi, 5 grandi.")
    if len({r["circuit_id"] for r in rows})!=50 or len({r["source_sha256"] for r in rows})!=50:
        raise ValueError("Identita o contenuti duplicati.")
    original=read(EXPERIMENT/"manifests/source_circuits_v2.json")
    previous={r["source_sha256"] for r in original["circuits"]}
    for row in rows:
        if row["split"]!="external_test" or sha(source_path(row))!=row["source_sha256"]:
            raise ValueError("Sorgente o partizione cambiati: "+row["circuit_id"])
        if row["source_sha256"] in previous:
            raise ValueError("Sovrapposizione byte-identica col corpus MQT.")
    verify_files(AREA/"circuiti",manifest["support_files"])
    return {"source_sha256":sha(SOURCE),"counts":manifest["counts"],"revision":manifest["revision"]}

def software_targets():
    from qiskit_dataset.catalog import load_catalog
    from scripts.mqt_predictor_protocol import target_payload, FROZEN_TARGET_SHA256
    from mqt.bench.targets import get_device
    if sys.version_info[:2] != (3,12):
        raise ValueError("Richiesto Python 3.12.")
    versions = {n:version(n) for n in ("qiskit","mqt.bench","numpy","networkx","qdrant-client","portalocker")}
    expected = dict(line.strip().split("==") for line in (ROOT/"requirements.txt").read_text().splitlines() if "==" in line)
    if any(versions[n] != expected[n] for n in versions):
        raise ValueError("Versioni non conformi: " + str(versions))
    catalog = load_catalog()
    for device in catalog.supported_device_ids:
        if digest(target_payload(get_device(device))) != FROZEN_TARGET_SHA256[device]:
            raise ValueError("Target cambiato: " + device)
    return {"versions":versions,"targets":FROZEN_TARGET_SHA256}

def rag_integrity():
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    value = load_corpus(verify_features=True)
    return {"records":len(value.records),"files":verify_files(ROOT, read(ROOT/"data/seal.json")["files"])}

def preflight(method):
    checks = {}
    tasks=[("corpus",corpus),("software_targets",software_targets)]
    if method=="llm_rag": tasks += [("local_llm_v2",selection_v2),("rag_train_integrity",rag_integrity)]
    for name, fn in tasks:
        print("Verifica: "+name, flush=True)
        try:
            checks[name] = {"ok":True,"details":fn()}
        except Exception as exc:
            checks[name] = {"ok":False,"error":type(exc).__name__+": "+str(exc)}
    if method == "mqt_predictor":
        import subprocess
        process = subprocess.run([sys.executable, str(AREA/"strumenti/mqt_gate.py")],
                                 text=True, capture_output=True)
        try:
            detail = __import__("json").loads(process.stdout)
        except ValueError:
            detail = {"stdout":process.stdout[-2000:],"stderr":process.stderr[-2000:]}
        checks["mqt_models"] = {"ok":process.returncode==0,"details":detail}
    plan = read(PLAN)
    checks["method_plan"] = {"ok":plan["methods"]==list(METHODS) and plan["circuits"]==50
                             and plan["study_id"]=="local-llm-v2"\
                             and plan["qiskit_seed"]==0 and plan["compilations_per_circuit"]==1\
                             and plan["llm_profile"]=="desktop" and plan["response_contract"]=="4.0.0"\
                             and plan["llm_max_completed_attempts"]==3 and plan["transport_retries"]==0\
                             and type(plan["mqt_sampling_seed"]) is int}
    return {"method":method,"at":now(),"ready":all(c["ok"] for c in checks.values()),"checks":checks}

def frozen_contract():
    return {"plan":read(PLAN),"source_sha256":sha(SOURCE),"selection":selection_v2(),
            "code":code_files(),"rag_seal_sha256":sha(ROOT/"data/seal.json")}

def freeze():
    path = AREA/"preparazione/contratto_congelato.json"
    contract = frozen_contract()
    if path.exists():
        if read(path) != contract:
            raise ValueError("Contratto cambiato dopo il congelamento: non mescolare esecuzioni.")
    else:
        save(path, contract)
    return sha(path)

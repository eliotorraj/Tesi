'Generate train/validation matrices and the RAG Dataset using the original functions.'
from pathlib import Path
import json, shutil
import settings as s
from processi import execute

def task(row,device,configuration,seed,catalog,manifest):
    from scripts.mqt_predictor_protocol import installed_package_versions
    identity={"circuit":row["source_sha256"],"split":row["split"],"id":row["circuit_id"],"device":device,
              "config":configuration.config_id,"seed":seed,"catalog":catalog.catalog_id}
    return {"experiment_id":s.EXPERIMENT_ID,"protocol_version":"2.0.0","run_id":"run_"+s.digest(identity),
            "dataset_scope":"full","split":row["split"],"objective":dict(catalog.objective),"circuit":row,
            "target_record":manifest["targets"][device],"configuration":configuration.to_dict(),
            "catalog_id":catalog.catalog_id,"seed_transpiler":seed,"versions":installed_package_versions(),
            "fixed_transpile_options":dict(catalog.fixed_transpile_options),"execution_policy":dict(catalog.execution_policy),
            "device_id":device,"source_path":str(s.WORK/row["source_ref"]),
            "timeout_seconds":catalog.execution_policy["timeout_seconds"],"resume_contract_sha256":s.sha(s.WORK/"contratto.json")}

def generate(splits=("train","validation")):
    from qiskit_dataset.catalog import load_catalog
    from concurrent.futures import ThreadPoolExecutor
    manifest=s.require_prepared();catalog=load_catalog()
    if set(splits)-{"train","validation"}:raise ValueError('Dataset generation does not read Test')
    import portalocker
    s.DATASET.mkdir(parents=True,exist_ok=True)
    with portalocker.Lock(str(s.DATASET/".lock"),timeout=0):
        jobs=[]
        for row in manifest["circuits"]:
            if row["split"] not in splits:continue
            for device in catalog.supported_device_ids:
                if row["num_qubits"]>manifest["targets"][device]["num_qubits"]:continue
                for config in catalog.configurations:
                    for seed in catalog.seeds:
                        t=task(row,device,config,seed,catalog,manifest)
                        jobs.append((s.DATASET/"tentativi"/t["run_id"],{"kind":"qiskit","task":t}))
        def one(item):return execute(*item,timeout=float(catalog.execution_policy["timeout_seconds"])+30)
        with ThreadPoolExecutor(max_workers=catalog.execution_policy["workers"]) as pool:
            for i,result in enumerate(pool.map(one,jobs),1):
                if i%25==0 or i==len(jobs):print(f"Dataset: {i}/{len(jobs)}",flush=True)
    return aggregate()

def aggregate():
    from qiskit_dataset.catalog import load_catalog
    from qiskit_dataset.views import aggregate_runs,build_rag_examples
    from qiskit_dataset.generation import _base_record
    from prototype.quantum_assistant.adapters.rag_features import FeatureTransform
    from prototype.quantum_assistant.adapters.rag_dataset import record_features
    manifest=s.require_prepared();catalog=load_catalog();summaries=[];missing=[]
    for device in catalog.supported_device_ids:
        rows=[r for r in manifest["circuits"] if r["split"] in ("train","validation") and r["num_qubits"]<=manifest["targets"][device]["num_qubits"]]
        runs=[]
        for row in rows:
            for config in catalog.configurations:
                for seed in catalog.seeds:
                    t=task(row,device,config,seed,catalog,manifest);p=s.DATASET/"tentativi"/t["run_id"]/"result.json"
                    if not p.exists():missing.append(t["run_id"]);continue
                    value=s.read(p)
                    if "run_id" not in value:
                        base=_base_record(t);base.update(status="timeout" if value["status"]=="timeout" else "failure",failure={"category":value["status"],"message":value.get("error",value["status"])})
                        base["timings_seconds"]["total"]=value.get("process_seconds");value=base
                    runs.append(value)
        m={"catalog_id":catalog.catalog_id,"seeds":list(catalog.seeds),"objective":dict(catalog.objective),"circuits":rows,"dataset_scope":"full"}
        summaries.extend(aggregate_runs(m,runs,catalog,manifest["targets"][device]))
    if missing:return {"status":"incomplete","missing_attempts":len(missing),"message":'Complete train and validation before sealing the Dataset'}
    s.same_or_save(s.DATASET/"aggregati.json",summaries)
    examples=build_rag_examples(summaries,device_order=catalog.supported_device_ids)
    if not examples:raise ValueError('No eligible RAG examples')
    data=s.WORK/"data";data.mkdir(parents=True,exist_ok=True)
    text="".join(json.dumps(x,ensure_ascii=False,allow_nan=False)+"\n" for x in examples)
    destination=data/"rag_examples.jsonl"
    if destination.exists() and destination.read_text()!=text:raise ValueError('A different Dataset is already sealed')
    if not destination.exists():destination.write_text(text,encoding="utf-8")
    train=[r for r in manifest["circuits"] if r["split"]=="train"]
    s.same_or_save(data/"train_manifest.json",{"experiment_id":s.EXPERIMENT_ID,"circuits":train})
    for row in train:
        target=data/row["source_ref"];target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if s.sha(target)!=row["source_sha256"]:raise ValueError('Train copy changed')
        else:shutil.copy2(s.WORK/row["source_ref"],target)
    transform=FeatureTransform.fit_train(record_features(x) for x in examples)
    s.same_or_save(data/"transform.json",transform.artifact(source_sha256=s.sha(destination),experiment_id=s.EXPERIMENT_ID))
    files={str(p.relative_to(s.WORK)):s.sha(p) for p in sorted(data.rglob('*')) if p.is_file() and p.name!='seal.json'}
    files["catalogo.json"]=s.sha(s.CATALOG_PATH)
    s.same_or_save(data/"seal.json",{"record_count":len(examples),"files":files})
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    corpus=load_corpus(verify_features=True)
    return {"status":"complete","rag_examples":len(corpus.records),"aggregates":len(summaries),"dataset":str(s.DATASET)}

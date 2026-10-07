'Executable record of the initial derivation; rejects existing tools.'
import hashlib,json
from pathlib import Path
AREA=Path(__file__).resolve().parents[1]
SOURCE=AREA.parent/"test/strumenti"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,text):
    path=AREA/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as out: out.write(text)
def change(text,old,new):
    if old not in text: raise ValueError('Unexpected source: '+old[:100])
    return text.replace(old,new)
sources={}
for name in ("common.py","runner.py","gates.py","mqt_gate.py","score.py","worker.py"):
    path=SOURCE/name
    text=path.read_text()
    sources[str(path.relative_to(AREA.parents[2]))]=sha(path)
    if name=="common.py":
        text=change(text,'SOURCE = EXPERIMENT / "manifests/source_circuits_v2.json"','SOURCE = AREA / "manifest.json"')
        text=change(text,'METHODS = ("llm_rag", "llm_senza_rag", "mqt_predictor", "random")','METHODS = ("llm_rag", "mqt_predictor")')
        text=change(text,'contained(ARCHIVE / "archivio/protocollo_v1", record["source_ref"])','contained(AREA / "circuiti", record["source_ref"])')
        text=text[:text.index("def code_files():")]+'''def code_files():
    paths=[ROOT/"config.json",ROOT/"requirements.txt",ROOT/"app.py",ROOT/"portable_features.py",
           ROOT/"docs/protocollo_sperimentale.md",PLAN,SOURCE,ARCHIVE/"uv.lock"]
    for folder in ("prototype","qiskit_dataset","scripts","schemas","runtime/toon"):
        paths += [p for p in (ROOT/folder).rglob("*") if p.suffix in (".py",".json",".js",".mjs")]
    paths += list(AREA.glob("*.py"))+list((AREA/"strumenti").glob("*.py"))
    for folder in (ARCHIVE/"scripts",EVALUATION/"addestramento/mqt"):
        paths += list(folder.glob("*.py"))
    return {p.relative_to(REPO).as_posix():sha(p) for p in sorted(set(paths)) if p.is_file()}
'''
    elif name=="runner.py":
        text=text.replace('"test"','"external_test"')
        text=change(text,'Run/resume the 90 Test circuits','Run/resume the 50 QASMBench circuits')
        text=change(text,'else 90,','else 50,')
        text=change(text,"""from report import generate
        output=generate(base)
        print(\"Results and report: \"+str(output))""",
                    'print("Results: "+str(base)+". Separate analysis: analizza.py")')
        text=change(text,'"method":method,\n              "retries"', '"method":method,"size_group":row.get("size_group"),\n              "retries"')
    elif name=="gates.py":
        start=text.index('def corpus():')
        end=text.index('def software_targets():')
        corpus="""def corpus():
    manifest=read(SOURCE)
    if sha(SOURCE)!=read(PLAN)[\"manifest_sha256\"]:
        raise ValueError(\"QASMBench manifest changed.\")
    rows=manifest[\"circuits\"]
    if len(rows)!=50 or Counter(r[\"size_group\"] for r in rows)!={\"small\":30,\"medium\":15,\"large\":5}:
        raise ValueError(\"30 small, 15 medium and 5 large circuits are required.\")
    if len({r[\"circuit_id\"] for r in rows})!=50 or len({r[\"source_sha256\"] for r in rows})!=50:
        raise ValueError(\"Duplicate identities or contents.\")
    original=read(EXPERIMENT/\"manifests/source_circuits_v2.json\")
    previous={r[\"source_sha256\"] for r in original[\"circuits\"]}
    for row in rows:
        if row[\"split\"]!=\"external_test\" or sha(source_path(row))!=row[\"source_sha256\"]:
            raise ValueError(\"Source or split changed: \"+row[\"circuit_id\"])
        if row[\"source_sha256\"] in previous:
            raise ValueError(\"Byte-identical overlap with the MQT corpus.\")
    verify_files(AREA/\"circuiti\",manifest[\"support_files\"])
    return {\"source_sha256\":sha(SOURCE),\"counts\":manifest[\"counts\"],\"revision\":manifest[\"revision\"]}

"""
        text=text[:start]+corpus+text[end:]
        text=change(text,'plan["circuits"]==90','plan["circuits"]==50')
        # Separate requirements: ML/RL only for MQT, LLM/RAG selection only for LLM methods.
        text=change(text,'for name, fn in (("local_llm_v2",selection_v2),("corpus",corpus),("software_targets",software_targets),\n                     ("rag_train_integrity",rag_integrity)):',
           'tasks=[("corpus",corpus),("software_targets",software_targets)]\n    if method=="llm_rag": tasks += [("local_llm_v2",selection_v2),("rag_train_integrity",rag_integrity)]\n    for name, fn in tasks:')
    elif name=="worker.py":
        text=change(text,'device = job.get("rl_device") or predict_device_for_figure_of_merit(circuit, figure_of_merit="expected_fidelity")\n            device = device.description if hasattr(device, "description") else str(device)',
           'selected = get_device(job["rl_device"]) if job.get("rl_device") else predict_device_for_figure_of_merit(circuit, figure_of_merit="expected_fidelity")\n            device = selected.description')
        text=change(text,'rl_compile(circuit, device=device,','rl_compile(circuit, device=selected,')
    put("strumenti/"+name,text)
for method in ("llm_rag","mqt_predictor"):
    put(method+".py",f'"""Independent QASMBench launch: {method}."""\nimport sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))\nfrom runner import cli\nif __name__=="__main__": raise SystemExit(cli("{method}"))\n')
plan=json.loads((AREA.parent/"test/piano.json").read_text())
plan.update(test_id="qasmbench-independent-v1",methods=["llm_rag","mqt_predictor"],
    split="external_test",circuits=50,manifest_sha256=sha(AREA/"manifest.json"),
    group_counts={"small":30,"medium":15,"large":5},
    independence="External source, static purposive selection; no byte-identical MQT corpus overlap; semantic/pretraining overlap not excluded.")
plan["analysis"]["comparisons"]=["llm_rag vs mqt_predictor"]
for key in ("no_rag_policy","frontier_model"): plan.pop(key,None)
put("piano.json",json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
put("provenienza_codice.json",json.dumps(sources,indent=2)+"\n")
put(".gitignore","__pycache__/\nrisultati/\npreparazione/\nprove_tecniche/\nreport/generati/\n")
# Preserve the four excluded candidates outside the manifest's fifty circuits.
selected={r["source_ref"] for r in json.loads((AREA/"manifest.json").read_text())["circuits"]}
for path in (AREA/"circuiti").rglob("*.qasm"):
    rel=path.relative_to(AREA/"circuiti")
    if rel.as_posix() not in selected:
        target=(AREA/"verifiche/esclusi"/rel).resolve()
        if not target.is_relative_to(AREA.resolve()): raise ValueError('External path')
        target.parent.mkdir(parents=True,exist_ok=True)
        path.rename(target)
print('Independent tools prepared.')

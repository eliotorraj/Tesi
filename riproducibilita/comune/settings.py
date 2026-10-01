"""Percorsi di una nuova esecuzione, indipendenti dall'archivio e dal prototipo."""
from pathlib import Path
import os, json, re, hashlib
KIT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get("RIPRO_CONFIG", KIT/"configurazioni/esperimento.json")).resolve()
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
EXPERIMENT_ID = CONFIG["experiment_id"]
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", EXPERIMENT_ID):
    raise ValueError("experiment_id non valido")
def input_path(value):
    p=Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (KIT/p).resolve()
OUTPUT = input_path(os.environ.get("RIPRO_OUTPUT", CONFIG.get("output", ".")))
WORK = OUTPUT/"esecuzioni"/EXPERIMENT_ID
DATASET = OUTPUT/"dataset/artefatti"/EXPERIMENT_ID
MQT = OUTPUT/"mqt/artefatti"/EXPERIMENT_ID
VALIDATION = OUTPUT/"validation/risultati"/EXPERIMENT_ID
TEST = OUTPUT/"test/risultati"/EXPERIMENT_ID
CORPUS = input_path(CONFIG["corpus"])
CATALOG_TEMPLATE = input_path(CONFIG["catalog"])
CATALOG_PATH = WORK/"catalogo.json"
SCHEMAS = KIT/"dataset/schemi"
REGISTRY_PATH = input_path(CONFIG["model_registry"])
def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def save(path,value):
    from uuid import uuid4
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.pending-'+uuid4().hex)
    with temporary.open("x",encoding="utf-8") as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n");f.flush();os.fsync(f.fileno())
    # Pubblicazione atomica e senza sovrascrittura. Un'interruzione lascia la copia pending.
    try:os.link(temporary,path)
    except BaseException:raise
    else:temporary.unlink()
def same_or_save(path,value):
    path=Path(path)
    if path.exists():
        if read(path)!=value:raise ValueError("Contenuto diverso: "+str(path)+"; usare un nuovo experiment_id")
    else:save(path,value)
def model_registry():
    values=[m for m in read(REGISTRY_PATH)["models"] if m.get("enabled",True)]
    ids=[m["id"] for m in values]
    if not values or len(ids)!=len(set(ids)):raise ValueError("Elenco modelli vuoto o ID duplicati")
    for m in values:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*",m["id"]):raise ValueError("ID modello non valido")
        p=Path(m["file"]).expanduser()
        m["path"]=str(p.resolve() if p.is_absolute() else (REGISTRY_PATH.parent/p).resolve())
    return {m["id"]:m for m in values}
def code_identity():
    excluded={"artefatti","risultati","esecuzioni","node_modules","__pycache__",".venv","modelli_llm","circuiti","esportazioni"}
    result={}
    for folder,dirs,files in os.walk(KIT):
        dirs[:]=sorted(d for d in dirs if d not in excluded and (Path(folder)/d) != KIT/"configurazioni/esperimenti")
        for name in sorted(files):
            p=Path(folder)/name
            if p.suffix in (".py",".mjs",".json",".lock",".toml",".sh"):
                result[str(p.relative_to(KIT))]=sha(p)
    return result
def require_prepared():
    m=read(WORK/"manifest.json")
    expected={"config":CONFIG,"catalog_sha256":sha(CATALOG_TEMPLATE),"code":code_identity()}
    if read(WORK/"contratto.json")!=expected:raise ValueError("Codice o configurazione cambiati: usare un nuovo experiment_id")
    for name,expected_hash in read(WORK/"ingressi_sigillati.json").items():
        if sha(WORK/name)!=expected_hash:raise ValueError("Ingresso congelato modificato: "+name)
    for row in m["circuits"]:
        p=WORK/row["source_ref"]
        if sha(p)!=row["source_sha256"]:raise ValueError("Circuito congelato modificato: "+str(p))
    return m

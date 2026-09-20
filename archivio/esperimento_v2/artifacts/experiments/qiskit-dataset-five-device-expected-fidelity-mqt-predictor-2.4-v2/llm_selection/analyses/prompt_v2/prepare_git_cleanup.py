"""Prepara due commit di rimozione in un indice isolato; non esegue push."""
from pathlib import Path
import json, os, subprocess
ROOT=Path.cwd().resolve()
DEST=Path(__file__).resolve().parent
def git(*args, env=None, data=None):
    return subprocess.check_output(["git",*args],cwd=ROOT,env=env,input=data,text=True).strip()
audited=json.loads((DEST/"remote_models_before.json").read_text())
remote=dict(line.split()[::-1] for line in git("ls-remote","--heads","origin").splitlines())
before_status=git("status","--porcelain=v1")
prepared=[]
objects={}
for row in audited:
    models=[m for m in row["models"] if m["path"].startswith(("artifacts/models/rl/","artifacts/checkpoints/rl/")) and m["path"].endswith(".zip")]
    if not models:
        continue
    ref=row["ref"]
    if remote.get(ref)!=row["sha"]:
        raise ValueError("Remote branch changed since inventory: "+ref)
    assert ref in ("refs/heads/main","refs/heads/mqt-predictor-2.4.0")
    paths=[m["path"] for m in models]
    assert all("\n" not in p for p in paths)
    env=dict(os.environ,GIT_INDEX_FILE=str(DEST/(ref.rsplit("/",1)[1]+".isolated.index")))
    if Path(env["GIT_INDEX_FILE"]).exists():
        raise ValueError("Isolated index already exists")
    git("read-tree",row["sha"],env=env)
    git("update-index","--force-remove","--stdin",env=env,data="\n".join(paths)+"\n")
    try:
        old_ignore=git("show",row["sha"]+":.gitignore")
    except subprocess.CalledProcessError:
        old_ignore=""
    rules=["/artifacts/models/rl/*.zip","/artifacts/checkpoints/rl/**/*.zip"]
    ignore=old_ignore+"\n\n# Vecchi pesi RL conservati fuori da Git; copie locali preservate.\n"
    ignore+="\n".join(rule for rule in rules if rule not in old_ignore.splitlines())+"\n"
    blob=git("hash-object","-w","--stdin",data=ignore)
    git("update-index","--add","--cacheinfo","100644",blob,".gitignore",env=env)
    tree=git("write-tree",env=env)
    changes=git("diff","--name-status",row["sha"],tree)
    changed={line.split("\t",1)[1]:line.split("\t",1)[0] for line in changes.splitlines()}
    assert set(changed)==set(paths)|{".gitignore"}
    assert all(changed[p]=="D" for p in paths)
    body=DEST/(ref.rsplit("/",1)[1]+".commit-message.txt")
    body.write_text("Rimuovi vecchi modelli RL e checkpoint da Git\n\n"
                    "Rimuove soltanto gli archivi ZIP storici sotto artifacts/models/rl e "
                    "artifacts/checkpoints/rl. Le copie locali e gli artefatti dell'esperimento corrente "
                    "rimangono invariati. Aggiunge le esclusioni per evitare nuovi caricamenti.\n\n"
                    "Gli oggetti LFS conservati nella cronologia richiedono una pulizia separata dello storage GitHub.\n")
    commit=git("commit-tree",tree,"-p",row["sha"],"-F",str(body))
    backup="refs/codex/legacy-rl-before-20260915/"+ref.rsplit("/",1)[1]
    git("update-ref",backup,row["sha"])
    (DEST/(ref.rsplit("/",1)[1]+".cleanup.diff")).write_text(changes+"\n")
    for model in models:
        objects[model["oid"]]=model["bytes"]
    prepared.append({"ref":ref,"before":row["sha"],"after":commit,"tree":tree,"backup_ref":backup,
                     "removed_paths":paths,"pointer_bytes_sum":sum(m["bytes"] for m in models)})
assert git("status","--porcelain=v1")==before_status
result={"prepared":prepared,"unique_lfs_objects":len(objects),"unique_lfs_bytes":sum(objects.values()),
        "working_tree_and_index_unchanged":True,"pushed":False}
with (DEST/"git_cleanup_prepared.json").open("x") as f: json.dump(result,f,indent=2)
print(json.dumps({**result,"prepared":[{k:v for k,v in p.items() if k!="removed_paths"}|{"removed_files":len(p["removed_paths"])} for p in prepared]},indent=2))

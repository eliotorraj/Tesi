from pathlib import Path
import json, subprocess
base=Path(__file__).resolve().parents[2]
p=json.loads((base/"prompts/train/dj_indep_tket_2.json").read_text())["prompt"]
e=p["retrieved_labeled_examples"][0]["example"]
print("example keys", list(e))
for k in ("input", "provenance"):
 print(k,json.dumps(e.get(k),ensure_ascii=False)[:5000])
print("label",json.dumps(e["label"],ensure_ascii=False)[:2500])
print("models")
heads=subprocess.check_output(["git","ls-remote","--heads","origin"],text=True)
rows=[]
for line in heads.splitlines():
 sha,ref=line.split()
 tree=subprocess.check_output(["git","ls-tree","-r",sha],text=True)
 candidates=[row.split("\t",1)[1] for row in tree.splitlines() if any(s in row for s in ("/models/","/checkpoints/rl/"))]
 pointers=[]
 for path in candidates:
  content=subprocess.check_output(["git","show",sha+":"+path])
  if content.startswith(b"version https://git-lfs.github.com/spec/v1"):
   fields=dict(row.split(" ",1) for row in content.decode().splitlines())
   pointers.append({"path":path,"oid":fields["oid"],"bytes":int(fields["size"])})
 rows.append({"ref":ref,"sha":sha,"models":pointers})
 print(ref,"pointers",len(pointers),"bytes",sum(p["bytes"] for p in pointers))
with (Path(__file__).parent/"remote_models_before.json").open("x") as f: json.dump(rows,f,indent=2)

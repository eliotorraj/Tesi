"""Conteggio preliminare dei prompt con i tokenizer ufficiali, senza tagli."""
import json
from tokenizers import Tokenizer
from .common import OUTPUT, now, write_json

def main():
    results=[]
    import sys
    from pathlib import Path
    model_root=Path(sys.argv[1]) if len(sys.argv)>1 else OUTPUT/"models"
    for model in sorted(model_root.iterdir()):
        source=model/"official_tokenizer.json"
        if not source.exists():
            continue
        tokenizer=Tokenizer.from_file(str(source))
        rows=[]
        for path in sorted((OUTPUT/"prompts").glob("*/*.json")):
            data=json.loads(path.read_text())
            content=json.dumps(data["prompt"],ensure_ascii=False,separators=(",",":"))
            rows.append({"split":path.parent.name,"circuit_id":path.stem,"tokens":len(tokenizer.encode(content,add_special_tokens=False).ids),"characters":len(content)})
        results.append({"model":model.name,"rows":rows})
        print(model.name, len(rows), max((r["tokens"] for r in rows),default=0),flush=True)
    write_json(OUTPUT/"preparation"/"preliminary_token_counts.json",{"created_at":now(),"method":"official tokenizer on compact JSON; chat template overhead excluded; no inference","models":results})
if __name__=="__main__": main()

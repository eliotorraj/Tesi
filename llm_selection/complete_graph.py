"""Prova esplorativa dei grafi; codifica comune in prototype.prompting."""
import json
from prototype.prompting.complete_graph import NOTE, decode, encode

def main():
    from tokenizers import Tokenizer
    from .common import OUTPUT, read_json, write_json, now
    rows=[]
    for model in ("qwen","phi","gemma"):
        tokenizer=Tokenizer.from_file(str(OUTPUT/"models"/model/"official_tokenizer.json"))
        for split in ("train","validation"):
            for path in sorted((OUTPUT/"prompts"/split).glob("*.json")):
                prompt=read_json(path)["prompt"]
                converted=encode(prompt)
                text=NOTE+"\n\n"+json.dumps(converted,ensure_ascii=False,separators=(",",":"))
                rows.append({"model":model,"split":split,"circuit_id":path.stem,"exact_roundtrip":True,
                             "graph_tokens":len(tokenizer.encode(text,add_special_tokens=False).ids)})
        del tokenizer
    target=OUTPUT/"preparation"/"complete_graph_token_probe.json"
    if target.exists(): raise ValueError("Probe already saved")
    write_json(target,{"at":now(),"measurement":"official tokenizer, excludes native chat wrapper","rows":rows})
    for model in ("qwen","phi","gemma"):
        for split in ("train","validation"):
            selected=[r["graph_tokens"] for r in rows if r["model"]==model and r["split"]==split]
            print(model,split,"count",len(selected),"min",min(selected),"max",max(selected),flush=True)
if __name__=="__main__": main()

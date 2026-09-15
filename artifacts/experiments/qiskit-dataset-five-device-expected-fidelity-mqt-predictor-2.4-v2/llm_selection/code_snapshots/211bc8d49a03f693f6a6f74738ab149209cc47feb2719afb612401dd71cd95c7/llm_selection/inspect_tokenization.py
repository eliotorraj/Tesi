"""Diagnostica del conteggio; usa esclusivamente un prompt tecnico train."""
import json
from tokenizers import Tokenizer
from .common import OUTPUT, write_json, now

def main():
    path=OUTPUT/"prompts"/"train"/"su2random_indep_tket_50.json"
    saved=json.loads(path.read_text())["prompt"]
    rows=[]
    for model in sorted((OUTPUT/"models").iterdir()):
        tokenizer=Tokenizer.from_file(str(model/"official_tokenizer.json"))
        sample=tokenizer.encode(saved["task"],add_special_tokens=False)
        lengths={key:len(tokenizer.encode(json.dumps(value,ensure_ascii=False,separators=(",",":")),add_special_tokens=False).ids) for key,value in saved.items()}
        alternatives={name:len(tokenizer.encode(json.dumps(saved,ensure_ascii=False,**kwargs),add_special_tokens=False).ids) for name,kwargs in [("default",{}),("indent2",{"indent":2}),("compact",{"separators":(",",":")})]}
        rows.append({"model":model.name,"task_tokens":sample.tokens,"sections":lengths,"representations":alternatives})
        print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
    write_json(OUTPUT/"preparation"/"tokenization_diagnostic.json",{"at":now(),"rows":rows})
if __name__=="__main__": main()

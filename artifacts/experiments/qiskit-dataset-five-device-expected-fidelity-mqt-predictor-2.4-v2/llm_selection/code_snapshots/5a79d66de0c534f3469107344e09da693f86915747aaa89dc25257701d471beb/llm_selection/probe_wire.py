"""Misura una serializzazione candidata sui soli prompt tecnici, senza inferenza."""
import json
import sys
from tokenizers import Tokenizer
from .common import OUTPUT, write_json, read_json, now
from .wire import encode_prompt, INSTRUCTION
def main():
    rows=[]
    for model in ("qwen","phi","gemma"):
        tokenizer=Tokenizer.from_file(str(OUTPUT/"models"/model/"official_tokenizer.json"))
        for path in sorted((OUTPUT/"prompts"/"train").glob("*.json")):
            prompt=read_json(path)["prompt"]
            original=json.dumps(prompt,ensure_ascii=False,separators=(",",":"))
            packed=INSTRUCTION+"\n\n"+encode_prompt(prompt)
            rows.append({"model":model,"circuit":path.stem,"split":"train","exact_roundtrip":True,
                         "original_tokens":len(tokenizer.encode(original,add_special_tokens=False).ids),
                         "table_tokens":len(tokenizer.encode(packed,add_special_tokens=False).ids),
                         "original_chars":len(original),"table_chars":len(packed)})
        del tokenizer
    target=OUTPUT/"preparation"/"lossless_table_probe.json"
    if target.exists(): raise ValueError("Probe already recorded")
    write_json(target,{"at":now(),"official_tokenizers_only_not_native_chat_counts":True,"rows":rows})
    for row in rows: print(row,flush=True)
if __name__=="__main__": main()

"""Prova tecnica sintetica del trasporto, distinta dai circuiti e dalla selezione."""
import sys
from .common import OUTPUT, write_json, now
from .gateway import audit_tokens, native_payload, generate
def main():
    directory=OUTPUT/"technical_transport"/sys.argv[1]
    directory.mkdir(parents=True,exist_ok=False)
    chat={"messages":[{"role":"user","content":'Return exactly {"ok":true} as JSON.'}],
          "chat_template_kwargs":{"enable_thinking":False},"reasoning_effort":"none",
          "response_format":{"schema":{"type":"object","properties":{"ok":{"const":True}},"required":["ok"],"additionalProperties":False}},
          "max_tokens":32,"temperature":0.0,"seed":20260913,"stream":True,"cache_prompt":True}
    count=audit_tokens(chat,directory/"audit")
    result=generate(native_payload(chat,directory/"audit"),directory/"call",timeout=120)
    write_json(directory/"summary.json",{"at":now(),"kind":"synthetic_transport_only","input_tokens":count,"response":result})
    print(result["content"],result["transport_success"],flush=True)
if __name__=="__main__": main()

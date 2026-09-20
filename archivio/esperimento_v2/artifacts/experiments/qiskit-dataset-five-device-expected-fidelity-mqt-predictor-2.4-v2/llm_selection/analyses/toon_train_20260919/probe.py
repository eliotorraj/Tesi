from pathlib import Path
import json,subprocess,copy
from prototype.prompting.minimal import model_input
from prototype.prompting.rendering import messages
from llm_selection.tokenization import count_texts
root=Path.cwd()
base=root/'artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection'
out=base/'analyses/toon_train_20260919'
node=base/'runtime/toon/current/bin/node'
bridge=root/'prototype/prompting/toon_runtime/codec.mjs'
rows=[]
for p in sorted((base/'prompts/train').glob('*.json')):
 value=model_input(json.loads(p.read_text())['prompt'])
 texts=[json.dumps(value,ensure_ascii=False,separators=(',',':'))];keys=['minimal_json']
 for table in [False,True]:
  v=copy.deepcopy(value)
  if table:
   for d in v['compatible_hardware']:
    if isinstance(d.get('coupling_edges'),list):
     d['coupling_edges']=[{'source':a,'target':b} for a,b in d['coupling_edges']]
  for delim in [',','\t','|']:
   if delim=='\\t':delim='\t'
   result=subprocess.run([str(node),str(bridge)],input=json.dumps({'operation':'encode','value':v,'delimiter':delim}),capture_output=True,text=True,check=True)
   result=json.loads(result.stdout)
   assert result['decoded']==v
   key=('edges_table_' if table else 'direct_')+repr(delim)
   texts.append(result['text']);keys.append(key)
   (out/(p.stem+'_'+str(len(texts))+'.probe.toon')).write_text(result['text'])
 counts=count_texts(texts,base/'models/qwen/official_tokenizer.json',base/'runtime/python/bin/python')
 row={'circuit':p.stem,'counts':dict(zip(keys,counts))}
 rows.append(row);print(row,flush=True)
(out/'format_probe.json').write_text(json.dumps({'method':'Official Qwen tokenizer, body only, no chat wrapper; exploration only','rows':rows},indent=2))

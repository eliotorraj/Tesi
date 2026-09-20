from pathlib import Path
import json,subprocess,copy
from prototype.prompting.minimal import model_input
from llm_selection.tokenization import count_texts
root=Path.cwd();base=root/'artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection'
out=base/'analyses/toon_train_20260919'
node=base/'runtime/toon/current/bin/node';bridge=root/'prototype/prompting/toon_runtime/codec.mjs'
rows=[]
for p in sorted((base/'prompts/train').glob('*.json')):
 value=model_input(json.loads(p.read_text())['prompt'])
 texts=[];keys=[]
 for table in [False,True]:
  v=copy.deepcopy(value)
  for d in v['compatible_hardware']:
   edges=d.get('coupling_edges')
   if isinstance(edges,list):
    adj={}
    for a,b in edges:adj.setdefault(str(a),[]).append(b)
    assert [[int(a),b] for a,ns in adj.items() for b in ns]==edges
    del d['coupling_edges'];d['coupling_adjacency']=adj
  if table:
   v['example_features']={}
   for e in v['retrieved_labeled_examples']:
    v['example_features'][e['id']]=e['circuit'].pop('features')
  for delim in [',','\t']:
   x=json.loads(subprocess.run([str(node),str(bridge)],input=json.dumps({'operation':'encode','value':v,'delimiter':delim}),capture_output=True,text=True,check=True).stdout)
   assert x['decoded']==v
   texts.append(x['text']);keys.append(('feature_table_' if table else 'adjacency_')+repr(delim))
   (out/(p.stem+'_ragtable_'+str(len(texts))+'.probe.toon')).write_text(x['text'])
 counts=count_texts(texts,base/'models/qwen/official_tokenizer.json',base/'runtime/python/bin/python')
 row={'circuit':p.stem,'counts':dict(zip(keys,counts))};rows.append(row);print(row,flush=True)
(out/'ragtable_probe.json').write_text(json.dumps({'method':'Official Qwen tokenizer, body only; exploration','rows':rows},indent=2))

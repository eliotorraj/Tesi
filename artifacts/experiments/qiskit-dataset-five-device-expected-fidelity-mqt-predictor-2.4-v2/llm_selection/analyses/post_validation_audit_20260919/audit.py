"""Audit descrittivo a posteriori. Non cambia risultati o criteri congelati.
Eseguire dalla radice: .venv/bin/python <percorso di questo file>
I segnali automatici richiedono revisione: non sono un validatore semantico.
"""
from pathlib import Path
import json,re,hashlib,collections,csv
ROOT=Path(__file__).resolve().parents[6]
OUT=Path(__file__).resolve().parent
BASE=OUT.parent.parent
STUDY=BASE/'studies/local-llm-v1'
files={}
def read(p):
    b=p.read_bytes(); files[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=hashlib.sha256(b).hexdigest()
    return json.loads(b)
def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifest=read(BASE.parent/'manifests/source_circuits_v2.json')
train={(r['circuit_id'],r['source_sha256']) for r in manifest['circuits'] if r['split']=='train'}
validation={r['circuit_id']:r for r in manifest['circuits'] if r['split']=='validation'}
rows=[]; failures=[]
for p in sorted(STUDY.glob('*/*/*/attempt_*/summary.json')):
    model,config,circuit,attempt,_=p.relative_to(STUDY).parts
    s=read(p); prompt=read(p.parent/'prompt.json'); enc=read(p.parent/'encoding.json')
    dec=read(p.parent.parent/'decision.json'); begin=read(p.parent.parent/'begin.json')
    native=read(p.parent/'call/request.json') if (p.parent/'call/request.json').exists() else {}
    resp=s.get('canonical_response',{})
    if not isinstance(resp,dict): resp={}
    examples=[]
    by_record={v:k for k,v in enc['aliases'].items()}
    for entry in prompt['retrieved_labeled_examples']:
        ex=entry['example']; cir=ex['input']['circuit']; label=ex['label']; tops=label.get('top_configurations',[])
        examples.append(dict(alias=by_record[entry['record_id']],circuit=cir['circuit_id'],source_sha256=cir['source_sha256'],train_verified=(cir['circuit_id'],cir['source_sha256']) in train,distance=entry['distance'],features=cir.get('features',{}),device=label.get('selected_device',{}).get('device_id'),top=[{k:t.get(k) for k in ('rank','config_id','median_score','tied_score_config_ids')} for t in tops[:3]]))
    claim=resp.get('claim',''); cited=[ex for ex in examples if ex['alias'] in resp.get('evidence',[])]
    selected=resp.get('selected_device'); chosen=resp.get('config_id')
    named=set(re.findall(r'[a-z0-9]+_indep_(?:qiskit|tket)_\d+',claim))
    flags=[]
    if named-{circuit}-{ex['circuit'] for ex in cited}: flags.append('named_circuit_not_in_cited_examples')
    if resp and cited and not any(ex['device']==selected for ex in cited): flags.append('selected_device_not_winner_in_cited_examples')
    if resp and cited and not any(ex['device']==selected and any(t['config_id']==chosen or chosen in (t['tied_score_config_ids'] or []) for t in ex['top']) for ex in cited): flags.append('selected_pair_not_in_cited_top_or_ties')
    if resp and any(ex['device']==selected and any((t['config_id']==chosen or chosen in (t['tied_score_config_ids'] or [])) and len(t['tied_score_config_ids'] or [])>1 for t in ex['top']) for ex in cited) and re.search(r'highest|best|optimal|superior|top.rank|ranked first|outperform',claim,re.I) and not re.search(r'tie|equal|same score|among|one of|parit',claim,re.I): flags.append('superlative_with_ties_review')
    if re.search(r'guarantee|ensur|optimal|best choice|most suitable',claim,re.I): flags.append('strong_language_review')
    if re.search(r'0\.\d+',claim): flags.append('numeric_claim_review')
    if resp and 'support' in claim.lower() and 'not' in claim.lower(): flags.append('negative_support_review')
    normalized=claim
    replacements=sorted({circuit,selected or '',chosen or '',*[ex['circuit'] for ex in examples]},key=len,reverse=True)
    for item in replacements:
        if item: normalized=normalized.replace(item,'<ID>')
    normalized=re.sub(r'\bE[1-5]\b','<E>',normalized)
    normalized=re.sub(r'\b\d+(?:\.\d+)?\b','<N>',normalized)
    row=dict(id=f'{model}/{config}/{circuit}/{attempt}',summary_path=str(p.relative_to(ROOT)),model=model,configuration=config,circuit=circuit,status=s['status'],claim=claim,evidence=resp.get('evidence',[]),selected_device=selected,selected_config=chosen,examples=examples,flags=flags,normalized_claim=normalized,all_examples_train=all(e['train_verified'] for e in examples),current_hash_absent_from_examples=all(e['source_sha256']!=begin['source_sha256'] for e in examples),input_tokens=s.get('input_tokens'),raw_response=s.get('response',{}).get('content',''),native_prompt_sha256=hashlib.sha256(native.get('prompt','').encode()).hexdigest(),decision_attempt_count=dec['attempt_count'])
    rows.append(row)
    if s['status']!='success':
        start=read(p.parent/'started.json'); server=Path(start.get('server_run_directory',begin['launch']['run_directory'])); r=s.get('response',{})
        failures.append(dict(id=row['id'],response={k:r.get(k) for k in ('started_at','ended_at','elapsed_seconds','curl_exit_code','stream_done','transport_success','content')},stderr=(p.parent/'call/stderr.txt').read_text(),resource_abort=read(server/'resource_abort.json') if (server/'resource_abort.json').exists() else None,exit=read(server/'exit.json') if (server/'exit.json').exists() else None))
# Identical normalized wording is grouped for semantic review; per-episode evidence is retained.
groups={}
for row in rows:
    key=row['normalized_claim']
    if key not in groups: groups[key]=dict(group_id=len(groups)+1,normalized_claim=key,example_claim=row['claim'],members=[],flag_counts=collections.Counter())
    g=groups[key];g['members'].append(row['id']);g['flag_counts'].update(row['flags']);row['review_group']=g['group_id']
with (OUT/'attempts.jsonl').open('w',encoding='utf8') as f:
    for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
dump('claim_groups.json',list(groups.values()));dump('transport_failures.json',failures)
selection=read(STUDY/'analysis/selection.json')
read(BASE/'frozen_study.json');read(STUDY/'all_decisions_sealed.json');read(BASE/'selection_complete.json')
summary=dict(attempts=len(rows),status_counts=dict(collections.Counter(r['status'] for r in rows)),attempt_count_distribution=dict(collections.Counter(r['decision_attempt_count'] for r in rows)),all_examples_train=all(r['all_examples_train'] for r in rows),no_current_hash_in_examples=all(r['current_hash_absent_from_examples'] for r in rows),claim_groups=len(groups),flag_counts=dict(collections.Counter(f for r in rows for f in r['flags'])),winner=selection['winner'],selection_steps=selection['steps'],per_trial={})
for trial in sorted({r['model']+'/'+r['configuration'] for r in rows}):
    sub=[r for r in rows if r['model']+'/'+r['configuration']==trial]
    summary['per_trial'][trial]=dict(attempts=len(sub),success=sum(r['status']=='success' for r in sub),flags=dict(collections.Counter(f for r in sub for f in r['flags'])))
dump('summary.json',summary);dump('input_fingerprints.json',files)
with (OUT/'attempts.csv').open('w',encoding='utf8',newline='') as f:
    keys=['id','status','selected_device','selected_config','claim','evidence','flags','review_group','summary_path'];w=csv.DictWriter(f,keys);w.writeheader()
    for r in rows:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],list) else r[k] for k in keys})
print(json.dumps({k:v for k,v in summary.items() if k not in ('selection_steps','per_trial')},ensure_ascii=False))

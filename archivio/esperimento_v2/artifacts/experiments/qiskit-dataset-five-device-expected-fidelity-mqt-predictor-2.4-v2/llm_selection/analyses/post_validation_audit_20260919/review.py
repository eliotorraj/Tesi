"""Revisione descrittiva separata. I giudizi non cambiano il success originale.
Tutte le formulazioni dei 646 gruppi sono state lette dall'assistente; i controlli
riproducibili coprono ogni singolo tentativo. Nessuna certificazione semantica
completa o nuova metrica di selezione viene ricavata da queste annotazioni.
"""
import json,re,csv,collections,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[5]
BASE=OUT.parent.parent
rows=[json.loads(l) for l in (OUT/'attempts.jsonl').read_text().splitlines()]
files=json.loads((OUT/'input_fingerprints.json').read_text())
def read(p):
    b=p.read_bytes();files[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=hashlib.sha256(b).hexdigest();return json.loads(b)
def dump(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Osservazioni qualitative dopo lettura completa dei gruppi. Non sono un gold standard.
current_result_groups=set([17,18,20,31,38,41,43,56,81,90,95,104,110,121,138,153,173,208,219,221,224,238,239,242,249,251,257,260,266,269,273,277,279,281,284,287,291,293,295,299,302,303,310,311,314,316,329,330,331,334,339,340,342,345,349,353,363,366,368,374,375,378,384,385,387,389])
notes={
156:'Confronta 10 qubit di un esempio con 156 del dispositivo, anziche con i 13 qubit del circuito corrente.',
184:'Il confronto 60 contro 156 confonde dimensione del circuito storico e capacita del dispositivo.',
263:'La motivazione parla di VQE a 14 qubit (esempio E5), mentre la richiesta e pricingcall a 11 qubit.',
286:'Nomina una piattaforma IBM Bragg non presente nel catalogo fornito: il dispositivo scelto e Heron 156.',
287:'Lo score 0.8815617931 appartiene a graphstate train; non e uno score misurato di QFT o di compatibilita.',
324:'I tre valori riportati coincidono con E1, E2, E3. Sono score di circuiti train e sono condivisi da configurazioni a pari merito; non misurano QFT.',
370:'Descrive il circuito QFT corrente come graph state: confusione con la famiglia dell esempio.',
408:'Il circuito corrente contiene Ry ma non Rx; il supporto nativo di singole porte non rende gli altri dispositivi incompatibili dopo compilazione.',
430:'La richiesta e QFT a 10 qubit, non a 156. 156 e la capacita di Heron; anche altri dispositivi sono compatibili.',
442:'Confonde i 60 qubit del circuito con i 156 del dispositivo e attribuisce score storici al circuito corrente.',
455:'Nel QFT entangled Qiskit a 40 qubit ci sono 39 CX e 780 CP, non 780 CNOT.',
461:'Il QFT entangled Qiskit a 8 qubit ha 7 CX; 84 non e il conteggio CX del circuito corrente.',
468:'Heron 156 non ha topologia fisica completamente connessa. La possibilita di routing non equivale a connettivita nativa completa.',
478:'Attribuisce 13 Hadamard al circuito pricingcall a 5 qubit; il prompt corrente non contiene porte H.',
479:'Falcon 127 non ha CCX, CRy e U3 tra le porte native del Target fornito.',
482:'Falcon 127 non ha una porta CCX nativa nel Target fornito.',
492:'Nel circuito corrente ci sono 55 CP, non 5.',
493:'12 qubit non superano la capacita di 27 qubit. Heron 156 non e l unica opzione compatibile.',
497:'La topologia Heron 156 non fornisce il sottografo completo a 16 qubit dichiarato.',
506:'Nel Target Falcon 127 fornito CX e nativa, H non lo e; H richiede una decomposizione.',
512:'I 10 qubit del circuito non coincidono con i 127 del dispositivo; le caratteristiche storiche non identificano il circuito corrente.',
515:'Heron 156 non e un sottoinsieme di Heron 133 nel catalogo. Le graduatorie degli esempi non sono una graduatoria del circuito corrente.',
519:'CU1 non e una porta nativa nel Target Quantinuum fornito; piena connettivita non elimina la decomposizione delle porte.',
545:'Il circuito corrente ha H, CP, CX e SWAP; non usa soltanto Ry e swap.',
550:'La connettivita completa non implica che tutte le operazioni possano essere eseguite simultaneamente: rimangono le dipendenze del circuito.',
552:'Il QFT entangled contiene CU1, CX, H e SWAP, assenti dalle operazioni native Quantinuum. La decomposizione e necessaria.',
580:'Le 66 CP del circuito corrente non sono porte native nel Target Quantinuum fornito.',
}
cache={}; reviewed=[]; native_checks=[]
for r in rows:
    p=ROOT/r['summary_path']; pr=cache.setdefault(r['circuit'],None)
    if pr is None: pr=read(p.parent/'prompt.json');cache[r['circuit']]=pr
    live=pr['live_request'];cir=live['circuit'];dev=next((d for d in live['compatible_hardware'] if d['id']==r['selected_device']),None)
    cited=[e for e in r['examples'] if e['alias'] in r['evidence']]
    observations=[]
    if r['status']!='success': observations.append('Nessuna risposta: claim ed evidence non valutabili. Non e un errore di ragionamento osservato.')
    else:
        if 'named_circuit_not_in_cited_examples' in r['flags']: observations.append('Almeno un circuito nominato non coincide con il circuito corrente o con quelli delle evidenze citate: controllare associazione nome/alias.')
        if 'selected_pair_not_in_cited_top_or_ties' in r['flags']: observations.append('Nessun esempio citato presenta la coppia scelta nelle prime configurazioni o nelle parita. La scelta e consentita, ma non ha questo sostegno storico diretto.')
        if r['review_group'] in current_result_groups: observations.append('La formulazione attribuisce o estende risultati/classifiche storici al circuito corrente; questa conclusione non e dimostrata dal prompt.')
        if re.search(r'\bnativ',r['claim'],re.I): observations.append('La compatibilita dopo compilazione va distinta dal supporto nativo. Confrontare le porte correnti con operation_names del Target, qui esportate.')
        if 'superlative_with_ties_review' in r['flags']: observations.append('Esiste una parita per la configurazione citata: massimo non implica migliore in modo esclusivo. Il solo superlativo non basta a dichiarare falso il claim.')
        if r['review_group'] in notes: observations.append(notes[r['review_group']])
        if not observations: observations.append('Motivazione leggibile come proposta o riferimento storico; nessuna contraddizione nei controlli circoscritti applicati. Non certifica ottimalita, causalita o correttezza semantica completa.')
    facts=dict(name=cir['name'],num_qubits=cir['num_qubits'],depth=cir['depth'],operation_names=cir['operation_names'],features=cir['features'])
    hardware={k:dev[k] for k in ('id','num_qubits','operation_names')} if dev else None
    if hardware:
        edges=dev['coupling_edges'];hardware['coupling_edge_count']=len(edges);hardware['native_complete_directed_graph']=len({tuple(e) for e in edges})==dev['num_qubits']*(dev['num_qubits']-1)
    support=[dict(alias=e['alias'],circuit=e['circuit'],device=e['device'],selected_device_matches=e['device']==r['selected_device'],selected_pair_supported=e['device']==r['selected_device'] and any(t['config_id']==r['selected_config'] or r['selected_config'] in (t['tied_score_config_ids'] or []) for t in e['top']),top=e['top']) for e in cited]
    reviewed.append(dict(**{k:r[k] for k in ('id','status','claim','evidence','selected_device','selected_config','review_group','flags','summary_path')},observations=observations,current_circuit=facts,selected_hardware=hardware,cited_examples=support))
    req=read(p.parent/'call/request.json'); template=read(p.parent/'audit/template/response.json'); msgs=read(p.parent/'audit/template/request.json')
    text=req['prompt'];current_part=text.split('retrieved_labeled_examples[')[0]
    numeric_score_lines=[line for line in current_part.splitlines() if re.search(r'(?:median_score|oracle_score|regret|expected_fidelity_score)\s*:',line)]
    native_checks.append(dict(id=r['id'],native_equals_archived_template=text==template['prompt'],no_score_field_before_examples=not numeric_score_lines,all_examples_train=r['all_examples_train'],current_hash_absent=r['current_hash_absent_from_examples'],message_count=len(msgs['messages'])))
# Compare messages actually used, not merely the current code constants.
checklist='Check that the device is compatible, config_id is allowed for it, and every cited example ID was supplied. Do not report a measured score for the new circuit.'
prompt_comparison=[]
for model in ('qwen','phi','gemma'):
 for circuit in sorted(cache):
    root=BASE/'studies/local-llm-v1'/model
    a=read(root/'p0_t0'/circuit/'attempt_1/audit/template/request.json');b=read(root/'p1_t0'/circuit/'attempt_1/audit/template/request.json')
    prompt_comparison.append(dict(model=model,circuit=circuit,only_checklist_difference=b['messages'][0]['content']==a['messages'][0]['content']+'\n'+checklist))
with (OUT/'reviewed_attempts.jsonl').open('w',encoding='utf8') as f:
 for r in reviewed:f.write(json.dumps(r,ensure_ascii=False)+'\n')
with (OUT/'reviewed_attempts.csv').open('w',encoding='utf8',newline='') as f:
 keys=['id','status','selected_device','selected_config','claim','evidence','observations','flags','review_group','summary_path'];w=csv.DictWriter(f,keys);w.writeheader()
 for r in reviewed:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],list) else r[k] for k in keys})
dump('review_notes.json',{'review_method':'Lettura di tutte le 645 formulazioni non vuote normalizzate, copertura dei 789 claim; dati e controlli delle citazioni per ciascun tentativo. Nessuna valutazione umana indipendente; nessuna percentuale globale di correttezza semantica. Le annotazioni sono qualitative e posteriori alla selezione.','current_result_groups':sorted(current_result_groups),'specific_notes':notes})
dump('prompt_integrity_checks.json',native_checks);dump('prompt_variant_comparison.json',prompt_comparison)
dump('input_fingerprints.json',files)
print(json.dumps({'reviewed':len(reviewed),'response_claims':sum(r['status']=='success' for r in reviewed),'named_circuit_mismatches':sum('named_circuit_not_in_cited_examples' in r['flags'] for r in reviewed),'no_direct_pair_support':sum('selected_pair_not_in_cited_top_or_ties' in r['flags'] for r in reviewed),'all_native_prompts_match_template':all(r['native_equals_archived_template'] for r in native_checks),'all_current_sections_no_score_fields':all(r['no_score_field_before_examples'] for r in native_checks),'all_p1_diff_only_checklist':all(r['only_checklist_difference'] for r in prompt_comparison)}))

choice_comparison=[]
for model in ('qwen','phi','gemma'):
    a={r['circuit']:r for r in rows if r['model']==model and r['configuration']=='p0_t0' and r['status']=='success'}
    b={r['circuit']:r for r in rows if r['model']==model and r['configuration']=='p1_t0' and r['status']=='success'}
    common=a.keys()&b.keys()
    choice_comparison.append(dict(model=model,common_successful_circuits=len(common),different_device=sum(a[k]['selected_device']!=b[k]['selected_device'] for k in common),different_pair=sum((a[k]['selected_device'],a[k]['selected_config'])!=(b[k]['selected_device'],b[k]['selected_config']) for k in common)))
dump('p0_p1_choice_comparison.json',choice_comparison)

"""Confronto QASMBench RAG k=5: legge esiti esistenti, non avvia compilazioni."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse
import csv
import json
import math
import statistics
from oracle_core import read, sha, digest, jobs, aggregate_rows, validate_result, plan_counts, REPO, SOURCE_SHA

TOL=1e-12

def require(condition,message):
    if not condition:raise ValueError(message)

def save(path,value):
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def difference(a,b):
    return round(a-b,10) if a is not None and b is not None else None

def average(values):
    xs=[x for x in values if x is not None]
    return statistics.mean(xs) if xs else None

def stats(rows):
    compared=[r for r in rows if r['gap'] is not None]
    return {'n':len(rows),'compared':len(compared),
        'mean_system':average(r['system_score'] for r in compared),
        'mean_oracle':average(r['oracle_score'] for r in compared),
        'mean_gap':average(r['gap'] for r in compared),
        'median_gap':statistics.median(r['gap'] for r in compared) if compared else None,
        'max_gap':max((r['gap'] for r in compared),default=None),
        'statuses':dict(Counter(r['status'] for r in rows)),
        'best_pairs':sum(r['selected_pair_is_best'] is True for r in rows),
        'within_001':sum(abs(r['gap'])<=.01 for r in compared)}

def audit_oracle(directory):
    directory=Path(directory).resolve();root=directory.parent.parent
    require(directory.parent.name=='analisi','Indicare una cartella analisi della campagna.')
    sources={}
    def checked(path):
        value=read(path);sources[str(path)]=sha(path);return value
    oc=checked(root/'contratto.json');identity=oc['identity']
    require(digest(identity)==oc['identity_sha256'],'Contratto oracle alterato.')
    require(identity['schema']=='qasmbench50-oracle-max3-v1','Non è la campagna QASMBench50.')
    require(identity['source_manifest_sha256']==SOURCE_SHA,'Manifest QASMBench diverso.')
    require(len(identity['circuits'])==50 and identity['seeds']==[0,1,2],'Piano oracle diverso.')
    summary=checked(directory/'riepilogo.json');refs=checked(directory/'oracle_test.json')
    pairs=checked(directory/'configurazioni.json');provenance=checked(directory/'provenienza.json')
    require(summary['identity_sha256']==oc['identity_sha256'],'Analisi di un altro contratto.')
    require(summary['plan']==plan_counts(identity)==oc['plan'],'Conteggi del piano incoerenti.')
    jobmap={j['job_id']:j for j in jobs(identity)};records={}
    for rel,expected_hash in provenance.items():
        path=(root/rel).resolve()
        require(path.is_relative_to(root/'tentativi') and path.name=='esito.json','Percorso esito non valido.')
        require(sha(path)==expected_hash,'Esito alterato: '+rel)
        result=checked(path);jid=result['job_id']
        require(jid in jobmap and jid not in records,'Esito duplicato o estraneo al piano.')
        require(path==root/'tentativi'/jid/'esito.json','Percorso/identità esito incoerente.')
        records[jid]=validate_result(jobmap[jid],result,path.parent)
    calculated_pairs,calculated_refs=aggregate_rows(identity,records)
    require(calculated_pairs==pairs and calculated_refs==refs,'Massimi o copertura diversi dagli esiti originali.')
    require(dict(Counter(r['status'] for r in records.values()))==summary['statuses'],'Stati incoerenti.')
    require(summary['terminal']==len(records) and summary['pending']==len(jobmap)-len(records),'Copertura incoerente.')
    require(summary['complete']==(len(records)==len(jobmap)),'Fine campagna incoerente.')
    require(summary['circuits_with_reference']==sum(r['reference_score'] is not None for r in refs),'Riferimenti incoerenti.')
    require(summary['circuits_with_exhaustive_reference']==sum(r['reference_is_exhaustive'] for r in refs),'Esaustività incoerente.')
    for row in identity['circuits']:
        path=root/'sorgenti'/(row['circuit_id']+'.qasm')
        require(sha(path)==row['source_sha256'],'Copia QASM alterata.')
        sources[str(path)]=sha(path)
    return oc,summary,refs,pairs,sources,len(records)

def audit_rag(rag_root,identity):
    """Verifica i 50 registri già esistenti; nessun import del runner storico."""
    root=Path(rag_root).resolve();sources={}
    def checked(path):
        value=read(path);sources[str(path)]=sha(path);return value
    contract_path=root/'preparazione/contratto_congelato.json'
    contract=checked(contract_path);execution=checked(root/'risultati/llm_rag/esecuzione.json')
    manifest=checked(root/'manifest.json');plan=checked(root/'piano.json')
    require(execution['contract_sha256']==sha(contract_path),'Contratto RAG alterato.')
    require(execution['plan_sha256']==sha(root/'piano.json') and plan==contract['plan'],'Piano RAG alterato.')
    require(identity['source_manifest_sha256']==contract['source_sha256']==sha(root/'manifest.json'),'Sorgenti RAG/oracle differenti.')
    require(contract['plan']['qiskit_seed']==0 and execution['method']=='llm_rag','Metodo o seed RAG differenti.')
    hardware=execution['preflight']['checks']['software_targets']['details']
    require(hardware['targets']==identity['catalog']['target_sha256'],'Target RAG/oracle differenti.')
    for name in ('qiskit','mqt.bench','numpy'):
        require(hardware['versions'][name]==identity['versions'][name],'Versione RAG/oracle differente: '+name)
    expected={r['circuit_id']:r for r in identity['circuits']}
    require(set(expected)=={r['circuit_id'] for r in manifest['circuits']},'Circuiti RAG/oracle differenti.')
    values={}
    for cid,row in expected.items():
        folder=root/'risultati/llm_rag/circuiti'/cid
        result=checked(folder/'esito.json');retrieval=checked(folder/'retrieval.json')
        require(result['circuit_id']==cid and result['source_sha256']==row['source_sha256'],'Identità RAG diversa.')
        require(result['method']=='llm_rag' and result['split']=='external_test','Esito estraneo al Test QASMBench.')
        require(len(retrieval['records'])==5,'Recupero diverso da k=5.')
        original=root/'circuiti'/row['source_ref'];inp=folder/'input.qasm'
        require(sha(original)==row['source_sha256'],'QASM originale RAG alterato.')
        # Il runner storico normalizza CRLF: confronto del testo, conservando entrambi gli hash.
        require(inp.read_text(encoding='utf-8')==original.read_text(encoding='utf-8'),'Input RAG differente.')
        sources[str(original)]=sha(original);sources[str(inp)]=sha(inp)
        if result['status']=='success':
            compiled=checked(folder/'compilazione/result.json');job=checked(folder/'compilazione/job.json')
            score=result['score']
            require(isinstance(score,(int,float)) and not isinstance(score,bool) and math.isfinite(score) and 0<=score<=1,'Score RAG non valido.')
            require(compiled['status']=='success' and compiled['score']==score and compiled['validation']['is_executable_on_target'],'Compilazione RAG incoerente.')
            require(job['decision']['selected_device']==result['device'] and job['decision']['config_id']==result['config_id'],'Decisione RAG incoerente.')
        else:require(result.get('score') is None,'Fallimento RAG con score presente.')
        values[cid]=result
    return values,execution,sources

def build_rows(identity,refs,pairs,rag):
    expected={r['circuit_id']:r for r in identity['circuits']}
    pairmap={(p['circuit_id'],p['device'],p['config_id']):p for p in pairs}
    rows=[]
    for o in sorted(refs,key=lambda r:r['circuit_id']):
        cid=o['circuit_id'];r=rag[cid];score=r.get('score') if r['status']=='success' else None
        selected=pairmap.get((cid,r.get('device'),r.get('config_id')))
        if score is not None:require(selected is not None and selected['compatible'],'Coppia RAG esterna alla griglia.')
        best=selected['max_score'] if selected else None;ref=o['reference_score']
        gap=difference(ref,score);choice=difference(ref,best);seed=difference(best,score)
        seed0=selected['seed_scores']['0'] if selected else None
        ps=[p for p in pairs if p['circuit_id']==cid and p['compatible']]
        rows.append(dict(id=len(rows)+1,circuit_id=cid,num_qubits=expected[cid]['num_qubits'],size_group=expected[cid]['size_group'],
            source_sha256=o['source_sha256'],system_status=r['status'],system_score=score,oracle_score=ref,
            gap=gap,gap_pp=100*gap if gap is not None else None,relative_gap_percent=100*gap/ref if gap is not None and ref else None,
            status='non confrontabile' if gap is None else ('pari' if abs(gap)<=TOL else ('sotto' if gap>0 else 'sopra')),
            exhaustive=o['reference_is_exhaustive'],device=r.get('device'),config_id=r.get('config_id'),
            selected_pair_max3=best,choice_gap=choice,within_pair_gap=seed,
            selected_pair_is_best=abs(choice)<=TOL if choice is not None else None,
            selected_pair_complete=selected['all_three_successful'] if selected else False,
            selected_seed_scores=selected['seed_scores'] if selected else {},selected_seed_statuses=selected['seed_statuses'] if selected else {},
            oracle_selected_seed0=seed0,seed0_repeat_difference=difference(seed0,score),
            best_seed0_global=o['best_seed0_score'],gap_vs_seed0_global=difference(o['best_seed0_score'],score),
            best_pairs=o['best_pairs'],successful_attempts=sum(len(p['successful_seeds']) for p in ps),expected_attempts=3*len(ps)))
    return rows

def summarize(rows):
    s=stats(rows)
    s['complete']=stats([r for r in rows if r['exhaustive']]);s['partial']=stats([r for r in rows if not r['exhaustive']])
    s['by_size']={g:stats([r for r in rows if r['size_group']==g]) for g in ('small','medium','large')}
    s['selected_pair_complete']=sum(r['selected_pair_complete'] for r in rows)
    s['decomposition_n']=sum(r['choice_gap'] is not None and r['within_pair_gap'] is not None for r in rows)
    s['seed0_different']=sum(r['seed0_repeat_difference'] is not None and abs(r['seed0_repeat_difference'])>TOL for r in rows)
    s['seed0_missing']=sum(r['seed0_repeat_difference'] is None for r in rows)
    s['seed0_max_abs_difference']=max((abs(r['seed0_repeat_difference']) for r in rows if r['seed0_repeat_difference'] is not None),default=None)
    s['mean_choice_gap']=average(r['choice_gap'] for r in rows if r['within_pair_gap'] is not None)
    s['mean_within_pair_gap']=average(r['within_pair_gap'] for r in rows if r['choice_gap'] is not None)
    s['mean_gap_vs_seed0_global']=average(r['gap_vs_seed0_global'] for r in rows)
    s['seed0_global_n']=sum(r['gap_vs_seed0_global'] is not None for r in rows)
    s['system_statuses']=dict(Counter(r['system_status'] for r in rows))
    return s

def compare(oracle,rag_root,output):
    output=Path(output)
    require(not output.exists(),'Destinazione confronto già esistente: scegliere una cartella nuova.')
    oc,summary,refs,pairs,sources,verified=audit_oracle(oracle)
    rag,execution,rag_sources=audit_rag(rag_root,oc['identity']);sources.update(rag_sources)
    rows=build_rows(oc['identity'],refs,pairs,rag);s=summarize(rows)
    require(all(sha(Path(p))==h for p,h in sources.items()),'Una fonte è cambiata durante l’analisi.')
    data=dict(created_at=datetime.now(timezone.utc).isoformat(),oracle_path=str(Path(oracle).resolve()),rag_path=str(Path(rag_root).resolve()),
        tolerance=TOL,summary=s,oracle_summary=summary,rows=rows,oracle_identity=oc['identity_sha256'],
        system_contract=execution['contract_sha256'],oracle_versions=oc['identity']['versions'],python=oc['identity']['python'],
        model_sha256=execution['server']['model_sha256'],system_started_at=execution['at'],synthetic=False)
    output.mkdir(parents=True)
    save(output/'dati.json',data)
    with (output/'confronto_50_circuiti.csv').open('x',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    save(output/'provenienza.json',dict(source_sha256=sources,oracle_results_verified=verified,
        scripts_sha256={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')},
        checks=dict(same_50_sources=True,retrieval_k5_all_cases=True,all_recorded_oracle_results_checked=True,
                    all_pair_and_circuit_maxima_recomputed=True,quantum_compilations_started=0)))
    return data

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--oracle',type=Path,required=True)
    ap.add_argument('--rag-root',type=Path,default=REPO/'archivio/valutazione/test_qasmbench')
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();compare(a.oracle,a.rag_root,a.output)
    from impagina import render
    print(render(a.output))

if __name__=='__main__':main()

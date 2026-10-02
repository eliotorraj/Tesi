"""Rigenera i report dei singoli sistemi e il confronto, leggendo soltanto artefatti."""
from __future__ import annotations
import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from dati import METHODS, LABELS, read, sha, digest, write_json, write_csv, load_run, compare, number, run_label
from fonti import load_sources
from confronto import comparison_body, discrete
from impaginazione import esc, fmt, table, figure, metric_table, metric_plot, reliability_plot, ecdf_plot, retry_plot, compile_document

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
AREA=HERE.parent
SOURCE=REPO/'archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/manifests/source_circuits_v2.json'


def exploratory_notice(run):
    source = run.get('source', {})
    if not source.get('exploratory'):
        return ''
    d = source['details']
    collection_note = ('La raccolta train comprende tentativi a 100 secondi e recuperi a 300 secondi. ' if d.get('collection_profile') == 'adaptive-100-then-300-v1' else '')
    return (r'\paragraph{MQT: prova esplorativa separata.} '
        'I risultati MQT provengono da '+r'\nolinkurl{'+source['area']+'}. '
        'Il confronto che comprende MQT è esplorativo e non completa la valutazione conforme al contratto originale. '
        f"Il selettore usa {fmt(d.get('training_samples'),0)} dei {fmt(d.get('expected_training_samples'),0)} campioni train previsti, "
        f"con {fmt(d.get('excluded_samples'),0)} esclusi e {fmt(d.get('successful_compilations'),0)} compilazioni riuscite "
        f"su {fmt(d.get('required_compilations'),0)} coppie. "
        'Il profilo di raccolta dichiarato è '+esc(d.get('collection_profile','non dichiarato'))+'. '+collection_note+
        'Le classi derivano dai dispositivi vincitori osservati; non vengono aggiunte classi artificiali. '
        'Restano gli stessi circuiti Test, la metrica e il limite di 100 secondi per la valutazione. '
        'Le deroghe di addestramento e il contratto separato restano nella provenienza; '
        'i confronti fra gli altri tre sistemi mantengono il piano originale.\n\n')


def method_body(output, run):
    m=run['meta']['method']; s=run['summary']; cs=run['circuits']; llm=m.startswith('llm')
    body='\\section{Risultati di '+esc(run_label(m, run))+'}\n'
    body+=exploratory_notice(run)
    body+=f"Sono conclusi {s['completed_circuits']} dei {s['expected_circuits']} circuiti previsti. "
    body+=f"I {s['episodes']} episodi conservati comprendono {s['successes']} successi e {s['failures']} fallimenti; {s['pending']} circuiti restano pendenti. "
    body+=f"I circuiti con almeno un successo sono {s['circuits_with_success']}; quelli con almeno un fallimento sono {s['circuits_with_failure']}.\n\n"
    body+='Un successo indica una compilazione valida, non la correttezza del testo libero prodotto dal modello. '
    body+='Lo score è riportato sui successi; tempi e costi includono anche i fallimenti quando misurati.\n\n'
    body+='\\subsection{Riepilogo delle misure}\n'+metric_table(s)
    body+='Le medie e le mediane sono calcolate sulle medie per circuito disponibili. La somma nota riguarda gli episodi. '
    body+='Le ultime due colonne indicano circuiti ed episodi con misura, sui rispettivi denominatori. '
    body+='Per lo score il denominatore degli episodi è il numero di successi.\n\n'
    partial={k:v['partially_measured_circuits'] for k,v in s['metrics'].items() if v['partially_measured_circuits']}
    if partial:
        body+='Sono presenti medie per circuito parziali: '+esc(str(partial))+'. Le coperture per circuito sono nei CSV.\n\n'
    if s['failure_causes']:
        body+='Cause dei fallimenti: '+', '.join(esc(k)+f" ({v})" for k,v in sorted(s['failure_causes'].items()))+'.\n\n'
    else:
        body+='Tutti gli episodi conservati hanno prodotto una compilazione valida.\n\n'
    if llm:
        body+=f"Episodi con almeno un retry: {s['episodes_with_retry']}/{s['episodes']}. "
        body+=f"Episodi accettati con fatti non verificati: {s['accepted_with_unverified_facts']}/{s['episodes']}. "
        body+='I retry correggono la risposta; non ripetono la compilazione.\n\n'
        body+='Distribuzione dei retry per episodio: '+', '.join(esc(k)+f" retry: {v} episodi" for k,v in s['retry_distribution'].items())+'.\n\n'
        for key,label in [('known_input_tokens','ingresso'),('known_output_tokens','uscita')]:
            v=s[key]
            body+=f"Somma parziale nota dei token in {label}: {fmt(v['sum_known'],0)}, con contatore disponibile in {v['measured_episodes']} episodi. "
        body+='Questi contatori non sostituiscono i totali completi se manca una misura.\n\n'
    body+=f"Score arrotondati a zero: {s['rounded_to_zero']}; indicatori di underflow: {s['underflow']}.\n"
    body+='\\subsection{Andamento sui circuiti}\nI grafici seguono l’ordine alfabetico dei circuiti nelle tabelle. Un punto indica la media disponibile per un circuito; le misure mancanti non sono zeri.\n'
    for metric,caption in [('score','Score di ogni circuito riuscito. Un punto assente non viene sostituito con zero.'),
                           ('total_seconds','Tempo totale per circuito, inclusi preparazione ed eventuali tentativi falliti.'),
                           ('compilation_seconds','Tempo interno del compilatore. I timeout senza misura interna restano assenti.'),
                           ('compilation_process_seconds','Tempo del processo di compilazione: comprende avvio e controlli; rende visibili i timeout.')]:
        metric_plot(output,metric,{m:run},metric)
        body+=figure(metric,caption+' I circuiti seguono lo stesso ordine alfabetico delle tabelle.')
    if llm:
        for metric,caption in [('total_tokens','Token di ingresso e uscita cumulativi di tutte le chiamate dell’episodio.'),
                               ('llm_response_seconds','Latenza cumulativa delle chiamate LLM per circuito.')]:
            metric_plot(output,metric,{m:run},metric)
            body+=figure(metric,caption+' Con più episodi si usa la media per circuito.')
    body+=r'\FloatBarrier\clearpage'+'\n'+r'\subsection{Dati di ogni circuito}'+'\n'
    body+='Gli identificativi sono ordinati lessicograficamente secondo il manifest Test. '
    body+='Sono riportati episodi conclusi, successi e fallimenti. Lo score è la media dei soli successi, con dieci decimali.\n'
    rows=[[esc(c['circuit_id']),c['episodes'],c['successes'],c['failures'],fmt(c['score'],10)] for c in cs]
    body+=table(['Circuito','Episodi','Successi','Fallimenti','Score'],rows,long=True,size='scriptsize')
    body+='\\subsection{Tempi per circuito}\nTutti i valori sono medie in secondi. -- indica una misura interna non disponibile, un caso pendente o una misura non applicabile.\n'
    headers=['Circuito','Totale','Compilatore','Processo']+(['Risposta LLM'] if llm else [])
    rows=[[esc(c['circuit_id'])]+[fmt(c.get(k)) for k in ('total_seconds','compilation_seconds','compilation_process_seconds')]+([fmt(c.get('llm_response_seconds'))] if llm else []) for c in cs]
    body+=table(headers,rows,long=True,size='footnotesize')
    if llm:
        body+='\\subsection{Token e retry per circuito}\nI costi comprendono tutti i tentativi dell’episodio. In presenza di repliche i valori sono medie, non somme.\n'
        rows=[[esc(c['circuit_id'])]+[discrete(c.get(k)) for k in ('input_tokens','output_tokens','total_tokens','retries','llm_calls')] for c in cs]
        body+=table(['Circuito','Ingresso','Uscita','Totali','Correzioni','Chiamate'],rows,long=True,size='footnotesize')
    body+='\\begin{samepage}\\subsection{Definizioni e limiti}\n'
    body+='Il tempo totale comprende il procedimento dal circuito all’esito misurato. La risposta LLM somma le latenze delle chiamate; '
    body+='il tempo interno di compilazione è distinto dal tempo del processo. Le misure mancanti non sono zeri. '
    body+='La media sui successi non dimostra superiorità rispetto a un altro sistema. La qualità è stimata su Target sintetici. '
    body+='Un solo episodio non misura la variabilità fra esecuzioni. Il confronto completo documenta procedura, appaiamento e limiti comuni.\n\\par\\end{samepage}\n'
    return body


def provenance_body(runs, fingerprint, provenance):
    body=r'\FloatBarrier\section{Provenienza e riproduzione}'+'\n'
    body+='Identità dell’analisi: '+r'\nolinkurl{'+fingerprint+'}.\n\n'
    body+='Il file '+r'\texttt{provenienza.json}'+' conserva le impronte di input, manifest, contratto, configurazione, protocollo e generatore. '
    body+='La cartella '+r'\texttt{generatore/}'+' contiene una copia dei sorgenti usati. '
    body+='Le tabelle CSV mantengono i valori numerici non formattati e i denominatori; i grafici derivano dagli stessi dati. '
    body+='Il documento autonomo e il frammento inseribile nella tesi sono nella cartella '+r'\texttt{latex/}'+'.\n\n'
    body+='Per aggiornare tutti i report, dalla radice del progetto:\n'+r'\begin{quote}\small\ttfamily .venv/bin/python prototipo/test/report/genera.py\end{quote}'+'\n'
    body+='Il comando legge gli esiti già presenti, verifica contratto, split e impronte dei circuiti e legge MQT dall’area esplorativa quando presente, mantenendone distinta la provenienza. '
    body+='Non avvia il Test e non chiama modelli. Le vecchie analisi e gli esiti originali vengono conservati.\n\n'
    return body


def build(area=AREA, output_root=None, compile_pdf=True, mqt_area=None):
    area=Path(area).resolve()
    contract_path=area/'preparazione/contratto_congelato.json'
    contract=read(contract_path)
    plan=read(area/'piano.json')
    if contract['plan']!=plan or plan.get('test_id')!='test-indipendenti-v1':
        raise ValueError('Piano corrente diverso dal contratto o non supportato.')
    if plan['analysis']!={'unit':'circuit','bootstrap_seed':20260901,'bootstrap_draws':10000,'confidence':0.95,'comparisons':['llm_rag vs llm_senza_rag','llm_rag vs mqt_predictor','llm_rag vs random'],'quality_population':'common successful circuits; failures reported separately','confirmatory_tests':'none; descriptive paired intervals, no superiority claim from incomplete comparison'}:
        raise ValueError('Piano di analisi non supportato: aggiornare anche la documentazione.')
    if sha(SOURCE)!=contract['source_sha256']:
        raise ValueError('Manifest diverso dalla fonte congelata.')
    expected={r['circuit_id']:r['source_sha256'] for r in read(SOURCE)['circuits'] if r['split']=='test'}
    if len(expected)!=plan['circuits']:
        raise ValueError('Numerosità Test incoerente.')
    runs=load_sources(area,expected,contract,mqt_area=mqt_area)
    if not runs:
        raise ValueError('Nessun registro Test disponibile.')
    # Legge i metadati del selettore senza caricare il modello.
    metadata_path=None
    if runs.get('mqt_predictor',{}).get('source',{}).get('exploratory'):
        metadata_path=Path(runs['mqt_predictor']['source']['area'])/'runtime/trained_clf_expected_fidelity.metadata.json'
        if metadata_path.exists():
            runs['mqt_predictor']['report_model_metadata']=read(metadata_path)
    sources={p.name:sha(p) for p in sorted(HERE.iterdir()) if p.suffix in ('.py','.tex','.md')}
    supporting=[SOURCE,contract_path,area/'piano.json',REPO/'prototipo/config.json',REPO/'prototipo/docs/protocollo_sperimentale.md']
    if metadata_path and metadata_path.exists():
        supporting.append(metadata_path)
    provenance=dict(schema_version=1, generator_files=sources,
        supporting_files={str(p.relative_to(REPO)):sha(p) for p in supporting},
        input_files={m:r['input_files'] for m,r in runs.items()},
        result_sources={m:r['source'] for m,r in runs.items()},
        run_metadata={m:r['meta'] for m,r in runs.items()},
        generation_settings={m:r['generation_settings'] for m,r in runs.items()},
        method_parameters={m:r.get('report_model_metadata',{}) for m,r in runs.items()},
        environment={'python':platform.python_version(),'numpy':np.__version__},
        aggregation='episode means within circuit; equal circuit weights; successful scores only; known costs on all episodes; no imputation',
        statistical_plan=plan['analysis'])
    fingerprint=digest(provenance)
    output_root=Path(output_root or area/'report_generati').resolve()
    output=output_root/fingerprint[:16]
    complete=output/'completato.json'
    comparison=compare(runs,plan['analysis'])
    if complete.exists():
        saved=read(complete)
        if all((output/p).exists() and sha(output/p)==v for p,v in saved['outputs'].items()) and (not compile_pdf or saved['pdf_available']):
            publish_latest(output_root,output,runs)
            return output
        # Una versione conclusa è immutabile, anche se era solo sorgenti.
        output=output_root/(fingerprint[:16]+('-pdf' if compile_pdf else '-sorgenti'))
        if (output/'completato.json').exists():
            raise ValueError('Artefatti già conclusi alterati o variante occupata: usare --output in una nuova cartella.')
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'provenienza.json',provenance)
    snapshot=output/'generatore';snapshot.mkdir(exist_ok=True)
    for name in sources:
        shutil.copy2(HERE/name,snapshot/name)
    write_json(output/'confronto.json',comparison)
    all_circuits=[]
    for method,run in runs.items():
        dest=output/'sistemi'/method
        write_json(dest/'riepilogo.json',run['summary'])
        write_csv(dest/'tabelle/circuiti.csv',run['circuits'])
        write_csv(dest/'tabelle/episodi.csv',run['rows'])
        write_json(dest/'tabelle/episodi.json',run['rows'])
        all_circuits.extend(dict(method=method,**c) for c in run['circuits'])
        print('Rapporto '+LABELS[method],flush=True)
        body=method_body(dest,run)+provenance_body({method:run},fingerprint,provenance)
        compile_document(dest,'Test: '+run_label(method, run),body,compile_pdf)
    dest=output/'confronto'
    write_csv(dest/'tabelle/circuiti_tutti_sistemi.csv',all_circuits)
    write_json(dest/'tabelle/riepiloghi.json',{m:r['summary'] for m,r in runs.items()})
    write_json(dest/'tabelle/confronti_appaiati.json',comparison)
    write_csv(dest/'tabelle/differenze_appaiate.csv',[dict(other_method=m,**row) for m,p in comparison['pairs'].items() for row in p['differences']],['other_method','circuit_id','difference'])
    print('Rapporto complessivo',flush=True)
    body=comparison_body(dest,runs,comparison,plan)
    compile_document(dest,'Confronto dei sistemi sul Test',body,compile_pdf)
    # Verifica che non sia cambiato alcun input durante la generazione.
    for method,run in runs.items():
        base=Path(run['source']['base'])
        for path, fingerprint_before in run['source']['supporting_files'].items():
            if sha(Path(path)) != fingerprint_before:
                raise RuntimeError('Contratto o piano della fonte cambiato durante la generazione: '+path)
        current={str(p.relative_to(base)):sha(p) for folder in ('circuiti','sessioni') for p in sorted((base/folder).rglob('*.json'))}
        current['esecuzione.json']=sha(base/'esecuzione.json')
        if current!=run['input_files']:
            raise RuntimeError('Input cambiati durante la generazione: '+method+'. Rilanciare dopo la conclusione delle scritture.')
    output_hashes={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='completato.json'}
    write_json(output/'completato.json',dict(at=datetime.now(timezone.utc).isoformat(),fingerprint=fingerprint,pdf_available=compile_pdf,outputs=output_hashes))
    publish_latest(output_root,output,runs)
    return output


def publish_latest(root,output,runs):
    value={'directory':str(output),'comparison_pdf':str(output/'confronto/latex/verifica.pdf'),
           'system_pdfs':{m:str(output/'sistemi'/m/'latex/verifica.pdf') for m in runs}}
    tmp=root/'ultimo.tmp.json';write_json(tmp,value);tmp.replace(root/'ultimo.json')
    text='# Report del Test\n\nUltima analisi: `'+output.name+'`.\n\n'
    text+='- [Rapporto complessivo]('+output.name+'/confronto/latex/verifica.pdf)\n'
    for m in runs:
        text+='- ['+run_label(m,runs[m])+']('+output.name+'/sistemi/'+m+'/latex/verifica.pdf)\n'
    text+='\nSorgenti LaTeX, tabelle, grafici e provenienza sono conservati accanto ai PDF.\n'
    (root/'README.md').write_text(text,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-sorgenti',action='store_true',help='Scrive LaTeX e dati senza compilare i PDF')
    parser.add_argument('--output',type=Path,help='Cartella alternativa per le versioni del report')
    parser.add_argument('--mqt-area',type=Path,help='Area MQT separata contenente piano.json, preparazione/ e risultati/; predefinita: prototipo/test_mqt_esplorativo')
    args=parser.parse_args()
    print(build(output_root=args.output,compile_pdf=not args.solo_sorgenti,mqt_area=args.mqt_area))


if __name__=='__main__':
    main()

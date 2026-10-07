'Regenerate individual system reports and comparisons by reading artifacts only.'
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
REPO=HERE.parents[3]
AREA=HERE.parent
SOURCE=REPO/'archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/manifests/source_circuits_v2.json'


def exploratory_notice(run):
    source = run.get('source', {})
    if not source.get('exploratory'):
        return ''
    d = source['details']
    if run['meta']['method'] == 'llm_recupero_random':
        return (f"\\paragraph{{Exploratory extension: five random examples.}} The model selects a device and configuration after receiving five train examples sampled uniformly without replacement from the same compatible candidates as RAG. No Manhattan distance is computed. Aliases E1--E5 follow the sampling order. The retrieval seed is {d['seed']}; the per-circuit seed also depends on the QASM fingerprint. The model still selects the pair: this variant differs from Random, which directly samples a device and configuration.\n\nIt uses Qwen3.5-4B Q8\\_0, temperature 0, a requested context of 60000 tokens and response contract v4. Up to three complete responses are allowed; a single Qiskit compilation is performed per circuit, with seed 0 and a 100-second limit. The actual submitted parameters are preserved in the provenance.\n\nThe variant was added after reviewing the Test. This document describes this single-seed run and does not constitute independent confirmation or a paired comparison with the other systems. Its contract and results remain separate from the original runs.\n\n")
    collection_note = ('The train collection includes 100-second attempts and 300-second recovery attempts. ' if d.get('collection_profile') == 'adaptive-100-then-300-v1' else '')
    return ('\\paragraph{MQT: separate exploratory run.} MQT results come from '+r'\nolinkurl{'+source['area']+f"}}. The comparison including MQT is exploratory and does not complete the evaluation under the original contract. The selector uses {fmt(d.get('training_samples'), 0)} of {fmt(d.get('expected_training_samples'), 0)} planned train samples, with {fmt(d.get('excluded_samples'), 0)} excluded and {fmt(d.get('successful_compilations'), 0)} successful compilations out of {fmt(d.get('required_compilations'), 0)} pairs. The declared collection profile is "+esc(d.get('collection_profile','not declared'))+'. '+collection_note+
        """Classes come from observed winning devices; no artificial classes are added. The same Test circuits, metric and 100-second evaluation limit apply. Training exceptions and the separate contract remain in the provenance; comparisons between the other three systems retain the original plan.

""")


def method_body(output, run):
    m=run['meta']['method']; s=run['summary']; cs=run['circuits']; llm=m.startswith('llm')
    body='\\section{Results for '+esc(run_label(m, run))+'}\n'
    body+=exploratory_notice(run)
    body+=f"Completed: {s['completed_circuits']} of {s['expected_circuits']} planned circuits. "
    body+=f"I {s['episodes']} preserved episodes include {s['successes']} successes and {s['failures']} failures; {s['pending']} circuits are still pending. "
    body+=f"Circuits with at least one success: {s['circuits_with_success']}; circuits with at least one failure: {s['circuits_with_failure']}.\n\n"
    body+="Success means a valid compilation, not correctness of the model's free text. "
    body+="""Scores cover successes; times and costs also include failures when measured.

"""
    body+="""\\subsection{Measurement summary}

"""+metric_table(s)
    body+='Means and medians are computed from available per-circuit means. The known sum covers episodes. '
    body+='The last two columns show circuits and episodes with measurements over their respective denominators. '
    body+="""For scores, the episode denominator is the number of successes.

"""
    partial={k:v['partially_measured_circuits'] for k,v in s['metrics'].items() if v['partially_measured_circuits']}
    if partial:
        body+='Partial per-circuit means are present: '+esc(str(partial))+""". Per-circuit coverage is in the CSV files.

"""
    if s['failure_causes']:
        body+='Failure causes: '+', '.join(esc(k)+f" ({v})" for k,v in sorted(s['failure_causes'].items()))+'.\n\n'
    else:
        body+="""All preserved episodes produced a valid compilation.

"""
    if llm:
        body+=f"Episodes with at least one retry: {s['episodes_with_retry']}/{s['episodes']}. "
        body+=f"Episodes accepted with unverified facts: {s['accepted_with_unverified_facts']}/{s['episodes']}. "
        body+="""Retries repair the response; they do not repeat compilation.

"""
        body+='Retry distribution per episode: '+', '.join(esc(k)+f' retry: {v} episodes' for k,v in s['retry_distribution'].items())+'.\n\n'
        for key,label in [('known_input_tokens','ingresso'),('known_output_tokens','uscita')]:
            v=s[key]
            body+=f"Known partial token sum in {label}: {fmt(v['sum_known'], 0)}, with a counter available in {v['measured_episodes']} episodes. "
        body+="""These counters do not replace complete totals when a measurement is missing.

"""
    body+=f"Scores rounded to zero: {s['rounded_to_zero']}; underflow indicators: {s['underflow']}.\n"
    body+="""\\subsection{Trends across circuits}
Plots follow the alphabetical circuit order in the tables. Each point is the available mean for a circuit; missing measurements are not zeros.

"""
    for metric,caption in [('score','Score of each successful circuit. Missing points are not replaced with zero.'),
                           ('total_seconds','Total time per circuit, including preparation and any failed attempts.'),
                           ('compilation_seconds','Internal compiler time. Timeouts without an internal measurement remain missing.'),
                           ('compilation_process_seconds','Compilation process time: includes startup and checks and shows timeouts.')]:
        metric_plot(output,metric,{m:run},metric)
        body+=figure(metric,caption+' Circuits follow the same alphabetical order as the tables.')
    if llm:
        for metric,caption in [('total_tokens','Cumulative input and output tokens from all calls in the episode.'),
                               ('llm_response_seconds','Cumulative LLM call latency per circuit.')]:
            metric_plot(output,metric,{m:run},metric)
            body+=figure(metric,caption+' With multiple episodes, the mean per circuit is used.')
    body+=r'\FloatBarrier\clearpage'+'\n'+'\\subsection{Per-circuit data}'+'\n'
    body+='Identifiers are sorted lexicographically according to the Test manifest. '
    body+="""Completed episodes, successes and failures are reported. The score is the mean of successes only, to ten decimal places.

"""
    rows=[[esc(c['circuit_id']),c['episodes'],c['successes'],c['failures'],fmt(c['score'],10)] for c in cs]
    body+=table(['Circuit','Episodes','Successes','Failures','Score'],rows,long=True,size='scriptsize')
    body+="""\\subsection{Times per circuit}
All values are means in seconds. -- indicates an unavailable internal measurement, a pending case or a non-applicable measurement.

"""
    headers=['Circuit','Total','Compiler','Process']+(['LLM response'] if llm else [])
    rows=[[esc(c['circuit_id'])]+[fmt(c.get(k)) for k in ('total_seconds','compilation_seconds','compilation_process_seconds')]+([fmt(c.get('llm_response_seconds'))] if llm else []) for c in cs]
    body+=table(headers,rows,long=True,size='footnotesize')
    if llm:
        body+="""\\subsection{Tokens and retries per circuit}
Costs include all attempts in the episode. With replicates, values are means, not sums.

"""
        rows=[[esc(c['circuit_id'])]+[discrete(c.get(k)) for k in ('input_tokens','output_tokens','total_tokens','retries','llm_calls')] for c in cs]
        body+=table(['Circuit','Input','Output','Total','Repairs','Calls'],rows,long=True,size='footnotesize')
    body+='\\begin{samepage}\\subsection{Definizioni e limiti}\n'
    body+='Total time includes the process from the circuit to the measured outcome. LLM response time sums call latencies; '
    body+='internal compilation time is separate from process time. Missing measurements are not zeros. '
    body+='The mean over successes does not demonstrate superiority over another system. Quality is estimated on synthetic Targets. '
    body+="""A single episode does not measure variability between runs. The full comparison documents the procedure, pairing and shared limitations.
\\par\\end{samepage}

"""
    return body


def provenance_body(runs, fingerprint, provenance):
    body='\\FloatBarrier\\section{Provenance and reproduction}'+'\n'
    body+='Analysis identity: '+r'\nolinkurl{'+fingerprint+'}.\n\n'
    body+='The file '+r'\texttt{provenienza.json}'+' preserves fingerprints of the inputs, manifest, contract, configuration, protocol and generator. '
    body+='The directory '+r'\texttt{generatore/}'+' contains a copy of the sources used. '
    body+='CSV tables retain unformatted numerical values and denominators; plots use the same data. '
    body+='The standalone document and thesis fragment are in the directory '+r'\texttt{latex/}'+'.\n\n'
    body+="""To update all reports, from the repository root:

"""+r'\begin{quote}\small\ttfamily .venv/bin/python archivio/valutazione/test/report/genera.py\end{quote}'+'\n'
    body+='The command reads existing outcomes, checks the contract, splits and circuit fingerprints, and reads MQT from the exploratory area when present, keeping its provenance separate. '
    body+="""It does not start the Test or call models. Previous analyses and original outcomes remain preserved.

"""
    return body


def build(area=AREA, output_root=None, compile_pdf=True, mqt_area=None):
    area=Path(area).resolve()
    contract_path=area/'preparazione/contratto_congelato.json'
    contract=read(contract_path)
    plan=read(area/'piano.json')
    if contract['plan']!=plan or plan.get('test_id')!='test-indipendenti-v1':
        raise ValueError('The current plan differs from the contract or is unsupported.')
    if plan['analysis']!={'unit':'circuit','bootstrap_seed':20260901,'bootstrap_draws':10000,'confidence':0.95,'comparisons':['llm_rag vs llm_senza_rag','llm_rag vs mqt_predictor','llm_rag vs random'],'quality_population':'common successful circuits; failures reported separately','confirmatory_tests':'none; descriptive paired intervals, no superiority claim from incomplete comparison'}:
        raise ValueError('Unsupported analysis plan: update the documentation as well.')
    if sha(SOURCE)!=contract['source_sha256']:
        raise ValueError('Manifest differs from the frozen source.')
    expected={r['circuit_id']:r['source_sha256'] for r in read(SOURCE)['circuits'] if r['split']=='test'}
    if len(expected)!=plan['circuits']:
        raise ValueError('Inconsistent Test size.')
    runs=load_sources(area,expected,contract,mqt_area=mqt_area)
    if not runs:
        raise ValueError('No Test records available.')
    # Read selector metadata without loading the model.
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
        # A completed version is immutable, even if it contained sources only.
        output=output_root/(fingerprint[:16]+('-pdf' if compile_pdf else '-sorgenti'))
        if (output/'completato.json').exists():
            raise ValueError('Completed artifacts have changed or the variant is occupied: use --output with a new directory.')
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
        print('Report '+LABELS[method],flush=True)
        body=method_body(dest,run)+provenance_body({method:run},fingerprint,provenance)
        compile_document(dest,'Test: '+run_label(method, run),body,compile_pdf)
    dest=output/'confronto'
    write_csv(dest/'tabelle/circuiti_tutti_sistemi.csv',all_circuits)
    write_json(dest/'tabelle/riepiloghi.json',{m:r['summary'] for m,r in runs.items()})
    write_json(dest/'tabelle/confronti_appaiati.json',comparison)
    write_csv(dest/'tabelle/differenze_appaiate.csv',[dict(other_method=m,**row) for m,p in comparison['pairs'].items() for row in p['differences']],['other_method','circuit_id','difference'])
    print('Overall report',flush=True)
    body=comparison_body(dest,runs,comparison,plan)
    compile_document(dest,'System comparison on the Test',body,compile_pdf)
    # Check that no input changed during generation.
    for method,run in runs.items():
        base=Path(run['source']['base'])
        for path, fingerprint_before in run['source']['supporting_files'].items():
            if sha(Path(path)) != fingerprint_before:
                raise RuntimeError('Source contract or plan changed during generation: '+path)
        current={str(p.relative_to(base)):sha(p) for folder in ('circuiti','sessioni') for p in sorted((base/folder).rglob('*.json'))}
        current['esecuzione.json']=sha(base/'esecuzione.json')
        if current!=run['input_files']:
            raise RuntimeError('Inputs changed during generation: '+method+'. Rerun after writes have finished.')
    output_hashes={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='completato.json'}
    write_json(output/'completato.json',dict(at=datetime.now(timezone.utc).isoformat(),fingerprint=fingerprint,pdf_available=compile_pdf,outputs=output_hashes))
    publish_latest(output_root,output,runs)
    return output


def publish_latest(root,output,runs):
    value={'directory':str(output),'comparison_pdf':str(output/'confronto/latex/verifica.pdf'),
           'system_pdfs':{m:str(output/'sistemi'/m/'latex/verifica.pdf') for m in runs}}
    tmp=root/'ultimo.tmp.json';write_json(tmp,value);tmp.replace(root/'ultimo.json')
    text="""# Test report

Latest analysis: `"""+output.name+'`.\n\n'
    text+='- [Overall report]('+output.name+'/confronto/latex/verifica.pdf)\n'
    for m in runs:
        text+='- ['+run_label(m,runs[m])+']('+output.name+'/sistemi/'+m+'/latex/verifica.pdf)\n'
    text+="""
LaTeX sources, tables, plots and provenance are preserved alongside the PDFs.

"""
    (root/'README.md').write_text(text,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-sorgenti',action='store_true',help='Write LaTeX and data without compiling PDFs')
    parser.add_argument('--output',type=Path,help='Alternative directory for report versions')
    parser.add_argument('--mqt-area',type=Path,help='Separate MQT area containing piano.json, preparazione/ and risultati/; default: archivio/valutazione/test_mqt_esplorativo')
    args=parser.parse_args()
    print(build(output_root=args.output,compile_pdf=not args.solo_sorgenti,mqt_area=args.mqt_area))


if __name__=='__main__':
    main()

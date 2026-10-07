'Final-comparison narrative and tables derived from preserved outcomes.'
from pathlib import Path
from dati import METHODS, number
from impaginazione import esc, fmt, table
from pannelli import PANEL_LABELS, threshold_counts, metric_grid, reliability_grid, threshold_grid, ecdf_grid, figure_page, method_order

HERE=Path(__file__).resolve().parent


def label(method, runs):
    value=PANEL_LABELS[method]
    if runs.get(method,{}).get('source',{}).get('exploratory'):
        value+=' (expl.)'
    return esc(value)


def discrete(value):
    # A noninteger replicate mean remains a mean; do not truncate it.
    if number(value) and float(value).is_integer():
        return fmt(value,0)
    return fmt(value,2)


def headers(methods, runs):
    values={'llm_rag':r'\shortstack{LLM +\\RAG}',
            'llm_senza_rag':r'\shortstack{LLM no\\RAG}',
            'mqt_predictor':r'\shortstack{MQT\\Predictor}',
            'random':'Random', 'llm_recupero_random':r'\shortstack{LLM +\\Random\\RAG\\(espl.)}'}
    if runs.get('mqt_predictor',{}).get('source',{}).get('exploratory'):
        values['mqt_predictor']=r'\shortstack{MQT\\Predictor\\(espl.)}'
    return [values[m] for m in methods]


def matrix(rows, runs, methods=None):
    methods=methods or [m for m in method_order(runs) if m in runs]
    # Use full names and consistent column positions in each summary.
    spec=r'>{\raggedright\arraybackslash}p{5.0cm}' + r'>{\centering\arraybackslash}p{1.9cm}'*len(methods) if len(methods)==5 else r'>{\raggedright\arraybackslash}p{5.8cm}' + r'>{\centering\arraybackslash}p{2.2cm}'*len(methods)
    return table(['Measurement']+headers(methods,runs),rows,spec=spec,size='small')


def mqt_details(runs):
    run=runs.get('mqt_predictor',{})
    if not run:
        return """MQT results are not yet available in this version.

"""
    detail=''
    md=run.get('report_model_metadata',{})
    classifier=md.get('classifier',{})
    if classifier:
        detail+=('The selector is a Random Forest with '+str(classifier['n_estimators'])+
                 ' trees, balanced class weights, seed '+str(classifier['random_state'])+
                 ' e '+str(classifier['n_jobs'])+' processes. ')
        if classifier.get('hyperparameter_search') is False:
            detail+='These parameters were fixed without validation hyperparameter search. '
        detail+='\n\n'
    source=run.get('source',{})
    if source.get('exploratory'):
        d=source['details']
        detail+=(f"\\textbf{{The MQT run reported here is exploratory.}} Its selector uses {d['training_samples']} of {d['expected_training_samples']} planned train samples; {d['excluded_samples']} are excluded. Collection contains {d['successful_compilations']} successful compilations out of {d['required_compilations']} expected pairs. ")
        if md.get('learned_classes'):
            detail+=f"The learned classes are {len(md['learned_classes'])}: Falcon 127, Heron 133, Heron 156 and Quantinuum H2-56. Falcon 27 does not appear among the Training set winners, although it has its own RL policy. "
        detail+=("""Collection includes 100-second attempts and 300-second recovery runs, whereas Test retains 100 seconds and original RL behavior. This separate-contract run does not complete the original-contract evaluation. Interpret MQT comparison within that limit; the other three systems retain the original plan.

""")
    return detail


def summary_tables(runs, comparison, plan):
    methods=[m for m in method_order(runs) if m in runs]
    summaries={m:r['summary'] for m,r in runs.items()}
    def count(key):return [s[key] for s in (summaries[m] for m in methods)]
    def stat(key,which='mean',digits=3):
        return [fmt(summaries[m]['metrics'].get(key,{}).get(which),digits) for m in methods]
    body='\\clearpage\\section{Results}'+'\n'+'\\subsection{Success and quality: aggregate results}'+'\n'
    body+=("""Tables first summarize the main results, giving each circuit equal weight. Mean score includes only successful compilations: changing success counts also changes the evaluated set. Failures are not assigned zero scores. Direct quality comparison therefore uses circuits successful for both systems.

""")
    rows=[['Expected circuits']+count('expected_circuits'),['Completed circuits']+count('completed_circuits'),
          ['Successful compilations']+count('successes'),['Failures']+count('failures'),['Pending circuits']+count('pending'),
          ['Mean score on successful compilations']+stat('score',digits=6),
          ['Median score on successful compilations']+stat('score','median',6)]
    body+=matrix(rows,runs)
    thresholds={m:threshold_counts(runs[m]) for m in methods}
    body+=("""The 0.8 threshold adds another view: how many planned circuits yield valid compilations at or above that score. The denominator includes failures; missing scores remain separate from below-threshold successes. This descriptive threshold was added for the report, not chosen before Test.

""")
    body+=matrix([
        ['Circuits with score $\\geq 0{,}8$']+[f"{thresholds[m]['high']}/{thresholds[m]['total']}" for m in methods],
        ['Percentage of Test circuits']+[fmt(100*thresholds[m]['high']/thresholds[m]['total'],1)+r'\%' if thresholds[m]['total'] else '--' for m in methods]
    ],runs)
    failures=[label(m,runs)+': '+str(summaries[m]['failures']) for m in methods if summaries[m]['failures']]
    if failures:
        body+='The observed failures are '+', '.join(failures)+'. '
        if all(set(summaries[m]['failure_causes']) <= {'process_timeout'} for m in methods):
            body+='In every such case, the process exceeded its time limit. '
    body+="""Details and missing measurements remain visible in the appendix.
"""

    body+='\\clearpage\\subsection{Time and response costs}'+'\n'
    body+=("""Total time covers input circuit to outcome, including selection, responses, repairs and compilation. Internal time measures compiler work only; process time includes startup and checks. Measured timeouts enter total/process time but receive no invented internal duration.

""")
    rows=[]
    for key,title in [('total_seconds','Total time'),('compilation_seconds','Internal compilation'),
                      ('compilation_process_seconds','Compilation process'),('choice_seconds','Preparation and selection')]:
        rows.extend([[title+' mean (s)']+stat(key,digits=2),
                     [title+' median (s)']+stat(key,'median',2),
                     ['Circuits with measurements']+[f"{summaries[m]['metrics'][key]['n']}/{summaries[m]['completed_circuits']}" for m in methods]])
    body+=matrix(rows,runs)
    llms=[m for m in methods if m.startswith('llm')]
    if llms:
        body+=("""Tokens sum input/output of every call, including repairs. A repair is an additional model request, not a new compilation. These costs do not apply to MQT or Random.

""")
        rows=[]
        for key,title in [('input_tokens','Input tokens'),('output_tokens','Output tokens'),
                          ('total_tokens','Total tokens'),('llm_calls','Calls'),('retries','Repairs')]:
            rows.append([title+' (sum)']+[discrete(summaries[m]['metrics'][key]['sum_known']) for m in llms])
        rows.append(['Circuits with repairs']+[summaries[m]['episodes_with_retry'] for m in llms])
        rows.append(['Accepted with unverified facts']+[summaries[m]['accepted_with_unverified_facts'] for m in llms])
        rows.append(['Mean response time (s)']+[fmt(summaries[m]['metrics']['llm_response_seconds']['mean']) for m in llms])
        rows.append(['Circuits with token measurements']+[f"{summaries[m]['metrics']['total_tokens']['n']}/{summaries[m]['completed_circuits']}" for m in llms])
        body+=matrix(rows,runs,llms)
        body+="""Non-integer count means remain means; actual counts are shown as integers.

"""

    body+='\\clearpage\\subsection{Comparisons on the same circuits}'+'\n'
    body+=("""Each LLM + RAG comparison uses circuits with scores available for both systems. Difference is RAG minus the other system; positive means higher estimated quality for RAG. This does not replace failure counts.

""")
    pairs=comparison['pairs'];others=[m for m in method_order(runs) if m in pairs]
    spec=r'>{\raggedright\arraybackslash}p{5.0cm}'+r'>{\centering\arraybackslash}p{2.4cm}'*len(others)
    rows=[
        ['Shared successful circuits']+[pairs[m]['n'] for m in others],
        ['Mean LLM + RAG score']+[fmt(pairs[m]['mean_left'],6) for m in others],
        ['Mean score of the column system']+[fmt(pairs[m]['mean_right'],6) for m in others],
        ['Mean difference (RAG minus other)']+[fmt(pairs[m]['mean_difference'],6) for m in others],
        ['Lower bound, 95\\% interval']+[fmt(pairs[m]['paired_bootstrap_95'][0],6) if pairs[m]['paired_bootstrap_95'] else '--' for m in others],
        ['Upper bound, 95\\% interval']+[fmt(pairs[m]['paired_bootstrap_95'][1],6) if pairs[m]['paired_bootstrap_95'] else '--' for m in others],
        ['RAG has a higher score']+[pairs[m]['wins'] for m in others],
        ['Equal score']+[pairs[m]['ties'] for m in others],
        ['RAG has a lower score']+[pairs[m]['losses'] for m in others]]
    if others:
        body+=table(['Comparison with LLM + RAG']+headers(others,runs),rows,spec=spec,size='small')
    body+=(f"The interval describes variation across observed circuits: it uses {plan['analysis']['bootstrap_draws']} pair resamples with seed {plan['analysis']['bootstrap_seed']} and percentiles 2.5 and 97.5. This is neither a confirmatory superiority test nor a measure of variability across new runs.\n\n")
    common=len(comparison['all_common_successes'])
    body+=f'Common successes across all available systems: {common}. Means on this same set are:\n\n'
    body+=matrix([['Mean score on shared successes']+[fmt(comparison['all_common_means'].get(m),6) for m in methods]],runs)
    body+=("""Plots keep LLM + RAG top-left, no-RAG LLM top-right, MQT bottom-left and Random bottom-right. Per-circuit horizontal positions follow appendix alphabetical order. Four panels share axis scales; missing measurements are not zero.

""")
    if 'llm_recupero_random' in runs:
        body=body.replace('MQT at the bottom left and Random at the bottom right.',
            'MQT on the left of the second row, Random on the right of the second row and LLM + Random RAG centered in the third row.')
        body=body.replace('in the four panels','in the five panels')
        body+="""Random-example comparison is exploratory: it was added after Test inspection with one retrieval seed.

"""
    return body


def chart_pages(output,runs):
    s={m:r['summary'] for m,r in runs.items()}
    def page(*args):
        return figure_page(*args, five='llm_recupero_random' in runs)
    body=''
    reliability_grid(output,runs)
    text=('Success means reaching a valid compiled circuit. Bars distinguish successes, failures and pending cases across all planned circuits, including those excluded from score means.')
    if all(m in s for m in METHODS):
        text+=f" The two LLM systems complete {s['llm_rag']['successes']} e {s['llm_senza_rag']['successes']} compilations; MQT completes {s['mqt_predictor']['successes']} and Random {s['random']['successes']}."
    if 'llm_recupero_random' in s:
        text+=f" LLM + Random RAG completes {s['llm_recupero_random']['successes']} compilations."
    body+=page('esiti','Circuits reaching valid compilation',text,
                      'Success over planned circuits. MQT denotes the exploratory run where the panel specifies it.')
    threshold_grid(output,runs)
    counts={m:threshold_counts(r) for m,r in runs.items()}
    text=('Each pie represents the whole Test with '+str(next(iter(counts.values()))['total'])+
          ' circuits. Blue means score at least 0.8; orange means lower score; gray means no score. Pending cases, if any, are separate. Quality and coverage thus share a denominator. ')
    text+='; '.join(PANEL_LABELS[m]+f": {c['high']}/{c['total']}" for m,c in counts.items())+'.'
    body+=page('soglia_score_080','Circuits reaching score at least 0.8',text,
                      'Percentages of planned circuits without assigning failure scores. The threshold is descriptive.')
    charts=[
        ('score','Compilation quality','Score',
         "Each point is one successful circuit's score. Four panels show distributions without overlapping systems. Missing points mean unavailable scores, not zero quality. Use the earlier paired tables to count how often RAG improves a choice.",
         'Scores on successful compilations; shared scale from 0 to 1.'),
        ('total_seconds','Time to reach an outcome','Total time (s)',
         "Total time is each circuit's observed execution cost, including failures. Near-timeout cases show costly waits. Mean and median distinguish aggregate from typical-circuit cost.",
         'Measured total seconds, including failed cases.'),
        ('compilation_seconds','Compiler time','Internal compilation (s)',
         "This isolates the compiler's internal time, excluding device selection and the LLM response. This measurement may be missing when an external timeout stops the process. Missing MQT and Random points must therefore not be read as instantaneous compilations or compared as though all systems completed the same cases.",
         'Internal duration for available measurements only; timeouts without a measurement remain missing.'),
        ('compilation_process_seconds','Compilation process duration','Compilation process (s)',
         'The process includes startup, compiler work and final checks. Unlike the internal measurement, this duration also shows externally recorded timeouts. The difference from the previous plot helps show the impact of cases that do not produce a valid compilation.',
         'Process duration in seconds, including measured timeouts.'),
        ('total_tokens','Text volume processed by the LLMs','Total tokens',
         'The count sums input and output tokens from all calls for the same circuit. RAG examples increase the input text; repair requests add further calls. Tokens describe the volume of processed text, not a monetary cost. This measurement does not apply to MQT or Random.',
         'Total tokens per circuit; non-applicable cells retain their expected positions.'),
        ('llm_response_seconds','Waiting for LLM responses','Response time (s)',
         'For each circuit, we sum the time between sending each request and receiving its complete LLM response. The plot separates this wait from compilation and example retrieval. RAG is associated with slower responses on average in this run, but the Test does not attribute the entire difference to a single cause.',
         'Cumulative response time in seconds; no LLM measurement for MQT or Random.'),
        ('retries','Repair requests before compilation','Repairs',
         "A repair is a call after the first call for the same case. It seeks an acceptable response and does not repeat quantum compilation. Peaks show where calls increase, together with tokens and waiting time. Successful compilation does not certify the model's free-text explanation.",
         'Repairs per circuit; zero means the first response was sufficient.')
    ]
    if 'llm_rag' in s and 'llm_senza_rag' in s:
        a=s['llm_rag']['metrics']['total_seconds']['mean'];b=s['llm_senza_rag']['metrics']['total_seconds']['mean']
        if number(a) and number(b) and b:
            charts[1]=(charts[1][0],charts[1][1],charts[1][2],
                       charts[1][3]+f' RAG takes an average of {fmt(a)} s compared with {fmt(b)} s without examples: approximately {fmt(a / b)} times as much.',
                       charts[1][4])
    for metric,title,ylabel,prose,caption in charts:
        if metric in ('total_tokens','llm_response_seconds','retries') and not any(m.startswith('llm') for m in runs):
            continue
        metric_grid(output,runs,metric,ylabel)
        if 'llm_recupero_random' in runs:
            prose=prose.replace('four panels','five panels')
        body+=page(metric,title,prose,caption)
    ecdf_grid(output,runs)
    body+=page('distribuzione_score','Score distributions',
         'The curve gives the proportion of successful compilations with scores no greater than the horizontal value. A rise near 1 indicates many high estimated-quality results. Each panel uses its own successes, with potentially different denominators shown on axes. This describes distribution shape and does not replace same-circuit comparison.',
         'Cumulative distributions on successes with shared scales.')
    return body


def conclusions(runs, comparison):
    body=r'\clearpage\section{Conclusioni}'+'\n'
    pairs=comparison['pairs']
    if 'llm_senza_rag' in pairs and 'random' in pairs:
        a,b=pairs['llm_senza_rag'],pairs['random']
        positive=a['wins']>a['n']/2 and b['wins']>b['n']/2
        body+=('The outcome supports the goal of using compilation examples to assist the LLM. '
               if positive else "Paired comparisons allow us to assess the examples' contribution to the LLM. ")
        body+=(f"LLM + RAG achieves a higher score in {a['wins']} of {a['n']} comparisons with LLM no RAG and in {b['wins']} of the {b['n']} comparisons with Random. ")
        if positive:
            body+='The examples therefore improve estimated quality in most observed comparisons. '
        body+="""This concerns comparable circuits and must be read alongside separately reported failures.

"""
    s={m:r['summary'] for m,r in runs.items()}
    if 'mqt_predictor' in pairs:
        p=pairs['mqt_predictor'];a=s['llm_rag'];b=s['mqt_predictor']
        body+=(f"On the {p['n']} shared successes, RAG has a mean score of {fmt(p['mean_left'], 4)} and MQT {fmt(p['mean_right'], 4)}. However, RAG produces {a['successes']} valid compilations out of {a['expected_circuits']} circuits, compared with {b['successes']} for MQT. ")
        if a['successes']>b['successes']:
            body+='It therefore offers greater coverage in the observed sample. '
        body+="""Success on every observed case, where achieved, suggests practical reliability but does not guarantee every future circuit.

"""
        ta=a['metrics']['total_seconds'];tb=b['metrics']['total_seconds']
        body+=(f"Mean total time also differs: {fmt(ta['mean'])} s for RAG and {fmt(tb['mean'])} s for MQT. The median is {fmt(ta['median'])} s for RAG and {fmt(tb['median'])} s for MQT. It is therefore appropriate to describe mean cost and the effect of timeouts without extending this ranking to every circuit or every timing statistic. ")
        if runs['mqt_predictor']['source'].get('exploratory'):
            body+='These MQT results also come from the exploratory run with an incomplete Training set described in the second section.'
        body+='\n\n'
    if 'llm_rag' in s and 'llm_senza_rag' in s:
        a=s['llm_rag']['metrics']['total_seconds']['mean'];b=s['llm_senza_rag']['metrics']['total_seconds']['mean']
        if number(a) and number(b) and b:
            body+=(f"The improvement over the model without examples has a cost: RAG's mean time is {fmt(a / b)} times that of LLM no RAG. Examples, repairs and the selected compilations contribute to the overall process. The Test shows this tradeoff without experimentally isolating each component's causal contribution.\n\n")
    body+=("""LLM + RAG currently chooses from twelve Qiskit configurations. Expanding the catalog and Dataset might include better compilation examples, but this is unproven and would increase collection cost and selection complexity.
Expected fidelity is integrated into MQT and is its policy-training objective. This alignment between training and evaluation helps contextualize results. The same metric evaluates every system and Qiskit example; its origin alone does not demonstrate bias. Other metrics or physical-hardware tests could rank systems differently.
Preparation is also relevant: LLM + RAG reuses an existing LLM and builds examples from Qiskit compilation without device-specific RL training. MQT needs RL policies and a supervised Training set. This reduces approach-specific training requirements, but Test timing does not measure either full preparation cost. Simpler preparation is supported; unmeasured numerical savings are not. Within this scope, LLM + RAG is promising for combining decision quality and compilation coverage.

""")
    if 'llm_recupero_random' in runs:
        from estensione_random import conclusion
        body+=conclusion(runs['llm_recupero_random']['comparison_detail'])
    body+=r'\clearpage'+(HERE/'limiti.tex').read_text(encoding='utf-8-sig')
    return body


def circuit_appendix(runs):
    body='\\clearpage\\appendix\\section{Per-circuit statistics}'+'\n'
    body+=("""Tables give full circuit names in plot alphabetical order and retain system names. Separate measurement tables avoid crowded columns. All times are seconds; tokens, calls and repairs are counts. -- means missing data; LLM measurements do not apply to MQT or Random.
The plan has one episode per circuit. If replicates exist, measurements are first averaged per circuit, with score restricted to successes; non-integer means stay non-integer. CSV retains complete values and coverage for every measurement.

""")
    methods=[m for m in method_order(runs) if m in runs]
    maps={m:{c['circuit_id']:c for c in r['circuits']} for m,r in runs.items()}
    ids=sorted(set.union(*(set(v) for v in maps.values())))
    definitions=[
        ('status','Compilation outcome','Successful means a valid compilation; failed means a terminal outcome without a result. Pending and mixed cases are explicit.'),
        ('score','Score','Scores of successful compilations, shown to six decimal places for readability. CSV files preserve ten decimal places. A failure is not a zero score.'),
        ('total_seconds','Total time (seconds)','Includes the path from the circuit to the outcome, including any repairs and failures.'),
        ('compilation_seconds','Internal compiler time (seconds)','A measurement missing after a timeout remains -- and is not replaced with 100 seconds.'),
        ('compilation_process_seconds','Compilation process time (seconds)','Includes startup, compilation and checks, including measured timeouts.'),
        ('choice_seconds','Preparation and selection (seconds)','Time before compilation, according to the measurement preserved by the system.'),
        ('input_tokens','Input tokens','Input tokens summed across all calls for the case.'),
        ('output_tokens','Output tokens','Output tokens summed across all calls for the case.'),
        ('total_tokens','Total tokens','Input plus output, including repair requests.'),
        ('llm_response_seconds','LLM response time (seconds)','Sum of waits for complete responses.'),
        ('retries','Repair requests','Additional calls after the first, before the single planned compilation.'),
        ('llm_calls','Number of LLM calls','Includes the first response and any repairs.'),
        ('rag_seconds','Example retrieval time (seconds)','Recorded retrieval time. Retrieval is disabled for LLM no RAG.')]
    for key,title,description in definitions:
        cols=methods if key in ('status','score','total_seconds','compilation_seconds','compilation_process_seconds','choice_seconds') else [m for m in methods if m.startswith('llm')]
        if not cols:continue
        body+=(r'\clearpage' if key!='status' else '')+r'\subsection{'+title+'}\n'+description+'\n'
        rows=[]
        for cid in ids:
            row=[r'\nolinkurl{'+cid+'}']
            for m in cols:
                c=maps[m].get(cid,{})
                if key=='status':
                    value={'success':'Successful','failure':'Failed','pending':'Pending','mixed':'Mixed'}.get(c.get(key),'--')
                elif key in ('input_tokens','output_tokens','total_tokens','retries','llm_calls'):
                    value=discrete(c.get(key))
                else:
                    value=fmt(c.get(key),6 if key=='score' else 3)
                row.append(value)
            rows.append(row)
        spec=r'>{\raggedright\arraybackslash}p{6.0cm}'+r'>{\centering\arraybackslash}p{1.75cm}'*len(cols)
        body+=table(['Circuit']+headers(cols,runs),rows,spec=spec,long=True,size='small')
    body+='\\clearpage\\section{Sources and interpretation criteria}'+'\n'
    body+=("""This document is derived from records of completed runs. Regeneration checks circuit identities and contracts without starting models or new quantum compilations. Previous reports and original outcomes remain preserved.

The current protocol is in """+r'\nolinkurl{prototipo/docs/protocollo_sperimentale.md}'+
           '. LLM settings are in '+r'\nolinkurl{prototipo/config.json}'+
           '. The separate MQT run preserves its own plan, contract and selector metadata in the directory '+r'\nolinkurl{archivio/valutazione/test_mqt_esplorativo/}'+""".

Alongside the document, """+r'\texttt{provenienza.json}'+
           ' collects versions, fingerprints, submitted parameters and source references. The directory '+r'\texttt{generatore/}'+
           """ preserves the sources used; table and plot directories contain the data behind figures. These details support reconstruction without burdening the main text.
Quality comparisons use common successful circuits. Costs include every outcome with available measurements. Sums concern observed episodes; means give circuits equal weight. Unknown measurements remain missing, not zero. Input-token counts include the full text even when the server reuses cache.
The local MQT architecture reference is \\nolinkurl{archivio/esperimento_v2/knowledge/MQT-Predictor.pdf}, the 2025 work. The 2023 paper predicts compilation options and must not be confused with this ML/RL sequence.

""")
    return body


def comparison_body(output,runs,comparison,plan):
    (output/'grafici').mkdir(parents=True,exist_ok=True)
    five='llm_recupero_random' in runs
    body=(HERE/('introduzione_cinque.tex' if five else 'introduzione.tex')).read_text(encoding='utf-8-sig')
    if comparison['missing_methods']:
        body+="""
Results not yet available: """+', '.join(PANEL_LABELS[m] for m in comparison['missing_methods'])+""". The comparison is partial.
"""
    body+=r'\clearpage'+'\n'+(HERE/('procedura_cinque.tex' if five else 'procedura.tex')).read_text(encoding='utf-8-sig').replace('%%MQT_DETAILS%%',mqt_details(runs).replace('the other three systems','the three systems in the original plan'))
    body+=summary_tables(runs,comparison,plan)
    body+=chart_pages(output,runs)
    body+=conclusions(runs,comparison)
    body+=circuit_appendix(runs)
    if five:
        body=body.replace('The best of the four observed systems','The best of the five observed systems')
        body+=("""
The random-example campaign and separate contract are under \\nolinkurl{archivio/valutazione/test/recupero_random/seed_20260927/}. Qubit groups and differences derive from the manifest and preserved outcomes.

""")
    return body


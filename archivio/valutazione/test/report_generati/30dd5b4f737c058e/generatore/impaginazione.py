"""Tabelle e figure PGFPlots: sorgenti leggibili, nessun servizio esterno."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from dati import LABELS, number, write_csv, run_label

COLORS = {'llm_rag':'blue!75!black','llm_senza_rag':'orange!85!black','mqt_predictor':'violet','random':'teal!80!black'}
MARKERS = {'llm_rag':'*','llm_senza_rag':'triangle*','mqt_predictor':'square*','random':'diamond*'}
METRIC_LABELS = {'score':'Expected fidelity', 'total_seconds':'Tempo totale (s)',
 'compilation_seconds':'Compilazione interna (s)', 'compilation_process_seconds':'Processo di compilazione (s)',
 'choice_seconds':'Preparazione e scelta (s)', 'llm_response_seconds':'Risposta LLM cumulativa (s)',
 'total_tokens':'Token totali', 'input_tokens':'Token in ingresso', 'output_tokens':'Token in uscita',
 'retries':'Retry LLM', 'llm_calls':'Chiamate LLM', 'rag_seconds':'Recupero RAG (s)'}


def esc(value):
    replacements={'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#',
                  '{':r'\{','}':r'\}','$':r'\$','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(replacements.get(c,c) for c in str(value))


def fmt(value, digits=2):
    if not number(value):
        return '--'
    return f'{value:,.{digits}f}'.replace(',','X').replace('.',',').replace('X',r'\,')


def table(headers, rows, spec=None, long=False, size='small'):
    spec=spec or ('l'+'r'*(len(headers)-1))
    env='longtable' if long else 'tabular'
    head=' & '.join(headers)+r' \\'+'\n'
    text='\\begingroup\\'+size+'\n\\setlength{\\tabcolsep}{5pt}\n'
    if not long:
        text+=r'\begin{center}'+'\n'
    text+='\\begin{'+env+'}{'+spec+'}\n'+r'\toprule'+'\n'+head+r'\midrule'+'\n'
    if long:
        text+=r'\endfirsthead'+'\n'+r'\toprule'+'\n'+head+r'\midrule\endhead'+'\n'
        text+='\\midrule\\multicolumn{'+str(len(headers))+'}{r}{\\footnotesize Segue nella pagina successiva}\\\\\n'+r'\endfoot'+'\n'+r'\bottomrule\endlastfoot'+'\n'
    text+='\n'.join(' & '.join(str(c) for c in row)+r' \\' for row in rows)+'\n'
    if not long:
        text+=r'\bottomrule'+'\n'
    text+='\\end{'+env+'}\n'
    if not long:
        text+=r'\end{center}'+'\n'
    return text+r'\endgroup'+'\n'


def figure(stem, caption):
    return '\n'+r'\begin{figure}[!htbp]\centering'+'\n'+r'\input{\TestReportPath grafici/'+stem+'.tex}\n'+r'\caption{'+caption+'}\n'+r'\end{figure}'+'\n'


def plot(output, stem, series, ylabel, xlabel='Indice del circuito', options='', coordinates=False):
    """series: (method, legend, [(x,y),...]); scrive anche tutti i dati CSV."""
    folder=output/'grafici'
    folder.mkdir(parents=True,exist_ok=True)
    text=r'\begin{tikzpicture}\begin{axis}['+'\n'
    text+=r'width=0.96\linewidth,height=6.2cm,grid=major,grid style={gray!20},tick label style={font=\small},label style={font=\small},'+'\n'
    text+='xlabel={'+xlabel+'},ylabel={'+ylabel+'},\n'
    text+=r'legend style={at={(0.5,1.03)},anchor=south,draw=none,column sep=8pt,font=\small},legend columns=2,unbounded coords=discard,'+'\n'
    text+=options+']\n'
    for i,(method,label,points) in enumerate(series):
        path=folder/f'{stem}_{i}.csv'
        write_csv(path,[{'x':x,'y':y} for x,y in points],['x','y'])
        # Non creare legende ingannevoli per popolazioni prive di misure.
        if not points:
            continue
        style=f"color={COLORS[method]},mark={MARKERS[method]},mark size=1.3pt"
        style+=',thick,no marks,const plot' if coordinates else ',only marks'
        text+='\\addplot['+style+'] table[x=x,y=y,col sep=comma]{\\TestReportPath grafici/'+path.name+'};\n'
        text+='\\addlegendentry{'+esc(label)+'}\n'
    text+=r'\end{axis}\end{tikzpicture}'+'\n'
    (folder/(stem+'.tex')).write_text(text,encoding='utf-8')


def metric_plot(output, stem, runs, metric):
    series=[(m,run_label(m,run),[(c['index'],c[metric]) for c in run['circuits'] if number(c.get(metric))]) for m,run in runs.items()]
    opts='ymin=0,ymax=1.02,' if metric=='score' else 'ymin=0,'
    max_index=max((c['index'] for run in runs.values() for c in run['circuits']),default=1)
    plot(output,stem,series,METRIC_LABELS[metric],options=opts+f'xmin=0,xmax={max_index+1},')


def reliability_plot(output, runs):
    methods=list(runs)
    folder=output/'grafici'; folder.mkdir(parents=True,exist_ok=True)
    rows=[dict(index=i,success=run['summary']['successes'],failure=run['summary']['failures']) for i,run in enumerate(runs.values(),1)]
    write_csv(folder/'esiti.csv',rows)
    ticks=','.join(str(i) for i in range(1,len(methods)+1))
    labels=','.join('{'+esc(run_label(m,runs[m]))+'}' for m in methods)
    text=r'\begin{tikzpicture}\begin{axis}[width=0.96\linewidth,height=5.5cm,ybar stacked,bar width=24pt,ymin=0,enlarge x limits=0.25,'
    text+='xtick={'+ticks+'},xticklabels={'+labels+'},'
    text+=r'ylabel={Episodi},nodes near coords,legend style={at={(0.5,1.03)},anchor=south,draw=none,column sep=8pt},legend columns=2,tick label style={font=\small}]'+'\n'
    for column,color,label in [('success','blue!65','Successi'),('failure','orange!85','Fallimenti')]:
        text+='\\addplot[fill='+color+'] table[x=index,y='+column+',col sep=comma]{\\TestReportPath grafici/esiti.csv};\n\\addlegendentry{'+label+'}\n'
    text+=r'\end{axis}\end{tikzpicture}'+'\n'
    (folder/'esiti.tex').write_text(text,encoding='utf-8')


def ecdf_plot(output, runs):
    series=[]
    for method,run in runs.items():
        vals=sorted(c['score'] for c in run['circuits'] if number(c.get('score')))
        series.append((method,run_label(method,run)+f' (n={len(vals)})',[(v,(i+1)/len(vals)) for i,v in enumerate(vals)]))
    plot(output,'distribuzione_score',series,'Quota cumulativa',xlabel='Expected fidelity',options='xmin=0,xmax=1,ymin=0,ymax=1,',coordinates=True)


def retry_plot(output, run):
    points=[(c['index'],c['retries']) for c in run['circuits'] if number(c.get('retries'))]
    method=run['meta']['method']
    plot(output,'retry',[(method,LABELS[method],points)],'Retry medi per episodio',options='ymin=0,ymax=2.2,ytick={0,1,2},')


def metric_table(summary, include_score=True):
    rows=[]
    for key,s in summary['metrics'].items():
        if key=='score' and not include_score:
            continue
        total='--' if key=='score' else fmt(s['sum_known'],0 if key in ('retries','llm_calls','input_tokens','output_tokens','total_tokens') else 2)
        rows.append([METRIC_LABELS[key],fmt(s['mean'],6 if key=='score' else 2),fmt(s['median'],6 if key=='score' else 2),total,
                     f"{s['n']}/{summary['completed_circuits']}",f"{s['measured_episodes']}/{s['measured_episodes']+s['missing_episodes']}"])
    return table(['Misura','Media','Mediana','Somma nota','Circuiti','Episodi'],rows,size='footnotesize')


def compile_document(output, title, body, compile_pdf=True):
    latex=output/'latex'; latex.mkdir(parents=True,exist_ok=True)
    preamble=r'''\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[italian]{babel}
\usepackage[margin=2cm]{geometry}
\usepackage{graphicx,booktabs,longtable,amsmath,placeins,array,pdflscape,caption}
\usepackage[expansion=false]{microtype}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{xurl}
\usepackage[hidelinks]{hyperref}
\setlength{\emergencystretch}{3em}
\setlength{\parskip}{3pt}
\captionsetup{font=small,labelfont=bf}
\widowpenalty=10000
\clubpenalty=10000
'''
    (latex/'preambolo.tex').write_text(preamble,encoding='utf-8')
    (latex/'risultati.tex').write_text(r'\providecommand{\TestReportPath}{../}'+'\n'+body,encoding='utf-8')
    standalone=r'\documentclass[11pt,a4paper]{article}'+'\n'+r'\input{preambolo.tex}'+'\n'+r'\title{'+esc(title)+'}\n'+r'\author{Confronto sperimentale sui circuiti Test}'+'\n'+r'\date{Analisi dei risultati conservati}'+'\n'+r'\begin{document}\maketitle'+'\n'+r'\input{risultati.tex}'+'\n'+r'\end{document}'+'\n'
    (latex/'verifica.tex').write_text(standalone,encoding='utf-8')
    if compile_pdf:
        if not shutil.which('pdflatex'):
            raise RuntimeError('pdflatex assente. Installare TeX Live oppure usare --solo-sorgenti.')
        logs=[]
        for _ in range(2):
            proc=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','verifica.tex'],cwd=latex,capture_output=True,timeout=120)
            logs.append(proc.stdout+proc.stderr)
            (latex/'compilazione_latex.log').write_bytes(b'\n'.join(logs))
            if proc.returncode:
                raise RuntimeError('Errore LaTeX: '+str(latex/'compilazione_latex.log'))
    return latex/'verifica.pdf'

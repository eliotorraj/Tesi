"""Grafici del confronto: una pagina, quattro sistemi, scale condivise."""
from __future__ import annotations
from dati import METHODS, LABELS, number, write_csv
from impaginazione import COLORS, esc

PANEL_LABELS = {**LABELS, 'llm_senza_rag': 'LLM no RAG'}


def threshold_counts(run, threshold=0.8):
    """Denominatore: tutti i circuiti attesi, inclusi fallimenti e pendenti."""
    cs = run['circuits']
    high = sum(number(c.get('score')) and c['score'] >= threshold for c in cs)
    low = sum(number(c.get('score')) and c['score'] < threshold for c in cs)
    pending = sum(c['status'] == 'pending' for c in cs)
    return dict(total=len(cs), high=high, low=low,
                no_score=len(cs)-high-low-pending, pending=pending)


def panel_title(method, run):
    title = PANEL_LABELS[method]
    if run and run.get('source', {}).get('exploratory'):
        title += ' (esplorativo)'
    return esc(title)


def grid(output, stem, runs, panels):
    folder = output/'grafici'
    folder.mkdir(parents=True, exist_ok=True)
    pieces = []
    for i, method in enumerate(METHODS):
        title = panel_title(method, runs.get(method))
        panel = panels.get(method, r'\parbox[c][5.8cm][c]{\linewidth}{\centering Risultati non disponibili}')
        pieces.append(r'\begin{minipage}[t]{0.49\linewidth}\centering'+'\n'
                      +r'{\large\bfseries '+title+r'}\par\smallskip'+'\n'
                      +panel+'\n'+r'\end{minipage}'+'\n')
        pieces.append(r'\hfill' if i % 2 == 0 else r'\par\vspace{0.45cm}')
    (folder/(stem+'.tex')).write_text(''.join(pieces), encoding='utf-8')


def axis(points, method, ylabel, options='', xlabel='Circuiti in ordine alfabetico', kind='points'):
    style = f"color={COLORS[method]},mark=*,mark size=1.6pt,only marks"
    if kind == 'ecdf':
        style = f"color={COLORS[method]},thick,no marks,const plot"
    coords = ' '.join(f'({x},{y})' for x,y in points)
    text = (r'\begin{tikzpicture}\begin{axis}['
            r'width=0.95\linewidth,height=6.1cm,grid=major,grid style={gray!18},'
            r'tick label style={font=\small},label style={font=\small},'
            r'scaled ticks=false,/pgf/number format/use comma,'
            r'unbounded coords=discard,'
            +f'xlabel={{{xlabel}}},ylabel={{{ylabel}}},'+options+']\n')
    if points:
        text += '\\addplot['+style+'] coordinates {'+coords+'};\n'
    else:
        text += r'\node at (rel axis cs:0.5,0.5) {Nessuna misura disponibile};'+'\n'
    return text+r'\end{axis}\end{tikzpicture}'


def metric_grid(output, runs, metric, label):
    measured = [c[metric] for run in runs.values() for c in run['circuits'] if number(c.get(metric))]
    ymax = 1.02 if metric == 'score' else max(measured, default=1)*1.08
    ymax = max(ymax, 1)
    last = max((c['index'] for r in runs.values() for c in r['circuits']), default=90)
    opts = f'xmin=0,xmax={last+1},ymin=0,ymax={ymax},'
    if metric in ('retries','llm_calls'):
        opts += 'ytick distance=1,'
    panels = {}
    for method, run in runs.items():
        if metric in ('total_tokens','llm_response_seconds','retries') and not method.startswith('llm'):
            panels[method] = (r'\parbox[c][6.1cm][c]{\linewidth}{\centering\large Non applicabile'
                              r'\\[5pt]\normalsize Questo sistema non usa un LLM.}')
            continue
        points = [(c['index'],c[metric]) for c in run['circuits'] if number(c.get(metric))]
        write_csv(output/'grafici'/f'{metric}_{method}.csv',
                  [dict(circuit=c['circuit_id'],position=c['index'],value=c[metric])
                   for c in run['circuits'] if number(c.get(metric))], ['circuit','position','value'])
        panels[method] = axis(points,method,label,opts)
    grid(output,metric,runs,panels)


def reliability_grid(output, runs):
    panels = {}
    rows = []
    ceiling = max((r['summary']['expected_circuits'] for r in runs.values()),default=90)
    for method,run in runs.items():
        cs=run['circuits']
        counts=[sum(c['status']=='success' for c in cs),sum(c['status']=='failure' for c in cs),
                sum(c['status']=='pending' for c in cs)]
        mixed=sum(c['status']=='mixed' for c in cs)
        labels=['Riusciti','Falliti','Pendenti']
        if mixed:
            counts.append(mixed);labels.append('Misti')
        rows.extend(dict(method=method,status=l,count=v) for l,v in zip(labels,counts))
        opts=(r'width=0.95\linewidth,height=6.1cm,ybar,bar width=25pt,ymin=0,'
              +f'ymax={ceiling*1.18},xmin=0.4,xmax={len(labels)+0.6},'
              +r'xtick={'+','.join(str(i) for i in range(1,len(labels)+1))+r'},xticklabels={'+','.join(labels)+'},'
              r'ytick distance=15,ylabel={Circuiti},nodes near coords,'
              r'every node near coord/.append style={font=\small},'
              r'tick label style={font=\small},grid=major,grid style={gray!18}]')
        colors=['blue!65','orange!80','gray!40','violet!50']
        text=r'\begin{tikzpicture}\begin{axis}['+opts+'\n'
        for i,(value,color) in enumerate(zip(counts,colors),1):
            text+=f'\\addplot[bar shift=0pt,fill={color},draw={color}] coordinates {{({i},{value})}};\n'
        panels[method]=text+r'\end{axis}\end{tikzpicture}'
    write_csv(output/'grafici/esiti.csv',rows)
    grid(output,'esiti',runs,panels)


def threshold_grid(output, runs):
    panels={}; rows=[]
    colors=['blue!65','orange!70','gray!55','gray!20']
    labels=[r'Score $\geq 0{,}8$',r'Score $<0{,}8$','Senza score','Pendenti']
    for method,run in runs.items():
        counts=threshold_counts(run)
        rows.append(dict(method=method,threshold=0.8,**counts,
                         percentage=100*counts['high']/counts['total'] if counts['total'] else None))
        total=counts['total']
        text=r'\begin{tikzpicture}[x=1cm,y=1cm]\path[use as bounding box] (-4,-2.7) rectangle (4,2.7);'+'\n'
        start=90
        for key,color in zip(('high','low','no_score','pending'),colors):
            count=counts[key]
            if not count or not total:
                continue
            end=start+360*count/total
            text+=f'\\filldraw[fill={color},draw=white,line width=1pt] (0,0) -- ({start}:2.5) arc ({start}:{end}:2.5) -- cycle;\n'
            middle=(start+end)/2
            pct=f'{100*count/total:.1f}'.replace('.',',')
            text+=f'\\node[font=\\large\\bfseries,align=center] at ({middle}:1.45) {{{pct}\\%}};\n'
            start=end
        text+=r'\end{tikzpicture}'+'\n'+r'\par{\small '
        text+='; '.join(labels[i]+': '+str(counts[key]) for i,key in enumerate(('high','low','no_score','pending')) if counts[key])
        text+='}'
        panels[method]=text
    write_csv(output/'tabelle/soglia_score_080.csv',rows,
              ['method','threshold','total','high','low','no_score','pending','percentage'])
    grid(output,'soglia_score_080',runs,panels)


def ecdf_grid(output, runs):
    panels={}
    for method,run in runs.items():
        vals=sorted(c['score'] for c in run['circuits'] if number(c.get('score')))
        points=([(0,0)]+[(v,(i+1)/len(vals)) for i,v in enumerate(vals)]+[(1,1)]) if vals else []
        write_csv(output/'grafici'/f'distribuzione_score_{method}.csv',
                  [dict(score=x,quota=y) for x,y in points],['score','quota'])
        panels[method]=axis(points,method,'Quota cumulativa','xmin=0,xmax=1,ymin=0,ymax=1,',
                            xlabel=f"Score (circuiti riusciti: {len(vals)})",kind='ecdf')
    grid(output,'distribuzione_score',runs,panels)


def figure_page(stem, title, prose, caption):
    """Testo e figura non flottante: la spiegazione precede sempre i pannelli."""
    return (r'\clearpage\newgeometry{margin=1.35cm}\begin{landscape}'+'\n'+r'\subsection{'+title+'}\n'
            +prose+'\n\n'+r'\begin{center}'+'\n'
            +r'\input{\TestReportPath grafici/'+stem+'.tex}\n'
            +r'\captionof{figure}{'+caption+'}\n'+r'\end{center}\end{landscape}\restoregeometry'+'\n')


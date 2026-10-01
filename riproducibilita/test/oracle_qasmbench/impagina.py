"""La stessa struttura del confronto dei 90 Test, con valori e scale derivati dai 50 QASMBench."""
from pathlib import Path
import argparse
import json
import math

PREAMBLE=r"""\documentclass[10pt,a4paper,landscape]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage[italian]{babel}
\usepackage[margin=15mm]{geometry}
\usepackage{lmodern,booktabs,array,amsmath,tikz,xcolor,hyperref,fancyhdr}
\hypersetup{colorlinks=true,linkcolor=blue!50!black}
\pagestyle{fancy}\fancyhf{}\lhead{\small QASMBench: LLM + RAG, Manhattan, 5 esempi}
\rhead{\small Confronto con oracle max3}\cfoot{\small\thepage}
\setlength{\headheight}{13pt}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\newcommand{\titolo}[1]{{\Large\bfseries #1}\par\vspace{3mm}}
\begin{document}
"""

def esc(value):
    chars={'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','{':r'\{','}':r'\}','$':r'\$','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(chars.get(c,c) for c in str(value))

def num(v,places=10):return '--' if v is None else f'{v:.{places}f}'
def line(c):return ' & '.join(map(str,c))+r' \\'+'\n'
def table(h,rows,cols):
    return r'\begin{tabular}{'+cols+'}\n\\toprule\n'+line(h)+'\\midrule\n'+''.join(line(r) for r in rows)+'\\bottomrule\n\\end{tabular}\n'

def gap_scale(rows):
    values=[r['gap'] for r in rows if r['gap'] is not None]
    lower=min([0.]+values);upper=max([0.]+values)
    # Una scala comune a tutte le pagine, con spazio anche per scarti negativi.
    span=max(upper-lower,.01);step=10**math.floor(math.log10(span/5))
    step*=next(x for x in (1,2,5,10) if x*step>=span/5)
    lo=math.floor(lower/step)*step;hi=math.ceil(upper/step)*step
    if hi==lo:hi=lo+5*step
    return lo,hi,step

def chart(rows,scale):
    lo,hi,step=scale
    gx=lambda value:20+5.5*(value-lo)/(hi-lo)
    t=[r'\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]',
       r'\node[anchor=west,font=\bfseries] at (0,.8) {Circuito (* = oracle parziale)};',
       r'\node[anchor=west,font=\bfseries] at (8.8,.8) {Score: RAG e massimo conosciuto};',
       r'\node[anchor=west,font=\bfseries] at (20,.8) {Scarto $R-S$};']
    bottom=-max(len(rows)*.37,1)
    for v in (0,.2,.4,.6,.8,1):
        x=8.8+10*v
        t.extend([fr'\draw[gray!25] ({x},.25)--({x},{bottom});',fr'\node at ({x},.42) {{{v:.1f}}};'])
    for i in range(round((hi-lo)/step)+1):
        value=lo+i*step;x=gx(value)
        t.extend([fr'\draw[gray!25] ({x},.25)--({x},{bottom});',fr'\node[font=\scriptsize] at ({x},.42) {{{value:.3f}}};'])
    for i,r in enumerate(rows):
        y=-i*.37
        if i%2==0:t.append(fr'\fill[gray!5] (0,{y-.16}) rectangle (25.6,{y+.16});')
        name=esc(r['circuit_id'])+('*' if not r['exhaustive'] else '')
        t.append(fr"\node[anchor=west] at (0,{y}) {{{r['id']:02d}\quad {name}}};")
        a=r['system_score'];b=r['oracle_score']
        if a is not None and b is not None:t.append(fr'\draw[gray,thick] ({8.8+10*a},{y})--({8.8+10*b},{y});')
        if b is not None:t.append(fr'\draw[orange!85!black,line width=.7pt] ({8.8+10*b},{y}) circle (2pt);')
        if a is not None:t.append(fr'\fill[blue!70!black] ({8.8+10*a},{y}) circle (1pt);')
        col='teal!75!black' if r['exhaustive'] else 'gray!65';gap=r['gap']
        if gap is None:t.append(fr'\node at ({gx(0)},{y}) {{--}};')
        elif abs(gap)<=1e-12:t.append(fr'\fill[{col}] ({gx(0)},{y}) circle (.8pt);')
        else:t.append(fr'\fill[{col}] ({gx(0)},{y-.10}) rectangle ({gx(gap)},{y+.10});')
    t.append(r'\end{tikzpicture}')
    return '\n'.join(t)

def render(directory):
    directory=Path(directory);d=json.loads((directory/'dati.json').read_text(encoding='utf-8'))
    rows=d['rows'];s=d['summary'];o=d['oracle_summary'];counts=o['statuses'];n=len(rows)
    dest=directory/'confronto_oracle_rag5.tex'
    if dest.exists():raise ValueError('Documento già presente: usare una nuova analisi.')
    out=[PREAMBLE]
    if d.get('synthetic'):
        out.append(r'\rhead{\color{red}\bfseries DATI FITTIZI -- SOLA VERIFICA GRAFICA}')
        out.append(r'\textbf{\color{red}Documento di collaudo: nessun risultato sperimentale.}')
    out.extend([r'\titolo{Quanto manca al massimo conosciuto?}',
        fr'{{\large LLM + RAG con 5 esempi sui {n} circuiti Test QASMBench}}\par',
        r"Il confronto usa gli esiti originali del RAG con distanza Manhattan e una nuova ricerca sulla griglia Qiskit. "
        r"Lo score è \texttt{expected\_fidelity}: una stima sui Target sintetici, non una misura su hardware quantistico reale. "
        r"La selezione comprende 30 circuiti piccoli, 15 medi e 5 grandi; è esterna per fonte rispetto al corpus MQT Bench.",
        fr"\textbf{{Risultato principale.}} Su {s['compared']}/{n} circuiti confrontabili, il sistema raggiunge il massimo conosciuto "
        fr"in {s['statuses'].get('pari',0)} casi, resta sotto in {s['statuses'].get('sotto',0)} e supera il riferimento in {s['statuses'].get('sopra',0)}. "
        fr"Lo scarto medio è {num(s['mean_gap'])}, pari a {num(100*s['mean_gap'] if s['mean_gap'] is not None else None,8)} punti percentuali. "
        fr"La mediana è {num(s['median_gap'])}; in {s['within_001']} casi lo scarto assoluto non supera 0,01."])
    groups=[s,s['complete'],s['partial']]
    tr=[['Circuiti']+[g['n'] for g in groups],['Confrontabili']+[g['compared'] for g in groups]]
    for label,key in [('Score medio RAG','mean_system'),('Massimo conosciuto medio','mean_oracle'),('Scarto medio','mean_gap'),('Scarto massimo','max_gap')]:
        tr.append([label]+[num(g[key]) for g in groups])
    for label,key in [('Al massimo conosciuto','pari'),('Sotto il massimo conosciuto','sotto'),('Sopra il massimo conosciuto','sopra')]:
        tr.append([label]+[f"{g['statuses'].get(key,0)} / {g['compared']}" for g in groups])
    out.append(table(['Misura','Tutti i circuiti','Oracle completo','Oracle parziale'],tr,'lrrr'))
    out.append(r"\medskip\textbf{Definizione.} Per ogni circuito, $R=\max_{d,c,s}F(d,c,s)$ è il massimo degli score validi osservati: "
        r"$d$ indica uno dei cinque dispositivi compatibili, $c$ una delle dodici configurazioni Qiskit e $s\in\{0,1,2\}$ il seed. "
        r"Il sistema ha una compilazione con seed 0 e score $S$. Lo scarto è $\Delta=R-S$: zero indica parità; un valore positivo indica margine osservato; "
        r"un valore negativo indica che il sistema supera il riferimento. I punti percentuali sono $100\Delta$; lo scarto relativo è $100\Delta/R$, non definito se $R=0$.")
    state='terminata' if o['complete'] else 'ancora parziale'
    out.append(fr"\textbf{{Copertura della generazione, {state}.}} Le {o['plan']['matrix_cells']} celle comprendono {o['plan']['incompatible_cells']} incompatibilità. "
        fr"Delle {o['plan']['compilations']} compilazioni compatibili, {counts.get('success',0)} riescono, {counts.get('timeout',0)} superano il limite di 100 secondi, "
        fr"{counts.get('failure',0)} falliscono e {counts.get('interrupted',0)} sono interrotte. Restano {o['pending']} celle non concluse. "
        fr"Hanno un riferimento {o['circuits_with_reference']}/{n} circuiti; per {s['complete']['n']} la griglia è completa. Errori e timeout sono dati mancanti, mai score zero.")
    out.append(fr"\textbf{{Interpretazione.}} Le parità con ricerca completa sono {s['complete']['statuses'].get('pari',0)}; "
        fr"quelle con ricerca parziale sono {s['partial']['statuses'].get('pari',0)}. "
        r"Una parità in una griglia incompleta non esclude alternative migliori. Non è una prova di ottimalità assoluta. L'oracle viene usato dopo le decisioni RAG, senza entrare nel recupero o nel prompt.")
    out.append(r'\newpage\titolo{Scelta della coppia e variabilità del seed}')
    out.append(r"Il massimo osservato della coppia scelta è $P=\max_{s=0,1,2}F(d_{\mathrm{LLM}},c_{\mathrm{LLM}},s)$, sui soli seed riusciti:"
        r"\[\underbrace{R-S}_{\text{scarto totale}}=\underbrace{R-P}_{\text{margine cambiando coppia}}+\underbrace{P-S}_{\text{differenza entro la stessa coppia}}.\]")
    out.append(fr"Le coppie scelte con tre seed riusciti sono {s['selected_pair_complete']}/{n}; la scomposizione è disponibile per {s['decomposition_n']} circuiti. "
        fr"Il margine medio tra coppie è {num(s['mean_choice_gap'])}; la differenza media entro la coppia è {num(s['mean_within_pair_gap'])}. "
        fr"La coppia scelta è fra le migliori note in {s['best_pairs']} casi. "
        fr"Il seed 0 della coppia scelta differisce dallo score RAG in {s['seed0_different']} casi; il confronto manca in {s['seed0_missing']}. "
        fr"Lo scarto medio rispetto al massimo globale del solo seed 0 è {num(s['mean_gap_vs_seed0_global'])}, su {s['seed0_global_n']} casi.")
    out.append(r"Il termine $P-S$ può includere differenze tra esecuzioni, oltre all'effetto del seed: la riproduzione del seed 0 viene quindi verificata. "
        r"Se mancano seed della coppia scelta, $P$ è parziale; uno scarto negativo viene conservato.")
    out.append(r'\textbf{I dieci scarti maggiori.} C = ricerca completa; P = ricerca parziale. I valori sono score, non percentuali.')
    top=sorted([r for r in rows if r['gap'] is not None],key=lambda r:r['gap'],reverse=True)[:10]
    out.append(table(['Circuito','RAG $S$','Oracle $R$','Totale $R-S$','Coppia $R-P$','Seed $P-S$','Ricerca'],
        [[esc(r['circuit_id'])]+[num(r[k],8) for k in ['system_score','oracle_score','gap','choice_gap','within_pair_gap']]+['C' if r['exhaustive'] else 'P'] for r in top],'lrrrrrc'))
    for r in top[:2]:
        winner=r['best_pairs'][0] if r['best_pairs'] else None
        out.append(fr"\medskip\textbf{{Esempio: \texttt{{{esc(r['circuit_id'])}}}.}} Il RAG sceglie \texttt{{{esc(r['device'])}}} "
            fr"con \texttt{{{esc(r['config_id'])}}} e ottiene {num(r['system_score'])}. "
            fr"La stessa coppia raggiunge {num(r['selected_pair_max3'])}; il massimo globale osservato è {num(r['oracle_score'])}. "
            fr"La copertura è {r['successful_attempts']}/{r['expected_attempts']} compilazioni compatibili riuscite.")
        if winner:out.append(fr"Una coppia vincente è \texttt{{{esc(winner['device'])}}}, \texttt{{{esc(winner['config_id'])}}}; seed migliori: {esc(', '.join(map(str,winner['best_seeds'])))}.")
    scale=gap_scale(rows)
    out.append(fr"\textbf{{Lettura dei grafici.}} Punto blu = RAG; cerchio arancione = oracle. Lo scarto usa una scala comune da {scale[0]:.3f} a {scale[1]:.3f}: "
        r"verde = oracle completo; grigio = parziale. L'asterisco segnala un riferimento parziale; -- indica dati mancanti. Gli ID e l'ordine alfabetico coincidono con le tabelle.")
    figs=directory/'grafici';figs.mkdir(exist_ok=False)
    chunks=[rows[i:i+30] for i in range(0,n,30)]
    for page,chunk in enumerate(chunks,1):
        c=chart(chunk,scale)
        out.append(fr"\newpage\titolo{{Score e scarto per circuito: {chunk[0]['id']}--{chunk[-1]['id']}}}"+'\n'+c)
        out.append(r'\par\small Blu: RAG; arancione: oracle. Scarto verde: riferimento completo; grigio: parziale. Scale identiche in tutte le pagine.')
        (figs/f'confronto_{page}.tex').write_text(r'\documentclass[10pt]{article}\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage{lmodern,tikz}\usepackage[paperwidth=28cm,paperheight=14cm,margin=8mm]{geometry}\pagestyle{empty}\begin{document}\noindent'+'\n'+c+'\n'+r'\end{document}',encoding='utf-8')
    for chunk in chunks:
        out.append(fr"\newpage\titolo{{Tabella completa: circuiti {chunk[0]['id']}--{chunk[-1]['id']}}}")
        out.append(r'\small Coppia al max: massimo osservato della coppia scelta uguale al massimo globale. C/P: oracle completo/parziale. --: dato mancante.\par\vspace{2mm}{\fontsize{8.5}{10}\selectfont\setlength{\tabcolsep}{5pt}\renewcommand{\arraystretch}{1.18}')
        out.append(table(['ID','Circuito','Qubit','RAG $S$','Oracle $R$','Scarto $R-S$','Coppia al max','C/P'],
            [[r['id'],esc(r['circuit_id']),r['num_qubits']]+[num(r[k]) for k in ['system_score','oracle_score','gap']]+['--' if r['selected_pair_is_best'] is None else ('Sì' if r['selected_pair_is_best'] else 'No'),'C' if r['exhaustive'] else 'P'] for r in chunk],'rlrrrrcc'))
        out.append(r'}\par\small Parità: tolleranza $10^{-12}$ sui valori a 10 decimali. Tutti i 50 circuiti sono mantenuti; gli scarti non calcolabili restano mancanti. Dettagli nel CSV e in \texttt{dati.json}.')
    out.append(r'\newpage\titolo{Fonti, controlli e riproducibilità}')
    out.append(fr"\textbf{{Sistema.}} Risultati originali \texttt{{llm\_rag}} QASMBench, avvio {esc(d['system_started_at'])}. "
        r"Qwen3.5-4B Q8\_0, profilo \texttt{qwen/p0\_t0}, recupero Manhattan con cinque esempi train e compilazione Qiskit con seed 0. "
        fr"Esiti del sistema: {esc(json.dumps(s['system_statuses'],ensure_ascii=False))}.")
    versions=', '.join(f'{k} {v}' for k,v in d['oracle_versions'].items())
    out.append(fr"\textbf{{Oracle.}} Python {esc(d['python'])}; {esc(versions)}. Massimo dei seed 0, 1, 2 per coppia, poi massimo tra coppie. "
        r"Target: \texttt{ibm\_falcon\_27}, \texttt{ibm\_heron\_133}, \texttt{ibm\_falcon\_127}, \texttt{ibm\_heron\_156}, \texttt{quantinuum\_h2\_56}. "
        r"Dodici configurazioni; limite 100 secondi per tentativo, import iniziali esclusi; controllo separato dell'avvio a 60 secondi. Parallelismo e impronte sono nel contratto.")
    out.append(fr"\textbf{{Verifiche.}} Controllati {o['terminal']} esiti originali; ricalcolati i massimi delle {n*60} coppie e dei {n} circuiti. "
        r"Verificati sorgenti, Target, versioni condivise, recupero k=5, decisioni e score nei risultati di compilazione. Il testo dell'input RAG è confrontato con il QASM originale tenendo conto della normalizzazione CRLF/LF. "
        fr"Le medie principali usano gli stessi {s['compared']} circuiti confrontabili. I sottogruppi completo/parziale contengono circuiti diversi e non isolano effetti causali. "
        r"I dieci casi sono selezionati per scarto decrescente; grafici, tabelle e CSV mantengono tutti i circuiti.")
    out.append(r"\textbf{Limiti.} L'oracle prende il migliore di tre seed; il sistema usa un solo seed. Il confronto è intenzionalmente favorevole all'oracle. "
        r"Un riferimento parziale è un limite inferiore del massimo della griglia completa, non un limite superiore per altri compilatori. "
        r"La selezione QASMBench è ragionata: la diversa fonte non esclude algoritmi equivalenti o la presenza nel preaddestramento dell'LLM. "
        r"Score arrotondati a zero non dimostrano identità dei valori non arrotondati. Il confronto non avvia compilazioni e non modifica le decisioni storiche.")
    out.append(r'\textbf{Fonti originali.}\par{\footnotesize')
    for value in [d['oracle_path'],d['rag_path']]:out.append(r'\path{'+str(value)+'}'+r'\par')
    out.append(r'}\textbf{Artefatti.} \texttt{analizza.py} verifica gli esiti; \texttt{impagina.py} genera il LaTeX. '
        r'\texttt{dati.json}, \texttt{confronto\_50\_circuiti.csv} e \texttt{provenienza.json} conservano valori, scelte, scarti relativi, scomposizione, denominatori e impronte; \texttt{grafici/} contiene figure autonome.')
    out.append(r"\textbf{Separazione.} Campagna e confronto sono nella cartella esterna QASMBench. Nessun risultato entra nel Dataset RAG, nel Training set o nelle pipeline decisionali. Il grafo graphify non viene aggiornato.\end{document}")
    dest.write_text('\n\n'.join(out),encoding='utf-8')
    return dest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True)
    print(render(ap.parse_args().directory))

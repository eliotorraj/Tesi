'Same layout as the 90-circuit Test comparison, with values and scales derived from 50 QASMBench circuits.'
from pathlib import Path
import argparse
import json
import math

PREAMBLE="""\\documentclass[10pt,a4paper,landscape]{article}
\\usepackage[utf8]{inputenc}\\usepackage[T1]{fontenc}\\usepackage[english]{babel}
\\usepackage[margin=15mm]{geometry}
\\usepackage{lmodern,booktabs,array,amsmath,tikz,xcolor,hyperref,fancyhdr}
\\hypersetup{colorlinks=true,linkcolor=blue!50!black}
\\pagestyle{fancy}\\fancyhf{}\\lhead{\\small QASMBench: LLM + RAG, Manhattan, 5 examples}
\\rhead{\\small Comparison with max3 oracle}\\cfoot{\\small\\thepage}
\\setlength{\\headheight}{13pt}\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{5pt}
\\newcommand{\\titolo}[1]{{\\Large\\bfseries #1}\\par\\vspace{3mm}}
\\begin{document}
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
    # Use a common scale across pages, allowing negative gaps.
    span=max(upper-lower,.01);step=10**math.floor(math.log10(span/5))
    step*=next(x for x in (1,2,5,10) if x*step>=span/5)
    lo=math.floor(lower/step)*step;hi=math.ceil(upper/step)*step
    if hi==lo:hi=lo+5*step
    return lo,hi,step

def chart(rows,scale):
    lo,hi,step=scale
    gx=lambda value:20+5.5*(value-lo)/(hi-lo)
    t=[r'\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]',
       '\\node[anchor=west,font=\\bfseries] at (0,.8) {Circuit (* = partial oracle)};',
       '\\node[anchor=west,font=\\bfseries] at (8.8,.8) {Score: RAG and best known};',
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
    if dest.exists():raise ValueError('Document already exists: use a new analysis.')
    out=[PREAMBLE]
    if d.get('synthetic'):
        out.append('\\rhead{\\color{red}\\bfseries SYNTHETIC DATA -- LAYOUT CHECK ONLY}')
        out.append('\\textbf{\\color{red}Verification document: no experimental results.}')
    out.extend(['\\titolo{How far is the best known result?}',
        f'{{\\large LLM + RAG with 5 examples on {n} QASMBench Test circuits}}\\par',
        'The comparison uses original Manhattan RAG outcomes and a new Qiskit-grid search. The score is \\texttt{expected\\_fidelity}, an estimate on synthetic Targets rather than a physical-hardware measurement. The selection contains 30 small, 15 medium and 5 large circuits from a source distinct from MQT Bench.',
        f"\\textbf{{Main result.}} On {s['compared']}/{n} comparable circuits, the system reaches the best known score in {s['statuses'].get('pari', 0)} cases and remains below it in {s['statuses'].get('sotto', 0)} and exceeds the reference in {s['statuses'].get('sopra', 0)}. Mean gap is {num(s['mean_gap'])}, equivalent to {num(100 * s['mean_gap'] if s['mean_gap'] is not None else None, 8)} percentage points. Median is {num(s['median_gap'])}; in {s['within_001']} cases have absolute gap at most 0.01."])
    groups=[s,s['complete'],s['partial']]
    tr=[['Circuits']+[g['n'] for g in groups],['Comparable']+[g['compared'] for g in groups]]
    for label,key in [('Mean RAG score','mean_system'),('Mean best-known score','mean_oracle'),('Mean gap','mean_gap'),('Largest gap','max_gap')]:
        tr.append([label]+[num(g[key]) for g in groups])
    for label,key in [('At the best known score','pari'),('Below the best known score','sotto'),('Above the best known score','sopra')]:
        tr.append([label]+[f"{g['statuses'].get(key,0)} / {g['compared']}" for g in groups])
    out.append(table(['Measurement','All circuits','Complete oracle','Partial oracle'],tr,'lrrr'))
    out.append('\\medskip\\textbf{Definition.} For each circuit, $R=\\max_{d,c,s}F(d,c,s)$ is the largest valid observed score: $d$ is a compatible device among the five, $c$ one of twelve Qiskit configurations, and $s\\in\\{0,1,2\\}$ the seed. The system has one seed-0 compilation with score $S$. The gap is $\\Delta=R-S$: zero means a tie, positive means observed headroom, and negative means the system exceeds the reference. Percentage points are $100\\Delta$; relative gap is $100\\Delta/R$, undefined for $R=0$.')
    state='terminata' if o['complete'] else 'still partial'
    out.append(f"\\textbf{{Generation coverage, {state}.}} The {o['plan']['matrix_cells']} cells include {o['plan']['incompatible_cells']} incompatibilities. Of {o['plan']['compilations']} compatible compilations, {counts.get('success', 0)} succeed, {counts.get('timeout', 0)} exceed the 100-second limit, {counts.get('failure', 0)} fail and {counts.get('interrupted', 0)} are interrupted. Remaining: {o['pending']} incomplete cells. A reference is available for {o['circuits_with_reference']}/{n} circuits; for {s['complete']['n']} the grid is complete. Errors and timeouts are missing data, never zero scores.")
    out.append(f"\\textbf{{Interpretation.}} Ties with complete search: {s['complete']['statuses'].get('pari', 0)}; ties with partial search: {s['partial']['statuses'].get('pari', 0)}. A tie in an incomplete grid does not exclude better alternatives or prove absolute optimality. The oracle is used after RAG decisions, outside retrieval and prompts.")
    out.append('\\newpage\\titolo{Pair selection and seed variability}')
    out.append("The selected pair's observed maximum is $P=\\max_{s=0,1,2}F(d_{\\mathrm{LLM}},c_{\\mathrm{LLM}},s)$ over successful seeds only:\\[\\underbrace{R-S}_{\\text{total gap}}=\\underbrace{R-P}_{\\text{headroom from changing pair}}+\\underbrace{P-S}_{\\text{difference within the same pair}}.\\]")
    out.append(f"Selected pairs with three successful seeds: {s['selected_pair_complete']}/{n}; decomposition is available for {s['decomposition_n']} circuits. Mean between-pair headroom is {num(s['mean_choice_gap'])}; mean within-pair difference is {num(s['mean_within_pair_gap'])}. The selected pair is among the best known in {s['best_pairs']} cases. Its seed-0 score differs from RAG in {s['seed0_different']} cases; comparison is missing in {s['seed0_missing']}. Mean gap from the global seed-0 maximum is {num(s['mean_gap_vs_seed0_global'])}, out of {s['seed0_global_n']} cases.")
    out.append('$P-S$ may include between-run differences as well as seed effects, so seed-0 reproduction is checked. If selected-pair seeds are missing, $P$ is partial; negative gaps are retained.')
    out.append('\\textbf{Ten largest gaps.} C = complete search; P = partial search. Values are scores, not percentages.')
    top=sorted([r for r in rows if r['gap'] is not None],key=lambda r:r['gap'],reverse=True)[:10]
    out.append(table(['Circuit','RAG $S$','Oracle $R$','Total $R-S$','Pair $R-P$','Seed $P-S$','Search'],
        [[esc(r['circuit_id'])]+[num(r[k],8) for k in ['system_score','oracle_score','gap','choice_gap','within_pair_gap']]+['C' if r['exhaustive'] else 'P'] for r in top],'lrrrrrc'))
    for r in top[:2]:
        winner=r['best_pairs'][0] if r['best_pairs'] else None
        out.append(f"\\medskip\\textbf{{Example: \\texttt{{{esc(r['circuit_id'])}}}.}} RAG selects \\texttt{{{esc(r['device'])}}} with \\texttt{{{esc(r['config_id'])}}} and achieves {num(r['system_score'])}. The same pair reaches {num(r['selected_pair_max3'])}; the observed global maximum is {num(r['oracle_score'])}. Coverage is {r['successful_attempts']}/{r['expected_attempts']} successful compatible compilations.")
        if winner:out.append(f"One winning pair is \\texttt{{{esc(winner['device'])}}}, \\texttt{{{esc(winner['config_id'])}}}; best seeds: {esc(', '.join(map(str, winner['best_seeds'])))}.")
    scale=gap_scale(rows)
    out.append(f'\\textbf{{Reading the plots.}} Blue point = RAG; orange circle = oracle. Gaps share a scale from {scale[0]:.3f} a {scale[1]:.3f}: green = complete oracle; gray = partial. An asterisk marks a partial reference; -- means missing data. IDs and alphabetical order match the tables.')
    figs=directory/'grafici';figs.mkdir(exist_ok=False)
    chunks=[rows[i:i+30] for i in range(0,n,30)]
    for page,chunk in enumerate(chunks,1):
        c=chart(chunk,scale)
        out.append(f"\\newpage\\titolo{{Score and gap per circuit: {chunk[0]['id']}--{chunk[-1]['id']}}}"+'\n'+c)
        out.append('\\par\\small Blue: RAG; orange: oracle. Green gap: complete reference; gray: partial. Identical scales on every page.')
        (figs/f'confronto_{page}.tex').write_text(r'\documentclass[10pt]{article}\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage{lmodern,tikz}\usepackage[paperwidth=28cm,paperheight=14cm,margin=8mm]{geometry}\pagestyle{empty}\begin{document}\noindent'+'\n'+c+'\n'+r'\end{document}',encoding='utf-8')
    for chunk in chunks:
        out.append(f"\\newpage\\titolo{{Full table: circuits {chunk[0]['id']}--{chunk[-1]['id']}}}")
        out.append("\\small Pair at max: selected pair's observed maximum equals the global maximum. C/P: complete/partial oracle. --: missing data.\\par\\vspace{2mm}{\\fontsize{8.5}{10}\\selectfont\\setlength{\\tabcolsep}{5pt}\\renewcommand{\\arraystretch}{1.18}")
        out.append(table(['ID','Circuit','Qubit','RAG $S$','Oracle $R$','Gap $R-S$','Pair at maximum','C/P'],
            [[r['id'],esc(r['circuit_id']),r['num_qubits']]+[num(r[k]) for k in ['system_score','oracle_score','gap']]+['--' if r['selected_pair_is_best'] is None else ('Yes' if r['selected_pair_is_best'] else 'No'),'C' if r['exhaustive'] else 'P'] for r in chunk],'rlrrrrcc'))
        out.append('}\\par\\small Ties: $10^{-12}$ tolerance on 10-decimal values. All 50 circuits are retained; uncomputable gaps remain missing. Details are in CSV and \\texttt{dati.json}.')
    out.append('\\newpage\\titolo{Sources, checks and reproducibility}')
    out.append(f"\\textbf{{System.}} Original QASMBench \\texttt{{llm\\_rag}} results, started {esc(d['system_started_at'])}. Qwen3.5-4B Q8\\_0, profile \\texttt{{qwen/p0\\_t0}}, Manhattan retrieval with five train examples and Qiskit compilation at seed 0. System outcomes: {esc(json.dumps(s['system_statuses'], ensure_ascii=False))}.")
    versions=', '.join(f'{k} {v}' for k,v in d['oracle_versions'].items())
    out.append(f"\\textbf{{Oracle.}} Python {esc(d['python'])}; {esc(versions)}. Maximum over seeds 0, 1 and 2 per pair, then across pairs. Targets: \\texttt{{ibm\\_falcon\\_27}}, \\texttt{{ibm\\_heron\\_133}}, \\texttt{{ibm\\_falcon\\_127}}, \\texttt{{ibm\\_heron\\_156}}, \\texttt{{quantinuum\\_h2\\_56}}. Twelve configurations; 100-second attempt limit excluding initial imports; separate 60-second startup check. Concurrency and hashes are recorded in the contract.")
    out.append(f"\\textbf{{Checks.}} Verified {o['terminal']} original outcomes; recomputed maxima for {n * 60} pairs and {n} circuits. Sources, Targets, shared versions, k=5 retrieval, decisions and compilation scores were verified. RAG input text is compared with original QASM allowing CRLF/LF normalization. Main means use the same {s['compared']} comparable circuits. Complete/partial subsets contain different circuits and do not isolate causal effects. The ten cases are selected by descending gap; plots, tables and CSV retain every circuit.")
    out.append("\\textbf{Limits.} The oracle takes the best of three seeds; the system uses one. This intentionally favors the oracle. A partial reference is a lower bound on the full grid's maximum, not an upper bound for other compilers. QASMBench selection is purposive: a distinct source does not rule out equivalent algorithms or LLM pretraining exposure. Scores rounded to zero do not prove equal unrounded values. Comparison starts no compilation and changes no historical decision.")
    out.append(r'\textbf{Fonti originali.}\par{\footnotesize')
    for value in [d['oracle_path'],d['rag_path']]:out.append(r'\path{'+str(value)+'}'+r'\par')
    out.append('}\\textbf{Artifacts.} \\texttt{analizza.py} verifies outcomes; \\texttt{impagina.py} generates LaTeX. \\texttt{dati.json}, \\texttt{confronto\\_50\\_circuiti.csv} and \\texttt{provenienza.json} preserve values, choices, relative gaps, decomposition, denominators and hashes; \\texttt{grafici/} contains standalone figures.')
    out.append('\\textbf{Separation.} Campaign and comparison stay in the external QASMBench directory. No result enters the RAG Dataset, Training set or decision pipelines. The graphify graph is not updated by this analysis.\\end{document}')
    dest.write_text('\n\n'.join(out),encoding='utf-8')
    return dest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True)
    print(render(ap.parse_args().directory))

'Standalone LaTeX and vector PGFPlots figures from dati.json.'
from pathlib import Path
import json
import math
import hashlib

import argparse
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument("--directory",type=Path,default=Path(__file__).resolve().parent)
BASE=ap.parse_args().directory.resolve()
D=json.loads((BASE/"dati.json").read_text())
KS=["1","5","10"]
S=D["summary"]
RUNS=D["runs"]
ROWS={k:{r["circuit_id"]:r for r in RUNS[k]} for k in KS}
IDS=sorted(ROWS["5"])
COLORS={"1":"kuno","5":"kcinque","10":"kdieci"}
def esc(v):
    return str(v).replace("\\",r"\textbackslash{}").replace("_",r"\_").replace("%",r"\%").replace("&",r"\&")
def fmt(v,n=2):
    if v is None:return "--"
    return f"{v:,.{n}f}".replace(",","§").replace(".",",").replace("§",r"\,")
def m(k,key,stat="mean"):return S[k]["metrics"][key][stat]
def row_metric(label,key,n=2,stat="mean"):
    return [label,*[fmt(m(k,key,stat),n) for k in KS]]
def table(headers,rows,spec=None):
    spec=spec or "X"+"r"*(len(headers)-1)
    return (r"\begingroup\small\renewcommand{\arraystretch}{1.18}\setlength{\tabcolsep}{5pt}"
            "\n"+r"\begin{tabularx}{\linewidth}{"+spec+r"}\toprule"+"\n"+
            " & ".join(headers)+r"\\\midrule"+"\n"+
            "\n".join(" & ".join(str(x) for x in row)+r"\\" for row in rows)+
            "\n"+r"\bottomrule\end{tabularx}\endgroup\par"+"\n")
def page(title):
    return "\n"+r"\clearpage\section{"+title+"}\n"
def coords(points):
    return " ".join(f"({x:.12g},{y:.12g})" for x,y in points)
def axis(metric,k,label,height="4.65cm",width=r".95\linewidth",extra=""):
    vals=[r[metric] for rows in RUNS.values() for r in rows]
    maximum=1 if metric=="score" else (2.25 if metric=="retries" else max(vals)*1.08)
    options=(f'width={width},height={height},title={{$k={k}$}},xlabel={{Circuit index}},ylabel={{{label}}},xmin=0,xmax=91,ymin=0,ymax={maximum:.12g},xtick={{1,15,30,45,60,75,90}},grid=major,scaled y ticks=false,tick label style={{font=\\scriptsize}},label style={{font=\\small}},title style={{font=\\bfseries}},'+extra)
    pts=[(r["index"],r[metric]) for r in RUNS[k]]
    return r"\begin{tikzpicture}\begin{axis}["+options+"]\n"+r"\addplot[only marks,mark=*,mark size=1.1pt,color="+COLORS[k]+",fill="+COLORS[k]+"] coordinates {"+coords(pts)+r"};\end{axis}\end{tikzpicture}"
def dual_page(title,a,b,la,lb,note):
    text=page(title)+note+r"\par\medskip"+"\n"
    text+=r"\noindent\begin{minipage}{.49\linewidth}\centering\textbf{"+la+r"}\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering\textbf{"+lb+r"}\end{minipage}\par"+"\n"
    for k in KS:
        text+=r"\noindent\begin{minipage}{.49\linewidth}\centering"+axis(a,k,la)+r"\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering"+axis(b,k,lb)+r"\end{minipage}\par\medskip"+"\n"
    text+='{\\small Each point is a circuit. Column scales match across the three k values. Indices follow appendix alphabetical order.}\\par'
    return text
PRE="""\\documentclass[a4paper,10pt]{article}
\\usepackage[margin=1.8cm]{geometry}\\usepackage[T1]{fontenc}\\usepackage[utf8]{inputenc}\\usepackage[english]{babel}
\\usepackage{lmodern,booktabs,tabularx,longtable,array,amsmath,xcolor,pgfplots,pdflscape,xurl,hyperref}\\usepackage[expansion=false]{microtype}\\pgfplotsset{compat=1.18}
\\definecolor{kuno}{HTML}{167D9A}\\definecolor{kcinque}{HTML}{D47A17}\\definecolor{kdieci}{HTML}{7656A3}\\hypersetup{hidelinks}\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{5pt}\\setlength{\\emergencystretch}{3em}\\newcommand{\\separatore}{\\par\\medskip}
\\begin{document}
{\\small\\bfseries PRESERVED-RECORD ANALYSIS | 29 September 2026}\\par
{\\LARGE\\bfseries How many examples does RAG need?}\\par
{\\Large Comparing $k=1$, $k=5$ and $k=10$}\\par\\medskip
"""
t=PRE
t+="""\\section{Question, settings and main result}
We compare the same LLM with one, five and ten similarity-retrieved train examples, examining decision quality, tokens and time. Each variant evaluated the same 90 Test circuits.
\\textbf{In this sample, more examples barely change score but increase tokens, waiting and repair requests.} All variants succeed on 90/90 circuits. Results do not establish that one example is always sufficient.
"""
t+=table(['Measurement',"$k=1$","$k=5$","$k=10$"],[
['Successful compilations',*[f'{S[k]["successes"]}/90' for k in KS]],
['Failures',*[str(90-S[k]["successes"]) for k in KS]],
row_metric('Mean score',"score",6),row_metric('Median score',"score",6,"median"),
['Score at least 0.8',*[f'{S[k]["threshold_08"]}/90' for k in KS]],
row_metric('Mean total time (s)',"total_seconds"),
row_metric('Total tokens, sum',"total_tokens",0,"sum"),
row_metric('Repairs, sum',"retries",0,"sum")])
t+="""\\subsection{Shared conditions}
The model is Qwen3.5-4B with Q8\\_0 weights and temperature 0. Records confirm identical GGUF and call parameters: seed 20260913, \\texttt{top\\_p}=0.95, \\texttt{top\\_k}=40 and \\texttt{min\\_p}=0. Requested context is 60,000 and maximum output 4,096 tokens. Extended reasoning is disabled; at most three attempts are allowed.
Retrieval uses the same 396 distinct train circuits, 49 features, train-fitted transformation, Manhattan distance and exact search. Filters and tie ordering are unchanged. Across all 90 cases, the k=1 example is the first in k=5 and k=10, and k=10's first five match the classical run.
Compilation uses the same twelve Qiskit configurations, five synthetic Targets, seed 0, one worker and external 100-second timeout. Expected fidelity ranges from 0 to 1, higher being better; it does not measure a physical-hardware execution.
\\subsection{Changes beyond example count}
The ten-example contract also allows E6--E10 and adjusts the prompt-column note. Responses still contain one or two facts with the same checks. Input uses TOON; output is JSON.
k=5 started on 21 September 2026; k=1 and k=10 started on 28 September after Test inspection. This descriptive comparison reuses the classical run across different dates and code revisions. It is neither fresh independent confirmation nor validation-based selection.
"""
t+=page('Times, tokens and repairs')
t+='Times are in seconds. Each following mean and median has 90 measurements per variant. Missing values were not imputed.\\par'
rows=[]
for label,key in [('Total',"total_seconds"),('Preparation and selection',"choice_seconds"),('Retrieval and RAG checks',"rag_seconds"),
                  ('LLM responses, cumulative',"llm_response_seconds"),('Internal compilation',"compilation_seconds"),
                  ('Compilation process',"compilation_process_seconds")]:
 rows.append([label,*[fmt(m(k,key))+" / "+fmt(m(k,key,"median")) for k in KS]])
t+=table(['Time: mean / median',"$k=1$","$k=5$","$k=10$"],rows)
t+="""\\textbf{Do not sum the components.} Preparation/selection includes RAG, prompt construction, tokenization, responses and checks. RAG time includes index loading and verification, not just search. Compilation process time includes startup and checks; internal time covers the compiler. Total covers the whole case.\\par\\subsection{Text volume and model requests}
Total tokens sum input/output across all calls, including repairs. Input also counts cache-served tokens; this is neither monetary cost nor only server-recomputed tokens.\\par"""
t+=table(['Measurement',"$k=1$","$k=5$","$k=10$"],[
row_metric('Mean first-attempt input',"first_input_tokens",1),
row_metric('Input tokens, sum',"input_tokens",0,"sum"),
row_metric('Output tokens, sum',"output_tokens",0,"sum"),
row_metric('Total tokens, sum',"total_tokens",0,"sum"),
row_metric('Mean total tokens per circuit',"total_tokens",1),
row_metric('Calls, sum',"llm_calls",0,"sum"),
row_metric('Repairs, sum',"retries",0,"sum"),
['Circuits with at least one repair',*[str(S[k]["retry_cases"])+"/90" for k in KS]],
['Responses with all facts valid on first attempt',*[str(S[k]["valid_first"])+"/90" for k in KS]],
['Final responses with all facts valid',*[str(S[k]["valid_final"])+"/90" for k in KS]],
['Valid final facts',*[f'{S[k]["facts_verified"]}/{S[k]["facts_total"]}' for k in KS]]])
t+='\\subsection{Changes relative to five examples}'+"\n"
t+=table(['Variant','Total tokens','Mean total time','$\\Delta$ mean score'],[
[f"$k={k}$",fmt(100*(m(k,"total_tokens","sum")/m("5","total_tokens","sum")-1))+r"\%",
 fmt(100*(m(k,"total_seconds")/m("5","total_seconds")-1))+r"\%",
 fmt(m(k,"score")-m("5","score"),8)] for k in ["1","10"]])
t+='First-input size grows with example count. Total cost grows further as repairs increase. Comparing first attempts separates initial prompt volume from repeated calls. Observed timings also include cache and host conditions not controlled through replicates.'
t+=page('Differences on the same circuits')
t+="All variants succeed on the same 90 circuits, so denominators match. Difference means first variant's score minus second variant's. A tie is $|\\Delta|\\leq10^{-12}$ on stored values, not a statistical equivalence test.\\par"
t+=table(['Comparison','Mean $\\Delta$','Better','Tied','Worse','Same pair'],[
[f"$k={p['a']}$ minus $k={p['b']}$",fmt(p["delta"]["mean"],8),str(p["wins"]),str(p["ties"]),str(p["losses"]),str(p["same_pair"])+"/90"] for p in D["pairs"]])
t+=r"\textbf{"+str(D["identical_all"])+' circuits out of 90 have exactly the same score in all three runs.} Median differences are always zero.\\par'
t+='\\subsection{All cases with different scores across variants}'+"\n"
t+='Cases are ordered by maximum-to-minimum score range. All are shown, without selecting only improvements.\\par'
t+=table(['Circuit',"$k=1$","$k=5$","$k=10$"],[
[r"\nolinkurl{"+c+"}",*[fmt(ROWS[k][c]["score"],8) for k in KS]] for c in D["changed_circuits"]])
t+='\\subsection{Results by qubit count}'+"\n"
t+=table(["Qubit",'Cases','Mean $k=1$','Mean $k=5$','Mean $k=10$'],[
[esc(g["label"]),str(g["n"]),*[fmt(g["score"][k]["mean"],6) for k in KS]] for g in D["qubit_groups"]])
t+='Size groups follow the reference comparison and do not alone define difficulty. Even above 16 qubits, ten examples offer no advantage over five: their scores match in that group. These data do not support automatic improvement on larger cases from adding examples, but concern this retrieval method and model.'
t+=page('Success, threshold and quality per circuit')
t+='Success and threshold counts use all 90 circuits. All three k values have equal coverage; score plots show how similar individual outcomes also are.\\par'
t+="""\\begin{center}\\begin{tikzpicture}\\begin{axis}[width=.86\\linewidth,height=4cm,ybar,bar width=14pt,ymin=0,ymax=103,symbolic x coords={k1,k5,k10},xtick={k1,k5,k10},xticklabels={$k=1$,$k=5$,$k=10$},ylabel={Circuits out of 90},nodes near coords,legend style={at={(.5,1.03)},anchor=south,legend columns=2,font=\\small}]
\\addplot[fill=kuno!70,draw=kuno] coordinates {(k1,90)(k5,90)(k10,90)};
\\addplot[fill=kcinque!70,draw=kcinque] coordinates {(k1,70)(k5,70)(k10,70)};
\\legend{Valid compilations,Score at least 0.8}\\end{axis}\\end{tikzpicture}\\end{center}
"""
for k in KS:
 t+=r"\begin{center}"+axis("score",k,"Score",height="3.75cm",width=".94\\linewidth",extra="ytick={0,.2,.4,.6,.8,1},")+r"\end{center}"+"\n"
t+='{\\small Shared alphabetical order and 0--1 scale. Median score is 0.921379 for all variants.}\\par'
t+=dual_page('Timing: full workflow and internal compilation',"total_seconds","compilation_seconds",'Total time (s)','Internal compilation (s)',
'Total cost grows with k. Mean internal compiler work stays near 1.7 seconds because choices change on few cases. Total-time peaks may reflect repairs or compilation and require the other records for interpretation.')
t+=dual_page('Timing: compilation process and LLM responses',"compilation_process_seconds","llm_response_seconds",'Compilation process (s)','LLM responses (s)',
'Left includes startup, compilation and checks. Right sums all LLM response waits for the same circuit. The clearest increase concerns the latter.')
t+=dual_page('Tokens and repair requests',"total_tokens","retries",'Total tokens','Repairs',
'Each repair requests another full response. Tokens include input/output of every call. Levels 0, 1 and 2 mean one, two and three responses. Shared scales show higher cost with ten examples.')
t+=dual_page('Preparation, retrieval and selection',"rag_seconds","choice_seconds",'RAG and checks (s)','Preparation and selection (s)',
'Retrieval timing includes source/index checks and averages about 3.6--3.9 seconds across campaigns. Selection also includes tokenization and LLM calls: increased total cost does not mean tenfold slower nearest-neighbor search.')
t+=page('Distributions and differences relative to five examples')
t+='The cumulative distribution gives the share of circuits with scores no greater than the horizontal value. Curves almost entirely overlap. Lower panels enlarge differences from k=5: zero means an equal score, not missing data.\\par'
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=6cm,xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score},ylabel={Quota cumulativa},grid=major,legend pos=north west]"+"\n"
for k,style in zip(KS,["solid","dashed","dotted"]):
 values=sorted(r["score"] for r in RUNS[k])
 t+=r"\addplot[const plot,thick,"+COLORS[k]+","+style+"] coordinates {"+coords([(0,0),*[(v,(i+1)/90) for i,v in enumerate(values)],(1,1)])+r"};\addlegendentry{$k="+k+"$}\n"
t+=r"\end{axis}\end{tikzpicture}\end{center}"
for k in ["1","10"]:
 t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=4.15cm,title={$k="+k+'$ minus $k=5$},xlabel={Circuit index},ylabel={Score difference},xmin=0,xmax=91,ymin=-.023,ymax=.002,xtick={1,15,30,45,60,75,90},grid=major]'
 t+=r"\addplot[gray,dashed,domain=0:91]{0};"
 t+=r"\addplot[only marks,mark=*,mark size=1.6pt,"+COLORS[k]+"] coordinates {"+coords([(i+1,ROWS[k][c]["score"]-ROWS["5"][c]["score"]) for i,c in enumerate(IDS)])+r"};\end{axis}\end{tikzpicture}\end{center}"
t+=page('Why costs grow and what facts show')
t+="""\\subsection{Initial input and total cost}
Left: mean first-attempt input tokens. Right: mean total per circuit, including output and repairs. Scales differ because the quantities differ.\\par"""
for title,key in [('Mean initial input',"first_input_tokens"),('Mean total per circuit',"total_tokens")]:
 t+=r"\begin{minipage}{.49\linewidth}\centering\begin{tikzpicture}\begin{axis}[width=.95\linewidth,height=5cm,ybar,bar width=22pt,bar shift=0pt,enlarge x limits=.3,ymin=0,ymax="+str(m("10",key)*1.22)+r",symbolic x coords={k1,k5,k10},xtick={k1,k5,k10},xticklabels={$k=1$,$k=5$,$k=10$},title={"+title+r"},ylabel={Token},scaled y ticks=false,tick label style={font=\small}]"
 for k in KS:t+=r"\addplot[fill="+COLORS[k]+"!75,draw="+COLORS[k]+"] coordinates {(k"+k+","+str(m(k,key))+")};"
 t+=r"\end{axis}\end{tikzpicture}\end{minipage}\hfill"
t+='\\par\\subsection{Content and validity of final facts}'+"\n"
types=[('Same device as the example',"selected_device_matches_example"),('Pair among shown results',"selected_pair_among_reported_best"),('Same qubit count',"same_qubit_count_as_example"),('Device capacity',"selected_device_has_enough_qubits")]
fr=[]
for label,kind in types:
 vals=[]
 for k in KS:
  items=[x for x in S[k]["fact_kinds"] if x["assertion"]==kind]
  vals.append(str(sum(x["n"] for x in items if x["result"]=="verified"))+"/"+str(sum(x["n"] for x in items)))
 fr.append([label,*vals])
t+=table(['Type: valid / declared',"$k=1$","$k=5$","$k=10$"],fr)
t+="""Device/configuration pairs are cited more often with ten examples: 35 final facts versus five with five examples and none with one. All these historical facts are supported by the cited records. Richer references do not yield appreciably higher current-circuit scores here.
Invalid facts number 2, 17 and 38. All associate device capacity with an example, although the rule requires the hardware catalog without \\texttt{example\\_id}. Capacity is sufficient: these are not 2, 17 and 38 impossible hardware choices.
The program requests repair but may accept an allowed pair with unverified facts on attempt three. This explains why every compilation can succeed despite invalid facts.
\\textbf{Free-text hypotheses are not semantically verified and must not be treated as established facts.} Correct structured facts certify neither the free explanation nor future choice quality.
"""
t+=page('Conclusions and limitations')
t+='\\subsection{Interpreting the comparison}'+"\n"
t+=('In these runs, k=1 offers the most favorable observed quality/cost balance. Relative to k=5, mean score is lower by '+
    fmt(m("5","score")-m("1","score"),8)+
    ' on a 0--1 scale; total tokens decrease by '+
    fmt(100*(1-m("1","total_tokens","sum")/m("5","total_tokens","sum")))+
    '\\% and mean total time by '+fmt(100*(1-m("1","total_seconds")/m("5","total_seconds")))+r"\%.\par"+"\n")
t+=('Moving from five to ten examples increases tokens by '+
    fmt(100*(m("10","total_tokens","sum")/m("5","total_tokens","sum")-1))+
    '\\% and mean total time by '+fmt(100*(m("10","total_seconds")/m("5","total_seconds")-1))+
    '\\%, without improving mean score. Repairs grow from 36 to 77 and final responses with invalid facts from 17 to 38.\\par'+"\n")
t+="""Results are consistent with the nearest example already supplying much of the useful information for this model and catalog. This is an \\textbf{interpretation}, not a general property of RAG. More examples may add references without improving decisions.
The most different case is \\nolinkurl{qpeinexact_indep_tket_6}: five or ten examples improve score by about 0.02113 over one. Keeping it visible prevents claiming identical variants on every circuit. Small mean differences are not relative percentages: a 0.000235 score difference is about 0.0235 percentage points on the 0--1 scale.
\\subsection{Limits of the conclusions}
One- and ten-example variants were chosen after Test inspection. This report does not retroactively change the validation-selected configuration. A more general operational choice would need new-data confirmation or dedicated selection.
Each circuit is evaluated once per variant. Corpus families are correlated; no replicates measure timing variation. Dates, code revisions and cache state differ. Models and call parameters match, but timings do not perfectly isolate k's causal effect. Energy and peak memory are unmeasured; no significance or statistical-equivalence test is presented.
\\subsection{Sources and reconstruction}
We checked 270 outcomes and """
t+=str(len(D["audited_attempts"]))
t+=""" complete responses, including repairs. Checks cover circuit/contract hashes, model identity, actual call parameters, circuit views, train examples, retrieval order, tokens and facts. Report generation performed no new inference or quantum compilation.
Sources are \\nolinkurl{test/risultati/llm_rag} for k=5 and \\nolinkurl{test/numero_esempi/k_1}, \\nolinkurl{test/numero_esempi/k_10} for the variants, relative to \\nolinkurl{archivio/valutazione}. The report follows the five-system comparison's success, 0.8 threshold, score, timing, token, repair, distribution and paired-comparison measures.
The directory retains \\texttt{dati.json}, \\texttt{provenienza.json}, \\texttt{tabelle/circuiti.csv}, the generator and standalone LaTeX. The appendix identifies every plotted point. Previous reports and experimental records remain unchanged.
"""
t+='\\clearpage\\appendix\\begin{landscape}\\section{Per-circuit values: score and total time}'+"\n"
t+='All cases succeeded. Times are seconds; full values remain in CSV. Indices are shared across plots.\\par'
t+='\\begingroup\\footnotesize\\setlength{\\tabcolsep}{4pt}\\renewcommand{\\arraystretch}{1.16}\\begin{longtable}{r l r rrr rrr}\\toprule Index & Circuit & Qubits & Score 1 & Score 5 & Score 10 & Time 1 & Time 5 & Time 10\\\\\\midrule\\endfirsthead\\toprule Index & Circuit & Qubits & Score 1 & Score 5 & Score 10 & Time 1 & Time 5 & Time 10\\\\\\midrule\\endhead\\bottomrule\\endfoot'+"\n"
for i,c in enumerate(IDS,1):
 vals=[str(i),esc(c),str(ROWS["5"][c]["num_qubits"]),*[fmt(ROWS[k][c]["score"],6) for k in KS],*[fmt(ROWS[k][c]["total_seconds"]) for k in KS]]
 t+=" & ".join(vals)+r"\\"+"\n"
t+=r"\end{longtable}\endgroup\end{landscape}"
t+='\\clearpage\\begin{landscape}\\section{Per-circuit values: tokens, repairs and facts}'+"\n"
t+='Tokens sum input/output across every attempt. C: repairs. V: all final facts valid (yes/no), not compilation success.\\par'
t+='\\begingroup\\footnotesize\\setlength{\\tabcolsep}{4pt}\\renewcommand{\\arraystretch}{1.16}\\begin{longtable}{r l rrr rrr ccc}\\toprule Index & Circuit & Tokens 1 & Tokens 5 & Tokens 10 & C1 & C5 & C10 & V1 & V5 & V10\\\\\\midrule\\endfirsthead\\toprule Index & Circuit & Tokens 1 & Tokens 5 & Tokens 10 & C1 & C5 & C10 & V1 & V5 & V10\\\\\\midrule\\endhead\\bottomrule\\endfoot'+"\n"
for i,c in enumerate(IDS,1):
 vals=[str(i),esc(c),*[fmt(ROWS[k][c]["total_tokens"],0) for k in KS],*[str(ROWS[k][c]["retries"]) for k in KS],*['yes' if ROWS[k][c]["facts_status"]=="verified" else "no" for k in KS]]
 t+=" & ".join(vals)+r"\\"+"\n"
t+=r"\end{longtable}\endgroup\end{landscape}\end{document}"+"\n"
(BASE/"confronto_k.tex").write_text(t,encoding="utf-8")
print(BASE/"confronto_k.tex")

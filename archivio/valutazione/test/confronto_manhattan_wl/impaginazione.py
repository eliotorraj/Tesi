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
KS=["M","W","S"]
LABELS={"M":"Manhattan","W":"WL","S":'WL + summary'}
S=D["summary"]
RUNS=D["runs"]
ROWS={k:{r["circuit_id"]:r for r in RUNS[k]} for k in KS}
IDS=sorted(ROWS["M"])
COLORS={"M":"kuno","W":"kcinque","S":"kdieci"}
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
    return (r"\par\medskip\begingroup\small\renewcommand{\arraystretch}{1.18}\setlength{\tabcolsep}{5pt}"
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
    options=(f'width={width},height={height},title={{{LABELS[k]}}},xlabel={{Circuit index}},ylabel={{{label}}},xmin=0,xmax=91,ymin=0,ymax={maximum:.12g},xtick={{1,15,30,45,60,75,90}},grid=major,scaled y ticks=false,tick label style={{font=\\scriptsize}},label style={{font=\\small}},title style={{font=\\bfseries}},'+extra)
    pts=[(r["index"],r[metric]) for r in RUNS[k]]
    return r"\begin{tikzpicture}\begin{axis}["+options+"]\n"+r"\addplot[only marks,mark=*,mark size=1.1pt,color="+COLORS[k]+",fill="+COLORS[k]+"] coordinates {"+coords(pts)+r"};\end{axis}\end{tikzpicture}"
def dual_page(title,a,b,la,lb,note):
    text=page(title)+note+r"\par\medskip"+"\n"
    text+=r"\noindent\begin{minipage}{.49\linewidth}\centering\textbf{"+la+r"}\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering\textbf{"+lb+r"}\end{minipage}\par"+"\n"
    for k in KS:
        text+=r"\noindent\begin{minipage}{.49\linewidth}\centering"+axis(a,k,la)+r"\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering"+axis(b,k,lb)+r"\end{minipage}\par\medskip"+"\n"
    text+="{\\small Each point is a circuit. Column scales are shared across the three systems. Indices follow the appendix's alphabetical order.}\\par"
    return text

PRE="""\\documentclass[a4paper,10pt]{article}
\\usepackage[margin=1.8cm]{geometry}
\\usepackage[T1]{fontenc}\\usepackage[utf8]{inputenc}\\usepackage[english]{babel}
\\usepackage{lmodern,booktabs,tabularx,longtable,array,amsmath,xcolor,pgfplots,xurl,hyperref,fancyvrb}
\\usepackage[expansion=false]{microtype}
\\usetikzlibrary{arrows.meta,positioning}
\\pgfplotsset{compat=1.18}
\\definecolor{kuno}{HTML}{167D9A}\\definecolor{kcinque}{HTML}{D47A17}\\definecolor{kdieci}{HTML}{7656A3}
\\hypersetup{hidelinks}\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{5pt}\\setlength{\\emergencystretch}{3em}
\\begin{document}
{\\small\\bfseries PRESERVED-RECORD COMPARISON | 29 September 2026}\\par
{\\LARGE\\bfseries Retrieving examples from circuit structure}\\par
{\\Large Manhattan RAG, WL RAG and WL RAG with summaries}\\par\\medskip
\\section{From feature distance to dependencies}
A useful historical example should help select a device and configuration for the current circuit. Classical retrieval compares 49 train-transformed numeric features by Manhattan distance. Structural retrieval instead represents operation dependencies and compares graphs. The hypothesis is that similarly structured circuits may need similar compilation choices; this must be measured rather than assumed.
Qiskit represents a circuit as a \\texttt{DAGCircuit}, a directed acyclic graph: operations are nodes and wires link successive operations. A two-qubit gate is one node with two incoming and outgoing wires \\cite{qiskit}. This DAG represents precedence, not device connectivity.
\\subsection{Example: same gates, different order}
In A, Z follows CX on the second qubit; in B it precedes CX. Both circuits have two qubits and the same three gates, but different DAGs. $I_i$ and $O_i$ denote inputs and outputs. Colors only aid reading.
"""
def drawing(before):
    # Circuit uses the same H/CX/Z dependencies as the DAG below.
    zpos=1.2 if before else 3.5
    out=r"\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth]"
    out+=r"\draw (0,0)--(4.2,0);\draw (0,-.8)--(4.2,-.8);\node[left] at (0,0){$q_0$};\node[left] at (0,-.8){$q_1$};"
    out+=r"\node[draw,fill=white,minimum size=.45cm] at (1.2,0){H};"
    out+=r"\draw (2.5,0)--(2.5,-.8);\fill (2.5,0) circle (2.5pt);\draw (2.5,-.8) circle (5pt);\draw (2.5,-1)--(2.5,-.6);"
    out+=r"\node[draw,fill=white,minimum size=.45cm] at ("+str(zpos)+r",-.8){Z};\end{tikzpicture}\par\medskip"
    out+=r"\begin{tikzpicture}[x=.85cm,y=.8cm,>=Stealth,n/.style={draw,rounded corners,fill=white,minimum size=.5cm,font=\small}]"
    out+=r"\node[n] (i0) at (0,1){$I_0$};\node[n] (i1) at (0,-1){$I_1$};\node[n,fill=kuno!15] (h) at (1.3,1){H};\node[n,fill=kcinque!20] (c) at (2.7,0){CX};\node[n] (o0) at (5.1,1){$O_0$};\node[n] (o1) at (5.1,-1){$O_1$};"
    out+=r"\node[n,fill=kdieci!15] (z) at ("+("1.3" if before else "3.8")+r",-1){Z};"
    out+=r"\draw[->] (i0)--(h);\draw[->] (h)--(c);\draw[->] (c)--(o0);"
    out+=(r"\draw[->] (i1)--(z);\draw[->] (z)--(c);\draw[->] (c)--(o1);" if before else r"\draw[->] (i1)--(c);\draw[->] (c)--(z);\draw[->] (z)--(o1);")
    return out+r"\end{tikzpicture}"
t=PRE
for name,before in [('A: Z after CX',False),('B: Z before CX',True)]:
 t+=r"\begin{minipage}{.49\linewidth}\centering\textbf{"+name+r"}\par\medskip"+drawing(before)+r"\end{minipage}\hfill"
t+="""\\par\\medskip
The implementation also retains measurements, barriers and classical wires. Arrows follow circuit direction. Original QASM gates are not decomposed, so source representation can affect similarity.
"""
t+=page('WL explained through the two graphs')
t+="""Weisfeiler--Lehman (WL) builds increasingly broad local descriptions: nodes start with labels and update them from neighbors each round. Label counts then compare graphs \\cite{wl}. This implementation adapts WL to directed, labeled edges.
\\textbf{Round 0.} H, CX and Z are identified by operation type; initial counts match in the two small graphs.
\\textbf{Round 1.} Each node considers predecessors and successors separately. CX in A sees Z as a successor; in B, as a predecessor, producing different new labels. Z's context also changes. H sees input and CX in both graphs, so its labels still match.
\\textbf{Round 2.} H now receives CX's differing label. The difference propagates to H. Later rounds collect increasingly distant information without adding circuit operations.
"""
t+=table(['Node','Round 0, A/B','Round 1, A/B','Round 2, A/B'],[
["H","uguale","uguale","diversa"],["CX","uguale","diversa","diversa"],["Z","uguale","diversa","diversa"]])
t+="""\\subsection{Implementation}
Initial labels contain gate name, operand count, control state and numerical parameters binned in $\\pi/8$ intervals. Absolute qubit names are excluded. Edges retain quantum/classical type and local operand position, distinguishing CX control and target. Barrier ports are symmetric; repeated edges are retained.
Each new label summarizes its previous label and incoming/outgoing neighbor multisets, including edge labels. Identical descriptions receive identical IDs across graphs. If $\\phi_r(G)$ counts round-$r$ labels, similarity is:\\[s_h(G,H)=\\frac{\\sum_{r=0}^{h}\\langle\\phi_r(G),\\phi_r(H)\\rangle}{\\sqrt{\\sum_{r=0}^{h}\\|\\phi_r(G)\\|^2}\\sqrt{\\sum_{r=0}^{h}\\|\\phi_r(H)\\|^2}}.\\]
Retrieve the five compatible train examples with greatest similarity, breaking ties by RAG ID. Test uses $h=24$, combining initial labels and 24 updates. Normalization reduces but does not eliminate size effects.
\\textbf{Limit.} High similarity does not imply quantum equivalence, equal fidelity or the same optimal choice. WL can fail to distinguish different graphs. Results depend on labels, parameter bins, original gates and depth. These are implementation decisions, not conclusions of the cited theoretical work.
"""
t+=page('Validation and controlled comparison')
v=D["validation"]["methods"]
t+="""Before the new Test runs, depth was selected on 88 validation circuits separate from the 90 Test circuits. Search was extended to 6 and then 30 rounds after inspecting earlier results, making it adaptive selection on the same 88 cases.
Validation did not call the LLM. It retrieved examples and scored the first-ranked pair of the first example using the validation circuit's archived compilation results. Pair score was the median of seeds 0, 1 and 2 with three successes; regret was the difference from the best available observed score. Seventy matrices were incomplete, so the reference is not a certified global optimum.
"""
t+=table(['Method','Mean score','Mean regret','Comparison (s)'],[
["Manhattan" if key=="manhattan" else "$h="+key[4:]+"$",fmt(v[key]["top1_score"]["mean"],6),fmt(v[key]["top1_regret_common"]["mean"],6),fmt(v[key]["ranking_seconds"]["mean"],3)]
 for key in ["manhattan","wl_h1","wl_h6","wl_h23","wl_h24","wl_h27","wl_h30"]])
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.91\linewidth,height=5cm,xmin=1,xmax=30,xlabel={Giri WL},ylabel={Score medio, validation},grid=major,legend pos=south east]"
t+=r"\addplot[thick,kcinque,mark=*,mark size=1.3pt] coordinates {"+coords([(h,v[f"wl_h{h}"]["top1_score"]["mean"]) for h in range(1,31)])+r"};\addlegendentry{WL}"
t+=r"\addplot[kuno,dashed,domain=1:30]{"+str(v["manhattan"]["top1_score"]["mean"])+r"};\addlegendentry{Manhattan}"
t+=r"\addplot[only marks,kdieci,mark=*,mark size=3pt] coordinates {(24,"+str(v["wl_h24"]["top1_score"]["mean"])+')};\\addlegendentry{Selected $h=24$}\\end{axis}\\end{tikzpicture}\\end{center}'
t+="""$h=24$ was fixed as the first depth sharing minimum regret with 25--27 and identical per-circuit scores. Its mean advantage over 23 is only 0.00000366; no statistical significance is claimed. Among tied depths, 24 takes less time and slightly improves a secondary five-example indicator. Selection was frozen before the new Test runs.
\\subsection{Three systems with the same example count}
"""
t+=table(['System','Retrieval','Information in the prompt'],[
["Manhattan (M)",'49 features','Standard prompt, five examples'],
["WL (W)","DAG, $h=24$",'Standard prompt, five examples'],
['WL + summary (S)',"DAG, $h=24$",'Classical prompt and summaries of six graphs']],"l l X")
t+='W and S retrieved identical five records, order and similarities on all 90 cases. Train remains unchanged: summaries are added dynamically to the current circuit and examples E1--E5. Response format and fact rules are shared.'
t+=page('An actual field added to the prompt')
ex=D["example"]; cur=ex["summaries"]["current_circuit"]; e1=ex["summaries"]["examples"][0]["summary"]
t+='The case is \\nolinkurl{'+ex["circuit_id"]+'}. This excerpt comes from the TOON block actually sent to the model and checked against \\texttt{prompt.json}. Other statistics and E1--E5 summaries are omitted.\\par'
lines=ex["actual_summary_toon"].splitlines()
end=next(i for i,line in enumerate(lines) if "most_frequent_direct_transitions" in line)
t+=r"\begin{Verbatim}[fontsize=\small,frame=single]"+"\n"+"\n".join(lines[:end])+"\n"+r"\end{Verbatim}"+"\n"
t+="""\\texttt{two\\_qubit\\_interaction\\_pairs: 66} means that 66 distinct current-circuit qubit pairs participate in two-qubit gates. For 12 qubits, these are all possible pairs. This describes the source, not future fidelity. \\texttt{dependency\\_layers\\_including\\_barriers} counts dependency layers including barriers; it is not physical duration and may differ from the classical prompt's depth.
"""
t+=table(['Field','Current circuit','Example E1'],[
["Qubit",cur["num_qubits"],e1["num_qubits"]],
['Operations, including barriers',cur["operation_nodes_including_barriers"],e1["operation_nodes_including_barriers"]],
['Dependency levels',cur["dependency_layers_including_barriers"],e1["dependency_layers_including_barriers"]],
['Interaction pairs',cur["two_qubit_interaction_pairs"],e1["two_qubit_interaction_pairs"]]])
t+='\\small Field \\texttt{dag\\_summaries.examples[0].example\\_id = E1} links the summary to the first retrieved record: \\nolinkurl{'+ex["records"][0]["rag_id"]+'}. The link was checked using the separate index. The full block also includes the eight most frequent directed transitions.\\normalsize\\par'
t+='The program computes these quantities; they are not invented LLM descriptions. The model may use them in its free explanation, but fact verification was not extended with new graph assertions.'
t+=page('Results on 90 Test circuits')
t+="""All systems use Qwen3.5-4B Q8\\_0 with the same weights, temperature 0, seed 20260913 and maximum output 4,096 tokens. Requested context is 60,000; extended reasoning is disabled. Five synthetic Targets, twelve Qiskit configurations, compilation seed 0, one worker and an external 100-second limit remain unchanged. Records cover exactly the same 90 Test sources.
Expected fidelity ranges from 0 to 1, higher being better. It estimates synthetic-Target performance rather than measuring physical hardware. Every compilation succeeds, so score means always have denominator 90.
"""
HEAD=['Measurement',*[LABELS[k] for k in KS]]
t+=table(HEAD,[
['Successful compilations',*[str(S[k]["successes"])+"/90" for k in KS]],
['Failures',*[str(90-S[k]["successes"]) for k in KS]],
row_metric('Mean score',"score",6),row_metric('Median score',"score",6,"median"),
['Score at least 0.8',*[str(S[k]["threshold_08"])+"/90" for k in KS]],
row_metric('Mean total time (s)',"total_seconds"),row_metric('Total tokens, sum',"total_tokens",0,"sum")])
t+=r"\subsection{Confronti appaiati}"
t+=table(['Difference','Mean score','Better','Tied','Worse','Same pair'],[
[LABELS[p["a"]]+' minus '+LABELS[p["b"]],fmt(p["delta"]["mean"],6),p["wins"],p["ties"],p["losses"],str(p["same_pair"])+"/90"] for p in D["pairs"]])
t+='Ties use $|\\Delta|\\leq10^{-12}$. A pair is device/configuration; equal scores need not mean equal choices. Means are not percentages of improved circuits.\\par'
t+=table(["Qubit",'Cases',"Manhattan","WL",'WL + summary'],[
[g["label"],g["n"],*[fmt(g["score"][k]["mean"],6) for k in KS]] for g in D["qubit_groups"]])
t+='Size groups follow the earlier report and are descriptive. Qubit count alone does not define difficulty. All cases, including low scores, enter tables and plots.'
t+=page('Where scores change')
changed=D["changed_circuits"]
t+=str(D["identical_all"])+' circuits have the same score in all three systems. The table shows '+str(min(12,len(changed)))+' cases with greatest maximum-to-minimum range, ordered without favoring a variant. The appendix includes all 90.\\par'
t+=table(['Circuit',"Manhattan","WL",'WL + summary'],[
[r"\nolinkurl{"+c+"}",*[fmt(ROWS[k][c]["score"],6) for k in KS]] for c in changed[:12]])
t+="""The five S-versus-W losses change devices: from Quantinuum H2 to IBM Falcon 127 for 30--40-qubit QPE, and to IBM Heron 156 for the two 50-qubit cases. For example, \\texttt{qpeexact\\_indep\\_qiskit\\_30} falls from 0.520294 to 0.043532. This is an observed choice change, not proof that one summary statistic caused it.
"""
t+='\\subsection{Retrieval differences}'
overlap=[len(set(D["retrieval_ids"]["M"][c])&set(D["retrieval_ids"]["W"][c])) for c in IDS]
t+=f'Manhattan and WL share an average of {fmt(sum(overlap) / 90, 2)} examples out of five. '
t+=f"In {sum((D['retrieval_ids']['M'][c] == D['retrieval_ids']['W'][c] for c in IDS))} cases out of 90 have identical records and order. "
t+='W and S always retrieve identical examples: response differences are observed with the same historical evidence plus graph information.\\par'
t+='\\subsection{Changes in the selected pair}'
for p in D["pairs"]:
 t+=LABELS[p["a"]]+' compared with '+LABELS[p["b"]]+": "+str(90-p["same_pair"])+' different pairs out of 90.\\par '
t+=page('Times: distinguish the components')
t+='Each cell shows mean / median seconds across 90 measurements. Do not sum rows: some components include others.\\par'
t+=table(HEAD,[[lab,*[fmt(m(k,key))+" / "+fmt(m(k,key,"median")) for k in KS]] for lab,key in [
('Case total',"total_seconds"),('Preparation and selection',"choice_seconds"),('RAG and checks',"rag_seconds"),
('LLM responses, cumulative',"llm_response_seconds"),('Internal compilation',"compilation_seconds"),('Compilation process',"compilation_process_seconds")]])
t+="""Total time covers the whole case. Preparation and selection include retrieval, prompt construction, tokenization, responses and checks. LLM time sums response waits, including repairs. Internal compilation time measures the compiler; process time includes startup and checks.
The WL maximum, 297.36 seconds for \\texttt{qpeexact\\_indep\\_qiskit\\_15}, includes 295.98 seconds of preparation/selection but only 24.65 seconds of LLM responses. Detailed phases do not explain the entire wait, so it is not attributed to WL. The case remains in the mean.
\\subsection{WL index cost is separate}
Manhattan's per-circuit RAG timing includes index checks and loading. The new systems check/load WL once per session and reuse it. This separately recorded cost is excluded from individual totals. Direct RAG timing comparisons therefore do not isolate algorithm speed.
"""
prep={k:sum(r["index_preparation_seconds"] for r in D["preparation"][k]) for k in ["W","S"]}
t+=table(['Measurement',"WL",'WL + summary'],[
['Recorded index preparation (s)',*[fmt(prep[k]) for k in ["W","S"]]],
['Computed share per 90 cases (s)',*[fmt(prep[k]/90) for k in ["W","S"]]],
['Mean total + index share (s)',*[fmt(m(k,"total_seconds")+prep[k]/90) for k in ["W","S"]]]])
t+='The allocated share is computed, not newly measured, and does not reconstruct historical index-building costs. Campaigns are not interleaved replicates: host load, cache and server startup affect time. Memory was not collected and cannot be compared.'
t+=page('Tokens, calls and fact correctness')
t+=table(HEAD,[
row_metric('First input, mean tokens',"first_input_tokens",1),
row_metric('Input, token sum',"input_tokens",0,"sum"),
row_metric('Output, token sum',"output_tokens",0,"sum"),
row_metric('Total token sum',"total_tokens",0,"sum"),
row_metric('Mean total per circuit',"total_tokens",1),
row_metric('Calls, sum',"llm_calls",0,"sum"),
row_metric('Repairs, sum',"retries",0,"sum"),
['Cases with repairs',*[str(S[k]["retry_cases"])+"/90" for k in KS]],
['All facts valid on first attempt',*[str(S[k]["valid_first"])+"/90" for k in KS]],
['All facts valid in final response',*[str(S[k]["valid_final"])+"/90" for k in KS]],
['Valid / declared final facts',*[f'{S[k]["facts_verified"]}/{S[k]["facts_total"]}' for k in KS]]])
t+="""Total tokens include input and output of every call. Input includes cache-served tokens, so it measures neither recomputed tokens alone nor monetary cost. First input separates initial prompt size from repair cost. At most three responses are allowed per circuit.
"""
types=[('Same device as the example',"selected_device_matches_example"),('Pair among shown results',"selected_pair_among_reported_best"),('Same qubit count',"same_qubit_count_as_example"),('Device capacity',"selected_device_has_enough_qubits")]
fr=[]
for label,kind in types:
 vals=[]
 for k in KS:
  items=[x for x in S[k]["fact_kinds"] if x["assertion"]==kind]
  vals.append(str(sum(x["n"] for x in items if x["result"]=="verified"))+"/"+str(sum(x["n"] for x in items)))
 fr.append([label,*vals])
t+=table(['Type: valid / declared',*[LABELS[k] for k in KS]],fr)
t+="""Invalid facts total 17, 33 and 54. In respectively 17, 33 and 53 cases, device capacity is associated with an example, although the rule requires the hardware catalog without E1--E5 references. This support error does not mean insufficient qubits. S also contains an incorrect historical reference: \\texttt{qpeexact\\_indep\\_qiskit\\_30} claims the same device as E4 (Quantinuum H2) while selecting IBM Falcon 127.
These are automatic structured-fact checks against cited records and the catalog. A final response may contain invalid facts with an allowed pair after the third attempt. Compilation success does not certify explanation.
\\textbf{Free-text hypotheses are not verified semantically and must not be treated as established facts.} Free deductions from graph summaries also remain hypotheses. Valid historical facts describe the cited example, not the current circuit's guaranteed score.
"""
t+=dual_page('Score and total time per circuit',"score","total_seconds","Score",'Total time (s)',
'Same 90 circuits and order in every panel. Score scale is 0--1. Cost differences are measurements from preserved campaigns.')
t+=dual_page('Compilation: internal and process time',"compilation_seconds","compilation_process_seconds",'Internal (s)','Process (s)',
'Process time includes startup and checks. Different choices can yield different compilations; these timings do not measure retrieval alone.')
t+=dual_page('Tokens and LLM response time',"total_tokens","llm_response_seconds",'Total tokens','LLM responses (s)',
'Both columns include every call for the same case. A large value may also reflect repair requests.')
t+=dual_page('Repairs and retrieval',"retries","rag_seconds",'Repairs','RAG and checks (s)',
'Zero, one and two count additional responses. RAG excludes per-session WL index preparation, reported separately.')
t+=page('Score distribution and paired differences')
t+='The cumulative curve gives the share of circuits with scores no greater than the horizontal value. Each point below is a difference on the same circuit; zero means a tie.\\par'
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=5cm,xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score},ylabel={Quota cumulativa},grid=major,legend pos=north west]"
for k,style in zip(KS,["solid","dashed","dotted"]):
 vals=sorted(r["score"] for r in RUNS[k])
 t+=r"\addplot[const plot,thick,"+COLORS[k]+","+style+"] coordinates {"+coords([(0,0),*[(x,(i+1)/90) for i,x in enumerate(vals)],(1,1)])+r"};\addlegendentry{"+LABELS[k]+"}"
t+=r"\end{axis}\end{tikzpicture}\end{center}"
deltas=[ROWS[k][c]["score"]-ROWS["M"][c]["score"] for k in ["W","S"] for c in IDS]
lo=min(deltas)-.02;hi=max(deltas)+.02
for k in ["W","S"]:
 t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=4.8cm,title={"+LABELS[k]+' minus Manhattan},xlabel={Circuit index},ylabel={Score difference},xmin=0,xmax=91,ymin='+str(lo)+",ymax="+str(hi)+r",grid=major]"
 t+=r"\addplot[gray,dashed,domain=0:91]{0};\addplot[only marks,mark size=1.5pt,"+COLORS[k]+"] coordinates {"+coords([(i+1,ROWS[k][c]["score"]-ROWS["M"][c]["score"]) for i,c in enumerate(IDS)])+r"};\end{axis}\end{tikzpicture}\end{center}"
t+=page('Comparison conclusions and limits')
t+='\\subsection{What these Test runs show}'
for p in D["pairs"]:
 a,b=p["a"],p["b"]
 t+=LABELS[a]+' compared with '+LABELS[b]+': mean score difference '+fmt(p["delta"]["mean"],6)+', with '+str(p["wins"])+' improvements, '+str(p["ties"])+' ties and '+str(p["losses"])+' decreases out of 90.\\par'
t+='Adding summaries, relative to WL alone, changes mean first input by '+fmt(100*(m("S","first_input_tokens")/m("W","first_input_tokens")-1))+'\\% and total tokens by '+fmt(100*(m("S","total_tokens","sum")/m("W","total_tokens","sum")-1))+'\\%. Observed mean total time changes by '+fmt(100*(m("S","total_seconds")/m("W","total_seconds")-1))+r"\%.\par"
t+="""WL alone is nearly indistinguishable from Manhattan in the mean: the difference is $-0.0000259$. Adding summaries loses about 0.01938 relative to WL, or 1.938 percentage points on the score scale. The five losses concern 30-, 40- and 50-qubit QPE. Above 16 qubits, the mean falls from 0.279117 to 0.181878, while the 0.8 threshold count stays 70/90 because these cases were already below it. Threshold coverage alone would hide the loss.
Validation measured transfer of a historical choice, not an LLM response. Better retrieval by that criterion does not force better LLM choices. W--S instead holds retrieved records constant, allowing observation of the added information's effect on responses, tokens and repairs.
"""
# Data-dependent conclusion, never copied from older report.
best=max(KS,key=lambda k:m(k,"score"))
t+='The highest observed mean score belongs to '+LABELS[best]+". "
if m("S","score")<=m("W","score"):
 t+='Adding summaries does not improve mean score over WL alone in this sample. '
else:
 t+='Adding summaries improves mean score over WL alone in this sample. '
t+="""This describes the preserved runs and does not prove that the same ranking holds for other models or circuits.
\\subsection{Limits and provenance}
Manhattan is the historical 21 September run; WL runs are from 29 September. Weights, generation parameters and input sources match, but code revisions, dates and index handling differ. No interleaved replicates or memory measurements were collected. Means are not a statistical superiority test.
Depth selection uses validation only, but campaign design followed analysis of earlier Test outcomes on these same 90 circuits. This is not a fresh unseen confirmation sample; circuits from the same family may also be correlated.
The report reconstructs circuit records rather than transcribing means. IDs, source hashes, contracts, model, call settings, retrieval, tokens, transmitted summaries and fact checks were verified. No new inference or quantum compilation was performed. Scripts, complete tables and source hashes are preserved beside the PDF.
\\subsection{Reproducibility}
\\texttt{genera\\_report.py} produces \\texttt{dati.json}, \\texttt{provenienza.json} and \\texttt{tabelle/circuiti.csv} from records. \\texttt{impaginazione.py} generates this standalone source with embedded vector plots. The first script's \\texttt{--output} creates a new directory without overwriting earlier analysis.
"""
t+=page('Appendix: all circuits and three scores')
t+='The index matches the plots. CSV also retains all timing, token and fact measurements without display rounding.\\par'
t+='\\begingroup\\small\\renewcommand{\\arraystretch}{1.1}\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{r p{8.2cm} r r r}\\toprule N & Circuit & Manhattan & WL & WL + summary\\\\\\midrule\\endfirsthead\\toprule N & Circuit & Manhattan & WL & WL + summary\\\\\\midrule\\endhead'
for i,c in enumerate(IDS):
 if i==45:t+=r"\pagebreak[4]"+"\n"
 t+=str(i+1)+r" & \nolinkurl{"+c+"} & "+" & ".join(fmt(ROWS[k][c]["score"],6) for k in KS)+r"\\ "+ "\n"
t+=r"\bottomrule\end{longtable}\endgroup"
t+=page('Appendix: per-circuit costs')
t+='Each cell shows total seconds / total tokens / repairs. WL timings exclude per-session index cost. Circuit indices refer to the preceding table.\\par'
t+=r"\begingroup\small\renewcommand{\arraystretch}{1.1}\setlength{\tabcolsep}{6pt}\begin{longtable}{r r r r}\toprule N & Manhattan: s / token / corr. & WL: s / token / corr. & WL + sintesi: s / token / corr.\\\midrule\endfirsthead\toprule N & Manhattan: s / token / corr. & WL: s / token / corr. & WL + sintesi: s / token / corr.\\\midrule\endhead"
for i,c in enumerate(IDS):
 if i==45:t+=r"\pagebreak[4]"+"\n"
 t+=str(i+1)+" & "+" & ".join(fmt(ROWS[k][c]["total_seconds"])+" / "+fmt(ROWS[k][c]["total_tokens"],0)+" / "+str(ROWS[k][c]["retries"]) for k in KS)+r"\\ "+"\n"
t+="""\\bottomrule\\end{longtable}\\endgroup
\\begin{thebibliography}{9}
\\bibitem{wl} N. Shervashidze, P. Schweitzer, E. J. van Leeuwen, K. Mehlhorn, K. M. Borgwardt. \\emph{Weisfeiler--Lehman Graph Kernels}. JMLR 12, 2011, 2539--2561. \\url{https://jmlr.org/papers/v12/shervashidze11a.html}.
\\bibitem{qiskit} IBM Quantum. \\emph{DAGCircuit}, official Qiskit documentation, accessed 29 September 2026. This report follows the local Qiskit 2.5.0 implementation. \\url{https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.dagcircuit.DAGCircuit}.
\\end{thebibliography}\\end{document}
"""
import re
t=re.sub(r"\\par(?=[A-Z])",lambda _:r"\par ",t)
(BASE/"confronto_manhattan_wl.tex").write_text(t,encoding="utf-8")
print(BASE/"confronto_manhattan_wl.tex")

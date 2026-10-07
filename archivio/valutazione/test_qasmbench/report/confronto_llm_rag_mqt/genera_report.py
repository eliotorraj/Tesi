'Generate standalone LaTeX and comparison data. Does not run experiments.'
from __future__ import annotations
import json, statistics
from collections import Counter
from pathlib import Path
from dati import HERE, METHODS, analyze, sha

NAMES={"llm_rag":"LLM + RAG","mqt_predictor":"MQT Predictor"}
GN={"all":'Total',"small":'Small',"medium":'Medium',"large":'Large'}
DEV={"ibm_falcon_27":"F27","ibm_falcon_127":"F127","ibm_heron_133":"H133","ibm_heron_156":"H156","quantinuum_h2_56":"Q56"}
def tex(x):
    return "".join({"\\":r"\textbackslash{}","_":r"\_","%":r"\%","&":r"\&","#":r"\#","{":r"\{","}":r"\}","$":r"\$"}.get(c,c) for c in str(x))
def num(x,d=2,sign=False):
    if x is None:return "--"
    s=(f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}").replace(",","X").replace(".",",").replace("X",r"\,")
    return s
def short(cid):return tex(cid.removeprefix("qasmbench_"))
def table(headers,rows,spec=None,small=True):
    spec=spec or ("l"+"r"*(len(headers)-1))
    return (r"\begin{center}"+("\n"+r"\small" if small else "")+"\n"+r"\setlength{\tabcolsep}{5pt}"+"\n"+
       r"\begin{tabular}{"+spec+"}\n"+r"\toprule"+"\n"+" & ".join(headers)+r"\\"+"\n"+r"\midrule"+"\n"+
       "\n".join(" & ".join(str(c) for c in row)+r"\\" for row in rows)+"\n"+r"\bottomrule"+"\n"+r"\end{tabular}\end{center}"+"\n")
def coords(pairs):
    return " ".join(f"({x:.10g},{y:.10g})" for x,y in pairs)
def plot(data,style):
    return r"\addplot["+style+"] coordinates {"+coords(data)+"};\n"
def axis(content,options="",width=r"\textwidth",height="6.4cm"):
    return r"\begin{tikzpicture}\begin{axis}[width="+width+",height="+height+","+options+"]\n"+content+r"\end{axis}\end{tikzpicture}"+"\n"
def fig(content,caption):
    return r"\begin{figure}[H]\centering"+"\n"+content+r"\caption{"+caption+"}\n"+r"\end{figure}"+"\n"
def two(a,b):
    return r"\begin{minipage}[t]{.48\textwidth}\centering"+a+r"\end{minipage}\hfill\begin{minipage}[t]{.48\textwidth}\centering"+b+r"\end{minipage}"
def ecdf(values):
    return [(v,(i+1)/len(values)*100) for i,v in enumerate(sorted(values))]
def section(title):return r"\clearpage\section{"+title+"}\n"
def render(rows,res,s):
    'Return LaTeX with the approved QASMBench comparison text.'
    gg=s["groups"]; g=gg["all"]; paired=s["paired"]; pp=g["paired"]; methods=g["methods"]
    def stat(m,k,key="mean"):return methods[m]["metrics"][k][key]
    def v(m,c):return res[m,c]
    a,b=METHODS
    body=[]
    body.append("""
\\begin{center}
{\\small\\color{muted} EVALUATION OF QUANTUM COMPILATION SYSTEMS}\\\\[8pt]
{\\LARGE\\bfseries\\color{navy} LLM + RAG and MQT Predictor}\\\\[5pt]
{\\Large Comparison on QASMBench}\\\\[9pt]
{\\large Additional independent test}\\\\[7pt]
{\\small Runs from 30 September 2026 · 50 circuits · 2 systems}
\\end{center}
\\vspace{8pt}
\\section{Main results}
The test uses QASMBench circuits, distinct from the project's MQT Bench corpus.
The selection contains 30 small, 15 medium and 5 large circuits. This document analyzes
preserved records; it does not start new compilations or change the evaluated configurations.

""")
    body.append(table(['Indicator',"LLM + RAG","MQT Predictor"],[
        ['Successful compilations / expected circuits',"50/50 (100\\%)","48/50 (96\\%)"],
        ['Score at least 0.8 / expected circuits',"41/50 (82\\%)","43/50 (86\\%)"],
        ['Mean score: the same 48 circuits',num(pp["llm_score"]["mean"],4),num(pp["mqt_score"]["mean"],4)],
        ['Mean total time: same 48 circuits',num(pp["llm_total"]["mean"])+" s",num(pp["mqt_total"]["mean"])+" s"],
        ['Mean internal compilation: same 48',num(pp["llm_compile"]["mean"])+" s",num(pp["mqt_compile"]["mean"])+" s"]]))
    body.append("""\\paragraph{Coverage.}
LLM + RAG completes all circuits. MQT Predictor finishes within the limit on 48 circuits.
The two timeouts, on \\texttt{gcm\\_n13} and \\texttt{qft\\_n63}, are reported separately:
they are not assigned a zero score.
\\paragraph{Quality.}

"""+f"On the 48 shared successes, MQT Predictor achieves a higher mean score by {num(-pp['mean_difference_llm_minus_mqt'], 4)}. "+
    f"LLM + RAG achieves the higher score in {pp['llm_wins']} cases and MQT in {pp['mqt_wins']}; there are no ties. "+
"""The largest differences favoring MQT are concentrated in some medium circuits.
\\paragraph{Times.}
Internal compilation chosen by the LLM is faster on all 48 shared successes.
However, the time needed to prepare and obtain the LLM decision changes the
overall result: MQT is faster in 45 of these 48 cases.
\\paragraph{Interpreting the comparison.}
The score is \\emph{estimated} fidelity on synthetic Targets, not a quantum hardware measurement.
The test compares two complete systems with different compilation strategies.
It cannot attribute the result to device selection alone.

""")

    body.append(section('Circuits and settings'))
    body.append("""The selection was fixed in the campaign manifest before these analyses. It is a
purposive selection, not a random sample of the entire QASMBench collection.
No byte-identical copies were found in the checked MQT corpus.
This check does not exclude algorithmic equivalence or similar circuits
in the LLM's original training data.

""")
    body.append(table(['Group','Circuits','Share','Observed qubits'],[
        ['Small',"30","60\\%","2--10"],['Medium',"15","30\\%","11--27"],
        ['Large',"5","10\\%","28, 63, 98, 111, 140"]]))
    body.append(table(['Item','Setting'],[
        ["LLM",'Qwen3.5-4B, Q8\\_0 weights, temperature 0'],
        ['Generation','Seed 20260913; maximum 4096 output tokens'],
        ['Other parameters',"top\\_p 0.95; top\\_k 40; min\\_p 0; cache enabled"],
        ['Context',"60\\,000 tokens requested; 60\\,160 reported by the server"],
        ["RAG",'5 examples; Manhattan distance; 49 features'],
        ["RAG Dataset",'396 distinct train circuits; TOON prompt format'],
        ['Decision','Contract 4.0.0; at most 3 completed responses'],
        ["MQT",'mqt.predictor 2.4.0; supervised selector + RL policies'],
        ["MQT Training set",'384 of 396 planned samples; 12 excluded'],
        ['Training set collection','1853/1878 successful compilations; adaptive 100/300 s limits'],
        ['Test compilation','One per circuit and method; process limit: 100 s'],
        ['Compilation seeds','Qiskit: 0; MQT sampling: 0'],
        ['Environment','Python 3.12.13; WSL2 x86\\_64; 12 logical CPUs detected']
    ],"p{4.2cm}p{11.1cm}"))
    body.append("""\\paragraph{Quality measurement.}
Each non-barrier instruction in the compiled circuit uses the error
recorded in the Target. The metric reproduces MQT Predictor 2.4.0's \\texttt{expected\\_fidelity}

""")

    body.append(section('Success and quality threshold'))
    bars=""
    for category,color,key in [('Score at least 0.8',"llm","threshold_08"),('Score below 0.8',"mqt","below_08"),("Timeout","muted","timeout")]:
        vv=[methods[m]["statuses"].get("timeout",0) if key=="timeout" else methods[m][key] for m in METHODS]
        bars+=plot(list(enumerate(vv,1)),"ybar,fill="+color+",draw="+color)+r"\addlegendentry{"+category+"}\n"
    body.append(fig(axis(bars,'ybar stacked,bar width=34pt,ymin=0,ymax=54,ytick={0,10,20,30,40,50},ylabel={Number of circuits},xtick={1,2},xticklabels={LLM + RAG,MQT Predictor},xmin=.4,xmax=2.6,legend style={at={(.5,-.18)},anchor=north,legend columns=3,font=\\small}',height="6.1cm"),
        'All 50 circuits per system. Timeouts are separate from successful cases below the threshold. The 0.8 threshold follows the reference report; it does not guarantee physical accuracy.'))
    body.append(table(['Group','LLM successes','MQT successes',r"$S\geq0{,}8$ LLM",r"$S\geq0{,}8$ MQT"],[
        [GN[group],f'{x["methods"][a]["statuses"].get("success",0)}/{x["expected"]}',
         f'{x["methods"][b]["statuses"].get("success",0)}/{x["expected"]}',
         f'{x["methods"][a]["threshold_08"]}/{x["expected"]}',
         f'{x["methods"][b]["threshold_08"]}/{x["expected"]}'] for group,x in gg.items()]))
    body.append("""For small circuits, LLM + RAG exceeds the threshold in every case. For medium circuits,
MQT exceeds it in all 14 completed cases, while LLM + RAG exceeds it in 11 of 15.
Neither system reaches 0.8 on completed large circuits.
\\subsection*{MQT Predictor's two timeouts}
The 100-second limit covers the entire compilation process, including startup,
imports and device selection. Recorded duration slightly exceeds
the limit because of shutdown and outcome collection.

""")
    body.append(table(['Circuit',"Qubit","Target MQT",r"$S$ LLM",'LLM total','MQT total'],[
        [short(f["circuit_id"]),f["qubits"],DEV[f["selection_before_timeout"]["device"]],
         num(v(a,f["circuit_id"])["score"],6),num(v(a,f["circuit_id"])["total_seconds"])+" s",num(f["total_seconds"])+" s"] for f in s["failed"]]))
    body.append("""The Targets for both timeouts come from \\texttt{selection.json}, written before
compilation: Q56 means Quantinuum H2-56 and H156 means IBM Heron 156.
Selection had therefore already occurred. No MQT score is available for comparison.
LLM + RAG completes \\texttt{qft\\_n63}, but with a very low score: technical success
and result quality remain separate measurements.

""")

    body.append(section('Quality on the 48 shared successes'))
    scatter=plot([(0,0),(1,1)],"gray,dashed,no marks,forget plot")
    for group,mark,color in [("small","*","llm"),("medium","triangle*","mqt"),("large","square*","navy")]:
        scatter+=plot([(p["mqt_score"],p["llm_score"]) for p in paired if p["size_group"]==group],"only marks,mark="+mark+",color="+color+",mark size=2pt")+r"\addlegendentry{"+GN[group]+"}\n"
    ec=""
    for method,key,color in [(a,"llm_score","llm"),(b,"mqt_score","mqt")]:
        ec+=plot(ecdf([p[key] for p in paired]),"const plot,thick,color="+color)+r"\addlegendentry{"+NAMES[method]+"}\n"
    body.append(fig(two(
        axis(scatter,r"xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score MQT},ylabel={Score LLM + RAG},legend style={at={(.5,-.25)},anchor=north,legend columns=3,font=\scriptsize}",r"\linewidth","6.8cm"),
        axis(ec,'xmin=0,xmax=1,ymin=0,ymax=100,xlabel={Score},ylabel={Circuits with score at or below (\\%)},legend style={at={(.5,-.25)},anchor=north,legend columns=1,font=\\scriptsize}',r"\linewidth","6.8cm")),
        'On the left, each point is a circuit: LLM + RAG wins above the diagonal. On the right, the cumulative distribution covers the same 48 circuits: at a given score, a lower proportion means fewer low-quality circuits.'))
    body.append(table(['Population','System',"N",'Mean','Median','Minimum'],[
        ['Shared successes',NAMES[m],48,num(pp[k]["mean"],4),num(pp[k]["median"],4),num(pp[k]["min"],6)]
        for m,k in [(a,"llm_score"),(b,"mqt_score")]]+[
        ['All successes',NAMES[m],stat(m,"score","n"),num(stat(m,"score"),4),num(stat(m,"score","median"),4),num(stat(m,"score","min"),6)] for m in METHODS]))
    body.append("""The first pair of rows is the main comparison: both scores exist
for the same circuits. Means over all successes have different denominators
and serve only to describe each system.

""")

    body.append(section('Where scores differ most'))
    delta=""
    for group,color in [("small","llm"),("medium","mqt"),("large","navy")]:
        delta+=plot([(p["index"],p["delta"]) for p in paired if p["size_group"]==group],"ybar,bar width=3pt,fill="+color+",draw="+color)+r"\addlegendentry{"+GN[group]+"}\n"
    delta+=plot([(0,0),(51,0)],"black,thin,no marks,forget plot")
    body.append(fig(axis(delta,'xmin=0,xmax=51,ymin=-.28,ymax=.1,xtick={1,10,20,30,40,50},xlabel={Circuit index in the manifest},ylabel={Score difference},legend style={at={(.5,-.22)},anchor=north,legend columns=3}',height="6.4cm"),
        'Per-circuit differences. Positive values favor LLM + RAG. Indices '+
        " e ".join(str(i) for i,r in enumerate(rows,1) if v(b,r["circuit_id"])["status"]=="timeout")+
        ' have no bar: they are MQT timeouts. The appendix maps indices to names.'))
    extremes=sorted(paired,key=lambda p:p["delta"])
    body.append(table(['Circuit',"LLM","MQT",r"$\Delta$","Target L/M"],[
        [short(p["circuit_id"]),num(p["llm_score"],4),num(p["mqt_score"],4),num(p["delta"],4,True),
         DEV[v(a,p["circuit_id"])["device"]]+"/"+DEV[v(b,p["circuit_id"])["device"]]]
         for p in extremes[:4]+list(reversed(extremes[-4:]))]))
    body.append("""The table shows the four largest differences in each direction,
without selecting cases to fit a narrative. Device names are
abbreviated: F127 = IBM Falcon 127, H133/H156 = IBM Heron 133/156,
Q56 = Quantinuum H2-56.

""")
    biggest=extremes[0];best=extremes[-1]
    body.append(f"\nThe largest MQT advantage occurs on \\texttt{{{short(biggest['circuit_id'])}}}: "+
    f"the difference is {num(-biggest['delta'], 4)}. The largest LLM + RAG advantage occurs on "+
    f"\\texttt{{{short(best['circuit_id'])}}}: {num(best['delta'],4)}.\n")
    body.append("""Choosing the same device does not make the systems equivalent.
LLM + RAG also chooses a Qiskit configuration from the catalog; MQT uses an
RL policy to construct the pass sequence. Device and compilation differences
act together. These data do not isolate a single cause of the observed advantage.

""")


    body.append(section('Cost of LLM decisions and repairs'))
    body.append(table(['Measurement','Total','Mean per circuit','Median'],[
        [label,num(stat(a,key,"sum"),d),num(stat(a,key),d),num(stat(a,key,"median"),d)]
        for key,label,d in [("input_tokens",'Input tokens',0),("output_tokens",'Output tokens',0),
                           ("total_tokens",'Total tokens',0),("llm_calls",'LLM calls',2),
                           ("retries",'Additional calls',2),("rag_seconds",'RAG time (s)',2),
                           ("llm_response_seconds",'LLM response time (s)',2)]]))
    hist=s["llm"]["calls_histogram"]
    hplot=plot([(i,int(hist.get(str(i),0))) for i in (1,2,3)],"ybar,fill=llm,draw=llm,nodes near coords")
    avcalls=[]
    for i in (1,2,3):
        z=[v(a,r["circuit_id"]) for r in rows if v(a,r["circuit_id"])["llm_calls"]==i]
        avcalls.append((i,statistics.mean(x["total_tokens"] for x in z)/1000))
    cplot=plot(avcalls,"ybar,fill=mqt,draw=mqt,nodes near coords,point meta=y")
    body.append(fig(two(
        axis(hplot,'ymin=0,ymax=40,xmin=.5,xmax=3.5,xtick={1,2,3},xlabel={Calls per circuit},ylabel={Number of circuits},bar width=24pt',r"\linewidth","5.6cm"),
        axis(cplot,'ymin=0,ymax=40,xmin=.5,xmax=3.5,xtick={1,2,3},xlabel={Calls per circuit},ylabel={Mean tokens (thousands)},bar width=24pt',r"\linewidth","5.6cm")),
        'Repairs increase requests and token volume. The right-hand columns are means over 35, 2 and 13 circuits, respectively. They do not measure the causal effect of repairs on quality.'))

    body.append(section('System choices and comparison limitations'))
    counts={m:Counter(v(m,r["circuit_id"]).get("device") for r in rows if v(m,r["circuit_id"])["status"]=="success") for m in METHODS}
    selections=Counter(x["selection_before_timeout"]["device"] for x in s["failed"])
    body.append(table(['Device','LLM (50 successes)','MQT (48 successes)',"MQT timeout"],[
        [label,counts[a][device],counts[b][device],selections[device]]
        for device,label in [("ibm_falcon_27","IBM Falcon 27"),("ibm_falcon_127","IBM Falcon 127"),
                             ("ibm_heron_133","IBM Heron 133"),("ibm_heron_156","IBM Heron 156"),("quantinuum_h2_56","Quantinuum H2-56")]]))
    body.append("""LLM + RAG chooses \\texttt{o2\\_default\\_default} 24 times,
\\texttt{o3\\_default\\_default} 24 times and \\texttt{o2\\_dense\\_sabre} twice.
MQT does not select one of these configurations: it executes RL policy steps.
Its selector retains four device classes (Falcon 127, Heron 133,
Heron 156 and H2-56). Falcon 27 is available in the catalog but is not a class
learned by this selector. Frequencies also reflect device capacity and
compatibility with circuits.

\\paragraph{Scope of the conclusion.}
MQT achieves higher mean quality on the 48 comparable circuits; LLM + RAG
offers complete coverage within the configured limit. Faster Qiskit compilation
does not make the entire LLM system faster.
These are three separate results: quality, success and time.

\\paragraph{Model constraints.}
The comparison concerns the artifacts actually used. The MQT selector's Training set
contains 384 samples, not all 396 planned samples. Its source collection
has 1853 successful compilations out of 1878 and used adaptive 100/300-second limits.
These training limits differ from the Test's 100 seconds. The document
does not extend results to a selector retrained on different data.


""")


    for start,end in [(0,25),(25,50)]:
        body.append(section('Appendix: per-circuit results' if start==0 else 'Appendix: per-circuit results (continued)'))
        body.append("""A = LLM + RAG; B = MQT Predictor. $S$ is the score; $t$ is total time
in seconds, including selection. P/M/G denote small/medium/large.
TO indicates a timeout: shutdown time is observed, while the score is missing.
The \\texttt{qasmbench\\_} prefix is omitted from names.

""")
        rr=[]
        for i,r in enumerate(rows[start:end],start+1):
            aa,bb=(v(m,r["circuit_id"]) for m in METHODS)
            rr.append([i,short(r["circuit_id"]),r["qubits"],{"small":"P","medium":"M","large":"G"}[r["size_group"]],
                num(aa["score"],5),num(bb["score"],5) if bb["status"]=="success" else "TO",
                num(aa["total_seconds"],1),num(bb["total_seconds"],1),
                aa["llm_calls"],"*" if aa["accepted_with_unverified_facts"] else ""])
        body.append(r"\begingroup\footnotesize\renewcommand{\arraystretch}{1.45}"+"\n")
        body.append(table(["N.",'Circuit',"Qubit","F.",r"$S_A$",r"$S_B$",r"$t_A$",r"$t_B$","Ch.",""],rr,"rlrrrrrrrr",small=False))
        body.append(r"\endgroup"+"\n")
        body.append("""Ch. indicates the number of LLM calls. An asterisk marks a decision
accepted with facts not fully verified. Scores are displayed
to five decimal places: comparisons, thresholds and differences use the ten decimal places
preserved in the records, before this formatting.

The \\path{dati/circuiti.csv} and \\path{dati/coppie.csv} files also report
internal and process times, devices, configurations, tokens, repairs,
log-scores, statuses and circuit fingerprints. Missing data remain empty,
without replacement by zeros.

""")
    preamble="""\\documentclass[11pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{lmodern}
\\usepackage[english]{babel}
\\usepackage[a4paper,margin=1.9cm,top=2.1cm,bottom=2cm,headheight=14pt]{geometry}
\\usepackage{amsmath,booktabs,array,graphicx,float,caption}
\\usepackage[expansion=false]{microtype}
\\usepackage{pgfplots}
\\pgfplotsset{compat=1.18}
\\usepackage{xcolor,fancyhdr,xurl}
\\usepackage[hidelinks]{hyperref}
\\definecolor{navy}{HTML}{193B53}
\\definecolor{llm}{HTML}{087F8C}
\\definecolor{mqt}{HTML}{CC6B22}
\\definecolor{muted}{HTML}{64748B}
\\definecolor{lightgrid}{HTML}{E2E8F0}
\\pgfplotsset{every axis/.append style={font=\\footnotesize,axis line style={muted},
tick style={muted},grid=major,grid style={lightgrid},legend style={draw=none},
scaled ticks=false,/pgf/number format/use comma,/pgf/number format/1000 sep={\\,}}}
\\captionsetup{font=small,labelfont=bf}
\\pagestyle{fancy}\\fancyhf{}
\\fancyhead[L]{\\small\\color{muted}Additional independent test · QASMBench}
\\fancyhead[R]{\\small\\color{muted}30 September 2026}
\\fancyfoot[C]{\\small\\thepage\\ / \\pageref{ultima}}
\\renewcommand{\\headrulewidth}{.3pt}
\\setlength{\\parindent}{0pt}
\\setlength{\\parskip}{5pt}
\\setlength{\\emergencystretch}{3em}
\\renewcommand{\\arraystretch}{1.2}
\\setcounter{secnumdepth}{1}
\\widowpenalty=10000\\clubpenalty=10000
\\hypersetup{pdftitle={LLM + RAG and MQT Predictor: additional independent QASMBench test},
pdfauthor={MQT thesis project},pdfsubject={Analysis of records from 30 September 2026}}
\\begin{document}

"""
    return preamble+"\n".join(body)+"\n"+r"\label{ultima}\end{document}"+"\n"

def main():
    rows,res,s=analyze()
    out=HERE/"confronto_qasmbench.tex"
    out.write_text(render(rows,res,s),encoding="utf-8")
    provenance={"note":'Generator and source fingerprints; compila.py adds the PDF.',
        "sha256":{p.name:sha(p) for p in (Path(__file__),HERE/"dati.py",out)},
        "inputs":len(s["provenance"]["source_sha256"])}
    (HERE/"artefatti.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"tex":str(out),"circuits":len(rows),"paired":len(s["paired"]),"source_files":provenance["inputs"]}))
if __name__=="__main__":main()

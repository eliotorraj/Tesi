"""Genera LaTeX autonomo e dati del confronto. Non esegue esperimenti."""
from __future__ import annotations
import json, statistics
from collections import Counter
from pathlib import Path
from dati import HERE, METHODS, analyze, sha

NAMES={"llm_rag":"LLM + RAG","mqt_predictor":"MQT Predictor"}
GN={"all":"Totale","small":"Piccoli","medium":"Medi","large":"Grandi"}
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
    """Restituisce il LaTeX con il testo approvato per il confronto QASMBench."""
    gg=s["groups"]; g=gg["all"]; paired=s["paired"]; pp=g["paired"]; methods=g["methods"]
    def stat(m,k,key="mean"):return methods[m]["metrics"][k][key]
    def v(m,c):return res[m,c]
    a,b=METHODS
    body=[]
    body.append(r"""
\begin{center}
{\small\color{muted} VALUTAZIONE DEI SISTEMI DI COMPILAZIONE QUANTISTICA}\\[8pt]
{\LARGE\bfseries\color{navy} LLM + RAG e MQT Predictor}\\[5pt]
{\Large Confronto su QASMBench}\\[9pt]
{\large Ulteriore test indipendente}\\[7pt]
{\small Esecuzioni del 30 settembre 2026 · 50 circuiti · 2 sistemi}
\end{center}
\vspace{8pt}
\section{Risultati principali}
Il test usa circuiti provenienti da QASMBench, diversi dal corpus MQT Bench del progetto.
Sono stati selezionati 30 circuiti piccoli, 15 medi e 5 grandi. Questo documento analizza
i registri conservati; non avvia nuove compilazioni e non modifica le configurazioni valutate.
""")
    body.append(table(["Indicatore","LLM + RAG","MQT Predictor"],[
        ["Compilazioni riuscite / circuiti previsti","50/50 (100\\%)","48/50 (96\\%)"],
        ["Score almeno 0,8 / circuiti previsti","41/50 (82\\%)","43/50 (86\\%)"],
        ["Score medio: stessi 48 circuiti",num(pp["llm_score"]["mean"],4),num(pp["mqt_score"]["mean"],4)],
        ["Tempo totale medio: stessi 48 circuiti",num(pp["llm_total"]["mean"])+" s",num(pp["mqt_total"]["mean"])+" s"],
        ["Compilazione interna media: stessi 48",num(pp["llm_compile"]["mean"])+" s",num(pp["mqt_compile"]["mean"])+" s"]]))
    body.append(r"""\paragraph{Copertura.}
LLM + RAG completa tutti i circuiti. MQT Predictor termina entro il limite su 48 circuiti.
I due timeout, su \texttt{gcm\_n13} e \texttt{qft\_n63}, sono riportati separatamente:
non ricevono uno score pari a zero.
\paragraph{Qualità.}
"""+f"Nei 48 successi comuni, MQT Predictor ottiene uno score medio maggiore di {num(-pp['mean_difference_llm_minus_mqt'],4)}. "+
f"LLM + RAG ottiene lo score maggiore in {pp['llm_wins']} casi e MQT in {pp['mqt_wins']}; non ci sono parità. "+
r"""Le differenze più ampie a favore di MQT si concentrano in alcuni circuiti medi.
\paragraph{Tempi.}
La compilazione interna scelta dall'LLM è più rapida in tutti i 48 successi comuni.
Il tempo necessario a preparare e ottenere la decisione LLM cambia però il risultato
complessivo: MQT è più rapido in 45 di questi 48 casi.
\paragraph{Lettura del confronto.}
Lo score è una fedeltà \emph{stimata} sui Target sintetici, non una misura su hardware quantistico.
Il test confronta i due sistemi completi, con strategie di compilazione diverse.
Non permette di attribuire il risultato al solo selettore del dispositivo.
""")

    body.append(section("Circuiti e impostazioni"))
    body.append(r"""La selezione è fissata nel manifest della campagna, prima di queste analisi. È una
selezione ragionata, non un campione casuale dell'intera raccolta QASMBench.
Non sono state trovate copie identiche byte per byte nel corpus MQT controllato.
Questo controllo non esclude equivalenze algoritmiche o la presenza di circuiti simili
nell'addestramento originario dell'LLM.
""")
    body.append(table(["Fascia","Circuiti","Quota","Qubit osservati"],[
        ["Piccoli","30","60\\%","2--10"],["Medi","15","30\\%","11--27"],
        ["Grandi","5","10\\%","28, 63, 98, 111, 140"]]))
    body.append(table(["Voce","Impostazione"],[
        ["LLM","Qwen3.5-4B, pesi Q8\\_0, temperatura 0"],
        ["Generazione","Seed 20260913; massimo 4096 token in uscita"],
        ["Altri parametri","top\\_p 0,95; top\\_k 40; min\\_p 0; cache attiva"],
        ["Contesto","60\\,000 token richiesti; 60\\,160 dichiarati dal server"],
        ["RAG","5 esempi; distanza Manhattan; 49 caratteristiche"],
        ["Dataset RAG","396 circuiti train distinti; formato del prompt TOON"],
        ["Decisione","Contratto 4.0.0; al massimo 3 risposte completate"],
        ["MQT","mqt.predictor 2.4.0; selettore supervisionato + politiche RL"],
        ["Training set MQT","384 dei 396 campioni previsti; 12 esclusi"],
        ["Raccolta del Training set","1853/1878 compilazioni riuscite; limiti adattivi 100/300 s"],
        ["Compilazione del Test","Una per circuito e metodo; limite del processo: 100 s"],
        ["Semi della compilazione","Qiskit: 0; campionamento MQT: 0"],
        ["Ambiente","Python 3.12.13; WSL2 x86\\_64; 12 CPU logiche rilevate"]
    ],"p{4.2cm}p{11.1cm}"))
    body.append(r"""\paragraph{Misura della qualità.}
Per ciascuna istruzione non di barriera del circuito compilato si usa l'errore
registrato nel Target. La metrica riproduce \texttt{expected\_fidelity} di MQT Predictor 2.4.0
""")

    body.append(section("Riuscita e soglia di qualità"))
    bars=""
    for category,color,key in [("Score almeno 0,8","llm","threshold_08"),("Score sotto 0,8","mqt","below_08"),("Timeout","muted","timeout")]:
        vv=[methods[m]["statuses"].get("timeout",0) if key=="timeout" else methods[m][key] for m in METHODS]
        bars+=plot(list(enumerate(vv,1)),"ybar,fill="+color+",draw="+color)+r"\addlegendentry{"+category+"}\n"
    body.append(fig(axis(bars,r"ybar stacked,bar width=34pt,ymin=0,ymax=54,ytick={0,10,20,30,40,50},ylabel={Numero di circuiti},xtick={1,2},xticklabels={LLM + RAG,MQT Predictor},xmin=.4,xmax=2.6,legend style={at={(.5,-.18)},anchor=north,legend columns=3,font=\small}",height="6.1cm"),
        "Tutti i 50 circuiti per sistema. I timeout sono distinti dai successi sotto soglia. La soglia 0,8 riprende il report di riferimento; non è una garanzia di accuratezza fisica."))
    body.append(table(["Fascia","Successi LLM","Successi MQT",r"$S\geq0{,}8$ LLM",r"$S\geq0{,}8$ MQT"],[
        [GN[group],f'{x["methods"][a]["statuses"].get("success",0)}/{x["expected"]}',
         f'{x["methods"][b]["statuses"].get("success",0)}/{x["expected"]}',
         f'{x["methods"][a]["threshold_08"]}/{x["expected"]}',
         f'{x["methods"][b]["threshold_08"]}/{x["expected"]}'] for group,x in gg.items()]))
    body.append(r"""Nei piccoli circuiti LLM + RAG supera la soglia in tutti i casi. Nei medi,
MQT la supera in tutti i 14 casi completati, mentre LLM + RAG la supera in 11 casi su 15.
Nessuno dei due sistemi raggiunge 0,8 sui grandi circuiti completati.
\subsection*{I due timeout di MQT Predictor}
Il limite di 100 secondi riguarda l'intero processo di compilazione: include avvio,
importazioni e selezione del dispositivo. La durata registrata supera leggermente
il limite per l'arresto e la raccolta dell'esito.
""")
    body.append(table(["Circuito","Qubit","Target MQT",r"$S$ LLM","Totale LLM","Totale MQT"],[
        [short(f["circuit_id"]),f["qubits"],DEV[f["selection_before_timeout"]["device"]],
         num(v(a,f["circuit_id"])["score"],6),num(v(a,f["circuit_id"])["total_seconds"])+" s",num(f["total_seconds"])+" s"] for f in s["failed"]]))
    body.append(r"""I Target dei due timeout sono ricavati da \texttt{selection.json}, scritto prima della
compilazione: Q56 indica Quantinuum H2-56 e H156 IBM Heron 156.
La scelta era quindi già avvenuta. Non è disponibile uno score MQT da confrontare.
LLM + RAG completa \texttt{qft\_n63}, ma con uno score molto basso: riuscita tecnica
e qualità del risultato restano due misure distinte.
""")

    body.append(section("Qualità sui 48 successi comuni"))
    scatter=plot([(0,0),(1,1)],"gray,dashed,no marks,forget plot")
    for group,mark,color in [("small","*","llm"),("medium","triangle*","mqt"),("large","square*","navy")]:
        scatter+=plot([(p["mqt_score"],p["llm_score"]) for p in paired if p["size_group"]==group],"only marks,mark="+mark+",color="+color+",mark size=2pt")+r"\addlegendentry{"+GN[group]+"}\n"
    ec=""
    for method,key,color in [(a,"llm_score","llm"),(b,"mqt_score","mqt")]:
        ec+=plot(ecdf([p[key] for p in paired]),"const plot,thick,color="+color)+r"\addlegendentry{"+NAMES[method]+"}\n"
    body.append(fig(two(
        axis(scatter,r"xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score MQT},ylabel={Score LLM + RAG},legend style={at={(.5,-.25)},anchor=north,legend columns=3,font=\scriptsize}",r"\linewidth","6.8cm"),
        axis(ec,r"xmin=0,xmax=1,ymin=0,ymax=100,xlabel={Score},ylabel={Circuiti con score non superiore (\%)},legend style={at={(.5,-.25)},anchor=north,legend columns=1,font=\scriptsize}",r"\linewidth","6.8cm")),
        "A sinistra ogni punto è un circuito: sopra la diagonale prevale LLM + RAG. A destra la distribuzione cumulativa sui medesimi 48 circuiti: a parità di score, una quota più bassa indica meno circuiti con qualità bassa."))
    body.append(table(["Popolazione","Sistema","N","Media","Mediana","Minimo"],[
        ["Successi comuni",NAMES[m],48,num(pp[k]["mean"],4),num(pp[k]["median"],4),num(pp[k]["min"],6)]
        for m,k in [(a,"llm_score"),(b,"mqt_score")]]+[
        ["Tutti i successi",NAMES[m],stat(m,"score","n"),num(stat(m,"score"),4),num(stat(m,"score","median"),4),num(stat(m,"score","min"),6)] for m in METHODS]))
    body.append(r"""La prima coppia di righe è il confronto principale: entrambi gli score esistono
per gli stessi circuiti. Le medie su tutti i successi hanno denominatori diversi
e servono soltanto a descrivere ciascun sistema.
""")

    body.append(section("Dove cambiano maggiormente gli score"))
    delta=""
    for group,color in [("small","llm"),("medium","mqt"),("large","navy")]:
        delta+=plot([(p["index"],p["delta"]) for p in paired if p["size_group"]==group],"ybar,bar width=3pt,fill="+color+",draw="+color)+r"\addlegendentry{"+GN[group]+"}\n"
    delta+=plot([(0,0),(51,0)],"black,thin,no marks,forget plot")
    body.append(fig(axis(delta,r"xmin=0,xmax=51,ymin=-.28,ymax=.1,xtick={1,10,20,30,40,50},xlabel={Indice del circuito nel manifest},ylabel={Differenza di score},legend style={at={(.5,-.22)},anchor=north,legend columns=3}",height="6.4cm"),
        "Differenze sui singoli circuiti. Valori positivi favoriscono LLM + RAG. Gli indici "+
        " e ".join(str(i) for i,r in enumerate(rows,1) if v(b,r["circuit_id"])["status"]=="timeout")+
        " non hanno una barra: sono i timeout MQT. L'appendice associa gli indici ai nomi."))
    extremes=sorted(paired,key=lambda p:p["delta"])
    body.append(table(["Circuito","LLM","MQT",r"$\Delta$","Target L/M"],[
        [short(p["circuit_id"]),num(p["llm_score"],4),num(p["mqt_score"],4),num(p["delta"],4,True),
         DEV[v(a,p["circuit_id"])["device"]]+"/"+DEV[v(b,p["circuit_id"])["device"]]]
         for p in extremes[:4]+list(reversed(extremes[-4:]))]))
    body.append(r"""La tabella mostra i quattro maggiori scarti in ciascuna direzione,
senza selezionare i casi in base alla narrativa. I nomi dei dispositivi sono
abbreviati: F127 = IBM Falcon 127, H133/H156 = IBM Heron 133/156,
Q56 = Quantinuum H2-56.
""")
    biggest=extremes[0];best=extremes[-1]
    body.append(f"\nIl maggiore vantaggio MQT compare su \\texttt{{{short(biggest['circuit_id'])}}}: "+
f"lo scarto è {num(-biggest['delta'],4)}. Il maggiore vantaggio LLM + RAG compare su "+
f"\\texttt{{{short(best['circuit_id'])}}}: {num(best['delta'],4)}.\n")
    body.append(r"""La sola scelta dello stesso dispositivo non rende uguali i sistemi.
LLM + RAG sceglie anche una configurazione Qiskit dal catalogo; MQT usa una politica
RL per costruire la sequenza dei passi. Differenze di dispositivo e di compilazione
agiscono insieme. Questi dati non isolano una causa unica del vantaggio osservato.
""")


    body.append(section("Costo delle decisioni LLM e correzioni"))
    body.append(table(["Misura","Totale","Media per circuito","Mediana"],[
        [label,num(stat(a,key,"sum"),d),num(stat(a,key),d),num(stat(a,key,"median"),d)]
        for key,label,d in [("input_tokens","Token in ingresso",0),("output_tokens","Token in uscita",0),
                           ("total_tokens","Token complessivi",0),("llm_calls","Chiamate LLM",2),
                           ("retries","Chiamate aggiuntive",2),("rag_seconds","Tempo RAG (s)",2),
                           ("llm_response_seconds","Tempo risposte LLM (s)",2)]]))
    hist=s["llm"]["calls_histogram"]
    hplot=plot([(i,int(hist.get(str(i),0))) for i in (1,2,3)],"ybar,fill=llm,draw=llm,nodes near coords")
    avcalls=[]
    for i in (1,2,3):
        z=[v(a,r["circuit_id"]) for r in rows if v(a,r["circuit_id"])["llm_calls"]==i]
        avcalls.append((i,statistics.mean(x["total_tokens"] for x in z)/1000))
    cplot=plot(avcalls,"ybar,fill=mqt,draw=mqt,nodes near coords,point meta=y")
    body.append(fig(two(
        axis(hplot,r"ymin=0,ymax=40,xmin=.5,xmax=3.5,xtick={1,2,3},xlabel={Chiamate per circuito},ylabel={Numero di circuiti},bar width=24pt",r"\linewidth","5.6cm"),
        axis(cplot,r"ymin=0,ymax=40,xmin=.5,xmax=3.5,xtick={1,2,3},xlabel={Chiamate per circuito},ylabel={Token medi (migliaia)},bar width=24pt",r"\linewidth","5.6cm")),
        "Le correzioni aumentano il numero di richieste e il volume di token. Le colonne di destra sono medie su 35, 2 e 13 circuiti, rispettivamente. Non misurano l'effetto causale delle correzioni sulla qualità."))

    body.append(section("Scelte dei sistemi e limiti del confronto"))
    counts={m:Counter(v(m,r["circuit_id"]).get("device") for r in rows if v(m,r["circuit_id"])["status"]=="success") for m in METHODS}
    selections=Counter(x["selection_before_timeout"]["device"] for x in s["failed"])
    body.append(table(["Dispositivo","LLM (50 successi)","MQT (48 successi)","MQT timeout"],[
        [label,counts[a][device],counts[b][device],selections[device]]
        for device,label in [("ibm_falcon_27","IBM Falcon 27"),("ibm_falcon_127","IBM Falcon 127"),
                             ("ibm_heron_133","IBM Heron 133"),("ibm_heron_156","IBM Heron 156"),("quantinuum_h2_56","Quantinuum H2-56")]]))
    body.append(r"""LLM + RAG sceglie 24 volte \texttt{o2\_default\_default}, 24 volte
\texttt{o3\_default\_default} e 2 volte \texttt{o2\_dense\_sabre}.
MQT non sceglie una di queste configurazioni: esegue i passi della politica RL.
Il suo selettore conserva quattro classi di dispositivo (Falcon 127, Heron 133,
Heron 156 e H2-56). Falcon 27 è disponibile nel catalogo, ma non è una classe
appresa da questo selettore. Le frequenze riflettono anche capacità e compatibilità
dei dispositivi con i circuiti.

\paragraph{Ambito della conclusione.}
MQT ottiene una qualità media maggiore sui 48 circuiti confrontabili; LLM + RAG
offre copertura completa entro il limite impostato. La rapidità della compilazione
Qiskit non basta a rendere più rapido l'intero sistema LLM.
Sono tre risultati distinti: qualità, riuscita e tempo.

\paragraph{Vincoli dei modelli.}
Il confronto riguarda gli artefatti realmente usati. Il Training set del selettore
MQT comprende 384 campioni, non tutti i 396 previsti. La raccolta che lo ha prodotto
ha 1853 compilazioni riuscite su 1878 e ha usato limiti adattivi di 100/300 secondi.
Questi limiti di addestramento sono diversi dai 100 secondi del Test. Il documento
non estende i risultati a un selettore ritrainato su dati diversi.

""")


    for start,end in [(0,25),(25,50)]:
        body.append(section("Appendice: risultati per circuito" if start==0 else "Appendice: risultati per circuito (continua)"))
        body.append(r"""A = LLM + RAG; B = MQT Predictor. $S$ è lo score; $t$ il tempo totale
in secondi, comprensivo della scelta. P/M/G indicano piccolo/medio/grande.
TO indica un timeout: il tempo dell'arresto è osservato, lo score è assente.
Il prefisso \texttt{qasmbench\_} è omesso dai nomi.
""")
        rr=[]
        for i,r in enumerate(rows[start:end],start+1):
            aa,bb=(v(m,r["circuit_id"]) for m in METHODS)
            rr.append([i,short(r["circuit_id"]),r["qubits"],{"small":"P","medium":"M","large":"G"}[r["size_group"]],
                num(aa["score"],5),num(bb["score"],5) if bb["status"]=="success" else "TO",
                num(aa["total_seconds"],1),num(bb["total_seconds"],1),
                aa["llm_calls"],"*" if aa["accepted_with_unverified_facts"] else ""])
        body.append(r"\begingroup\footnotesize\renewcommand{\arraystretch}{1.45}"+"\n")
        body.append(table(["N.","Circuito","Qubit","F.",r"$S_A$",r"$S_B$",r"$t_A$",r"$t_B$","Ch.",""],rr,"rlrrrrrrrr",small=False))
        body.append(r"\endgroup"+"\n")
        body.append(r"""Ch. indica il numero di chiamate LLM. L'asterisco segnala una decisione
accettata con fatti non completamente verificati. Gli score sono visualizzati
con cinque decimali: confronti, soglie e differenze sono calcolati dai dieci decimali
conservati nei registri, prima di questa formattazione.

I file \path{dati/circuiti.csv} e \path{dati/coppie.csv} riportano anche
tempi interni e di processo, dispositivi, configurazioni, token, correzioni,
log-score, stati e impronte dei circuiti. I dati mancanti restano vuoti,
senza sostituzione con zeri.
""")
    preamble=r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[italian]{babel}
\usepackage[a4paper,margin=1.9cm,top=2.1cm,bottom=2cm,headheight=14pt]{geometry}
\usepackage{amsmath,booktabs,array,graphicx,float,caption}
\usepackage[expansion=false]{microtype}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{xcolor,fancyhdr,xurl}
\usepackage[hidelinks]{hyperref}
\definecolor{navy}{HTML}{193B53}
\definecolor{llm}{HTML}{087F8C}
\definecolor{mqt}{HTML}{CC6B22}
\definecolor{muted}{HTML}{64748B}
\definecolor{lightgrid}{HTML}{E2E8F0}
\pgfplotsset{every axis/.append style={font=\footnotesize,axis line style={muted},
tick style={muted},grid=major,grid style={lightgrid},legend style={draw=none},
scaled ticks=false,/pgf/number format/use comma,/pgf/number format/1000 sep={\,}}}
\captionsetup{font=small,labelfont=bf}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{muted}Ulteriore test indipendente · QASMBench}
\fancyhead[R]{\small\color{muted}30 settembre 2026}
\fancyfoot[C]{\small\thepage\ / \pageref{ultima}}
\renewcommand{\headrulewidth}{.3pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\emergencystretch}{3em}
\renewcommand{\arraystretch}{1.2}
\setcounter{secnumdepth}{1}
\widowpenalty=10000\clubpenalty=10000
\hypersetup{pdftitle={LLM + RAG e MQT Predictor: ulteriore test indipendente QASMBench},
pdfauthor={Progetto Tesi MQT},pdfsubject={Analisi dei registri del 30 settembre 2026}}
\begin{document}
"""
    return preamble+"\n".join(body)+"\n"+r"\label{ultima}\end{document}"+"\n"

def main():
    rows,res,s=analyze()
    out=HERE/"confronto_qasmbench.tex"
    out.write_text(render(rows,res,s),encoding="utf-8")
    provenance={"note":"Impronte dei generatori e del sorgente; il PDF viene aggiunto da compila.py.",
        "sha256":{p.name:sha(p) for p in (Path(__file__),HERE/"dati.py",out)},
        "inputs":len(s["provenance"]["source_sha256"])}
    (HERE/"artefatti.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"tex":str(out),"circuits":len(rows),"paired":len(s["paired"]),"source_files":provenance["inputs"]}))
if __name__=="__main__":main()

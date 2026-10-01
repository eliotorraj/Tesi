"""LaTeX autonomo e grafici vettoriali PGFPlots a partire da dati.json."""
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
    options=(f"width={width},height={height},title={{$k={k}$}},xlabel={{Indice circuito}},ylabel={{{label}}},"
             f"xmin=0,xmax=91,ymin=0,ymax={maximum:.12g},xtick={{1,15,30,45,60,75,90}},"
             "grid=major,scaled y ticks=false,tick label style={font=\\scriptsize},"
             "label style={font=\\small},title style={font=\\bfseries},"+extra)
    pts=[(r["index"],r[metric]) for r in RUNS[k]]
    return r"\begin{tikzpicture}\begin{axis}["+options+"]\n"+r"\addplot[only marks,mark=*,mark size=1.1pt,color="+COLORS[k]+",fill="+COLORS[k]+"] coordinates {"+coords(pts)+r"};\end{axis}\end{tikzpicture}"
def dual_page(title,a,b,la,lb,note):
    text=page(title)+note+r"\par\medskip"+"\n"
    text+=r"\noindent\begin{minipage}{.49\linewidth}\centering\textbf{"+la+r"}\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering\textbf{"+lb+r"}\end{minipage}\par"+"\n"
    for k in KS:
        text+=r"\noindent\begin{minipage}{.49\linewidth}\centering"+axis(a,k,la)+r"\end{minipage}\hfill\begin{minipage}{.49\linewidth}\centering"+axis(b,k,lb)+r"\end{minipage}\par\medskip"+"\n"
    text+=r"{\small Ogni punto è un circuito. Le scale sono comuni fra i tre valori di $k$ per ciascuna colonna. L'indice segue l'ordine alfabetico dell'appendice.}\par"
    return text
PRE=r"""\documentclass[a4paper,10pt]{article}
\usepackage[margin=1.8cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[italian]{babel}
\usepackage{lmodern,booktabs,tabularx,longtable,array,amsmath,xcolor,pgfplots,pdflscape,xurl,hyperref}
\usepackage[expansion=false]{microtype}
\pgfplotsset{compat=1.18}
\definecolor{kuno}{HTML}{167D9A}
\definecolor{kcinque}{HTML}{D47A17}
\definecolor{kdieci}{HTML}{7656A3}
\hypersetup{hidelinks}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\emergencystretch}{3em}
\newcommand{\separatore}{\par\medskip}
\begin{document}
{\small\bfseries ANALISI DEI REGISTRI CONSERVATI | 29 settembre 2026}\par
{\LARGE\bfseries Quanti esempi servono al RAG?}\par
{\Large Confronto fra $k=1$, $k=5$ e $k=10$}\par\medskip
"""
t=PRE
t+=r"""\section{Domanda, impostazioni e risultato principale}
Confrontiamo lo stesso LLM con uno, cinque e dieci esempi train recuperati
per somiglianza. Vogliamo capire quanto il numero di esempi incida sulla
qualità della scelta, sui token e sui tempi. Ogni variante è stata applicata
agli stessi 90 circuiti Test.

\textbf{Nel campione osservato, aumentare gli esempi cambia pochissimo lo score,
ma aumenta token, attesa e richieste di correzione.} La riuscita è 90/90 in tutte
le varianti. I risultati non dimostrano che un solo esempio sia sempre sufficiente.

"""
t+=table(["Misura","$k=1$","$k=5$","$k=10$"],[
["Compilazioni riuscite",*[f'{S[k]["successes"]}/90' for k in KS]],
["Fallimenti",*[str(90-S[k]["successes"]) for k in KS]],
row_metric("Score medio","score",6),row_metric("Score mediano","score",6,"median"),
["Score almeno 0,8",*[f'{S[k]["threshold_08"]}/90' for k in KS]],
row_metric("Tempo totale medio (s)","total_seconds"),
row_metric("Token complessivi, somma","total_tokens",0,"sum"),
row_metric("Correzioni, somma","retries",0,"sum")])
t+=r"""\subsection{Che cosa resta uguale}
Il modello è Qwen3.5-4B, pesi Q8\_0 e temperatura 0. I registri confermano
lo stesso GGUF e gli stessi parametri delle chiamate: seme 20260913,
\texttt{top\_p}=0,95, \texttt{top\_k}=40 e \texttt{min\_p}=0.
Il contesto richiesto è 60.000 token e il limite di risposta è 4.096.
Il pensiero esteso è disattivato. Sono consentiti al massimo tre tentativi.

Il recupero usa gli stessi 396 circuiti train distinti, 49 caratteristiche,
trasformazione calcolata sul train, distanza Manhattan e ricerca esatta.
Filtri e ordinamento delle parità sono invariati. È stato verificato su tutti
i 90 casi che l'esempio di $k=1$ sia il primo di $k=5$ e $k=10$, e che i primi
cinque di $k=10$ coincidano con quelli della prova classica.

La compilazione usa lo stesso catalogo di dodici configurazioni Qiskit,
cinque Target sintetici, seme 0, un solo processo e limite esterno di 100 secondi.
Lo score è \emph{expected fidelity}, fra 0 e 1: maggiore è migliore.
Non misura un'esecuzione su hardware quantistico reale.

\subsection{Che cosa cambia, oltre alla quantità di esempi}
Con dieci esempi il contratto ammette anche E6--E10 e la nota sulle colonne del
prompt viene adeguata. Restano uno o due fatti nella risposta e le stesse regole
di verifica. Il contenuto è inviato in TOON; la risposta è JSON.

La prova $k=5$ è iniziata il 21 settembre 2026; le prove $k=1$ e $k=10$ il
28 settembre, dopo la lettura del Test. Il confronto è quindi descrittivo e
riusa la prova classica, con revisioni di codice e date diverse. Non è una
nuova conferma indipendente né una selezione fatta sulla validation.
"""
t+=page("Tempi, token e correzioni")
t+=r"""I tempi sono in secondi. Le medie e le mediane seguenti hanno tutte
90 misure per variante. Non sono stati imputati valori mancanti.\par"""
rows=[]
for label,key in [("Totale","total_seconds"),("Preparazione e scelta","choice_seconds"),("Recupero e controlli RAG","rag_seconds"),
                  ("Risposte LLM, cumulative","llm_response_seconds"),("Compilazione interna","compilation_seconds"),
                  ("Processo di compilazione","compilation_process_seconds")]:
 rows.append([label,*[fmt(m(k,key))+" / "+fmt(m(k,key,"median")) for k in KS]])
t+=table(["Tempo: media / mediana","$k=1$","$k=5$","$k=10$"],rows)
t+=r"""\textbf{Le componenti non vanno sommate fra loro.} Preparazione e scelta
comprende RAG, costruzione del prompt, tokenizzazione, risposte e controlli.
Il tempo RAG include caricamento e verifica dell'indice, non soltanto la ricerca.
Il processo di compilazione include anche avvio e controlli, mentre la misura
interna riguarda il compilatore. Il totale copre l'intero caso.\par
\subsection{Volume di testo e richieste al modello}
I token complessivi sommano ingresso e uscita di tutte le chiamate, comprese
le correzioni. L'ingresso conta anche i token serviti dalla cache. Non è un
costo monetario né una misura dei soli token ricalcolati dal server.\par"""
t+=table(["Misura","$k=1$","$k=5$","$k=10$"],[
row_metric("Ingresso del primo tentativo, media","first_input_tokens",1),
row_metric("Token in ingresso, somma","input_tokens",0,"sum"),
row_metric("Token in uscita, somma","output_tokens",0,"sum"),
row_metric("Token complessivi, somma","total_tokens",0,"sum"),
row_metric("Token complessivi per circuito, media","total_tokens",1),
row_metric("Chiamate, somma","llm_calls",0,"sum"),
row_metric("Correzioni, somma","retries",0,"sum"),
["Circuiti con almeno una correzione",*[str(S[k]["retry_cases"])+"/90" for k in KS]],
["Risposte con tutti i fatti validi al primo tentativo",*[str(S[k]["valid_first"])+"/90" for k in KS]],
["Risposte finali con tutti i fatti validi",*[str(S[k]["valid_final"])+"/90" for k in KS]],
["Fatti finali validi",*[f'{S[k]["facts_verified"]}/{S[k]["facts_total"]}' for k in KS]]])
t+=r"\subsection{Variazioni rispetto a cinque esempi}"+"\n"
t+=table(["Variante","Token totali","Tempo totale medio","$\\Delta$ score medio"],[
[f"$k={k}$",fmt(100*(m(k,"total_tokens","sum")/m("5","total_tokens","sum")-1))+r"\%",
 fmt(100*(m(k,"total_seconds")/m("5","total_seconds")-1))+r"\%",
 fmt(m(k,"score")-m("5","score"),8)] for k in ["1","10"]])
t+=r"""Il primo ingresso cresce con il numero di esempi. Il costo complessivo
cresce ulteriormente perché aumentano le correzioni. Il confronto dei primi
tentativi separa il volume iniziale del prompt dalla successiva ripetizione
delle chiamate. I tempi osservati includono anche effetti di cache e condizioni
del computer non controllati da repliche."""
t+=page("Differenze sugli stessi circuiti")
t+=r"""Tutte le varianti riescono sugli stessi 90 circuiti: qui i denominatori
coincidono. La differenza è lo score della prima variante meno quello della
seconda. Una parità significa $|\Delta|\leq10^{-12}$ sui valori conservati;
non è un test statistico di equivalenza.\par"""
t+=table(["Confronto","Media $\\Delta$","Meglio","Pari","Peggio","Stessa coppia"],[
[f'$k={p["a"]}$ meno $k={p["b"]}$',fmt(p["delta"]["mean"],8),str(p["wins"]),str(p["ties"]),str(p["losses"]),str(p["same_pair"])+"/90"] for p in D["pairs"]])
t+=r"\textbf{"+str(D["identical_all"])+r" circuiti su 90 hanno esattamente lo stesso score in tutte e tre le prove.} Le mediane delle differenze sono sempre zero.\par"
t+=r"\subsection{Tutti i casi con score diverso fra le tre varianti}"+"\n"
t+=r"I casi sono ordinati per escursione fra score massimo e minimo. Sono mostrati tutti, senza selezionare soltanto i miglioramenti.\par"
t+=table(["Circuito","$k=1$","$k=5$","$k=10$"],[
[r"\nolinkurl{"+c+"}",*[fmt(ROWS[k][c]["score"],8) for k in KS]] for c in D["changed_circuits"]])
t+=r"\subsection{Lettura per numero di qubit}"+"\n"
t+=table(["Qubit","Casi","Media $k=1$","Media $k=5$","Media $k=10$"],[
[esc(g["label"]),str(g["n"]),*[fmt(g["score"][k]["mean"],6) for k in KS]] for g in D["qubit_groups"]])
t+=r"""Le fasce riprendono il confronto di riferimento. Non definiscono da sole
la difficoltà del circuito. Anche sopra 16 qubit non emerge un vantaggio di
dieci esempi su cinque: in quella fascia i loro score coincidono. Questi dati
non sostengono l'idea che aggiungere esempi migliori automaticamente i casi
più grandi. Riguardano però questo recupero e questo modello."""
t+=page("Riuscita, soglia e qualità per circuito")
t+=r"""La riuscita e la soglia hanno come denominatore tutti i 90 circuiti.
I tre valori di $k$ hanno le stesse coperture; i grafici degli score mostrano
quanto siano simili anche i risultati individuali.\par"""
t+=r"""\begin{center}\begin{tikzpicture}
\begin{axis}[width=.86\linewidth,height=4cm,ybar,bar width=14pt,ymin=0,ymax=103,
symbolic x coords={k1,k5,k10},xtick={k1,k5,k10},xticklabels={$k=1$,$k=5$,$k=10$},
ylabel={Circuiti su 90},nodes near coords,legend style={at={(.5,1.03)},anchor=south,legend columns=2,font=\small}]
\addplot[fill=kuno!70,draw=kuno] coordinates {(k1,90)(k5,90)(k10,90)};
\addplot[fill=kcinque!70,draw=kcinque] coordinates {(k1,70)(k5,70)(k10,70)};
\legend{Compilazioni valide,Score almeno 0{,}8}
\end{axis}\end{tikzpicture}\end{center}
"""
for k in KS:
 t+=r"\begin{center}"+axis("score",k,"Score",height="3.75cm",width=".94\\linewidth",extra="ytick={0,.2,.4,.6,.8,1},")+r"\end{center}"+"\n"
t+=r"{\small Stesso ordine alfabetico e stessa scala 0--1. Lo score mediano è 0,921379 per tutte le varianti.}\par"
t+=dual_page("Tempi: intero percorso e compilazione interna","total_seconds","compilation_seconds","Tempo totale (s)","Compilazione interna (s)",
r"Il costo totale aumenta con $k$. Il lavoro interno del compilatore resta mediamente vicino a 1,7 secondi: le scelte cambiano soltanto in pochi casi. I picchi del totale possono dipendere dalle correzioni o dalla compilazione e vanno letti insieme agli altri registri.")
t+=dual_page("Tempi: processo di compilazione e risposte LLM","compilation_process_seconds","llm_response_seconds","Processo compilazione (s)","Risposte LLM (s)",
r"La colonna sinistra comprende avvio, compilazione e controlli. A destra si sommano tutte le attese delle risposte LLM dello stesso circuito. L'aumento più evidente riguarda questa seconda componente.")
t+=dual_page("Token e richieste di correzione","total_tokens","retries","Token totali","Correzioni",
r"Ogni correzione richiede un'altra risposta completa. I token includono ingresso e uscita di tutte le chiamate. I livelli 0, 1 e 2 indicano rispettivamente una, due o tre risposte. Le scale comuni rendono visibile l'aumento di costo con dieci esempi.")
t+=dual_page("Preparazione, recupero e scelta","rag_seconds","choice_seconds","RAG e controlli (s)","Preparazione e scelta (s)",
r"Il recupero è misurato insieme ai controlli della fonte e dell'indice. La sua media è vicina a 3,6--3,9 secondi nelle tre campagne. La scelta comprende anche tokenizzazione e chiamate LLM: la crescita del costo non coincide con una ricerca dei vicini dieci volte più lenta.")
t+=page("Distribuzioni e differenze rispetto a cinque esempi")
t+=r"""La distribuzione cumulativa indica la quota di circuiti con score non
superiore al valore in ascissa. Le curve si sovrappongono quasi interamente.
I pannelli inferiori ingrandiscono le differenze rispetto a $k=5$:
qui zero significa lo stesso score, non un dato mancante.\par"""
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=6cm,xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score},ylabel={Quota cumulativa},grid=major,legend pos=north west]"+"\n"
for k,style in zip(KS,["solid","dashed","dotted"]):
 values=sorted(r["score"] for r in RUNS[k])
 t+=r"\addplot[const plot,thick,"+COLORS[k]+","+style+"] coordinates {"+coords([(0,0),*[(v,(i+1)/90) for i,v in enumerate(values)],(1,1)])+r"};\addlegendentry{$k="+k+"$}\n"
t+=r"\end{axis}\end{tikzpicture}\end{center}"
for k in ["1","10"]:
 t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=4.15cm,title={$k="+k+r"$ meno $k=5$},xlabel={Indice circuito},ylabel={Differenza di score},xmin=0,xmax=91,ymin=-.023,ymax=.002,xtick={1,15,30,45,60,75,90},grid=major]"
 t+=r"\addplot[gray,dashed,domain=0:91]{0};"
 t+=r"\addplot[only marks,mark=*,mark size=1.6pt,"+COLORS[k]+"] coordinates {"+coords([(i+1,ROWS[k][c]["score"]-ROWS["5"][c]["score"]) for i,c in enumerate(IDS)])+r"};\end{axis}\end{tikzpicture}\end{center}"
t+=page("Perché aumentano i costi e che cosa dicono i fatti")
t+=r"""\subsection{Ingresso iniziale e costo complessivo}
A sinistra, il numero medio di token in ingresso al primo tentativo.
A destra, il totale medio per circuito, che comprende uscita e correzioni.
Le scale sono diverse perché descrivono misure diverse.\par"""
for title,key in [("Ingresso iniziale medio","first_input_tokens"),("Totale medio per circuito","total_tokens")]:
 t+=r"\begin{minipage}{.49\linewidth}\centering\begin{tikzpicture}\begin{axis}[width=.95\linewidth,height=5cm,ybar,bar width=22pt,bar shift=0pt,enlarge x limits=.3,ymin=0,ymax="+str(m("10",key)*1.22)+r",symbolic x coords={k1,k5,k10},xtick={k1,k5,k10},xticklabels={$k=1$,$k=5$,$k=10$},title={"+title+r"},ylabel={Token},scaled y ticks=false,tick label style={font=\small}]"
 for k in KS:t+=r"\addplot[fill="+COLORS[k]+"!75,draw="+COLORS[k]+"] coordinates {(k"+k+","+str(m(k,key))+")};"
 t+=r"\end{axis}\end{tikzpicture}\end{minipage}\hfill"
t+=r"\par\subsection{Contenuto e validità dei fatti finali}"+"\n"
types=[("Stesso dispositivo dell'esempio","selected_device_matches_example"),("Coppia fra i risultati mostrati","selected_pair_among_reported_best"),("Stesso numero di qubit","same_qubit_count_as_example"),("Capacità del dispositivo","selected_device_has_enough_qubits")]
fr=[]
for label,kind in types:
 vals=[]
 for k in KS:
  items=[x for x in S[k]["fact_kinds"] if x["assertion"]==kind]
  vals.append(str(sum(x["n"] for x in items if x["result"]=="verified"))+"/"+str(sum(x["n"] for x in items)))
 fr.append([label,*vals])
t+=table(["Tipo: validi / dichiarati","$k=1$","$k=5$","$k=10$"],fr)
t+=r"""La coppia dispositivo/configurazione viene citata più spesso con dieci
esempi: 35 fatti finali, contro 5 con cinque esempi e nessuno con uno.
Questi fatti storici risultano tutti sostenuti dai record indicati.
La maggiore ricchezza dei riferimenti non si traduce qui in un aumento
apprezzabile dello score sul circuito corrente.

I fatti non validi sono 2, 17 e 38. Riguardano sempre la capacità del dispositivo
con un riferimento a un esempio, mentre la regola richiede il catalogo hardware
senza \texttt{example\_id}. La capacità è comunque sufficiente.
Non sono quindi 2, 17 e 38 scelte hardware impossibili.

Il programma richiede la correzione; al terzo tentativo può accettare una coppia
ammessa con fatti ancora non verificati. Questa regola spiega come tutte le
compilazioni possano riuscire anche quando alcune risposte hanno fatti non validi.

\textbf{Le ipotesi in prosa non sono verificate semanticamente e non vanno
considerate affermazioni vere.} La correttezza dei fatti strutturati non
certifica la spiegazione libera né la qualità della scelta futura.
"""
t+=page("Conclusioni e limiti")
t+=r"\subsection{Lettura del confronto}"+"\n"
t+=("In queste esecuzioni, $k=1$ offre il compromesso osservato più favorevole fra "
    "qualità e costo. Rispetto a $k=5$, lo score medio è inferiore di "+
    fmt(m("5","score")-m("1","score"),8)+
    " su una scala 0--1; i token complessivi diminuiscono del "+
    fmt(100*(1-m("1","total_tokens","sum")/m("5","total_tokens","sum")))+
    r"\% e il tempo totale medio del "+fmt(100*(1-m("1","total_seconds")/m("5","total_seconds")))+r"\%.\par"+"\n")
t+=("Passare da cinque a dieci esempi aumenta i token del "+
    fmt(100*(m("10","total_tokens","sum")/m("5","total_tokens","sum")-1))+
    r"\% e il tempo totale medio del "+fmt(100*(m("10","total_seconds")/m("5","total_seconds")-1))+
    r"\%, senza un miglioramento medio dello score. Le correzioni passano da 36 a 77 e le risposte finali con fatti non validi da 17 a 38.\par"+"\n")
t+=r"""Il risultato è coerente con l'idea che il primo vicino contenga già buona
parte dell'informazione utile per questo modello e questo catalogo. È una
\textbf{interpretazione}, non una proprietà dimostrata del RAG in generale.
Aggiungere esempi può introdurre altri riferimenti senza migliorare la decisione.

Il caso più diverso è \nolinkurl{qpeinexact_indep_tket_6}: cinque o dieci esempi
migliorano lo score di circa 0,02113 rispetto a uno. Questo caso resta visibile
e impedisce di descrivere le tre varianti come identiche su ogni circuito.
Le piccole differenze delle medie non sono percentuali relative: per esempio,
0,000235 di score equivale a circa 0,0235 punti percentuali della scala 0--1.

\subsection{Che cosa non possiamo concludere}
Le varianti a uno e dieci esempi sono state decise dopo aver osservato il Test.
Questo report non cambia retroattivamente la configurazione scelta sulla
validation. Per scegliere un valore operativo con evidenza più generale
servirebbe una conferma su dati nuovi o una procedura di selezione dedicata.

Ogni circuito è valutato una volta per variante. Le famiglie del corpus sono
correlate e non ci sono repliche per misurare la variabilità temporale.
Le date, le revisioni del codice e lo stato della cache differiscono.
I parametri delle chiamate e il modello coincidono, ma i tempi non isolano
perfettamente l'effetto causale di $k$. Non sono misurati energia o picco
di memoria; non presentiamo test di significatività né equivalenza statistica.

\subsection{Fonti e ricostruzione}
Sono stati controllati i 270 esiti e le """
t+=str(len(D["audited_attempts"]))
t+=r""" risposte complete, comprese
le correzioni. Sono stati verificati hash dei circuiti e contratti, identità
del modello, parametri reali delle chiamate, vista del circuito, contenuto
degli esempi train, ordine dei recuperi, token e fatti. Nessuna nuova inferenza
o compilazione quantistica è stata eseguita per creare questo report.

I risultati provengono da \nolinkurl{test/risultati/llm_rag} per $k=5$ e dalle
campagne \nolinkurl{test/numero_esempi/k_1} e \nolinkurl{test/numero_esempi/k_10}.
Tutti i percorsi sono relativi ad \nolinkurl{archivio/valutazione}.
Il documento riprende dal confronto a cinque sistemi le misure di riuscita,
soglia 0,8, score, tempi, token, correzioni, distribuzioni e confronti appaiati.

La cartella conserva \texttt{dati.json}, \texttt{provenienza.json},
\texttt{tabelle/circuiti.csv}, il generatore e questo sorgente LaTeX autonomo.
L'appendice rende individuabile ogni punto dei grafici. I rapporti precedenti
e i registri sperimentali non sono stati modificati.
"""
t+=r"\clearpage\appendix\begin{landscape}\section{Valori per circuito: score e tempo totale}"+"\n"
t+=r"Tutti i casi sono riusciti. I tempi sono in secondi; i valori completi restano nel CSV. L'indice è comune a tutti i grafici.\par"
t+=r"\begingroup\footnotesize\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.16}\begin{longtable}{r l r rrr rrr}\toprule Indice & Circuito & Qubit & Score 1 & Score 5 & Score 10 & Tempo 1 & Tempo 5 & Tempo 10\\\midrule\endfirsthead\toprule Indice & Circuito & Qubit & Score 1 & Score 5 & Score 10 & Tempo 1 & Tempo 5 & Tempo 10\\\midrule\endhead\bottomrule\endfoot"+"\n"
for i,c in enumerate(IDS,1):
 vals=[str(i),esc(c),str(ROWS["5"][c]["num_qubits"]),*[fmt(ROWS[k][c]["score"],6) for k in KS],*[fmt(ROWS[k][c]["total_seconds"]) for k in KS]]
 t+=" & ".join(vals)+r"\\"+"\n"
t+=r"\end{longtable}\endgroup\end{landscape}"
t+=r"\clearpage\begin{landscape}\section{Valori per circuito: token, correzioni e fatti}"+"\n"
t+=r"Token: somma di ingresso e uscita su tutti i tentativi. C: correzioni. V: tutti i fatti finali validi (sì/no); non indica la riuscita della compilazione.\par"
t+=r"\begingroup\footnotesize\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.16}\begin{longtable}{r l rrr rrr ccc}\toprule Indice & Circuito & Token 1 & Token 5 & Token 10 & C1 & C5 & C10 & V1 & V5 & V10\\\midrule\endfirsthead\toprule Indice & Circuito & Token 1 & Token 5 & Token 10 & C1 & C5 & C10 & V1 & V5 & V10\\\midrule\endhead\bottomrule\endfoot"+"\n"
for i,c in enumerate(IDS,1):
 vals=[str(i),esc(c),*[fmt(ROWS[k][c]["total_tokens"],0) for k in KS],*[str(ROWS[k][c]["retries"]) for k in KS],*["sì" if ROWS[k][c]["facts_status"]=="verified" else "no" for k in KS]]
 t+=" & ".join(vals)+r"\\"+"\n"
t+=r"\end{longtable}\endgroup\end{landscape}\end{document}"+"\n"
(BASE/"confronto_k.tex").write_text(t,encoding="utf-8")
print(BASE/"confronto_k.tex")

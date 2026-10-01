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
KS=["M","W","S"]
LABELS={"M":"Manhattan","W":"WL","S":"WL + sintesi"}
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
    options=(f"width={width},height={height},title={{{LABELS[k]}}},xlabel={{Indice circuito}},ylabel={{{label}}},"
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
    text+=r"{\small Ogni punto è un circuito. Le scale sono comuni fra i tre sistemi per ciascuna colonna. L'indice segue l'ordine alfabetico dell'appendice.}\par"
    return text

PRE=r"""\documentclass[a4paper,10pt]{article}
\usepackage[margin=1.8cm]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[italian]{babel}
\usepackage{lmodern,booktabs,tabularx,longtable,array,amsmath,xcolor,pgfplots,xurl,hyperref,fancyvrb}
\usepackage[expansion=false]{microtype}
\usetikzlibrary{arrows.meta,positioning}
\pgfplotsset{compat=1.18}
\definecolor{kuno}{HTML}{167D9A}\definecolor{kcinque}{HTML}{D47A17}\definecolor{kdieci}{HTML}{7656A3}
\hypersetup{hidelinks}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\setlength{\emergencystretch}{3em}
\begin{document}
{\small\bfseries CONFRONTO DEI REGISTRI CONSERVATI | 29 settembre 2026}\par
{\LARGE\bfseries Recuperare esempi dalla struttura dei circuiti}\par
{\Large RAG Manhattan, RAG WL e RAG WL con sintesi}\par\medskip
\section{L'idea: dalla distanza fra caratteristiche alle dipendenze}
Un buon esempio storico dovrebbe aiutare a scegliere dispositivo e configurazione
per il circuito corrente. Il recupero classico confronta 49 caratteristiche numeriche,
trasformate usando il train, con la distanza Manhattan.
La nuova idea è rappresentare le dipendenze fra le operazioni e confrontare i grafi.
La nostra ipotesi è che circuiti con strutture simili possano richiedere scelte di
compilazione simili. È un'ipotesi da misurare, non una proprietà garantita.

Qiskit rappresenta il circuito come \texttt{DAGCircuit}, un grafo diretto senza
cicli: le operazioni sono nodi e i fili collegano operazioni successive.
Una porta su due qubit è un solo nodo con due fili in ingresso e in uscita
\cite{qiskit}. Il DAG rappresenta precedenze; non è il grafo di connessione del dispositivo.

\subsection{Un esempio concreto: stesse porte, ordine diverso}
In A la porta Z segue CX sul secondo qubit; in B la precede.
I due circuiti hanno due qubit e le stesse tre porte, ma il loro DAG cambia.
I nodi $I_i$ e $O_i$ sono ingressi e uscite. I colori servono soltanto a leggere il disegno.
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
for name,before in [("A: Z dopo CX",False),("B: Z prima di CX",True)]:
 t+=r"\begin{minipage}{.49\linewidth}\centering\textbf{"+name+r"}\par\medskip"+drawing(before)+r"\end{minipage}\hfill"
t+=r"""\par\medskip
Nel codice si conservano anche misura, barriere e fili classici. Le frecce
rispettano il verso del circuito. Non si decompongono le porte originali del QASM:
anche il modo in cui il circuito è scritto può quindi influire sulla somiglianza.
"""
t+=page("WL, spiegato attraverso i due grafi")
t+=r"""Weisfeiler--Lehman (WL) costruisce descrizioni locali sempre più ampie:
ogni nodo parte da un'etichetta e, a ogni giro, la aggiorna usando le etichette
dei vicini. Si contano poi le etichette ottenute per confrontare i grafi
\cite{wl}. La versione usata qui è un adattamento diretto e con archi etichettati.

\textbf{Giro 0.} H, CX e Z sono riconosciute dal tipo di operazione.
Nei due piccoli grafi il conteggio iniziale è uguale.

\textbf{Giro 1.} Ogni nodo guarda separatamente chi lo precede e chi lo segue.
Il nodo CX di A vede Z fra i successori; quello di B la vede fra i predecessori.
Le sue nuove etichette sono diverse. Anche Z cambia contesto.
H vede invece ingresso e CX in entrambi i grafi: la sua etichetta resta uguale fra A e B.

\textbf{Giro 2.} H riceve ora la diversa etichetta del vicino CX.
La differenza si propaga quindi anche a H. I giri successivi raccolgono
informazione a distanza crescente; non aggiungono operazioni al circuito.
"""
t+=table(["Nodo","Giro 0, A/B","Giro 1, A/B","Giro 2, A/B"],[
["H","uguale","uguale","diversa"],["CX","uguale","diversa","diversa"],["Z","uguale","diversa","diversa"]])
t+=r"""\subsection{Che cosa calcola la nostra implementazione}
Le etichette iniziali contengono nome della porta, numero di operandi,
stato dei controlli e parametri numerici raggruppati in intervalli di $\pi/8$.
I nomi assoluti dei qubit non entrano nelle etichette. Gli archi conservano
tipo quantistico/classico e posizione locale dell'operando: per CX si distinguono
controllo e bersaglio. Le porte delle barriere sono trattate simmetricamente.
Archi ripetuti non vengono eliminati.

Una nuova etichetta riassume quella precedente e i due insiemi con molteplicità
di vicini entranti e uscenti, includendo le etichette degli archi.
Le stesse descrizioni ricevono gli stessi identificativi anche in grafi diversi.
Se $\phi_r(G)$ conta le etichette al giro $r$, la similarità è:
\[
s_h(G,H)=
\frac{\sum_{r=0}^{h}\langle\phi_r(G),\phi_r(H)\rangle}
{\sqrt{\sum_{r=0}^{h}\|\phi_r(G)\|^2}
 \sqrt{\sum_{r=0}^{h}\|\phi_r(H)\|^2}}.
\]
Si recuperano i cinque esempi train compatibili con similarità maggiore;
le parità sono ordinate per identificativo RAG. Nei Test si usa $h=24$:
il confronto combina il giro iniziale e 24 aggiornamenti.
La normalizzazione attenua l'effetto della dimensione, ma non lo elimina.

\textbf{Limite della misura.} Similarità alta non significa equivalenza
quantistica, stessa fedeltà o stessa scelta ottimale. WL può non distinguere
alcuni grafi diversi. Il risultato dipende da etichette, parametri raggruppati,
porte originali e profondità scelta. Queste sono decisioni della nostra
implementazione, non conclusioni del lavoro teorico citato.
"""
t+=page("Validation e confronto controllato")
v=D["validation"]["methods"]
t+=r"""Prima dei nuovi Test è stato scelto il numero di giri usando gli 88
circuiti di validation, separati dai 90 circuiti Test.
La ricerca è stata estesa prima a 6 e poi a 30 giri, dopo aver osservato
i risultati precedenti. Si tratta quindi di una selezione adattiva sugli stessi 88 casi.

La validation non chiamava l'LLM. Recuperava esempi e valutava la coppia al primo
posto del primo esempio sui risultati di compilazione già archiviati del circuito
di validation. Lo score era la mediana dei semi 0, 1 e 2, per coppie con tre successi.
Il \emph{regret} era la differenza dal migliore score osservato disponibile.
In 70 casi le matrici erano incomplete: il riferimento non è un ottimo globale certo.
"""
t+=table(["Metodo","Score medio","Regret medio","Confronto (s)"],[
["Manhattan" if key=="manhattan" else "$h="+key[4:]+"$",fmt(v[key]["top1_score"]["mean"],6),fmt(v[key]["top1_regret_common"]["mean"],6),fmt(v[key]["ranking_seconds"]["mean"],3)]
 for key in ["manhattan","wl_h1","wl_h6","wl_h23","wl_h24","wl_h27","wl_h30"]])
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.91\linewidth,height=5cm,xmin=1,xmax=30,xlabel={Giri WL},ylabel={Score medio, validation},grid=major,legend pos=south east]"
t+=r"\addplot[thick,kcinque,mark=*,mark size=1.3pt] coordinates {"+coords([(h,v[f"wl_h{h}"]["top1_score"]["mean"]) for h in range(1,31)])+r"};\addlegendentry{WL}"
t+=r"\addplot[kuno,dashed,domain=1:30]{"+str(v["manhattan"]["top1_score"]["mean"])+r"};\addlegendentry{Manhattan}"
t+=r"\addplot[only marks,kdieci,mark=*,mark size=3pt] coordinates {(24,"+str(v["wl_h24"]["top1_score"]["mean"])+r")};\addlegendentry{Scelto $h=24$}\end{axis}\end{tikzpicture}\end{center}"
t+=r"""È stato fissato $h=24$: è il primo valore del minimo regret condiviso con
25--27, con score identici circuito per circuito. Il vantaggio medio su 23 è
soltanto 0,00000366. Non si attribuisce significato statistico a questa differenza.
Fra i valori a pari merito, 24 richiede meno tempo e ha un indicatore secondario
leggermente migliore sui cinque esempi. La scelta è stata congelata prima dei nuovi Test.

\subsection{Tre sistemi, una sola quantità di esempi}
"""
t+=table(["Sistema","Recupero","Informazioni nel prompt"],[
["Manhattan (M)","49 caratteristiche","Prompt classico, cinque esempi"],
["WL (W)","DAG, $h=24$","Prompt classico, cinque esempi"],
["WL + sintesi (S)","DAG, $h=24$","Prompt classico e sintesi dei sei grafi"]],"l l X")
t+=r"""W e S hanno recuperato gli stessi cinque record, nello stesso ordine e
con le stesse similarità in tutti i 90 casi. Il Dataset train resta immutato:
la sintesi è aggiunta dinamicamente al circuito corrente e agli esempi E1--E5.
Il formato della risposta e le regole sui fatti sono comuni."""
t+=page("Un campo reale aggiunto al prompt")
ex=D["example"]; cur=ex["summaries"]["current_circuit"]; e1=ex["summaries"]["examples"][0]["summary"]
t+=r"Il caso è \nolinkurl{"+ex["circuit_id"]+r"}. Il seguente estratto proviene dal blocco TOON realmente inviato al modello, verificato rispetto a \texttt{prompt.json}. Sono omesse le altre statistiche e le sintesi di E1--E5.\par"
lines=ex["actual_summary_toon"].splitlines()
end=next(i for i,line in enumerate(lines) if "most_frequent_direct_transitions" in line)
t+=r"\begin{Verbatim}[fontsize=\small,frame=single]"+"\n"+"\n".join(lines[:end])+"\n"+r"\end{Verbatim}"+"\n"
t+=r"""\texttt{two\_qubit\_interaction\_pairs: 66} significa che nel circuito
corrente 66 coppie distinte di qubit sono coinvolte in porte a due qubit.
Con 12 qubit sono tutte le coppie possibili. È una proprietà del sorgente,
non una misura della fedeltà futura.
\texttt{dependency\_layers\_including\_barriers} conta livelli di dipendenza
includendo le barriere; non esprime una durata fisica e può differire dalla
profondità riportata dal prompt classico.
"""
t+=table(["Campo","Circuito corrente","Esempio E1"],[
["Qubit",cur["num_qubits"],e1["num_qubits"]],
["Operazioni, incluse barriere",cur["operation_nodes_including_barriers"],e1["operation_nodes_including_barriers"]],
["Livelli di dipendenza",cur["dependency_layers_including_barriers"],e1["dependency_layers_including_barriers"]],
["Coppie di interazione",cur["two_qubit_interaction_pairs"],e1["two_qubit_interaction_pairs"]]])
t+=r"\small Il campo \texttt{dag\_summaries.examples[0].example\_id = E1} collega la sintesi al primo record recuperato: \nolinkurl{"+ex["records"][0]["rag_id"]+r"}. Il collegamento è stato controllato con l'indice separato. Il blocco completo contiene anche le otto transizioni dirette più frequenti.\normalsize\par"
t+=r"""I numeri sono calcolati dal programma; non sono una descrizione inventata
dall'LLM. Il modello può usarli nella spiegazione libera, ma il verificatore dei
fatti non è stato ampliato con nuove affermazioni sul grafo."""
t+=page("Risultati sui 90 circuiti Test")
t+=r"""Tutti i sistemi usano Qwen3.5-4B Q8\_0, lo stesso file di pesi,
temperatura 0, seme 20260913 e massimo 4.096 token di risposta.
Contesto richiesto: 60.000 token; pensiero esteso disattivato.
Restano invariati cinque Target sintetici, dodici configurazioni Qiskit,
seme di compilazione 0, un processo e limite esterno di 100 secondi.
I record confrontati sono tutti e soli i 90 Test, con gli stessi sorgenti.

Lo score è l'\emph{expected fidelity}, fra 0 e 1: maggiore è migliore.
È una stima sul Target sintetico, non una misura su hardware quantistico reale.
Il denominatore delle medie dello score è qui sempre 90, perché tutte le
compilazioni sono riuscite.
"""
HEAD=["Misura",*[LABELS[k] for k in KS]]
t+=table(HEAD,[
["Compilazioni riuscite",*[str(S[k]["successes"])+"/90" for k in KS]],
["Fallimenti",*[str(90-S[k]["successes"]) for k in KS]],
row_metric("Score medio","score",6),row_metric("Score mediano","score",6,"median"),
["Score almeno 0,8",*[str(S[k]["threshold_08"])+"/90" for k in KS]],
row_metric("Tempo totale medio (s)","total_seconds"),row_metric("Token totali, somma","total_tokens",0,"sum")])
t+=r"\subsection{Confronti appaiati}"
t+=table(["Differenza","Media score","Meglio","Pari","Peggio","Stessa coppia"],[
[LABELS[p["a"]]+" meno "+LABELS[p["b"]],fmt(p["delta"]["mean"],6),p["wins"],p["ties"],p["losses"],str(p["same_pair"])+"/90"] for p in D["pairs"]])
t+=r"La parità usa $|\Delta|\leq10^{-12}$. La coppia è dispositivo/configurazione; score uguali non implicano scelte uguali. Le medie non sono percentuali di circuiti migliorati.\par"
t+=table(["Qubit","Casi","Manhattan","WL","WL + sintesi"],[
[g["label"],g["n"],*[fmt(g["score"][k]["mean"],6) for k in KS]] for g in D["qubit_groups"]])
t+=r"""Le fasce riprendono il report precedente e sono descrittive.
Il numero di qubit da solo non definisce la difficoltà. Tutti i casi,
anche quelli con score basso, entrano nelle tabelle e nei grafici."""
t+=page("Dove cambiano gli score")
changed=D["changed_circuits"]
t+=str(D["identical_all"])+r" circuiti hanno lo stesso score nei tre sistemi. La tabella mostra i "+str(min(12,len(changed)))+r" casi con maggiore escursione fra massimo e minimo, ordinati senza privilegiare una variante. L'appendice comprende tutti i 90 casi.\par"
t+=table(["Circuito","Manhattan","WL","WL + sintesi"],[
[r"\nolinkurl{"+c+"}",*[fmt(ROWS[k][c]["score"],6) for k in KS]] for c in changed[:12]])
t+=r"""Nei cinque peggioramenti di S rispetto a W cambiano i dispositivi:
da Quantinuum H2 a IBM Falcon 127 nei casi QPE a 30--40 qubit,
e a IBM Heron 156 nei due casi a 50 qubit. Per esempio,
\texttt{qpeexact\_indep\_qiskit\_30} passa da 0,520294 a 0,043532.
È un cambiamento osservato nella scelta, non la prova che una singola
statistica della sintesi ne sia la causa.
"""
t+=r"\subsection{Quanto cambia il recupero}"
overlap=[len(set(D["retrieval_ids"]["M"][c])&set(D["retrieval_ids"]["W"][c])) for c in IDS]
t+=f"Manhattan e WL hanno in media {fmt(sum(overlap)/90,2)} esempi comuni su cinque. "
t+=f"In {sum(D['retrieval_ids']['M'][c]==D['retrieval_ids']['W'][c] for c in IDS)} casi su 90 coincidono tutti i record e il loro ordine. "
t+=r"Fra W e S il recupero coincide sempre: le differenze di risposta sono osservate con gli stessi esempi storici, ma con informazioni aggiuntive sul grafo.\par"
t+=r"\subsection{Cambiamenti nella coppia scelta}"
for p in D["pairs"]:
 t+=LABELS[p["a"]]+" rispetto a "+LABELS[p["b"]]+": "+str(90-p["same_pair"])+r" coppie diverse su 90.\par "
t+=page("Tempi: distinguere le componenti")
t+=r"Tutte le celle riportano media / mediana in secondi, su 90 misure. Non si sommano le righe: alcune componenti sono incluse in altre.\par"
t+=table(HEAD,[[lab,*[fmt(m(k,key))+" / "+fmt(m(k,key,"median")) for k in KS]] for lab,key in [
("Totale del caso","total_seconds"),("Preparazione e scelta","choice_seconds"),("RAG e controlli","rag_seconds"),
("Risposte LLM, cumulative","llm_response_seconds"),("Compilazione interna","compilation_seconds"),("Processo di compilazione","compilation_process_seconds")]])
t+=r"""Il totale copre l'intero caso. Preparazione e scelta comprende recupero,
costruzione del prompt, tokenizzazione, risposte e controlli.
Il tempo LLM somma le attese delle risposte, incluse le correzioni.
La misura interna riguarda il compilatore; quella di processo include anche
avvio e controlli.

Il massimo WL, 297,36 secondi in \texttt{qpeexact\_indep\_qiskit\_15},
comprende 295,98 secondi di preparazione/scelta ma soltanto 24,65 secondi
di risposte LLM. Le fasi dettagliate non spiegano tutta l'attesa:
non se ne attribuisce la causa a WL. Il caso resta incluso nella media.

\subsection{Il costo dell'indice WL è separato}
Nel sistema Manhattan i controlli e il caricamento dell'indice fanno parte
della misura RAG per circuito. Nei nuovi sistemi l'indice WL è verificato/caricato
una volta per sessione e riutilizzato. Il suo costo è conservato separatamente
e non è incluso nel totale dei singoli casi. Il confronto diretto dei tempi
RAG non isola quindi la velocità dei due algoritmi.
"""
prep={k:sum(r["index_preparation_seconds"] for r in D["preparation"][k]) for k in ["W","S"]}
t+=table(["Misura","WL","WL + sintesi"],[
["Preparazione indice registrata (s)",*[fmt(prep[k]) for k in ["W","S"]]],
["Quota per 90 casi (s), calcolata",*[fmt(prep[k]/90) for k in ["W","S"]]],
["Totale medio + quota indice (s)",*[fmt(m(k,"total_seconds")+prep[k]/90) for k in ["W","S"]]]])
t+=r"""La quota è una ripartizione calcolata, non una nuova misura.
Non ricostruisce eventuali costi storici di costruzione dell'indice.
Le campagne non sono repliche intercalate: carico del computer, cache e avvio
del server possono influire sui tempi. Non è stata raccolta la memoria,
quindi non si può confrontarne il consumo."""
t+=page("Token, chiamate e correttezza dei fatti")
t+=table(HEAD,[
row_metric("Primo ingresso, media token","first_input_tokens",1),
row_metric("Ingresso, somma token","input_tokens",0,"sum"),
row_metric("Uscita, somma token","output_tokens",0,"sum"),
row_metric("Totale, somma token","total_tokens",0,"sum"),
row_metric("Totale per circuito, media","total_tokens",1),
row_metric("Chiamate, somma","llm_calls",0,"sum"),
row_metric("Correzioni, somma","retries",0,"sum"),
["Casi con correzioni",*[str(S[k]["retry_cases"])+"/90" for k in KS]],
["Tutti i fatti validi al primo tentativo",*[str(S[k]["valid_first"])+"/90" for k in KS]],
["Tutti i fatti validi nella risposta finale",*[str(S[k]["valid_final"])+"/90" for k in KS]],
["Fatti finali validi / dichiarati",*[f'{S[k]["facts_verified"]}/{S[k]["facts_total"]}' for k in KS]]])
t+=r"""I token totali includono ingresso e uscita di tutte le chiamate.
L'ingresso conta anche token serviti dalla cache: non è una misura dei soli token
ricalcolati né del costo monetario.
Il primo ingresso separa la lunghezza iniziale del prompt dal costo delle correzioni.
Le regole consentono al massimo tre risposte per circuito.
"""
types=[("Stesso dispositivo dell'esempio","selected_device_matches_example"),("Coppia fra i risultati mostrati","selected_pair_among_reported_best"),("Stesso numero di qubit","same_qubit_count_as_example"),("Capacità del dispositivo","selected_device_has_enough_qubits")]
fr=[]
for label,kind in types:
 vals=[]
 for k in KS:
  items=[x for x in S[k]["fact_kinds"] if x["assertion"]==kind]
  vals.append(str(sum(x["n"] for x in items if x["result"]=="verified"))+"/"+str(sum(x["n"] for x in items)))
 fr.append([label,*vals])
t+=table(["Tipo: validi / dichiarati",*[LABELS[k] for k in KS]],fr)
t+=r"""I fatti non validi sono 17, 33 e 54. In 17, 33 e 53 casi,
rispettivamente, la capacità del dispositivo viene associata a un esempio,
mentre la regola richiede il catalogo hardware e nessun riferimento E1--E5.
Questo errore di supporto non significa che il dispositivo abbia pochi qubit.
Nella variante S resta anche un riferimento storico sbagliato:
in \texttt{qpeexact\_indep\_qiskit\_30} viene dichiarato lo stesso dispositivo
di E4, che riporta Quantinuum H2, mentre la scelta è IBM Falcon 127.

Sono verifiche automatiche dei fatti strutturati rispetto ai record citati
e al catalogo hardware. Una risposta finale può contenere fatti non validi
pur proponendo una coppia ammessa: dopo il terzo tentativo il protocollo lo consente.
La riuscita della compilazione non certifica la spiegazione.

\textbf{Le ipotesi in prosa non sono verificate semanticamente e non vanno
prese come affermazioni vere.} Anche le deduzioni libere dalla sintesi del
grafo restano ipotesi. I fatti storici validi descrivono l'esempio citato,
non garantiscono lo score del circuito corrente."""
t+=dual_page("Score e tempo totale per circuito","score","total_seconds","Score","Tempo totale (s)",
r"Stessi 90 circuiti e stesso ordine in tutti i pannelli. La scala dello score è 0--1. Le differenze di costo sono misure delle campagne conservate.")
t+=dual_page("Compilazione: tempo interno e tempo di processo","compilation_seconds","compilation_process_seconds","Interno (s)","Processo (s)",
r"Il processo comprende anche avvio e controlli. Scelte diverse possono produrre compilazioni diverse; questi tempi non misurano soltanto il recupero.")
t+=dual_page("Token e tempo delle risposte LLM","total_tokens","llm_response_seconds","Token totali","Risposte LLM (s)",
r"Entrambe le colonne includono tutte le chiamate dello stesso caso. Un punto elevato può riflettere anche le richieste di correzione.")
t+=dual_page("Correzioni e recupero","retries","rag_seconds","Correzioni","RAG e controlli (s)",
r"Zero, uno e due indicano il numero di risposte aggiuntive. La colonna RAG esclude la preparazione per sessione dell'indice WL, riportata separatamente.")
t+=page("Distribuzione degli score e differenze appaiate")
t+=r"La cumulativa mostra la quota di circuiti con score non superiore all'ascissa. Nei pannelli sotto ogni punto è una differenza sullo stesso circuito; zero è una parità.\par"
t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=5cm,xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Score},ylabel={Quota cumulativa},grid=major,legend pos=north west]"
for k,style in zip(KS,["solid","dashed","dotted"]):
 vals=sorted(r["score"] for r in RUNS[k])
 t+=r"\addplot[const plot,thick,"+COLORS[k]+","+style+"] coordinates {"+coords([(0,0),*[(x,(i+1)/90) for i,x in enumerate(vals)],(1,1)])+r"};\addlegendentry{"+LABELS[k]+"}"
t+=r"\end{axis}\end{tikzpicture}\end{center}"
deltas=[ROWS[k][c]["score"]-ROWS["M"][c]["score"] for k in ["W","S"] for c in IDS]
lo=min(deltas)-.02;hi=max(deltas)+.02
for k in ["W","S"]:
 t+=r"\begin{center}\begin{tikzpicture}\begin{axis}[width=.92\linewidth,height=4.8cm,title={"+LABELS[k]+r" meno Manhattan},xlabel={Indice circuito},ylabel={Differenza score},xmin=0,xmax=91,ymin="+str(lo)+",ymax="+str(hi)+r",grid=major]"
 t+=r"\addplot[gray,dashed,domain=0:91]{0};\addplot[only marks,mark size=1.5pt,"+COLORS[k]+"] coordinates {"+coords([(i+1,ROWS[k][c]["score"]-ROWS["M"][c]["score"]) for i,c in enumerate(IDS)])+r"};\end{axis}\end{tikzpicture}\end{center}"
t+=page("Conclusioni e limiti del confronto")
t+=r"\subsection{Che cosa mostrano questi Test}"
for p in D["pairs"]:
 a,b=p["a"],p["b"]
 t+=LABELS[a]+" rispetto a "+LABELS[b]+": differenza media di score "+fmt(p["delta"]["mean"],6)+", con "+str(p["wins"])+" miglioramenti, "+str(p["ties"])+" parità e "+str(p["losses"])+r" peggioramenti su 90.\par"
t+="L'aggiunta della sintesi, rispetto al solo WL, cambia il primo ingresso medio di "+fmt(100*(m("S","first_input_tokens")/m("W","first_input_tokens")-1))+r"\% e i token complessivi di "+fmt(100*(m("S","total_tokens","sum")/m("W","total_tokens","sum")-1))+r"\%. Il tempo totale medio osservato cambia di "+fmt(100*(m("S","total_seconds")/m("W","total_seconds")-1))+r"\%.\par"
t+=r"""Il solo WL è quasi indistinguibile da Manhattan nella media:
la differenza è $-0,0000259$. La sintesi perde invece circa 0,01938
rispetto a WL, cioè 1,938 punti sulla scala dello score espressa in percentuale.
I cinque peggioramenti riguardano QPE a 30, 40 e 50 qubit.
Nella fascia oltre 16 qubit la media scende da 0,279117 a 0,181878;
la soglia di 0,8 resta però 70/90 perché quei casi erano già sotto soglia.
Per questo la sola copertura della soglia nasconderebbe il peggioramento.

La validation riguardava un criterio di trasferimento della scelta storica,
non la risposta del modello. Un recupero migliore secondo quel criterio
non obbliga l'LLM a scegliere meglio. Il confronto W--S mantiene invece identici
i record recuperati e consente di osservare l'effetto dell'informazione aggiunta
sulle risposte, sui token e sulle correzioni.
"""
# Data-dependent conclusion, never copied from older report.
best=max(KS,key=lambda k:m(k,"score"))
t+="Il maggiore score medio osservato appartiene a "+LABELS[best]+". "
if m("S","score")<=m("W","score"):
 t+="La sintesi non migliora lo score medio rispetto al solo recupero WL in questo campione. "
else:
 t+="La sintesi migliora lo score medio rispetto al solo recupero WL in questo campione. "
t+=r"""Questa è una conclusione descrittiva delle esecuzioni conservate,
non una prova che lo stesso ordinamento valga per altri modelli o circuiti.

\subsection{Limiti e provenienza}
La base Manhattan è la prova storica del 21 settembre; le due prove WL sono
del 29 settembre. Pesi, parametri di generazione e sorgenti coincidono,
ma revisioni del codice, data e gestione dell'indice differiscono.
Non sono state fatte repliche intercalate o misure di memoria.
Le medie non costituiscono un test statistico di superiorità.

La scelta di $h$ usa esclusivamente la validation; la progettazione della nuova
campagna avviene però dopo l'analisi dei Test precedenti sugli stessi 90 circuiti.
Non si tratta dunque di un nuovo campione di conferma mai osservato.
Circuiti della stessa famiglia possono inoltre essere correlati.

Il report è ricostruito dai registri di ogni circuito, non trascritto dalle
sole medie. Sono stati controllati identificativi e hash dei sorgenti, contratti,
modello, parametri delle chiamate, recuperi, token, sintesi realmente inviate e
verifiche dei fatti. Nessuna nuova inferenza o compilazione quantistica è stata eseguita.
Gli script, le tabelle complete e gli hash delle fonti sono conservati accanto al PDF.

\subsection{Riproducibilità}
\texttt{genera\_report.py} legge i registri e produce \texttt{dati.json},
\texttt{provenienza.json} e \texttt{tabelle/circuiti.csv}.
\texttt{impaginazione.py} genera questo sorgente autonomo, con grafici vettoriali
incorporati. L'opzione \texttt{--output} del primo script permette di creare
una nuova cartella senza sovrascrivere un'analisi precedente.
"""
t+=page("Appendice: tutti i circuiti e i tre score")
t+=r"L'indice è quello dei grafici. Il CSV contiene anche tutte le misure di tempo, token e fatti, senza arrotondamenti di presentazione.\par"
t+=r"\begingroup\small\renewcommand{\arraystretch}{1.1}\setlength{\tabcolsep}{4pt}\begin{longtable}{r p{8.2cm} r r r}\toprule N & Circuito & Manhattan & WL & WL + sintesi\\\midrule\endfirsthead\toprule N & Circuito & Manhattan & WL & WL + sintesi\\\midrule\endhead"
for i,c in enumerate(IDS):
 if i==45:t+=r"\pagebreak[4]"+"\n"
 t+=str(i+1)+r" & \nolinkurl{"+c+"} & "+" & ".join(fmt(ROWS[k][c]["score"],6) for k in KS)+r"\\ "+ "\n"
t+=r"\bottomrule\end{longtable}\endgroup"
t+=page("Appendice: costi per circuito")
t+=r"Ogni cella riporta tempo totale in secondi / token complessivi / correzioni. I tempi WL escludono il costo per sessione dell'indice. L'indice del circuito rimanda alla tabella precedente.\par"
t+=r"\begingroup\small\renewcommand{\arraystretch}{1.1}\setlength{\tabcolsep}{6pt}\begin{longtable}{r r r r}\toprule N & Manhattan: s / token / corr. & WL: s / token / corr. & WL + sintesi: s / token / corr.\\\midrule\endfirsthead\toprule N & Manhattan: s / token / corr. & WL: s / token / corr. & WL + sintesi: s / token / corr.\\\midrule\endhead"
for i,c in enumerate(IDS):
 if i==45:t+=r"\pagebreak[4]"+"\n"
 t+=str(i+1)+" & "+" & ".join(fmt(ROWS[k][c]["total_seconds"])+" / "+fmt(ROWS[k][c]["total_tokens"],0)+" / "+str(ROWS[k][c]["retries"]) for k in KS)+r"\\ "+"\n"
t+=r"""\bottomrule\end{longtable}\endgroup
\begin{thebibliography}{9}
\bibitem{wl} N. Shervashidze, P. Schweitzer, E. J. van Leeuwen, K. Mehlhorn,
K. M. Borgwardt. \emph{Weisfeiler--Lehman Graph Kernels}. JMLR 12, 2011, 2539--2561.
\url{https://jmlr.org/papers/v12/shervashidze11a.html}.
\bibitem{qiskit} IBM Quantum. \emph{DAGCircuit}, documentazione ufficiale Qiskit,
consultata il 29 settembre 2026. La descrizione del report segue il codice
locale Qiskit 2.5.0.
\url{https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.dagcircuit.DAGCircuit}.
\end{thebibliography}
\end{document}
"""
import re
t=re.sub(r"\\par(?=[A-Z])",lambda _:r"\par ",t)
(BASE/"confronto_manhattan_wl.tex").write_text(t,encoding="utf-8")
print(BASE/"confronto_manhattan_wl.tex")

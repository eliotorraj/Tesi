"""Testo e impaginazione del supplemento; numeri e JSON provengono dall'audit."""
import json
def esc(text):
    return "".join({"\\":r"\textbackslash{}","_":r"\_","%":r"\%","&":r"\&","#":r"\#",
                    "{":r"\{","}":r"\}","$":r"\$"}.get(c,c) for c in str(text))
def listing(value):
    return "\\begin{lstlisting}\n"+json.dumps(value,ensure_ascii=False,indent=2)+"\n\\end{lstlisting}\n"
PREAMBLE=r"""
\documentclass[a4paper,10pt]{article}
\usepackage[margin=1.85cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[italian]{babel}
\usepackage{lmodern,booktabs,tabularx,xcolor,listings,tikz,hyperref}
\usetikzlibrary{arrows.meta,positioning}
\definecolor{ink}{HTML}{163047}
\definecolor{pale}{HTML}{EEF4F7}
\definecolor{warn}{HTML}{934618}
\lstset{basicstyle=\ttfamily\fontsize{7.8}{9.1}\selectfont,breaklines=true,
breakatwhitespace=false,columns=fullflexible,keepspaces=true,showstringspaces=false,
backgroundcolor=\color{pale},frame=single,rulecolor=\color{pale},
xleftmargin=4pt,xrightmargin=4pt,aboveskip=6pt,belowskip=6pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\newcommand{\tagline}[1]{{\small\color{ink}\textbf{#1}}\par}
\begin{document}
\tagline{INTEGRAZIONE AL CONFRONTO SUL TEST | 27 settembre 2026}
{\LARGE\bfseries Qualità e correttezza\\dei fatti verificabili}\par
Analisi dei registri delle 90 decisioni LLM + RAG e delle 90 decisioni LLM senza RAG già raccolte.
Questo documento integra il confronto esistente senza modificarlo e senza eseguire nuovi Test.
\section*{Che cosa è verificato}
La risposta JSON separa \texttt{facts} da \texttt{hypothesis}. I fatti sono asserzioni scelte da quattro
tipi predefiniti: il programma confronta campi precisi con i dati disponibili. Non valuta la verità di un testo libero.

\textbf{E1, \ldots, E5 identificano gli esempi recuperati, non i fatti.}
Ogni fatto con riferimento indica un alias locale. La posizione dell'esempio nel prompt lo collega
a un record train preciso. E1 può quindi indicare circuiti diversi in richieste diverse.
\begin{center}
\begin{tikzpicture}[node distance=5mm,every node/.style={draw=ink,rounded corners,
align=center,font=\small,fill=pale,minimum height=13mm},>=Latex]
\node(a){Fatto nel JSON\\\texttt{example\_id: Ei}};
\node(b)[right=of a]{Alias Ei\\nel prompt};
\node(c)[right=of b]{Record train\\\texttt{rag\_id}};
\node(d)[right=of c]{Campo del record\\confrontato};
\draw[->,thick](a)--(b);\draw[->,thick](b)--(c);\draw[->,thick](c)--(d);
\end{tikzpicture}\end{center}
\section*{Risultati su tutti i casi}
"""
COMMENTS=[
("Due fatti sostenuti dallo stesso esempio",
 "Il dispositivo scelto coincide con quello selezionato nel record. Anche la coppia "
 r"Falcon 127 / o2\_dense\_sabre compare nella graduatoria mostrata, al primo posto. "
 r"È presente una parità con o3\_dense\_sabre: il fatto non certifica un vincitore unico. "
 "Il valore 0,9822170185 è la mediana storica di QAOA, non una misura del circuito groundstate corrente.",
 "L'ipotesi propone che il risultato si trasferisca al circuito nuovo. Questo passaggio non è verificato."),
("Coppia storica e uguaglianza dei qubit",
 "La coppia scelta è presente nelle righe mostrate del record Deutsch--Jozsa. "
 "Il circuito corrente e l'esempio hanno entrambi 2 qubit: il secondo fatto è quindi vero. "
 "L'uguaglianza del numero di qubit non prova che topologia, sequenza delle porte o risposta "
 "alla compilazione siano simili.",
 r"La formulazione \emph{similar 2-qubit circuit} è una valutazione libera. Il validatore controlla "
 "l'uguaglianza 2 = 2, non la similarità strutturale né il trasferimento delle prestazioni."),
("Un riferimento valido e uno attribuito male",
 "Il primo fatto è valido: E4 seleziona Heron 156, come la risposta. Il secondo è "
 "non valido per il contratto: la capacità deve essere confrontata con il catalogo hardware, "
 r"senza \texttt{example\_id}. In questo caso 156 qubit sono sufficienti per i 3 qubit richiesti, "
 "ma E4 non è la fonte ammessa per questa asserzione. Non correggiamo il JSON originale.",
 "Il testo ripete anche istruzioni ricevute nel prompt. Questa ripetizione riduce la qualità "
 "espositiva; non aggiunge evidenza. Profondità e qubit citati nella prosa non sono certificati "
 "dal solo fatto sul dispositivo.")]
def render(data):
    from analizza_fatti import SAMPLES
    r=data["reports"]["llm_rag"]["counts"]
    out=[PREAMBLE,r"\begin{tabularx}{\linewidth}{Xrr}\toprule Misura & LLM + RAG & Senza RAG\\\midrule"]
    for label,a,b in [
        ("Risposte finali con tutti i fatti validi",f"{r['verified']}/90","90/90"),
        ("Risposte finali con almeno un fatto non valido",f"{r['unverified']}/90","0/90"),
        ("Fatti validi nelle risposte finali",f"{r['fact_verified']}/180","90/90"),
        ("Risposte valide già al primo tentativo",f"{r['first_verified']}/90","90/90"),
        ("Risposte complete, incluse le correzioni",str(r["attempts"]),"90")]:
        out.append(f"{label} & {a} & {b}"+r"\\")
    out += [r"\bottomrule\end{tabularx}",
        f"Nel RAG, {r['historical_verified']} fatti finali riferiti agli esempi risultano tutti coerenti "
        "con i campi citati. I 17 fatti non validi sono sempre fatti sulla capacità del dispositivo "
        "con un riferimento Ei non consentito. La capacità risulta comunque sufficiente; l'errore "
        "è nell'attribuzione dell'evidenza. Dopo tre tentativi queste scelte sono state accettate dalla "
        "regola prevista, conservando lo stato di mancata verifica.",
        r"\textbf{Il 90/90 senza RAG riguarda solo la capacità in qubit.} È un controllo più semplice: "
        "non dimostra spiegazioni migliori né prestazioni di compilazione superiori.",
        r"\textbf{Le ipotesi non sono verificate sul piano dei contenuti e non vanno prese come affermazioni vere.} "
        "I controlli di formato, lunghezza o scelta ammessa non certificano ciò che il testo sostiene."]
    for i,name in enumerate(SAMPLES):
        s=next(s for s in data["samples"] if s["circuit"]==name)
        alias=next(iter(s["records"])); record=s["records"][alias]
        e=next(e for e in s["view"]["retrieved_labeled_examples"] if e["id"]==alias)
        title,explanation,limit=COMMENTS[i]
        out += [r"\newpage",r"\tagline{CAMPIONE "+str(i+1)+r" / 3 | selezione illustrativa}",
          r"\section*{"+title+"}",r"\textbf{Circuito Test:} \texttt{"+esc(name)+"}. "
          f"Risposta finale, tentativo {s['attempt']}.",
          r"\textbf{JSON originale dell'LLM.} Valori integrali; sola impaginazione modificata.",
          listing(s["response"]),r"\textbf{Collegamento all'evidenza train}",
          r"\begin{center}\begin{tikzpicture}[>=Latex,every node/.style={draw=ink,fill=pale,rounded corners,font=\small,align=center}]"
          r"\node(a){\texttt{example\_id: "+alias+r"}};"
          r"\node(b)[right=8mm of a]{"+alias+r" nel prompt};"
          r"\node(c)[right=8mm of b]{\texttt{"+esc(e["circuit"]["circuit_id"])+r"}\\esempio train};"
          r"\draw[->,thick](a)--(b);\draw[->,thick](b)--(c);\end{tikzpicture}\end{center}",
          r"{\footnotesize Record completo: \texttt{"+esc(record["rag_id"])+r"}}\par",
          r"\textbf{Estratto del record (prima riga della graduatoria)}",
          listing({"id":alias,"num_qubits":e["circuit"]["num_qubits"],"selected_device":e["selected_device"],
                   "top_configurations":[e["top_configurations"][0]]}),
          r"\textbf{Esito del controllo.} "+explanation,
          r"{\color{warn}\textbf{Limite dell'ipotesi.}} "+limit,
          r"{\small Stati registrati, in ordine: \texttt{"+esc(", ".join(c["result"] for c in s["checks"]))+r"}. "
          r"Stato della risposta: \texttt{"+esc(s["status"])+r"}.}"]
    out += [r"\newpage\tagline{PORTATA DEI RISULTATI E RIPRODUCIBILITÀ}",
       r"\section*{Correttezza dei fatti e qualità della spiegazione}",
       r"\begin{tabularx}{\linewidth}{Xrr}\toprule Tipo di fatto finale RAG & Validi & Totali\\\midrule"]
    labels={"selected_device_matches_example":"Stesso dispositivo dell'esempio",
            "selected_pair_among_reported_best":"Coppia tra le configurazioni mostrate",
            "same_qubit_count_as_example":"Stesso numero di qubit",
            "selected_device_has_enough_qubits":"Capacità in qubit sufficiente"}
    for kind,label in labels.items():
        rows=[x for x in data["reports"]["llm_rag"]["kinds"] if x["assertion"]==kind]
        out.append(label+f" & {sum(x['count'] for x in rows if x['result']=='verified')} & {sum(x['count'] for x in rows)}"+r"\\")
    out += [r"\bottomrule\end{tabularx}",
       "Il sistema rende controllabile una parte limitata della motivazione. La maggior parte dei fatti storici "
       "riguarda solo il dispositivo: 88 asserzioni. Soltanto 5 riguardano esplicitamente la coppia "
       "dispositivo/configurazione. Le 2 uguaglianze dei qubit descrivono la dimensione, senza dimostrare "
       "una somiglianza di comportamento.",
       r"\textbf{Fatto corretto non significa scelta ottima.} La presenza di una coppia nelle prime righe "
       "vale per quel circuito, quei Target sintetici e quella procedura. La regola sulla coppia accetta "
       "le righe mostrate e le parità dichiarate; non implica sempre primo posto né superiorità sul "
       "circuito corrente. La capacità in qubit è solo una condizione necessaria.",
       r"\textbf{Ipotesi: nessuna verifica semantica.} Il sistema non confronta la prosa con esperimenti, "
       "conoscenze esterne o una prova logica. Non certifica promesse di qualità, spiegazioni causali, "
       "similarità dei circuiti o bontà della configurazione. Anche una risposta con tutti i fatti validi "
       r"mantiene \texttt{explanation\_fully\_verified=false}. Le tre osservazioni sulla prosa nelle pagine "
       "precedenti sono un commento qualitativo manuale, non una misura automatica né una valutazione "
       "sistematica di tutte le 90 ipotesi.",
       r"\section*{Come è stata svolta l'analisi}",
       "Abbiamo riletto tutti i JSON delle risposte e dei controlli, compresi i tentativi scartati. "
       "Il JSON del tentativo finale coincide con la decisione conservata. Le mappe Ei, le impronte "
       "della vista e il contenuto degli esempi sono stati confrontati con prompt, registri e Dataset train "
       "verificato. Le quattro regole sono state riapplicate, anche con confronti espliciti separati "
       "dagli esiti salvati. I risultati coincidono con i controlli registrati.",
       f"Le {r['attempts']} risposte RAG contengono complessivamente "
       f"{r['attempt_fact_verified']+r['attempt_fact_unsupported']} fatti: "
       f"{r['attempt_fact_verified']} validi e {r['attempt_fact_unsupported']} non validi. "
       "Questo denominatore include le correzioni e non va confuso con i 180 fatti finali. "
       "I campioni sono scelti per illustrare tre casi diversi; i conteggi complessivi provengono "
       "dall'intero insieme dei 90 circuiti.",
       r"\section*{Fonti locali e ricostruzione}",
       r"{\small\raggedright Generatore: \texttt{archivio/valutazione/test/report/analizza\_fatti.py}. "
       r"Dati: \texttt{test/risultati/llm\_rag} e \texttt{llm\_senza\_rag}. Per ogni circuito: "
       r"\texttt{prompt.json}, \texttt{encoding.json}, \texttt{decision\_validation.json}, "
       r"\texttt{decision.json} e \texttt{attempt\_*/call/response\_raw.json}.\par}",
       r"Il file \texttt{audit\_fatti.json} conserva conteggi, controlli su tutti i tentativi, "
       "i tre JSON completi, esempi train integrali e impronte SHA-256 delle fonti. "
       "La rianalisi non ripete le compilazioni storiche: la correttezza qui riguarda la coerenza "
       "con i dati forniti, non una verifica fisica della fedeltà.",r"\end{document}"]
    return "\n".join(x + (r"\par" if x.endswith(".") or x.endswith(r"\end{tabularx}") else "") for x in out)

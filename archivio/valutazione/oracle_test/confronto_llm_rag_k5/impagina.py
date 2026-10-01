"""Genera LaTeX e grafici TikZ autonomi dai dati verificati."""
from pathlib import Path
import argparse,json
HERE=Path(__file__).resolve().parent
def esc(s): return str(s).replace("_",r"\_")
def line(c): return " & ".join(map(str,c))+r" \\"+"\n"
def table(h,rs,cols):
 return r"\begin{tabular}{"+cols+"}\n\\toprule\n"+line(h)+"\\midrule\n"+"".join(line(r) for r in rs)+"\\bottomrule\n\\end{tabular}\n"
def chart(rows):
 t=[r"\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]",
 r"\node[anchor=west,font=\bfseries] at (0,.8) {Circuito (* = oracle parziale)};",
 r"\node[anchor=west,font=\bfseries] at (8.8,.8) {Score: RAG e massimo conosciuto};",
 r"\node[anchor=west,font=\bfseries] at (20,.8) {Scarto $R-S$};"]
 for val in [0,.2,.4,.6,.8,1]:
  x=8.8+10*val
  t.extend([fr"\draw[gray!25] ({x},.25)--({x},-11.1);",fr"\node at ({x},.42) {{{val:.1f}}};"])
 for val in [0,.005,.01,.015,.02,.025]:
  x=20+5.5*val/.026
  t.extend([fr"\draw[gray!25] ({x},.25)--({x},-11.1);",fr"\node[font=\scriptsize] at ({x},.42) {{{val:.3f}}};"])
 for i,r in enumerate(rows):
  y=-i*.37
  if i%2==0: t.append(fr"\fill[gray!5] (0,{y-.16}) rectangle (25.6,{y+.16});")
  name=esc(r["circuit_id"])+("*" if not r["exhaustive"] else "")
  t.append(fr"\node[anchor=west] at (0,{y}) {{{r['id']:02d}\quad {name}}};")
  aa=8.8+10*r["system_score"]; b=8.8+10*r["oracle_score"]
  t.extend([fr"\draw[gray,thick] ({aa},{y})--({b},{y});",fr"\draw[orange!85!black,line width=.7pt] ({b},{y}) circle (2pt);",fr"\fill[blue!70!black] ({aa},{y}) circle (1pt);"])
  end=20+5.5*r["gap"]/.026; col="teal!75!black" if r["exhaustive"] else "gray!65"
  t.append(fr"\fill[{col}] (20,{y-.10}) rectangle ({end},{y+.10});" if r["gap"]>1e-12 else fr"\fill[{col}] (20,{y}) circle (.8pt);")
 return "\n".join(t+[r"\end{tikzpicture}"])
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--directory",type=Path,default=HERE/"risultati");a=ap.parse_args()
 d=json.loads((a.directory/"dati.json").read_text());rows=d["rows"];s=d["summary"]
 out=[r"""\documentclass[10pt,a4paper,landscape]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage[italian]{babel}
\usepackage[margin=15mm]{geometry}
\usepackage{lmodern,booktabs,array,amsmath,tikz,xcolor,hyperref,fancyhdr}
\hypersetup{colorlinks=true,linkcolor=blue!50!black}
\pagestyle{fancy}\fancyhf{}\lhead{\small Test: LLM + RAG, Manhattan, 5 esempi}
\rhead{\small Confronto con oracle max3}\cfoot{\small\thepage}
\setlength{\headheight}{13pt}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\newcommand{\titolo}[1]{{\Large\bfseries #1}\par\vspace{3mm}}
\begin{document}
\titolo{Quanto manca al massimo conosciuto?}
{\large LLM + RAG con 5 esempi sui 90 circuiti Test}\par
Il confronto usa i risultati originali del RAG con distanza Manhattan e l'oracle
generato il 29 settembre 2026. Lo score è \texttt{expected\_fidelity}:
una stima sui Target sintetici, non una misura su hardware quantistico reale.

\textbf{Risultato principale.} Il sistema raggiunge il massimo conosciuto in
55 casi su 90 (61,1\%) e resta sotto in 35 (38,9\%). Nessun caso supera il riferimento.
Lo scarto medio è 0,0018434763, pari a 0,18434763 punti percentuali sulla scala dello score.
La mediana dello scarto è zero. In 84 casi su 90 lo scarto non supera 0,01.
"""]
 sr=[]
 for label,key in [("Score medio RAG","mean_system"),("Massimo conosciuto medio","mean_oracle"),("Scarto medio","mean_gap"),("Scarto massimo","max_gap")]:
  sr.append([label]+[f"{v[key]:.10f}" for v in [s,s["complete"],s["partial"]]])
 out.append(table(["Misura","Tutti i circuiti","Oracle completo","Oracle parziale"],[["Circuiti",90,30,60]]+sr+[["Al massimo conosciuto","55 / 90","9 / 30","46 / 60"],["Sotto il massimo conosciuto","35 / 90","21 / 30","14 / 60"]],"lrrr"))
 out.append(r"""
\medskip\textbf{Definizione.}
Per ogni circuito, $R=\max_{d,c,s} F(d,c,s)$ è il massimo degli score validi osservati:
5 dispositivi, 12 configurazioni Qiskit e seed $s\in\{0,1,2\}$, solo su dispositivi compatibili.
Il sistema ha una sola compilazione, con seed 0, e score $S$.
Lo scarto è $\Delta=R-S$: zero indica parità; un valore positivo indica margine osservato.
I punti percentuali sono $100\Delta$; la perdita percentuale relativa è invece $100\Delta/R$.

\textbf{La generazione è terminata, ma non tutti i riferimenti sono completi.}
Le 16\,200 celle comprendono 864 incompatibilità. Delle 15\,336 compilazioni compatibili,
14\,249 riescono, 1\,086 superano il limite di 100 secondi e una fallisce.
Tutti i 90 circuiti hanno un riferimento; solo 30 hanno tutte le compilazioni compatibili riuscite.
Negli altri 60, il massimo osservato può sottostimare ciò che si otterrebbe completando le prove.
Errori e timeout sono dati mancanti, mai score zero.

\textbf{Conclusione corretta.}
In 9 circuiti il sistema uguaglia il massimo dell'intera griglia valutata;
in altri 46 uguaglia il massimo osservato di una griglia incompleta.
Non è una prova di ottimalità assoluta, né un limite superiore per compilatori esterni alla griglia.
Il confronto è descrittivo e successivo al Test: l'oracle non è stato usato nel recupero o nel prompt.
\newpage
\titolo{Scelta della coppia e variabilità del seed}
Il massimo della coppia scelta è $P=\max_{s=0,1,2}F(d_{\mathrm{LLM}},c_{\mathrm{LLM}},s)$:
\[
\underbrace{R-S}_{\text{scarto totale}} =
\underbrace{R-P}_{\text{margine cambiando coppia}}+
\underbrace{P-S}_{\text{margine cambiando seed nella stessa coppia}}.
\]
Tutte le 90 coppie scelte hanno tre compilazioni riuscite nell'oracle.
In tutti i casi il loro seed 0 riproduce esattamente lo score storico del RAG.
Il margine medio tra coppie è 0,0014354875; quello interno alla coppia è 0,0004079888.
La coppia scelta è fra le migliori note in 55/90 casi.
Anche confrontando solo il seed 0 dell'oracle, lo scarto medio resta 0,0018044775.

\textbf{I dieci scarti maggiori.} C = ricerca completa; P = ricerca parziale.
I valori sono score, non percentuali.
""")
 top=sorted(rows,key=lambda r:r["gap"],reverse=True)[:10]
 out.append(table(["Circuito","RAG $S$","Oracle $R$","Totale $R-S$","Coppia $R-P$","Seed $P-S$","Ricerca"],
 [[esc(r["circuit_id"])]+[f"{r[k]:.8f}" for k in ["system_score","oracle_score","gap","choice_gap","within_pair_gap"]]+["C" if r["exhaustive"] else "P"] for r in top],"lrrrrrc"))
 out.append(r"""
\medskip\textbf{Esempio: \texttt{qpeexact\_indep\_tket\_6}.}
Il RAG sceglie \texttt{ibm\_heron\_156} con \texttt{o3\_default\_default}.
Lo score è 0,9460784319. La stessa coppia arriva a 0,9622779418 con seed 1 o 2.
Il massimo noto è 0,9705120914 su \texttt{quantinuum\_h2\_56}
(per esempio \texttt{o2\_default\_default}, tutti i seed).
Dello scarto 0,0244336595, 0,0161995099 riguarda il seed e 0,0082341496 la coppia.
Il riferimento è parziale: 172 compilazioni valide su 180.

\textbf{Esempio: \texttt{tsp\_indep\_qiskit\_9}.}
Qui il riferimento è completo. Il RAG sceglie \texttt{quantinuum\_h2\_56},
\texttt{o2\_default\_default}, con score 0,9247191115 per tutti i seed.
\texttt{ibm\_falcon\_127}, con \texttt{o2\_default\_default} oppure
\texttt{o3\_default\_default}, raggiunge 0,9448083109.
L'intero scarto 0,0200891994 riguarda la scelta della coppia.

\textbf{Lettura dei grafici.}
Punto blu = RAG; cerchio arancione = oracle. Se coincidono, il punto è dentro il cerchio.
A destra lo scarto è ingrandito su una scala comune da 0 a 0,026:
barre verdi = oracle completo; grigie = parziale. L'asterisco indica un oracle parziale.
Gli ID e l'ordine alfabetico coincidono con le tabelle.
""")
 figs=a.directory/"grafici";figs.mkdir(exist_ok=True)
 for p in range(3):
  c=chart(rows[p*30:(p+1)*30])
  out.append(r"\newpage"+"\n"+r"\titolo{Score e scarto per circuito: "+f"{p*30+1}--{(p+1)*30}"+"}\n"+c)
  out.append(r"\par\small Blu: RAG; arancione: oracle. Scarto verde: riferimento completo; grigio: parziale. Scale identiche nelle tre pagine. I piccoli scarti sono leggibili nelle tabelle.")
  (figs/f"confronto_{p+1}.tex").write_text(r"""\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage{lmodern,tikz}
\usepackage[paperwidth=28cm,paperheight=14cm,margin=8mm]{geometry}
\pagestyle{empty}\begin{document}\noindent
"""+c+"\n"+r"\end{document}",encoding="utf-8")
 for p in range(3):
  out.append(r"\newpage"+"\n"+r"\titolo{Tabella completa: circuiti "+f"{p*30+1}--{(p+1)*30}"+"}\n")
  out.append(r"""\small Coppia al max: massimo dei tre seed della coppia scelta uguale al massimo globale.
C/P: oracle completo/parziale. Tutti gli esiti RAG sono successi.
\par\vspace{2mm}
{\fontsize{8.5}{10}\selectfont\setlength{\tabcolsep}{5pt}\renewcommand{\arraystretch}{1.18}
""")
  out.append(table(["ID","Circuito","Qubit","RAG $S$","Oracle $R$","Scarto $R-S$","Coppia al max","C/P"],
  [[r["id"],esc(r["circuit_id"]),r["num_qubits"]]+[f"{r[k]:.10f}" for k in ["system_score","oracle_score","gap"]]+["Sì" if r["selected_pair_is_best"] else "No","C" if r["exhaustive"] else "P"] for r in rows[p*30:(p+1)*30]],"rlrrrrcc"))
  out.append(r"}\par\small Parità: tolleranza $10^{-12}$ sui valori a 10 decimali. Scelte, seed e tutti i pari merito sono in \texttt{confronto\_90\_circuiti.csv} e \texttt{dati.json}.")
 out.append(r"""\newpage
\titolo{Fonti, controlli e riproducibilità}
\textbf{Sistema.} Risultati originali \texttt{llm\_rag}, avviati il 21 settembre 2026.
Recupero Manhattan e 5 esempi verificati nei registri dei 90 circuiti.
Modello Qwen selezionato con profilo \texttt{qwen/p0\_t0}, compilazione Qiskit con seed 0.
Non si usano varianti WL, recupero casuale, $k=1$ o $k=10$.

\textbf{Oracle.} Analisi \texttt{20260929T210523\_9df1db2b}, campagna \texttt{test\_max3\_v1}.
Massimo dei seed 0, 1 e 2 per coppia, poi massimo fra coppie.
Versioni: Python 3.12.13, Qiskit 2.5.0, MQT Bench 2.2.3, NumPy 2.5.1, MQT Predictor 2.4.0.
Dispositivi: \texttt{ibm\_falcon\_27}, \texttt{ibm\_heron\_133}, \texttt{ibm\_falcon\_127},
\texttt{ibm\_heron\_156}, \texttt{quantinuum\_h2\_56}.
Configurazioni, Target e opzioni sono quelli del contratto dell'oracle.

\textbf{Verifiche.}
Controllate le impronte dei 16\,200 esiti originali dell'oracle.
Ricalcolati i massimi delle 5\,400 coppie e dei 90 circuiti.
Identificativi e impronte dei sorgenti coincidono fra oracle e RAG.
Gli score RAG sono verificati sui risultati di compilazione.
Medie aritmetiche per circuito, senza esclusioni.
I sottogruppi completo/parziale comprendono circuiti diversi: le loro medie non isolano un effetto causale.
I dieci casi sono selezionati per scarto decrescente; grafici, tabelle e CSV includono tutti i 90.

\textbf{Limiti.}
L'oracle prende il migliore di tre seed, il sistema usa un solo seed:
il confronto principale è intenzionalmente favorevole all'oracle, come richiesto.
Un riferimento parziale è un limite inferiore del massimo della griglia completa.
La parità non certifica allora l'assenza di alternative migliori.
Score arrotondati a zero non provano identità dei valori non arrotondati.
Non sono state avviate compilazioni quantistiche né modificati dati originali, decisioni, prompt o Dataset.
Il grafo graphify non è stato aggiornato.

\textbf{Fonti originali.}\par
{\footnotesize
\path{/home/elio/oracoli_mqt_test/test_max3_v1/analisi/20260929T210523_9df1db2b}\par
\path{/home/elio/Tesi-mqt-2.4-v2/archivio/valutazione/test/risultati/llm_rag}\par
\path{/home/elio/Tesi-mqt-2.4-v2/archivio/valutazione/test/preparazione/contratto_congelato.json}\par
}
\textbf{Artefatti.}
\texttt{analizza.py} legge e verifica le fonti; \texttt{impagina.py} genera il LaTeX.
\texttt{dati.json} conserva misure e pari merito.
\texttt{confronto\_90\_circuiti.csv} contiene anche scelte, scarti relativi e scomposizione.
\texttt{provenienza.json} registra le impronte. In \texttt{grafici/} sono conservate le tre figure autonome.

\textbf{Separazione.}
Il report è nell'area di valutazione \texttt{oracle\_test/confronto\_llm\_rag\_k5}.
La campagna oracle resta nella cartella esterna. Nessun risultato è aggiunto all'indice RAG
o alle pipeline di decisione.
\end{document}
""")
 (a.directory/"confronto_oracle_rag5.tex").write_text("\n".join(out),encoding="utf-8")
 print(a.directory/"confronto_oracle_rag5.tex")
if __name__=="__main__":main()

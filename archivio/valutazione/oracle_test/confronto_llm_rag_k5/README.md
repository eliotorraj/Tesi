# RAG con 5 esempi e massimo conosciuto

Il report confronta il RAG classico con distanza Manhattan e 5 esempi con
l'oracle Test max3 terminato il 29 settembre 2026. Tutti i 90 circuiti sono inclusi.
Questa cartella contiene soltanto un'analisi successiva alle decisioni:
nessun dato è aggiunto al Dataset, al prompt o all'indice RAG.

## Dove leggere i risultati

- risultati/confronto_oracle_rag5.pdf: report di 9 pagine con riepilogo, esempi,
  tre grafici e tabella completa sui 90 circuiti.
- risultati/confronto_oracle_rag5.tex: sorgente autonomo, grafici incorporati.
- risultati/confronto_90_circuiti.csv: tabella con precisione completa, scelte,
  massimi, scarti assoluti e relativi, seed e tutti i pari merito.
- risultati/grafici/: tre figure autonome in PDF, PNG e LaTeX.
- risultati/dati.json: tutte le misure e i riepiloghi.
- risultati/provenienza.json: impronte delle fonti e controlli.
- risultati/verifica.json e controllo_visivo/: controlli e pagine renderizzate.

## Criterio

R è il massimo osservato fra dispositivi, configurazioni e seed 0, 1, 2.
S è lo score originale del RAG con seed 0. Lo scarto è R-S, senza tagliare
eventuali valori negativi. P è il massimo dei tre seed della coppia scelta.
La scomposizione R-S = (R-P) + (P-S) distingue il margine tra coppie da quello
ottenibile cambiando seed nella stessa coppia.

I riferimenti completi sono 30; gli altri 60 sono parziali per timeout/errori.
Parità significa differenza non superiore a 1e-12 sugli score a 10 decimali.
Tutti i 16.200 esiti originali dell'oracle sono verificati con SHA-256 e tutti
i massimi sono ricostruiti. Le 90 ricompilazioni seed 0 delle coppie scelte
riproducono esattamente gli score RAG originali.
L'unità è il circuito; le medie non pesano per numero di qubit.
La selezione dei dieci esempi è per scarto decrescente.
Il massimo di tre seed è un confronto favorevole all'oracle: non è una stima
della prestazione media. Le parità sui riferimenti parziali non dimostrano
ottimalità assoluta.

## Riprodurre

Dalla radice del progetto in WSL, per una nuova analisi senza sovrascrivere questa:

    .venv/bin/python archivio/valutazione/oracle_test/confronto_llm_rag_k5/analizza.py --output archivio/valutazione/oracle_test/confronto_llm_rag_k5/ricalcolo
    .venv/bin/python archivio/valutazione/oracle_test/confronto_llm_rag_k5/impagina.py --directory archivio/valutazione/oracle_test/confronto_llm_rag_k5/ricalcolo

Il testo interpretativo è specifico della campagna citata: per una nuova
campagna va aggiornato insieme ai risultati, non riutilizzato alla cieca.
Gli script usano solo la libreria standard di Python.
Per ricompilare e verificare il report presente, senza rigenerare il LaTeX:

    .venv/bin/python archivio/valutazione/oracle_test/confronto_llm_rag_k5/compila_verifica.py

Sono richiesti pdflatex, TikZ e Poppler, già presenti in WSL. Il compilatore
integrato nell'editor ha restituito "Unable to find standard directories for
platform"; il PDF è stato compilato con pdflatex in WSL, senza installazioni.
Per modificare il testo in modo permanente, cambiare impagina.py e rigenerare.
Per modifiche dirette al documento, cambiare il .tex e lanciare solo la compilazione.

## Risultato

55/90 score uguali al massimo conosciuto, 35/90 inferiori.
Score medio RAG 0,79837881407; oracle 0,8002222903788889.
Scarto medio 0,0018434763088888888: circa 0,1843 punti percentuali.
Tra i 55 pareggi, 9 hanno oracle completo e 46 parziale.
Nessuna nuova compilazione quantistica, nessuna modifica alle fonti.
Il grafo graphify non è stato aggiornato.

# Confronto Manhattan, WL e WL con sintesi

Il report confronta gli stessi 90 circuiti Test, con cinque esempi per richiesta.
La profondità WL è h=24, scelta sugli 88 circuiti di validation prima delle due nuove prove.
I dati sperimentali originali e gli altri report restano nelle rispettive cartelle.

## Contenuti

- confronto_manhattan_wl.tex e confronto_manhattan_wl.pdf: documento autonomo, diagrammi e grafici vettoriali incorporati.
- genera_report.py: ricostruisce le misure e controlla i registri originali.
- impaginazione.py: produce il LaTeX dai dati, con testo e figure.
- dati.json: misure, riepiloghi, confronti appaiati, esempio reale e validation.
- tabelle/circuiti.csv: tutti i 270 esiti, con tempi, token, scelte e fatti.
- provenienza.json: hash delle fonti e controlli.
- verifica_report.py e verifica_report.json: verifica finale delle fonti, dell'invio della sintesi e dei diagrammi didattici.
- controllo_visivo/: immagini delle pagine per il controllo dell'impaginazione.

## Ricompilare dopo una modifica al LaTeX

Dalla radice del progetto, in WSL:

    cd archivio/valutazione/test/confronto_manhattan_wl
    pdflatex -interaction=nonstopmode -halt-on-error confronto_manhattan_wl.tex
    pdflatex -interaction=nonstopmode -halt-on-error confronto_manhattan_wl.tex

Le due compilazioni risolvono i riferimenti bibliografici. Non occorrono immagini esterne.
Il compilatore integrato nell'app ha restituito un errore di piattaforma
("Unable to find standard directories for platform"); il PDF è stato compilato con
il pdflatex già presente in WSL, senza installazioni.

## Rigenerare testo e grafici dai dati

Dalla radice del progetto:

    .venv/bin/python archivio/valutazione/test/confronto_manhattan_wl/impaginazione.py

Questo comando riscrive il LaTeX: le modifiche permanenti al testo vanno quindi fatte
in impaginazione.py. Per rileggere i registri senza sovrascrivere questa analisi:

    .venv/bin/python archivio/valutazione/test/confronto_manhattan_wl/genera_report.py --output archivio/valutazione/test/confronto_manhattan_wl/ricalcolo
    .venv/bin/python archivio/valutazione/test/confronto_manhattan_wl/impaginazione.py --directory archivio/valutazione/test/confronto_manhattan_wl/ricalcolo

Il generatore rifiuta una cartella che contenga già dati.json.

## Fonti e metodo

Manhattan: test/risultati/llm_rag.
WL: test/dag_wl_retrieval/risultati/llm_rag_dag_wl.
WL con sintesi: test/dag_wl_sintesi/risultati/llm_rag_dag_wl_sintesi.
Validation: valutazione/validation_dag_wl/esecuzioni/wl_v3.
Scelta congelata: valutazione/validation_dag_wl/selezioni/wl_v3/wl_h24.json.

Sono controllati tutti i 90 circuiti e tutti i 504 tentativi LLM, inclusi quelli corretti.
Nessuna esclusione, imputazione, nuova inferenza o compilazione quantistica.
Le medie dello score hanno denominatore 90; i fatti dichiarati sono 180 per sistema.
Parità appaiata: valore assoluto della differenza non superiore a 1e-12.
Le fasce di qubit (fino a 5, 6-16, oltre 16) riprendono il report precedente.
La tabella dei casi più diversi mostra i primi 12 per escursione fra i tre score;
le appendici e il CSV comprendono tutti i 90 casi.

I token e i tempi LLM sommano tutte le chiamate. Il primo ingresso è separato.
I tempi dell'indice WL per sessione sono fuori dal totale dei singoli circuiti.
Il picco WL di circa 297 secondi è mantenuto nella media: la durata complessiva
è registrata, ma le singole fasi non ne spiegano tutto il valore.
Il confronto dei tempi non isola la velocità dei metodi di similarità.

La progettazione segue Test precedenti già esaminati: confronto descrittivo,
non nuova conferma su circuiti mai osservati. Memoria non raccolta.
Fatti strutturati verificati automaticamente; ipotesi libere non verificate.
Il grafo graphify non è stato aggiornato.

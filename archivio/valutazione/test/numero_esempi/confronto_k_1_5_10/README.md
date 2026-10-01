# Confronto RAG con 1, 5 e 10 esempi

`confronto_k.pdf` è il report compilato di 17 pagine.
`confronto_k.tex` è il sorgente LaTeX autonomo, con grafici vettoriali PGFPlots.
Il documento confronta gli stessi 90 circuiti nei tre sistemi. Include:

- riuscita, score medio e mediano, soglia 0,8;
- confronti appaiati e tutti i nove circuiti con score diverso;
- tabelle per fasce di qubit;
- token, tempi, correzioni e validità dei fatti;
- grafici per circuito con scale comuni e distribuzioni cumulative;
- appendici con score, tempi, token, correzioni e fatti per tutti i casi;
- conclusioni e limiti delle esecuzioni osservate.

Il risultato principale è una qualità quasi invariata, con costi crescenti.
In 81/90 circuiti lo score è identico nelle tre prove.
I token complessivi sono 888.083, 1.480.707 e 2.511.611.
Il tempo totale medio è 21,00, 27,49 e 37,98 secondi.
Le medie non sono una prova di equivalenza né una garanzia su altri circuiti.

## Modificare e compilare

Dalla radice del repository:

```bash
cd archivio/valutazione/test/numero_esempi/confronto_k_1_5_10
pdflatex -interaction=nonstopmode -halt-on-error confronto_k.tex
pdflatex -interaction=nonstopmode -halt-on-error confronto_k.tex
```

Per modifiche testuali, lavorare direttamente sul sorgente LaTeX.
Non rieseguire l'impaginazione dopo modifiche manuali senza conservarne una copia:
il generatore riscrive il sorgente dai dati.

Il sorgente è stato aperto nell'editor integrato. Il compilatore integrato
non trova le directory standard dell'ambiente; il PDF consegnato è stato
compilato con pdflatex in WSL e controllato visivamente.
Non sono necessarie immagini esterne o file LaTeX aggiuntivi.

## Riprodurre l'analisi in una cartella nuova

Dalla radice del repository, scegliere una cartella non ancora usata:

```bash
.venv/bin/python archivio/valutazione/test/numero_esempi/confronto_k_1_5_10/genera_report.py --output /tmp/confronto_k_riprodotto
.venv/bin/python archivio/valutazione/test/numero_esempi/confronto_k_1_5_10/impaginazione.py --directory /tmp/confronto_k_riprodotto
cd /tmp/confronto_k_riprodotto
pdflatex -interaction=nonstopmode -halt-on-error confronto_k.tex
pdflatex -interaction=nonstopmode -halt-on-error confronto_k.tex
```

Il raccoglitore rifiuta di sovrascrivere un `dati.json` esistente.
Non avvia inferenze né compilazioni quantistiche. Rilegge i registri e verifica:

- corrispondenza dei 90 circuiti e delle loro impronte;
- contratti, modello e parametri effettivi delle chiamate;
- uguaglianza della vista del circuito, a parte gli esempi;
- recuperi annidati: il primo di k=1 e i primi cinque di k=5 coincidono con k=10;
- corrispondenza di ogni esempio con il Dataset train;
- token e tempi delle chiamate fisiche;
- regole dei fatti su tutte le 389 risposte complete;
- decisione finale e score conservato dopo la compilazione.

`dati.json` conserva esiti, aggregazioni, metadati e controlli.
`provenienza.json` contiene le impronte delle fonti.
`tabelle/circuiti.csv` contiene 270 righe con valori completi.
`verifica_finale.json` conserva i controlli del PDF e le impronte degli artefatti.
`controllo_visivo/` raccoglie testo estratto e anteprime delle pagine.

## Limiti e provenienza

k=5 riusa la prova del 21 settembre; k=1 e k=10 sono estensioni del
28 settembre decise dopo la lettura del Test. Non sono nuovi dati mai osservati.
Il contratto a dieci esempi ammette E6-E10; le regole sui fatti restano le stesse.
Le ipotesi libere non sono verificate. Tempi, cache e stato del computer non
sono replicati in condizioni controllate. Non si stimano energia o memoria.

Per qualità e distribuzioni tutti i denominatori coincidono: 90 successi.
I confronti appaiati usano tolleranza assoluta 1e-12; non sono test statistici.
Le fasce di qubit sono <=5, 6-16 e >16, come nel confronto di riferimento.
Il report non modifica i risultati o il documento precedente dei cinque sistemi.
Il grafo non è stato aggiornato.

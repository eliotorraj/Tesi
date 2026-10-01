# Confronto tra LLM + RAG e MQT Predictor su QASMBench

Questa cartella contiene il documento LaTeX e il PDF dell'ulteriore test indipendente sui 50 circuiti QASMBench. Riprende le misure pertinenti del precedente confronto dei cinque sistemi: riuscita, score, soglia 0,8, tempi, token e correzioni.

Il report usa soltanto i risultati QASMBench del 30 settembre 2026. Non contiene nuove esecuzioni dei sistemi.

## Documenti e dati

- `confronto_qasmbench.pdf`: documento compilato, 12 pagine, con 6 figure e tabelle. Alcune figure hanno due pannelli.
- `confronto_qasmbench.tex`: sorgente autonomo, con dati e grafici vettoriali incorporati.
- `dati/circuiti.csv`: 100 esiti, comprese le due interruzioni per timeout.
- `dati/coppie.csv`: i 48 circuiti con uno score per entrambi i sistemi.
- `dati/riepilogo.json`: statistiche, denominatori, intervalli, configurazioni e impronte di provenienza.
- `artefatti.json`: impronte dei generatori, del LaTeX e del PDF.
- `anteprime/`: immagini delle pagine per il controllo dell'impaginazione.
- `compilazione_1.txt`, `compilazione_2.txt`, `verifica_pdf.txt`: log e caratteristiche del PDF.
- `verifica_testo.txt`: testo estratto dal PDF per controlli.

## Risultato principale

LLM + RAG completa 50 circuiti; MQT Predictor ne completa 48 e va in timeout su `gcm_n13` e `qft_n63`.
Sui 48 successi comuni, lo score medio è 0,8839 per LLM + RAG e 0,9168 per MQT.
LLM ottiene lo score maggiore in 22 casi, MQT in 26.
La compilazione interna LLM è più rapida, ma il tempo della decisione porta il totale medio a 26,76 s contro 17,94 s sulle stesse 48 coppie.

I timeout non ricevono score zero. Le medie su tutti i successi hanno denominatori diversi e sono separate dal confronto appaiato.
Le durate comprendenti i timeout sono tempi osservati fino all'arresto; non stimano il tempo necessario a terminare senza limite.

Il selettore MQT è quello scelto per questa campagna: 384 campioni dei 396 previsti, 12 esclusi.
La raccolta del Training set ha 1853 compilazioni riuscite su 1878, con limiti adattivi 100/300 secondi.
La campagna è documentata come ulteriore test indipendente.

## Rigenerare il documento

Dalla radice del progetto:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/report/confronto_llm_rag_mqt/genera_report.py
.venv/bin/python archivio/valutazione/test_qasmbench/report/confronto_llm_rag_mqt/compila.py
```

Il testo del generatore è stato allineato il 30 settembre 2026 alla versione ridotta del LaTeX modificata dall’utente. La rigenerazione dai registri produce le stesse 445 righe, identiche byte per byte. L’esito e le impronte della verifica sono in `verifica_rigenerazione.json`.
Le statistiche complete restano nei dati JSON e CSV, anche quando non compaiono nel documento.

Il primo comando usa la libreria standard Python e la procedura di analisi della campagna.
Verifica gli identificativi, i contratti, i 50 originali, i 100 esiti, i contatori LLM e gli intervalli già conservati.
Le copie di lavoro dei circuiti possono avere i fine riga normalizzati da CRLF a LF; viene controllata l'identità del testo oltre all'impronta degli originali.

Il secondo comando richiede `pdflatex`, i pacchetti LaTeX dichiarati nel sorgente e gli strumenti Poppler `pdfinfo`, `pdftotext` e `pdftoppm`.
Pillow è facoltativo e serve soltanto alla tavola di contatto delle anteprime.
I due passaggi LaTeX completano riferimenti e numerazione delle pagine.
La compilazione è stata verificata anche tramite log, testo estratto e immagini delle pagine.

La rigenerazione aggiorna i soli file derivati di questa cartella, non i registri originali.
Prompt, risposte, evidenze RAG e tutti i tentativi restano sotto `../../risultati/`.
Non vengono avviati LLM, nuove compilazioni quantistiche, addestramenti o modifiche al Dataset.

## Metodo dell'analisi

L'unità è il circuito. La qualità è confrontata soltanto sui successi comuni.
Le fasce sono quelle del manifest: 30 piccoli, 15 medi, 5 grandi.
Il ricampionamento appaiato usa 10.000 estrazioni con reinserimento e seed 20260901.
I limiti dell'intervallo sono gli elementi agli indici `int(0.025 * (10000 - 1))` e `int(0.975 * (10000 - 1))` delle medie ordinate, come in `../../analizza.py`.
Gli intervalli sono descrittivi: la selezione non è casuale e non permette una prova di superiorità sull'intera raccolta.
La soglia 0,8 riprende il report precedente; gli score sono fedeltà stimate su Target sintetici.

Il report non presenta misure su hardware quantistico, un riferimento ottimo o memoria di picco.
Il tempo di compilazione interno è già incluso nel tempo del processo; recupero RAG e risposte sono già inclusi nel tempo di scelta.
I token in ingresso contano l'intero contesto a ogni chiamata, compreso quello riutilizzato dalla cache.
I 13 esiti con fatti non completamente verificati sono distinti dai successi tecnici della compilazione.

## Compilatore

Il compilatore integrato nell'app non ha potuto avviarsi per un errore dell'ambiente (`Unable to find standard directories for platform`).
Il PDF consegnato è stato prodotto con pdfLaTeX installato in WSL. Il sorgente resta disponibile nell'editor.

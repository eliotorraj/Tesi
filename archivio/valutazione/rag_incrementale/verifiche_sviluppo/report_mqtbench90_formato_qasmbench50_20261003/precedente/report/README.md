# Report della memoria incrementale

`genera.py` legge solo gli esiti conclusi e verificati delle quattro campagne.
Non chiama LLM, non compila circuiti e non alimenta la memoria.

Ogni generazione crea una cartella nuova con:
- `dati.json`: misure complete, limiti e provenienza.
- `circuiti.csv`: un record per posizione effettivamente conclusa.
- `riepilogo.csv`: confronto riassuntivo degli ordinamenti.
- `rapporto.tex` e, con `--pdf`, `rapporto.pdf`.
- `grafici/`: grafici autonomi in LaTeX e PDF.
- `provenienza.json`: impronte degli ingressi, del generatore e dei file prodotti.

I grafici principali mostrano la differenza media cumulativa rispetto al
controllo storico e la crescita della memoria. I dettagli su uso degli esempi,
fatti, tempi, token e riferimento oracle restano nei dati.
I report parziali dichiarano quanti circuiti sono conclusi.

L'analisi ricontrolla i registri e il controllo storico. Non richiede che il codice
di avvio sia ancora identico alla revisione congelata, che resta identificata nel
contratto. L'avvio e la ripresa richiedono invece le stesse impronte.

Per comandi e condizioni leggere il [README principale](../README.md).

# Verifiche della preparazione

`verifiche.json` riassume i controlli e le impronte degli script; `controllo_preliminare.json` conserva il risultato di `avvia.sh --verifica`.

I 14 test del motore e gli 8 del confronto sono riusciti. Le prove hanno usato dati e compilazioni simulati. Il controllo di integrazione legge i 50 registri RAG storici e li confronta soltanto con esiti oracle fittizi conservati in una cartella temporanea.

L'anteprima LaTeX fittizia è stata compilata con pdflatex e controllata su tutte le sette pagine. È contrassegnata su ogni pagina e non rappresenta risultati sperimentali. I file grafici di collaudo restano locali, esclusi da Git.

Il compilatore integrato non si è inizializzato; è stato usato quello già installato in WSL. Non è stato installato software. Nessuna generazione oracle reale è stata avviata e il grafo non è stato aggiornato.

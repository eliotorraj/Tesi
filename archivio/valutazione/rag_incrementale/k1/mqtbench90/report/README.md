# Report k=1: 90 circuiti

Il generatore legge i registri della nuova campagna mqtbench90, verifica i
passaggi conclusi e confronta il RAG fisso k=1 con i quattro ordinamenti k=1.
Non usa gli score k=5 come controllo. Per avviarlo seguire il
[README principale](../../README.md).

Il PDF è sintetico: breve descrizione dei sistemi e del campione, grafico
dello scarto medio dall'oracle, dettagli per circuito e conclusioni. La croce
rossa grande indica RAG fisso; punto blu e cerchio arancione mostrano RAG
incrementale e oracle. La scala di R-S è comune ai quattro ordinamenti.
Tempi, token, memoria e confronti fra coppie restano nei dati e nelle figure
autonome. Le conclusioni distinguono misure e ipotesi e valgono per il campione.

Le medie fra tutti i sistemi usano i successi comuni. Ogni confronto fra due
ordinamenti dichiara invece la propria intersezione. Fallimenti, dati mancanti,
score zero e oracle parziali rimangono distinti.

Il riferimento predefinito è:
`archivio/valutazione/oracle_test/confronto_llm_rag_k5/risultati/dati.json`.

I vecchi file di confronto sono verificati per ricostruire il riferimento
oracle. Nel confronto k=1 vengono utilizzati soltanto massimi, copertura e
identità dei circuiti; gli score del vecchio LLM non vengono trasferiti.

Ogni versione in `risultati/<experiment_id>/` contiene `rapporto.tex`,
`dati.json`, `provenienza.json`, tabelle CSV e la cartella `grafici/`.
La tabella `rag_fisso.csv` conserva gli esiti del nuovo controllo.
Con `--pdf` vengono compilati il documento e i grafici autonomi.
Sono supportati report parziali e `--senza-oracle`.

# LLM con cinque esempi casuali

Questa è una nuova variante esplorativa. Il modello sceglie dispositivo e
configurazione dopo aver ricevuto cinque esempi train estratti a caso.
Non coincide con `casuale.py`, che estrae direttamente la coppia senza LLM.

## Che cosa cambia

Si usa lo stesso Dataset di 396 circuiti train distinti. Restano gli stessi
filtri del RAG: esperimento, train, obiettivo e dispositivo selezionato
nell'esempio compatibile con la richiesta corrente. Dai candidati ordinati
per `rag_id` si estraggono cinque record uniformemente, senza reinserimento.
Non si calcolano distanze Manhattan e non si consulta l'indice Qdrant.

Il seme predefinito è 20260927. Il seme per circuito deriva dal seme scelto e
dall'impronta del testo QASM UTF-8. L'ordine di estrazione determina E1...E5.
I tentativi di correzione usano gli stessi esempi. Meno di cinque candidati
causano un errore, senza ricorrere a validation o test.

Modello Qwen, precisione, temperatura 0, prompt facts v4, contesto, catalogo,
timeout, massimo tre risposte e compilazione Qiskit con seme 0 restano quelli
dell'avvio originale. Il solo punto aggiunto al valutatore comune è il
parametro facoltativo `prepare_fn`; gli avvii esistenti usano il comportamento
precedente.

Il registro comune delle evidenze richiede una distanza numerica. Contiene
0.0 come **segnaposto tecnico**, dichiarato nella politica, mai usato per
ordinare. La vista inviata all'LLM omette le distanze. In `retrieval.json`
le distanze sono `null`: non sono state misurate.

## Comandi dalla radice della repository

Controlli senza inferenza e senza eseguire i circuiti Test:

```bash
.venv/bin/python archivio/valutazione/test/llm_recupero_random.py --verifica
```

Prova su Bell sintetico, con server locale già avviato e GGUF ufficiale:

```bash
.venv/bin/python archivio/valutazione/test/llm_recupero_random.py --tecnico \
  --model-path /percorso/al/modello.gguf --url http://127.0.0.1:8089
```

Avvio futuro dei 90 casi; non eseguito durante lo sviluppo di questa variante:

```bash
.venv/bin/python archivio/valutazione/test/llm_recupero_random.py --esegui \
  --model-path /percorso/al/modello.gguf --url http://127.0.0.1:8089 --seed 20260927
```

Il percorso GGUF va sostituito con quello reale. Server e impronta dei pesi
vengono controllati come negli altri avvii. Non servono i modelli MQT.

## Registri e ripresa

Ogni seme ha una cartella `seed_<n>/`. I controlli sono in `preparazione/`;
le prove Bell in `prove_tecniche/`; i casi Test in
`risultati/llm_recupero_random/`. Il contratto è locale alla nuova esecuzione.
Quello originale del Test non viene riscritto.

Si conservano politica e seme, versione Python, impronte di codice e dati,
configurazione selezionata, candidati e record estratti, prompt, alias,
risposte, tutti i tentativi, errori, tempi, token e score. La memoria non è
misurata ed è dichiarata mancante. I file originali dei tentativi non sono
sovrascritti. Un caso interrotto resta tale; non viene rieseguito in modo
silenzioso. Un errore di trasporto ferma i casi successivi.

La ripresa con codice, dati, ambiente o seme incompatibili viene rifiutata.
I riepiloghi JSON in `analisi/` dichiarano denominatori e dati mancanti.
Il report comparativo storico a quattro metodi non include automaticamente
questa variante: va creata una nuova analisi dopo la raccolta.

Il Test è già stato osservato. Questa aggiunta è un'estensione esplorativa,
non una conferma su dati mai visti. Più semi vanno stabiliti prima e riportati
tutti. Non si deve scegliere a posteriori il seme con il risultato migliore.

## Verifiche di sviluppo

```bash
.venv/bin/python -m unittest discover \
  -s archivio/valutazione/test/verifiche -p test_recupero_random.py -v
```

Le prove usano il train, Bell e dati sintetici. Controllano riproducibilità,
assenza di duplicati e distanze, filtri, alias, validatore, registri e
rifiuto di riprese incompatibili. Non misurano la qualità della variante.

## Report della campagna con seme 20260927

Il [report indipendente](../report_generati/09ccc501601d9f34/sistemi/llm_recupero_random/latex/verifica.pdf)
descrive i 90 esiti del riepilogo 8306d9dedffd4f3faa69ed74ef058baa.
Contiene sei grafici e le tabelle di score, tempi, token e correzioni.
Sono conservati sorgenti LaTeX, CSV, generatore e provenienza nella stessa
cartella della versione. Il confronto originale resta separato.

La compilazione è riuscita in 90 casi su 90. Lo score medio è 0,7518119794.
Sono registrate 112 correzioni e 55 esiti accettati con fatti non verificati.
La prova usa un solo seme ed è un'estensione esplorativa del Test.

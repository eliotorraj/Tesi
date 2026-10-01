# Quanto conta il numero di esempi RAG

Questa estensione confronta il RAG classico con **1 oppure 10 esempi train**.
Serve a misurare qualità della scelta, validità dei fatti, token e tempi.
La prova classica a 5 esempi resta il riferimento.

Gli avvii sono separati:

| Avvio nella cartella Test | Metodo nei registri | Campagna |
| --- | --- | --- |
| `llm_rag_1_esempio.py` | `llm_rag_k1` | `numero_esempi/k_1/` |
| `llm_rag_10_esempi.py` | `llm_rag_k10` | `numero_esempi/k_10/` |

Sono estensioni decise dopo la lettura dei risultati sui 90 circuiti Test.
Non costituiscono una nuova conferma su dati mai osservati. Non selezionano
nuovi parametri sulla validation e non sostituiscono il contratto ufficiale.

## Che cosa cambia

Cambia il numero di esempi. Restano gli stessi 396 record train verificati,
le 49 caratteristiche, la trasformazione ricavata dal train e la ricerca
esatta con distanza Manhattan. Restano i filtri di esperimento, obiettivo e
dispositivo compatibile. Le parità seguono distanza e identificativo del record.
Non si campiona a caso e non si leggono gli score del circuito da decidere.

Modello, temperatura, semi, configurazioni, budget di risposta, tre tentativi
e compilazione finale sono quelli del Test classico. Il profilo desktop
mantiene 60.000 token di contesto e 4.096 token massimi di risposta.
L'output contiene ancora uno o due fatti, non dieci.

Per dieci esempi è necessario permettere anche i riferimenti E6-E10.
La nuova variante estende soltanto quel limite dello schema e la nota che
descrive le colonne degli esempi. Le regole di verifica dei fatti non cambiano.
La revisione `facts-v4-k10-toon3-20260928` e l'impronta dello schema sono
conservate in `encoding.json`. Il percorso a un esempio mantiene lo schema
classico E1-E5; i riferimenti a esempi assenti sono comunque non validi.

Il comportamento predefinito del prototipo e degli avvii precedenti resta
a cinque esempi. La copia dei sorgenti precedenti e la verifica del prompt
classico sono in `verifiche_sviluppo/`.

## Comandi

Dalla radice del repository, controlli senza server, inferenza o compilazione:

```bash
.venv/bin/python archivio/valutazione/test/llm_rag_1_esempio.py --verifica
.venv/bin/python archivio/valutazione/test/llm_rag_10_esempi.py --verifica
```

Per una prova sul solo Bell sintetico, usare `--tecnico` con gli stessi
parametri del server. Per avviare i 90 casi:

```bash
.venv/bin/python archivio/valutazione/test/llm_rag_1_esempio.py --esegui \
  --model-path /mnt/d/Tesi-mqt/llm-selection/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/models/qwen/Q8_0.gguf \
  --url http://127.0.0.1:8089

.venv/bin/python archivio/valutazione/test/llm_rag_10_esempi.py --esegui \
  --model-path /mnt/d/Tesi-mqt/llm-selection/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/models/qwen/Q8_0.gguf \
  --url http://127.0.0.1:8089
```

Il server va avviato come per gli altri Test; il percorso deve indicare il
GGUF effettivamente caricato. In WSL si usa lo stesso collegamento a Windows
tramite curl.exe del prototipo. Per confrontare i tempi, eseguire le campagne
una alla volta sullo stesso hardware e con lo stesso profilo del server.

Non si riduce il numero di esempi se la richiesta supera il contesto.
Il programma registra il problema e non avvia la generazione di quel caso.
Se mancano esempi compatibili, il caso fallisce prima dell'inferenza.
Non si ripiega su validation, test o esempi duplicati.

## Dati conservati e ripresa

Ogni campagna contiene controlli in `preparazione/`, prove Bell in
`prove_tecniche/` e risultati in `risultati/llm_rag_k1/` oppure
`risultati/llm_rag_k10/`. Contratto, sessioni e risultati sono indipendenti.

Dentro ogni circuito vengono salvati prompt, esempi con alias e distanza,
codifica, richieste e risposte di ogni tentativo, token, tempi, validazioni,
decisione finale, compilazione e score. `retrieval.json` dichiara quanti
esempi sono richiesti e quanti restituiti.

Il riepilogo in `analisi/<id>.json` riporta:

- successi, fallimenti, cause, score medio e relativo denominatore;
- token in ingresso, in uscita e totali; completezza delle misure;
- tempo del recupero, della scelta, delle risposte LLM e della compilazione;
- chiamate, correzioni e fatti validi nelle decisioni finali disponibili.

I token e i tempi LLM comprendono tutti i tentativi di generazione.
L'ingresso comprende anche i token riutilizzati dalla cache. Il tempo RAG
include caricamento e controlli del Dataset e dell'indice; non è il solo
tempo di ricerca. Il tempo della scelta comprende preparazione, tokenizzazione,
correzioni e verifiche. Le misure mancanti restano distinte dagli zeri.
La memoria non è misurata. Le ipotesi non sono verificate semanticamente.

Rilanciare lo stesso comando riprende solo i casi non ancora iniziati.
Successi, errori e interruzioni già registrati non vengono sovrascritti o
ripetuti. Una modifica a codice, dati, piano o numero di esempi impedisce
di mescolare la ripresa con l'esecuzione precedente.
I contratti storici non vengono riscritti per aggirare questa verifica.

## Verifiche di sviluppo

```bash
.venv/bin/python -m unittest discover \
  -s archivio/valutazione/test/verifiche -p test_numero_esempi.py -v
```

Le verifiche usano Bell, il Dataset train e risposte simulate. Controllano
ordine Manhattan, alias E10, andata e ritorno TOON, correzioni, token,
limite del contesto, isolamento dei risultati e rifiuto delle riprese
incompatibili. Non chiamano Qwen e non eseguono circuiti Test reali.

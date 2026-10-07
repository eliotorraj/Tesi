# Confronto fra RAG fisso e incrementale con k=1

Questa cartella contiene un nuovo test con **un solo esempio recuperato per ogni
decisione**, sia per il RAG fisso sia per le quattro varianti incrementali.
I 90 circuiti MQT Bench e i 50 QASMBench hanno campagne e report separati.

Il RAG fisso viene eseguito di nuovo con k=1. I suoi risultati servono come
controllo per le quattro varianti. Gli score dei precedenti test k=5 non vengono
riutilizzati nel confronto. Il Dataset originale, il prototipo, il kit di
riproducibilità e le campagne precedenti restano invariati.

## I cinque sistemi

| Identificativo | Procedura |
| --- | --- |
| `00_rag_fisso` | Dataset train fisso; circuiti nell'ordine del manifest. |
| `01_manifest` | Memoria incrementale; ordine del manifest. |
| `02_inverso` | Memoria incrementale; ordine inverso. |
| `03_casuale_20261002` | Memoria incrementale; permutazione con seed 20261002. |
| `04_casuale_20261003` | Memoria incrementale; permutazione con seed 20261003. |

Tutti partono dai 396 esempi train. Ciascuna variante ha una memoria separata,
inizialmente vuota. MQT Bench e QASMBench non si scambiano osservazioni.
Una compilazione riuscita entra nella memoria solo dopo la conclusione del
circuito. Il RAG fisso non aggiunge osservazioni.

Il recupero usa la stessa distanza Manhattan e la stessa trasformazione
calcolata sul train. Cerca un solo vicino nel Dataset disponibile, senza quote
riservate alla memoria nuova. Il circuito corrente è escluso per impronta del
QASM. Il prompt e la verifica dei fatti accettano soltanto il riferimento
`E1`. Le nuove osservazioni sono descritte come singole compilazioni,
senza attribuire loro un'ottimalità non misurata.

## Avviare i due test

I comandi partono dalla radice della repository, in WSL/Linux.
Serve l'ambiente Python 3.12 già utilizzato e il server locale
Qwen3.5-4B Q8_0, con contesto 60000 e porta 8089.
Sostituire il percorso GGUF con quello del modello effettivamente servito.
Lo script verifica contenuto del modello, server, ingressi e dipendenze.

**MQT Bench, 90 circuiti:**

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/avvia_mqtbench90.py \
  --esegui --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

**QASMBench, 50 circuiti:**

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/avvia_qasmbench50.py \
  --esegui --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

Ogni comando esegue prima il RAG fisso e poi i quattro ordinamenti, in sequenza.
Sono previste 450 decisioni per MQT Bench e 250 per QASMBench. Per ogni decisione
sono consentiti fino a tre tentativi LLM e al massimo una compilazione Qiskit,
con seed zero e limite di 100 secondi. Un blocco comune impedisce di avviare
contemporaneamente i due test k=1.

Per un server Windows raggiunto da WSL si può aggiungere `--transport windows`;
per un server Linux, `--transport native`. Il valore predefinito è `auto`.
`--url` permette di indicare un'altra porta locale.

Opzioni comuni ai due comandi:

- `--verifica`: controlla gli ingressi senza chiamare il server.
- `--prepara`: crea i registri vuoti e congela le impostazioni, senza inferenza.
- `--sistema 01_manifest`: seleziona soltanto quel sistema. Vale anche per gli altri identificativi della tabella.
- `--experiment-id NOME`: crea o riprende una campagna con un altro nome.

Le tre modalità `--esegui`, `--verifica` e `--prepara` sono alternative.
Non serve eseguire la preparazione prima di `--esegui`.

## Generare i report

Dopo le prove:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/report_mqtbench90.py --pdf
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/report_qasmbench50.py --pdf
```

I report mantengono forma e grafici dei precedenti: score e scarti dall'oracle
per circuito, confronto dei cinque sistemi sui successi comuni, confronti fra
le sei coppie di ordinamenti, andamento cumulativo, memoria, tempi e token.
I dati riguardano soltanto il nuovo test k=1.

Ogni generazione salva una nuova versione, con JSON, CSV, sorgenti LaTeX,
grafici autonomi e PDF. `--pdf` richiede pdfLaTeX già installato; senza
questa opzione si producono comunque dati, tabelle e sorgenti dei grafici.
Il PDF non viene generato automaticamente alla fine delle campagne.

I riferimenti oracle esistenti vengono verificati e usati solo per il report.
Il massimo osservato non dipende da k. Gli score LLM k=5 presenti nei file
storici sono esclusi dal confronto. `--oracle /percorso/dati.json` permette di
indicare un'altra copia verificabile; `--senza-oracle` produce un documento
che dichiara l'assenza del riferimento. Un report parziale distingue risultati
mancanti e fallimenti dagli score zero.

Se è stato scelto un altro `--experiment-id`, passarlo anche al report.

## Dove vengono salvati i risultati

| Test | Identificativo predefinito | Cartella |
| --- | --- | --- |
| MQT Bench | `mqtbench90_rag_k1_v1` | [mqtbench90/](mqtbench90/README.md) |
| QASMBench | `qasmbench50_rag_k1_v1` | [qasmbench50/](qasmbench50/README.md) |

In ciascuna cartella, il controllo va in `rag_fisso/campagne/<experiment_id>/`
e ogni variante in `ordinamenti/<ordine>/campagne/<experiment_id>/`.
Le estensioni del Dataset sono nei rispettivi `memoria_incrementale/records/`;
l'esportazione `dataset.jsonl` viene prodotta a campagna conclusa.
I report vanno in `report/risultati/<experiment_id>/<versione>/`.

I registri conservano configurazione, impronte, recuperi, prompt, risposte,
controlli dei fatti, compilazioni, esiti, tempi, token e interruzioni.
Ripetere lo stesso comando riprende dal prefisso già concluso. Non ripete i
risultati pubblicati. Un tentativo iniziato ma senza esito finale resta
registrato come interrotto; la sequenza prosegue dal circuito successivo.
Non eliminare manualmente cartelle o registri per riprendere.

Una modifica a sorgenti, impostazioni o ingressi richiede un nuovo identificativo.
I salvataggi dei file conclusi sono sincronizzati prima di pubblicare il
passaggio che li collega alla memoria.

## Interpretazione e verifiche

È una nuova valutazione sequenziale su Test già esaminati. La condizione k=1
è richiesta per questo confronto e non viene presentata come una nuova scelta
ottenuta sulla validation. Restano fissi modello, metrica e regole dei precedenti
esperimenti; cambia il numero di esempi recuperati.

Il report esplicita denominatori, riferimenti oracle parziali e dipendenza fra
gli ordinamenti. Misura l'effetto delle osservazioni passate sulle decisioni
successive, senza usare risultati futuri per la stessa decisione.

Le [verifiche di sviluppo](verifiche_sviluppo/README.md) usano risposte e
compilazioni simulate. Non costituiscono risultati sperimentali.

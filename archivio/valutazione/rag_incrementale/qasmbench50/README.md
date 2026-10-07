# RAG incrementale sui 50 QASMBench

Questa campagna usa gli stessi cinquanta circuiti del Test QASMBench già svolto:
30 piccoli, 15 medi e 5 grandi. I cinquanta esiti LLM + RAG esistenti sono il
controllo storico. Le nuove decisioni non sono ancora state eseguite.

Tutto ciò che viene generato rimane in questa cartella. Il Dataset originale
resta in sola lettura. Ciascun ordinamento parte dai 396 esempi train e da una
memoria vuota, senza importare osservazioni da MQT Bench o dagli altri ordini.
Il codice è una copia autonoma della procedura incrementale, per mantenere
immutati gli avvii e i contratti MQT Bench già preparati.

## I quattro ordini

| Cartella | Sequenza |
| --- | --- |
| [01_manifest](ordinamenti/01_manifest/avvia.py) | Ordine del manifest QASMBench. |
| [02_inverso](ordinamenti/02_inverso/avvia.py) | Manifest al contrario. |
| [03_casuale_20261002](ordinamenti/03_casuale_20261002/avvia.py) | Permutazione con seed 20261002. |
| [04_casuale_20261003](ordinamenti/04_casuale_20261003/avvia.py) | Permutazione con seed 20261003. |

L'ordinamento riguarda l'arrivo dei circuiti. La regola del recupero è fissa:
cinque esempi, distanza Manhattan e normalizzazione ricavata dal train.

## Controllare e preparare

Dalla radice della repository, in WSL/Linux:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/esperimento.py --verifica
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/esperimento.py --prepara
```

La preparazione congela impostazioni, sorgenti, quattro sequenze e quattro memorie
vuote. L'identificativo predefinito è `qasmbench50_incrementale_v1`.
Non viene chiamato il server e non vengono compilati i circuiti QASMBench.

## Eseguire

Avviare il server Qwen3.5-4B Q8_0 con il profilo desktop, contesto 60000 e porta
locale 8089, secondo la guida del prototipo. Sostituire il percorso GGUF di esempio.

Per un ordine:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/ordinamenti/01_manifest/avvia.py \
  --esegui --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

Per tutti, in sequenza:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/esperimento.py \
  --esegui --tutti --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

Sono previste **200 nuove decisioni e fino a 200 compilazioni**, oltre alle
eventuali correzioni delle risposte. `--transport native` usa il server Linux;
`--transport windows` collega WSL al server Windows. Il valore predefinito è
automatico. `--url` cambia la porta locale.

Ripetere il comando riprende la sequenza senza ripetere successi, fallimenti,
timeout o tentativi interrotti dall'esito incerto. Un errore di trasporto ferma
la campagna. I registri restano conservati. Per cambiare codice, impostazioni
o ingressi serve un nuovo `--experiment-id`.

## Memoria e registri

Ogni ordine contiene `campagne/<experiment_id>/`:

- `contratto.json`: ingressi, sequenza, parametri e impronte.
- `memoria_incrementale/records/`: osservazioni ammesse dopo gli esiti.
- `memoria_incrementale/dataset.jsonl`: esportazione finale della memoria.
- `circuiti/`: prompt, recuperi, risposte, scelte, compilazioni ed esiti.
- `sessioni/` e `verifiche/`: avvii, arresti e controlli.

Una compilazione valida entra nella memoria anche se lo score è zero. Rimane
una singola osservazione, senza essere descritta come configurazione migliore.
Il risultato corrente può aiutare soltanto i circuiti successivi. L'oracle e
gli esiti storici non alimentano la memoria.

## Report con oracle

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/report/genera.py --pdf
```

Il riferimento predefinito è il confronto QASMBench già disponibile in
`~/oracoli_qasmbench_test/qasmbench50_max3_v1/analisi/20261001T200715_e284d5b5/confronto_llm_rag_k5/risultati/dati.json`.
Con `--oracle /percorso/dati.json` si può indicare un'altra analisi verificabile
della stessa campagna. La struttura e gli esiti originali devono essere
disponibili: il solo riepilogo non basta.

Il report ricalcola i massimi e controlla gli esiti oracle originali. Non li
rigenera e non avvia compilazioni quantistiche. Per produrre esplicitamente
un report senza oracle usare `--senza-oracle`; i riferimenti mancanti sono
segnalati, mai sostituiti con zero.

Ogni generazione crea una nuova cartella in
`report/risultati/<experiment_id>/<data_id>/`. Sono inclusi:

- grafici per tutti i 50 circuiti di ogni ordine, con score, oracle e scarto;
- confronto fra i quattro ordini e RAG fisso sui circuiti comuni;
- sei confronti a coppie, con denominatori espliciti;
- andamento cumulativo, crescita della memoria, token, tempi e fallimenti;
- CSV, JSON, LaTeX autonomo e PDF; dodici figure autonome in LaTeX e PDF.

Senza `--pdf` vengono prodotti dati, tabelle e sorgenti LaTeX. Con `--pdf`
si usa pdfLaTeX già installato. I report parziali dichiarano la copertura.
I dettagli sono nel [protocollo](protocollo.md) e nella [guida ai report](report/README.md).

## Verifiche

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/test_incrementale.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/test_report.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/test_report.py --verifica-oracle
.venv/bin/python -B archivio/valutazione/rag_incrementale/qasmbench50/verifica_report.py --pdf
```

I test della procedura simulano l'LLM e compilano solo un Bell tecnico. La
verifica oracle legge esiti reali già esistenti. L'ultimo comando produce
un'anteprima interamente sintetica, contrassegnata su ogni pagina e figura,
in `verifiche_sviluppo/temporanei/`. Non è un risultato sperimentale.

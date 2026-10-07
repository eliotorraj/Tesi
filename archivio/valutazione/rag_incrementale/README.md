# RAG con memoria incrementale

Il nuovo confronto con **k=1 per RAG fisso e quattro varianti incrementali**, separato per MQT Bench e QASMBench, è in [k1/](k1/README.md).

La campagna separata sui **50 QASMBench**, con grafici della distanza dall'oracle e confronto dei quattro ordini, è in [qasmbench50/](qasmbench50/README.md). Le istruzioni seguenti riguardano i 90 MQT Bench.

Questa prova verifica se le compilazioni concluse durante l'uso aiutano a scegliere
meglio sui circuiti successivi. Usa i 90 circuiti Test MQT Bench e confronta le
nuove scelte con i 90 esiti LLM + RAG già conservati.

La procedura è confinata in questa cartella di archivio. Non modifica
`prototipo/`, `riproducibilita/`, il Dataset originale o gli esiti storici.
Il framework del prototipo viene importato in sola lettura. Non occorrono modelli
MQT addestrati. Serve l'ambiente Python 3.12 completo già disponibile.

## I quattro ordinamenti

| Cartella | Ordine dei circuiti |
| --- | --- |
| [01_manifest](ordinamenti/01_manifest/avvia.py) | Ordine nel manifest originale. |
| [02_inverso](ordinamenti/02_inverso/avvia.py) | Ordine del manifest al contrario. |
| [03_casuale_20261002](ordinamenti/03_casuale_20261002/avvia.py) | Permutazione con seed 20261002. |
| [04_casuale_20261003](ordinamenti/04_casuale_20261003/avvia.py) | Permutazione con seed 20261003. |

Ciascun ordine riparte dai 396 esempi train e da una memoria vuota.
Le memorie non si scambiano esempi. Restano cinque esempi per richiesta,
la distanza Manhattan e la normalizzazione ricavata dal train.
L'ordinamento riguarda l'arrivo dei circuiti: la regola del recupero resta fissa.

## Controllare e preparare

I comandi seguenti partono dalla radice della repository, in WSL/Linux:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/esperimento.py --verifica
.venv/bin/python -B archivio/valutazione/rag_incrementale/esperimento.py --prepara
```

Il primo comando controlla sorgenti, esempi train, Target, dipendenze,
configurazione Qwen e presenza del controllo storico. Non chiama il server.
Il secondo congela i quattro ordini e crea le quattro memorie vuote.
L'identificativo predefinito è `mqtbench90_incrementale_v1`.

## Avviare le prove

Avviare prima il server Qwen con il profilo desktop già utilizzato:
Qwen3.5-4B Q8_0, contesto 60000, server locale sulla porta 8089.
Indicare il file GGUF effettivamente servito; nome, contenuto e contesto vengono
controllati. Il percorso sotto è un segnaposto da sostituire.

Per un solo ordine:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/ordinamenti/01_manifest/avvia.py \
  --esegui --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

Le altre tre cartelle hanno lo stesso comando `avvia.py`.
Per eseguire tutti gli ordini uno dopo l'altro:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/esperimento.py \
  --esegui --tutti --model-path /percorso/Qwen3.5-4B-Q8_0.gguf
```

Con server Linux si può specificare `--transport native`; per server Windows
da WSL `--transport windows`. Il valore predefinito mantiene la scelta automatica
del framework. `--url` consente un'altra porta locale.
Non avviare altri carichi pesanti durante le misure.

Si prevedono **360 nuove decisioni e fino a 360 compilazioni**, oltre alle
eventuali correzioni delle risposte. Gli esiti storici non alimentano la memoria:
servono soltanto al confronto. La preparazione non avvia queste prove.

## Dati prodotti e ripresa

Ogni ordine contiene `campagne/<experiment_id>/`:

- `contratto.json`: sequenza, impostazioni e impronte degli ingressi.
- `memoria_incrementale/records/`: una singola osservazione per nuovo circuito ammesso.
- `memoria_incrementale/dataset.jsonl`: esportazione della memoria a campagna completata.
- `circuiti/`: ingressi, recuperi, prompt, risposte, controlli dei fatti, compilazioni ed esiti.
- `sessioni/` e `verifiche/`: avvii, arresti e controlli.

Una compilazione riuscita con score valido entra nella memoria dopo il salvataggio
dell'esito. Il suo score può essere anche zero. Non diventa un'etichetta di
ottimalità e non viene presentato come mediana di più seed.
Il contenuto del QASM identifica i duplicati; non si certifica la diversità
semantica dei circuiti.

Ripetere lo stesso comando riprende la sequenza. Non ripete risultati conclusi
o tentativi già iniziati dall'esito incerto: questi ultimi restano interrotti.
I record non ancora collegati a un passaggio concluso non sono usati nel recupero.
Gli errori restano conservati e non diventano score zero.
Dopo un errore di trasporto la campagna si ferma; ripristinare il server e riprendere.

Una modifica a codice, impostazioni o dati impedisce la ripresa.
Per un'altra campagna usare un nuovo `--experiment-id`, conservando la precedente.
Non cancellare i registri per ottenere un altro esito.

## Report

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/report/genera.py \
  --experiment-id mqtbench90_incrementale_v1 --pdf \
  --oracle archivio/valutazione/oracle_test/confronto_llm_rag_k5/risultati/dati.json
```

`--oracle` è facoltativo e viene letto solo dall'analisi.
`--pdf` usa pdfLaTeX già installato; senza questo parametro genera comunque
LaTeX, tabelle e dati. Ogni avvio crea una nuova versione in
`report/risultati/<experiment_id>/`, senza sovrascrivere la precedente.
Sono disponibili anche report parziali; quelli senza esiti lo dichiarano.

Il report include confronto degli score sugli stessi circuiti, andamento
cumulativo, crescita e utilizzo della memoria, fallimenti, token e tempi con
denominatori. Conserva CSV completi, JSON, grafici autonomi, LaTeX e PDF.
I dettagli scientifici sono nel [protocollo della prova](protocollo.md).

## Verifiche di sviluppo

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/test_incrementale.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/verifica_report.py --pdf
```

I test usano risposte LLM simulate. Una verifica compila davvero un piccolo
circuito Bell; non misura la qualità sui Test. Il secondo comando genera
un'anteprima chiaramente etichettata con dati sintetici, separata dai risultati.
La descrizione e gli esiti dei controlli sono in
[verifiche_sviluppo](verifiche_sviluppo/README.md).

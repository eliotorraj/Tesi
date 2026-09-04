# Dataset Qiskit diretto — protocollo e struttura

## Nota sul protocollo 2.0

Questa cartella conserva il protocollo 1.0 e i risultati legacy. Il protocollo
2.0 non scrive qui. Usa invece:

    datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/

Le cache, i modelli, i checkpoint e i piani 2.0 sono sotto:

    artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/

Prima dell'apertura del test, i manifest 2.0 contengono soltanto train e
validation. Gli esempi RAG contengono sempre e soltanto train. La procedura
completa è descritta in
[docs/protocollo_sperimentale_v2.md](../../docs/protocollo_sperimentale_v2.md).

## 1. Spiegazione generale

Questa cartella contiene il Dataset sperimentale ottenuto compilando circuiti
direttamente con Qiskit. L'unità elementare dell'esperimento è:

```text
(circuito, dispositivo, configurazione Qiskit, seed)
```

La misura da massimizzare è
`mqt.predictor.reward.expected_fidelity`. Il valore è una stima offline basata
sul Target sintetico e deterministico di MQT Bench. Non deriva dall'esecuzione
del circuito su hardware quantistico reale.

Il Dataset ha due dimensioni:

- `pilot` usa dieci circuiti e serve a verificare il protocollo, i tempi e i
  casi di errore;
- `full` usa seicento circuiti e rappresenta l'esperimento completo da
  popolare dopo aver fissato il protocollo.

Il campione pilota contiene risultati separati per cinque dispositivi e una
vista generale che li confronta. Ogni vista per dispositivo può essere
controllata da sola. La vista generale viene costruita in seguito e non
modifica i dati di partenza.

Solo i circuiti della parte `train` diventano esempi per il RAG. I circuiti di
`validation` e `test` vengono compilati per creare il riferimento esterno usato
nella valutazione, ma non entrano nell'indice.

## 2. Struttura della directory e compito dei file

```text
datasets/expected_fidelity/
  README.md
  pilot/
    circuits/
      train/
      validation/
      test/
    <device_id>/
      split_manifest.json
      qiskit_runs.jsonl
      qiskit_configuration_aggregates.jsonl
      rag_examples.jsonl
      generation_status.json
      dataset_statistics.json
      reports/
        pilot_report.md
        pilot_summary.json
        configuration_statistics.csv
        circuit_statistics.csv
        failure_details.csv
    global/
      qiskit_runs.jsonl
      qiskit_configuration_aggregates.jsonl
      rag_examples.jsonl
      dataset_statistics.json
      reports/
        failure_details.csv
    device_comparison.md
    device_comparison.csv
  full/
    circuits/
      train/
      validation/
      test/
    split_manifest.json
    <device_id>/
    global/
```

Le cartelle `circuits/` conservano una sola copia dei file OpenQASM per ciascun
insieme. I manifest dei dispositivi puntano a questi file condivisi.

Ogni cartella `<device_id>/` è un mini-Dataset indipendente:

- `split_manifest.json` elenca i circuiti, la loro suddivisione e l'impronta
  SHA-256;
- `qiskit_runs.jsonl` conserva un record per ogni tentativo;
- `qiskit_configuration_aggregates.jsonl` riunisce i tre seed della stessa
  configurazione;
- `rag_examples.jsonl` contiene gli esempi etichettati della parte `train`;
- `generation_status.json` registra l'avanzamento della generazione;
- `dataset_statistics.json` riassume dimensioni, esiti e versioni dei record;
- `reports/` contiene il resoconto del campione, le statistiche e il dettaglio
  degli errori.

La cartella `global/` unisce i mini-Dataset e permette il confronto tra
dispositivi. `device_comparison.md` e `device_comparison.csv` riassumono invece
i risultati del campione pilota per una lettura immediata.

### Codice collegato al Dataset

```text
configs/
  qiskit_dataset_configurations.json
qiskit_dataset/
  __init__.py
  aggregation.py
  catalog.py
  core.py
  generation.py
  reporting.py
  views.py
scripts/
  07_prepare_qiskit_dataset.py
  08_generate_qiskit_dataset.py
  09_build_qiskit_dataset_views.py
  10_aggregate_qiskit_dataset.py
schemas/
  qiskit_run.schema.json
  qiskit_configuration_aggregate.schema.json
  qiskit_rag_example.schema.json
```

- `configs/qiskit_dataset_configurations.json` fissa il catalogo
  sperimentale.
- `qiskit_dataset/catalog.py` legge il catalogo e ne controlla la coerenza.
- `qiskit_dataset/core.py` prepara corpus, suddivisioni, manifest e tentativi.
- `qiskit_dataset/generation.py` esegue le compilazioni e salva risultati o
  errori.
- `qiskit_dataset/views.py` aggrega i seed e costruisce gli esempi RAG.
- `qiskit_dataset/aggregation.py` unisce le viste dei dispositivi.
- `qiskit_dataset/reporting.py` produce statistiche, tabelle e resoconti.
- Gli script `07`, `08`, `09` e `10` espongono in ordine le quattro fasi della
  procedura.
- I tre schemi JSON descrivono rispettivamente il singolo tentativo,
  l'aggregato di una configurazione e l'esempio destinato al RAG.

## 3. Implementazione

### 3.1 Catalogo sperimentale

`configs/qiskit_dataset_configurations.json` fissa:

- cinque dispositivi;
- dodici configurazioni Qiskit;
- i seed `0`, `1` e `2`;
- la misura, la direzione del confronto e le opzioni comuni di compilazione.

Le configurazioni comprendono:

- livello di ottimizzazione 2 e 3 con scelte Qiskit predefinite;
- metodi di disposizione `sabre`, `dense` e `trivial` con instradamento
  `sabre`;
- instradamento `lookahead` e `basic` con disposizione `sabre`.

Il valore `null` lascia a Qiskit la scelta predefinita. Le combinazioni fuori
catalogo non appartengono al riferimento sperimentale.

### 3.2 Suddivisione e copia dei circuiti

La suddivisione viene fatta per famiglie prima di espandere dispositivi,
configurazioni e seed:

- `train`, 422 circuiti: ae, dj, graphstate, portfolio, qaoa, qnn,
  random/ansatz, vqe e wstate;
- `validation`, 88 circuiti: qft/qftentangled e pricing;
- `test`, 90 circuiti: qpeexact/qpeinexact, tsp, routing e groundstate.

Non ci sono impronte QASM condivise tra le tre parti. Un limite noto è che
`validation` e `test` arrivano a 70 qubit, mentre i circuiti da 80 e 90 qubit
sono in `train`.

Il campione pilota usa dieci circuiti con suddivisione 6/2/2 ed è bilanciato tra
generatori Qiskit e TKET.

Ogni insieme conserva un unico corpus:

```text
pilot/circuits/{train,validation,test}/
full/circuits/{train,validation,test}/
```

Il campo `source_ref` dei manifest è relativo alla radice dell'insieme. Durante
la preparazione viene verificata l'impronta SHA-256. Un file condiviso già
presente non viene sovrascritto se il contenuto è diverso.

### 3.3 Preparazione e generazione

Lo script `07_prepare_qiskit_dataset.py` crea il corpus e il manifest del
dispositivo scelto. Da quel manifest vengono ricavati tutti i tentativi
previsti dal protocollo.

Lo script `08_generate_qiskit_dataset.py` esegue ogni combinazione. Per ciascun
tentativo:

1. legge il circuito;
2. carica il Target del dispositivo;
3. applica la configurazione e il seed;
4. compila con `qiskit.transpile`;
5. controlla gate e connettività;
6. calcola `expected_fidelity` oppure registra l'errore;
7. salva il record e le versioni usate.

Ogni record viene salvato in modo atomico. Una nuova esecuzione riparte dai
record mancanti. Le opzioni principali sono:

- `--retry-failures` ripete errori e superamenti del limite temporale;
- `--force` ignora e sovrascrive i risultati già presenti nella memoria locale;
- `--limit-runs N` limita il numero di tentativi per una prova rapida.

Per confrontare i tempi tra dispositivi bisogna usare lo stesso numero di
processi e lo stesso limite temporale. Cambiare questa regola significa cambiare
il protocollo e deve essere annotato.

### 3.4 Aggregati ed esempi RAG

Lo script `09_build_qiskit_dataset_views.py` riunisce i tre seed di ogni
configurazione. Una configurazione entra nella graduatoria solo se tutti e tre i
tentativi sono riusciti. Il valore usato per il confronto è la mediana di
`expected_fidelity`.

`qiskit_configuration_aggregates.jsonl` conserva anche le osservazioni
`run_id + seed + score`. In questo modo ogni prova citata successivamente può
essere ricondotta ai tentativi originali.

`rag_examples.jsonl` contiene una riga per ogni circuito `train` non duplicato.
Nella vista generale ogni riga comprende:

- circuito e 49 caratteristiche;
- misura e dispositivi compatibili;
- dispositivo scelto;
- tre migliori configurazioni per quel dispositivo;
- affermazioni in linguaggio naturale;
- prove con punteggi, seed, tentativi, Target e margini;
- limiti scientifici espliciti.

Il dispositivo scelto è quello la cui migliore configurazione valida ha il
punteggio più alto. In caso di parità esatta viene usato l'ordine stabile del
catalogo e l'affermazione chiarisce che i dati non mostrano una superiorità.
La stessa regola rende esplicite le parità tra configurazioni.

Affermazioni e prove descrivono ciò che è stato osservato. Non attribuiscono il
risultato alla complessità del circuito, alla configurazione o all'hardware
senza un confronto sperimentale controllato.

I vincoli della richiesta dell'utente sono ora descritti separatamente da
`schemas/assistant_request.schema.json`. Gli esempi offline non applicano
vincoli retroattivi: il relativo campo resta vuoto e usa lo stato
`not_applied_offline`.

### 3.5 Errori e limiti temporali

Il limite temporale vale per un singolo tentativo. Quando viene superato, il
sistema distingue:

- fase osservata;
- ultimo pass completato;
- punto dello stack in cui è stata osservata l'interruzione;
- fase Qiskit dedotta solo per corrispondenze verificate con Qiskit 2.1.1;
- parte della configurazione associata;
- livello di confidenza e base della deduzione.

L'ultimo pass completato non coincide necessariamente con quello interrotto. Lo
stack mostra il punto dell'interruzione, ma non ne dimostra la causa. Per questo
`causal_attribution_supported` rimane `false`.

I resoconti storici possono essere arricchiti usando le tracce già salvate,
senza riscrivere `qiskit_runs.jsonl`.

### 3.6 Aggregazione generale

Lo script `10_aggregate_qiskit_dataset.py` legge i mini-Dataset, ne controlla
manifest, versioni e collegamenti, poi scrive solo nella cartella `global/`.
Non modifica tentativi, aggregati o resoconti dei singoli dispositivi.

L'opzione `--check-only` esegue i controlli e calcola le statistiche senza
scrivere. `--devices` permette di costruire una vista dichiaratamente parziale.
Le statistiche elencano sempre i dispositivi mancanti, così un Dataset
incompleto non può essere presentato come completo.




### 3.7 Comandi principali

Procedura per un dispositivo:

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_127
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_127 \
  --workers 2 --timeout-seconds 120
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope pilot --device ibm_falcon_127 --top-k 3
```

Aggregazione dei dispositivi:

```bash
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope pilot --top-k 3 --require-all-supported
```

### 3.8 Sviluppi successivi

Prima di popolare l'insieme `full` vanno fissati:

1. catalogo e dispositivi;
2. limite temporale, numero di processi e ripetizione dei tentativi;
3. suddivisione e criteri di esclusione dei circuiti;
4. misura e regola della graduatoria;
5. valutazione della ricerca e del sistema con modello linguistico.

La politica per ripetere una risposta non valida del modello resta nel livello
applicativo. Non modifica il riferimento sperimentale del Dataset.

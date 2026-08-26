# Dataset Qiskit diretto — protocollo e struttura

Questa cartella contiene il Dataset sperimentale ottenuto compilando
direttamente con Qiskit. L'unità elementare è:

```text
(circuito, device, configurazione Qiskit, seed)
```

Lo score è `mqt.predictor.reward.expected_fidelity`, da massimizzare. È una
stima offline basata sul `Qiskit Target` sintetico e deterministico di MQT
Bench, non una misura ottenuta eseguendo il circuito su hardware reale.

## Catalogo sperimentale

`configs/qiskit_dataset_configurations.json` congela:

- cinque device;
- dodici configurazioni Qiskit;
- seed `0`, `1`, `2`;
- objective, direzione e opzioni fisse di transpile.

Le configurazioni coprono:

- baseline O2/O3 con layout e routing di default;
- layout `sabre`, `dense`, `trivial` con routing `sabre`;
- routing `lookahead` e `basic` con layout `sabre`.

`null` significa lasciare a Qiskit la scelta di default. Combinazioni fuori
catalogo non sono ground truth di questo protocollo.

## Split dei circuiti

Lo split avviene per gruppi di famiglie prima di espandere device,
configurazioni e seed:

- train, 422 circuiti: ae, dj, graphstate, portfolio, qaoa, qnn,
  random/ansatz, vqe e wstate;
- validation, 88 circuiti: qft/qftentangled e pricing;
- test, 90 circuiti: qpeexact/qpeinexact, tsp, routing e groundstate.

Non ci sono hash QASM condivisi tra split. Il claim sperimentale sostenibile e
quindi la generalizzazione a famiglie non viste. Limite noto: validation e test
arrivano a 70 qubit, mentre gli esempi da 80/90 qubit sono nel train.

Il pilot usa un sottoinsieme fisso di dieci circuiti, split 6/2/2 e bilanciato
tra generatori Qiskit e TKET. Validation e test vengono compilati offline per
creare la ground truth dell'evaluatore, ma non entrano nell'indice RAG.

## Una sola copia dei circuiti

Ogni scope conserva un solo corpus:

```text
pilot/circuits/{train,validation,test}/
full/circuits/{train,validation,test}/
```

I manifest rimangono nelle cartelle dei device ma `source_ref` e relativo
alla root dello scope. La preparazione verifica SHA-256 e non sovrascrive un
QASM condiviso già presente con contenuto diverso.

## Layout

```text
datasets/expected_fidelity/
  pilot/
    circuits/
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
      reports/failure_details.csv
    device_comparison.{md,csv}
  full/
    circuits/
    <device_id>/
    global/
```

Le cartelle per-device sono mini-Dataset indipendenti. Lo script 10 le legge e
scrive soltanto in `global/`: non modifica i loro raw run, aggregati o report.

Le versioni dei record sono separate per evitare ambiguità nelle migrazioni:

- manifest `2.0.0`: `source_ref` è relativo alla root dello scope condiviso;
- raw run `1.0.0`: la diagnostica timeout è un'aggiunta retrocompatibile;
- aggregato di configurazione `2.0.0`: include le osservazioni
  `run_id + seed + score` richieste dalle evidence;
- esempio RAG `2.0.0`: include label device/configurazioni, claim, evidence e
  caveat.

`dataset_statistics.json` riporta queste versioni in
`record_schema_versions`.

## Significato dei file

### `qiskit_runs.jsonl`

Una riga per tentativo. Contiene input, feature, device, configurazione, seed,
fase, tempi, validazione, score o failure e provenance delle versioni.

### `qiskit_configuration_aggregates.jsonl`

Una riga per circuito-device-configurazione. I tre seed sono repliche
sperimentali. Una configurazione è eleggibile soltanto con tutti i seed
riusciti; il ranking usa la mediana di expected fidelity. Le osservazioni
`run_id + seed + score` sono conservate per rendere verificabile ogni
evidence successiva.

### `rag_examples.jsonl`

Una riga per circuito train non duplicato. Nella vista globale:

- input: circuito, 49 feature, objective, device compatibili e campo
  versionato per futuri vincoli utente;
- label: device selezionato e top-3 configurazioni su quel device;
- claim: spiegazioni naturali della scelta;
- evidence: mediana, dispersione, seed, run, summary, target, margine e
  provenance;
- caveat: limiti scientifici espliciti.

Il device scelto è quello la cui migliore configurazione eleggibile ha lo score
più alto. In caso di parità esatta si usa l'ordine del catalogo e il claim
dichiara che i dati non dimostrano superiorità. Le top-3 sono poi ristrette al
device selezionato.

Anche le parità tra configurazioni sono etichettate: ogni top configuration
elenca `tied_score_config_ids` e il claim chiarisce quando la posizione deriva
soltanto dall'ordine deterministico del catalogo.

Claim ed evidence descrivono il risultato osservato. Non inferiscono che
complessita del circuito, configurazione o hardware siano la causa del
risultato senza un confronto sperimentale controllato.

## Timeout e failure

Il timeout copre un singolo tentativo. Per i nuovi run, il callback pubblico di
Qiskit registra l'ultimo pass completato; il traceback SIGALRM registra il frame
in cui l'interruzione e stata osservata. Il CSV distingue:

- fase osservata;
- ultimo pass completato;
- frame/pass interrotto osservato;
- stage Qiskit inferito solo per mapping verificati su Qiskit 2.1.1;
- componente della configurazione associata;
- confidenza, base dell'inferenza e `causal_attribution_supported=false`.

Il callback è post-pass: l'ultimo pass completato non è necessariamente quello
interrotto. Lo stack indica il punto di interruzione, non prova la causa. I
report storici vengono arricchiti dal traceback esistente senza riscrivere i
raw run.

## Procedura per-device

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_127
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_127 \
  --workers 2 --timeout-seconds 120
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope pilot --device ibm_falcon_127 --top-k 3
```

La generazione salva atomicamente ogni record. Rieseguire riprende dai record
mancanti. `--retry-failures` riesegue failure e timeout; `--force` ignora
la cache; `--limit-runs N` serve agli smoke test.

Per tempi confrontabili tra device usare lo stesso numero di worker e la stessa
soglia. Una modifica della timeout policy cambia il protocollo e va annotata.

## Aggregazione generale

```bash
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope pilot --top-k 3 --require-all-supported
```

`--check-only` valida e calcola le statistiche senza scrivere. `--devices`
permette una vista esplicitamente parziale; le statistiche elencano sempre i
device mancanti, evitando che un Dataset incompleto sembri completo.

## Popolazione e sviluppi futuri

Prima della popolazione full vanno congelati con i relatori:

1. catalogo e device;
2. timeout, worker e retry dei tentativi;
3. split e criteri di esclusione;
4. metrica e regola di ranking;
5. valutazione del retriever e del sistema LLM.

I vincoli utente saranno formalizzati in uno schema separato e versionato. Gli
esempi offline conservano per ora liste vuote con stato
`not_applied_offline`: non inventano vincoli retroattivi. Analogamente, la
politica di retry dell'LLM resta nel livello applicativo e verrà congelata come
parte del protocollo, senza alterare la ground truth.

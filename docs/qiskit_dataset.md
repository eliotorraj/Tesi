# Dataset Qiskit diretto

Questa pipeline sostituisce le trace RL con una ground truth ottenuta compilando
direttamente in Qiskit. L'unita sperimentale e la tupla:

```text
(circuito, device, configurazione Qiskit, seed)
```

I device ammessi sono `ibm_falcon_27`, `ibm_heron_133`,
`ibm_falcon_127`, `ibm_heron_156` e `quantinuum_h2_56`. Il device di
default resta `ibm_falcon_127`, ma ogni esecuzione deve usare l'opzione
`--device` per rendere esplicita la scelta.

Lo score e `mqt.predictor.reward.expected_fidelity` calcolato sul circuito
compilato. Piu alto e migliore. E una stima ottenuta dal Qiskit Target sintetico
e deterministico fornito da MQT Bench, non una misura su hardware IBM reale.

## Catalogo sperimentale

Il catalogo versionato e
`configs/qiskit_dataset_configurations.json`. Contiene esattamente 12
configurazioni e tre seed, `0, 1, 2`.

- baseline: O2/default/default e O3/default/default;
- layout: per O2 e O3, layout sabre, dense o trivial con routing sabre;
- routing: per O2 e O3, layout sabre con routing lookahead o basic.

Nel JSON e in Python, `null`/`None` significa lasciare a Qiskit la scelta
default. Non viene passata la stringa `"default"`.

Ogni coppia circuito-device compatibile produce 36 tentativi: 12 configurazioni
per 3 seed. I 10 circuiti del pilot restano identici per tutti i device, ma
quelli troppo larghi vengono annotati nel manifest e non espansi in 36 failure
ridondanti. Le cardinalita del pilot sono:

- 216 tentativi su 6 circuiti per `ibm_falcon_27`;
- 288 tentativi su 8 circuiti per `quantinuum_h2_56`;
- 360 tentativi su 10 circuiti per i tre device da almeno 127 qubit.

## Split dei circuiti

Lo split e per gruppi di famiglie, prima di espandere configurazioni e seed:

- train, 422 circuiti: ae, dj, graphstate, portfolio, qaoa, qnn,
  random/ansatz, vqe e wstate;
- validation, 88 circuiti: qft/qftentangled e pricing;
- test, 90 circuiti: qpeexact/qpeinexact, tsp, routing e groundstate.

Non ci sono hash QASM condivisi fra split. Il claim sostenibile e quindi la
generalizzazione a famiglie non viste. Limite da dichiarare: validation e test
arrivano a 70 qubit; gli esempi da 80/90 qubit compaiono soltanto nel train.

Il pilota e un sottoinsieme fisso 6/2/2, bilanciato 5 Qiskit e 5 TKET. I 600
nomi del corpus vengono conservati. Le 26 coppie di contenuto identico fra
`realamprandom` e `twolocalrandom` restano nello stesso split; gli alias
duplicati sono esclusi soltanto dall'export RAG.

## Struttura

```text
datasets/
  expected_fidelity/
    pilot/
      <device_id>/
        split_manifest.json
        circuits/{train,validation,test}/
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
      device_comparison.{md,csv}
    full/
      <device_id>/
        ...
```

La vecchia root `pilot/` con il primo esperimento Falcon-127 resta intatta
come snapshot storico. Tutte le nuove esecuzioni usano una sottocartella
`<device_id>`, quindi non possono sovrascriversi a vicenda. I report sono
piccoli artefatti derivati pensati per essere letti e confrontati.

I tre record hanno contratti formali in `schemas/`:

- `qiskit_run.schema.json`: una riga per tentativo, inclusi fase e dettagli
  completi in caso di failure o timeout;
- `qiskit_configuration_aggregate.schema.json`: una riga per
  circuito-device-configurazione, aggregata sui tre seed;
- `qiskit_rag_example.schema.json`: un esempio train-only con le top-k
  configurazioni.

## Procedura

Eseguire sempre dalla root del branch:

```bash
cd ~/Tesi
git switch qiskit_dataset
```

Preparare il pilot del device desiderato, per esempio Falcon-27:

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27
```

Controllare il piano senza compilare:

```bash
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27 --dry-run
```

Eseguire il pilot e costruire aggregati, RAG e report:

```bash
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27 \
  --workers 2 --timeout-seconds 100
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope pilot --device ibm_falcon_27 --top-k 3
```

Ripetere i tre comandi cambiando soltanto `--device`. Per statistiche di tempo
confrontabili, eseguire i pilot uno alla volta con 2 worker e la stessa soglia.
Il report per-device viene scritto in `reports/pilot_report.md`; il confronto
aggiornato è in `pilot/device_comparison.md`.

Dopo avere controllato i cinque pilot, preparare e avviare il completo:

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope full --device ibm_falcon_27
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope full --device ibm_falcon_27 \
  --workers 6 --timeout-seconds 100
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope full --device ibm_falcon_27 --top-k 3
```

La generazione salva atomicamente un record cache per tentativo. Ripetere lo
stesso comando riprende dai record mancanti. Usare `--retry-failures` soltanto
dopo avere corretto una causa sistematica; `--force` ricompila i tentativi
selezionati. `--limit-runs N` e destinato agli smoke test.

## Regola di ranking e RAG

I tre seed sono repliche sperimentali e non sono una scelta dell'LLM. Una
configurazione entra nel ranking soltanto con 3/3 tentativi riusciti. Il ranking
usa la mediana di expected fidelity, in ordine decrescente, con tie-break
deterministico dato dall'ordine del catalogo.

`rag_examples.jsonl` contiene esclusivamente circuiti train e non espone un
best seed. Validation e test restano ground truth di valutazione nei tentativi e
negli aggregati, ma non entrano nell'indice RAG.

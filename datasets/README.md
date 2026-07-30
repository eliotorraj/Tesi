# Circuiti sorgente per il dataset LLM

Questa cartella contiene uno split leakage-aware di circuiti
target-independent provenienti dal corpus bundled di MQT Predictor 2.3.0.

## Corpus di origine

Il framework installato contiene:

- 500 QASM nel corpus RL, da 2 a 30 qubit;
- 600 QASM nel corpus ML;
- gli stessi 500 file RL sono presenti nel corpus ML con lo stesso nome e hash;
- il corpus ML aggiunge 100 circuiti più grandi, da 30 a 90 qubit.

Lo split principale usa soltanto i 500 circuiti RL. Sono la distribuzione
coerente con il training delle policy device-specifiche. I 100 circuiti
ML-only vengono riservati a un futuro esperimento out-of-distribution.

## Split selezionato

| Split | Circuiti | Percentuale | Qiskit | TKET | Small 2–7 | Medium 8–15 | Large 16–30 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training | 56 | 70% | 30 | 26 | 29 | 21 | 6 |
| Validation | 12 | 15% | 7 | 5 | 3 | 4 | 5 |
| Test | 12 | 15% | 6 | 6 | 4 | 4 | 4 |
| Totale | 80 | 100% | 43 | 37 | 36 | 29 | 15 |

Cartelle:

```text
datasets/
├── llm_train/
│   ├── uncompiled/    56 QASM
│   └── compiled/
├── llm_validation/
│   ├── uncompiled/    12 QASM
│   └── compiled/
└── llm_test/
    ├── uncompiled/    12 QASM
    └── compiled/
```

Le cartelle `compiled` sono inizialmente vuote. Il generatore end-to-end
incorpora il QASM compilato direttamente nel JSON e non crea automaticamente
un file QASM esterno.

## Separazione per gruppi algoritmici

Famiglie correlate vengono trattate come un unico leakage group e non
attraversano i confini dello split.

### Training

- `graphstate`;
- `ae`;
- `groundstate_small` e `groundstate_medium`;
- `portfolioqaoa` e `portfoliovqe`;
- `pricingcall` e `pricingput`;
- `qaoa`;
- `qnn`;
- `random`, `realamprandom`, `su2random` e `twolocalrandom`;
- `routing`;
- `vqe`.

### Validation

- `dj`;
- `qft` e `qftentangled`.

### Test

- `wstate`;
- `qpeexact` e `qpeinexact`;
- `tsp`.

Questa separazione impedisce, ad esempio, che una variante `qft` compaia nel
training e una variante `qftentangled` nel test.

## Manifest

I file:

```text
datasets/split_manifest.csv
datasets/split_manifest.json
```

registrano per ogni circuito:

- split e famiglia;
- leakage group;
- generatore Qiskit/TKET;
- qubit, depth, size e gate count;
- fascia dimensionale;
- feature SupermarQ;
- hash SHA-256;
- percorso sorgente e destinazione;
- criterio deterministico di selezione.

Il manifest JSON contiene anche confronto RL/ML, quote, riepiloghi e risultato
della validazione di overlap, hash e parsing.

Lo split è riproducibile con:

```bash
python scripts/10_prepare_llm_circuit_splits.py --dry-run
```

Per ricrearlo intenzionalmente:

```bash
python scripts/10_prepare_llm_circuit_splits.py --overwrite
```

## Generazione dei JSON end-to-end

Prima conviene eseguire un singolo seed per controllare costo e tasso di
fallimento. Per il training:

```bash
python scripts/07_generate_llm_dataset.py \
  --input-dir datasets/llm_train/uncompiled \
  --metric expected_fidelity \
  --no-deterministic \
  --repetitions 1 \
  --output output/llm_dataset/train_expected_fidelity.json
```

Dopo il pilot si può aumentare `--repetitions`, ad esempio a 5. Validation e
test devono essere generati in file separati usando le rispettive cartelle.

Le trace di validation e test non devono essere inserite nel training,
nel retrieval o negli esempi few-shot dell'LLM.

## Limite sperimentale

Questo split misura la generalizzazione dell'LLM verso famiglie non viste
durante il suo addestramento. Non è però un test non visto per MQT Predictor:
le policy PPO sono state addestrate sul corpus RL completo da cui provengono
questi circuiti.

Per studiare anche la generalizzazione della policy MQT bisognerà creare un
esperimento OOD separato usando:

- i 100 circuiti ML-only più grandi;
- oppure circuiti esterni mai usati dal framework.

Quell'esperimento non va mescolato con lo split in-distribution corrente.

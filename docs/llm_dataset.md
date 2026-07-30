# Dataset JSON end-to-end per LLM

Questo progetto genera record JSON che rendono osservabile l'intera pipeline
di MQT Predictor 2.3.0:

```text
circuito target-independent
→ feature vector
→ figure of merit
→ ranking e scelta del device
→ policy RL specifica del device
→ sequenza dei pass
→ circuito compilato e score
```

## Generatore

Lo script principale è:

```text
scripts/07_generate_llm_dataset.py
```

Per un pilot su un solo circuito:

```bash
python scripts/07_generate_llm_dataset.py \
  --metric expected_fidelity \
  --max-circuits 1 \
  --no-deterministic \
  --output output/llm_dataset/pilot_expected_fidelity.json \
  --overwrite
```

Per generare un record per tutti i circuiti del mini-training set:

```bash
python scripts/07_generate_llm_dataset.py \
  --input-dir datasets/llm_train/uncompiled \
  --metric expected_fidelity \
  --no-deterministic \
  --repetitions 1 \
  --output output/llm_dataset/mqt_pipeline_expected_fidelity.json
```

Un'esecuzione lunga viene salvata dopo ogni circuito. Se viene interrotta:

```bash
python scripts/07_generate_llm_dataset.py \
  --input-dir datasets/llm_train/uncompiled \
  --metric expected_fidelity \
  --no-deterministic \
  --output output/llm_dataset/mqt_pipeline_expected_fidelity.json \
  --resume
```

L'opzione `--overwrite` sostituisce esplicitamente un output già esistente.
Senza `--resume` o `--overwrite`, lo script non sovrascrive un dataset.

## Struttura del JSON

Il documento contiene:

- `dataset`: versione, configurazione, ambiente, commit Git e conteggi;
- `feature_schema`: ordine e significato delle 49 feature;
- `figure_of_merit`: implementazione, direzione e interpretazione della metrica;
- `hardware_catalog`: descrizione deduplicata dei `Qiskit Target`;
- `records`: un record per circuito, ripetizione e seed.

Ogni record contiene:

- QASM e statistiche del circuito sorgente;
- feature vector ordinato e dizionario nome-valore;
- ranking completo di `predict_proba`, compatibilità e device selezionato;
- ground truth offline e score per device, quando presenti negli array `.npy`;
- catalogo delle azioni MQT e trace sequenziale della policy PPO;
- QASM, statistiche, score e validazione del circuito compilato;
- timeout o errore con la trace parziale, se la compilazione fallisce.

Il campo `device_selection.selected_device` è la predizione del classificatore.
Il campo `device_selection.offline_ground_truth.best_device_label`, quando
disponibile, è invece la label ottenuta dal confronto offline degli score.
I due concetti non vanno confusi.

## Inferenza deterministica e stocastica

MQT Predictor 2.3.0 invoca `model.predict` senza richiedere inferenza
deterministica. Per replicare questo comportamento si usa
`--no-deterministic`. La modalità `--deterministic` è utile come variante
controllata, ma policy poco addestrate possono ripetere ciclicamente alcuni
pass senza scegliere `terminate`.

Per questo motivo il dataset conserva anche record `error` e `timeout`: sono
esempi negativi utili e non vanno eliminati senza documentarlo.

## Dimensione e QASM intermedi

Il QASM sorgente e quello finale sono sempre incorporati nel JSON. Di default,
gli stati intermedi salvano feature e statistiche compatte. Per includere
anche il QASM dopo ogni azione:

```bash
python scripts/07_generate_llm_dataset.py \
  --include-intermediate-qasm \
  ...
```

Questa opzione può aumentare molto la dimensione del dataset.

## Limiti interpretativi

- `expected_fidelity` è una stima derivata dagli errori del `Target`; non è una
  fidelity misurata eseguendo il circuito su hardware reale.
- Il device predetto è il migliore secondo il classificatore locale e le sue
  classi, non il migliore dispositivo esistente in assoluto.
- Le policy disponibili sono artefatti locali di training; una trace valida
  non dimostra da sola qualità competitiva.
- I record devono mantenere versioni, seed, timeout e commit Git per poter
  essere confrontati scientificamente.

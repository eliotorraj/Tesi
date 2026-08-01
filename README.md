# MQT Predictor — workspace sperimentale

Questo repository contiene una sola pipeline operativa per MQT Predictor 2.3.0:

1. addestrare una policy RL per ogni coppia `device × metrica`;
2. compilare i 600 circuiti del corpus device-selection;
3. costruire il dataset supervisionato del device selector;
4. addestrare il classificatore e produrre il JSON supervisionato;
5. esportare gli esempi strict-RL nel dataset per l'LLM.

Le istruzioni operative sono tutte in questo file. La cartella `knowledge/`
contiene invece paper e note storiche: non descrive la struttura corrente del
workspace.

## Struttura canonica

```text
scripts/
  01_check_install.py
  02_list_devices.py
  03_train_rl_model.py
  04_train_device_selector.py
  05_sync_models.py
  06_export_llm_dataset.py
  bootstrap_ubuntu.sh
  bootstrap_windows.ps1

datasets/
  device_selector_expected_fidelity.json
  llm_mqt_full_pipeline_expected_fidelity.json

artifacts/
  models/
    rl/
    device_selector/
  cache/
    device_selector/expected_fidelity/
      compiled/
      manifest.jsonl
  checkpoints/
    rl/
  logs/
    rl/
    device_selector/
```

### `datasets/`

Contiene il dataset supervisionato del device selector e l'export separato per
l'LLM. Nel primo, ogni record rappresenta uno dei 600 circuiti sorgente e
contiene:

- le 49 feature del circuito target-independent;
- lo score esplicito per ciascun device compatibile;
- il device vincitore usato come label;
- il percorso dei QASM compilati;
- la provenienza della compilazione: RL, fallback Qiskit o legacy.

Il file autorevole è:

```text
datasets/device_selector_expected_fidelity.json
```

I circuiti sorgente non sono duplicati nel repository: sono i 600 QASM inclusi
in MQT Predictor e si trovano nell'ambiente `.venv`.

### `artifacts/cache/`

I QASM sotto `compiled/` non sono un secondo dataset. Sono risultati intermedi:
per ogni circuito esiste un QASM per ogni device compatibile. Servono per
ricalcolare score e label senza ripetere una compilazione durata molte ore.

`manifest.jsonl` è il registro append-only di tentativi, timeout, successi RL e
fallback. Non è il dataset supervisionato.

Questa cache può essere eliminata soltanto se si accetta di ricompilare tutto.

### `artifacts/models/`

È l'unica copia autorevole dei modelli nel workspace:

- `rl/`: policy PPO finali;
- `device_selector/`: classificatore supervisionato finale.

MQT Predictor richiede anche una copia runtime dentro `.venv`. Quella copia è
parte dell'ambiente installato, non è un secondo store del progetto, e può
essere ricreata con `05_sync_models.py`.

### `artifacts/checkpoints/rl/`

Contiene snapshot intermedi usati esclusivamente per riprendere un training RL
interrotto. Non sono i modelli finali usati da `qcompile`.

### `artifacts/logs/`

Tutti i log sono riuniti qui:

- `logs/rl/`: eventi TensorBoard;
- `logs/device_selector/`: log del runner, dei worker e di BQSKit.

## Setup

Su Ubuntu/WSL2:

```bash
bash scripts/bootstrap_ubuntu.sh
source .venv/bin/activate
```

Controllo rapido:

```bash
python scripts/01_check_install.py
python scripts/02_list_devices.py
```

Il baseline riproducibile usa Python 3.12 e `mqt.predictor==2.3.0` con le
versioni fissate in `pyproject.toml` e `uv.lock`.

## Installare i modelli nell'ambiente

Dopo aver ricreato `.venv`:

```bash
python scripts/05_sync_models.py install
```

Per acquisire eccezionalmente modelli già presenti nella `.venv`:

```bash
python scripts/05_sync_models.py capture --overwrite
```

I normali script di training aggiornano automaticamente sia il modello
canonico sia la copia runtime; non serve un export manuale successivo.

## Training RL

Serve una policy per ogni coppia `device × metrica`:

```bash
python scripts/03_train_rl_model.py \
  --device ibm_falcon_27 \
  --metric expected_fidelity \
  --timesteps 4096
```

I checkpoint vengono scritti in `artifacts/checkpoints/rl/<device>/`; i log
TensorBoard in `artifacts/logs/rl/`.

## Device selector e dataset JSON

La pipeline completa e riprendibile è gestita soltanto da:

```text
scripts/04_train_device_selector.py
```

Esempio:

```bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --num-workers 2
```

Lo script riusa automaticamente ogni QASM valido già presente nella cache.
Al termine genera il JSON, seleziona gli iperparametri e rifà il fit finale su
tutti i circuiti disponibili.

Per rigenerare modello e JSON dalla cache senza compilare:

```bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --finalize-only
```

Per rigenerare soltanto il JSON, senza compilazione e senza training:

```bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --export-json-only
```

## Stato del dataset corrente

Il JSON corrente contiene 600 circuiti e 1.646 compilazioni compatibili:

- 610 compilazioni prodotte dagli agenti RL;
- 1.031 compilazioni prodotte dal fallback Qiskit;
- 5 compilazioni legacy recuperate.

La distribuzione delle label è sbilanciata:

- `quantinuum_h2_56`: 522;
- `ibm_falcon_127`: 67;
- `ibm_falcon_27`: 11.

Questi dati validano la pipeline, ma il forte uso di fallback sui device IBM va
dichiarato in qualunque valutazione scientifica del selector.

## Dataset per l'LLM

Controllare prima la copertura strict-RL:

```bash
python scripts/06_export_llm_dataset.py --audit-only
```

Creare poi il JSON senza fallback o record legacy:

```bash
python scripts/06_export_llm_dataset.py --overwrite
```

Ogni record separa `input`, `expected_output` e
`deterministic_ground_truth`: score e QASM compilati restano disponibili per
la validazione, ma non devono entrare nel prompt. Il bilanciamento predefinito
limita a 3:1 il rapporto tra label hardware senza duplicare esempi; usare
`--balance none` per conservare tutti i record idonei.
## TensorBoard

```bash
tensorboard --logdir artifacts/logs/rl --port 6006
```

I file `events.out.tfevents...` sono binari e vanno aperti con TensorBoard.

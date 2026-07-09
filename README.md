# MQT Predictor - ambiente e primi test

Questo progetto contiene una pipeline riproducibile per analizzare e testare MQT Predictor 2.3.0. Le dipendenze di compilazione principali sono allineate al lockfile ufficiale della release, evitando incompatibilità con versioni future di MQT Bench e Qiskit.

La pipeline è stata verificata su Ubuntu 24.04/WSL2 con Python 3.12: lo smoke training ha creato entrambi i modelli e `qcompile` ha compilato con successo un GHZ a 5 qubit per `ibm_falcon_127`, restituendo circuito, lista dei pass RL e nome del device.

## Contenuto della cartella

- `scripts/`: setup, controlli dell'installazione, smoke test, training RL e training del selettore ML;
- `artifacts/results/`: circuito QASM e riepilogo JSON prodotti dal test di `qcompile`;
- `artifacts/smoke/`: circuiti usati e prodotti dallo smoke test, con relativi log;
- `artifacts/training_logs/`: eventi TensorBoard del training reale;
- `artifacts/checkpoints/`: checkpoint da cui riprendere il training RL.

## Scelta ambiente: Ubuntu su WSL2

MQT Predictor dichiara supporto ufficiale per Linux, macOS e Windows. Lo stack comprende PyTorch, Stable-Baselines3, Qiskit, TKET e BQSKit; shell, processi paralleli e futuri workflow di training/HPC risultano in genere più naturali su Linux. Windows nativo resta una buona alternativa per il solo smoke test.

Da PowerShell verifica anzitutto il nome con cui la distro è registrata:

```powershell
wsl --list --verbose
wsl --set-default Ubuntu-24.04
wsl -d Ubuntu-24.04
```

Usa in `--set-default` il nome esatto mostrato dalla prima istruzione: potrebbe essere `Ubuntu-24.04` oppure `Ubuntu` o altri nomi. Se l'app Ubuntu è stata appena scaricata ma la lista è vuota, avviala una volta dal menu Start per completare la registrazione e creare l'utente Linux. Solo se non è effettivamente installata usa `wsl --install -d Ubuntu-24.04` da PowerShell come amministratore.

## Setup Ubuntu

Dalla root del progetto:

```bash
bash scripts/bootstrap_ubuntu.sh
```

Il bootstrap installa `uv` se manca, prepara Python 3.12 e installa la release fissata in `pyproject.toml`. Alla fine stampa il comando di attivazione corretto.


```bash
cd ~/Nome_Cartella
source .venv/bin/activate
```

Per uscire dall'ambiente:

```bash
deactivate
```

## Setup Windows nativo (alternativa)

Installa prima `uv` con il comando ufficiale indicato dalla documentazione MQT:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Riapri PowerShell, quindi:

```powershell
.\scripts\bootstrap_windows.ps1
.\.venv\Scripts\Activate.ps1
```

## Percorso di test consigliato

Con l'ambiente attivo:

```bash
python scripts/01_check_install.py
python scripts/02_list_devices.py
python scripts/02_list_devices.py --details ibm_falcon_127
python scripts/03_train_smoke_models.py
python scripts/04_test_qcompile.py
```

Il terzo script replica l'idea dell'integration test ufficiale: addestra rapidamente una policy RL deterministica e un selettore con un solo device. Verifica che training, persistenza dei modelli, selezione e compilazione funzionino insieme, ma **non produce un modello scientificamente significativo**.

Nota di compatibilità: nella release 2.3.0 `qcompile` cerca rigidamente file chiamati `model_<metrica>_<device>.zip`. Gli script di questo repository lasciano quindi il parametro `model_name` al valore predefinito `model`; un nome personalizzato come quello mostrato in un esempio della documentazione stabile produrrebbe un file che `qcompile` non carica automaticamente.

`04_test_qcompile.py` controlla i tre risultati restituiti dall'API di MQT Predictor:

1. circuito compilato;
2. lista ordinata dei pass scelti dalla policy RL;
3. `qiskit.transpiler.Target` del device selezionato.

QASM e report JSON vengono salvati sotto `artifacts/results/`.

## Training non-smoke

Una policy RL deve essere addestrata per ogni coppia `device × figure_of_merit`:

```bash
python scripts/05_train_rl_model.py --device ibm_falcon_27 --metric expected_fidelity --timesteps 4096
python scripts/05_train_rl_model.py --device quantinuum_h2_56 --metric expected_fidelity --timesteps 4096
```

Dopo aver addestrato tutti i device candidati, genera score, label e Random Forest:

```bash
python scripts/06_train_device_selector.py \
  --devices ibm_falcon_27 quantinuum_h2_56 \
  --metric expected_fidelity \
  --num-workers 1 \
  --uncompiled-circuits PATH_UNCOMPILED_CIRUITS \
  --compiled-circuits PATH_COMPILED_CIRUITS
```

Lo script imposta automaticamente `GITHUB_ACTIONS=true` per usare le impostazioni BQSKit più leggere e `MPLCONFIGDIR=/tmp/mqt-predictor-matplotlib` per evitare problemi di cache Matplotlib.
Si può tentare con più worker, ma spesso ci sono conflitti; `--num-workers 1` è la scelta più stabile, ovviamente a costo della velocità di training.

Questa seconda fase compila il dataset per ogni device e può richiedere molto tempo. Il paper riporta più di 500 circuiti; il lavoro del 2023 impiegò circa cinque giorni per una generazione dati più ampia.

## Stato corrente dell'esperimento

Il training reale è stato avviato per il device `quantinuum_h2_56`, con figure of merit `expected_fidelity` e target di 4096 step; e per il device `ibm_heron_133` con figure of merit `critical_depth` e target di 4096 step, . Sono stati salvati un checkpoint automatico a 2.048 step.

## Log e checkpoint

I file `events.out.tfevents...` sotto `artifacts/training_logs/` sono log TensorBoard e non file di testo. Per consultarli, da un secondo terminale con l'ambiente attivo:

```bash
tensorboard --logdir artifacts/training_logs --port 6006
```

Apri quindi `http://localhost:6006`. I grafici principali sono `rollout/ep_rew_mean`, per l'andamento medio della reward, e `rollout/ep_len_mean`, per la lunghezza degli episodi. Con `n_steps=2048`, le metriche `train/*` compaiono dopo il primo rollout completo.

I file `.zip` sotto `artifacts/checkpoints/<device>/` non sono log: contengono lo stato del modello e servono per riprendere il training con `--resume-from`.

## Conservare i modelli

MQT Predictor 2.3.0 salva modelli e training data dentro il pacchetto installato in `.venv`. Prima di ricreare l'ambiente esportali:

```bash
python scripts/model_store.py export
```

Per ripristinarli in un nuovo ambiente:

```bash
python scripts/model_store.py import
```

Lo store predefinito è `artifacts/model_store/`. Può diventare molto grande e non è incluso in questa cartella di consegna.

## Generare il foglio Excel
Per generare il foglio excel contenente le informazioni sul dataset usato dal classificatore ho sviluppato 2 script. Si trovano in tmp/mqt_dataset_export/ e sono export_device_selector_dataset.py e build_dataset_workbook.py.

export_device_selector_dataset.py crea i file json che salvano i dati del dataset. 
Permette anche di scegliere la figure of merit che ci interessa con `--metric`, oppure di generare i fogli per tutte le metriche disonibili con `--all-available`
```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py --metric expected_fidelity
python tmp/mqt_dataset_export/export_device_selector_dataset.py --all-available
```

build_dataset_workbook.py crea il foglio excel a partire dai json creati precedentemente.
```bash
python tmp/mqt_dataset_export/build_dataset_workbook.py
```


## Nota importante sulla versione 2.x

Dalla versione 2.0 MQT Predictor non include più modelli preaddestrati. `pip install mqt.predictor` installa il framework, non una pipeline immediatamente pronta per `qcompile`. Occorre prima addestrare le policy RL e il device selector, oppure ripristinare artefatti già addestrati.

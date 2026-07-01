# MQT Predictor - ambiente e primi test

Questo workspace usa i documenti in `knowledge/` come base tecnica e contiene una pipeline riproducibile per MQT Predictor 2.3.0. Le dipendenze di compilazione principali sono allineate al lockfile ufficiale della release, evitando incompatibilità con versioni future di MQT Bench e Qiskit.

La pipeline è stata verificata su Ubuntu 24.04/WSL2 con Python 3.12: lo smoke training ha creato entrambi i modelli e `qcompile` ha compilato con successo un GHZ a 5 qubit per `ibm_falcon_127`, restituendo circuito, lista dei pass RL e `qiskit.transpiler.Target`.

## Scelta consigliata: Ubuntu su WSL2

MQT Predictor dichiara supporto ufficiale per Linux, macOS e Windows. Per questo progetto consiglio comunque **Ubuntu 24.04 tramite WSL2**: lo stack comprende PyTorch, Stable-Baselines3, Qiskit, TKET e BQSKit; shell, processi paralleli e futuri workflow di training/HPC risultano in genere più naturali su Linux. Windows nativo resta una buona alternativa per il solo smoke test.

Da PowerShell verifica anzitutto il nome con cui la distro è registrata:

```powershell
wsl --list --verbose
wsl --set-default Ubuntu-24.04
wsl -d Ubuntu-24.04
```

Usa in `--set-default` il nome esatto mostrato dalla prima istruzione: potrebbe essere `Ubuntu-24.04` oppure `Ubuntu`. Se l'app Ubuntu è stata appena scaricata ma la lista è vuota, avviala una volta dal menu Start per completare la registrazione e creare l'utente Linux. Solo se non è effettivamente installata usa `wsl --install -d Ubuntu-24.04` da PowerShell come amministratore.

Per training lunghi è preferibile tenere il progetto nel filesystem Linux, ad esempio `~/projects/MQT-Predictor-understanding`, anziché sotto `/mnt/c`.

## Setup Ubuntu

Dalla root del progetto:

```bash
bash scripts/bootstrap_ubuntu.sh
```

Il bootstrap installa `uv` se manca, prepara Python 3.12 e installa la release fissata in `pyproject.toml`. Alla fine stampa il comando di attivazione corretto.

Se il progetto si trova sotto `/mnt/c`, come in questo workspace, l'ambiente viene collocato nel filesystem Linux per evitare i forti rallentamenti di una `.venv` su NTFS:

```bash
source ~/.venvs/MQT-Predictor-understanding/bin/activate
```

Se anche il progetto si trova nel filesystem Linux, viene invece usata la classica `.venv` locale. Il percorso può essere personalizzato impostando `MQT_VENV_PATH` prima del bootstrap.

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

`04_test_qcompile.py` controlla i tre risultati discussi nella KB:

1. circuito compilato;
2. lista ordinata dei pass scelti dalla policy RL;
3. `qiskit.transpiler.Target` del device selezionato.

QASM e report JSON vengono salvati sotto `artifacts/results/`.

## Training non-smoke

Una policy RL deve essere addestrata per ogni coppia `device × figure_of_merit`:

```bash
python scripts/05_train_rl_model.py --device ibm_falcon_27 --metric expected_fidelity --timesteps 100000
python scripts/05_train_rl_model.py --device quantinuum_h2_56 --metric expected_fidelity --timesteps 100000
```

Dopo aver addestrato tutti i device candidati, genera score, label e Random Forest:

```bash
python scripts/06_train_device_selector.py \
  --devices ibm_falcon_27 quantinuum_h2_56 \
  --metric expected_fidelity
```

Questa seconda fase compila il dataset per ogni device e può richiedere molto tempo. Il paper riporta più di 500 circuiti; il lavoro del 2023 impiegò circa cinque giorni per una generazione dati più ampia. Parti dallo smoke test, poi misura i tempi su un sottoinsieme prima di lanciare esperimenti completi.

## Conservare i modelli

MQT Predictor 2.3.0 salva modelli e training data dentro il pacchetto installato in `.venv`. Prima di ricreare l'ambiente esportali:

```bash
python scripts/model_store.py export
```

Per ripristinarli in un nuovo ambiente:

```bash
python scripts/model_store.py import
```

Lo store predefinito è `artifacts/model_store/` ed è ignorato da Git perché i modelli possono diventare grandi.

## Nota importante sulla versione 2.x

Dalla versione 2.0 MQT Predictor non include più modelli preaddestrati. `pip install mqt.predictor` installa il framework, non una pipeline immediatamente pronta per `qcompile`. Occorre prima addestrare le policy RL e il device selector, oppure ripristinare artefatti già addestrati.

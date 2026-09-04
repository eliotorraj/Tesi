# Procedura operativa: modelli RL, modello ML e Dataset Qiskit full

Questa è la guida da seguire per produrre gli artefatti confermativi del
protocollo MQT Predictor 2.4-v2. Usa soltanto gli script del repository e non
richiede array o cicli Bash scritti a mano.

La guida scientifica completa resta
[protocollo_sperimentale_v2.md](protocollo_sperimentale_v2.md). Questo
documento è il runbook operativo: indica cosa eseguire, su quale computer, come
riprendere un'interruzione e quali file devono esistere alla fine.

## Perché prima compariva RL_DEVICES

La dichiarazione RL_DEVICES non era un requisito di MQT Predictor e non faceva
parte del protocollo. Era soltanto una variabile Bash usata per evitare di
ripetere due o tre comandi. Ora la ripartizione è incorporata
nell'orchestratore:

- **pc1**: ibm_falcon_127, ibm_heron_156, quantinuum_h2_56;
- **pc2**: ibm_falcon_27, ibm_heron_133.

Sui due computer bastano rispettivamente:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc1
~~~

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc2
~~~

L'orchestratore richiama 03_train_rl_model.py una volta per device, in modo
sequenziale. Non reimplementa il training. Passa esplicitamente i parametri
congelati, salta solo un modello finale già conforme e riprende automaticamente
il checkpoint v2 valido con il maggior numero di step.

## 1. Regole che non devono cambiare

- Branch: codex/experiment-v2-mqt-2.4.0.
- I due computer devono usare lo stesso commit del branch e lo stesso uv.lock.
- Ambiente: Ubuntu/WSL, Python 3.12, dipendenze installate con uv sync --frozen.
- Metrica: expected_fidelity.
- Circuiti RL e ML: esclusivamente i 422 circuiti dello split train v2.
- Training RL: 100000 step, seed 0, max_steps 64, checkpoint ogni 2048 step,
  timeout di una singola azione BQSKit pari a 60 secondi.
- Dataset Qiskit prima del rilascio finale: soltanto train e validation.
- Non usare allow-overwrite, allow-target-drift, include-test o lo split test.
- Non eseguire le fasi v2 dal vecchio branch mqt-predictor-2.4.0.

Il commit di implementazione congelato è
66284c1b567b3fb411e42a7849f3b1c8453f0dcd. Eventuali commit successivi che
aggiungono soltanto questa guida e l'orchestratore non cambiano la logica
scientifica degli script 03--15. Prima di iniziare, i due computer devono
comunque mostrare lo stesso valore con:

~~~bash
git rev-parse HEAD
~~~

## 2. Controllo iniziale su entrambi i computer

Entrare nel worktree v2, attivare l'ambiente e mostrare il piano:

~~~bash
cd /home/elioe/Tesi-mqt-2.4-v2
source .venv/bin/activate
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
.venv/bin/python scripts/16_run_pipeline_v2.py plan
~~~

Se la preparazione è già stata completata, non è necessario rifarla. È però
sicuro rilanciarla: gli script sono idempotenti.

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py prepare
~~~

Questo comando esegue in ordine:

1. controllo delle versioni e dei cinque Target congelati;
2. controllo preventivo della preparazione v2;
3. materializzazione dei soli circuiti train e validation;
4. congelamento dei piani validation e test, senza aprire né eseguire il test.

Se prepare fallisce, non avviare il training. Correggere prima l'errore di
ambiente, versione, Target o manifest.

## 3. Training dei cinque modelli RL su due computer

I training sono sequenziali su ogni computer e paralleli tra i due computer.
Questo evita di tenere più modelli PPO/BQSKit pesanti contemporaneamente sulla
stessa macchina.

### Computer 1

~~~bash
cd /home/elioe/Tesi-mqt-2.4-v2
source .venv/bin/activate
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc1
~~~

Ordine eseguito:

1. ibm_falcon_127;
2. ibm_heron_156;
3. quantinuum_h2_56.

### Computer 2

~~~bash
cd /home/elioe/Tesi-mqt-2.4-v2
source .venv/bin/activate
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc2
~~~

Ordine eseguito:

1. ibm_falcon_27;
2. ibm_heron_133.

### Interruzione e ripresa RL

Per interrompere, premere Ctrl+C una sola volta e attendere il messaggio
“Training interrotto. Checkpoint di emergenza”. Non chiudere forzatamente il
terminale e non usare kill -9.

Per riprendere basta rilanciare esattamente lo stesso comando del gruppo.
L'orchestratore:

1. salta le policy finali già presenti e conformi;
2. cerca soltanto nella directory v2 della run prevista;
3. valida archivio, metadati, device, Target, seed, manifest e profilo;
4. passa a 03_train_rl_model.py il checkpoint valido più avanzato.

Per indicare manualmente un checkpoint:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl \
  --group pc2 \
  --resume-from ibm_falcon_27=artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/checkpoints/rl/ibm_falcon_27/v2-ibm-falcon-27-seed0/NOME_CHECKPOINT.zip
~~~

Il target 100000 rappresenta sempre il totale della run, non altri 100000 step
da aggiungere al checkpoint.

### Output RL attesi

Ogni computer salva i propri risultati sotto:

~~~text
artifacts/experiments/
  qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/
    models/rl/
~~~

Per ogni device devono esistere insieme:

~~~text
model_expected_fidelity_<device>.zip
model_expected_fidelity_<device>.metadata.json
~~~

Il file ZIP e il suo file metadata sono una coppia indivisibile. I checkpoint
e i log possono restare sul computer che ha eseguito il training.

## 4. Riunire i cinque modelli sul computer coordinatore

Si consiglia di usare il computer 1 come coordinatore. Dal computer 2 copiare
nella directory models/rl del coordinatore queste quattro risorse:

~~~text
model_expected_fidelity_ibm_falcon_27.zip
model_expected_fidelity_ibm_falcon_27.metadata.json
model_expected_fidelity_ibm_heron_133.zip
model_expected_fidelity_ibm_heron_133.metadata.json
~~~

Si possono usare scp, rsync, una cartella condivisa o un supporto esterno. Non
usare Git per versionare i modelli e non sostituire silenziosamente un file
diverso già presente. Dopo la copia, sul coordinatore eseguire:

~~~bash
.venv/bin/python scripts/05_sync_models.py install --component rl --overwrite
.venv/bin/python scripts/05_sync_models.py verify --component rl
~~~

Il secondo comando deve terminare con “5/5 artefatti conformi”. La verifica
controlla anche che ogni copia runtime sia identica al modello canonico e che i
metadati attestino 100000 step sul protocollo v2.

## 5. Costruzione del Training set e training del modello ML

Questa fase si esegue soltanto sul coordinatore, dopo avere riunito e verificato
tutti i modelli RL:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml
~~~

Il comando richiama in ordine gli script 05, 04, 05, 01 e 07 per:

1. installare e verificare le cinque policy RL nella .venv del coordinatore;
2. compilare in modo durevole le coppie circuito-device dello split train;
3. costruire il **Training set** del selettore;
4. addestrare la Random Forest con tutte e cinque le classi;
5. installare e verificare il modello ML;
6. eseguire il canary finale di qcompile.

Impostazioni conservative predefinite: un worker RL, tre tentativi massimi per
coppia, timeout 300 secondi, startup timeout 240 secondi e un worker per la
Random Forest.

La parte costosa è la costruzione del Training set, non il fit finale della
Random Forest. Ogni compilazione valida viene salvata subito. Dopo
un'interruzione, rilanciare lo stesso comando ml: lo script 04 riusa i
checkpoint durevoli e continua dalle coppie mancanti.

Output principali:

~~~text
datasets/experiments/
  qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/
    training_set/device_selector_expected_fidelity.json

artifacts/experiments/
  qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/
    models/ml/trained_clf_expected_fidelity.joblib
    models/ml/trained_clf_expected_fidelity.metadata.json
~~~

Nel lessico del progetto, questo è il **Training set** del modello ML. Non è il
**Dataset** destinato al RAG/LLM.

## 6. Canary del Dataset Qiskit full

Il Dataset Qiskit è tecnicamente indipendente dai modelli RL/ML, ma in questa
procedura viene popolato dopo il canary di qcompile per ridurre la contesa di
CPU e RAM.

Sul coordinatore:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-canary
~~~

Il comando prepara ciascuno dei cinque device ed esegue un solo tentativo
train mancante per device. Non usa validation e non può richiedere test. Se
riesce per tutti i device, passare al popolamento completo.

## 7. Popolamento del Dataset Qiskit full

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full
~~~

Per ciascuno dei cinque device il comando esegue:

1. 07_prepare_qiskit_dataset.py con scope full;
2. 08_generate_qiskit_dataset.py sullo split train;
3. 08_generate_qiskit_dataset.py sullo split validation;
4. 09_build_qiskit_dataset_views.py con top-k 3.

Alla fine richiama 10_aggregate_qiskit_dataset.py richiedendo tutti i device.
Lo split test non è una scelta disponibile in questo orchestratore. Prima
dell'apertura del test sono previsti 87120 tentativi Qiskit sulle coppie
compatibili per larghezza.

La generazione è riprendibile. In caso di interruzione, rilanciare lo stesso
comando: i record terminali già presenti vengono riconosciuti e non sono
ricalcolati. Timeout e failure sono risultati sperimentali e restano nel
Dataset; non forzare o ripetere i fallimenti senza una decisione esplicita di
protocollo.

Output globale principale:

~~~text
datasets/experiments/
  qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/
    expected_fidelity/full/global/rag_examples.jsonl
~~~

Gli output per device, gli aggregati, i report e lo stato di generazione
rimangono sotto la stessa directory expected_fidelity/full/.

## 8. Checklist finale

La pipeline è pronta quando sono vere tutte le condizioni seguenti:

- la verifica RL riporta 5/5;
- la verifica complessiva dei modelli riporta 6/6;
- il controllo installazione con Target e modelli richiesti riesce;
- il canary qcompile riesce;
- esiste il Training set JSON del device selector;
- esiste la vista globale del Dataset Qiskit full;
- l'aggregazione Qiskit comprende tutti i cinque device;
- nessun comando ha usato lo split test.

Verifica manuale finale:

~~~bash
.venv/bin/python scripts/05_sync_models.py verify
.venv/bin/python scripts/01_check_install.py \
  --require-frozen-targets --require-models
.venv/bin/python scripts/07_validate_qcompile.py \
  --timeout 300 --max-steps 64
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope full \
  --catalog configs/qiskit_dataset_configurations_v2.json \
  --top-k 3 \
  --require-all-supported \
  --check-only
~~~

## 9. Sequenza minima da ricordare

Computer 1:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc1
~~~

Computer 2:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group pc2
~~~

Poi, dopo avere copiato sul coordinatore i due modelli prodotti dal computer 2:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-canary
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full
~~~

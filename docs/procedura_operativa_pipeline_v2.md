# Procedura operativa: modelli RL, modello ML e Dataset Qiskit full

Questa è la guida da seguire per produrre gli artefatti confermativi del
protocollo MQT Predictor 2.4-v2. Usa soltanto gli script del repository e non
richiede array o cicli Bash scritti a mano.

La guida scientifica completa resta
[protocollo_sperimentale_v2.md](protocollo_sperimentale_v2.md). Questo
documento è il runbook operativo: indica cosa eseguire, su quale computer, come
riprendere un'interruzione e quali file devono esistere alla fine.

## Divisione dei ruoli tra i due computer

La dichiarazione RL_DEVICES non era un requisito di MQT Predictor e non faceva
parte del protocollo: era soltanto una comodità Bash. Non serve più.
I due computer, sullo stesso HEAD, hanno ora ruoli indipendenti:

- **PC Dataset**: popola subito il Dataset Qiskit train+validation per RAG;
- **PC Modelli**: allena in sequenza tutti i cinque modelli RL, calibra il
  timeout ML e poi costruisce il Training set e allena il selettore ML.

I due comandi lunghi possono essere eseguiti contemporaneamente perché il
Dataset Qiskit non dipende dai modelli RL o ML:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full
~~~

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group models
~~~

L'orchestratore richiama gli script numerati e non reimplementa né training né
generazione. Il gruppo models contiene tutti e cinque i device nell'ordine
congelato. Salta soltanto un modello finale già conforme e riprende
automaticamente il checkpoint v2 valido con il maggior numero di step.

## 1. Regole che non devono cambiare

- Branch: codex/experiment-v2-mqt-2.4.0.
- I due computer devono usare lo stesso commit del branch e lo stesso uv.lock.
- Ambiente: Ubuntu/WSL, Python 3.12, dipendenze installate con uv sync --frozen.
- Metrica: expected_fidelity.
- Circuiti RL e ML: esclusivamente i 422 circuiti dello split train v2.
- Training RL: target richiesto 100000 step, seed 0, max_steps 64, rollout PPO
  da 2048 step, checkpoint ogni 10240 step e timeout di una singola azione
  BQSKit pari a 60 secondi.
- Dataset Qiskit prima del rilascio finale: soltanto train e validation.
- Non usare allow-overwrite, allow-target-drift, include-test o lo split test.
- Non eseguire le fasi v2 dal vecchio branch mqt-predictor-2.4.0.

Stable-Baselines3 completa sempre il rollout corrente: con target 100000 il
contatore finale atteso e validato è quindi 100352, cioè 49 × 2048. La cadenza
10240 equivale a cinque rollout completi e produce nove checkpoint storici per
modello. In aggiunta esiste un solo file latest_rollout, aggiornato dopo ogni
rollout da 2048 e sempre sovrascritto: rende sicura la ripresa senza far
crescere lo spazio occupato. Il modello finale e un eventuale snapshot
d'emergenza a nome fisso completano il set.

Prima di iniziare, i due computer devono mostrare lo stesso valore con:

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

## 3. Training dei cinque modelli RL sul PC Modelli

Un solo comando allena tutti i modelli in sequenza. In questo modo sulla
macchina resta attivo un solo PPO/BQSKit pesante alla volta:

~~~bash
cd /home/elioe/Tesi-mqt-2.4-v2
source .venv/bin/activate
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group models
~~~

Ordine eseguito:

1. ibm_falcon_27;
2. ibm_heron_133;
3. ibm_falcon_127;
4. ibm_heron_156;
5. quantinuum_h2_56.

### Interruzione e ripresa RL

Per interrompere, premere Ctrl+C una sola volta e attendere il messaggio sullo
snapshot diagnostico. Non chiudere forzatamente il terminale e non usare
kill -9. Lo snapshot interrupted fotografa anche stati parziali e non viene
usato per riprendere.

Dopo ogni aggiornamento PPO completo lo script sovrascrive latest_rollout; ogni
cinque aggiornamenti conserva anche un checkpoint storico. Per riprendere basta
rilanciare esattamente lo stesso comando del gruppo.
L'orchestratore:

1. salta le policy finali già presenti e conformi;
2. cerca soltanto nella directory v2 della run prevista;
3. valida archivio, metadati, device, Target, seed, manifest, profilo e
   allineamento al rollout, scartando lo snapshot interrupted;
4. passa a 03_train_rl_model.py lo stato PPO completo più avanzato.

Per indicare manualmente un checkpoint:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl \
  --group models \
  --resume-from ibm_falcon_27=artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/checkpoints/rl/ibm_falcon_27/v2-ibm-falcon-27-seed0/NOME_CHECKPOINT.zip
~~~

Il target 100000 rappresenta sempre il totale della run, non altri 100000 step
da aggiungere al checkpoint.

### Output RL attesi

Il PC Modelli salva tutti i propri risultati sotto:

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
e i log restano sul PC Modelli.

## 4. Popolamento parallelo sul PC Dataset

Non bisogna attendere la fine degli RL. Dopo prepare, sul secondo computer
eseguire prima il canary e poi il popolamento completo:

~~~bash
cd /home/elioe/Tesi-mqt-2.4-v2
source .venv/bin/activate
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-canary
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full
~~~

Il secondo comando riconosce il lavoro del canary e prosegue dai tentativi
mancanti. Popola esclusivamente train e validation per tutti i cinque device,
costruisce le viste top-k e aggrega il Dataset globale. È riprendibile
rilanciando lo stesso comando. Gli artefatti generati sono esclusi da Git:
avere lo stesso HEAD sincronizza il codice, non le directory datasets/ e
artifacts/.

## 5. Costruzione del Training set e training del modello ML

Questa fase si esegue sul PC Modelli, dopo il completamento di tutti i modelli
RL. Non dipende dal popolamento Qiskit in corso sull'altro computer.

### Canary e scelta del timeout

Al momento non esiste un manifest di compilazioni ML dal quale ricavare tempi
affidabili. I tempi e i timeout del Dataset Qiskit non sono trasferibili:
Qiskit e le policy RL del device selector percorrono compilatori diversi.
Perciò 300 secondi resta il tetto provvisorio, non una soglia già dimostrata
necessaria.

Appena terminano i cinque RL, eseguire:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml-canary
~~~

Il canary usa un solo worker, un solo tentativo e i primi 10 circuiti train
compatibili, con timeout 300 e modalità compile-only. Le compilazioni valide
restano riutilizzabili nel run completo; un fallimento conserva invece altri
tentativi disponibili. Tempi e stati sono nel file:

~~~text
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/cache/ml/expected_fidelity/manifest.jsonl
~~~

Dopo il canary si sceglie il timeout guardando distribuzione dei tempi dei
successi e fallimenti saturati, non soltanto la media. Se il campione mostra
ampio margine, si usa un valore inferiore; se non dà evidenza sufficiente, si
mantengono 300 secondi. Per evitare una decisione arbitraria, fermarsi qui e
valutare il manifest prima del run completo.

### Run completo

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml --timeout SECONDI_SCELTI
~~~

Il comando richiama in ordine gli script 05, 04, 05, 01 e 07 per:

1. installare e verificare le cinque policy RL nella .venv del PC Modelli;
2. compilare in modo durevole le coppie circuito-device dello split train;
3. costruire il **Training set** del selettore;
4. addestrare la Random Forest con tutte e cinque le classi;
5. installare e verificare il modello ML;
6. eseguire il canary finale di qcompile.

Impostazioni conservative predefinite: un worker RL, tre tentativi massimi per
coppia, startup timeout 240 secondi e un worker per la Random Forest. Se
--timeout viene omesso, il valore resta 300 secondi.

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

Il Dataset Qiskit è tecnicamente indipendente dai modelli RL/ML. Sul PC Dataset
questa fase può iniziare subito e procedere mentre l'altro computer allena gli
RL. Le sezioni 6 e 7 dettagliano i due comandi già mostrati nella sezione 4.

Sul PC Dataset:

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

Verifica manuale finale sul PC Modelli:

~~~bash
.venv/bin/python scripts/05_sync_models.py verify
.venv/bin/python scripts/01_check_install.py \
  --require-frozen-targets --require-models
.venv/bin/python scripts/07_validate_qcompile.py \
  --timeout SECONDI_SCELTI --max-steps 64
~~~

Verifica manuale finale sul PC Dataset:

~~~bash
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope full \
  --catalog configs/qiskit_dataset_configurations_v2.json \
  --top-k 3 \
  --require-all-supported \
  --check-only
~~~

Non è necessario spostare il Dataset, che è l'artefatto più grande, per
considerare completate le due produzioni. Se serve una sola macchina finale,
conviene usare il PC Dataset come coordinatore e copiarvi dal PC Modelli la
directory models/ completa e la directory training_set/. Conservare sempre
insieme ciascun modello e il relativo metadata, non usare Git per questi
artefatti e verificare gli hash prima di sostituire file già presenti.

## 9. Sequenza minima da ricordare

I due blocchi seguenti iniziano in parallelo dopo prepare.

PC Dataset:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-canary
.venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full
~~~

PC Modelli:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --group models
~~~

Solo quando tutti i modelli RL sono pronti:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml-canary
~~~

Valutato il manifest dei tempi:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py ml --timeout SECONDI_SCELTI
~~~

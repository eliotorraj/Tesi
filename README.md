# Assistente LLM per la compilazione quantistica con MQT Predictor

Progetto di tesi dedicato alla scelta dell'hardware e alla compilazione di
circuiti quantistici. La repository contiene esperimenti riproducibili basati
su MQT Predictor e lo scheletro di un futuro assistente LLM.

Il progetto è in sviluppo. I modelli, i risultati sperimentali e il prototipo
verranno aggiornati durante il lavoro di tesi.

## 1. Introduzione e scopo della tesi

Compilare un circuito quantistico significa adattarlo a un hardware preciso:
bisogna rispettarne il numero di qubit, i gate disponibili, le connessioni e le
caratteristiche fisiche. Hardware diversi possono produrre risultati diversi
per lo stesso circuito.

Questa tesi studia come assistere tale scelta attraverso due livelli:

1. riprodurre e analizzare la pipeline di MQT Predictor, che sceglie un hardware
   e compila il circuito mediante modelli di apprendimento automatico;
2. costruire un prototipo basato su LLM che riceva circuito e richiesta
   dell'utente, consulti i risultati sperimentali, proponga una scelta motivata
   e avvii la compilazione soltanto dopo una conferma esplicita.

Il prototipo non deve sostituire gli strumenti deterministici. L'LLM suggerisce
e spiega; compatibilità e risultato vengono controllati dal programma, mentre
la compilazione effettiva viene eseguita con Qiskit.

In questa repository usiamo due termini distinti:

- **Training set**: insieme delle coppie circuito-hardware usato per addestrare
  il modello supervisionato che sceglie l'hardware;
- **Dataset**: insieme di informazioni destinato ai futuri esperimenti con
  l'LLM, tramite RAG o eventuale addestramento.


## 2. MQT Predictor in breve

[MQT Predictor](https://mqt.readthedocs.io/projects/predictor/en/stable/)
è il progetto su cui si basa la parte sperimentale della tesi. Riceve un
circuito non ancora adattato a uno specifico hardware e lavora in due fasi:

1. un modello supervisionato analizza le caratteristiche del circuito e
   suggerisce l'hardware più promettente;
2. un modello di Reinforcement Learning specifico per hardware e metrica
   sceglie la sequenza dei passi di compilazione.

Il risultato comprende il circuito compilato, l'hardware selezionato e la lista
dei passi eseguiti. Un esempio essenziale è disponibile nella
[guida ufficiale di MQT Predictor](https://mqt.readthedocs.io/projects/predictor/en/stable/quickstart.html).

La scelta del risultato migliore dipende dalla figure of merit, cioè dalla
metrica da ottimizzare. Il lavoro corrente usa soprattutto expected_fidelity:
è una stima calcolata dalle informazioni del dispositivo, non il risultato di
un'esecuzione su hardware quantistico reale.

Questa repository non reimplementa MQT Predictor. Lo usa come base e aggiunge:

- una procedura riproducibile per addestrare e conservare i modelli;
- una pipeline resistente a errori e interruzioni;
- la generazione del Training set del selettore hardware;
- l'esportazione dei dati necessari agli esperimenti con l'LLM;
- lo scheletro del futuro assistente.

## 3. Requisiti e installazione

### 3.1 Ambiente supportato

La configurazione riproducibile del progetto è:

- Ubuntu oppure Ubuntu su WSL2;
- Python 3.12;
- mqt.predictor 2.4.0;
- dipendenze fissate in pyproject.toml e uv.lock.

Lo script principale per il Training set richiede funzioni disponibili su
Linux. L'esecuzione Python nativa da Windows non è quindi supportata. Su Windows
bisogna usare WSL2. macOS non fa parte dell'ambiente verificato.

Non servono credenziali per un hardware quantistico reale. Serve una connessione
Internet durante la prima installazione delle dipendenze.

Il protocollo sperimentale usa soltanto `expected_fidelity` e congela questo
ordine dei candidati, condiviso con il branch `qiskit_dataset`:

1. `ibm_falcon_27`;
2. `ibm_heron_133`;
3. `ibm_falcon_127`;
4. `ibm_heron_156`;
5. `quantinuum_h2_56`.

MQT Predictor 2.4.0 usa MQT Bench 2.2.3, mentre i risultati Qiskit già
congelati erano stati prodotti con MQT Bench 2.0.0. Un hash grezzo non è
direttamente confrontabile, perché Qiskit 2.5 aggiunge al `Target` operazioni
di control-flow e questo branch usa uno schema di fingerprint versionato. Il
controllo normalizza prima queste sole differenze di rappresentazione.

Dopo la normalizzazione, i dati nativi dei quattro Target IBM risultano
realmente cambiati; `quantinuum_h2_56` coincide invece con il Target legacy.
Vanno comunque rigenerati per tutti e cinque i device Qiskit default, Qiskit
random e oracle nell'ambiente 2.4.0/Qiskit 2.5.0: soltanto così gli score
`expected_fidelity` e le pipeline dei competitor restano omogenei.

La [guida ufficiale al training](https://mqt.readthedocs.io/projects/predictor/en/stable/setup.html)
descrive le due fasi originali; gli script locali aggiungono checkpoint,
timeout, validazione e copie canoniche riproducibili.

### 3.2 Risorse hardware consigliate

Questi valori sono indicazioni pratiche, non requisiti imposti da MQT:

| Risorsa | Indicazione |
| --- | --- |
| CPU | processore moderno con più core |
| RAM | con 8 GiB usare 1 worker; con almeno 16 GiB si possono provare 2 worker |
| Disco | almeno 20 GiB per ambiente e codice; 50 GiB o più per modelli, checkpoint e training completi |
| GPU | non obbligatoria per la pipeline corrente |

Ogni worker RL può usare diversi GiB di memoria. Se la macchina ha circa 8 GiB
di RAM, mantenere `--num-workers 1`.

### 3.3 Preparare WSL2 su Windows

Da PowerShell avviato come amministratore:

~~~powershell
wsl --install -d Ubuntu
wsl --set-version Ubuntu 2
wsl -d Ubuntu
~~~

La procedura ufficiale è descritta nella
[documentazione Microsoft per WSL](https://learn.microsoft.com/windows/wsl/install).

Dentro Ubuntu installare gli strumenti di base:

~~~bash
sudo apt update
sudo apt install -y git git-lfs curl
git lfs install
~~~

È preferibile conservare il progetto nella home Linux, per esempio in
~/Tesi, e non sotto /mnt/c. L'accesso continuo al disco Windows può rallentare
molto la creazione dell'ambiente e il training.

### 3.4 Scaricare la repository

Clone normale, comprensivo dei file gestiti da Git LFS:

~~~bash
cd ~
git clone <URL_REPOSITORY>
cd <NOME_REPOSITORY>
~~~

Modelli e checkpoint sono file molto grandi. Per scaricare inizialmente solo
codice e documentazione:

~~~bash
cd ~
GIT_LFS_SKIP_SMUDGE=1 git clone <URL_REPOSITORY>
cd <NOME_REPOSITORY>
~~~

I file LFS possono essere recuperati in seguito con:

~~~bash
git lfs pull
~~~

Git LFS è un programma separato da Git. Senza Git LFS, al posto dei modelli
verranno scaricati soltanto piccoli file di riferimento. Per maggiori dettagli:
[GitHub Docs - Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).

### 3.5 Creare l'ambiente Python

Dalla cartella principale della repository:

~~~bash
bash scripts/bootstrap_ubuntu.sh
source .venv/bin/activate
~~~

Lo script:

1. verifica di essere in Linux;
2. installa uv se non è disponibile;
3. installa Python 3.12;
4. crea l'ambiente virtuale;
5. installa le versioni fissate in uv.lock;
6. esegue un primo controllo dell'installazione.

Se il progetto si trova sotto /mnt, lo script crea automaticamente l'ambiente
nel filesystem Linux. Al termine mostra il comando corretto per attivarlo.

Controllo manuale:

~~~bash
python scripts/01_check_install.py
python scripts/02_list_devices.py
~~~

MQT Predictor non può eseguire la pipeline completa finché i modelli richiesti
non sono stati addestrati oppure installati nell'ambiente. Se i modelli sono
già presenti in artifacts/models:

~~~bash
python scripts/05_sync_models.py install --component rl
python scripts/05_sync_models.py verify --component rl
~~~

Gli script di training aggiornano automaticamente sia la copia conservata nella
repository sia quella usata dall'ambiente Python. Dopo avere creato anche il
selettore ML, il gate completo per `qcompile` è:

~~~bash
python scripts/05_sync_models.py verify
python scripts/01_check_install.py --require-models
~~~

Prima del benchmark finale aggiungere `--require-frozen-targets`: questo gate
verifica i nuovi fingerprint del protocollo 2.4-v2, non quelli legacy.

### 3.6 Regole pratiche

- Eseguire i comandi dalla cartella principale della repository.
- Attivare l'ambiente prima di avviare gli script.
- Non avviare due istanze di scripts/04_train_device_selector.py sulla stessa
  cartella di cache.
- Non modificare manualmente manifest, checkpoint o circuiti compilati.
- Prima di ricreare .venv, verificare che i modelli finali siano presenti in
  artifacts/models.
- Usare Git LFS per modelli e checkpoint, non il normale Git.

## 4. Struttura della repository

~~~text
.
├── scripts/                 comandi per setup, training ed esportazione
├── datasets/                Training set e Dataset generati
├── artifacts/
│   ├── models/              modelli finali
│   ├── checkpoints/         salvataggi intermedi del training RL
│   ├── cache/               compilazioni riutilizzabili e manifest
│   └── logs/                log di training e compilazione
├── prototype/               scheletro dell'assistente LLM
├── tests/                   test automatici della pipeline e del prototipo
├── knowledge/               paper e note di studio
├── report/                  documenti di avanzamento della tesi
├── pyproject.toml           dipendenze dirette e versione Python
├── uv.lock                  versioni esatte delle dipendenze
├── .gitattributes           regole Git LFS
└── AGENTS.md                convenzioni e contesto locale del progetto
~~~

### 4.1 Script disponibili

Tutti gli esempi seguenti vanno eseguiti dalla cartella principale, con
l'ambiente attivo.

#### 01_check_install.py

Controlla Python, pacchetti installati e percorsi in cui MQT cerca i modelli.

~~~bash
python scripts/01_check_install.py
~~~

#### 02_list_devices.py

Mostra gli hardware descritti da MQT Bench:

~~~bash
python scripts/02_list_devices.py
~~~

Mostra i dettagli di un singolo hardware:

~~~bash
python scripts/02_list_devices.py --details ibm_falcon_27
~~~

#### 03_train_rl_model.py

Addestra una policy RL per una coppia hardware-metrica.

Esempio di training:

~~~bash
python scripts/03_train_rl_model.py \
  --device ibm_falcon_27 \
  --metric expected_fidelity \
  --timesteps 100000 \
  --checkpoint-every 2048 \
  --max-steps 64 \
  --bqskit-action-timeout 60 \
  --seed 0 \
  --run-name restart-240-seed0 \
  --allow-overwrite
~~~

Per riprendere da un checkpoint:

~~~bash
python scripts/03_train_rl_model.py \
  --device ibm_falcon_27 \
  --metric expected_fidelity \
  --timesteps 100000 \
  --run-name restart-240-seed0 \
  --resume-from artifacts/checkpoints/rl/ibm_falcon_27/restart-240-seed0/NOME_CHECKPOINT.zip \
  --allow-overwrite
~~~

Con `--resume-from`, `--timesteps` indica il totale desiderato, non gli step
aggiuntivi. `--training-circuits` permette di usare una cartella QASM
personalizzata. `--allow-overwrite` autorizza soltanto la sostituzione del
modello canonico al termine del training. Checkpoint e log sono isolati sotto
il nome della run; una nuova esecuzione quindi non sovrascrive i checkpoint
storici.

Lo script mantiene il profilo BQSKit leggero usato negli esperimenti e sceglie
`max_synthesis_size` dinamicamente: usa 3 soltanto quando il circuito contiene
almeno un gate a tre qubit, altrimenti conserva il limite 2. Il Training set RL
bundled contiene infatti circuiti con gate `ccx` e `cswap`: il limite 3 evita
che una di queste azioni interrompa PPO, mentre il limite 2 riduce il costo
della sintesi per gli altri circuiti. Misure e barriere non sono considerate
gate sintetizzabili. Non viene applicata alcuna patch al codice della dipendenza
dentro `.venv`; gli ID delle 22 azioni restano invariati e i checkpoint
precedenti rimangono caricabili. La sola scrittura prevista nell'ambiente è la
copia runtime del modello finale, necessaria a `qcompile`.

Prima di decidere se riprendere i checkpoint esistenti, eseguire l'audit:

~~~bash
python scripts/08_audit_rl_models.py --deep-load
~~~

L'audit restituisce codice 1 quando raccomanda un riavvio. I cinque archivi
correnti sono integri, caricabili con SB3 2.9.0 e conservano le 22 azioni e lo
stesso spazio delle osservazioni. Non sono però modelli sufficientemente
affidabili per l'esperimento:

| Device | Step salvati | Evidenza operativa disponibile |
| --- | ---: | --- |
| `ibm_falcon_27` | 100720 | 40 successi grezzi su 482 compilazioni |
| `ibm_falcon_127` | 100240 | 50 successi grezzi su 600 compilazioni |
| `ibm_heron_133` | 100480 | 0 successi su 600 compilazioni |
| `ibm_heron_156` | 100352 | 0 successi su 600 compilazioni |
| `quantinuum_h2_56` | 60000 | 1 successo su 564; il canary 2.4.0 va in timeout |

I checkpoint precedenti non sono inoltre accompagnati da compilazioni che
documentino la nuova prova di terminazione, validità sul Target e provenienza
2.4.0. La decisione per questo branch è quindi **riavviare da zero tutti e
cinque i training**, mantenendo i vecchi file come baseline storica e non come
punto di ripresa.

Lo stesso gate è applicato dagli script di training ML e validazione `qcompile`:
accettano soltanto modelli RL corredati da metadata 2.4.0 coerenti con device,
metrica, hash del modello, Target congelato e profilo BQSKit. I cinque modelli
storici restano quindi conservati, ma non possono entrare accidentalmente nel
nuovo esperimento.

Esecuzione sequenziale consigliata:

~~~bash
devices=(
  ibm_falcon_27
  ibm_heron_133
  ibm_falcon_127
  ibm_heron_156
  quantinuum_h2_56
)
for device in "${devices[@]}"; do
  python scripts/03_train_rl_model.py \
    --device "$device" \
    --metric expected_fidelity \
    --timesteps 100000 \
    --checkpoint-every 10000 \
    --max-steps 64 \
    --bqskit-action-timeout 60 \
    --seed 0 \
    --run-name restart-240-seed0 \
    --allow-overwrite || break
done
~~~

Il loop si ferma al primo errore. Ogni modello canonico viene sostituito solo
dopo il completamento della rispettiva run; i checkpoint storici nella cartella
del device non vengono sovrascritti.

#### 04_train_device_selector.py

È lo script principale. Compila ogni circuito con tutti i modelli RL
compatibili, assegna uno score a ogni risultato e costruisce il Training set.
Il modello supervisionato usa come risposta corretta l'hardware con lo score
più alto.

Per un risultato pubblicabile ogni coppia compatibile deve provenire dalla
policy RL, terminare esplicitamente con l'azione `terminate` e produrre un QASM
il cui hash corrisponda al campo `compiled_sha256` del manifest. Il circuito
deve inoltre essere eseguibile sul Target. Timeout, fallback e risultati
troncati restano nel manifest ma non diventano label.
La finalizzazione si blocca finché la copertura non è completa. Solo
`--allow-incomplete` crea un artefatto esplorativo nella staging area, senza
aggiornare il modello o il Training set canonico.

I cinque device e `expected_fidelity` sono già i default. Controllare prima
piano, Target, modelli e copertura senza scrivere:

~~~bash
python scripts/04_train_device_selector.py --dry-run
~~~

Eseguire quindi un canary piccolo. Non usare `--skip-preflight` nel run
completo finché ogni policy non ha superato almeno una compilazione:

~~~bash
python scripts/04_train_device_selector.py \
  --num-workers 1 \
  --timeout 300 \
  --rl-max-steps 64 \
  --seed 0 \
  --max-attempts 1 \
  --limit-circuits 2 \
  --compile-only
~~~

Se il canary riesce per tutti i device, completare la cache riprendibile:

~~~bash
python scripts/04_train_device_selector.py \
  --num-workers 1 \
  --timeout 300 \
  --rl-max-steps 64 \
  --seed 0 \
  --max-attempts 3 \
  --compile-only
~~~

Rieseguire lo stesso comando riprende soltanto QASM con provenienza, hash,
versione Predictor, modello RL, Target, seed e limite passi identici. I vecchi
91 risultati non hanno queste prove e vengono quindi ignorati intenzionalmente.

Con `--num-workers 1` estrazione delle feature e scoring sono eseguiti in un
ciclo sequenziale diretto, riutilizzando in cache gli oggetti device. Questo
evita sia il costo di migliaia di `deepcopy` sia l'errore secondario interno a
Joblib che in precedenza compariva dopo `Ctrl-C`.

Quando la copertura rigorosa è completa, generare Training set e modello ML:

~~~bash
python scripts/04_train_device_selector.py \
  --num-workers 1 \
  --rl-max-steps 64 \
  --seed 0 \
  --finalize-only
~~~

Parametri principali:

| Parametro | Significato |
| --- | --- |
| `--devices` | default: i cinque hardware congelati, nell'ordine del protocollo |
| `--metric` | default e metrica pubblicabile: `expected_fidelity` |
| `--num-workers` | modelli RL residenti e compilazioni parallele |
| `--timeout` | limite totale per una coppia circuito-hardware |
| `--rl-max-steps` | limite di azioni della policy per episodio |
| `--seed` | seed condiviso da policy, BQSKit e Random Forest |
| `--startup-timeout` | tempo massimo per caricare un worker RL |
| `--max-attempts` | tentativi totali per ogni coppia circuito-hardware |
| `--rf-workers` | processi usati nell'addestramento finale del classificatore |
| `--limit-circuits` | limita l'esecuzione ai primi N circuiti |
| `--compile-only` | aggiorna la cache senza creare il modello finale |
| `--finalize-only` | usa soltanto i risultati già presenti nella cache |
| `--allow-incomplete` | crea solo artefatti esplorativi, mai canonici |
| `--allow-target-drift` | bypassa il gate; il run resta fuori protocollo finché hash e ID non vengono aggiornati |
| `--export-json-only` | rigenera il JSON solo con copertura corrente completa |
| `--dry-run` | mostra piano e copertura senza scrivere |

I parametri --uncompiled-circuits, --compiled-circuits, --cache-dir, --log-dir
e --dataset-json permettono di sostituire i percorsi predefiniti.

#### 05_sync_models.py

Sincronizza esclusivamente le cinque policy RL e il selettore ML del protocollo
tra `artifacts/models` e la copia runtime nella virtualenv. Prima di copiare
verifica puntatori Git LFS, integrità ZIP, 22 azioni, spazio delle osservazioni,
classi ML, numero di feature e hash.

~~~bash
python scripts/05_sync_models.py verify
python scripts/05_sync_models.py install
~~~

Se una destinazione contiene bytes diversi, la copia viene rifiutata. Usare
`--overwrite` solo dopo aver verificato quale artefatto debba essere
autorevole. L'acquisizione inversa dalla virtualenv è eccezionale:

~~~bash
python scripts/05_sync_models.py capture --overwrite
~~~

Il normale training aggiorna già copia canonica e runtime.

#### 06_export_llm_dataset.py

Controlla i risultati della pipeline ed esporta il Dataset destinato ai futuri
esperimenti con l'LLM.

Verifica senza scrivere:

~~~bash
python scripts/06_export_llm_dataset.py --audit-only
~~~

Esportazione:

~~~bash
python scripts/06_export_llm_dataset.py --overwrite
~~~

Esempio con percorsi personalizzati:

~~~bash
python scripts/06_export_llm_dataset.py \
  --input datasets/device_selector_expected_fidelity.json \
  --output datasets/llm_mqt_full_pipeline_expected_fidelity.json \
  --overwrite
~~~

#### 07_validate_qcompile.py

Dopo il training, esegue cinque canary RL deterministici e un canary
end-to-end con l'API ufficiale `qcompile`. Ogni processo ha un timeout rigido
e il report richiede `terminate`, score finito e circuito eseguibile sul
Target:

~~~bash
python scripts/07_validate_qcompile.py --timeout 300 --max-steps 64
~~~

Finché il selettore ML non copre tutte le cinque classi, il controllo si blocca
prima dei canary senza modificare i modelli.

#### 08_audit_rl_models.py

Analizza struttura, metadati, log TensorBoard e manifest storico delle cinque
policy; con `--deep-load` verifica anche il caricamento completo dei tensori:

~~~bash
python scripts/08_audit_rl_models.py --deep-load
~~~

Un codice di uscita 1 significa che almeno una policy va riaddestrata; il report
JSON spiega separatamente integrità tecnica e qualità operativa.

Per vedere tutti i parametri disponibili per uno script:

~~~bash
python scripts/04_train_device_selector.py --help
~~~

### 4.2 Cartelle e artefatti

- datasets/ contiene i file JSON prodotti dalle pipeline. Non modificarli
  manualmente: devono poter essere rigenerati dagli script.
- artifacts/models/rl/ contiene i modelli RL finali addestrati.
- artifacts/models/ml/ contiene il classificatore supervisionato finale addestrato.
- artifacts/checkpoints/rl/ contiene salvataggi intermedi dai quali riprendere
  un training RL.
- artifacts/cache/ml/ contiene circuiti compilati e manifest usati per
  riprendere il lavoro senza ricominciare da zero.
- artifacts/logs/rl/ e artifacts/logs/ml/ contengono i log di esecuzione.
- prototype/ contiene il servizio applicativo, il filtro di compatibilità, la
  validazione della risposta LLM e la compilazione Qiskit controllata. La
  spiegazione completa è in [prototype/README.md](prototype/README.md).
- knowledge/ contiene le fonti locali e le note di studio. Alcune parti
  descrivono esperimenti storici; per i comandi correnti fa fede questo README.
- report/ contiene i documenti di avanzamento della tesi.
- tests/ contiene i test automatici. Per eseguirli senza modificare le
  dipendenze del progetto:

~~~bash
uv run --with pytest pytest -q
~~~

I log TensorBoard del training RL possono essere aperti con:

~~~bash
tensorboard --logdir artifacts/logs/rl --port 6006
~~~

### 4.3 Collaborare con Git

Per ogni modifica è consigliato creare un branch dedicato:

~~~bash
git switch -c nome-breve-modifica
git status
~~~

Versionare codice, documentazione e configurazioni con commit piccoli e
descrittivi. Evitare di aggiungere .venv, cache temporanee o nuovi file binari
grandi senza avere prima deciso dove conservarli. I file già gestiti da Git LFS
devono continuare a essere modificati tramite Git LFS.

## 5. Stato attuale della tesi

Completato:

- ambiente riproducibile Python 3.12 con MQT Predictor 2.4.0 e lock di progetto;
- protocollo `expected_fidelity` sui cinque device, con fingerprint Target
  deterministici e distinzione dagli hash legacy di `qiskit_dataset`;
- audit dei modelli di `main`: archivi tecnicamente compatibili ma qualità
  operativa insufficiente, decisione `restart_all`;
- training RL con seed, limite azioni, timeout BQSKit, resume e directory per run;
- pipeline del Training set che accetta solo compilazioni RL terminate,
  validate, integre e con provenienza coerente;
- sincronizzazione atomica dei sei artefatti richiesti da `qcompile`;
- canary isolati per cinque policy e per il flusso `qcompile`;
- esportazione controllata del Dataset LLM e test automatici.

In corso:

- nuovo training da zero delle cinque policy con Predictor 2.4.0;
- completamento delle 2846 compilazioni compatibili e training del selettore ML;
- rigenerazione dei risultati Qiskit e oracle sui Target MQT Bench 2.2.3.

Passi successivi:

1. completare e validare le cinque policy RL;
2. generare il Training set completo e il selettore ML a cinque classi;
3. superare il canary end-to-end di `qcompile`;
4. rigenerare Qiskit default, Qiskit random e oracle nello stesso protocollo;
5. confrontare MQT Predictor con LLM+RAG, LLM senza RAG, LLM di frontiera e gli
   altri competitor congelati;
6. completare Dataset, prototipo RAG, UI e valutazione finale.

## Riferimenti principali

- [MQT Predictor - documentazione stabile](https://mqt.readthedocs.io/projects/predictor/en/stable/)
- [MQT Predictor - setup e training](https://mqt.readthedocs.io/projects/predictor/en/stable/setup.html)
- [MQT Predictor 2.4.0 - release](https://github.com/munich-quantum-toolkit/predictor/releases/tag/v2.4.0)
- [MQT Predictor 2.4.0 - guida di upgrade](https://github.com/munich-quantum-toolkit/predictor/blob/v2.4.0/UPGRADING.md)
- [Installare WSL](https://learn.microsoft.com/windows/wsl/install)
- [Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)

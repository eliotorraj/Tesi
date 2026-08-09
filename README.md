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
- mqt.predictor 2.3.0;
- dipendenze fissate in pyproject.toml e uv.lock.

Lo script principale per il Training set richiede funzioni disponibili su
Linux. L'esecuzione Python nativa da Windows non è quindi supportata. Su Windows
bisogna usare WSL2. macOS non fa parte dell'ambiente verificato.

Non servono credenziali per un hardware quantistico reale. Serve una connessione
Internet durante la prima installazione delle dipendenze.

### 3.2 Risorse hardware consigliate

Questi valori sono indicazioni pratiche, non requisiti imposti da MQT:

| Risorsa | Indicazione |
| --- | --- |
| CPU | processore moderno con più core |
| RAM | almeno 8 GiB usando 2 worker; 16 GiB sono consigliati |
| Disco | almeno 20 GiB per ambiente e codice; 50 GiB o più per modelli, checkpoint e training completi |
| GPU | non obbligatoria per la pipeline corrente |

Ogni worker RL può usare diversi GiB di memoria. Se la macchina ha circa 8 GiB
di RAM, mantenere --num-workers 2.

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
python scripts/05_sync_models.py install
~~~

Gli script di training aggiornano automaticamente sia la copia conservata nella
repository sia quella usata dall'ambiente Python.

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
  --checkpoint-every 2048
~~~

Per riprendere da un checkpoint:

~~~bash
python scripts/03_train_rl_model.py \
  --device ibm_falcon_27 \
  --metric expected_fidelity \
  --timesteps 100000 \
  --resume-from artifacts/checkpoints/rl/ibm_falcon_27/NOME_CHECKPOINT.zip \
  --allow-overwrite
~~~

Nel secondo comando, --timesteps indica il numero totale desiderato, non gli
step aggiuntivi. Il parametro --training-circuits permette di usare una
cartella QASM personalizzata. --allow-overwrite è necessario se esiste già un
modello finale con lo stesso nome.

Lo script mantiene il profilo BQSKit leggero usato negli esperimenti e sceglie
`max_synthesis_size` dinamicamente: usa 3 soltanto quando il circuito contiene
almeno un gate a tre qubit, altrimenti conserva il limite 2. Il Training set RL
bundled contiene infatti circuiti con gate `ccx` e `cswap`: il limite 3 evita
che una di queste azioni interrompa PPO, mentre il limite 2 riduce il costo
della sintesi per gli altri circuiti. Misure e barriere non sono considerate
gate sintetizzabili. Non viene modificato alcun file dentro `.venv`, gli ID
delle 22 azioni restano invariati e i checkpoint precedenti rimangono
caricabili.

Per continuare il modello `quantinuum_h2_56` esistente fino a 100000 step:

~~~bash
python scripts/03_train_rl_model.py \
  --device quantinuum_h2_56 \
  --metric expected_fidelity \
  --timesteps 100000 \
  --checkpoint-every 10000 \
  --resume-from artifacts/checkpoints/rl/quantinuum_h2_56/model_expected_fidelity_quantinuum_h2_56_8192_steps.zip \
  --allow-overwrite
~~~

#### 04_train_device_selector.py

È lo script principale. Compila ogni circuito con tutti i modelli RL
compatibili, assegna uno score a ogni risultato e costruisce il Training set.
Il modello supervisionato usa come risposta corretta l'hardware con lo score
più alto.

Se una compilazione fallisce, lo script assegna a quella coppia lo score minimo
-1.0 e continua. Se tutti i modelli falliscono per lo stesso circuito, quel
circuito non viene usato per addestrare il classificatore.

Esecuzione completa:

~~~bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --num-workers 2 \
  --timeout 300
~~~

Lo script è riprendibile: rieseguendo lo stesso comando, i risultati RL validi
già presenti nella cache non vengono compilati di nuovo.

Controllare il piano senza scrivere file:

~~~bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --dry-run
~~~

Provare pochi circuiti senza addestrare il modello finale:

~~~bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --limit-circuits 5 \
  --compile-only
~~~

Generare Training set e modello usando la cache esistente:

~~~bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --finalize-only
~~~

Rigenerare soltanto il file JSON dagli array già installati:

~~~bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --export-json-only
~~~

Parametri principali:

| Parametro | Significato |
| --- | --- |
| --devices | hardware da confrontare; richiede una policy RL per ciascuno |
| --metric | expected_fidelity oppure critical_depth |
| --num-workers | compilazioni RL eseguite in parallelo |
| --timeout | tempo massimo per una compilazione circuito-hardware |
| --startup-timeout | tempo massimo per caricare un worker RL |
| --max-attempts | tentativi totali per ogni coppia circuito-hardware |
| --rf-workers | processi usati nell'addestramento finale del classificatore |
| --limit-circuits | limita l'esecuzione ai primi N circuiti |
| --compile-only | esegue la compilazione senza creare il modello finale |
| --finalize-only | usa soltanto i risultati già presenti nella cache |
| --export-json-only | rigenera soltanto il JSON |
| --dry-run | mostra piano e copertura senza scrivere |

I parametri --uncompiled-circuits, --compiled-circuits, --cache-dir, --log-dir
e --dataset-json permettono di sostituire i percorsi predefiniti.

#### 05_sync_models.py

Sincronizza i modelli finali tra artifacts/models e la copia interna in .venv usata da
MQT Predictor.

Installare nell'ambiente .venv i modelli conservati nella repository: (artifacts/models ---> .venv/lib/python3.12/site-packages/mqt/predictor/rl/training_data/training_model/)

~~~bash
python scripts/05_sync_models.py install
~~~

Acquisire eccezionalmente modelli già presenti nell'ambiente: (.venv/lib/python3.12/site-packages/mqt/predictor/rl/training_data/training_model/  ---> artifacts/models)

~~~bash
python scripts/05_sync_models.py capture --overwrite
~~~

L'azione capture non è necessaria dopo il normale training, perché gli script
aggiornano già entrambe le copie.

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

- ambiente riproducibile basato su Python 3.12 e MQT Predictor 2.3.0;
- script per training, checkpoint e ripresa dei modelli RL;
- pipeline resistente agli errori per costruire il Training set e addestrare il
  selettore hardware;
- assegnazione dello score minimo alle compilazioni RL fallite, senza
  interrompere l'intera elaborazione;
- esportazione controllata dei dati per i successivi esperimenti LLM;
- scheletro del prototipo con analisi del circuito, filtro di compatibilità,
  validazione e compilazione Qiskit dopo conferma;
- test automatici per le parti principali introdotte nella repository.

In corso:

- rigenerazione del Training set e del modello supervisionato con la nuova
  pipeline basata soltanto sui risultati RL validi;
- verifica sperimentale dei modelli e degli artefatti prodotti.

Passi successivi:

1. valutare il modello supervisionato ottenuto;
2. completare e verificare il Dataset per l'LLM;
3. collegare al prototipo una ricerca RAG sul Dataset;
4. scegliere il servizio LLM e implementare il relativo collegamento;
5. realizzare la UI e valutare il sistema completo.

## Riferimenti principali

- [MQT Predictor - documentazione stabile](https://mqt.readthedocs.io/projects/predictor/en/stable/)
- [Installare WSL](https://learn.microsoft.com/windows/wsl/install)
- [Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)

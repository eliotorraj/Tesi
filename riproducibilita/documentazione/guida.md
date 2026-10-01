# Dalla prima configurazione al proprio prototipo

Questa guida accompagna una nuova esecuzione su Linux, dalla scelta degli ingressi al Test. Le impostazioni si cambiano con `configura.py`: il programma scrive i JSON, controlla i valori e conserva le revisioni.

Se vuoi soltanto provare il sistema già selezionato, parti dalla [guida del prototipo](../../prototipo/docs/guida_passo_passo.md). Questo kit serve invece a generare un nuovo Dataset, scegliere le impostazioni sulla validation e costruire un altro prototipo. Circuiti nuovi, pesi GGUF, driver ed eseguibile llama.cpp devono essere forniti da chi usa il kit.

Il percorso principale usa un esperimento chiamato `prova-cpu`, con Qwen e tre sistemi Test. È un punto di partenza ridotto per imparare i comandi. I limiti sono espliciti: una GPU adeguata è consigliata e 16 GB di RAM non garantiscono che tutti i circuiti, modelli e contesti possano essere elaborati. Una compilazione con un solo Target e una sola configurazione non è un confronto significativo fra scelte alternative. Quando il percorso funziona, duplica l'esperimento e amplia il catalogo.

## Come leggere i comandi della guida

I due programmi principali sono file Python nella cartella `riproducibilita/`: **`configura.py`** serve a scegliere e modificare le impostazioni; **`esperimento.py`** serve a eseguire le fasi della prova. Dopo il nome dello script si specificano l'azione da svolgere e gli eventuali parametri.

Per esempio, al punto 5 eseguiremo questo comando, dopo avere installato l'ambiente e scelto gli ingressi:

```bash
python esperimento.py --esperimento prova-cpu prepara
```

| Parte del comando | Significato |
| --- | --- |
| `python` | Avvia l'interprete Python dell'ambiente attivato. |
| `esperimento.py` | È lo script da eseguire, presente nella cartella del kit. |
| `--esperimento prova-cpu` | Indica quale configurazione nominata usare. |
| `prepara` | È il sottocomando, cioè l'azione richiesta allo script. |

**`prepara` è quindi un comando di `esperimento.py`.** Controlla gli ingressi e salva circuiti, catalogo e impostazioni di riferimento per quella prova. Nella guida chiamiamo questa operazione «congelamento»: la prova viene associata a condizioni precise, così i passaggi successivi possono accorgersi se vengono cambiate. Per provare condizioni diverse si usa un altro nome, anche duplicando la configurazione.

Quando trovi scritto «prima di `prepara`», significa **prima di eseguire quel comando nel terminale**. La configurazione con `configura.py` viene prima; generazione del Dataset, addestramento e valutazione vengono dopo. Puoi vedere le azioni disponibili con `python esperimento.py --help` e leggere la spiegazione della preparazione con `python esperimento.py prepara --help`.

## 1. Installare e controllare l'ambiente Linux

Servono Linux/Ubuntu o Ubuntu in WSL, Python 3.12, `uv`, Node.js 22/npm e un eseguibile llama.cpp compatibile. Per installarli consulta i [prerequisiti Linux](../../prototipo/docs/guida_passo_passo.md#a2-installare-i-prerequisiti) e la [compilazione CPU di llama.cpp b10930](../../prototipo/docs/guida_passo_passo.md#a4-preparare-llamacpp-per-cpu); per GPU consulta i [backend Linux](../../prototipo/docs/installazione_e_runtime.md#gpu-su-linux).

Dalla radice del clone:

```bash
cd riproducibilita
bash setup.sh
source .venv/bin/activate
python esperimento.py verifica
```

**Da qui tutti i comandi partono da `riproducibilita/`, con l'ambiente attivato.** In un nuovo terminale bisogna entrare di nuovo nel kit e ripetere `source .venv/bin/activate`. Se preferisci non attivarlo, sostituisci `python` con `.venv/bin/python`.

`setup.sh` usa il lock delle dipendenze, con MQT Predictor 2.4.0, e installa TOON dal lock npm. Non scarica pesi, non addestra e non ricrea un ambiente esistente. Prima di ricostruire una `.venv` conserva i modelli MQT canonici e quelli installati nel pacchetto. Node deve essere nel PATH; `PROTOTIPO_NODE` permette di indicare il suo eseguibile.

## 2. Creare una configurazione con un nome

```bash
python configura.py nuovo prova-cpu --profilo cpu --modelli qwen \
  --sistemi llm_rag llm_senza_rag random
python configura.py mostra prova-cpu
```

Il comando crea `configurazioni/esperimenti/prova-cpu/` e lascia intatti i valori distribuiti. Puoi tenere più esperimenti contemporaneamente. `mostra` spiega quali modelli sono attivi, dove si cercano i file, dove finiranno i risultati e quante compilazioni prevede al massimo la griglia.

Il profilo CPU imposta contesto 16.384, risposta massima 4.096 token, batch 128, microbatch 64, zero strati GPU e un processo Qiskit. Non riduce da solo circuiti, Target, configurazioni o temperature. Per questo primo percorso riduciamo esplicitamente la griglia:

```bash
python configura.py dispositivi prova-cpu ibm_falcon_27
python configura.py compilazioni prova-cpu o2_default_default
python configura.py parametri prova-cpu --temperature 0
```

Restano i tre seed di compilazione richiesti dal protocollo. Con il corpus distribuito si ottengono al massimo 1.530 compilazioni train/validation prima dei filtri di compatibilità: anche una griglia ridotta non è una prova istantanea. Per imparare con pochi circuiti puoi fornire un corpus più piccolo nel passaggio seguente.

### Se usi una GPU o il fisso

Ci sono **due profili**, che scelgono dove eseguire il LLM:

| Profilo | Dove si eseguono i calcoli del LLM | Dove vengono mantenuti i pesi |
| --- | --- | --- |
| `cpu` | CPU | RAM del computer |
| `gpu` | GPU per gli strati trasferiti, con CPU di supporto | VRAM della scheda per gli strati trasferiti; resta necessario usare anche RAM |

Con `gpu` il server richiede di trasferire tutti gli strati possibili sulla scheda (`gpu_layers=999`). Il numero 999 è un modo per richiedere tutti gli strati, non il numero effettivo di strati del modello. Questa impostazione non garantisce che qualsiasi GGUF entri nella VRAM. Se la memoria non basta, il caricamento può fallire: puoi scegliere un modello più piccolo o impostare esplicitamente meno strati GPU. In quest'ultimo caso parte del modello resta sulla CPU e usa la RAM. La memoria serve anche al contesto e alle strutture di lavoro, oltre che ai pesi.

I due profili partono dalle **stesse altre impostazioni**: contesto 16.384 token, risposta massima 4.096, batch 128, microbatch 64 e un processo Qiskit. Contesto e parallelismo si regolano separatamente con `modello --contesto` e `risorse --processi`, prima di `prepara`. I processi Qiskit riguardano CPU e RAM per le compilazioni del Dataset; non indicano quante richieste LLM vengono eseguite in parallelo.

Per un nuovo computer con GPU:

```bash
python configura.py nuovo prova-gpu --profilo gpu
```

Anche il fisso usa il profilo `gpu`. Se vuoi assegnargli il contesto esteso e il parallelismo del riferimento, dichiarali esplicitamente:

```bash
python configura.py nuovo prova-fisso --profilo gpu
python configura.py modello prova-fisso qwen --contesto 60000
python configura.py risorse prova-fisso --processi 6 --batch 512 --microbatch 128
```

Questi valori non vengono scelti automaticamente dal tipo di computer o dal modello di scheda. Prima di usarli verifica che le risorse siano adeguate. Nei passaggi successivi sostituisci `prova-cpu` con il nome scelto.

Tutti i profili partono dal trasporto Linux `native`. Se sul fisso mantieni il server Windows e il client WSL, indica per Qwen il percorso WSL del GGUF e il trasporto:

```bash
python configura.py modello prova-fisso qwen \
  --file /mnt/d/percorso/Qwen3.5-4B-Q8_0.gguf --trasporto windows
```

Avvia poi Qwen con gli script del [percorso personale](../../prototipo/docs/guida_passo_passo.md#percorso-b--elio-fisso-con-gpu-e-client-wsl). I `.ps1` e i sensori del fisso restano disponibili. Questi avviatori sono specifici del loro modello: per altri LLM serve un avvio coerente con il candidato. `esperimento.py server` avvia eseguibili Linux; il suo `--controlla` può verificare anche il server Windows attraverso `curl.exe`.

## 3. Decidere quali circuiti usare

Puoi mantenere il corpus distribuito: 422 train, 88 validation e 90 test. In questo caso non serve alcun comando. I 422 train contengono 396 contenuti byte-distinti; il kit conserva anche gli alias.

Per usare i tuoi circuiti, prepara una directory con tre sottocartelle e collegala:

```bash
python configura.py circuiti prova-cpu --cartella "$HOME/circuiti-prova" --crea
```

`--crea` crea soltanto `train/`, `validation/` e `test/` se mancano. Metti i QASM direttamente nelle rispettive cartelle, poi controlla il riepilogo. Il programma non scarica circuiti, non decide come dividerli e non cambia quelli distribuiti. I nomi devono essere univoci fra split e ciascuno split deve contenere almeno un circuito.

Non mettere lo stesso circuito in train e test con nomi diversi. `prepara` verifica contenuto e sequenza delle istruzioni, ma non può dimostrare ogni possibile equivalenza quantistica o indipendenza fra famiglie. I cinquanta QASMBench in `circuiti/esterni/` restano un corpus separato: se vuoi usarli, copia gli ingressi desiderati nella tua nuova suddivisione, conservando la provenienza.

## 4. Collegare il GGUF e llama.cpp

Per conoscere le fonti dei modelli di riferimento:

```bash
python configura.py disponibili modelli
```

Scarica autonomamente il GGUF della revisione indicata, rispettandone la licenza. Puoi metterlo in `modelli_llm/qwen/modello.gguf` oppure collegare un file già presente, anche su un altro disco:

```bash
python configura.py modello prova-cpu qwen --file /percorso/Qwen3.5-4B-Q8_0.gguf
python configura.py risorse prova-cpu --server-bin /percorso/llama-server --threads 6
```

Sostituisci i percorsi con quelli reali. Per `qwen`, `phi` e `gemma` resta l'impronta del GGUF di riferimento: cambiare percorso non autorizza silenziosamente pesi diversi. Se vuoi un'altra quantizzazione o un altro LLM, usa `aggiungi-modello`, descritto nel [ricettario di configurazione](configurazione.md#registrare-un-altro-llm).

Con GPU puoi vedere i dispositivi realmente esposti dal tuo eseguibile senza caricare il modello:

```bash
python esperimento.py --esperimento prova-gpu server qwen --list-devices
python configura.py risorse prova-gpu --device ID_RESTITUITO_DAL_COMANDO
```

Il numero `999` chiede di trasferire tutti gli strati disponibili; non dimostra che siano stati caricati sulla GPU. Controlla il registro del server. Non serve sostituire nel codice il nome della Radeon con quello di un'altra scheda.

## 5. Controllare le scelte e preparare l'esperimento

Se vuoi salvare gli output altrove, stabiliscilo adesso. Il percorso rimarrà associato all'esperimento:

```bash
python configura.py risorse prova-cpu --risultati /percorso/risultati
```

Altrimenti gli output restano nelle aree del kit, separati per nome. Rileggi le scelte e verifica gli ingressi:

```bash
python configura.py mostra prova-cpu
python configura.py verifica prova-cpu
```

`verifica` controlla split, nomi, duplicati byte-identici, presenza dei candidati e impronte GGUF; segnala anche gli eseguibili mancanti. Non avvia inferenza e non congela nulla. Per file grandi il calcolo SHA-256 richiede tempo. La verifica non certifica che la memoria sia sufficiente né che un GGUF arbitrario sia compatibile con llama.cpp.

Quando gli ingressi sono pronti:

```bash
python esperimento.py --esperimento prova-cpu prepara
python esperimento.py --esperimento prova-cpu stato
```

Il primo comando richiama la funzione `prepare()` di [comune/corpus.py](../comune/corpus.py). Controlla le versioni installate, i Target e la separazione fra train, validation e test; legge i QASM ed estrae 49 caratteristiche. Salva poi, sotto `esecuzioni/prova-cpu/` nella radice risultati scelta:

- `circuits/`: copie dei circuiti assegnati alla prova;
- `manifest.json`: elenco dei circuiti con caratteristiche, provenienza, split e impronte;
- `catalogo.json`: dispositivi quantistici e configurazioni Qiskit della prova;
- `contratto.json` e `ingressi_sigillati.json`: impostazioni e impronte con cui i passaggi successivi controllano l'integrità.

Questa è la preparazione degli ingressi. Le compilazioni che generano il Dataset e gli addestramenti si eseguono con i comandi dei punti successivi. **Da quando viene scritto il contratto, la configurazione non si modifica con il configuratore**, anche se una fase successiva della preparazione incontra un errore. Il comando `stato` aiuta a vedere se la preparazione è completa. Per cambiare una scelta:

```bash
python configura.py duplica prova-cpu prova-cpu-02
python configura.py parametri prova-cpu-02 --temperature 0 0.4 0.7
```

La copia eredita le impostazioni e i percorsi degli ingressi, senza copiare risultati o riusare un addestramento come nuovo. Anche se eredita la stessa radice di output, le sottocartelle useranno il nuovo nome. Conserva l'ambiente e i sorgenti per riprendere una prova: cambiare il codice dopo il congelamento può rendere incompatibile la ripresa.

`stato` resta consultabile in qualunque momento. Mostra gli artefatti presenti, conta gli esiti Test e suggerisce il passaggio successivo. Un file presente non è da solo una certificazione di successo: le singole fasi eseguono i controlli d'integrità.

## 6. Preparare MQT soltanto se incluso nei sistemi Test

Il percorso `prova-cpu` non include `mqt`, quindi passa al punto 7. Per prevederlo in un'altra campagna, aggiungilo con `configura.py sistemi` **prima di `prepara`**. Il comando sostituisce l'intero elenco, per esempio:

```bash
python configura.py sistemi altra-prova llm_rag llm_senza_rag random mqt
```

L'installazione di MQT da sola non fornisce politiche RL addestrate e selettore. Dopo `prepara`, addestra una politica per **ogni** dispositivo selezionato; il riepilogo o `hardware` mostrano quali:

```bash
python esperimento.py --esperimento altra-prova hardware
python esperimento.py --esperimento altra-prova mqt rl --device ibm_falcon_27
```

Ripeti l'ultimo comando per gli altri Target del tuo catalogo. Sono addestramenti reali, potenzialmente lunghi. I 100.000 passi richiesti diventano normalmente 100.352 al completamento del rollout PPO. Checkpoint e modelli vanno in `mqt/artefatti/<nome>/`. Pochi passi possono controllare la meccanica, ma non dimostrano qualità della compilazione.

Completate le politiche:

```bash
python esperimento.py --esperimento altra-prova mqt selettore --dry-run
python esperimento.py --esperimento altra-prova mqt selettore --compile-only --num-workers 1
python esperimento.py --esperimento altra-prova mqt selettore --finalize-only --num-workers 1
python esperimento.py --esperimento altra-prova mqt verifica
python esperimento.py --esperimento altra-prova test tecnico-mqt
```

La raccolta produce compilazioni circuito/dispositivo; la finalizzazione costruisce Training set e array, sceglie gli iperparametri e addestra il selettore. Mantieni gli stessi parametri fra le due fasi. `mqt selettore --num-workers 1` può svolgerle entrambe. La prova tecnica usa un Bell sintetico senza leggere Test.

Le opzioni dei trainer sono in `mqt rl -- --help` e `mqt selettore -- --help`. Gli addestramenti devono usare la `.venv` del kit; sono protetti da modifiche accidentali all'ambiente della vecchia repository. I processi del trainer si impostano con `--num-workers`: `configura.py risorse --processi` riguarda la generazione Qiskit del Dataset.

## 7. Generare Dataset e matrice validation

```bash
python esperimento.py --esperimento prova-cpu dataset
```

Il comando compila train e validation sulle coppie compatibili, le configurazioni e i tre seed. Conserva errori, timeout e QASM compilati. Le mediane richiedono tre seed riusciti per quella configurazione. Gli esempi RAG e la normalizzazione provengono soltanto da train.

I tentativi sono in `dataset/artefatti/<nome>/`; il pacchetto train usato nelle decisioni è in `esecuzioni/<nome>/data/`. Questi percorsi partono dalla radice di output scelta. Per separare il lavoro usa `dataset --split train` e `dataset --split validation`. Il sigillo si crea quando entrambi hanno tutti i tentativi registrati, compresi i fallimenti. `dataset --aggrega` ricostruisce gli aggregati senza compilare.

Una ripresa avvia soltanto i tentativi mai iniziati. Le esecuzioni interrotte senza esito diventano terminali: il sistema non elimina fallimenti per riprovare con lo stesso nome.

## 8. Eseguire la validation e scegliere il candidato

```bash
python esperimento.py --esperimento prova-cpu validation congela
python esperimento.py --esperimento prova-cpu server qwen
```

Il primo comando verifica tutti i GGUF attivi e congela la griglia. Il secondo avvia il server con percorso, contesto, batch, thread e strati GPU già salvati. In `prova-cpu` gli strati GPU sono zero; non occorre aggiungere l'opzione a ogni avvio. Il terminale rimane occupato e i registri sono in `esecuzioni/<nome>/servers/`.

Apri un secondo terminale, entra nel kit e attiva la stessa `.venv`. Attendi che il modello sia caricato, poi controlla:

```bash
python esperimento.py --esperimento prova-cpu server qwen --controlla
python esperimento.py --esperimento prova-cpu validation esegui --modello qwen
```

`--controlla` verifica l'identità del GGUF e il contesto esposto dal server, senza inviare un prompt. Se il server si sta ancora caricando, attendi e ripeti il controllo. Se non parte, consulta soprattutto `stderr.log` della sua cartella di registri.

Con più LLM: termina il server corrente con Ctrl+C, avvia quello successivo e ripeti `validation esegui --modello ID`. Il comando prova tutte le temperature configurate per quell'ID. La porta predefinita è condivisa: avvia un candidato per volta.

Dopo aver eseguito **tutti i candidati attivi**:

```bash
python esperimento.py --esperimento prova-cpu validation seleziona
python esperimento.py --esperimento prova-cpu validation report
python esperimento.py --esperimento prova-cpu stato
```

Le decisioni sono sigillate prima di leggerne gli score. Il criterio predefinito privilegia copertura, minore regret mediano sui circuiti comuni, meno correzioni/chiamate, tempi e token quando completi, infine ordine lessicografico. Il riferimento è la migliore mediana osservata fra coppie eleggibili, non un ottimo teorico. Sono conservati anche candidati scartati e denominatori. Con un solo candidato non si confrontano alternative, ma restano le misure sulla validation.

Se hai incluso `llm_wl` o `llm_wl_sintesi`, prima del Test esegui anche:

```bash
python esperimento.py --esperimento prova-cpu validation wl
```

Questa fase seleziona la profondità del recupero strutturale usando train e validation, senza inferenza LLM e senza Test.

## 9. Congelare ed eseguire Test

Avvia il server del modello selezionato. Per MQT devono essere pronti anche modelli e prove tecniche; per WL serve la selezione del recupero. Il percorso iniziale include questi tre sistemi:

```bash
python esperimento.py --esperimento prova-cpu test congela
python esperimento.py --esperimento prova-cpu test esegui --metodo llm_rag
python esperimento.py --esperimento prova-cpu test esegui --metodo llm_senza_rag
python esperimento.py --esperimento prova-cpu test esegui --metodo random
python esperimento.py --esperimento prova-cpu test analizza
```

Esegui soltanto i sistemi che hai dichiarato, preferibilmente in sequenza per confrontare i tempi. Le varianti disponibili sono descritte da `configura.py disponibili sistemi`. Il kit richiede la selezione sulla validation prima di congelare Test, anche se l'elenco contiene soltanto Random o MQT.

Ogni circuito conserva un esito; errori, timeout e interruzioni non vengono nascosti. Per gli LLM si registrano prompt, evidenze, richieste, risposte, correzioni e token misurabili. Gli score mancanti non diventano zero e i confronti appaiati indicano i circuiti comuni.

`test oracle` è facoltativo: genera una griglia di riferimento separata, mai letta dai decisori. Può costare molte più compilazioni di un sistema singolo. Non è necessario per completare questo percorso.

I report sono in `test/risultati/<nome>/report/`. JSON e CSV non richiedono LaTeX. Il `report.tex` autonomo si compila dalla sua cartella con `pdflatex -halt-on-error report.tex`; serve una distribuzione LaTeX con PGFPlots. Il report validation include anche una figura generata dai dati.

## 10. Esportare e ritrovare il lavoro

```bash
python esperimento.py --esperimento prova-cpu esporta /percorso/nuovo-prototipo
python configura.py elenca
```

La destinazione dell'esportazione deve essere nuova. Riceve framework, Dataset train, catalogo e configurazione selezionata, senza pesi GGUF né score validation/Test. Ha README e setup propri e funziona senza il kit. La temperatura scelta viene conservata. `prototipo/` distribuito nella repository rimane autonomo.

Conserva configurazioni, revisioni, codice, lock, tutte le cartelle dei risultati e i pesi o fonti verificabili. Il kit non fa commit né push: gli output e i pesi restano locali. Per modificare catalogo, modelli, griglie e risorse consulta il [ricettario](configurazione.md). Per capire i moduli leggi la [mappa](mappa.md); per interpretare scientificamente il confronto leggi le [condizioni](condizioni.md).

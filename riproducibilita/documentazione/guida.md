# Eseguire una nuova campagna su Linux

## 1. Preparare l'ambiente

Questa guida serve a rigenerare dati, addestrare MQT, scegliere LLM e misurare i metodi. Per provare soltanto il framework già selezionato usare la [guida del prototipo](../../prototipo/docs/guida_passo_passo.md): comprende il nuovo utente Linux CPU e il fisso con GPU.

Il kit richiede Linux/Ubuntu o Ubuntu in WSL, Python 3.12, `uv`, Node.js 22/npm e un eseguibile llama.cpp compatibile. Su un computer nuovo seguire i [prerequisiti Linux](../../prototipo/docs/guida_passo_passo.md#a2-installare-i-prerequisiti). Per compilare llama.cpp b10930 vedere la [procedura CPU](../../prototipo/docs/guida_passo_passo.md#a4-preparare-llamacpp-per-cpu) o i [backend GPU](../../prototipo/docs/installazione_e_runtime.md#gpu-su-linux). È ammessa una compilazione esterna al progetto: passarne il percorso con `--bin`. I comandi del kit non dipendono dal client del prototipo.

Una GPU compatibile è consigliata per Qwen e gli altri LLM. **16 GB di RAM non garantiscono l'intera campagna**: compilazioni Qiskit, addestramento, inferenza e report hanno carichi diversi. I valori distribuiti, compreso contesto 60.000 e tre modelli Q8_0, non sono un profilo ridotto CPU. Prima di congelare la configurazione scegliere numero di processi, candidati, contesto e batch in base alle risorse.

Dalla radice del clone, entrare nel kit e prepararlo:

```bash
cd riproducibilita
bash setup.sh
.venv/bin/python -B esperimento.py verifica
.venv/bin/python -B esperimento.py hardware
```

**Tutti i comandi successivi partono da `riproducibilita/`.** `verifica` controlla l'ambiente; `hardware` mostra i Target quantistici e le impronte, non la GPU del PC. `setup.sh` usa `uv sync --frozen` con MQT Predictor 2.4.0 e installa TOON dal lock npm. Non scarica GGUF, non addestra e non ricrea una `.venv` già presente. Prima di ricostruirla conservare i modelli MQT installati e quelli canonici.

Node 22 deve essere nel PATH; in alternativa `PROTOTIPO_NODE` indica il suo eseguibile. I pesi dei candidati si scaricano dagli URL di `modelli_llm/provenienza_originale.json`, rispettandone licenze e revisioni, o si forniscono autonomamente. Una prova con server simulato è disponibile con `.venv/bin/python -B verifiche/checks.py` e non richiede pesi.

## 2. Scegliere gli ingressi

Modificare `configurazioni/esperimento.json`, `configurazioni/catalogo.json` e `modelli_llm/modelli.json` prima di `prepara`.

- Assegnare un `experiment_id` nuovo, per esempio `mio-corpus-01`.
- Lasciare i QASM distribuiti oppure sostituire train, validation e test. Usare nomi univoci fra split.
- Nel registro mantenere soltanto i modelli da provare. Indicare file, provenienza/revisione, precisione, temperature, contesto e budget. Per un nuovo GGUF sostituire anche l'hash atteso.
- Scegliere `test_methods`. Se non si intende addestrare MQT, eliminare `mqt` prima del congelamento.
- Nel catalogo impostare `execution_policy.workers` secondo la RAM disponibile, per esempio 1 per una macchina limitata. Per confrontare i tempi eseguire i metodi Test in sequenza.

Per una nuova prova **CPU** limitata si può mantenere solo Qwen nel registro, impostare `context: 16384`, `max_output_tokens: 4096`, `server.batch_size: 128`, `server.ubatch_size: 64` e `transport: "native"`. Ridurre la griglia delle temperature se non serve confrontarle tutte. Queste impostazioni vanno dichiarate prima della prova e non garantiscono che tutti i circuiti entrino nel contesto; un fallimento resta un esito. Per la prima verifica su un PC da 16 GB è preferibile il Bell del prototipo.

Sul **fisso con server Windows**, il client del kit resta in WSL. Per il candidato Qwen impostare `transport: "windows"`, contesto 60.000 e il percorso GGUF leggibile da WSL, per esempio sotto `/mnt/d/`. Il server si avvia come nel [percorso personale](../../prototipo/docs/guida_passo_passo.md#percorso-b--elio-fisso-con-gpu-e-client-wsl). Gli avviatori Qwen non avviano automaticamente Phi e Gemma: per una griglia con più modelli occorrono server adeguati a ciascun candidato oppure il percorso Linux generico.

I percorsi relativi degli ingressi sono risolti rispetto a `riproducibilita/`. Il campo `file` dei GGUF è relativo al registro LLM. Si possono usare percorsi assoluti. `--config` e `--output` precedono il sottocomando:

```bash
.venv/bin/python -B esperimento.py --config /percorso/esperimento.json --output /disco/risultati prepara
```

Ripetere gli stessi parametri nei comandi successivi. Il server separato legge le stesse impostazioni attraverso le variabili `RIPRO_CONFIG` e `RIPRO_OUTPUT`, per esempio:

```bash
RIPRO_CONFIG=/percorso/esperimento.json RIPRO_OUTPUT=/disco/risultati \
  .venv/bin/python -B modelli_llm/server.py qwen --bin /percorso/llama-server --gpu-layers 999
```

Gli esempi seguenti usano i percorsi predefiniti.

## 3. Congelare corpus e Target

```bash
.venv/bin/python -B esperimento.py prepara
```

Il comando verifica versioni e Target, estrae 49 caratteristiche, controlla duplicati fra split e crea copie sotto `esecuzioni/<id>/circuits/`. Produce manifest, catalogo e impronte. Gli ingressi distribuiti sono 422 train, 88 validation e 90 test; i 422 train corrispondono a 396 contenuti distinti. Un corpus nuovo può avere altre dimensioni.

Una modifica di codice, configurazione o copie congelate blocca la ripresa: usare un nuovo identificativo e conservare la precedente esecuzione. `manifest_originale.json` è un riferimento di provenienza, non va riscritto quando si cambiano gli ingressi.

## 4. Preparare MQT, se previsto

Addestrare una politica per ciascun dispositivo nel catalogo:

```bash
.venv/bin/python -B esperimento.py mqt rl --device ibm_falcon_27
.venv/bin/python -B esperimento.py mqt rl --device ibm_heron_133
.venv/bin/python -B esperimento.py mqt rl --device ibm_falcon_127
.venv/bin/python -B esperimento.py mqt rl --device ibm_heron_156
.venv/bin/python -B esperimento.py mqt rl --device quantinuum_h2_56
```

Sono addestramenti reali, potenzialmente lunghi. I 100.000 passi richiesti diventano normalmente 100.352 al completamento del rollout PPO. Checkpoint, modelli e metadati vanno in `mqt/artefatti/<id>/`. Un modello addestrato per pochi passi controlla la meccanica, non la qualità della compilazione.

Dopo tutte le politiche:

```bash
.venv/bin/python -B esperimento.py mqt selettore --dry-run
.venv/bin/python -B esperimento.py mqt selettore --compile-only --num-workers 1
.venv/bin/python -B esperimento.py mqt selettore --finalize-only --num-workers 1
.venv/bin/python -B esperimento.py mqt verifica
.venv/bin/python -B esperimento.py test tecnico-mqt
```

La prima fase raccoglie compilazioni circuito/dispositivo. La seconda genera Training set e array, seleziona gli iperparametri e addestra il classificatore. Conservare gli stessi parametri operativi fra le fasi. In alternativa `mqt selettore --num-workers 1` svolge entrambe. La prova finale usa un Bell sintetico, una volta per politica e una volta per selettore+RL, senza leggere Test.

Le opzioni complete sono visibili con `esperimento.py mqt rl -- --help` e `esperimento.py mqt selettore -- --help`. Non usare bypass o sovrascritture per mescolare esperimenti. L'installazione dei modelli richiede la `.venv` interna al kit e protegge il vecchio ambiente della repository.

## 5. Generare Dataset e matrice validation

```bash
.venv/bin/python -B esperimento.py dataset
```

Si compilano train e validation sulle coppie compatibili, le configurazioni e i tre seed. Si conservano anche errori, timeout e QASM compilati. Le mediane si calcolano sulle configurazioni con tutti e tre i seed riusciti; gli esempi RAG e la normalizzazione provengono solo da train.

I tentativi sono in `dataset/artefatti/<id>/`; il pacchetto train da leggere nelle decisioni è in `esecuzioni/<id>/data/`. Nessun risultato Test entra nel Dataset. Per separare il lavoro usare `dataset --split train` e `dataset --split validation`. Il sigillo viene creato quando entrambi hanno tutti i tentativi registrati, inclusi i fallimenti. `dataset --aggrega` rilegge i registri senza compilare.

Una ripresa avvia soltanto i tentativi mai iniziati. I lavori interrotti senza esito diventano terminali: non si cancellano risultati sfavorevoli per riprovare sotto lo stesso identificativo.


## 6. Selezionare LLM e temperatura

Inserire i GGUF oppure indicarne i percorsi nel registro. Poi:

```bash
.venv/bin/python -B esperimento.py validation congela
```

Il comando richiede tutti i candidati, calcola le impronte e congela la griglia. In un terminale separato avviare il primo server:

```bash
.venv/bin/python -B modelli_llm/server.py qwen --bin /percorso/llama-server --gpu-layers 999
```

Sostituire `/percorso/llama-server` con il proprio eseguibile Linux. `--gpu-layers 999` richiede l'accelerazione degli strati: controllare in `stderr.log` cosa il backend carica realmente. Per CPU usare `--gpu-layers 0`; contesto e batch restano quelli già dichiarati nel registro. Per scegliere una GPU, elencarla e usare il suo identificativo:

```bash
.venv/bin/python -B modelli_llm/server.py --bin /percorso/llama-server --list-devices
```

Aggiungere `--device ID` all'avvio se occorre scegliere tra più schede. Non ci sono nomi Radeon fissi né controlli termici AMD in questo avviatore. La compatibilità dipende da driver, backend e memoria disponibile.

Lasciare il terminale aperto; i log sono in `esecuzioni/<id>/servers/`. In un secondo terminale, sempre dal kit, attendere il caricamento:

```bash
curl --fail http://127.0.0.1:8089/health
```

Per il server Windows usare `curl.exe`. Attendere `status: ok`, poi:

```bash
.venv/bin/python -B esperimento.py validation esegui --modello qwen
```

Fermare il server con Ctrl+C, avviare il candidato successivo e ripetere il comando con il suo identificativo. Il programma verifica GGUF e contesto del server. Con server su Windows e client WSL usare `transport: "windows"` nel registro e un avvio Windows equivalente; il trasporto predefinito `native` usa il server Linux/WSL.

Dopo tutti i candidati:

```bash
.venv/bin/python -B esperimento.py validation seleziona
.venv/bin/python -B esperimento.py validation report
```

Le decisioni sono sigillate prima della valutazione sugli score. Il criterio predefinito privilegia maggiore copertura di scelte valide e compilabili, minore regret mediano sui circuiti comuni, meno correzioni e chiamate, tempi/token se completi e ordine lessicografico. Il riferimento è la migliore mediana osservata fra le coppie eleggibili, non un ottimo teorico. I report comprendono candidati scartati e denominatori.

## 7. Valutare le varianti WL, se previste

Prima di `llm_wl` e `llm_wl_sintesi` eseguire:

```bash
.venv/bin/python -B esperimento.py validation wl
```

Si confrontano le profondità in `wl_iterations`. Si registrano i recuperi dai DAG dei QASM e dal train; soltanto dopo si valutano le coppie recuperate sulla matrice validation. Questa è una selezione del recupero, senza inferenza LLM né Test. I cinque esempi e l'eventuale sintesi del DAG alimentano poi il rispettivo metodo Test.

## 8. Congelare ed eseguire Test

Avviare il server del modello selezionato. Se MQT è previsto, completarne i modelli e le prove Bell. Poi:

```bash
.venv/bin/python -B esperimento.py test congela
.venv/bin/python -B esperimento.py test esegui --metodo llm_rag
.venv/bin/python -B esperimento.py test esegui --metodo llm_senza_rag
.venv/bin/python -B esperimento.py test esegui --metodo random
.venv/bin/python -B esperimento.py test esegui --metodo llm_recupero_random
.venv/bin/python -B esperimento.py test esegui --metodo mqt
.venv/bin/python -B esperimento.py test analizza
```

Lanciare soltanto i metodi dichiarati in `test_methods`. Ogni circuito ha un esito: successo, timeout e fallimento restano tutti registrati. Per gli LLM si conservano prompt, evidenze, richieste, risposte, correzioni e token misurabili. Gli score mancanti non diventano zero; i confronti appaiati indicano i circuiti comuni.

`test oracle` è facoltativo e produce una griglia di riferimento separata, mai letta dai decisori. Dichiara se tutte le compilazioni sono riuscite. Costa molte più compilazioni di un metodo singolo.

I report sono sotto `test/risultati/<id>/report/`; ciascuna versione è legata alle impronte dei registri. Il `report.tex` autonomo si compila dalla propria directory con `pdflatex -halt-on-error report.tex`. Serve una distribuzione LaTeX con PGFPlots; il report validation include una figura generata dai dati. JSON e CSV si producono anche senza un compilatore LaTeX.

## 9. Esportare il proprio prototipo

```bash
.venv/bin/python -B esperimento.py esporta /percorso/nuovo-prototipo
```

La destinazione deve essere nuova. Si copiano framework, Dataset train, catalogo e configurazione selezionata, senza GGUF né score validation/Test. La nuova cartella ha README e setup propri e funziona senza il kit. La temperatura selezionata è mantenuta anche quando diversa da zero. `prototipo/` già presente nella repository rimane invariato.

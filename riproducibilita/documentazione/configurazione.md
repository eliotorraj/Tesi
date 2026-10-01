# Configurare una campagna senza modificare JSON

Questo ricettario raccoglie i comandi per personalizzare il kit. Eseguili da `riproducibilita/`, dopo `source .venv/bin/activate`. Gli esempi usano `mia-prova`: sostituiscilo con il nome del tuo esperimento. Se stai iniziando, segui prima la [guida completa](guida.md).

`configura.py` ed `esperimento.py` sono script Python. Le parole che seguono, come `nuovo`, `mostra`, `prepara` o `dataset`, indicano l'azione da eseguire. In particolare, quando qui si dice «prima di `prepara`», si intende prima di lanciare `python esperimento.py --esperimento mia-prova prepara`. Quel comando controlla e conserva gli ingressi e le impostazioni di riferimento della prova. La [guida spiega la sintassi](guida.md#come-leggere-i-comandi-della-guida) e quando eseguirlo.

## Creare, conoscere e duplicare le impostazioni

```bash
python configura.py nuovo mia-prova --profilo cpu
python configura.py mostra mia-prova
python configura.py elenca
python configura.py --help
python configura.py modello --help
```

Il nuovo esperimento parte da Qwen e dai sistemi `llm_rag`, `llm_senza_rag`, `random`. Il catalogo contiene inizialmente tutti i cinque Target e le dodici configurazioni, con le tre temperature di riferimento. Il profilo modifica soltanto le risorse iniziali. Per specificare subito i candidati e i sistemi:

```bash
python configura.py nuovo confronto-gpu --profilo gpu --modelli qwen phi gemma \
  --sistemi llm_rag llm_senza_rag random llm_recupero_random mqt
```

I profili sono due: `cpu` esegue il LLM sulla CPU con i pesi in RAM; `gpu` richiede il trasferimento di tutti gli strati possibili sulla GPU, usando la VRAM e mantenendo anche l'uso di RAM e CPU. Entrambi partono da contesto 16.384, risposta massima 4.096, batch 128, microbatch 64 e un processo Qiskit. Contesto, processi e batch si modificano separatamente: il fisso usa anch'esso `gpu`, con le risorse dichiarate tramite i comandi. La [spiegazione dei profili](guida.md#se-usi-una-gpu-o-il-fisso) contiene anche gli esempi per il fisso.

Le impostazioni nominate sono sotto `configurazioni/esperimenti/<nome>/`. I JSON restano leggibili: ogni modifica crea una revisione e aggiorna atomicamente il punto d'ingresso `esperimento.json`. Un valore rifiutato lascia attiva la configurazione precedente. I comandi non cancellano revisioni, risultati o pesi e non pubblicano su GitHub.

Dopo `prepara`, il configuratore rifiuta modifiche. Anche una preparazione parziale che abbia già creato il contratto protegge l'esecuzione. Per cambiare strada:

```bash
python configura.py duplica mia-prova mia-prova-02
python configura.py mostra mia-prova-02
```

La copia contiene le impostazioni, senza risultati; mantiene i riferimenti ai circuiti e ai GGUF. Se questi file vengono modificati, anche la nuova prova userà i nuovi contenuti al momento della preparazione. Le copie degli ingressi già congelati restano separate. Una configurazione preparata tramite `--output` è protetta anche quando gli output sono fuori dal kit.

## Scegliere i sistemi Test

```bash
python configura.py disponibili sistemi
python configura.py sistemi mia-prova llm_rag llm_senza_rag random
```

`sistemi` **sostituisce tutto l'elenco**. Non aggiunge implicitamente un metodo a quelli precedenti.

| Identificativo | Cosa confronta | Prerequisito specifico |
| --- | --- | --- |
| `llm_rag` | LLM con esempi recuperati dal train | Dataset RAG e selezione LLM |
| `llm_senza_rag` | LLM senza esempi recuperati | Selezione LLM |
| `random` | Scelta casuale di dispositivo e configurazione | Catalogo preparato |
| `llm_recupero_random` | LLM con esempi train estratti casualmente | Dataset RAG e selezione LLM |
| `mqt` | Selettore supervisionato e politiche RL | Addestramenti e `test tecnico-mqt` |
| `llm_rag_k1`, `llm_rag_k10` | RAG con uno o dieci esempi | Train con esempi compatibili sufficienti |
| `llm_wl`, `llm_wl_sintesi` | Recupero strutturale, con o senza sintesi del DAG | Anche `validation wl` |

Il kit mantiene la sequenza Dataset → validation → selezione → Test. Attualmente anche una campagna che valuti soltanto Random o MQT richiede la selezione sulla validation prima di `test congela`. Se togli `mqt`, non servono i suoi addestramenti per il confronto. Se lo aggiungi, il comando registra l'intenzione ma non avvia né recupera automaticamente modelli addestrati.

## Cambiare i circuiti

```bash
python configura.py circuiti mia-prova --cartella "$HOME/miei-circuiti" --crea
```

Il comando collega una cartella e, con `--crea`, crea gli split mancanti. Inserisci tu i `.qasm` direttamente in `train/`, `validation/` e `test/`. Se hai già una suddivisione, ometti `--crea`. Non vengono cancellati file esistenti e non si generano o ripartiscono automaticamente i circuiti.

Il percorso passato dal terminale è relativo alla directory corrente; il configuratore lo salva relativo al kit quando possibile, altrimenti assoluto. Sono supportati spazi nei percorsi, racchiudendoli fra virgolette. I campi degli schemi non devono essere modificati per cambiare il corpus.

## Selezionare o ampliare il catalogo Qiskit

Il catalogo descrive hardware **quantistico sintetico** e opzioni di compilazione. La GPU del PC si configura nella sezione risorse.

```bash
python configura.py disponibili dispositivi
python configura.py dispositivi mia-prova ibm_falcon_27 quantinuum_h2_56
python configura.py disponibili compilazioni
python configura.py compilazioni mia-prova o2_default_default o3_default_default o2_sabre_sabre
```

Entrambi i comandi sostituiscono il rispettivo elenco. Il primo Target diventa quello predefinito; le sue impronte vengono riprese dal riferimento distribuito e verificate in `prepara`. Le configurazioni standard possono essere riaggiunte per ID anche dopo averle escluse.

Per aggiungere una combinazione delle opzioni supportate:

```bash
python configura.py aggiungi-compilazione mia-prova o3_dense_basic \
  --ottimizzazione 3 --layout dense --routing basic --studio routing
```

L'ID deve essere nuovo, lungo al massimo 64 caratteri, e la combinazione non deve essere già presente. Sono accettati livelli 2 e 3; layout `default`, `sabre`, `dense`, `trivial`; routing `default`, `sabre`, `lookahead`, `basic`. `default` lascia la scelta a Qiskit, senza passare un metodo esplicito. `--studio` è un'etichetta di analisi fra `baseline`, `layout`, `routing`, non un parametro del compilatore.

Il comando non può inventare un Target, un plugin o un livello non previsto dagli schemi. Un sesto dispositivo o un metodo di compilazione fuori da questo insieme richiede l'estensione coerente di codice, schemi e prompt. Il kit lo segnala invece di produrre un catalogo apparentemente utilizzabile.

Le combinazioni personalizzate sono riutilizzabili finché rimangono nel catalogo attivo; se le escludi con `compilazioni`, per riattivarle ricreale con `aggiungi-compilazione`. La definizione precedente resta nelle revisioni.

## Scegliere i modelli già registrati

```bash
python configura.py disponibili modelli
python configura.py modelli mia-prova qwen phi
python configura.py modello mia-prova qwen --file /disco/modelli/Qwen3.5-4B-Q8_0.gguf
```

`modelli` seleziona i candidati fra quelli registrati; gli altri diventano inattivi. I loro percorsi e parametri restano conservati e possono essere riattivati. I pesi dei candidati inattivi non sono richiesti da `verifica` o dal congelamento della validation.

Cambiare il percorso di un modello di riferimento non ne cambia l'identità attesa. Se il file è diverso, la verifica dell'impronta fallisce. Per pesi diversi, inclusa un'altra quantizzazione dello stesso LLM, registra un nuovo ID.

## Registrare un altro LLM

Recupera autonomamente un GGUF compatibile con il tuo llama.cpp, quindi registra provenienza, revisione e precisione:

```bash
python configura.py aggiungi-modello mia-prova mio-llm \
  --file /disco/modelli/mio-modello.gguf \
  --fonte 'URL o provenienza verificabile del file' \
  --revisione 'identificativo-della-revisione' \
  --precisione Q4_K_M \
  --contesto 16384 --token-risposta 4096 --temperature 0 0.4
python configura.py modelli mia-prova qwen mio-llm
```

Sostituisci i valori esemplificativi con quelli reali. Il programma richiede un file locale esistente e calcola SHA-256. `--repository` permette di dichiarare anche il repository del modello base, se conosciuto. Per un file prodotto localmente indica una versione locale riconoscibile e conserva il procedimento che lo ha generato; il programma non ricostruisce informazioni di provenienza mancanti.

Il nuovo candidato diventa attivo. Eredita le risorse del primo candidato attivo per i valori non specificati, senza ereditarne identità e impronta. Rivedi il riepilogo: un contesto valido per Qwen può non esserlo per un altro LLM. Il comando non carica il GGUF e non certifica compatibilità, qualità o memoria sufficiente.

Per cambiare i parametri di un candidato già registrato:

```bash
python configura.py modello mia-prova mio-llm \
  --contesto 8192 --token-risposta 2048 --temperature 0 0.2 \
  --timeout 1800 --url http://127.0.0.1:8090
```

Il budget di risposta deve essere minore del contesto; le temperature devono essere finite, non negative e distinte. `--timeout` è in secondi. Sono supportati server locali con `transport` nativo o Windows, non provider remoti. La stessa porta può essere condivisa fra candidati eseguiti uno alla volta.

## Regolare CPU, GPU e cartella dei risultati

```bash
python configura.py risorse mia-prova \
  --processi 1 --timeout-compilazione 100 \
  --threads 4 --gpu-layers 0 --batch 128 --microbatch 64 \
  --server-bin /percorso/llama-server \
  --risultati /disco/risultati
```

`--processi` e `--timeout-compilazione` regolano la griglia Qiskit. Thread, strati GPU, batch e microbatch regolano il server di **tutti i candidati attivi**. Gli altri candidati mantengono le proprie impostazioni: quando li riattivi, rivedi il riepilogo. Il trainer del selettore MQT ha invece il proprio `--num-workers`.

Per una GPU disponibile:

```bash
python esperimento.py --esperimento mia-prova server qwen --list-devices
python configura.py risorse mia-prova --gpu-layers 999 --device ID_GPU
```

Usa l'ID restituito dal backend. `--device auto` lascia la scelta al backend; con zero strati GPU l'avviatore passa `--device none`. Un numero inferiore di strati può ridurre il carico sulla VRAM, ma la scelta dipende dal modello e dall'hardware. Non si sostituisce nel codice un nome di scheda fisso.

Se serve un'impostazione diversa per un solo candidato, usa le stesse opzioni con `modello`, per esempio `modello mia-prova qwen --threads 4 --gpu-layers 0`. Il comando `risorse` non cambia il contesto: si modifica con `modello --contesto`.

La radice risultati è memorizzata nella configurazione. I comandi successivi la ritrovano attraverso `--esperimento`; non occorre ripetere `--output`. Mantieni le risorse costanti durante la campagna. Gli argomenti diretti di `server`, come `--threads`, sono sostituzioni operative e vengono registrati nel comando di avvio; per condizioni pianificate usa il configuratore prima di `prepara`.

## Temperature, recupero, seed e selezione

```bash
python configura.py parametri mia-prova \
  --temperature 0 0.4 0.7 --k 5 --passi-rl 100000 \
  --seed 20260913 --seed-test 0 --seed-random 20260927 \
  --seed-compilazione 0 1 2 --wl 1 2 3 4 5 \
  --criterio median_regret
```

Puoi fornire soltanto le opzioni da cambiare. Le temperature vengono applicate a tutti i candidati attivi; `modello --temperature` permette una griglia specifica. `--k` accetta 1, 5 o 10; le varianti Test `llm_rag_k1` e `llm_rag_k10` mantengono il proprio k esplicito. WL recupera cinque esempi e seleziona la profondità fra i valori di `--wl`.

Il protocollo richiede esattamente tre seed di compilazione distinti. `--seed` controlla la generazione LLM; `--seed-test` e `--seed-random` i rispettivi percorsi di valutazione. Le scelte complete vanno conservate: fissare i seed non garantisce identità dei tempi o determinismo di ogni backend.

Il criterio può essere `median_regret` o `mean_regret`, sempre con priorità alla copertura. Le impostazioni di generazione di livello inferiore rimangono in `configurazioni/generazione_llm.json`; cambiarle è un intervento avanzato da fare prima delle campagne. Non è implementato un comando generico per modificare qualunque campo degli schemi.

## Capire cosa manca senza avviare una prova

```bash
python configura.py mostra mia-prova
python configura.py verifica mia-prova
python esperimento.py --esperimento mia-prova stato
python esperimento.py --esperimento mia-prova server qwen --controlla
```

| Comando | Che cosa controlla |
| --- | --- |
| `mostra` | Impostazioni, percorsi, candidati, conteggi e carico massimo della griglia. Non calcola hash dei GGUF. |
| `configura.py verifica` | Presenza degli ingressi attivi, nomi/duplicati byte-identici, hash GGUF e percorso del server. Non carica modelli. |
| `esperimento.py verifica` | Installazione e componenti software del kit. |
| `stato` | Artefatti presenti, integrità della preparazione quando disponibile ed esiti Test; suggerisce la fase successiva. |
| `server ID --controlla` | Identità dei pesi e contesto del server già acceso, senza inferenza. |

Errori frequenti:

- **GGUF mancante:** scarica il file corretto o collega il suo percorso. Non è incluso nel clone.
- **GGUF diverso dall'impronta:** recupera la revisione attesa oppure registra consapevolmente un nuovo modello; cambiare percorso non cambia l'identità.
- **Split vuoto o nome duplicato:** sistema i circuiti nella suddivisione prima di preparare.
- **Esperimento preparato:** usa `duplica` e un nuovo nome; non cancellare contratti o registri per sbloccare una prova.
- **Server non trovato:** indica un eseguibile Linux con `--server-bin` e verifica i permessi di esecuzione.
- **Server non pronto:** attendi il caricamento; se il processo termina, leggi `stderr.log` nella cartella mostrata all'avvio.
- **Memoria o contesto insufficienti:** scegli un GGUF più piccolo, meno processi o un contesto diverso in una nuova configurazione. Il kit conserva l'esito della prova fallita.

Per l'interfaccia tradizionale restano disponibili `esperimento.py --config FILE --output CARTELLA ...` e `modelli_llm/server.py`. Nel primo caso `--config` e `--output` precedono la fase; il server separato legge `RIPRO_CONFIG` e `RIPRO_OUTPUT`. Per l'uso ordinario preferisci il nome dell'esperimento, che evita di dover mantenere manualmente quei percorsi allineati.

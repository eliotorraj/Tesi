# Revisione degli script del secondo esperimento

Data: 20 settembre 2026. Non sono stati cambiati gli script dell'esperimento. Le copie lette sono quelle raccolte prima dello spostamento in `archivio/esperimento_v2/`.

## Che cosa è stato controllato

Sono stati inventariati 147 script operativi nelle cartelle `scripts`, `qiskit_dataset`, `prototype`, `llm_selection` e `tests`: 34.750 righe. Tutti hanno superato un controllo di sintassi. Sono 135 file Python, 9 PowerShell, un Bash, un JavaScript e un C#. Il codice C# è stato compilato senza creare oggetti o accedere ai sensori. Il programma Node è stato usato soltanto con `--check`.

La lettura ragionata copre interamente 14 script e una porzione di `03_train_rl_model.py`. Gli altri 132 hanno ricevuto un controllo statico di struttura, import, descrizioni e costanti candidate. Questo lavoro non equivale a una lettura manuale completa delle 34.750 righe. Non sono stati eseguiti gli esperimenti, i modelli o l'intera suite di test.

I dettagli per ogni file sono in `rassegna_tutti_script.md` e `inventario_operativo.json`. Il JSON contiene percorso originale e attuale, SHA-256, scopo, import, descrizioni, candidati hardcoded, controllo svolto, intervalli letti a mano ed esito. I candidati hardcoded derivano da una ricerca euristica: una corrispondenza non è automaticamente un errore e una lista vuota non dimostra l'assenza di costanti nel codice.

## Problemi verificati

### R01 — P2: il server può restare attivo se fallisce il primo registro

In `llm_selection/serve.ps1:53` il server viene avviato. La scrittura di `launch.json` a riga 64 e la creazione del registro delle risorse a riga 66 precedono il `try/finally`, che inizia a riga 77. Un errore in queste operazioni interrompe lo script prima della protezione che arresta il server. Se `launch.json` non è stato creato, anche `llm_selection/controller.py:60` ritorna senza arrestarlo.

È stato riprodotto il caso di una scrittura fallita usando il blocco originale delle righe 52–76, un processo fittizio e un errore simulato. Il processo fittizio risulta avviato prima dell'errore. Non sono stati avviati programmi reali. Il risultato è in `reproduction_serve_lifecycle.json`.

Nella prossima versione conviene includere l'avvio e tutta l'inizializzazione nel `try/finally`. La chiusura deve tollerare risorse non ancora create e mantenere l'identità del processo anche se il disco non consente di scrivere il registro.

### R02 — P2: il timeout Python può perdere i dati del trasporto

In `llm_selection/gateway.py:22`, se `subprocess.run` genera `TimeoutExpired`, la funzione termina prima di salvare `response.json`, `stderr.txt` e `transport.json`. Rimane soltanto `request.json`. Il timeout ordinario gestito da curl passa invece dalle scritture: il problema riguarda il timeout del processo Python, fissato a 15 secondi oltre quello di curl.

La funzione originale è stata estratta via AST e chiamata con un processo fittizio che genera un timeout contenente stdout e stderr parziali. Questi dati e la durata non vengono conservati. Il risultato è in `reproduction_gateway_timeout.json`. Non sono state eseguite richieste di rete.

Nella prossima versione conviene salvare l'errore, i tempi e gli output disponibili prima di propagare l'eccezione. Lo stato della chiamata va dichiarato sconosciuto quando non è verificabile. Non occorre ripetere automaticamente la richiesta.

Questi rilievi descrivono casi di errore. Non dimostrano che tali casi si siano verificati nelle prove già registrate e non invalidano automaticamente i risultati passati.

## Costanti e percorsi

Le costanti scientifiche dell'esperimento — versione MQT, impronte, dispositivi, schema, seed, split e contratto delle risposte — servono a rendere le prove riproducibili. Non vanno trasformate indiscriminatamente in opzioni o modificate nei file congelati.

Alcuni valori appartengono invece alla macchina e limitano il riuso:

| File | Valore | Intervento utile in una nuova versione |
|---|---|---|
| `llm_selection/launch_technical.ps1:18` | Ubuntu e `/home/elio/Tesi-mqt-2.4-v2` | Ricavare il progetto dal percorso dello script o passarlo esplicitamente; il percorso fisso non segue lo spostamento nell'archivio. |
| `llm_selection/common.py:61` | Nome della distribuzione WSL Ubuntu | Un solo convertitore di percorsi con distribuzione configurata. |
| `llm_selection/gateway.py:10` e `controller.py:17` | Programmi Windows in `/mnt/c` | Un'unica configurazione locale verificata all'avvio. |
| `llm_selection/gateway.py:11` | Porta 8089 | Collegarla ai dati di avvio del server; `serve.ps1` espone già un parametro Port. |
| `llm_selection/storage.py:5` | `/mnt/d/Tesi-mqt/llm-selection` | Parametro esplicito di archiviazione; conservare la distinzione fra percorso logico e fisico. |
| `scripts/03_train_rl_model.py:448` | `/mnt/d/RL_Models_Tesi/MODELLI NUOVI` | Opzione per i checkpoint, registrata nei metadati della singola esecuzione. |
| `llm_selection/AmdSensors.cs:13` | DLL AMD in `C:\Windows\System32` | Documentare il requisito Windows/AMD; valutare una risoluzione dal sistema se si amplia la portabilità. |

Sono limiti del riuso, non errori dimostrati nell'ambiente originario. Eventuali adattamenti dello storico devono stare in un avviatore esterno o in una nuova revisione; i file vincolati dalle impronte restano invariati.

## Chiarezza e ottimizzazione

120 dei 135 moduli Python hanno già una descrizione iniziale. I 15 senza descrizione sono file di test, nei quali classi e casi forniscono già i nomi degli scenari. Aggiungere commenti ripetitivi a ogni assegnazione aumenterebbe il rumore. I commenti più utili spiegano invarianti, motivi delle scelte e condizioni di ripresa.

La priorità di leggibilità è nelle funzioni lunghe. `scripts/04_train_device_selector.py` ha 2.546 righe: `compile_resumably` ne occupa 399 e `main` 417. Il metodo `validate` in `prototype/quantum_assistant/adapters/validation.py` occupa 755 righe. Questi dati derivano dall'AST, non da una revisione semantica completa. In una nuova versione conviene separare preparazione, esecuzione, verifica e salvataggio, mantenendo i controlli esistenti. Nessuna riscrittura automatica è stata applicata.

Nel recupero RAG, `QdrantContextRetriever.retrieve` ricarica il corpus a ogni richiesta e `verified_client` verifica l'intera raccolta. La ricerca richiede tutti i candidati e ricalcola le distanze prima di ordinare: serve anche a gestire le parità in modo deterministico. È una scelta prudente per il piccolo corpus corrente. Se i tempi di preparazione diventano rilevanti, si può conservare in memoria una copia verificata e immutabile, legata alle impronte dei dati, della trasformazione e del catalogo. Prima occorre misurare il costo. Non è giustificato eliminare i controlli o restringere semplicemente ai primi k punti.

Nel trasporto ogni riga del flusso viene sincronizzata sul disco. Questo protegge la ricostruzione delle interruzioni ma può aumentare il tempo di I/O. Un eventuale raggruppamento delle scritture richiede una scelta esplicita sulla quantità massima di dati che si può perdere e una nuova misura dei tempi. Non è stato proposto come miglioramento gratuito.

## Copie storiche

Sono stati inventariati 1.880 script negli archivi preesistenti e nelle copie di codice degli esperimenti: 195 impronte distinte. Di questi, 1.567 file sono identici a un sorgente operativo inventariato. Tutti i percorsi attuali sono stati ritrovati dopo lo spostamento.

`inventario_storico.json` conserva percorso, impronta, dimensione ed eventuale corrispondenza con un sorgente operativo. `duplicati_storici.json` raggruppa le copie identiche. Questi file hanno ricevuto un inventario e un confronto delle impronte, non una lettura manuale delle versioni storiche diverse. Non sono stati eliminati duplicati. La dipendenza `node_modules/@toon-format/toon/dist/index.mjs` non è stata contata come sorgente operativo del progetto.

## Limiti

I controlli sintattici non verificano gli import durante l'esecuzione o la compatibilità dei programmi installati. Non è stata consultata documentazione esterna: i rilievi dipendono dal codice locale osservato. Non sono stati modificati Git, ambienti, dati, sigilli o risultati. Le prove simulate sono separate dalle prove sperimentali e non misurano la qualità delle scelte dei modelli.

## Variante ripristinata durante il riordino

Alla verifica finale 146 dei 147 file coincidono ancora con la copia esaminata. Il coordinatore ha ripristinato la versione congelata di `llm_selection/v2/plots.py`, conservando la versione precedente. La rassegna e il campo `sha256` descrivono la copia raccolta prima del ripristino; `current_sha256` descrive il file archiviato finale. Anche la variante ripristinata supera il controllo AST. La differenza è registrata in `verifica_finale.json` e non deriva da modifiche della revisione.

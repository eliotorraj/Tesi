# Tesi — modelli linguistici per la compilazione quantistica

Il progetto studia se un modello linguistico (LLM), aiutato da esempi di
compilazioni precedenti, può scegliere **su quale dispositivo compilare un
circuito quantistico e con quali impostazioni Qiskit**.

L'obiettivo è ottenere scelte di buona qualità, spiegabili attraverso evidenze
verificabili e con tempi accettabili. Il sistema viene confrontato con
MQT Predictor e con metodi più semplici.

**Punto attuale — 15 settembre 2026:** il Dataset Qiskit e il recupero RAG sono
pronti. Il collegamento al modello locale funziona, ma le risposte Qwen non
superano ancora tutti i controlli sulle evidenze. La selezione sulla validation
non è conclusa e il test resta chiuso. In parallelo prosegue l'addestramento RL.

## Come leggere il progetto

1. Questo README: obiettivo, funzionamento, stato e avvio.
2. I README delle cartelle: responsabilità e descrizione dei singoli file.
3. [Protocollo sperimentale](docs/protocollo_sperimentale.md): regole e sequenza delle prove.
4. [Approfondimenti](docs/approfondimenti/README.md) e [resoconti](docs/resoconti/README.md): istruzioni tecniche, decisioni, errori e risultati.

## Il problema, in parole semplici

Lo stesso circuito può essere adattato in modi diversi a dispositivi diversi.
Cambiano le operazioni disponibili, i collegamenti tra i qubit e gli errori
stimati. Provare tutte le alternative costa tempo.

L'idea è usare compilazioni già effettuate per aiutare un LLM a scegliere
una buona alternativa per un nuovo circuito. Il modello sceglie da un catalogo
chiuso: **cinque dispositivi e dodici configurazioni Qiskit**.

La qualità è misurata con `expected_fidelity`, una stima basata sulle proprietà
dei Target sintetici di MQT Bench. Questi esperimenti non eseguono circuiti su
hardware quantistico reale. Il confronto finale fra i metodi deve ancora essere
svolto: non abbiamo ancora dimostrato la superiorità dell'assistente.

## Come funziona

### 1. Prepariamo gli esempi, prima delle richieste

Partiamo da 600 circuiti e li separiamo in **422 train, 88 validation e 90 test**.
Train serve a costruire gli esempi; validation a scegliere la configurazione
LLM; test a misurarne poi la qualità su dati riservati.

Per train e validation proviamo le configurazioni Qiskit sui dispositivi
compatibili, con tre semi casuali fissati. Conserviamo successi, timeout,
circuiti compilati, punteggi e tempi. Dai risultati train costruiamo il Dataset
per il RAG: ogni esempio descrive un circuito, il dispositivo vincente e fino
a tre configurazioni valide di quel dispositivo.

Il Dataset RAG contiene **396 circuiti train distinti per contenuto**:
i 26 duplicati byte per byte dei 422 file train non aggiungono esempi.

### 2. L'assistente prepara e controlla una scelta

```text
Circuito e vincoli dell'utente
          ↓
Lettura del circuito e controllo dei dispositivi compatibili
          ↓
Recupero di cinque esempi train simili tramite Qdrant
          ↓
LLM: scelta di dispositivo e configurazione, con riferimenti alle evidenze
          ↓
Controlli su formato, compatibilità, piano e riferimenti
          ↓
Risposta valida oppure errore registrato
          ↓
Nel prototipo: conferma della proposta e compilazione Qiskit
```

La similarità usa **49 caratteristiche numeriche del circuito**.
Il RAG non consulta i punteggi del circuito da valutare e non cerca brani nei PDF.

Il modello non può inventare configurazioni. Il programma verifica anche che
le fonti citate sostengano le affermazioni. Una risposta con dispositivo giusto
e citazioni sbagliate viene rifiutata. Sono consentite al massimo tre chiamate,
comprese le correzioni di risposte non valide.

Nella selezione sperimentale le decisioni vengono prima registrate e sigillate.
Un valutatore separato le confronta poi con la matrice Qiskit già prodotta,
senza mostrarla al modello durante la scelta.

### 3. Prepariamo MQT Predictor come termine di confronto

MQT Predictor segue un percorso diverso:

```text
Circuito → selettore supervisionato del dispositivo → compilatore RL dedicato
```

Per questo addestriamo una politica RL per ciascuno dei cinque dispositivi.
Poi costruiamo il Training set del selettore e addestriamo il classificatore.
Solo dopo i controlli dei modelli e dell'intero flusso possiamo usare
`qcompile` come riferimento sperimentale.

**Dataset** indica gli esempi per il RAG/LLM. **Training set** indica i dati
circuito-dispositivo per il modello supervisionato MQT. Il fine-tuning dell'LLM
non è un risultato già realizzato dell'esperimento corrente.

## Struttura delle cartelle

Ogni collegamento porta alla guida dei file di quell'area.

| Cartella | Responsabilità |
| --- | --- |
| [scripts/](scripts/README.md) | Comandi per preparare dati, addestrare MQT, eseguire controlli e valutare i metodi. |
| [qiskit_dataset/](qiskit_dataset/README.md) | Logica riutilizzabile per generazione, aggregazione e valutazione del Dataset. |
| [prototype/](prototype/README.md) | Assistente: richieste, vincoli, RAG, scelta, validazione e compilazione. Include una vista Qdrant facoltativa. |
| [llm_selection/](llm_selection/README.md) | Collegamento ai modelli locali, prove tecniche, selezione sulla validation e analisi. |
| [configs/](configs/README.md) | Catalogo delle configurazioni e impostazioni dei metodi. |
| [schemas/](schemas/README.md) | Regole della struttura dei documenti JSON scambiati dal sistema. |
| [datasets/](datasets/README.md) | Circuiti, risultati Qiskit, esempi RAG e Training set. |
| [artifacts/](artifacts/README.md) | Modelli, checkpoint, cache, piani, indici, registri e risultati delle esecuzioni. |
| [tests/](tests/README.md) | Verifiche automatiche del comportamento e delle protezioni sperimentali. |
| [docs/](docs/README.md) | Protocollo, approfondimenti, resoconti e manutenzione. |
| [knowledge/](knowledge/README.md) | Concetti e articoli di riferimento. |
| [archivio/](archivio/README.md) | Materiale storico e corpus originale ancora necessario alla verifica dei dati. |
|[.vscode/](.vscode/README.md) | Preferenze dell'editor. |

I dati correnti sono nelle rispettive cartelle `experiments/`, sotto
`qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2`.
Le cartelle dei cinque dispositivi e `global/` sono viste dello stesso Dataset.

### File nella radice

| File o gruppo | Funzione |
| --- | --- |
| `README.md` | Mappa generale e punto della situazione. |
| `pyproject.toml` | Progetto Python e dipendenze dirette. |
| `uv.lock` | Versioni esatte delle dipendenze, per ricostruire l'ambiente. |
| `.python-version` | Versione Python prevista. |
| `.gitignore` | File locali e pesanti da non trasferire con Git. |
| `.gitattributes` | Attributi Git; le precedenti regole LFS sono state rimosse. |
| `AGENTS.md` | Istruzioni locali per gli assistenti di sviluppo. |
| `.git` | Collegamento ai metadati Git della cartella di lavoro. |
| `.venv/` | Ambiente Python locale generato; non è codice del progetto. |

## Che cosa abbiamo fatto e dove siamo

Questo è uno stato della cartella verificato il **15 settembre 2026**, integrato
con l'avvio RL comunicato dall'utente. Non è un monitor in tempo reale.

| Fase | Stato e significato |
| --- | --- |
| Studio e prime prove | Svolti: studio MQT, prove con la vecchia versione 2.3.0 e primo prototipo. Risultati conservati nell'archivio. |
| Protocollo v2 e ambiente 2.4.0 | Predisposti: dipendenze, corpus, partizioni, cinque Target e catalogo congelati. |
| Dataset Qiskit train + validation | Completo: **87.120 tentativi, 82.621 successi e 4.499 timeout**. Sono esiti conservati, non 87.120 successi. |
| RAG | Pronto: **396 esempi train**, indice Qdrant e verifica tecnica dei prompt su **88 validation**. Questo controllo non è la selezione LLM. |
| Assistente e collegamento LLM | Implementati: richiesta, maschera, recupero, risposta JSON, verifiche delle evidenze, correzioni e registri. |
| Prove tecniche LLM | In corso sul train. Ultima prova Qwen su DJ: scelta corretta, **0 risposte interamente valide su 3 chiamate**, per errori nei riferimenti. |
| Riduzione dei prompt | Verificata senza perdita di contenuto su **93 prompt: 5 train e 88 validation**. Non dimostra la qualità delle decisioni LLM. |
| Modelli RL | Quantinuum ha un modello canonico con **100.352 passi registrati**. L'utente ha comunicato l'avvio di `ibm_falcon_27`; gli altri quattro modelli finali non sono tutti disponibili/verificati in questa cartella. |
| Selettore ML e verifica qcompile | Da completare/verificare dopo i cinque modelli RL; il solo modello Quantinuum non basta. |
| Selezione LLM sulla validation | Da svolgere fino al completamento e al congelamento della configurazione. I modelli finali sono ancora non configurati nel file generale dei metodi. |
| Confronto finale sul test | **Non iniziato: test chiuso.** |
| Scrittura della tesi | Bozza iniziale e bibliografia presenti localmente; risultati finali e verifica dell'impaginazione da completare. |

Le evidenze e i dettagli delle prove sono nell'[indice dei resoconti](docs/resoconti/README.md).
Non confondere il completamento di un addestramento, il superamento dei controlli
del programma e la dimostrazione di buona qualità sperimentale.

### Prossimi passi

1. Proseguire le prove tecniche dei modelli locali, risolvendo o documentando gli errori di risposta e fissando impostazioni sostenibili.
2. Congelare la griglia di selezione, raccogliere tutte le decisioni sugli 88 validation, poi valutarle e scegliere il modello con le sue impostazioni.
3. In parallelo, completare e controllare i cinque RL, costruire il Training set, addestrare il selettore ML e verificare `qcompile`.
4. Fissare tutti i metodi finali, compreso il modello di frontiera, e superare le condizioni di apertura del test.
5. Eseguire il confronto finale: LLM con/senza RAG, LLM di frontiera, MQT Predictor, Qiskit fisso e casuale. Confrontare con il riferimento esaustivo solo dove la matrice è interamente riuscita.
6. Produrre analisi, grafici e resoconto LaTeX dai dati conservati, dichiarando fallimenti e circuiti effettivamente confrontabili.

La selezione locale può procedere senza aspettare che MQT sia completo.
Il confronto finale richiede invece anche quel ramo.

## Come avviare il progetto

Il progetto è un insieme di librerie e comandi, con strumenti di esplorazione
facoltativi. Non ha ancora un'unica applicazione grafica che racchiuda tutto.

L'ambiente sperimentale usa Ubuntu/WSL, **Python 3.12 e MQT Predictor 2.4.0**,
con le versioni di `uv.lock`. Su una nuova installazione:

```bash
cd /home/elio/Tesi-mqt-2.4-v2
bash scripts/bootstrap_ubuntu.sh
```

Prima occorre ripristinare anche i dati e i modelli esterni nei percorsi previsti:
Git da solo non li trasferisce. Seguire le
[istruzioni di trasferimento](docs/manutenzione/rimozione_lfs_2026-09-15/README.md).
Non ricreare l'ambiente mentre un training lo sta usando; conservare anche
le copie dei modelli installate al suo interno.

Con l'ambiente già pronto, questo comando mostra il piano senza avviare training:

```bash
.venv/bin/python scripts/16_run_pipeline_v2.py plan
```

Per le prove dei modelli locali seguire la
[guida della selezione](docs/approfondimenti/selezione_llm.md).
I comandi di addestramento, ripresa e apertura del test restano nel
[protocollo](docs/protocollo_sperimentale.md).

## Una demo

1. **Mostrare un circuito train e il suo esempio RAG.** Spiegare quali alternative sono state provate e quali informazioni ha il modello.
2. **Mostrare la preparazione della richiesta.** Il comando qui sotto produce prompt ed evidenze, senza chiamare un LLM e senza compilare.
3. **Mostrare una risposta reale già salvata.** Usare la [prova Qwen su DJ](docs/resoconti/2026-09-15_prompt_compatto.md), con risposta, errori e tempi. Spiegare perché una scelta giusta può ancora essere rifiutata.
4. **Mostrare il punto del protocollo.** Distinguere le parti implementate dalle prove scientifiche ancora da fare.

Per il secondo passaggio, quando le risorse del computer sono disponibili:

```bash
EXP=qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2
.venv/bin/python scripts/17_rag_v2.py query \
  --qasm "datasets/experiments/$EXP/expected_fidelity/full/circuits/train/dj_indep_tket_2.qasm" \
  --k 5
```

Richiede Dataset e indice Qdrant già preparati. La ricognizione documentale
non ha rieseguito questa demo né avviato nuove inferenze durante il training RL.

# Revisione integrale degli script — 21 settembre 2026

Sono stati letti integralmente **23 script, per 8.496 righe**. Tutti gli hash SHA-256 corrispondono ai sorgenti congelati e tutti i file superano il controllo sintattico AST. Non restano letture parziali in questo gruppo. Il JSON contiene hash, intervalli, dipendenze e una scheda per ogni file.

I sorgenti non sono stati modificati. Sono state eseguite sette simulazioni isolate, descritte sotto; non sono stati avviati addestramenti, modelli, compilazioni sperimentali o inferenze e il Test non è stato aperto. Le condizioni riprodotte mostrano difetti possibili: non dimostrano che abbiano alterato i risultati storici.

Riferimento letto: ramo `riorganizzazione-prototipo`, commit `2772f2a6e70215eb66495afafb56a02278785fcd`. Le dipendenze aggiuntive lette, con intervalli precisi, sono elencate nel JSON e non aumentano la copertura dei 23 script.

## Rilievi verificati

Sono riportati dieci rilievi P2. I problemi riguardano soprattutto ripresa, conservazione dei tentativi e legami di provenienza. Le correzioni vanno applicate a una revisione futura, preservando questi sorgenti congelati.

### SCR-01 — Ripresa automatica cerca i checkpoint in un percorso diverso da quello del trainer (P2)

Riferimenti: [16_run_pipeline_v2.py:141–150](../../esperimento_v2/scripts/16_run_pipeline_v2.py#L141), [03_train_rl_model.py:448–466](../../esperimento_v2/scripts/03_train_rl_model.py#L448).

**Condizione.** Un addestramento produce checkpoint nel percorso fisso sul disco D e viene rilanciato attraverso la pipeline. **Evidenza.** latest_valid_checkpoint cerca in EXPERIMENT_ROOT/checkpoints/rl; il trainer scrive in /mnt/d/RL_Models_Tesi/MODELLI NUOVI/checkpoints/rl. Le cartelle archiviate checkpoints e checkpoints/rl non sono collegamenti simbolici.

**Effetto.** La pipeline non trova il checkpoint e riparte senza --resume; il trainer può poi rifiutare la cartella già popolata. **Intervento proposto.** Nella futura revisione usare una sola configurazione del percorso di checkpoint condivisa fra trainer e pipeline.

**Verifica.** Lettura dei due flussi e controllo dei percorsi; nessun addestramento eseguito.

### SCR-02 — Una coda JSONL interrotta assorbe il record successivo (P2)

Riferimenti: [04_train_device_selector.py:160–187](../../esperimento_v2/scripts/04_train_device_selector.py#L160).

**Condizione.** Il processo si interrompe dopo avere scritto un frammento JSON privo del newline conclusivo. **Evidenza.** append_manifest aggiunge JSON al file senza controllare la coda; load_manifest ignora le righe non decodificabili.

**Effetto.** Il successivo record completo si concatena al frammento e viene ignorato; si perdono risultato e conteggio dei tentativi, con possibili ripetizioni. **Intervento proposto.** Conservare il frammento e ripristinare una separazione valida prima di appendere; segnalare la corruzione interna anziché ignorarla.

**Verifica.** S02_jsonl_partial_tail: il record nuovo scompare da attempts e statuses.

### SCR-03 — Un risultato già in coda può essere sostituito da worker_crash (P2)

Riferimenti: [04_train_device_selector.py:1335–1344](../../esperimento_v2/scripts/04_train_device_selector.py#L1335), [04_train_device_selector.py:1496–1526](../../esperimento_v2/scripts/04_train_device_selector.py#L1496).

**Condizione.** Un worker termina quando la sua coda contiene ancora messaggi phase, result e done. **Evidenza.** Il supervisore consuma un messaggio per iterazione, poi rimuove il worker non più vivo prima di drenare i risultati rimanenti.

**Effetto.** Può registrare worker_crash e consumare un tentativo pur avendo un risultato riuscito disponibile; il ramo output_changed può eliminare il nuovo output. **Intervento proposto.** Drenare i messaggi del worker o richiedere un evento terminale prima di classificare la sua uscita come anomala.

**Verifica.** S03_pending_worker_results: registrati running e worker_crash; result success e done restano in coda. Nessun processo reale avviato.

### SCR-04 — La provenienza dei tentativi non distingue il limite di tempo (P2)

Riferimenti: [04_train_device_selector.py:1043–1060](../../esperimento_v2/scripts/04_train_device_selector.py#L1043), [04_train_device_selector.py:2261–2286](../../esperimento_v2/scripts/04_train_device_selector.py#L2261).

**Condizione.** Si riutilizza un manifest fra esecuzioni con limiti diversi, consentiti per ml-canary. **Evidenza.** record_matches_run_configuration confronta versione, seed, passi, modello e target ma non timeout; i metadati finali descrivono il timeout richiesto dalla nuova esecuzione.

**Effetto.** Un successo da 150 secondi ottenuto con limite 300 può essere riusato in una configurazione dichiarata a 100 secondi; il conteggio dei fallimenti non distingue le due politiche. **Intervento proposto.** Registrare il timeout di ogni tentativo e includerlo nell’identità del risultato o dichiarare esplicitamente quello originario del risultato riusato.

**Verifica.** S04_timeout_not_in_cache_key: configurazione accettata e nessun parametro timeout nel validatore.

### SCR-05 — La chiusura del figlio qcompile senza risposta non produce un esito persistito (P2)

Riferimenti: [12_run_qcompile_v2.py:159–184](../../esperimento_v2/scripts/12_run_qcompile_v2.py#L159), [12_run_qcompile_v2.py:320–342](../../esperimento_v2/scripts/12_run_qcompile_v2.py#L320).

**Condizione.** Il processo figlio chiude la pipe prima di inviare un risultato, per esempio dopo un arresto anomalo. **Evidenza.** poll può restituire true a EOF; recv solleva EOFError non gestito e il chiamante non costruisce il record terminale.

**Effetto.** La chiamata può sparire dal registro e venire ripetuta alla ripresa senza documentare l’interruzione. **Intervento proposto.** Gestire EOFError e gli errori di comunicazione registrando un esito di infrastruttura distinto con le informazioni disponibili.

**Verifica.** S05_qcompile_eof: EOFError e nessun record terminale; nessun processo reale avviato.

### SCR-06 — Gli ingressi storici di validation e apertura Test non usano la selezione ufficiale local-llm-v2 (P2)

Riferimenti: [14_evaluate_methods_v2.py:55–59](../../esperimento_v2/scripts/14_evaluate_methods_v2.py#L55), [15_release_test_v2.py:265–283](../../esperimento_v2/scripts/15_release_test_v2.py#L265), [15_release_test_v2.py:328–330](../../esperimento_v2/scripts/15_release_test_v2.py#L328).

**Condizione.** Si usa la selezione ufficiale local-llm-v2 con questi ingressi storici. **Evidenza.** La validation richiama llm_selection.evaluate.evaluate e ritorna subito; il rilascio importa verify_local_selection, FINAL e PROOF dal primo llm_selection.finalize, legato ai precedenti final_configuration.json, selection_complete.json e studio congelato.

**Effetto.** Il controllo non certifica la selezione ufficiale v2. Il ramo validation ignora anche catalog e overwrite dell’ingresso storico. **Intervento proposto.** Collegare esplicitamente valutazione e controllo di apertura allo studio ufficiale local-llm-v2 nella futura implementazione.

**Verifica.** Lettura integrale degli ingressi e di llm_selection/finalize.py e evaluate.py. Limite già riconosciuto da AGENTS.md; il Test non è stato aperto.

### SCR-07 — Il controllo canary non lega il rapporto ai modelli correnti (P2)

Riferimenti: [15_release_test_v2.py:232–259](../../esperimento_v2/scripts/15_release_test_v2.py#L232).

**Condizione.** Un rapporto canary riuscito resta disponibile dopo la sostituzione di un modello con un altro formalmente valido. **Evidenza.** I modelli correnti sono validati separatamente; check_canary verifica successo, sei risultati, limiti e presenza di qcompile, senza confrontare hash degli artefatti né copertura distinta dei cinque dispositivi.

**Effetto.** Un rapporto relativo a vecchi modelli può soddisfare il prerequisito sui nuovi modelli. **Intervento proposto.** Confrontare hash, versioni, target, circuito train e copertura dei cinque dispositivi con la configurazione corrente.

**Verifica.** S07_stale_canary_gate: rapporto con hash outdated accettato dal controllo estratto; nessun rilascio Test eseguito.

### SCR-08 — La ripartenza da zero può sovrascrivere il registro degli episodi (P2)

Riferimenti: [03_train_rl_model.py:456–469](../../esperimento_v2/scripts/03_train_rl_model.py#L456), [03_train_rl_model.py:507–513](../../esperimento_v2/scripts/03_train_rl_model.py#L507).

**Condizione.** Una corsa si interrompe prima del primo checkpoint valido e viene rilanciata con lo stesso nome senza --resume. **Evidenza.** La guardia consente la cartella contenente soltanto lo snapshot interrotto; il nuovo Monitor usa ancora monitor.csv. ResultsWriter di Stable-Baselines3, con override_existing predefinito, apre il file in modalità w.

**Effetto.** Si perdono gli episodi del tentativo precedente; il nome dello snapshot diagnostico può essere riusato a una successiva interruzione. **Intervento proposto.** Assegnare un identificativo e registri distinti a ogni avvio fisico, anche quando si riparte da zero.

**Verifica.** S08_restart_overwrites_episode_log: guardia originale accettata e ResultsWriter installato sovrascrive un CSV sintetico. Nessun training.

### SCR-09 — Gli esiti canary vengono salvati soltanto alla fine e il rapporto viene sostituito (P2)

Riferimenti: [07_validate_qcompile.py:89–98](../../esperimento_v2/scripts/07_validate_qcompile.py#L89), [07_validate_qcompile.py:495–524](../../esperimento_v2/scripts/07_validate_qcompile.py#L495).

**Condizione.** La validazione si interrompe dopo alcuni controlli o viene ripetuta con il percorso predefinito. **Evidenza.** I risultati delle sei chiamate restano in memoria sino al salvataggio finale; la scrittura atomica sostituisce validation_report.json senza archiviare la versione precedente.

**Effetto.** Un’interruzione perde gli esiti già completati; una ripetizione può cancellare evidenze di successo o fallimento precedenti. **Intervento proposto.** Salvare ogni risultato sotto un identificativo di esecuzione immutabile e aggiornare separatamente il riferimento al rapporto corrente.

**Verifica.** Lettura completa del flusso di raccolta e scrittura. Nessuna validazione con modelli eseguita.

### SCR-10 — La validazione degli artefatti non verifica tutti i legami di provenienza (P2)

Riferimenti: [mqt_model_artifacts.py:182–231](../../esperimento_v2/scripts/mqt_model_artifacts.py#L182), [mqt_model_artifacts.py:299–335](../../esperimento_v2/scripts/mqt_model_artifacts.py#L299), [mqt_model_artifacts.py:339–412](../../esperimento_v2/scripts/mqt_model_artifacts.py#L339).

**Condizione.** Gli artefatti hanno metadati formalmente conformi ma derivano da un manifest diverso o da politiche RL diverse da quelle correnti. **Evidenza.** Il validatore RL non confronta training_manifest_sha256; quello ML non lega source_manifest_sha256 e rl_models al manifest e ai cinque modelli correnti. validate_model_set non aggiunge questi confronti.

**Effetto.** Un insieme formalmente pronto può combinare Training set o politiche non corrispondenti. Non si conclude che gli artefatti reali presenti siano errati. **Intervento proposto.** Verificare gli hash del manifest congelato e delle cinque politiche usate per costruire le etichette prima di dichiarare pronto l’insieme.

**Verifica.** S10_provenance_bindings: metadati sintetici con riferimenti differenti restituiscono zero errori. Nessun modello caricato.

## Copertura e scopo dei singoli file

| File | Righe lette | Scopo | Rilievi |
|---|---:|---|---|
| [01_check_install.py](../../esperimento_v2/scripts/01_check_install.py) | 1–250 | Verifica ambiente Python e versioni, dispositivi congelati e corrispondenza tra modelli canonici e copie operative. | Nessun difetto locale concreto rilevato |
| [02_list_devices.py](../../esperimento_v2/scripts/02_list_devices.py) | 1–43 | Elenca i dispositivi disponibili e, se richiesto, ne mostra le caratteristiche. | Nessun difetto locale concreto rilevato |
| [03_train_rl_model.py](../../esperimento_v2/scripts/03_train_rl_model.py) | 1–629 | Addestra una politica RL per dispositivo, conserva checkpoint dopo gli aggiornamenti e metadati di provenienza. | SCR-01, SCR-08 |
| [04_train_device_selector.py](../../esperimento_v2/scripts/04_train_device_selector.py) | 1–2546 | Produce i risultati circuito-dispositivo riprendibili e addestra il selettore supervisionato usando il Training set train. | SCR-02, SCR-03, SCR-04 |
| [05_sync_models.py](../../esperimento_v2/scripts/05_sync_models.py) | 1–253 | Verifica e installa le copie operative dei modelli canonici con confronto degli hash. | Nessun difetto locale concreto rilevato |
| [06_prepare_experiment_v2.py](../../esperimento_v2/scripts/06_prepare_experiment_v2.py) | 1–202 | Verifica il corpus e prepara le viste di train e validation della seconda versione dell’esperimento. | Nessun difetto locale concreto rilevato |
| [07_prepare_qiskit_dataset.py](../../esperimento_v2/scripts/07_prepare_qiskit_dataset.py) | 1–73 | Espone la preparazione del catalogo Qiskit tramite parametri di ambito, sorgente e dispositivi. | Nessun difetto locale concreto rilevato |
| [07_validate_qcompile.py](../../esperimento_v2/scripts/07_validate_qcompile.py) | 1–530 | Esegue cinque verifiche tecniche per dispositivo e una verifica completa qcompile su un circuito train. | SCR-09 |
| [08_audit_rl_models.py](../../esperimento_v2/scripts/08_audit_rl_models.py) | 1–366 | Riepiloga integrità e provenienza dei modelli RL, andamento osservato e facoltativamente caricamento approfondito. | Nessun difetto locale concreto rilevato |
| [08_generate_qiskit_dataset.py](../../esperimento_v2/scripts/08_generate_qiskit_dataset.py) | 1–143 | Avvia generazione e ripresa dei risultati Qiskit secondo catalogo e protocollo v2. | Nessun difetto locale concreto rilevato |
| [09_build_qiskit_dataset_views.py](../../esperimento_v2/scripts/09_build_qiskit_dataset_views.py) | 1–55 | Costruisce le viste del Dataset dal catalogo e dai risultati disponibili. | Nessun difetto locale concreto rilevato |
| [10_aggregate_qiskit_dataset.py](../../esperimento_v2/scripts/10_aggregate_qiskit_dataset.py) | 1–70 | Aggrega risultati e riepiloghi del Dataset con verifica facoltativa senza scrittura. | Nessun difetto locale concreto rilevato |
| [11_freeze_method_plan_v2.py](../../esperimento_v2/scripts/11_freeze_method_plan_v2.py) | 1–147 | Congela il piano dei metodi e consente soltanto la migrazione storica prevista della politica dei tentativi. | Nessun difetto locale concreto rilevato |
| [12_run_qcompile_v2.py](../../esperimento_v2/scripts/12_run_qcompile_v2.py) | 1–368 | Esegue qcompile isolato, registra esiti per circuito e riprende quelli con provenienza compatibile. | SCR-05 |
| [13_import_llm_decisions_v2.py](../../esperimento_v2/scripts/13_import_llm_decisions_v2.py) | 1–88 | Importa decisioni LLM esterne verificandole rispetto a piano e configurazione congelata. | Nessun difetto locale concreto rilevato |
| [14_evaluate_methods_v2.py](../../esperimento_v2/scripts/14_evaluate_methods_v2.py) | 1–170 | Coordina valutazione dei metodi e costruzione dei riepiloghi dai risultati disponibili. | SCR-06 |
| [15_release_test_v2.py](../../esperimento_v2/scripts/15_release_test_v2.py) | 1–366 | Controlla i prerequisiti per l’apertura Test e, solo su richiesta esplicita, conserva il relativo attestato. | SCR-06, SCR-07 |
| [16_run_pipeline_v2.py](../../esperimento_v2/scripts/16_run_pipeline_v2.py) | 1–607 | Coordina preparazione, addestramento RL, selettore ML, sincronizzazione e verifiche tecniche con ripresa. | SCR-01 |
| [17_rag_v2.py](../../esperimento_v2/scripts/17_rag_v2.py) | 1–58 | Espone preparazione, controllo e interrogazione delle evidenze RAG senza effettuare chiamate LLM. | Nessun difetto locale concreto rilevato |
| [18_qdrant_dashboard.py](../../esperimento_v2/scripts/18_qdrant_dashboard.py) | 1–123 | Prepara una copia delle evidenze in Qdrant locale per consultazione e verifica che equivalga alla sorgente. | Nessun difetto locale concreto rilevato |
| [mqt_model_artifacts.py](../../esperimento_v2/scripts/mqt_model_artifacts.py) | 1–412 | Verifica struttura, metadati e coerenza delle copie dei modelli RL e del selettore ML. | SCR-10 |
| [mqt_predictor_protocol.py](../../esperimento_v2/scripts/mqt_predictor_protocol.py) | 1–750 | Raccoglie costanti, percorsi, verifica del corpus, identità semantica e controlli condivisi del protocollo. | Nessun difetto locale concreto rilevato |
| [report_local_validation_v2.py](../../esperimento_v2/scripts/report_local_validation_v2.py) | 1–247 | Genera relazione e figure esplicative della validation locale v2 da uno studio già sigillato. | Nessun difetto locale concreto rilevato |

## Chiarezza, valori fissi e ottimizzazioni

Le descrizioni iniziali chiariscono in genere lo scopo dei comandi. Il problema principale di leggibilità è la concentrazione di molte responsabilità in `04_train_device_selector.py`, seguito dai flussi di addestramento e coordinamento. Una nuova versione dovrebbe distinguere supervisione dei processi, registrazione degli esiti, costruzione delle etichette e addestramento, conservando le verifiche già presenti. Non sono state proposte aggiunte automatiche di commenti prive di contenuto.

Versioni software, cinque dispositivi, 49 caratteristiche, seed, dimensioni degli split e politica congelata dei tentativi sono scelte dell’esperimento. Non sono difetti perché fissate nel codice e non vanno rese liberamente modificabili nella copia storica. Il percorso dei checkpoint sul disco D è invece una dipendenza dalla macchina che oggi diverge dal coordinatore. Endpoint Qdrant locale e numeri del rapporto validation sono adeguati alla dimostrazione o allo studio specifico; una futura generalizzazione deve renderne esplicito il contesto.

Le ottimizzazioni utili sono riusare verifiche di hash e ZIP entro la stessa operazione, evitare avvio BQSKit senza lavori, mantenere i modelli RL residenti e conservare risultati progressivi prima di operazioni lunghe. La persistenza deve registrare separatamente ogni avvio fisico e ogni interruzione. Per comandi brevi che delegano alle librerie non emerge un beneficio concreto da ulteriori astrazioni.

Le schede JSON distinguono anche limiti diagnostici: soglia del 95% e ultimo valore TensorBoard non certificano il modello corrente; il successo dei sei controlli tecnici non prova qualità scientifica.

## Simulazioni e riproducibilità

I risultati sono in [scripts_simulations.json](scripts_simulations.json) e il riproduttore è [scripts_reproductions.py](scripts_reproductions.py). Usa funzioni estratte via AST dai sorgenti, metadati sintetici, code simulate e directory temporanee. La prova del registro usa soltanto lo scrittore CSV installato di Stable-Baselines3, senza addestrare o caricare modelli.

Sono coperti SCR-02, SCR-03, SCR-04, SCR-05, SCR-07, SCR-08 e SCR-10. SCR-01, SCR-06 e SCR-09 sono verificati tramite i percorsi e i flussi completi del codice. Non sono state aggiunte simulazioni ulteriori né eseguite le prove sperimentali.

Il dettaglio elaborabile è in [scripts.json](scripts.json).

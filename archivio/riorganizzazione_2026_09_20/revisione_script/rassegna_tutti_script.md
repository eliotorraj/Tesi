# Rassegna di tutti gli script operativi

I percorsi sono quelli precedenti allo spostamento. Oggi sono sotto `archivio/esperimento_v2/`. Ogni riga rimanda a una voce completa dell'inventario JSON. «Statica» non significa verifica del comportamento; «manuale parziale» indica i soli intervalli registrati.

| Script | Scopo | Copertura | Commenti/docstring | Costanti candidate | Esito |
|---|---|---|---|---|---|
| `llm_selection/AmdSensors.cs` | Legge i sensori AMD attraverso ADL; non eseguito nella revisione. | Statica | 2 righe di commento | 2 | Sintassi valida |
| `llm_selection/__init__.py` | Selezione locale degli LLM e registri riproducibili per la tesi. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/acquire.py` | Download riprendibile di pesi pubblici con revisioni e SHA-256 verificati. | Statica | Modulo descritto | 7 | Sintassi valida |
| `llm_selection/chat.py` | Avvia una chat locale Qwen, Phi o Gemma, separata dalle prove sperimentali. | Statica | Modulo descritto | 3 | Sintassi valida |
| `llm_selection/cli.py` | Comandi manuali dell'esperimento. Nessun avvio implicito durante status/doctor. | Statica | Modulo descritto | 2 | Sintassi valida |
| `llm_selection/common.py` | Percorsi e scritture durevoli, separati dagli artefatti MQT. | Manuale completa + statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/compact_prompt.py` | Compatibilità degli import precedenti; implementazione in prototype.prompting. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/complete_graph.py` | Prova esplorativa dei grafi; codifica comune in prototype.prompting. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/configuration.py` | Griglia piccola comune; la selezione viene sigillata solo dopo le prove train. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/controller.py` | Supervisore sequenziale: un solo modello, registri persistenti, ripresa esplicita. | Manuale completa + statica | Modulo descritto | 1 | Sintassi valida; R01 |
| `llm_selection/evaluate.py` | Valuta la validation soltanto dopo i sigilli; riusa la matrice Qiskit. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/finalize.py` | Fissa il vincitore locale senza configurare il modello di frontiera o aprire il test. | Statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/gateway.py` | Collegamento locale Windows/WSL con richieste e flussi originali conservati. | Manuale completa + statica | Modulo descritto | 2 | Sintassi valida; R02 |
| `llm_selection/gpu_monitor.ps1` | Raccoglie misure della GPU Windows. | Statica | 0 righe di commento | 0 | Sintassi valida |
| `llm_selection/hardware.py` | Limiti operativi richiesti per le prove; non sono specifiche del produttore. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/inspect_server.ps1` | Ispeziona il processo server Windows. | Statica | 0 righe di commento | 0 | Sintassi valida |
| `llm_selection/inspect_tokenization.py` | Diagnostica del conteggio; usa esclusivamente un prompt tecnico train. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/launch_technical.ps1` | Avvia in background una prova tecnica train tramite WSL. | Manuale completa + statica | 0 righe di commento | 1 | Sintassi valida |
| `llm_selection/minimal_audit.py` | Confronto riproducibile train, senza inferenza: prepara file per llama-tokenize. | Statica | Modulo descritto | 6 | Sintassi valida |
| `llm_selection/output_contract.py` | Compatibilità delle istruzioni, centralizzate in prototype.prompting. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/plots.py` | Grafici eseguiti nel solo ambiente isolato di analisi. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/prepare.py` | Inventario e prompt train/validation; non legge punteggi di validation. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/probe_storage.ps1` | Controlla lo spazio e i percorsi dei dischi Windows. | Statica | 0 righe di commento | 0 | Sintassi valida |
| `llm_selection/probe_wire.py` | Misura una serializzazione candidata sui soli prompt tecnici, senza inferenza. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/prompt_audit.py` | Verifica/esporta prompt senza inferenza. Non apre gli score di validation. | Statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/prompt_report.py` | Riepilogo riproducibile dei prompt e di una prova tecnica train, senza nuovi score. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/provenance.py` | Provenienza leggibile e copie del codice; nessuna variabile segreta salvata. | Manuale completa + statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/recovery.py` | Ispezione delle scritture interrotte; conserva sempre i file originali. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/render_pdf.py` | Esporta tutte le pagine del PDF in PNG per il controllo visivo. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/report.py` | Figure e documento LaTeX generati dai dati congelati, senza numeri trascritti. | Statica | Modulo descritto | 3 | Sintassi valida |
| `llm_selection/resource_probe.ps1` | Legge informazioni sulle risorse Windows. | Statica | 0 righe di commento | 0 | Sintassi valida |
| `llm_selection/run.py` | Esecuzione riprendibile. Questo modulo non carica la matrice degli score. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/runtime_check.py` | Inventario breve del runtime isolato, senza caricare i modelli. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/serve.ps1` | Avvia e sorveglia il server locale con limiti di risorse. | Manuale completa + statica | 0 righe di commento | 4 | Sintassi valida; R01 |
| `llm_selection/server_state.py` | Accerta un arresto senza inventare ora o codice di uscita. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/setup_report.py` | Installazione esplicita del solo compilatore LaTeX e del lettore PDF isolato. | Manuale completa + statica | Modulo descritto | 3 | Sintassi valida |
| `llm_selection/setup_toon.py` | Installa Node e TOON nelle cartelle del progetto, senza cambiare l'ambiente MQT. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/smoke_transport.py` | Prova tecnica sintetica del trasporto, distinta dai circuiti e dalla selezione. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/stop.ps1` | Arresta il processo identificato nel registro dopo averne verificato l'identità. | Manuale completa + statica | 0 righe di commento | 2 | Sintassi valida |
| `llm_selection/storage.py` | Registri del server Windows su D; percorso logico del progetto conservato. | Manuale completa + statica | Modulo descritto | 3 | Sintassi valida |
| `llm_selection/study.py` | Congelamento locale e sigilli: nessuna lettura degli score in questo modulo. | Statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/technical.py` | Riepilogo delle prove train e degli arresti, senza score di validation. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/token_counts.py` | Conteggio preliminare dei prompt con i tokenizer ufficiali, senza tagli. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/tokenization.py` | Conta testi nel runtime separato dei tokenizer, senza cambiare uv.lock. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/tokenize_files.ps1` | Conta i token dei file con il programma Windows. | Statica | 3 righe di commento | 0 | Sintassi valida |
| `llm_selection/toon_audit.py` | Confronta tre rappresentazioni sui cinque train, senza chiamare i modelli. | Statica | Modulo descritto | 4 | Sintassi valida |
| `llm_selection/toon_report.py` | Documento e figure dai conteggi TOON; eseguire nel runtime delle analisi. | Statica | Modulo descritto | 2 | Sintassi valida |
| `llm_selection/train_check.py` | Controllo tecnico train: identità del sorgente e uso delle prove recuperate. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/__init__.py` | Seconda selezione: contratto v4, studi indipendenti e ripresa durevole. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/__main__.py` | Comandi per preparare, provare sul train e avviare uno studio esplicito. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/evaluate.py` | Analisi post-sigillo: riferimento osservato sugli 88 circuiti. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/plots.py` | Rigenera solo le sette figure della validation; non modifica sorgenti LaTeX o risultati. | Statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/v2/report.py` | Rapporto tecnico o di validation, con sorgenti LaTeX e figure. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/run.py` | Episodi v4. Le interruzioni fisiche non consumano tentativi logici. | Manuale completa + statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/settings.py` | Regole esplicite della seconda validation. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/v2/study.py` | Preparazione, congelamento e sigilli indipendenti per ogni studio. | Statica | Modulo descritto | 1 | Sintassi valida |
| `llm_selection/verify_weights.ps1` | Calcola l'impronta dei pesi tramite Windows. | Statica | 1 righe di commento | 0 | Sintassi valida |
| `llm_selection/weights.py` | Verifica i pesi sul percorso Windows senza leggerli nella cache WSL. | Statica | Modulo descritto | 0 | Sintassi valida |
| `llm_selection/wire.py` | Compatibilità degli import precedenti della codifica tabellare. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/__init__.py` | Prototype applications for the thesis workspace. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/__init__.py` | Vista essenziale e contratto corrente condivisi dall'assistente. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/compact.py` | Prompt reversibile: nessun circuito, esempio, campo o valore viene eliminato. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/complete_graph.py` | Rappresentazione esatta e breve dei soli grafi completi di connettività. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/facts.py` | Contratto v4: fatti controllabili e ipotesi libera, senza score di valutazione. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/legacy_rendering.py` | Solo confronto e lettura storica dei prompt v2; non usare per nuove inferenze. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/minimal.py` | Vista LLM essenziale. Il documento canonico e la provenienza restano esterni. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/output_contract.py` | Istruzioni esplicite delle regole già applicate dal validatore. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/rendering.py` | Messaggi essenziali condivisi da chat, prove e tentativi correttivi. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/prompting/toon.py` | TOON ufficiale: vista reversibile, valori controllati dopo la decodifica. | Statica | Modulo descritto | 1 | Sintassi valida |
| `prototype/prompting/toon_runtime/codec.mjs` | Codifica e decodifica TOON con verifica della versione. | Manuale completa + statica | 0 righe di commento | 0 | Sintassi valida |
| `prototype/prompting/wire.py` | Serializzazione tabellare senza perdita: campi e valori restano ricostruibili. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/__init__.py` | Prototipo di compilazione quantistica assistita da un LLM. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/__init__.py` | Espone gli adattatori locali usati dal prototipo. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/compilation.py` | Compila con Qiskit dopo la conferma esplicita dell'utente. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/context.py` | Recupera esempi sicuri dal Dataset e costruisce la richiesta per l'LLM. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/explanations.py` | Costruisce in modo deterministico le spiegazioni già validate. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/hardware.py` | Costruisce il catalogo MQT e applica i vincoli hardware verificabili. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/llm.py` | Adattatori indipendenti dal servizio usato per chiamare l'LLM. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/parsing.py` | Mantiene gli import storici per richieste e maschera hardware. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/qdrant_context.py` | Qdrant locale persistente: raccolta verificata e ricerca esatta filtrata. | Manuale completa + statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/rag_checks.py` | Prove tecniche del recupero: nessuna raccomandazione LLM o compilazione. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/rag_dataset.py` | Fonte RAG unica, provenienza train ed evidenze verificate. | Manuale completa + statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/rag_features.py` | Trasformazione train-only delle 49 feature e distanza Manhattan canonica. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/request.py` | Legge la richiesta, analizza il QASM e ne controlla il significato. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/adapters/validation.py` | Legge e controlla in modo deterministico le raccomandazioni dell'LLM. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/controller.py` | Controllore per la UI con raccomandazioni conservate lato servizio. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/errors.py` | Errori strutturati prodotti durante la preparazione della richiesta. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/factory.py` | Costruzione del prototipo locale con gli adattatori predefiniti. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/models.py` | Modelli del dominio condivisi dai livelli del prototipo. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/ports.py` | Interfacce sostituibili usate dai componenti del prototipo. | Statica | Modulo descritto | 0 | Sintassi valida |
| `prototype/quantum_assistant/schema_validation.py` | Validazione locale del sottoinsieme JSON Schema usato dal progetto. | Statica | Modulo descritto | 1 | Sintassi valida |
| `prototype/quantum_assistant/services.py` | Coordinamento della raccomandazione e della compilazione approvata. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/__init__.py` | Espone gli elementi principali per costruire il Dataset Qiskit. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/aggregation.py` | Riunisce le viste dei singoli dispositivi senza modificarle. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/catalog.py` | Definisce e valida le configurazioni ammesse per il Dataset Qiskit. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/core.py` | Prepara i circuiti, le suddivisioni e i file comuni del Dataset. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/experiment_v2.py` | Contratti deterministici per piani, decisioni e valutazione del protocollo v2. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/generation.py` | Esegue e riprende i tentativi di compilazione diretta con Qiskit. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/reporting.py` | Crea statistiche leggibili per i Dataset Qiskit pilot e full. | Statica | Modulo descritto | 0 | Sintassi valida |
| `qiskit_dataset/views.py` | Riunisce i seed e crea gli esempi RAG riservati all'addestramento. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/01_check_install.py` | Verify the exact MQT Predictor 2.4.0 environment and frozen protocol. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/02_list_devices.py` | Elenca i dispositivi quantistici disponibili tramite MQT Bench. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/03_train_rl_model.py` | Train a non-smoke RL compiler for one device and figure of merit. | Manuale parziale + statica | Modulo descritto | 1 | Sintassi valida |
| `scripts/04_train_device_selector.py` | Compile resumably and train the supervised MQT device selector. | Statica | Modulo descritto | 5 | Sintassi valida |
| `scripts/05_sync_models.py` | Synchronize the five frozen MQT models with the active Python runtime. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/06_prepare_experiment_v2.py` | Verifica il corpus congelato e prepara solo train/validation per il protocollo v2. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/07_prepare_qiskit_dataset.py` | Prepara le suddivisioni riproducibili dei circuiti del Dataset Qiskit. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/07_validate_qcompile.py` | Run strict per-device RL canaries and one end-to-end qcompile canary. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/08_audit_rl_models.py` | Audit the five expected-fidelity RL models before deciding resume or restart. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/08_generate_qiskit_dataset.py` | Esegue i tentativi Qiskit con salvataggio, limite di tempo e ripresa. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/09_build_qiskit_dataset_views.py` | Costruisce gli aggregati e gli esempi RAG destinati all'addestramento. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/10_aggregate_qiskit_dataset.py` | Unisce le viste dei dispositivi in un Dataset generale senza modificarle. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/11_freeze_method_plan_v2.py` | Congela il piano dei metodi e le estrazioni casuali senza leggere gli score. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/12_run_qcompile_v2.py` | Esegue qcompile tre volte per circuito con timeout e ripresa rigorosa. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/13_import_llm_decisions_v2.py` | Valida e congela decisioni LLM terminali senza consultare gli score. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/14_evaluate_methods_v2.py` | Valuta tutti i metodi sullo stesso split dopo avere sigillato le scelte. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/15_release_test_v2.py` | Verifica tutti i prerequisiti e, su richiesta, apre lo split test. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/16_run_pipeline_v2.py` | Orchestra le fasi lunghe del protocollo MQT Predictor 2.4-v2. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/17_rag_v2.py` | Prepara, verifica e prova il recupero RAG senza LLM né compilazioni. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/18_qdrant_dashboard.py` | Copia nella dashboard locale i punti dell'indice RAG già verificato. | Statica | Modulo descritto | 1 | Sintassi valida |
| `scripts/bootstrap_ubuntu.sh` | Prepara Python 3.12 e le dipendenze fissate in uv.lock. | Manuale completa + statica | 1 righe di commento | 2 | Sintassi valida |
| `scripts/mqt_model_artifacts.py` | Shared validation helpers for canonical and runtime MQT model artifacts. | Statica | Modulo descritto | 0 | Sintassi valida |
| `scripts/mqt_predictor_protocol.py` | Frozen MQT Predictor protocol and target-validation helpers. | Statica | Modulo descritto | 1 | Sintassi valida |
| `scripts/report_local_validation_v2.py` | Resoconto esplicativo post-selezione: nessuna nuova inferenza o scelta. | Statica | Modulo descritto | 1 | Sintassi valida |
| `tests/test_claim_evidence_validation.py` | Verifiche automatiche: _StaticRetriever, _CountingRegistryBuilder, _RegistrySpyValidator, _FakeCompiler, ClaimEvidenceValidationTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_compact_prompt.py` | Controlli su dati invariati, fonti inventate, errori reali e ripresa. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_experiment_v2.py` | Verifiche automatiche: ExperimentV2Tests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_llm_chat.py` | Chat manuale: scelta modello, controlli e isolamento dei processi (avvii simulati). | Statica | Modulo descritto | 1 | Sintassi valida |
| `tests/test_llm_output_validation.py` | Verifiche automatiche: _CountingRetriever, _FakeCompiler, LlmOutputValidationTests, BrokenValidator, MismatchedFilter. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_llm_selection.py` | Verifiche delle proprietà scientifiche e della ripresa, con soli dati sintetici. | Statica | Modulo descritto | 4 | Sintassi valida |
| `tests/test_llm_selection_v2.py` | Contratto v4, fallback, ripresa e confronto su riferimenti incompleti. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_minimal_prompt.py` | Nuovo contratto: contenuti minimi, citazioni locali e controlli applicativi. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_mqt_predictor_protocol.py` | Verifiche automatiche: PredictorProtocolTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_mqt_support_scripts.py` | Verifiche automatiche: DummyClassifier, ModelArtifactTests, QcompileAuditTests, RLAuditTests. | Statica | Scenari nei nomi dei test | 1 | Sintassi valida |
| `tests/test_prototype_architecture.py` | Verifiche automatiche: PrototypeArchitectureTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_prototype_v2.py` | Verifiche automatiche: PrototypeV2Tests, PlanAlignmentTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_qdrant_dashboard.py` | Controlla che la copia di consultazione rilevi modifiche reali ai dati. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_qdrant_retrieval.py` | Ricerca reale Qdrant locale, precisione, persistenza e integrità train. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_qiskit_dataset.py` | Verifiche automatiche: QiskitCatalogTests, QiskitSplitAndPlanTests, QiskitAggregationTests, QiskitFailureRecordTests, JsonSchemaFilesTests. | Statica | Scenari nei nomi dei test | 1 | Sintassi valida |
| `tests/test_qiskit_dataset_aggregation.py` | Verifiche automatiche: GlobalDatasetAggregationTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_qiskit_reporting.py` | Verifiche automatiche: QiskitReportingTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_request_constraints.py` | Verifiche automatiche: PhaseTwoRequestTests. | Statica | Scenari nei nomi dei test | 1 | Sintassi valida |
| `tests/test_run_pipeline_v2.py` | Verifiche automatiche: PipelineRunnerTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_toon_prompt.py` | Verifica il codec reale e la conservazione dei dati attraverso Node/TOON. | Statica | Modulo descritto | 0 | Sintassi valida |
| `tests/test_train_device_selector.py` | Verifiche automatiche: DeviceSelectorTrainingTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_train_rl_model.py` | Verifiche automatiche: RLObservationSpaceTests, RLTrainingRuntimeTests. | Statica | Scenari nei nomi dei test | 0 | Sintassi valida |
| `tests/test_workspace_layout.py` | Verifiche automatiche: WorkspaceLayoutTests. | Statica | Scenari nei nomi dei test | 4 | Sintassi valida |

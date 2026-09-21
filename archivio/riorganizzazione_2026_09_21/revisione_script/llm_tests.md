# Revisione dei sorgenti LLM e dei test

La lettura manuale copre integralmente **72 file e 11.278 righe**. Ogni scheda nel registro `llm_tests.json` riporta scopo, dipendenze, condizioni da conservare, portabilità, opportunità di miglioramento e intervalli letti. Le impronte SHA-256 sono state ricontrollate dopo la lettura: tutti i sorgenti coincidono con quelli esaminati. Nessun sorgente congelato è stato modificato.

L’inventario iniziale indicava 11.403 righe. Il file `llm_selection/v2/plots.py` contiene effettivamente 74 righe, contro le 199 dell’inventario. La copertura si riferisce al contenuto presente sul ramo `riorganizzazione-prototipo`, identificato dalle impronte complete nel JSON.

## Rilievi verificabili

P2 indica un difetto funzionale da correggere se il codice viene riusato; P3 indica un problema circoscritto di risorse o copertura. I sorgenti storici restano conservati. Le correzioni proposte riguardano una copia attiva.

### LLM-01 · P3 · Contesto ADL non distrutto se il costruttore fallisce

Fonte: `llm_selection/AmdSensors.cs`, righe 30–51.

Dopo ADL2_Main_Control_Create riuscito, le eccezioni di enumerazione escono dal costruttore senza chiamare Destroy; il finally libera soltanto buffer. L oggetto non viene consegnato al chiamante e non ha finalizzatore.

Perdita risorsa nativa nelle ripetute inizializzazioni fallite.

Nella versione futura distruggere context in catch del costruttore.

### LLM-02 · P2 · File .part vuoto impedisce la ripresa

Fonte: `llm_selection/acquire.py`, righe 51–61.

Se .part esiste con zero byte, offset=0 e open usa xb sul file gia esistente: FileExistsError prima di scrivere.

Un interruzione subito dopo la creazione del file blocca tutti i tentativi successivi senza intervento manuale. Anche repair_tail su un parziale inferiore a 256 MiB lo tronca a zero e incontra lo stesso errore.

Gestire esplicitamente il parziale vuoto preservando le verifiche.

### LLM-03 · P2 · Riutilizzo episodio terminale non controlla il budget richiesto

Fonte: `llm_selection/run.py`, righe 88–95.

Il ramo decision.json esistente verifica prompt e configurazione e restituisce subito. Il confronto timeout/max_attempts esiste solo nel ramo begin incompleto, righe 119-120.

Riusando un etichetta tecnica con timeout o numero tentativi diversi si ottiene il vecchio risultato senza errore; la nuova impostazione non viene provata.

Verificare budget anche prima del ritorno del risultato terminale.

Rilievo sul comando tecnico con --technical-timeout/--technical-max-attempts ammessi. Il resume intenzionale della stessa cella con budget identico resta corretto; validation congelata verifica separatamente i budget.

### LLM-06 · P2 · Il rapporto v2 non verifica le impronte delle analisi lette

Fonte: `llm_selection/v2/report.py`, righe 28–33.

Dopo require_sealed vengono letti direttamente analysis/episode_results.json e analysis/selection.json. Il sigillo delle decisioni non comprende la cartella analysis; le sue impronte sono registrate separatamente da v2/evaluate.py:205-208 in selection_complete.json, mai verificate qui.

Una modifica accidentale a una analisi dopo la selezione può entrare nel rapporto senza essere rilevata dai sigilli originali, rendendo rapporto e selezione finale incoerenti.

Nella copia attiva verificare selection_complete.json e le impronte delle analisi prima di generare il rapporto; mantenere gli artefatti storici.

### LLM-04 · P2 · Il sigillo v2 non rifiuta file aggiunti dopo il congelamento

Fonte: `llm_selection/v2/study.py`, righe 162–172.

require_sealed verifica solo i percorsi seal.files; non confronta insieme effettivo dei file, a differenza di study.verify_model_seal v1. evaluate.py e episode_data leggono summary tramite glob, quindi un nuovo attempt_*/summary.json puo entrare nei costi/fatti senza essere sigillato.

Il rapporto puo incorporare dati non coperti dalle impronte della decisione sigillata.

Nella copia futura confrontare file effettivi con il sigillo e allineare tentativi alla decisione.

### LLM-05 · P3 · Avvio diretto salta la classe finale di test

Fonte: `tests/test_llm_selection_v2.py`, righe 320–324.

unittest.main() precede la definizione di TechnicalCodeReviewTests e termina il processo; unittest discovery importa invece la classe e la esegue.

Eseguendo questo file direttamente si omettono i due controlli finali del confronto codice tecnico.

Usare discovery; in copia futura porre unittest.main alla fine del file.

## Riproduzioni brevi

Le tre prove seguenti hanno eseguito le funzioni originali estratte tramite AST, con dipendenze simulate e file temporanei. Non hanno avviato inferenze, compilazioni quantistiche o rete. Servono a confermare i singoli rami difettosi, non a certificare l’intero sistema.

- **LLM-02**: FileExistsError con .part esistente di zero byte; destinazione non creata.
- **LLM-03**: Budget originale 100s/3; chiamata 1s/1 restituisce lo stesso vecchio risultato, come la ripresa intenzionale 100s/3.
- **LLM-04**: Aggiunta attempt_999/summary.json dopo i sigilli: require_sealed accetta ancora; hash dei file gia sigillati invariati.

La perdita ADL è dedotta dal ciclo di vita nativo nel costruttore e non è stata riprodotta sul driver. Il problema di esecuzione diretta del test deriva dalla posizione di `unittest.main()` prima dell’ultima classe. Il controllo mancante del rapporto è verificato leggendo il flusso e il contenuto dei sigilli.

## Condizioni scientifiche e limiti

Le prove tecniche sul train, la selezione sulla validation e il Test hanno ruoli distinti nei moduli letti. La prima selezione confronta la qualità sui casi comuni con riferimento completo. La seconda distingue il riferimento osservato dal massimo esaustivo. I valori mancanti restano espliciti. I rapporti dichiarano che la correttezza dei fatti strutturati non certifica l’ipotesi libera o una causa della scelta. Il recupero dello stesso circuito di train è intenzionale nelle prove tecniche e non misura generalizzazione.

I test sui vecchi contratti usano esplicitamente la modalità storica. I test MQT attuali fissano la versione 2.4.0; i dati 2.3.0 appartengono ai cataloghi storici. I test RL includono una prova minima di addestramento, utile per la compatibilità della pipeline ma insufficiente per dimostrare qualità. Non è stata eseguita in questa revisione.

Alcuni test dipendono da artefatti preparati: prompt tecnici train, mini Dataset pilot, codec Node/TOON e pacchetti MQT. La sola lettura non dimostra che la suite completa passi su un ambiente nuovo. Il JSON registra queste dipendenze. Nessun Test sperimentale è stato aperto.

I percorsi Windows, le chiamate ADL, i blocchi Linux e i runtime separati sono assunzioni dell’ambiente storico. Una futura versione portabile deve conservarne le informazioni di provenienza, rendendo configurabili i percorsi. Eventuali conteggi dei token riusati richiedono gli stessi hash di input, tokenizer, modello del messaggio e codec.

## Copertura per file

| File | Righe lette | Rilievi |
|---|---:|---|
| `llm_selection/AmdSensors.cs` | 1–76 | LLM-01 |
| `llm_selection/__init__.py` | 1–1 | Nessuno aggiuntivo verificato |
| `llm_selection/acquire.py` | 1–113 | LLM-02 |
| `llm_selection/chat.py` | 1–130 | Nessuno aggiuntivo verificato |
| `llm_selection/cli.py` | 1–104 | Nessuno aggiuntivo verificato |
| `llm_selection/compact_prompt.py` | 1–6 | Nessuno aggiuntivo verificato |
| `llm_selection/complete_graph.py` | 1–26 | Nessuno aggiuntivo verificato |
| `llm_selection/configuration.py` | 1–31 | Nessuno aggiuntivo verificato |
| `llm_selection/evaluate.py` | 1–230 | Nessuno aggiuntivo verificato |
| `llm_selection/finalize.py` | 1–87 | Nessuno aggiuntivo verificato |
| `llm_selection/gpu_monitor.ps1` | 1–16 | Nessuno aggiuntivo verificato |
| `llm_selection/hardware.py` | 1–38 | Nessuno aggiuntivo verificato |
| `llm_selection/inspect_server.ps1` | 1–9 | Nessuno aggiuntivo verificato |
| `llm_selection/inspect_tokenization.py` | 1–18 | Nessuno aggiuntivo verificato |
| `llm_selection/minimal_audit.py` | 1–161 | Nessuno aggiuntivo verificato |
| `llm_selection/output_contract.py` | 1–4 | Nessuno aggiuntivo verificato |
| `llm_selection/plots.py` | 1–81 | Nessuno aggiuntivo verificato |
| `llm_selection/prepare.py` | 1–63 | Nessuno aggiuntivo verificato |
| `llm_selection/probe_storage.ps1` | 1–18 | Nessuno aggiuntivo verificato |
| `llm_selection/probe_wire.py` | 1–24 | Nessuno aggiuntivo verificato |
| `llm_selection/prompt_audit.py` | 1–82 | Nessuno aggiuntivo verificato |
| `llm_selection/prompt_report.py` | 1–98 | Nessuno aggiuntivo verificato |
| `llm_selection/recovery.py` | 1–55 | Nessuno aggiuntivo verificato |
| `llm_selection/render_pdf.py` | 1–13 | Nessuno aggiuntivo verificato |
| `llm_selection/report.py` | 1–171 | Nessuno aggiuntivo verificato |
| `llm_selection/resource_probe.ps1` | 1–9 | Nessuno aggiuntivo verificato |
| `llm_selection/run.py` | 1–290 | LLM-03 |
| `llm_selection/runtime_check.py` | 1–12 | Nessuno aggiuntivo verificato |
| `llm_selection/server_state.py` | 1–18 | Nessuno aggiuntivo verificato |
| `llm_selection/setup_toon.py` | 1–35 | Nessuno aggiuntivo verificato |
| `llm_selection/smoke_transport.py` | 1–16 | Nessuno aggiuntivo verificato |
| `llm_selection/study.py` | 1–202 | Nessuno aggiuntivo verificato |
| `llm_selection/technical.py` | 1–36 | Nessuno aggiuntivo verificato |
| `llm_selection/token_counts.py` | 1–24 | Nessuno aggiuntivo verificato |
| `llm_selection/tokenization.py` | 1–15 | Nessuno aggiuntivo verificato |
| `llm_selection/tokenize_files.ps1` | 1–21 | Nessuno aggiuntivo verificato |
| `llm_selection/toon_audit.py` | 1–155 | Nessuno aggiuntivo verificato |
| `llm_selection/toon_report.py` | 1–122 | Nessuno aggiuntivo verificato |
| `llm_selection/train_check.py` | 1–66 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/__init__.py` | 1–1 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/__main__.py` | 1–182 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/evaluate.py` | 1–209 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/plots.py` | 1–74 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/report.py` | 1–146 | LLM-06 |
| `llm_selection/v2/settings.py` | 1–43 | Nessuno aggiuntivo verificato |
| `llm_selection/v2/study.py` | 1–177 | LLM-04 |
| `llm_selection/verify_weights.ps1` | 1–23 | Nessuno aggiuntivo verificato |
| `llm_selection/weights.py` | 1–19 | Nessuno aggiuntivo verificato |
| `llm_selection/wire.py` | 1–4 | Nessuno aggiuntivo verificato |
| `tests/test_claim_evidence_validation.py` | 1–1107 | Nessuno aggiuntivo verificato |
| `tests/test_compact_prompt.py` | 1–165 | Nessuno aggiuntivo verificato |
| `tests/test_experiment_v2.py` | 1–657 | Nessuno aggiuntivo verificato |
| `tests/test_llm_chat.py` | 1–115 | Nessuno aggiuntivo verificato |
| `tests/test_llm_output_validation.py` | 1–596 | Nessuno aggiuntivo verificato |
| `tests/test_llm_selection.py` | 1–345 | Nessuno aggiuntivo verificato |
| `tests/test_llm_selection_v2.py` | 1–353 | LLM-05 |
| `tests/test_minimal_prompt.py` | 1–301 | Nessuno aggiuntivo verificato |
| `tests/test_mqt_predictor_protocol.py` | 1–55 | Nessuno aggiuntivo verificato |
| `tests/test_mqt_support_scripts.py` | 1–302 | Nessuno aggiuntivo verificato |
| `tests/test_prototype_architecture.py` | 1–310 | Nessuno aggiuntivo verificato |
| `tests/test_prototype_v2.py` | 1–151 | Nessuno aggiuntivo verificato |
| `tests/test_qdrant_dashboard.py` | 1–62 | Nessuno aggiuntivo verificato |
| `tests/test_qdrant_retrieval.py` | 1–318 | Nessuno aggiuntivo verificato |
| `tests/test_qiskit_dataset.py` | 1–733 | Nessuno aggiuntivo verificato |
| `tests/test_qiskit_dataset_aggregation.py` | 1–156 | Nessuno aggiuntivo verificato |
| `tests/test_qiskit_reporting.py` | 1–162 | Nessuno aggiuntivo verificato |
| `tests/test_request_constraints.py` | 1–714 | Nessuno aggiuntivo verificato |
| `tests/test_run_pipeline_v2.py` | 1–187 | Nessuno aggiuntivo verificato |
| `tests/test_toon_prompt.py` | 1–96 | Nessuno aggiuntivo verificato |
| `tests/test_train_device_selector.py` | 1–400 | Nessuno aggiuntivo verificato |
| `tests/test_train_rl_model.py` | 1–343 | Nessuno aggiuntivo verificato |
| `tests/test_workspace_layout.py` | 1–96 | Nessuno aggiuntivo verificato |

La copertura indica lettura integrale, non un esito positivo di esecuzione. I risultati delle tre riproduzioni sono conservati in forma strutturata nel JSON insieme a metodo e limitazioni.

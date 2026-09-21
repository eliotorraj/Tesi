# Revisione manuale di prototype e qiskit_dataset

Tutti i **38 file assegnati, 13.399 righe**, sono stati letti integralmente. La copertura non deriva da una sola analisi sintattica. Gli intervalli e le impronte SHA-256 di ogni sorgente letto sono nel file `prototype_data.json`. Le impronte coincidono con l’inventario assegnato; nessun sorgente congelato è stato modificato.

La revisione riguarda i sorgenti storici in `archivio/esperimento_v2/`. Non comprende `rag_dataset.py` e `qdrant_context.py`, assegnati a una revisione precedente. La lettura ha seguito contratti, chiamanti e dati necessari, distinguendo i percorsi storici v2/v3 dal contratto facts v4. Non è stato aggiornato il grafo.

## Prove eseguite e limiti

Sono state eseguite soltanto riproduzioni circoscritte: due casi numerici del validatore JSON, una compilazione di Bell creato in una cartella temporanea, una sostituzione di record in cache temporanea due verifiche su record sintetici in memoria e una scadenza simulata nel validatore del Target. Nessun modello LLM o MQT addestrato è stato caricato; nessun Dataset nuovo è stato generato; nessun circuito di validation o Test è stato aperto. La compilazione tecnica ha usato il Target sintetico ibm_falcon_27 e non dimostra qualità delle raccomandazioni.

I difetti indicano comportamenti del codice su ingressi riproducibili o condizioni esplicite. Non costituiscono prova che i risultati congelati siano alterati. Il controllo delle impronte degli artefatti completi è separato da questa lettura dei sorgenti. Non sono state eseguite prove su Windows nativo o misure complete delle prestazioni.

## Rilievi

### PD-08 — P3 — La allowlist legacy viene resa insieme prima di controllare i tipi

File: `archivio/esperimento_v2/prototype/quantum_assistant/adapters/request.py`, righe 210–219.

len(set(allowed_devices)) precede il controllo isinstance(device_id,str); un elemento lista/dizionario provoca TypeError prima di _raise_issue.

Riproduzione o evidenza: Evidenza statica: UiSubmission con allowed_devices=([],) raggiunge set(([],)) alla riga 213, che solleva TypeError: unhashable type: list. Non è stato eseguito un circuito né richiamata la versione legacy in questa revisione.

Effetto e limiti: Difetto limitato al vecchio ingresso Python UiSubmission, non al normale ingresso JSON validato o al comando del dimostratore.

Intervento proposto: Controllare prima che gli elementi siano stringhe, poi unicità e formato.

### PD-01 — P2 — Alcuni numeri JSON interrompono la validazione invece di produrre un errore strutturato

File: `archivio/esperimento_v2/prototype/quantum_assistant/schema_validation.py`, righe 167–181.

parse_constant rifiuta NaN/Infinity letterali ma json.loads converte 1e999 in float inf. uniqueItems serializza con allow_nan=False prima di controllare il tipo degli elementi. _is_type(number) converte inoltre interi arbitrari in float senza intercettare OverflowError.

Riproduzione o evidenza: decode_json_object('{"evidence":[1e999]}') restituisce {"evidence":[inf]}; validate_instance({"type":"array","uniqueItems":True,"items":{"type":"string"}}, value["evidence"], error_code="TEST") solleva ValueError: Out of range float values are not JSON compliant: inf. validate_instance({"type":"number"},10**1000,error_code="TEST") solleva OverflowError: int too large to convert to float.

Effetto e limiti: Richieste JSON malformate e risposte del contratto minimo v3 possono uscire dal percorso RequestValidationError/ValidationResult. facts.verify v4 effettua prima json.dumps(allow_nan=False), quindi la risposta LLM del dimostratore è protetta; il parser copiato conserva il limite per chiamate programmatiche.

Intervento proposto: Controllare ricorsivamente numeri finiti dopo il decode e gestire overflow; validare gli elementi prima di uniqueItems oppure trasformare anche tali errori in ValidationIssue. Non modificare qui gli originali.

### PD-04 — P2 — Il controllo raw/aggregati non ricalcola mediana ed eleggibilità

File: `archivio/esperimento_v2/qiskit_dataset/aggregation.py`, righe 289–355.

_validate_summary_run_links confronta run_ids, osservazioni e quattro conteggi, ma non ranking_score, score_statistics, complete o eligible_for_ranking, poi tali valori alimentano build_rag_examples.

Riproduzione o evidenza: Con un raw success score=0.5 e una sola osservazione identica, un aggregato con ranking_score=0.99 ed eligible_for_ranking=True supera _validate_summary_run_links senza eccezioni. Record interamente sintetici in memoria.

Effetto e limiti: La verifica autonoma della vista globale non scopre un aggregato numericamente alterato o incoerente. La pipeline dispone però di ricostruzione separata in views.aggregate_runs, sigilli del corpus e controllo più forte in experiment_v2.validate_qiskit_matrix (righe 795–858), che ricalcola la mediana. Questo esempio non dimostra alterazioni delle etichette congelate né supera quei controlli aggiuntivi.

Intervento proposto: Riutilizzare un controllo numerico condiviso prima della costruzione globale del RAG, verificando anche statistiche ed eleggibilità rispetto ai raw.

### PD-06 — P2 — Il riepilogo non dichiara quanti successi contribuiscono alla mediana del regret

File: `archivio/esperimento_v2/qiskit_dataset/experiment_v2.py`, righe 1296–1314.

regrets esclude i successi con regret_absolute=None, mentre l’oggetto finale espone successes ma non len(regrets). Ciò avviene quando un metodo riesce e l’oracolo è incompleto.

Riproduzione o evidenza: summarize_results su due record success del medesimo metodo, con regret_absolute rispettivamente 0.0 e None, restituisce successes=2 e median_regret_absolute=0.0 senza un campo che indichi l’unico valore confrontabile. Record sintetici in memoria.

Effetto e limiti: Il lettore del solo riepilogo non ricostruisce il denominatore della mediana. I record dettagliati conservano None, quindi l’informazione non è persa nel dato grezzo. Nessuna affermazione sul numero di casi mancanti delle prove correnti.

Intervento proposto: Aggiungere comparable_regret_count e missing_oracle_count nei riepiloghi futuri e mostrare il denominatore accanto alla statistica.

### PD-02 — P1 — Il QASM eseguito non viene confrontato con l’impronta registrata nel piano

File: `archivio/esperimento_v2/qiskit_dataset/generation.py`, righe 498–501.

execute_attempt apre direttamente source_path. La sorgente è verificata durante la preparazione, ma non di nuovo quando viene compilata; run_id e circuit.source_sha256 restano quelli del task.

Riproduzione o evidenza: Eseguito un solo Bell tecnico in TemporaryDirectory, con task.circuit.source_sha256="0"*64, target ibm_falcon_27, optimization_level=2, seed_transpiler=7, num_processes=1, timeout=10s. Esito success e failure=null; record conserva 64 zeri, mentre SHA256 reale del file è 7d44e21c07f288034b521edb642e70a4664d05b87b182d9d3604593e45ceee0b. Nessun record del Dataset usato o scritto.

Effetto e limiti: Una modifica fra preparazione ed esecuzione può associare score e circuito compilato a un’identità sorgente sbagliata; il controllo successivo dei soli metadati non la rileva. È un difetto latente, non prova di alterazione dei dati congelati. Il parser del nuovo dimostratore calcola l’hash dell’ingresso reale e non usa questo generatore.

Intervento proposto: Leggere i byte una sola volta, confrontarli al digest atteso e compilare il contenuto verificato. Un mismatch deve essere registrato come errore di sorgente.

### PD-03 — P2 — La ripetizione di un run sostituisce l’esito precedente nella cache

File: `archivio/esperimento_v2/qiskit_dataset/generation.py`, righe 875–889.

retry_failures e force rimettono in coda lo stesso run_id; _persist_record usa sempre lo stesso percorso e atomic_json_write lo sostituisce. Non esiste un identificativo distinto del tentativo fisico o un registro precedente.

Riproduzione o evidenza: In cache temporanea isolata, _persist_record del medesimo run_id prima con status timeout e poi success lascia un solo JSON, con status success. Esito precedente non più presente.

Effetto e limiti: Le opzioni di ripetizione perdono errori, tempi e diagnostica del primo tentativo, impedendo di ricostruire tutti gli esiti. Non è stata invocata alcuna ripetizione sui risultati congelati.

Intervento proposto: Conservare ogni esecuzione fisica separatamente e mantenere un indice che indica il risultato scelto per la vista corrente, senza sovrascrivere gli esiti sfavorevoli.

### PD-05 — P2 — Su Windows nativo il timeout dichiarato viene ignorato

File: `archivio/esperimento_v2/qiskit_dataset/generation.py`, righe 349–369.

Quando signal non espone SIGALRM, _hard_timeout esegue yield senza limite. Il coordinatore attende FIRST_COMPLETED senza una scadenza esterna, quindi non compensa questa assenza.

Riproduzione o evidenza: Evidenza statica della diramazione not hasattr(signal,"SIGALRM") alla riga 352. Nessuna prova lunga o tentativo Windows è stato avviato.

Effetto e limiti: L’esportazione diretta del generatore su Windows non conserva la politica temporale registrata. L’ambiente sperimentale Linux/WSL resta il contesto previsto; anche lì SIGALRM non è una garanzia di terminazione immediata durante chiamate native.

Intervento proposto: Rifiutare esplicitamente piattaforme senza supporto oppure eseguire ciascun tentativo in un processo sorvegliato dal padre. Non dichiarare equivalenza temporale senza misurarla.

### PD-07 — P3 — Il testo delle parità usa un criterio diverso dall’ordinamento

File: `archivio/esperimento_v2/qiskit_dataset/views.py`, righe 571–580.

La scelta ordina lo score esatto; le liste tied_* usano math.isclose(rel_tol=1e-12,abs_tol=1e-15). Se un dispositivo successivo nel catalogo ha score appena maggiore ma entro tolleranza, vince per score, mentre selection_reason e testo sostengono che abbia vinto il tie-break del catalogo.

Riproduzione o evidenza: Evidenza aritmetica: con ordine [A,B], score A=0.5 e B=0.5000000000001, la chiave (-score,ordine) seleziona B; math.isclose considera entrambi pari e attiva il ramo tie_break_catalog_order. Non sono stati letti score sperimentali per cercare casi reali.

Effetto e limiti: Possibile spiegazione inesatta della regola di scelta per score quasi uguali; non altera la scelta numerica già congelata.

Intervento proposto: Distinguere parità esatta, che attiva il tie-break, da equivalenza numerica entro tolleranza nel testo e nei metadati futuri.

### PD-09 — P2 — Il controllo del Target intercetta il timeout e lo riclassifica come errore del circuito

File: `archivio/esperimento_v2/qiskit_dataset/generation.py`, righe 384–399.

validate_compiled_circuit cattura Exception durante GatesInBasis e CheckMap. Anche AttemptTimeoutError generato da SIGALRM appartiene a questa classe: viene trasformato in validation_errors. execute_attempt riceve allora is_executable_on_target=False e genera TargetValidationError, registrando failure/target_invalid invece di timeout.

Riproduzione o evidenza: Con circuito e Target minimi in memoria, patch di qiskit.transpiler.passes.GatesInBasis per sollevare AttemptTimeoutError("synthetic deadline"). validate_compiled_circuit restituisce basis_valid=null, connectivity_valid=true, validation_errors=["GatesInBasis:AttemptTimeoutError:synthetic deadline"], is_executable_on_target=false, senza propagare la scadenza. Nessuna compilazione o attesa reale in questa riproduzione.

Effetto e limiti: Una scadenza durante il controllo della base o della mappa viene classificata in modo errato nei registri. Non è stato cercato né affermato un caso concreto tra i risultati congelati.

Intervento proposto: Propagare esplicitamente AttemptTimeoutError prima degli except Exception generici, mantenendo la distinzione tra scadenza e Target realmente non valido.

## Distinzioni da conservare

- Le evidenze RAG contengono risultati storici del solo train. Il codice letto non inserisce nel prompt lo score del nuovo ingresso. La presenza di controlli sui dati non sostituisce il sigillo del corpus.
- Il servizio storico costruisce normalmente il contratto v3; il verificatore facts v4 è un ingresso distinto. La presenza di `facts.py` non trasforma automaticamente tutta la fabbrica nel flusso sperimentale ufficiale.
- Nel contratto v4 i fatti e la coppia dispositivo/configurazione sono controllati; l’ipotesi testuale rimane dichiaratamente non verificata. Tre tentativi e ripiego sono gestiti dal chiamante, fuori dai moduli di prompt.
- Lo score è expected fidelity sul Target sintetico. Non è una misura da hardware reale e le spiegazioni non stabiliscono rapporti causali.
- PD-01 è ereditabile dal parser copiato nel dimostratore tramite ingresso programmatico. Il controllo preventivo di `facts.verify` protegge invece la risposta v4. PD-02, PD-03 e PD-05 riguardano il generatore storico, non il percorso `prototipo/app.py`.

## Schede dei file

### `archivio/esperimento_v2/prototype/__init__.py`

Lettura: **1–1**, SHA-256 `4056a7f00459bae311abefbb1aa5e4a4f2351d889be64e11a26e93d081b61811`.

Dichiara il pacchetto storico prototype.

Contratti verificati: Nessuna esecuzione o dipendenza introdotta dal file.

Dipendenze: nessuna.

Portabilità: Portabile; resta necessario il corretto percorso di importazione.

Ottimizzazione possibile: Nessuna ottimizzazione utile.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/__init__.py`

Lettura: **1–5**, SHA-256 `0e18f00b16784733f8b22841dbcf9451a176ba0b4b13d1bbcbbb1f5ea60e025e`.

Espone i punti di ingresso per rappresentare i prompt.

Contratti verificati: Le esportazioni rimandano ai convertitori senza riscrivere contenuti.

Dipendenze: `minimal`, `rendering`.

Portabilità: Le dipendenze dei convertitori, in particolare Node, determinano la portabilità.

Ottimizzazione possibile: Evitare di aggiungere importazioni di componenti costosi a questo ingresso.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/compact.py`

Lettura: **1–173**, SHA-256 `744d3f7be7bfdeb49c256d9b5d018a64a09721d100cf4a0dee78d147ed6cb986`.

Codifica v2 senza perdita mediante alias, tabelle e dizionario delle ripetizioni.

Contratti verificati: Marcatori riservati rifiutati; ripristino canonico confrontato con originale; espansione limitata ai campi identificativi previsti.

Dipendenze: `.`, `__future__`, `collections`, `copy`, `hashlib`, `json`, `prototype.quantum_assistant.adapters.validation`, `prototype.quantum_assistant.schema_validation`, `re`, `wire`.

Portabilità: Python; non dipende da GPU o servizi. È una rappresentazione storica distinta dal contratto v4.

Ottimizzazione possibile: Le scansioni e serializzazioni ricorsive possono essere riutilizzate; verificare sempre la medesima rappresentazione canonica.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/complete_graph.py`

Lettura: **1–30**, SHA-256 `82773d23ceaf6a7057d57df0554138544588de3b6f686b44af43440e6cc7661e`.

Sostituisce l’elenco completo dei collegamenti con una descrizione reversibile.

Contratti verificati: Compressione soltanto se il grafo coincide esattamente con quello diretto completo; ripristino verificabile.

Dipendenze: `copy`, `json`.

Portabilità: Python e strutture JSON; nessun percorso di sistema.

Ottimizzazione possibile: La costruzione della lista attesa richiede spazio quadratico; un controllo per cardinalità e insieme potrebbe evitare una seconda lista.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/facts.py`

Lettura: **1–132**, SHA-256 `b82bc77517c51fd6e571f152a5adbf06ebab144cf96617d97630c17fa40ce937`.

Costruisce e verifica il contratto v4 con fatti controllabili e ipotesi testuale.

Contratti verificati: Uno o due fatti; scelta limitata a dispositivo compatibile e configurazione ammessa; citazioni risolte negli esempi correnti; testo ipotetico esplicitamente non verificato; numeri non finiti rifiutati prima dello schema.

Dipendenze: `__future__`, `copy`, `json`, `minimal`, `prototype.quantum_assistant.schema_validation`, `re`, `time`, `toon`.

Portabilità: Dipende dai modelli interni, dal catalogo e dalla rappresentazione minima. Il numero di tentativi e il ripiego sono responsabilità del chiamante.

Ottimizzazione possibile: Conservare il controllo JSON preventivo: protegge anche dal rilievo PD-01.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/legacy_rendering.py`

Lettura: **1–35**, SHA-256 `0ad466e7174ef665640766910e34709ed0583f127584bd74d74fec5f49d6ddab`.

Rende i prompt storici v2 nei formati configurati.

Contratti verificati: Mantiene esplicita la distinzione tra forma completa e compressa e i relativi metadati.

Dipendenze: `compact`, `complete_graph`, `json`, `output_contract`.

Portabilità: Il formato TOON eredita i vincoli del runtime Node storico.

Ottimizzazione possibile: Mantenere questa variante nell’archivio per riprodurre le prove precedenti.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/minimal.py`

Lettura: **1–208**, SHA-256 `2ba91963a32043b57e3bcfbbedaed21299ac5dd07932ece881f640b2948d1fd0`.

Riduce il prompt v3 e lega gli alias degli esempi alla richiesta e al registro.

Contratti verificati: Massimo cinque esempi distinti; impronte di QASM, vincoli, feature e registro; lista esplicita dei campi ammessi; score soltanto storici; schema delle citazioni coerente con il registro.

Dipendenze: `__future__`, `copy`, `dataclasses`, `hashlib`, `json`, `prototype.quantum_assistant.schema_validation`, `re`, `toon`.

Portabilità: Python; gli schemi devono restare disponibili nel percorso del progetto.

Ottimizzazione possibile: Evitare copie ripetute del grafo completo; non eliminare dispositivi o vincoli per ridurre il prompt senza dichiararlo.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/output_contract.py`

Lettura: **1–23**, SHA-256 `c13ba8d85eb35727f774194284111280626094c933dd2aaddb8b4159fcf3d4cd`.

Raccoglie istruzioni e metadati del contratto di uscita storico.

Contratti verificati: Versione e significato del contratto restano espliciti; non implementa la selezione sperimentale.

Dipendenze: nessuna.

Portabilità: Modulo di testo Python.

Ottimizzazione possibile: Nessuna ottimizzazione necessaria.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/rendering.py`

Lettura: **1–36**, SHA-256 `cdebabb98ec7f65b1991edf73e866c3b3bce4c1023fd1874c9e7ccc1b24954e5`.

Rende il prompt minimo v3 come JSON o TOON e registra la trasformazione.

Contratti verificati: Formati espliciti e checklist opzionale; rifiuto della forma completa non prevista da questa versione.

Dipendenze: `json`, `minimal`, `toon`.

Portabilità: Per TOON richiede il runtime verificato da toon.py.

Ottimizzazione possibile: Non confondere questo ingresso v3 con la costruzione facts v4 usata dallo studio ufficiale.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/toon.py`

Lettura: **1–113**, SHA-256 `8141dea24b531cdc4e800b66ffc974d3c1827af4cab12347c5a3a2aca3245348`.

Invoca il convertitore TOON Node e controlla il ripristino del contenuto.

Contratti verificati: Impronte del runtime verificate; scadenza della chiamata; uguaglianza dopo codifica e decodifica, comprese feature e ordine dei collegamenti.

Dipendenze: `__future__`, `copy`, `functools`, `hashlib`, `json`, `pathlib`, `subprocess`.

Portabilità: Percorso storico fissato a Node Linux x64: non funziona da solo su Windows nativo; il dimostratore ha un proprio adattamento.

Ottimizzazione possibile: Primo calcolo dell’impronta del binario e processi Node per nuovi prompt incidono sul tempo; cache limitata e misure separate dalla latenza LLM.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/prompting/wire.py`

Lettura: **1–36**, SHA-256 `9c4f0ef09d7efdc0360eaf7c6774701a5469d3f3f6955eaedec1a6e82badf3ca`.

Converte liste omogenee in tabelle JSON reversibili per il trasporto.

Contratti verificati: Marcatori riservati protetti; colonne uniche e larghezze delle righe verificate; controllo di ripristino.

Dipendenze: `__future__`, `json`.

Portabilità: Solo Python; formato interno, non parser generale di documenti non attendibili.

Ottimizzazione possibile: Le serializzazioni ripetute potrebbero essere ridotte preservando il controllo di uguaglianza.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/__init__.py`

Lettura: **1–93**, SHA-256 `a3ef2a0db32c761feb64894a8f1b7a87cc0573be3408d5ee7b5c8c82e4624512`.

Espone modelli, servizio e fabbrica del prototipo storico.

Contratti verificati: Esportazioni coerenti con modelli e adattatori letti.

Dipendenze: `adapters.context`, `controller`, `errors`, `factory`, `models`, `services`.

Portabilità: Importazioni eager trascinano Qdrant, Qiskit, MQT e schemi anche per usi limitati del pacchetto.

Ottimizzazione possibile: Esportazioni leggere o differite ridurrebbero costo e accoppiamento; il dimostratore separato usa inizializzatori più piccoli.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/__init__.py`

Lettura: **1–44**, SHA-256 `43404058094847f91d547cf5f8348cd4adbb0bc1c021a2e0dd95b3ce1ee6f2c8`.

Espone gli adattatori disponibili.

Contratti verificati: Gli adattatori concreti restano distinti dalle interfacce.

Dipendenze: `compilation`, `context`, `explanations`, `hardware`, `llm`, `parsing`, `qdrant_context`, `rag_features`, `validation`.

Portabilità: Importazioni eager richiedono l’ambiente sperimentale completo.

Ottimizzazione possibile: Ridurre gli import all’avvio in un futuro pacchetto riusabile.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/compilation.py`

Lettura: **1–119**, SHA-256 `6f9d20a575221abcd4f56bd5a211ca6196b32eb920295be7ecef0bf7e6534c1f`.

Compila la raccomandazione approvata con il Target Qiskit selezionato.

Contratti verificati: Metrica e larghezza controllate; configurazione dal modello validato; GatesInBasis, CheckMap e porte sconosciute verificati prima di restituire QASM e statistiche.

Dipendenze: `__future__`, `io`, `models`, `mqt.bench.targets`, `qiskit`, `qiskit.qasm2`, `qiskit.transpiler.passes`, `typing`.

Portabilità: Richiede Qiskit e MQT Bench compatibili. Nessun timeout esterno della compilazione in questo adattatore.

Ottimizzazione possibile: Separare il processo di compilazione per applicare un limite reale di tempo e memoria su ingressi grandi; non cambiare opzioni o seed del protocollo congelato.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/context.py`

Lettura: **1–994**, SHA-256 `89985147afdee737edddf18e5837a8b33cf8479a5e979faa8ccaf926a8d2b3c8`.

Costruisce registro delle evidenze e prompt dai risultati storici recuperati.

Contratti verificati: Rifiuta etichette parziali; controlla record, claim, evidenze, configurazioni e ranghi; mediana e riferimenti devono coincidere; esempi non etichettati non sostengono affermazioni storiche.

Dipendenze: `__future__`, `collections.abc`, `json`, `math`, `models`, `pathlib`, `prototype.prompting.minimal`, `qdrant_context`, `qiskit_dataset.catalog`, `rag_dataset`, `schema_validation`, `typing`.

Portabilità: Richiede catalogo e adattatori RAG, oltre agli schemi. StructuredPromptBuilder predefinito produce v3; v4 è costruito esplicitamente dal livello dello studio.

Ottimizzazione possibile: I record sono piccoli e il recupero è limitato a cinque esempi; evitare refactoring del registro senza prove di equivalenza.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/explanations.py`

Lettura: **1–289**, SHA-256 `5b35c86d97080a7baf73368f77d5699ba252f9ce63a119f682ca45926baa2c49`.

Deriva spiegazioni da claim strutturati già validati.

Contratti verificati: Ogni riferimento deve essere risolvibile; testo costruito da valori verificati; caveat scientifici e provenienza mantenuti.

Dipendenze: `__future__`, `collections.abc`, `models`.

Portabilità: Solo modelli Python; renderer del contratto v2, diverso dal testo ipotetico v4.

Ottimizzazione possibile: Nessuna ottimizzazione prioritaria sul piccolo numero di claim.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/hardware.py`

Lettura: **1–675**, SHA-256 `0ccfb961ede66c9fd0742747587d33ef239447cd3dd95074de426e30f6818cab`.

Costruisce l’istantanea hardware e applica vincoli di compatibilità.

Contratti verificati: Cinque definizioni note; versioni e impronte dei Target confrontate al catalogo; Target non disponibili esclusi; tutte le ragioni di incompatibilità registrate; istantanea legata alla richiesta.

Dipendenze: `__future__`, `collections.abc`, `dataclasses`, `hashlib`, `importlib.metadata`, `json`, `models`, `mqt.bench.targets`, `qiskit_dataset.catalog`, `schema_validation`, `scripts.mqt_predictor_protocol`, `typing`.

Portabilità: Richiede versioni MQT/Qiskit fissate e Target sintetici riproducibili; non descrive disponibilità o calibrazione live.

Ottimizzazione possibile: Istantanea già memorizzata; mantenere distinti costo del suo caricamento e tempo della raccomandazione.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/llm.py`

Lettura: **1–34**, SHA-256 `55f4d301a67d6a8da141ad9d36b1e9ff91ffccab4aa3ecc967b38f33376fb76a`.

Adatta una funzione a collegamento LLM e segnala la mancata configurazione.

Contratti verificati: Nessuna risposta inventata e nessuna chiamata implicita quando il collegamento manca.

Dipendenze: `__future__`, `collections.abc`, `models`.

Portabilità: La funzione fornita dal chiamante decide trasporto e piattaforma.

Ottimizzazione possibile: Modulo minimo; nessuna ottimizzazione necessaria.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/parsing.py`

Lettura: **1–29**, SHA-256 `cf4d2531ff0cb2c7623c090f5a97d96ca70799023dcaf217cbe3ece805a88724`.

Mantiene il vecchio punto di importazione del parser.

Contratti verificati: Riesporta le implementazioni correnti senza duplicarne la logica.

Dipendenze: `hardware`, `request`.

Portabilità: Eredita requisiti Qiskit/MQT del parser.

Ottimizzazione possibile: Conservare per compatibilità; nessuna ottimizzazione utile.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/rag_checks.py`

Lettura: **1–140**, SHA-256 `fa9332f868e5d2beea277cde6c0c49f25ba4150267c6bd8b1f43b44b190aee2d`.

Confronta tecnicamente il recupero della validation con una formula indipendente.

Contratti verificati: Nessuna chiamata LLM né compilazione; confronto di identificativi ordinati e distanze; verifica di 88 richieste validation; esclusione per hash del Test dalla preparazione tecnica.

Dipendenze: `__future__`, `factory`, `hashlib`, `llm`, `math`, `pathlib`, `qdrant_context`, `qiskit_dataset.experiment_v2`, `rag_dataset`, `rag_features`, `scripts.mqt_predictor_protocol`, `sys`, `time`, `uuid`.

Portabilità: Richiede corpus sigillato, Qdrant e ambiente sperimentale. Non è parte dell’avvio portabile e non è stato eseguito durante questa revisione.

Ottimizzazione possibile: Il riferimento ricalcola divisori e vettori per ciascuna query: utile come controllo indipendente, evitabile nel percorso operativo.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/rag_features.py`

Lettura: **1–105**, SHA-256 `43013abb3743f64802c07b07567bd35b2543bb10eb451e85f7cdd65de2b4e34b`.

Trasforma 49 feature con log1p e divisori del solo train e misura la distanza Manhattan.

Contratti verificati: Ordine fissato; tipi, finitezza e domini verificati; divisori positivi; nessun clipping o normalizzazione L2; precisione canonica float64 e tolleranze Qdrant dichiarate.

Dipendenze: `__future__`, `collections.abc`, `dataclasses`, `math`, `qiskit_dataset.experiment_v2`, `typing`.

Portabilità: Solo Python. Il fit_train riceve feature senza etichette di split: il vincolo train è garantito dal caricatore chiamante.

Ottimizzazione possibile: Per 396 righe il costo è modesto; qualunque vettorizzazione deve conservare ordinamento finale e tolleranze.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/request.py`

Lettura: **1–509**, SHA-256 `05b9530b069eae4cc27018b2e3080d66e5bf8e27b6e59c432d424ba3b2552d24`.

Valida richiesta e vincoli, analizza QASM e ricava le 49 feature.

Contratti verificati: Limiti di byte e lunghezza; include ammessi soltanto qelib1.inc; metrica unica; feature finite; normalizzazione vincoli e istantanea hardware.

Dipendenze: `__future__`, `collections.abc`, `errors`, `hashlib`, `math`, `models`, `mqt.predictor.ml.helper`, `pathlib`, `ports`, `qiskit`, `re`, `schema_validation`, `typing`.

Portabilità: Importa il calcolo delle feature MQT nell’ambiente storico; il dimostratore lo sostituisce con copia verificata. PD-01 può propagarsi dall’API JSON; il normale comando del dimostratore costruisce vincoli stringa.

Ottimizzazione possibile: Controllare la larghezza prima dell’estrazione costosa: il limite sui byte non limita qubit o espansione delle porte.

Esito: vedere PD-08.

### `archivio/esperimento_v2/prototype/quantum_assistant/adapters/validation.py`

Lettura: **1–999**, SHA-256 `f563d44f95e6d454746af938f47b32367e495a58cdb1570c385617da1805465f`.

Valida risposte v2 e v3 rispetto a richiesta, catalogo e registro delle evidenze.

Contratti verificati: Riferimenti e claim collegati integralmente; un solo uso per riferimento; configurazioni e dispositivi ammissibili; v3 verifica provenienza delle citazioni e dichiara il testo non verificato.

Dipendenze: `__future__`, `collections.abc`, `explanations`, `models`, `ports`, `prototype.prompting.minimal`, `qiskit_dataset.catalog`, `schema_validation`, `typing`.

Portabilità: Non è il verificatore facts v4. Eredita PD-01 nel percorso v3 senza controllo JSON preventivo.

Ottimizzazione possibile: Feedback limitato a dodici errori; costo trascurabile per risposte piccole.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/controller.py`

Lettura: **1–75**, SHA-256 `a377b30312e18ee7f4fd69ff7277b28f6f6275124898b64350f032b8c5c8d285`.

Coordina la schermata e associa conferme di compilazione a raccomandazioni emesse.

Contratti verificati: Compilazione richiede richiesta memorizzata e conferma; risultati non fabbricati dalla schermata.

Dipendenze: `__future__`, `dataclasses`, `models`, `ports`, `services`, `typing`.

Portabilità: Componente in memoria, senza persistenza o gestione di sessioni multiutente.

Ottimizzazione possibile: Per un servizio duraturo introdurre scadenza e isolamento dei risultati conservati.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/errors.py`

Lettura: **1–30**, SHA-256 `f73b2cac0f2796adf41db63f39695873f0bbfb61fde4d3407003c5abf4e95a3c`.

Definisce gli errori di dominio e i rispettivi esiti strutturati.

Contratti verificati: Cause di richiesta non valida, assenza candidati e risposta non valida restano distinguibili.

Dipendenze: `__future__`, `models`.

Portabilità: Solo Python e modelli interni.

Ottimizzazione possibile: Nessuna ottimizzazione necessaria.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/factory.py`

Lettura: **1–68**, SHA-256 `3623710b86cbb73327a5e90f4ded5f5e12bb3d74a66e6b49344ada40f568333f`.

Assembla parser, hardware, recupero, prompt, validatore e compilatore.

Contratti verificati: Catalogo condiviso; recupero qdrant/reference/none esplicito; collegamento LLM iniettato; default storico non equivale automaticamente allo studio v4.

Dipendenze: `__future__`, `adapters.compilation`, `adapters.context`, `adapters.parsing`, `adapters.qdrant_context`, `adapters.rag_dataset`, `adapters.validation`, `collections.abc`, `pathlib`, `ports`, `qiskit_dataset.catalog`, `services`.

Portabilità: La fabbrica storica richiede la disposizione archiviata dei dati; non è un avvio autonomo del dimostratore.

Ottimizzazione possibile: Validare subito retrieval_limit<=5 per le rappresentazioni minime; attualmente il costruttore del prompt segnala il limite più tardi.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/models.py`

Lettura: **1–1394**, SHA-256 `78e8e62c4152a151c0dce2636dab4293c715b5c133e2bd0ecb8ccb891490485d`.

Definisce richieste, istantanee, evidenze, raccomandazioni e risultati.

Contratti verificati: Identificativi e riferimenti controllati; congelamento profondo di feature e payload delle evidenze; tuple normalizzate nei modelli storici; risultato valido richiede raccomandazione senza errori.

Dipendenze: `__future__`, `collections.abc`, `dataclasses`, `enum`, `math`, `types`, `typing`.

Portabilità: Solo Python. Annotazioni e dataclass frozen non sostituiscono una validazione universale di oggetti costruiti a mano; parser e costruttori sono i confini previsti.

Ottimizzazione possibile: Ricerca lineare di riferimenti adeguata ai piccoli registri; nessun indice aggiuntivo necessario.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/ports.py`

Lettura: **1–153**, SHA-256 `61df7fb5f747a49a592b31ba450548668d6ce2180e9b840c543aff61afe8a440`.

Definisce interfacce strutturali per parser, catalogo, recupero, LLM, validatore e compilatore.

Contratti verificati: Tipi e responsabilità corrispondono ai componenti concreti; nessuna esecuzione LLM o compilazione implicita.

Dipendenze: `__future__`, `models`, `typing`.

Portabilità: Solo typing e modelli interni.

Ottimizzazione possibile: Nessuna ottimizzazione necessaria.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/prototype/quantum_assistant/schema_validation.py`

Lettura: **1–341**, SHA-256 `0b3a19abb2adf03ee0a980c4b02fe47b11da446ffe895cf3c8f97e38587d1862`.

Implementa il sottoinsieme di JSON Schema usato dai contratti del progetto.

Contratti verificati: Parole chiave ammesse esplicite; riferimenti soltanto locali; duplicati di chiave rifiutati; limiti di documento; PD-01 interrompe il percorso strutturato per alcuni numeri fuori dominio.

Dipendenze: `__future__`, `collections.abc`, `json`, `math`, `models`, `pathlib`, `re`, `typing`, `uuid`.

Portabilità: Solo Python e schemi locali; deve essere distribuito con le risorse corrette.

Ottimizzazione possibile: Validare i numeri finiti e gli elementi prima di serializzarli per uniqueItems; evitare conversioni float senza gestione dell’overflow.

Esito: vedere PD-01.

### `archivio/esperimento_v2/prototype/quantum_assistant/services.py`

Lettura: **1–251**, SHA-256 `7ecf7348bc0bc5bf961acbeb39f52f44c17a0d4fd9981f0f930d4b7eeae531c3`.

Orchestra preparazione, recupero, tentativi logici e compilazione dopo conferma.

Contratti verificati: Nessuna compilazione durante raccomandazione; numero tentativi limitato; esiti invalidi ritentati con feedback; conferma richiede identità di un risultato emesso dal servizio.

Dipendenze: `__future__`, `adapters.context`, `adapters.request`, `dataclasses`, `models`, `ports`, `prototype.prompting.minimal`.

Portabilità: Componenti iniettati; errori di trasporto propagati al chiamante. Il percorso facts v4 e il suo ripiego sono esterni a questa orchestrazione storica.

Ottimizzazione possibile: La lista dei risultati emessi cresce senza scadenza; limitarla per impieghi continuativi.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/qiskit_dataset/__init__.py`

Lettura: **1–15**, SHA-256 `db3cb07fe7ea99d2e35dca70468edba1d675deb66dd12cc4fb76d18be41d6289`.

Espone funzioni e tipi comuni del Dataset Qiskit.

Contratti verificati: Riesportazioni coerenti e prive di esecuzioni sperimentali automatiche.

Dipendenze: `catalog`.

Portabilità: Richiede pacchetti del repository; dipendenze scientifiche caricate nelle funzioni dove previsto.

Ottimizzazione possibile: Mantenere leggero l’ingresso del pacchetto.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/qiskit_dataset/aggregation.py`

Lettura: **1–627**, SHA-256 `ce7044b1a742a2496b0fdac572ae9b0dd0579daf1a34247277d37ad9af114471`.

Unisce viste dei dispositivi e produce la vista globale e gli esempi train.

Contratti verificati: Circuiti condivisi confrontati e ricontrollati via hash; identità, split, cataloghi e collegamenti raw/aggregati verificati; RAG riservato al train; PD-04 riguarda il mancato ricalcolo numerico in questo controllo.

Dipendenze: `__future__`, `catalog`, `collections`, `core`, `json`, `pathlib`, `reporting`, `scripts.mqt_predictor_protocol`, `typing`, `views`.

Portabilità: Dipende dalla struttura di cartelle sperimentale e dai manifest. Non è necessario al caricatore compatto del dimostratore.

Ottimizzazione possibile: Rilegge e serializza molti record e circuiti per dispositivo; riutilizzare identità già verificate solo con un contratto di cache esplicito.

Esito: vedere PD-04.

### `archivio/esperimento_v2/qiskit_dataset/catalog.py`

Lettura: **1–289**, SHA-256 `dd5b0994a36ef9f082a07670c346e6c6d8d410ccdc8f8ad6ebc9a313e137c6fa`.

Carica dodici configurazioni, tre seed, dispositivi e vincoli del protocollo.

Contratti verificati: Identificativi unici, seed interi distinti, default presente, versioni e impronte v2 richieste; oggetto frozen con mappe interne trattate come dati fidati.

Dipendenze: `__future__`, `dataclasses`, `json`, `pathlib`, `re`, `scripts.mqt_predictor_protocol`, `typing`.

Portabilità: JSON locale e Python; catalogo storico deve restare accanto al proprio ambiente.

Ottimizzazione possibile: by_id ricostruisce dodici elementi, costo irrilevante. Rafforzare domini di opzioni e timeout se il catalogo diventa ingresso esterno.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/qiskit_dataset/core.py`

Lettura: **1–801**, SHA-256 `3abb6b19b68d39de8c9985308b64f460181e3af2ca9752bf80c58cedfeff9eca`.

Prepara corpus, split, copie di QASM, manifest e piano dei tentativi.

Contratti verificati: Gruppi di famiglie fissi; duplicate alias registrate; controllo hash tra split; Test v2 richiede apertura esplicita; copia mai sovrascritta se incoerente; run_id include contratto di compilazione.

Dipendenze: `__future__`, `catalog`, `collections`, `hashlib`, `importlib`, `json`, `math`, `mqt.bench.targets`, `mqt.predictor.ml.helper`, `os`, `pathlib`, `qiskit`, `re`, `scripts.mqt_predictor_protocol`, `shutil`, `typing`, `zipfile`.

Portabilità: Richiede corpus MQT, dipendenze fissate e percorsi dell’esperimento; il corpus sorgente originale deve essere conservato.

Ottimizzazione possibile: Le feature possono essere estratte una volta e riusate soltanto dopo verifica di versione, sorgente e contratto; scritture JSONL oggi accumulano tutto in memoria.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/qiskit_dataset/experiment_v2.py`

Lettura: **1–1333**, SHA-256 `aaa7e52ab6694e8f407470a9d39aad5eb216714e89abfc83a3ddb1c56792bdab`.

Valida piani e risultati dei metodi e costruisce il confronto con oracolo e regret.

Contratti verificati: Universi ordinati e unici; estrazioni casuali prima degli score; matrice Qiskit completa e provenienza verificata; mediane ricalcolate dai raw; oracolo definito soltanto a matrice interamente riuscita; fallimenti e non applicabilità distinti.

Dipendenze: `__future__`, `catalog`, `collections`, `core`, `hashlib`, `json`, `math`, `mqt.bench.targets`, `os`, `pathlib`, `random`, `scripts.mqt_predictor_protocol`, `statistics`, `typing`, `views`.

Portabilità: Moduli e artefatti dell’esperimento v2; alcune impronte provengono da costanti locali, quindi non è una libreria generica.

Ottimizzazione possibile: Indicizzare per hash del circuito evita scansioni della matrice per ogni circuito; aggiungere il denominatore specifico del regret senza cambiare statistiche congelate.

Esito: vedere PD-06.

### `archivio/esperimento_v2/qiskit_dataset/generation.py`

Lettura: **1–1019**, SHA-256 `0220a36623138bb29969c45a65aadd4d57814011e51362c676680ccca8a5acd4`.

Esegue compilazioni Qiskit, valida i Target e conserva risultati e cache per la ripresa.

Contratti verificati: Versioni, Target, seed e politica v2 verificati; pool spawn con coda limitata; errori e timeout hanno fase e diagnostica; PD-02/03/05/09 descrivono i limiti di integrità, conservazione e portabilità.

Dipendenze: `__future__`, `catalog`, `collections`, `concurrent.futures`, `contextlib`, `core`, `functools`, `io`, `json`, `math`, `mqt.bench.targets`, `mqt.predictor.reward`, `multiprocessing`, `pathlib`, `qiskit`, `qiskit.qasm2`, `qiskit.transpiler.passes`, `re`, `scripts.mqt_predictor_protocol`, `signal`, `sys`, `time`, `traceback`, `typing`.

Portabilità: La scadenza usa SIGALRM/ITIMER_REAL e non è applicata su Windows nativo; chiamate native lunghe possono differire il segnale anche su POSIX. Usare l’ambiente Linux previsto.

Ottimizzazione possibile: Una futura versione dovrebbe usare un processo sorvegliato per tentativo, registri append-only e verifica della sorgente immediatamente prima del parse.

Esito: vedere PD-02, PD-03, PD-05, PD-09.

### `archivio/esperimento_v2/qiskit_dataset/reporting.py`

Lettura: **1–1099**, SHA-256 `a8a9eb3a641716b2b979edd691dccb83bdaf7983b8759cad8cc518d216180535`.

Genera riepiloghi, CSV e confronti dei dispositivi conservando fallimenti e censura dei tempi.

Contratti verificati: Tempi dei soli successi dichiarati; conteggi attesi e osservati separati; politiche miste segnalate; intersezione dei circuiti resa esplicita; diagnosi di timeout distingue osservazioni e inferenze.

Dipendenze: `__future__`, `catalog`, `collections`, `core`, `csv`, `generation`, `io`, `json`, `math`, `pathlib`, `statistics`, `typing`.

Portabilità: Python e file locali; ricostruisce la diagnosi per record storici privi di campi nuovi.

Ottimizzazione possibile: Il confronto rilegge dati e report di ogni dispositivo: riutilizzarli in memoria evita I/O ripetuto. I report riassumono, non sostituiscono una verifica di integrità.

Esito: nessun difetto specifico confermato oltre ai limiti e alle dipendenze descritti.

### `archivio/esperimento_v2/qiskit_dataset/views.py`

Lettura: **1–1082**, SHA-256 `e9a923ce905134b072e35d86ce41b1629caeb1aeb353daedc4c6d120b66eda22`.

Riunisce i tre seed, ordina le configurazioni e costruisce etichette RAG train.

Contratti verificati: Eleggibilità richiede tutti i seed riusciti; alias duplicati esclusi; mediana e osservazioni conservate; vincitore seguito da tre configurazioni del suo dispositivo; nessuno score del nuovo ingresso.

Dipendenze: `__future__`, `catalog`, `collections`, `core`, `json`, `math`, `pathlib`, `reporting`, `scripts.mqt_predictor_protocol`, `statistics`, `typing`.

Portabilità: Dipende dalla struttura dei manifest e dai cataloghi. Le etichette storiche devono restare congelate anche se si corregge il testo delle parità in seguito.

Ottimizzazione possibile: Dimensioni attuali gestibili; mantenere ordine deterministico e separazione train/validation/test in ogni refactoring.

Esito: vedere PD-07.

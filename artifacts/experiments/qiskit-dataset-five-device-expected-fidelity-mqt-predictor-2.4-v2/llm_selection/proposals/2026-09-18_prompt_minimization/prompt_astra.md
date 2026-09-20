# Incarico per Astra — riduzione del prompt Qwen e semplificazione delle evidenze

Modello destinatario: Astra. Impostazione richiesta all'utente nell'interfaccia: reasoning Extra high (xhigh).
Questo documento è un prompt operativo: implementa la modifica, verifica il percorso completo e documenta i risultati. Non limitarti a proporre un piano.

## Obiettivo e decisioni già approvate

Riduci il prompt effettivamente inviato a Qwen al minimo necessario per scegliere dispositivo e configurazione Qiskit. Mantieni JSON: niente TOON in questa attività. Riduci sia i contenuti sia la complessità della risposta richiesta.

Conserva separatamente:
- dati canonici completi, hash SHA-256, manifest, versioni e provenienza, necessari all'esperimento;
- rappresentazione essenziale destinata al modello;
- corrispondenze per ricondurre gli alias locali agli originali.

Non abbreviare gli hash canonici e non riscrivere il Dataset o gli artefatti storici. Le nuove decisioni superano il precedente requisito di reversibilità integrale del testo mostrato al modello: questa volta è autorizzata l'omissione di contenuti dal prompt. Aggiorna di conseguenza la documentazione del protocollo, distinguendo richiesta canonica e rappresentazione LLM.

## Orientamento e graphify

Lavora nel progetto /home/elio/Tesi-mqt-2.4-v2, rispettando AGENTS.md. Leggi prima knowledge/riassunto_kb_mqt_predictor.md e il protocollo corrente docs/protocollo_sperimentale.md.

Usa la skill .codex/skills/graphify/SKILL.md e interroga il grafo prima di cercare nel codice. Il 18 settembre 2026 il grafo esistente conteneva 18.122 nodi e sono riuscite queste interrogazioni, senza ricostruzione e senza API:
    /home/elio/.local/bin/graphify query "prompt compact alias aliases" --budget 1800
    /home/elio/.local/bin/graphify query "claim evidence validate" --budget 1800

Il terminale isolato di Codex falliva prima di avviare il processo con helper_unknown_error: setup refresh had errors. Ha funzionato exec_command con PowerShell esplicito, login=false, directory C:/Users/User, sandbox_permissions=require_escalated, invocando wsl.exe -d Ubuntu --cd /home/elio/Tesi-mqt-2.4-v2. Richiedi tale escalation attraverso il normale strumento solo se il problema persiste. Non trattarlo come errore del grafo e non reinstallare graphify.

Eseguibile WSL: /home/elio/.local/bin/graphify.
Interprete: /home/elio/.local/share/uv/tools/graphifyy/bin/python.
Il riferimento graphify-out/.graphify_python è stato ripristinato. Il vocabolario è in graphify-out/.vocab.txt.
Per script complessi conviene passare uno script Python tramite stdin a wsl.exe e usare subprocess con argomenti separati: evita perdite di quoting fra PowerShell e WSL. rg non risultava disponibile nel comando WSL verificato; usa una ricerca mirata alternativa se necessario.

Usa il grafo per orientarti e conferma sui sorgenti correnti: indicizza anche copie storiche in code_snapshots, che non sono il codice attivo.

## Punti già verificati da cui partire

Radice degli artefatti LLM:
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/

La prova precedente con alias è in:
proposals/2026-09-14_prompt_reduction/
Leggi probe.py, proposta.md, counts.json, metadata.json, compact_5_aliases.json e compact_5_aliases_map.json.
Quella prova ometteva anche alcune feature: NON riprendere questa scelta, perché ora le caratteristiche del circuito devono restare invariate.

Conteggi storici, cinque esempi e un solo circuito train:
- original_5: 80.612 token;
- compact_5: 29.391;
- compact_5_aliases: 18.372.
Sono misure archiviate di una proposta precedente, non il risultato della nuova implementazione né un confronto di qualità.

Esiste già codice attivo per la compattazione:
- prototype/prompting/compact.py: encode, model_input, audit, expand_response;
- prototype/prompting/rendering.py: messaggi e istruzioni;
- llm_selection/compact_prompt.py: re-export per compatibilità;
- llm_selection/configuration.py: payload e schema di risposta;
- prototype/quantum_assistant/adapters/validation.py: StructuredRecommendationValidator;
- tests/test_compact_prompt.py e tests/test_claim_evidence_validation.py.
Segui le relazioni del grafo per trovare costruttore del prompt, modelli, schemi, gateway, registri, correzioni, chat, interfaccia e compilatore.

La codifica attuale lossless-v2-20260914 conserva tutti i contenuti, usa molte famiglie di alias R/C/E/S/U/H, shared_values e tabelle $columns/$rows. Non basta rinominare quegli alias: bisogna eliminare le informazioni inutili e semplificare il contratto.

Caso di riferimento:
technical_episodes/qwen-prompt-v2-02/qwen/p1_t0/dj_indep_tket_2/attempt_1/
Leggi prompt.json, encoding.json, summary.json e call/request.json.
Il riepilogo registra 34.318 token, JSON e schema validi, ma invalid_output per claim/evidence. La scelta ibm_falcon_127 + o2_default_default coincideva con l'etichetta primaria. La prova recuperava anche il circuito train stesso: è una prova tecnica, non evidenza di generalizzazione.
prompt.json è il documento canonico completo. call/request.json contiene il vero prompt serializzato con template e schema: misura quel percorso, non soltanto il JSON salvato.

## Nuovo input al modello

1. Mantieni cinque esempi RAG, stesso recupero, stesso ordine, stesse feature e relativi valori/formato. Non cambiare indice, distanza, normalizzazione, split o criteri di scelta degli esempi per ottenere meno token.
2. Usa E1...E5 come unici identificativi degli esempi nel prompt e nelle citazioni. La mappa locale esterna deve restare stabile nei tentativi correttivi della stessa richiesta. Evita collisioni e riuso della mappa di un'altra richiesta.
3. source_sha256 resta canonico nei registri. Nella rappresentazione LLM usa un'identità breve del circuito soltanto se serve; evita un campo chiamato source_sha256 che contenga qualcosa che non è uno SHA-256. Non introdurre un secondo identificativo se E1 basta già a individuare l'esempio.
4. Conserva le caratteristiche del circuito attuale e degli esempi esattamente come sono: niente rimozione degli zeri, arrotondamenti o selezione di feature in questa attività.
5. Elimina tutto il QASM2 testuale dall'input LLM, comprese eventuali copie in messaggi, istruzioni, registri e correzioni. Il sorgente originale resta disponibile al prototipo e al compilatore.
6. Mantieni un solo catalogo compatible_hardware con le descrizioni hardware necessarie. Dentro gli esempi compatible_devices contiene solo nomi/ID, senza ripetere descrizioni e proprietà.
7. Ogni esempio contiene essenzialmente circuito/feature, obiettivo, dispositivi compatibili, dispositivo vincente e tre configurazioni migliori in ordine, con associazione al dispositivo preservata. I contenuti comuni, come l'obiettivo, possono essere dichiarati una sola volta.
8. Rimuovi record_id/rag_id duplicati, summary_id, claim_id, evidence_id, caveat_id, hash, manifest, percorsi, revisioni e metadati di provenienza dalla vista LLM. Non chiedere al modello di copiare request_id, catalog_snapshot_id o altri metadati che il programma conosce già: gestiscili fuori dalla risposta del modello e vincolali alla richiesta corretta.
9. Snellisci i claim storici se utili, senza richiedere nuovi testi generati tramite altre chiamate LLM. Le evidence non devono riprodurre l'esempio, il circuito, le etichette o l'hardware. Il registro completo delle fonti resta nell'applicazione.
10. Mantieni una sola definizione dello spazio di scelta e delle istruzioni essenziali. Evita istruzioni vecchie che impongono claim strutturati, riferimenti multilivello o caveat obbligatori. I limiti scientifici necessari possono essere espressi una sola volta in linguaggio naturale.

Non introdurre altre codifiche dense o indirection complesse per risparmiare pochi caratteri. La comprensibilità per Qwen è un requisito insieme al numero di token.

## Risposta e validazione

La motivazione deve essere libera, breve e collegata agli esempi. Esempio illustrativo, non una risposta da fissare nel prompt:

{
  "selected_device": "ibm_falcon_27",
  "config_id": "o2_default_default",
  "claim": "Ho scelto questo dispositivo perché si comporta meglio negli esempi storici con caratteristiche simili; la configurazione scelta è sostenuta dai risultati citati.",
  "evidence": ["E2", "E4"]
}

Preferisci un config_id del catalogo se consente al programma di ricostruire senza ambiguità i parametri Qiskit. Seed e altri valori governati dal protocollo restano applicativi. Non inventare combinazioni e non modificare lo spazio delle dodici configurazioni.

Non richiedere claim_id, source_claim_id, source_id, reference_id, caveat_id, copie degli esempi o sottografi di evidenze. Lo stesso esempio può sostenere la scelta del dispositivo e della configurazione: niente obbligo di duplicarlo con ID diversi.

Aggiorna insieme schema di risposta, istruzioni, parser, modelli, validatore, correzioni, registrazione e visualizzazione. Mantieni i controlli sostanziali su compatibilità hardware, configurazione ammessa, tipi/formato, vincolo alla richiesta e accesso al compilatore soltanto dopo validazione.

Il validatore deve verificare che gli alias citati appartengano agli esempi realmente forniti e risolverli alle fonti canoniche. Gestisci esplicitamente ID sconosciuti, mappe errate, riferimenti duplicati e assenza di esempi. Conserva anche il funzionamento senza RAG: evidence vuota, senza inventare supporto storico.

Distinzione obbligatoria: una citazione risolvibile dimostra che la risposta cita un esempio fornito, non dimostra causalmente che il modello lo abbia usato né garantisce la verità di ogni frase libera. Documenta il limite. Eventuali controlli meccanici di sostegno di dispositivo/configurazione vanno separati dalla validità delle citazioni; non chiamare la semplice risoluzione degli alias "verifica semantica del claim". Non trasformare il testo libero in un nuovo oneroso contratto di ID.

Non fabbricare claim strutturati o correggere silenziosamente scelte per soddisfare il vecchio validatore. Versiona il nuovo contratto e mantieni leggibili gli artefatti precedenti.

## Verifica e consegna

- Controlla lo stato Git prima di lavorare e conserva le modifiche altrui. Alla ricognizione erano presenti modifiche in AGENTS.md e llm_selection/serve.ps1, oltre a registri RL e nuovi artefatti: non sovrascriverli.
- Implementa il nuovo percorso condiviso, anche per chat e tentativi correttivi dove pertinenti, senza lasciare un vecchio schema nella generazione vincolata.
- Aggiungi test mirati: cinque esempi invariati, feature identiche, assenza di QASM/hash lunghi/metadati esclusi nel testo inviato, hardware non duplicato, risoluzione alias e isolamento delle richieste, risposta valida/ID inesistente, configurazione incompatibile, flusso senza RAG, correzioni e compilazione protetta.
- Produci esempi prima/dopo su richieste train esistenti, incluso il caso indicato. Usa gli stessi cinque esempi per confrontare i formati.
- Conta la richiesta completa con il tokenizer e il template effettivi di Qwen, includendo istruzioni e trattamento dello schema. Riporta token totali, contributi delle sezioni come misure non necessariamente additive, riduzione assoluta/percentuale e metodo. Non confondere caratteri o stime con token misurati; non promettere una soglia non verificata.
- Predisponi i registri prima di eventuali piccole prove tecniche train. Non avviare validation completa, test, training, cambio modello/precisione o riavvio di servizi che interferisca con attività in corso. Se non puoi misurare col tokenizer reale, conserva il confronto preparato e dichiara esattamente la misura mancante.
- Non usare gli score del circuito corrente nel suo prompt o nelle evidenze. Conserva split, vincoli del protocollo e distinzione fra verifica tecnica e qualità sperimentale.
- Salva in una nuova directory di artifacts/ configurazione, revisione del prompt, mappe, input canonico, testo realmente inviato, schema, conteggi, esiti e limiti. Non sovrascrivere tentativi o risultati precedenti.
- Aggiorna docs/protocollo_sperimentale.md e la documentazione specifica in italiano semplice: spiegare omissione del QASM dalla vista LLM, nuovo contratto, provenienza conservata e significato limitato della validazione delle citazioni.
- Esegui test pertinenti e graphify update . dopo le modifiche al codice, seguendo la skill e verificando lo scope per non confondere snapshot storici con sorgenti correnti.
- Consegna un riepilogo di modifiche, file interessati, test eseguiti, token prima/dopo, esempio reale del nuovo prompt e risposta, limiti e verifiche eventualmente mancanti.

Non aggiungere TOON. Non ridurre il numero di esempi o alterare le feature. L'obiettivo di questa attività è semplificare il contenuto e il contratto, mantenendo tracciabilità e funzionamento del prototipo.

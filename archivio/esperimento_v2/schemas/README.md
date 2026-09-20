# Formati dei dati

Gli schemi JSON descrivono come devono essere fatti i messaggi scambiati
dal prototipo e i risultati salvati. Consentono di rilevare campi mancanti,
tipi errati e valori non ammessi.

| File | Contenuto che controlla |
| --- | --- |
| [assistant_request.schema.json](assistant_request.schema.json) | Richiesta iniziale: circuito, obiettivo e vincoli hardware. |
| [hardware_catalog.schema.json](hardware_catalog.schema.json) | Fotografia dei dispositivi disponibili e provenienza delle informazioni. |
| [hardware_mask_result.schema.json](hardware_mask_result.schema.json) | Dispositivi compatibili e motivi di esclusione degli altri. |
| [llm_recommendation.schema.json](llm_recommendation.schema.json) | Risposta richiesta al modello: dispositivo, piano Qiskit, affermazioni e fonti citate. |
| [qiskit_run.schema.json](qiskit_run.schema.json) | Un tentativo di compilazione per circuito, dispositivo, configurazione e seed; conserva anche errori e tempi. |
| [qiskit_configuration_aggregate.schema.json](qiskit_configuration_aggregate.schema.json) | Riepilogo dei tre seed di una configurazione e sua ammissibilità al confronto. |
| [qiskit_rag_example.schema.json](qiskit_rag_example.schema.json) | Un esempio train recuperabile dal RAG, con scelta suggerita, risultati di supporto e limiti. |
| [method_decision_v2.schema.json](method_decision_v2.schema.json) | Decisione di un metodo sperimentale, con identità, tentativi, consumi ed eventuale fallimento. |
| [method_result_v2.schema.json](method_result_v2.schema.json) | Risultato comune ai metodi confrontati, con score, riferimento esaustivo, distanza dal riferimento e provenienza. |

Superare lo schema non basta: il codice controlla anche che il dispositivo
sia compatibile, il piano ammesso e le citazioni coerenti con le fonti.
Una risposta può quindi essere JSON corretto e restare non valida.

Per il flusso che usa questi dati, vedere il [prototipo](../prototype/README.md).

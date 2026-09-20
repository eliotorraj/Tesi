# Controlli automatici

Questa cartella verifica il comportamento del codice e le regole che rendono
ricostruibili gli esperimenti. I controlli riguardano la separazione dei dati,
la compilazione, la validazione delle risposte e il recupero degli esempi.

Molte prove usano dati sintetici e collegamenti LLM simulati. Altre leggono
i manifest reali, caricano i Target MQT o aprono un database Qdrant locale
temporaneo. Superare queste prove significa che il codice rispetta le regole
controllate. Non dimostra che un modello scelga il dispositivo migliore.

## Come eseguirli

Da Ubuntu/WSL, nella radice del progetto e con l'ambiente installato:

```bash
# Una famiglia di controlli
.venv/bin/python -m unittest discover -s tests -p 'test_request_constraints.py' -v

# L'intera raccolta
.venv/bin/python -m unittest discover -s tests -v
```

La raccolta completa comprende anche piccole prove reali di addestramento e
compilazione. Per una dimostrazione del flusso è utile
`test_prototype_architecture.py`: usa un LLM simulato e verifica il passaggio
dalla risposta alla compilazione confermata.

## Protocollo, ambiente e modelli MQT

| File | Cosa controlla |
| --- | --- |
| [test_experiment_v2.py](test_experiment_v2.py) | Numeri e separazione degli split, configurazioni congelate, piani riproducibili, decisioni, risultati e condizioni di apertura del test. |
| [test_mqt_predictor_protocol.py](test_mqt_predictor_protocol.py) | Corrispondenza dei Target MQT con le impronte previste e rilevamento dei cambiamenti hardware. |
| [test_mqt_support_scripts.py](test_mqt_support_scripts.py) | Validità degli archivi e dei metadati dei modelli, sincronizzazione e riconoscimento delle compilazioni RL valide. |
| [test_train_rl_model.py](test_train_rl_model.py) | Rappresentazione delle osservazioni, breve addestramento e ripresa, salvataggi, limiti delle azioni BQSKit e VF2. |
| [test_train_device_selector.py](test_train_device_selector.py) | Scelta delle etichette, gestione dei fallimenti, completezza delle compilazioni RL e validità dei risultati riutilizzati. |
| [test_run_pipeline_v2.py](test_run_pipeline_v2.py) | Parametri dei comandi coordinati, selezione dei dispositivi, ripresa e protezione dello split test. |
| [test_workspace_layout.py](test_workspace_layout.py) | Separazione tra cartelle correnti e storiche e risoluzione dei percorsi congelati del corpus. |

## Dataset e resoconti

| File | Cosa controlla |
| --- | --- |
| [test_qiskit_dataset.py](test_qiskit_dataset.py) | Catalogo delle dodici configurazioni, circuiti compatibili, suddivisioni, tentativi, mediane e costruzione degli esempi RAG dal solo train. |
| [test_qiskit_dataset_aggregation.py](test_qiskit_dataset_aggregation.py) | Unione dei Dataset dei dispositivi senza modificare le fonti e collegamento tra affermazioni ed evidenze originali. |
| [test_qiskit_reporting.py](test_qiskit_reporting.py) | Produzione dei resoconti e corretta distinzione tra diverse politiche di esecuzione e timeout. |

## Assistente e risposte LLM

| File | Cosa controlla |
| --- | --- |
| [test_request_constraints.py](test_request_constraints.py) | Richiesta JSON, circuito, catalogo, vincoli hardware e arresto prima del recupero quando nessun dispositivo è ammesso. |
| [test_prototype_architecture.py](test_prototype_architecture.py) | Collegamento tra componenti: errore LLM, correzione, risposta valida, conferma e compilazione. |
| [test_prototype_v2.py](test_prototype_v2.py) | Allineamento tra prototipo e v2: istruzioni QASM, versioni, Target, impronte e conservazione dei piani precedenti. |
| [test_llm_output_validation.py](test_llm_output_validation.py) | Forma e significato della risposta, configurazioni consentite, errori correggibili e limite dei tentativi. |
| [test_claim_evidence_validation.py](test_claim_evidence_validation.py) | Provenienza delle evidenze, rifiuto di citazioni inventate e costruzione delle spiegazioni dai soli dati verificati. |
| [test_compact_prompt.py](test_compact_prompt.py) | Conservazione di circuito ed evidenze, messaggi compatti effettivamente passati al trasporto, fonti, correzioni e provenienza del codice condiviso. |
| [test_llm_chat.py](test_llm_chat.py) | Scelta Qwen/Phi/Gemma, profili, controllo senza avvio e rispetto dei server già attivi, con processi simulati. |
| [test_llm_selection.py](test_llm_selection.py) | Equità del confronto tra LLM, chiusura delle decisioni prima degli score, tentativi interrotti, risorse, provenienza dei pesi e analisi dai risultati salvati. |

## Recupero RAG e dashboard

| File | Cosa controlla |
| --- | --- |
| [test_qdrant_retrieval.py](test_qdrant_retrieval.py) | Trasformazione delle 49 caratteristiche, distanza, filtri, parità, persistenza e integrità del recupero in Qdrant locale. |
| [test_qdrant_dashboard.py](test_qdrant_dashboard.py) | Corrispondenza della copia di consultazione con i vettori e i dati dell'indice originale. |

Le cartelle `__pycache__/`, quando presenti, sono generate da Python.
I risultati scientifici e i tentativi sperimentali sono documentati nelle
cartelle dell'esperimento, non in questa raccolta di controlli.

[Torna alla guida del progetto](../README.md).

# Artefatti dell’esperimento corrente

Questa cartella è il registro operativo dell’esperimento. L’identificativo
`qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2`
collega i suoi contenuti al [Dataset](../../../datasets/README.md) e al
[protocollo](../../../docs/protocollo_sperimentale.md).

## Mappa dei contenuti

| Cartella | Responsabilità |
| --- | --- |
| [manifests/](manifests/README.md) | Identità del corpus, partizioni e impronte dei dispositivi. |
| [sources/](sources/README.md) | Sorgenti train e validation predisposti per gli strumenti. |
| [models/](models/README.md) | Copie canoniche dei modelli addestrati. |
| [checkpoints/](checkpoints/README.md) | Salvataggi intermedi utili a riprendere l’addestramento RL. |
| [logs/](logs/README.md) | Andamento delle esecuzioni RL e Qiskit. |
| [qiskit_dataset_cache/](qiskit_dataset_cache/README.md) | Esiti delle singole compilazioni e circuiti compilati. |
| [rag/](rag/README.md) | Indice Qdrant e prove di coerenza del recupero. |
| [plans/](plans/README.md) | Piani di confronto validation e test e copie delle versioni precedenti. |
| [llm_selection/](llm_selection/README.md) | Pesi, richieste, risposte e registri delle prove dei modelli locali. |

## Come interpretare lo stato

Un modello salvato non certifica da solo la qualità del confronto. Servono
anche metadati, controlli dei cinque dispositivi e verifica dell'intero flusso.
I log iniziali non dimostrano che un addestramento sia terminato.

Lo stato complessivo è nel [README principale](../../../README.md).
Le evidenze della ricognizione sono nel [resoconto datato](../../../docs/resoconti/2026-09-16_ricognizione_documentazione.md).

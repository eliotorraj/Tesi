# Prototipo LLM per suggerimento e compilazione quantistica

Questa directory contiene lo scheletro applicativo che usera il Dataset Qiskit
diretto. Separa deliberatamente:

- parsing OpenQASM e feature deterministiche;
- compatibilità hardware;
- retrieval di esempi etichettati;
- generazione LLM;
- validazione e retry;
- conferma dell'utente;
- compilazione Qiskit e validazione finale.

## Flusso

```text
richiesta + QASM + vincoli
  -> parsing e feature
  -> hardware compatibili
  -> retrieval train-only dal Dataset globale
  -> prompt con label, claim, evidence e caveat storici
  -> risposta LLM strutturata
  -> validazione deterministica
       -> retry con errori espliciti, se non valida
       -> proposta all'utente, se valida
  -> conferma esplicita
  -> qiskit.transpile
  -> validazione sul Target
```

L'LLM suggerisce e spiega. Non modifica il catalogo, non disattiva i controlli
e non esegue la compilazione senza conferma.

## Componenti

| Parte | Implementazione | Responsabilita |
| --- | --- | --- |
| Parsing | `QasmRequestParser` | QASM, metadati e 49 feature |
| Compatibilita | `WidthCompatibilityFilter` | device ammessi per larghezza e richiesta |
| Retrieval | `JsonDatasetContextRetriever` | JSONL RAG globale o JSON legacy |
| Prompt | `StructuredPromptBuilder` | input live ed esempi etichettati |
| LLM | `LlmGateway` | integrazione provider ancora da scegliere |
| Validazione | `StructuredRecommendationValidator` | device e configurazione allowlisted |
| Orchestrazione | `PrototypeService` | ordine, retry e conferma |
| Compilazione | `QiskitDeterministicCompiler` | transpile e controllo Target |

## Dataset usato dal retriever

Il percorso previsto e:

```text
datasets/expected_fidelity/<scope>/global/rag_examples.jsonl
```

Il retriever usa le feature per una distanza deterministica e considera
soltanto esempi il cui device etichettato e disponibile nella richiesta live.
Nel prompt inserisce:

- input storico compatto;
- device e top-3 configurazioni etichettati;
- claim naturali;
- evidence con score e provenance;
- caveat scientifici.

Non inserisce il QASM storico completo. Il circuito live rimane invece
disponibile al modello dopo il parsing e il mascheramento previsti
dall'applicazione.

Il supporto al vecchio JSON con `records[].input` resta disponibile per
compatibilità, ma in quel formato le label di training e la ground truth di
valutazione non vengono esposte.

## Avvio del servizio

```python
from pathlib import Path

from prototype.quantum_assistant.factory import build_default_service

llm_gateway = ...  # implementazione del provider scelta in seguito

service = build_default_service(
    device_names=(
        "ibm_falcon_27",
        "ibm_heron_133",
        "ibm_falcon_127",
        "ibm_heron_156",
        "quantinuum_h2_56",
    ),
    dataset_path=Path(
        "datasets/expected_fidelity/pilot/global/rag_examples.jsonl"
    ),
    llm_gateway=llm_gateway,
    max_llm_attempts=3,
    retrieval_limit=5,
)
```

`llm_gateway` e un segnaposto: al momento il prototipo non effettua chiamate
di rete.

## Contratto della risposta LLM

```json
{
  "selected_device": "ibm_falcon_27",
  "figure_of_merit": "expected_fidelity",
  "compiler": "qiskit",
  "qiskit_plan": {
    "optimization_level": 2,
    "seed_transpiler": 0,
    "layout_method": "sabre",
    "routing_method": "sabre"
  },
  "explanation": "Motivazione leggibile.",
  "evidence": ["evidence_<sha256>", "live_request.circuit.features"],
  "warnings": ["Expected fidelity è una stima offline."]
}
```

Il validatore rifiuta device incompatibili, metriche o compiler diversi,
configurazioni fuori catalogo, seed non validi, spiegazioni vuote e liste
malformate.

## Vincoli e retry: confini futuri

`UiSubmission.constraints` è già separato dal Dataset. La formalizzazione
successiva dovrà introdurre:

- schema e versione dei vincoli;
- distinzione tra vincoli rigidi e preferenze;
- filtro deterministico del catalogo;
- comportamento esplicito quando nessun candidato resta.

Il retry esistente passa gli errori di validazione al tentativo successivo e si
ferma dopo `max_llm_attempts`. Restano da congelare nel protocollo:

- errori retryable e terminali;
- eventuale fallback deterministico;
- contenuto accumulato tra tentativi;
- metriche di validità, successo e costo.

Queste policy non vengono dedotte dagli esempi del Dataset e non ne modificano
le etichette.

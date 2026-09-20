# Assistente quantistico

Questa cartella contiene il prototipo applicativo della tesi e uno strumento
per esplorare gli esempi del Dataset.

L'assistente riceve un circuito OpenQASM 2 e i vincoli dell'utente.
Propone un dispositivo e una configurazione Qiskit. Controlla la proposta
e, dopo la conferma, compila il circuito.

## Come funziona

```text
circuito e vincoli
  → controllo della richiesta e dei dispositivi utilizzabili
  → recupero di circuiti simili dal Dataset train
  → proposta del modello linguistico
  → controllo della proposta e delle fonti citate
  → spiegazione costruita dai dati validati
  → conferma dell'utente
  → compilazione con Qiskit
```

Il modello sceglie tra le alternative ammesse. Non genera codice da eseguire.
Una proposta non valida può essere corretta entro il limite di tentativi
configurato. Se non esiste un dispositivo compatibile, il flusso si ferma
prima di interrogare il modello.

Il recupero predefinito usa Qdrant locale. Gli esempi provengono dal train;
validation e test restano separati. I risultati dei circuiti simili sono
precedenti storici, non misure del circuito appena inviato.

## Cosa contiene

| Percorso | A cosa serve |
| --- | --- |
| [quantum_assistant/](quantum_assistant/README.md) | Libreria Python dell'assistente: dati, coordinamento e componenti sostituibili. |
| [prompting/](prompting/README.md) | Codifica compatta e messaggi comuni per i modelli linguistici. |
| [quantum_assistant/adapters/](quantum_assistant/adapters/README.md) | Implementazioni di lettura della richiesta, catalogo, recupero, LLM, controlli e compilazione. |
| [qdrant_dashboard/](qdrant_dashboard/README.md) | Configurazione Docker e istruzioni per consultare una copia degli esempi tramite la dashboard Qdrant. |
| [__init__.py](__init__.py) | Rende questa cartella importabile da Python. |

## Che cosa è già utilizzabile

Il prototipo offre un'interfaccia Python tramite `PrototypeController`:

- `get_hardware_catalog()`: mostra dispositivi e vincoli disponibili;
- `prepare_request(...)`: controlla circuito e vincoli senza chiamare l'LLM;
- `request_recommendation(...)`: recupera gli esempi e ottiene una proposta validata;
- `compile_recommendation(..., user_confirmed=True)`: compila la proposta conservata dal servizio.

La funzione `build_default_service` collega i componenti locali e richiede
un adattatore `llm_gateway`. Il collegamento ai modelli locali per gli esperimenti
si trova in [llm_selection/](../llm_selection/README.md).

Il controller è una base per una futura interfaccia utente. In questa cartella
non è presente un'applicazione web completa. La dashboard Qdrant serve a
esplorare gli esempi, non a usare l'assistente.

## Come mostrarlo

Per una dimostrazione sono disponibili tre livelli:

1. **Dataset:** esplorare esempi, dispositivo vincente e risultati nella
   [dashboard](qdrant_dashboard/README.md).
2. **Recupero:** usare `scripts/17_rag_v2.py query --qasm PERCORSO.qasm --k 5`
   con l'ambiente del progetto. Mostra la preparazione del prompt e gli esempi,
   senza chiamare un LLM o compilare.
3. **Flusso applicativo:** consultare o eseguire
   `tests/test_prototype_architecture.py`, che usa un LLM simulato e controlla
   correzione, conferma e compilazione.

Queste prove mostrano il funzionamento del sistema. La qualità delle scelte
LLM deve essere stabilita dal confronto sulla validation e poi dal test,
secondo il [protocollo sperimentale](../docs/protocollo_sperimentale.md).

I dettagli dell'architettura e delle decisioni precedenti sono conservati
nell'[approfondimento del prototipo](../docs/approfondimenti/prototipo_architettura.md).

[Torna alla guida del progetto](../README.md).

# Libreria dell'assistente

Questa cartella descrive le informazioni scambiate dal prototipo e raccoglie
le operazioni che leggono il circuito, selezionano l'hardware compatibile,
recuperano esempi e compilano la proposta. Il programma
[app.py](../../app.py) coordina queste operazioni.

| File o cartella | Funzione |
| --- | --- |
| [models.py](models.py) | Rappresenta richieste, circuiti, vincoli, cataloghi, maschere, evidenze, proposte e circuiti compilati. |
| [ports.py](ports.py) | Descrive le interfacce Python dei componenti; contiene anche contratti conservati per compatibilità. |
| [errors.py](errors.py) | Esprime gli errori della richiesta con codici, messaggi e posizione del campo. |
| [schema_validation.py](schema_validation.py) | Legge JSON rigoroso e controlla il sottoinsieme JSON Schema usato nel progetto. |
| [adapters/](adapters/README.md) | Implementa lettura QASM, catalogo hardware, recupero RAG e compilazione Qiskit. |

La costruzione dei messaggi e la verifica della risposta LLM corrente sono
in [prompting/](../prompting/README.md). Il formato corrente della risposta
è v4: coppia dispositivo-configurazione, fatti controllabili e ipotesi libera.
Alcuni modelli interni conservano nomi o versioni storiche: non sostituiscono
il contratto applicato da `app.py`.

La descrizione tecnica completa è in
[architettura e flusso](../../docs/architettura_e_flusso.md).
[Torna ai componenti](../README.md).

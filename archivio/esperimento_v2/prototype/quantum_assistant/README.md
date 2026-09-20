# Libreria dell'assistente

Questa cartella coordina il percorso dalla richiesta dell'utente alla
compilazione. Tiene separate le regole del sistema dalle implementazioni di
Qdrant, del modello linguistico e di Qiskit.

La [guida del prototipo](../README.md) descrive il funzionamento generale e
le possibilità di dimostrazione.

## File

| File | A cosa serve |
| --- | --- |
| [__init__.py](__init__.py) | Espone le classi pubbliche della libreria. |
| [models.py](models.py) | Definisce le strutture dati: circuito, vincoli, catalogo, esempi, evidenze, proposta e compilazione. |
| [ports.py](ports.py) | Definisce le operazioni richieste ai componenti sostituibili, come recupero, LLM e compilatore. |
| [services.py](services.py) | Coordina preparazione, recupero, proposta, eventuali correzioni e compilazione confermata. |
| [controller.py](controller.py) | Espone operazioni adatte a una futura interfaccia e conserva le proposte validate per la compilazione. |
| [factory.py](factory.py) | Costruisce il servizio con i componenti locali, il catalogo v2 e il collegamento LLM fornito dal chiamante. |
| [errors.py](errors.py) | Rappresenta gli errori della richiesta con codici e campi riconoscibili. |
| [schema_validation.py](schema_validation.py) | Controlla i documenti JSON usando le regole degli schemi del progetto. |
| [adapters/](adapters/README.md) | Contiene le implementazioni concrete di tutti i collegamenti. |

## Confini utili da ricordare

Il servizio decide **quando** eseguire ogni fase. Gli adattatori stabiliscono
**come** leggere il circuito, recuperare esempi o compilare.
Il controller conserva le raccomandazioni controllate: la compilazione
non riceve una proposta liberamente modificabile dal chiamante.

Gli schemi di richiesta, catalogo, maschera hardware e risposta LLM si trovano
in [schemas/](../../schemas/README.md). I controlli automatici sono descritti in
[tests/](../../tests/README.md).

La factory permette recupero con Qdrant, confronto locale esaustivo oppure
assenza deliberata di recupero. Il modello linguistico resta un componente
esplicito da configurare; non viene scelto automaticamente dalla libreria.

Le cartelle `__pycache__/`, quando presenti, sono generate da Python.

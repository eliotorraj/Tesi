# Componenti concreti dell'assistente

Gli adattatori collegano le regole dell'assistente ai dati e agli strumenti
usati nel progetto. Ogni file copre una fase riconoscibile del flusso.

## Richiesta e hardware

| File | A cosa serve |
| --- | --- |
| [request.py](request.py) | Legge la richiesta JSON e il circuito OpenQASM 2, calcola le caratteristiche e controlla i vincoli dell'utente. |
| [hardware.py](hardware.py) | Costruisce il catalogo MQT e determina quali dispositivi rispettano circuito e vincoli. |
| [parsing.py](parsing.py) | Mantiene disponibili le importazioni delle versioni precedenti; rimanda ai componenti attuali. |

## Recupero degli esempi

| File | A cosa serve |
| --- | --- |
| [rag_dataset.py](rag_dataset.py) | Carica la fonte RAG e controlla identità, provenienza train e coerenza delle evidenze. |
| [rag_features.py](rag_features.py) | Trasforma le 49 caratteristiche usando parametri stimati sul solo train e definisce la distanza Manhattan. |
| [qdrant_context.py](qdrant_context.py) | Prepara e verifica l'indice Qdrant locale e cerca gli esempi compatibili. Offre anche il confronto esaustivo di riferimento e la modalità senza recupero. |
| [rag_checks.py](rag_checks.py) | Verifica il recupero e la costruzione dei prompt sulla validation senza chiamare LLM o compilatori. |
| [context.py](context.py) | Costruisce il registro delle evidenze e il prompt del modello. Conserva anche un lettore JSON per i collegamenti compatibili. |

Il recupero seleziona esempi dal train compatibili con i dispositivi ammessi.
La ricerca riguarda le caratteristiche dei circuiti: non usa i punteggi del
circuito di validation o test per decidere quali esempi mostrare al modello.

## Modello, controlli e compilazione

| File | A cosa serve |
| --- | --- |
| [llm.py](llm.py) | Definisce il collegamento configurabile a un modello e l'errore esplicito quando tale collegamento manca. |
| [validation.py](validation.py) | Controlla formato, dispositivo, configurazione, affermazioni e riferimenti della risposta LLM. |
| [explanations.py](explanations.py) | Produce la spiegazione dai soli dati e riferimenti già validati. |
| [compilation.py](compilation.py) | Esegue il piano Qiskit approvato e controlla che il circuito prodotto rispetti il Target. |
| [__init__.py](__init__.py) | Raccoglie gli adattatori esposti dalla libreria. |

Una citazione deve appartenere agli esempi effettivamente recuperati.
Il modello non può introdurre evidenze nuove. Un errore del database o dei
dati ferma il flusso; non viene nascosto sostituendo automaticamente il
recupero.

Per i dettagli del formato e dei controlli, leggere
l'[approfondimento dell'architettura](../../../docs/approfondimenti/prototipo_architettura.md).
Le cartelle `__pycache__/`, quando presenti, sono generate da Python.

[Torna alla libreria](../README.md).

# Operazioni concrete dell'assistente

Gli adattatori collegano le regole del prototipo a Qiskit, ai Target di MQT
Bench e al Dataset train. Ogni file realizza una fase del percorso dal
circuito alla proposta compilabile.

| File | Funzione |
| --- | --- |
| [request.py](request.py) | Legge OpenQASM 2, ricava le caratteristiche del circuito e controlla la richiesta e i vincoli. |
| [hardware.py](hardware.py) | Costruisce il catalogo verificato dei Target e filtra i dispositivi secondo i vincoli. |
| [rag_dataset.py](rag_dataset.py) | Carica i 396 esempi train distribuiti e ne verifica integrità, provenienza ed evidenze. |
| [rag_features.py](rag_features.py) | Trasforma le 49 caratteristiche con parametri ricavati dal train e calcola la distanza Manhattan. |
| [qdrant_context.py](qdrant_context.py) | Crea e verifica l'indice locale e recupera gli esempi più vicini. Contiene anche componenti espliciti senza RAG e di riferimento esaustivo. |
| [context.py](context.py) | Costruisce il registro delle evidenze e il documento completo dal quale si ricava l'ingresso del modello. |
| [compilation.py](compilation.py) | Compila con una configurazione del catalogo e controlla operazioni e collegamenti del circuito prodotto. |

Il flusso pubblico usa Qdrant locale. Gli esempi provengono solo dal train;
la ricerca non usa punteggi del circuito da valutare. Un errore dei dati o
del database interrompe il percorso e non attiva una modalità alternativa.

Il server LLM è chiamato da [app.py](../../../app.py). La risposta viene
verificata da [facts.py](../../prompting/facts.py).
Per algoritmi, controlli e limiti leggere
[architettura e flusso](../../../docs/architettura_e_flusso.md).

[Torna alla libreria](../README.md).

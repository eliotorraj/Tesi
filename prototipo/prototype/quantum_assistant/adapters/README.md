# Implementazioni delle operazioni

| Modulo | Responsabilità |
| --- | --- |
| `request.py` | Legge il QASM, estrae caratteristiche e normalizza i vincoli. |
| `hardware.py` | Ricostruisce i Target e filtra quelli compatibili. |
| `rag_dataset.py`, `rag_features.py` | Verificano il train e definiscono trasformazione e distanza. |
| `qdrant_context.py` | Costruisce e interroga l'indice Qdrant locale. |
| `context.py` | Organizza esempi ed evidenze nel documento della richiesta. |
| `compilation.py` | Risolve i parametri ammessi, compila con Qiskit e controlla base e collegamenti. |

Le classi disponibili supportano anche interfacce strutturate. Il percorso pubblico da leggere per primo è `app.py`: il suo contratto LLM effettivo è facts v4, preparato da `prototype/prompting/`. Il trasporto HTTP e la scelta CPU/GPU sono descritti nella [guida del runtime](../../../docs/installazione_e_runtime.md), non nel catalogo dei Target.

La [spiegazione del flusso](../../../docs/architettura_e_flusso.md) collega ciascun modulo alla fase in cui viene usato.

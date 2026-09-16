# Preparazione comune dei messaggi LLM

Questa cartella trasforma il contesto completo dell'assistente in messaggi
compatti per il modello. Mantiene ricostruibili circuito, esempi e valori.
La stessa implementazione viene usata dalla selezione locale, dal collegamento
LLM del prototipo e dall'esportazione dei prompt per la chat.

| File | A cosa serve |
| --- | --- |
| `__init__.py` | Espone le funzioni comuni della cartella. |
| `compact.py` | Abbrevia le fonti, raccoglie le ripetizioni e verifica la ricostruzione; ripristina le sigle delle risposte. |
| `complete_graph.py` | Rappresenta i grafi completi tramite una regola esatta. |
| `wire.py` | Converte gruppi di dati in tabelle e li ricostruisce. |
| `rendering.py` | Compone istruzioni e dati nei messaggi inviati al modello. |
| `output_contract.py` | Spiega le regole che una risposta deve rispettare. |

Il Dataset resta completo e il recupero RAG precede questa trasformazione.
Questa cartella non carica modelli e non esegue compilazioni.

Dettagli, percorso del comando tecnico e verifiche nella
[guida della compattazione](../../docs/approfondimenti/compattazione_prompt.md).

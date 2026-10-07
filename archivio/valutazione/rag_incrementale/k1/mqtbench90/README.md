# Test k=1 sui 90 MQT Bench

Questa area contiene il RAG fisso e quattro varianti incrementali, tutte con k=1.
Usa gli stessi 90 circuiti Test del manifest originale. Il Dataset iniziale
contiene i 396 esempi train.

Il comando di avvio è [../avvia_mqtbench90.py](../avvia_mqtbench90.py).
L'identificativo predefinito è `mqtbench90_rag_k1_v1`.
Le istruzioni complete sono nel [README del confronto k=1](../README.md).

- `rag_fisso/`: nuova esecuzione del controllo con Dataset fisso.
- `ordinamenti/`: quattro memorie e sequenze indipendenti.
- `piano.json`: impostazioni dichiarate della prova.
- [report/](report/README.md): analisi, tabelle, grafici e LaTeX/PDF.
- `test_incrementale.py` e `test_report.py`: verifiche tecniche senza LLM reale.

Nessun risultato delle precedenti campagne MQT Bench o QASMBench viene
importato nella memoria. L'oracle MQT Bench viene letto soltanto dal report.

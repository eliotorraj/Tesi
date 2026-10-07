# Test k=1 sui 50 QASMBench

Questa area contiene il RAG fisso e quattro varianti incrementali, tutte con k=1.
Usa i 50 circuiti esterni già selezionati: 30 piccoli, 15 medi e 5 grandi.
Il Dataset iniziale contiene i 396 esempi train.

Il comando di avvio è [../avvia_qasmbench50.py](../avvia_qasmbench50.py).
L'identificativo predefinito è `qasmbench50_rag_k1_v1`.
Le istruzioni complete sono nel [README del confronto k=1](../README.md).

- `rag_fisso/`: nuova esecuzione del controllo con Dataset fisso.
- `ordinamenti/`: quattro memorie e sequenze indipendenti.
- `piano.json`: impostazioni dichiarate della prova.
- [report/](report/README.md): analisi, tabelle, grafici e LaTeX/PDF.
- `test_incrementale.py` e `test_report.py`: verifiche tecniche senza LLM reale.

Nessun risultato delle precedenti campagne QASMBench o MQT Bench viene
importato nella memoria. L'oracle QASMBench viene letto soltanto dal report.

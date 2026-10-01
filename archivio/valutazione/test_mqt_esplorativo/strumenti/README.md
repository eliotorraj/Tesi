# Strumenti della valutazione

Questi moduli svolgono le operazioni richiamate dagli ingressi nella cartella
superiore. Non sono necessari al prototipo per un circuito libero.

| File | Funzione |
| --- | --- |
| `common.py` | Risolve percorsi, legge i dati e conserva scritture e impronte. |
| `gates.py` | Verifica requisiti, provenienza e contratto sperimentale. |
| `mqt_gate.py` | Controlla i modelli MQT in un processo separato. |
| `runner.py` | Coordina un metodo, registra gli errori e misura le fasi. |
| `worker.py` | Compila un circuito in un processo separato. |
| `score.py` | Calcola expected fidelity sul circuito compilato. |
| `report.py` | Produce i riepiloghi precedenti dagli esiti conservati. |

Il framework è importato da `prototipo/`; esiti e preparazione restano
nell'area sperimentale corrente. Le fonti congelate non vengono riscritte.
Il contratto rifiuta la ripresa se cambiano codice, dati o impostazioni.
I dettagli del metodo sono nel
[protocollo corrente](../../../../prototipo/docs/protocollo_sperimentale.md).
Per struttura e stato dell'area leggere il [README superiore](../README.md).

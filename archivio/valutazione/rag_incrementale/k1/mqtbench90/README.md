# MQT Bench k=1 campaign

This campaign uses the 90 original Test circuits and 396 initial train examples. `rag_fisso/` holds the newly run fixed-memory control; `ordinamenti/` holds four separate incremental sequences; `piano.json` fixes settings. `report/` contains analysis code and outputs. The local `test_incrementale.py`, `test_report.py` and `verifica_report.py` cover software behavior.

The parent launcher is `avvia_mqtbench90.py`, with default identifier `mqtbench90_rag_k1_v1`. Prior campaign outcomes are not imported into memory. Only report generation reads the MQT Bench oracle.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [report/](report/README.md) | MQT Bench k=1 reports. |

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

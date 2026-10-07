# Incremental RAG on QASMBench

This self-contained campaign uses the 50 selected external circuits and the saved fixed k=5 LLM + RAG run as a historical control. Every order starts with the same 396 train examples and an empty independent memory. MQT Bench observations and other order memories are not imported.

`esperimento.py`, `adattatore.py`, `memoria.py`, `registro.py` and `comune.py` implement execution. `ordinamenti/` contains manifest, reverse and two seeded permutations. `piano.json` and `protocollo.md` define conditions; `report/` reads saved outcomes and the external oracle; `verifiche_sviluppo/` preserves software checks. Inspect saved step/completion records for campaign status; early preparation notes are historical.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [report/](report/README.md) | QASMBench incremental-memory reports. |
| [verifiche_sviluppo/](verifiche_sviluppo/README.md) | QASMBench incremental development checks. |

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

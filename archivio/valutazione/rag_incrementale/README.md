# Incremental retrieval experiments

This directory studies whether previously completed compilations help later decisions. The original campaign uses 90 MQT Bench Test circuits, a fixed 396-example train Dataset and four independent processing orders. `qasmbench50/` provides a separate external campaign; `k1/` compares newly run fixed and incremental systems with one example.

`esperimento.py` coordinates preparation/execution; `adattatore.py` connects the framework; `memoria.py` manages admitted observations; `registro.py` preserves steps; `comune.py` handles shared settings. `piano.json` and `protocollo.md` define conditions. `ordinamenti/` contains manifest, reverse and two seeded orders; `report/` analyzes saved results; `verifiche_sviluppo/` documents checks.

Each order has its own memory and excludes the current circuit and future observations. Completed-step checks and source contracts govern resume. Follow the local protocol for these specialized campaigns; do not infer current completion from the original preparation date.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [k1/](k1/README.md) | Fixed and incremental RAG with k=1. |
| [qasmbench50/](qasmbench50/README.md) | Incremental RAG on QASMBench. |
| [report/](report/README.md) | MQT Bench incremental-memory reports. |
| [verifiche_sviluppo/](verifiche_sviluppo/README.md) | Incremental-procedure development checks. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

# Fixed and incremental RAG with k=1

`mqtbench90/` and `qasmbench50/` hold separate campaigns and reports. Each compares a new fixed-Dataset run (`00_rag_fisso`) with four incremental orders: manifest, reverse, seed 20261002 and seed 20261003. All use one retrieved example per decision; older k=5 outcomes are not reused as the fixed control.

`avvia_mqtbench90.py` and `avvia_qasmbench50.py` are launchers; `report_mqtbench90.py` and `report_qasmbench50.py` generate reports. `prompt_k1/` supports the one-example contract, and `verifiche_sviluppo/` records checks. Inspect each launcher's `--help` before use; real runs require the configured Qwen server and exact GGUF. The original Dataset and other campaign memories remain separate.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [mqtbench90/](mqtbench90/README.md) | MQT Bench k=1 campaign. |
| [qasmbench50/](qasmbench50/README.md) | QASMBench k=1 campaign. |
| [verifiche_sviluppo/](verifiche_sviluppo/README.md) | Development checks for k=1. |

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

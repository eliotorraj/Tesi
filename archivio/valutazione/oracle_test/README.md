# MQT Bench Test oracle

`genera_oracle_test.py`, `oracle_core.py` and `oracle_worker.py` compute a separate exhaustive reference for the 90 Test circuits. `stato_riferimento_attuale.json` records the reference available before this extension; `test_oracle.py` and `verifiche_sviluppo/` document technical checks. `confronto_llm_rag_k5/` contains the analysis of the completed max3 oracle.

The Test oracle uses the maximum observed score across the grid and three seeds. This differs from the validation reference based on eligible seed medians. Keep these reference definitions distinct. Oracle outcomes are stored separately and do not enter the selected prototype's Dataset, prompt or retrieval index.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [confronto_llm_rag_k5/](confronto_llm_rag_k5/README.md) | Five-example RAG versus Test oracle. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

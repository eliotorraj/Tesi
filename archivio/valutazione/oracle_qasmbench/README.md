# External QASMBench oracle tools

This directory contains the separate exhaustive reference calculation for the selected 50 QASMBench circuits. `genera_oracle_test.py` coordinates execution; `oracle_core.py` and `oracle_worker.py` implement the grid and isolated jobs. `catalogo.json` fixes the search space. `analizza.py`, `impagina.py` and `confronto_llm_rag_k5/` support comparison with saved LLM + RAG decisions.

Using the configured Python 3.12 environment, run the entry point from the repository root to inspect options: `python -B archivio/valutazione/oracle_qasmbench/genera_oracle_test.py --help`.

Oracle results are evaluation references, not prompt or RAG inputs. `verifiche_sviluppo/` records preparation checks; `test_oracle.py` and `test_confronto.py` use controlled test data. Consult saved completion records for actual generation status.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [verifiche_sviluppo/](verifiche_sviluppo/README.md) | QASMBench oracle preparation checks. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

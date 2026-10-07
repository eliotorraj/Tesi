# MQT Bench incremental-memory reports

`genera.py` analyzes the four 90-circuit orders, their fixed historical control and the MQT Bench oracle. `oracoli.py` checks reference data; `sintesi.py` and `aggiorna_sintesi.py` support report summaries.

From the repository root, the generator accepts `--experiment-id mqtbench90_incrementale_v1 --pdf`. Its default oracle is the saved comparison under `archivio/valutazione/oracle_test/confronto_llm_rag_k5/risultati/dati.json`; `--oracle` selects another verified copy and `--senza-oracle` explicitly omits it. Generation reads results without updating memory. Old report versions retain their original data and provenance.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

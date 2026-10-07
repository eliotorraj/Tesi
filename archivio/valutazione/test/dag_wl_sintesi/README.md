# DAG/WL retrieval with prompt summaries

The launcher `../llm_rag_dag_wl_sintesi.py` uses the same frozen WL settings and five examples as retrieval-only WL, adding deterministic DAG summaries for the query and examples.

Summaries include operation counts, dependency layers, maximum layer width, two-qubit interactions and the eight most frequent directed operand-role transitions, with omitted types declared. Layers include barriers and are not physical durations. TOON round-trip checks preserve the encoded data. The response schema, fact policy and generation parameters remain those of the comparison.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

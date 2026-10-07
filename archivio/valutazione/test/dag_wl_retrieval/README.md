# DAG/WL retrieval campaign

This variant retrieves five train examples using DAG/WL similarity. The launcher is `../llm_rag_dag_wl.py`, with shared code in `../strumenti/dag_wl_*.py`.

Five train examples are selected with WL at the frozen validation depth. The standard prompt content is otherwise retained; the DAG itself is not sent to the model. This method has separate artifacts from the summary variant. Use the saved WL configuration for provenance rather than choosing depth on Test outcomes.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

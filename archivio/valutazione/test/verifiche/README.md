# Evaluation software checks

`test_indipendenti.py` checks isolation, resume and metrics; `test_server.py` checks model/server identity; `test_trasporto.py` covers transport failures; `test_percorsi.py` covers layouts and source contracts. Retrieval variants have dedicated `test_numero_esempi.py`, `test_recupero_random.py` and `test_dag_wl.py`.

Using the configured Python 3.12 environment, run the family from the repository root with `python -m unittest discover -s archivio/valutazione/test/verifiche -v`. Tests use technical circuits and simulated responses without opening a new scientific campaign. Report-generator checks are in the sibling `report/verifiche/` directory.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

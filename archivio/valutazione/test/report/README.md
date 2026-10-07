# Test report generators

These programs analyze saved outcomes without launching inference or compilation. `fonti.py` and `dati.py` load sources; `confronto.py` computes comparisons; `impaginazione.py`, `pannelli.py` and the LaTeX fragments build presentation. `genera.py` produces the original reports, while `genera_recupero_random.py` and `genera_confronto_cinque.py` produce later extensions. Fact audits have separate `analizza_fatti*.py` modules; `verifiche/` holds tests.

Outputs are versioned in the sibling `report_generati/` tree. The MQT source prefers the separately contracted run under `test_mqt_esplorativo/` when present, without summing duplicate campaigns. Reports retain reduced Training set coverage, missing values and comparable-case denominators. Generator snapshots beside published reports identify the source revision used.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

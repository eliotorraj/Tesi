# DAG/WL retrieval validation

`valida.py` compares Manhattan retrieval with WL depths using only the 88 validation circuits and 396 train examples, always k=5. It reads sealed validation aggregates without LLM calls or new compilation. The historical selection transfers the first configuration of the first retrieved example, an indirect retrieval measure rather than LLM performance.

The validation covered wl_v1 (h=1–3), wl_v2 (h=1–6) and wl_v3 (h=1–30). The later grids were adaptive extensions, with their own contracts. `selezioni/wl_v3/` records h=24; `revisioni_codice/` preserves earlier sources; `analisi_copertura_train/` measures train graph diameters. `verifiche/` and `verifiche_sviluppo/` hold checks.

The current toolkit's WL selector has its own documented aggregation criterion. Do not silently equate it with this historical procedure or use Test outcomes to redefine the main configuration.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [analisi_copertura_train/](analisi_copertura_train/README.md) | Train graph propagation coverage. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

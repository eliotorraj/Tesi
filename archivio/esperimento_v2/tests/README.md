# Archived software checks

`test_*.py` covers protocol integrity, split separation, Dataset aggregation, assistant responses, retrieval, LLM selection and MQT support. Many tests simulate model calls; some open temporary Qdrant stores or perform small real training/compilation jobs.

These checks document software behavior, not model quality. Run only the relevant family in a compatible archived environment. Current toolkit checks are under root-level `riproducibilita/verifiche/`, and standalone prototype checks under `archivio/valutazione/verifiche_prototipo/`.

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

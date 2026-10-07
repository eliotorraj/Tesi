# LLM with five random train examples

`seed_20260927/` contains the saved random-retrieval campaign. Its launcher is `../llm_recupero_random.py`. This differs from `casuale.py`, which samples a device/configuration pair without an LLM.

The method uniformly samples five eligible train records without replacement from a stable `rag_id` ordering. The per-circuit seed combines the configured seed and QASM fingerprint. Repairs reuse the same examples; fewer than five eligible examples causes failure. No Manhattan distance or Qdrant search is used. The model and facts v4 policy match the corresponding comparison.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

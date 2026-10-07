# Train data for RAG

| Entry | Purpose |
| --- | --- |
| `circuits/` | QASM sources for the 396 unique train circuits. |
| `rag_examples.jsonl` | Retrieved examples and compilation choices. |
| `train_manifest.json` | The 422 original train records, including aliases. |
| `transform.json` | Feature scaling fitted on train only. |
| `catalog_original.json` | Catalog used to produce the examples. |
| `seal.json` | Integrity references for the package. |
| `pstools_verified.json` | Verified tool metadata for the Windows desktop runtime. |

Setup or `app.py prepare` prepares retrieval from the train examples. Validation and Test scores are not inputs to new recommendations. To replace the corpus, use [riproducibilita/](../../riproducibilita/README.md) and export a new prototype with its own provenance.

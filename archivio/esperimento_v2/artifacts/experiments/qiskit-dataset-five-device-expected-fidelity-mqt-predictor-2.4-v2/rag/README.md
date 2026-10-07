# RAG index and verification

The archived retriever uses 396 train examples, 49 numeric features and exact Manhattan distance. `index/manifest.json` records identity; `index/transform.json` stores train-derived scaling; `index/qdrant/` stores vectors and payloads.

`verification.json` and `validation_check.json` record index/retrieval checks, not LLM decision quality. `dashboard/` contains an inspection copy and its checks; `audit/` contains additional retrieval audits. Temporary `.index-build-*` directories are build evidence, not alternate selected indexes.

[Parent directory](../README.md) · [Current repository guide](../../../../../../README.md)

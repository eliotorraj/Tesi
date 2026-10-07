# JSON contracts

The schemas describe requests, evidence and accepted responses. The public client uses `llm_recommendation_v4.schema.json` through `prototype/prompting/facts.py`. Other schemas cover intermediate structures.

Checks include catalog membership, device compatibility and facts matched against prompt evidence. Contract hashes are part of package integrity. See [architecture and data flow](../docs/architettura_e_flusso.md).

# Operation implementations

| Module | Purpose |
| --- | --- |
| `request.py` | Read QASM, extract features and normalize constraints. |
| `hardware.py` | Reconstruct Targets and filter compatible devices. |
| `rag_dataset.py`, `rag_features.py` | Verify train inputs and define transformation and distance. |
| `qdrant_context.py` | Build and query the local index. |
| `context.py` | Organize examples and request evidence. |
| `compilation.py` | Resolve parameters, compile and check gates and connectivity. |

Start with `app.py` for the public execution path. Its facts v4 prompt and response checks are in `prototype/prompting/`. Additional adapters support internal operations rather than separate CLI commands. See [architecture and data flow](../../../docs/architettura_e_flusso.md).

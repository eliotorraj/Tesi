# Framework types and operations

`models.py` defines requests, Targets, examples, recommendations and compilation artifacts. `ports.py` defines operation interfaces. [adapters/](adapters/README.md) implements them. `schema_validation.py` checks the supported JSON Schema subset; `errors.py` defines exceptions.

The public path starts in `app.py` and uses train retrieval, TOON and facts v4. Other Python interfaces are framework building blocks. See the [architecture guide](../../docs/architettura_e_flusso.md). New experimental campaigns belong in [riproducibilita/](../../../riproducibilita/README.md).

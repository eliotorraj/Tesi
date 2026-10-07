# Historical assistant library

`models.py` and `ports.py` define types and interfaces. `services.py` coordinates request preparation, retrieval, recommendation, repairs and confirmed compilation. `controller.py` retains validated proposals for an application interface; `factory.py` assembles components. `adapters/` contains concrete integrations; schema validation and errors have separate modules.

This library documents the earlier service architecture. The selected standalone client uses a smaller public path under root-level `prototipo/`.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [adapters/](adapters/README.md) | Historical assistant adapters. |

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

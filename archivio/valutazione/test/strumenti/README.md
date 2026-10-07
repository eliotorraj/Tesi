# Historical evaluation utilities

`common.py` resolves paths and records; `gates.py` checks inputs/contracts; `mqt_gate.py` verifies models in a separate process. `runner.py` coordinates methods, `worker.py` isolates compilation, `score.py` computes expected fidelity and `report.py` produces earlier summaries.

`recupero_random.py` and `numero_esempi.py` implement retrieval variants; `dag_wl_*.py` implements graph extraction, validation and campaigns. The framework is imported from root-level `prototipo/`. Saved contracts reject resume after source, data or setting changes; frozen runs require their recorded revisions.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

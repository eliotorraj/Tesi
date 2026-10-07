# Archived prompt representations

`minimal.py` and `rendering.py` build reduced prompts and repair messages. `toon.py` and `toon_runtime/` provide reversible TOON encoding. `facts.py` implements the later structured-fact checks. `compact.py`, `complete_graph.py`, `wire.py`, `output_contract.py` and `legacy_rendering.py` retain earlier formats for comparison.

Reduction occurs after retrieval and does not change train membership, feature values, distance or example order. Full QASM and provenance remain in canonical records. Use study metadata to identify the actual representation used in a given run.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

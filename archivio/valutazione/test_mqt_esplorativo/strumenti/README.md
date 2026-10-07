# Utilities for the separate MQT run

`common.py` handles paths and records; `gates.py` and `mqt_gate.py` check the separate contract and trained models; `runner.py` manages execution; `worker.py` isolates compilation; `score.py` computes expected fidelity; `report.py` summarizes saved outcomes.

These modules belong to the separately contracted evaluation and preserve its reduced Training set conditions. They are not required for ordinary QAdviser usage. Resume is tied to the recorded source/data/settings fingerprints.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

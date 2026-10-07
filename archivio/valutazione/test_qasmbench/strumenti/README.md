# QASMBench execution utilities

`runner.py` records one method's outcomes; `worker.py` isolates compilation with an external 100-second deadline. `gates.py` checks inputs, versions and Targets and freezes the contract; `mqt_gate.py` checks selector/policy provenance. `common.py` manages paths and protected records; `score.py` computes expected fidelity.

The code reuses the prototype framework and archived trained-artifact checks without importing previous Test launchers. It does not install or alter trained models.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

# Five-device expected-fidelity Dataset

`expected_fidelity/full/` contains the train/validation compilation grid. `circuits/` holds operational QASM copies; the five device directories hold per-device attempts and aggregates; `global/` combines eligible results and supplies RAG examples.

Each compatible circuit/device pair was evaluated with twelve configurations and three seeds. Scores are expected-fidelity estimates on synthetic Targets, not hardware measurements. The `full` name describes the corpus scope and does not itself establish Test evaluation. Consult the frozen manifests, attempt records and aggregation metadata for coverage and denominators.

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

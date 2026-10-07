# Five-device v2 artifacts

This directory connects the frozen corpus, device identities, compilation attempts and LLM studies for `qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2`.

`manifests/` identifies inputs; `sources/` holds train/validation copies. `logs/` preserves training evidence. `qiskit_dataset_cache/` stores attempts and compiled QASM. `rag/` contains retrieval indexes and checks; `llm_selection/` contains model selection records. `plans/` and `method_results/` preserve planned comparisons and recorded outcomes.

A planned method or an initial log does not establish that a run completed. Consult the associated completion records and later evaluation archive rather than treating old status notes as current state.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [checkpoints/](checkpoints/README.md) | RL training reference. |
| [llm_selection/](llm_selection/README.md) | LLM study records. |
| [logs/](logs/README.md) | Execution logs. |
| [manifests/](manifests/README.md) | Frozen corpus identity. |
| [models/](models/README.md) | MQT model documentation. |
| [plans/](plans/README.md) | Historical comparison plans. |
| [qiskit_dataset_cache/](qiskit_dataset_cache/README.md) | Qiskit compilation cache. |
| [rag/](rag/README.md) | RAG index and verification. |
| [sources/](sources/README.md) | Prepared circuit sources. |

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

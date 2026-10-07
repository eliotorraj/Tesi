# Archived Qiskit Dataset implementation

`catalog.py` loads device/configuration definitions; `core.py` prepares circuits, splits and attempts; `generation.py` compiles and records successes or failures. `views.py` aggregates seeds into examples, `aggregation.py` combines device views, and `reporting.py` produces summaries. `experiment_v2.py` supports the frozen v2 workflow.

The numbered scripts in the sibling `scripts/` directory call these modules. RAG examples come only from train. MQT selector training is a separate pipeline based on RL compilation outcomes.

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

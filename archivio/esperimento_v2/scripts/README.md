# Historical experiment commands

Numbered scripts preserve environment checks, RL/selector training, model synchronization, corpus preparation, Qiskit generation/aggregation, method plans, evaluation, retrieval and dashboard inspection. Prefixes 07 and 08 are reused historically, so this is not a sequence to execute blindly.

`16_run_pipeline_v2.py` orchestrates the earlier pipeline, `17_rag_v2.py` handles retrieval, and `report_local_validation_v2.py` generates the explained validation report. `mqt_model_artifacts.py` and `mqt_predictor_protocol.py` provide shared checks. Commands originally ran from the archived workspace root and require its environment and artifacts. Use `riproducibilita/` for new campaigns.

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

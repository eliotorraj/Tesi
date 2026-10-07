# Local-llm-v2: structured facts and hypotheses

This package contains the second local validation study. `settings.py` and `study.py` define candidates and frozen inputs; `run.py` records attempts; `evaluate.py` computes outcomes; `report.py` and `plots.py` produce reports; `__main__.py` is the module entry point.

Schema v4 requires `selected_device`, `config_id`, one or two distinct facts and a hypothesis of at most 1,000 characters. Facts are checked against supplied evidence. The free hypothesis is not semantically certified. Up to three responses are allowed; the last may accept an allowed pair with unverified facts, recorded explicitly. Original decisions, interruption records, seals and selection belong to the corresponding archived study.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

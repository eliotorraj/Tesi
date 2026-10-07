# MQT Targets, policies and selector

| Entry | Purpose |
| --- | --- |
| `gestione.py` | Inspect Targets and verify the environment. |
| `addestra_rl.py` | Train one RL compilation policy per selected device. |
| `addestra_selettore.py`, `motore_ml.py`, `deduplica.py` | Collect circuit/device outcomes, prepare the Training set and train the selector. |
| `validazione_selettore.py` | Validate the selector and artifacts. |
| [artefatti/](artefatti/README.md) | MQT training documentation. |

The environment uses Python 3.12, MQT Predictor 2.4.0 and the toolkit lock. Installation alone does not provide trained models. Follow the [guide](../documentazione/guida.md) for `esperimento.py mqt ...` and Bell checks.

For named runs, put `--esperimento NAME` before `mqt`. Configure devices and RL steps before preparation with `configura.py dispositivi` and `parametri --passi-rl`. Explicitly include `mqt` among Test methods to evaluate it.

MQT and llama.cpp use different stacks; GPU availability for one does not guarantee it for the other. Smoke training validates the pipeline, not compilation quality.

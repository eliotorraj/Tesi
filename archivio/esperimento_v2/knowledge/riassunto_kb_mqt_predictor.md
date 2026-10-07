# Project context and MQT concepts

Use the [repository README](../../../README.md) for current navigation and the [current experimental protocol](../../../prototipo/docs/protocollo_sperimentale.md) for scientific rules. The [archived protocol](../docs/protocollo_sperimentale.md) and dated records explain earlier work; they are not instructions to reopen completed experiments.

## Purpose and current organization

QAdviser evaluates whether an LLM supported by earlier compilation examples can choose a useful quantum device and Qiskit configuration. The completed comparisons include the selected LLM with and without RAG, random example retrieval, Random and MQT Predictor. Earlier plans also discussed a frontier LLM and fixed Qiskit baselines; a planned comparison must not be described as completed without its records.

The pinned experiment uses MQT Predictor **2.4.0**, Python **3.12** and the exact dependencies in `uv.lock`. MQT Predictor 2.3.0 results are historical. `prototipo/` is the standalone selected system; `riproducibilita/` supports new campaigns; `archivio/` preserves sources, experiments and provenance.

## Terminology

| Term | Meaning in this project |
| --- | --- |
| Dataset | Examples for RAG or possible LLM adaptation. |
| Training set | Circuit/device data used to train MQT Predictor's supervised selector. |
| Train | Circuits supplying examples and learning data. |
| Validation | Circuits used to select a configuration before the main comparison. |
| Test | Circuits reserved for the main evaluation; subsequent analyses of the same cases do not constitute a new unseen test. |
| Technical check | A software or resource check, without conclusions about generalization. |

Circuit/device evaluations determine selector labels: each final supervised row labels a circuit with the best device among those evaluated. Distinguish the intended 396 unique train samples from the actual 384-sample selector used in the archived MQT comparison.

## Two different MQT papers

**2023 compilation-option predictor:** a supervised model predicts a configuration covering technology, device, compiler and settings.

**2025 MQT Predictor architecture:** a supervised model selects the device. A device- and metric-specific reinforcement learning policy then selects compilation passes.

```text
MQT: circuit → features → ML selector → device → RL compiler

QAdviser: circuit and constraints → compatible devices → RAG examples
          → LLM choice → checks → Qiskit compilation
```

The comparison does not establish universal superiority. QAdviser offers greater coverage under the recorded timeout conditions; MQT has higher mean scores on shared successful cases. LLM fine-tuning is not a completed phase of this experiment.

## Meaning of quality

A source circuit is device independent and must be adapted to the selected hardware's allowed operations and connectivity. `expected_fidelity` combines operation and readout fidelities. These experiments use synthetic MQT Bench Targets, not execution on a real quantum computer.

A device is better for a particular circuit, metric, hardware description and compilation procedure. Changing any of these can change selector labels. A smoke-trained model demonstrates that the pipeline runs; it does not establish good compilation quality. Installing MQT Predictor alone does not supply the trained RL policies and supervised selector required by `qcompile`.

## Corpus and retrieval

The frozen corpus has 600 source circuits, split into 422 train, 88 validation and 90 Test entries. The train Dataset contains 396 unique records. Within this archived experiment, Dataset files and artifacts are under `datasets/experiments/` and `artifacts/experiments/`.

The original corpus in `archivio/protocollo_v1/datasets/expected_fidelity/full/` still verifies provenance. Its old scores are not reused as v2 results. Frozen manifest paths are logical references resolved by the source resolver; do not rewrite them to match a later directory layout.

The selected RAG uses train examples from the global view. It compares 49 numerical circuit features using Manhattan distance after transformations and scaling fitted on train only. Local Qdrant stores the derived index. The current circuit's evaluation score does not enter its prompt or evidence.

## History and sources

The earlier summary combined theory and conversations in more than 6000 lines. Its full text remains in the [history through 9 September](../docs/resoconti/cronologia_progetto_fino_al_9_settembre_2026.md), including TuniQ comparisons and reasons for early decisions. Read its commands and statuses in their historical context.

Papers are listed in the [knowledge README](README.md). Archived technical guides are in [docs/approfondimenti/](../docs/approfondimenti/README.md), and dated evidence is in [docs/resoconti/](../docs/resoconti/README.md).

Always distinguish claims from papers, behavior of the pinned software and this project's engineering or experimental choices. For future API or installation changes, consult official MQT documentation and package metadata rather than assuming that a paper describes the installed release.

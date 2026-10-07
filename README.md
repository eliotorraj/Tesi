# QAdviser

QAdviser is an LLM + RAG system that recommends a quantum device and a Qiskit compilation configuration for an OpenQASM 2 circuit. It retrieves train examples, checks the model's response and can compile the circuit locally. This repository also supplies tools for new experiments and an archive of the experiments behind the thesis.

## Where to start

| Your goal | Start here |
| --- | --- |
| Try the selected QAdviser prototype | [Prototype guide](prototipo/docs/guida_passo_passo.md) |
| Change circuits or models and run a new experiment | [Toolkit guide](riproducibilita/documentazione/guida.md) |
| Find completed experiments, reports and provenance | [Experiment archive](archivio/README.md) |
| Understand the experimental rules | [Current scientific protocol](prototipo/docs/protocollo_sperimentale.md) |

## Repository layout

| Directory | Contents |
| --- | --- |
| [prototipo/](prototipo/README.md) | Standalone selected prototype, train examples, setup scripts and current documentation. |
| [riproducibilita/](riproducibilita/README.md) | New circuits, MQT training, Dataset generation, LLM validation, Test evaluation and prototype export. |
| [archivio/](archivio/README.md) | Historical sources, frozen inputs, results, development checks and reorganization records. |
| [.vscode/](.vscode/README.md) | Optional editor settings and task definitions. |

The prototype and toolkit each carry their own runtime components. Neither imports code from the archive. New toolkit results are grouped by `experiment_id`; archived outcomes document earlier runs.

The current experiment uses Python 3.12 and MQT Predictor 2.4.0. Follow the installation guide and dependency lock for the component you need.

## Conventions

**Dataset** means RAG/LLM examples. **Training set** means circuit/device samples for the MQT selector. Train, validation and Test have separate roles. Catalog Targets are synthetic quantum device descriptions; the CPU/GPU running the LLM is a separate resource.

Documentation, maintained comments and program messages use English. Existing paths, command names and stored identifiers remain stable. Raw historical observations and frozen source snapshots retain their original provenance.

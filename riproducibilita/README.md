# Reproduction and new experiments

This Linux toolkit prepares circuits, trains MQT models, generates a Qiskit Dataset, selects LLM settings on validation, evaluates fixed methods on Test and exports standalone prototypes. It carries its own runtime components and does not import code from `prototipo/` or `archivio/`.

To try the already selected QAdviser system, use the [prototype guide](../prototipo/docs/guida_passo_passo.md). For new experiments, follow this toolkit's [complete guide](documentazione/guida.md) and [configuration recipes](documentazione/configurazione.md).

After setup, activate the configured Python environment and run from this directory:

```bash
python configura.py nuovo trial-cpu --profilo cpu
python configura.py mostra trial-cpu
python configura.py disponibili sistemi
python esperimento.py --esperimento trial-cpu stato
```

`nuovo` initially selects Qwen and three methods without MQT. All catalog devices and compilation configurations remain selected until narrowed down. `prepara` freezes inputs and settings before generation or training. Duplicate a prepared experiment under a new name to change those conditions. Existing command and option names retain their spelling; help text is in English.

## Directory map

| Directory | Purpose |
| --- | --- |
| [circuiti/](circuiti/README.md) | 600 train/validation/Test inputs and a separate 50-circuit QASMBench collection. |
| [mqt/](mqt/README.md) | Quantum Targets, RL policies, Training set and supervised selector. |
| [dataset/](dataset/README.md) | Qiskit grid execution, aggregation, schemas and train-only RAG examples. |
| [modelli_llm/](modelli_llm/README.md) | Model registry, GGUF locations and CPU/GPU server launcher. |
| [validation/](validation/README.md) | Model/temperature selection and optional WL retrieval selection. |
| [test/](test/README.md) | Frozen evaluation plans, methods, comparisons and optional oracle. |
| [configurazioni/](configurazioni/README.md) | Named experiments, catalog, seeds, resources and generation settings. |
| [comune/](comune/README.md) | Configuration, integrity, framework, processes, reports and export. |
| [verifiche/](verifiche/README.md) | Software checks with small circuits and a simulated LLM server. |
| [documentazione/](documentazione/README.md) | Operational guide, recipes, module map and conditions. |
| [esecuzioni/](esecuzioni/README.md) | Experiment lifecycle reference. |
| [esportazioni/](esportazioni/README.md) | Standalone prototype export instructions. |

`setup.sh`, `pyproject.toml`, `uv.lock` and `.python-version` define the Python environment; TOON has its own npm lock. Setup does not download weights or train models. `configura.py --help` lists configuration actions; `esperimento.py --help` lists phases.

CPU/GPU profiles concern LLM inference; catalog Targets describe quantum hardware. Check resources and backend support on the actual machine. The small prototype CPU example does not establish the requirements for a full campaign. Read the [conditions](documentazione/condizioni.md) for operational differences from the historical experiment, including selection criteria and MQT coverage requirements.

**Dataset** means RAG/LLM examples; **Training set** means MQT circuit/device samples. LLM fine-tuning is not implemented. `provenienza_sorgenti.json` records origins without adding archive runtime dependencies.

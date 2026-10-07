# RAG Dataset generation

`genera.py` plans train and validation grids. `qiskit_dataset/` implements catalog loading, compilation, aggregation and example generation. `schemi/` defines JSON contracts. [artefatti/](artefatti/README.md) links to the Dataset generation documentation.

After setup and preparation, from the toolkit root:

```bash
python esperimento.py --esperimento my-trial dataset
```

`--split train`, `--split validation` and `--aggrega` separate stages. Successes, errors and timeouts are recorded. Eligible medians require all three successful seeds. Only train enters retrieval examples and feature scaling. Validation scores are reserved for evaluation after decisions are sealed.

Generation uses Qiskit CPU/RAM resources, not the LLM server. Configure devices, options and workers before preparation. This Dataset is separate from the MQT Training set. See the [guide](../documentazione/guida.md).

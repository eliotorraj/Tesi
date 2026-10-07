# Toolkit software checks

After setup, activate the configured Python 3.12 environment and run from the toolkit root:

```bash
python -B -m unittest discover -s verifiche -p test_configuratore.py -v
python -B verifiche/checks.py --configuratore
```

Focused tests cover revisions, rejected edits, candidate selection, fingerprints, paths with spaces, preparation locks and independence between experiments.

`checks.py` copies the toolkit into a temporary directory, creates small QASM inputs and runs a simulated LLM server. It exercises Dataset generation, split separation, validation, Test variants, resumes, contracts, reports and export. `--configuratore` also covers named CLI configuration and CPU launcher arguments; without it, checks use explicit `--config`. Reports are compiled when LaTeX is available.

The output directory is printed and retained; `--directory /path/to/new-directory` selects it. Node.js 22 and the installed TOON codec are required. No real GGUF, GPU or RL training is needed. Software checks do not establish model quality or hardware performance.

Integration checks use one Qiskit worker, limited BLAS threads and a 300-second compilation timeout. A timeout remains a failed check with preserved records. For real inference, follow the [prototype guide](../../prototipo/docs/guida_passo_passo.md).

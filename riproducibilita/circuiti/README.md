# Input circuits

`train/`, `validation/` and `test/` contain 422, 88 and 90 OpenQASM 2 files. The 422 train records represent 396 distinct contents; aliases remain in the manifest without adding duplicate RAG examples or MQT samples. `manifest_originale.json` records the distributed corpus's provenance.

For a new corpus, use a separate root with these three split directories and QASM files directly inside them. Filenames must be unique across splits. Preparation rejects byte-identical and instruction-identical overlap; it does not prove algorithmic independence.

From the toolkit root, before preparation:

```bash
python configura.py circuiti trial-cpu --cartella /path/to/corpus --crea
```

This creates missing split directories, not circuits or their assignments. The [QASMBench selection](esterni/qasmbench/README.md) is separate. See the [configuration guide](../documentazione/configurazione.md); retain the original manifest as provenance for the supplied corpus.

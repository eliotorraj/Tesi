# Exported standalone prototypes

After validation selection, from the toolkit root:

```bash
python esperimento.py --esperimento my-trial esporta DESTINATION
```

Use a new destination; external directories are supported. The export contains framework, train Dataset, catalog, selected settings, model registry and Linux setup instructions. It excludes GGUF weights and validation/Test scores and does not overwrite `prototipo/`.

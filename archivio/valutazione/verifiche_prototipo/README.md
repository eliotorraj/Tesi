# Offline prototype development checks

`checks.py` verifies all 396 train feature extractions, Qdrant retrieval against direct distance, facts v4 with synthetic responses, context limits and Bell compilation. It was formerly `prototipo/checks.py`.

Using the configured Python 3.12 environment, run from the repository root: `python archivio/valutazione/verifiche_prototipo/checks.py`. `--quick` limits retrieval comparisons to five queries but still extracts all train features. Dated subdirectories retain later report checks. These checks do not query Qwen or run the scientific Test. Ordinary installation checks use `prototipo/app.py check`.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [confronto_cinque_2026_09_28/](confronto_cinque_2026_09_28/README.md) | Five-system report verification. |
| [report_recupero_random_2026_09_27/](report_recupero_random_2026_09_27/README.md) | Random-retrieval report verification. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

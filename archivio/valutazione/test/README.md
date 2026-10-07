# MQT Bench evaluation archive

This area preserves the 90-circuit comparison and its later retrieval analyses. `llm_rag.py`, `llm_senza_rag.py`, `casuale.py` and `mqt_predictor.py` are method entry points. `piano.json` defines the evaluation plan. `strumenti/` implements execution; `verifiche/` contains software tests.

`recupero_random/` stores the five-random-example variant. `numero_esempi/` compares k=1,5,10. `dag_wl_retrieval/`, `dag_wl_sintesi/` and `confronto_manhattan_wl/` contain structural-retrieval extensions. `report/` contains generators; `report_generati/` contains versioned outputs.

The evaluated MQT records are in the separate reduced-Training-set campaign, with its own contract. Later Test-set analyses do not retrospectively replace the main validation-selected configuration. See the current scientific protocol for interpretation and the toolkit for new runs.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [confronto_manhattan_wl/](confronto_manhattan_wl/README.md) | Manhattan, WL and WL-summary comparison. |
| [dag_wl_retrieval/](dag_wl_retrieval/README.md) | DAG/WL retrieval campaign. |
| [dag_wl_sintesi/](dag_wl_sintesi/README.md) | DAG/WL retrieval with prompt summaries. |
| [numero_esempi/](numero_esempi/README.md) | Number of retrieved examples. |
| [recupero_random/](recupero_random/README.md) | LLM with five random train examples. |
| [report/](report/README.md) | Test report generators. |
| [report_generati/](report_generati/README.md) | Generated Test reports. |
| [strumenti/](strumenti/README.md) | Historical evaluation utilities. |
| [verifiche/](verifiche/README.md) | Evaluation software checks. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

# External QASMBench comparison

This directory contains the completed comparison of LLM + RAG and MQT Predictor on 50 selected original QASMBench circuits: 30 small, 15 medium and five large. The source revision is `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`. The selected system was applied without new training; the comparison is evidence of transfer to this distinct collection.

`circuiti/`, `manifest.json` and `selezione.csv` identify inputs. `llm_rag.py` and `mqt_predictor.py` launch methods; `prepara.py` checks preparation; `piano.json` and `selettore_mqt.json` identify conditions. `strumenti/` implements execution; `verifiche/` holds checks; `report/` contains analysis.

The September 30 comparison has 50 QAdviser successes and 48 MQT successes. MQT uses the separately documented 384-sample selector; quality comparisons use common successful circuits. Earlier preparation records remain historical and do not imply that the Test is still unrun.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [report/](report/README.md) | QASMBench reports. |
| [strumenti/](strumenti/README.md) | QASMBench execution utilities. |
| [verifiche/](verifiche/README.md) | QASMBench development checks. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

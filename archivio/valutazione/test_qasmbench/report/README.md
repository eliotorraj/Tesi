# QASMBench reports

`confronto_llm_rag_mqt/` contains the September 30 comparison's PDF/LaTeX, data, figures and regeneration code. The parent `analizza.py` reads only this campaign and writes a new analysis directory; it does not call models or compile circuits.

The comparison uses the reduced-coverage MQT selector, with 384/396 training samples and adaptive 100/300-second collection. QASMBench outcomes are new measurements for that collection, not reused MQT Bench results. Compare score quality on common successes and report coverage separately.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [confronto_llm_rag_mqt/](confronto_llm_rag_mqt/README.md) | QAdviser and MQT on QASMBench. |

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

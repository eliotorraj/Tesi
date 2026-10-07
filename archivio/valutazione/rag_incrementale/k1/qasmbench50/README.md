# QASMBench k=1 campaign

This campaign uses the 50 selected external circuits: 30 small, 15 medium and five large, with 396 initial train examples. `rag_fisso/` holds a new fixed-memory control; `ordinamenti/` holds four independent sequences; `piano.json` fixes settings; `report/` analyzes outcomes. Local test modules cover procedure and reporting.

The parent launcher is `avvia_qasmbench50.py`, with default identifier `qasmbench50_rag_k1_v1`. No prior MQT Bench or QASMBench outcomes enter memory. The oracle is read only by the report.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [report/](report/README.md) | QASMBench k=1 reports. |

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

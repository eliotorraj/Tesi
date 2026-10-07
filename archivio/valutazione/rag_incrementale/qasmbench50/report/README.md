# QASMBench incremental-memory reports

`genera.py` reads the four local campaigns and fixed historical control; `oracoli.py` verifies the oracle. It does not call the model, compile circuits or update memory.

Reports show mean and per-circuit signed oracle gaps with common scales across orders. Each order has two 25-circuit detail pages. Global comparisons use common successes; pairwise comparisons declare their intersections. Missing results and partial references are visible rather than converted into zero scores.

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

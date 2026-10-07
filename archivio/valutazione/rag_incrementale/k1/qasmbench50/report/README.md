# QASMBench k=1 reports

`genera.py` compares the new fixed k=1 control and four incremental k=1 orders; `oracoli.py` verifies the external reference. Use the parent `report_qasmbench50.py` launcher.

The report retains explicit common-success and pairwise denominators, signed oracle gaps, valid zero scores, missing values and partial references. It does not reuse k=5 scores as the fixed control. No inference, compilation or memory update is performed by the report generator.

[Parent directory](../README.md) · [Current repository guide](../../../../../../README.md)

# External QASMBench selection

This reference collection contains 50 OpenQASM 2 circuits: 30 in `small/`, 15 in `medium/` and 5 in `large/`. It is a selection from [PNNL QASMBench](https://github.com/pnnl/QASMBench), not a full clone. `manifest.json` and `selezione.csv` record sources and selection; `LICENSE` and `NOTICE` preserve attribution.

For a new experiment, copy chosen inputs into your own `train/`, `validation/` and `test/` directories and configure that corpus before preparation. Use unique names and avoid overlap. Follow the [toolkit guide](../../../documentazione/guida.md).

Keep this reference collection and manifest intact. Size labels guarantee neither Target compatibility nor feasibility with 16 GB RAM. An external Test evaluates a fixed configuration; its outcomes must not select that configuration retrospectively.

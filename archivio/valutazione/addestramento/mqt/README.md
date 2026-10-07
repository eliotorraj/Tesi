# Archived MQT selector training

`addestra.py` is the entry point; `motore_ml.py` manages workers, compilation records and Random Forest training. `deduplica.py` selects unique train inputs, `validazione_selettore.py` checks artifacts and `sincronizza.py` handles recorded synchronization. `verifiche/` contains software checks; `SVILUPPO.md` records development.

The original 422 train files contain 396 distinct QASM contents and 1,878 compatible circuit/device pairs. Later comparison records use 384 training samples, with 12 excluded and 1,853 successful compilations collected under 100/300-second limits. These conditions differ from a complete Training set. New training uses the toolkit's `mqt/` directory.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

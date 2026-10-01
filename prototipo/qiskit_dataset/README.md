# Catalogo usato dal prototipo

Nonostante il nome ereditato dal progetto sperimentale, questa cartella contiene utility necessarie all'esecuzione: `catalog.py` carica configurazioni e dispositivi e ne controlla la coerenza; `experiment_v2.py` fornisce funzioni di serializzazione e impronta.

Non genera nuove compilazioni per il Dataset e non apre gli esperimenti. Legge il catalogo in `configs/`; i dettagli sono in [architettura e flusso](../docs/architettura_e_flusso.md).

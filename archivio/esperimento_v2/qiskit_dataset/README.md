# Costruzione e valutazione del Dataset Qiskit

Questo pacchetto contiene la logica che prepara i circuiti, esegue le
compilazioni Qiskit e trasforma i risultati in esempi utilizzabili dal RAG.
Contiene anche i controlli per confrontare i metodi previsti dal protocollo.

Non si avvia direttamente. I comandi in [scripts/](../scripts/README.md)
richiamano le sue funzioni.

## Il percorso dei dati

```text
circuiti e split congelati
  → piano delle compilazioni per dispositivo, configurazione e seed
  → tentativi salvati, compresi errori e timeout
  → riepiloghi delle ripetizioni
  → confronto delle configurazioni e dei dispositivi
  → esempi RAG ricavati dal solo train
```

Il Dataset Qiskit fornisce precedenti al modello linguistico. Il Training set
del selettore supervisionato MQT segue invece le compilazioni RL gestite da
`scripts/04_train_device_selector.py`.

## File

| File | Responsabilità |
| --- | --- |
| [__init__.py](__init__.py) | Espone le parti pubbliche del pacchetto. |
| [catalog.py](catalog.py) | Legge e controlla l'elenco delle configurazioni Qiskit ammesse. |
| [core.py](core.py) | Prepara circuiti, caratteristiche, manifest, split e identificativi stabili dei tentativi. Raccoglie le funzioni comuni di lettura e salvataggio. |
| [generation.py](generation.py) | Esegue le compilazioni, impone i limiti di tempo, verifica i circuiti prodotti e salva risultati e diagnostica per la ripresa. |
| [views.py](views.py) | Riunisce i seed, calcola le statistiche delle configurazioni e costruisce gli esempi con etichette ed evidenze. |
| [aggregation.py](aggregation.py) | Unisce le viste dei dispositivi, controllando identità dei circuiti e collegamenti con i risultati originali. |
| [reporting.py](reporting.py) | Produce riepiloghi leggibili e tabelle CSV su successi, errori, timeout, qualità e tempi. |
| [experiment_v2.py](experiment_v2.py) | Costruisce e verifica i piani del confronto, le decisioni LLM, le esecuzioni MQT e la matrice Qiskit. Calcola i risultati comuni dopo la chiusura delle scelte. |

## Ingressi e risultati

- [configs/](../configs/README.md): configurazioni ammesse e parametri del protocollo.
- [datasets/](../datasets/README.md): circuiti, manifest, tentativi e viste del Dataset.
- [artifacts/](../artifacts/README.md): piani, decisioni e risultati del confronto.
- [tests/](../tests/README.md): controlli della costruzione, dell'aggregazione e dei resoconti.

I dettagli scientifici e i criteri di confronto sono nel
[protocollo sperimentale](../docs/protocollo_sperimentale.md).
Le cartelle `__pycache__/`, quando presenti, contengono file temporanei di Python.

[Torna alla guida del progetto](../README.md).

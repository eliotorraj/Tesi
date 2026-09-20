# Comandi del progetto

Questa cartella contiene i comandi da eseguire dalla radice del progetto.
Servono a preparare l'ambiente, addestrare MQT Predictor, costruire il Dataset
Qiskit e svolgere il confronto sperimentale.

Le regole e l'ordine delle fasi sono nel
[protocollo sperimentale](../docs/protocollo_sperimentale.md). La numerazione
conserva la storia del progetto: i prefissi `07` e `08` compaiono due volte.
Non bisogna eseguire tutti i file in ordine senza considerare la fase corrente.

## Come si usano

In Ubuntu/WSL, dalla radice del progetto:

```bash
.venv/bin/python scripts/01_check_install.py
.venv/bin/python scripts/16_run_pipeline_v2.py --help
.venv/bin/python scripts/17_rag_v2.py --help
```

Ogni comando Python operativo offre `--help`. Per le operazioni lunghe,
`16_run_pipeline_v2.py` raccoglie i parametri previsti dal protocollo e richiama
gli altri comandi. Gli esiti sono conservati in `artifacts/experiments/` e
`datasets/experiments/`, secondo il tipo di risultato.

## Ambiente e modelli MQT

| File | A cosa serve |
| --- | --- |
| [bootstrap_ubuntu.sh](bootstrap_ubuntu.sh) | Installa o usa `uv`, prepara Python 3.12 e l'ambiente con le versioni di `uv.lock`, poi controlla l'installazione. È destinato a Ubuntu/WSL. |
| [01_check_install.py](01_check_install.py) | Controlla versioni, protocollo congelato e, nelle modalità previste, disponibilità e validità dei modelli. |
| [02_list_devices.py](02_list_devices.py) | Mostra i dispositivi disponibili tramite MQT Bench e le loro caratteristiche. |
| [03_train_rl_model.py](03_train_rl_model.py) | Addestra o riprende il compilatore RL di un dispositivo. Conserva salvataggi e metadati dell'addestramento. |
| [04_train_device_selector.py](04_train_device_selector.py) | Compila i circuiti con i compilatori RL, conserva ogni tentativo e costruisce il Training set del selettore supervisionato. Può poi addestrare e installare il selettore. |
| [05_sync_models.py](05_sync_models.py) | Verifica e sincronizza i modelli conservati nel progetto con le copie usate dal pacchetto Python installato. |
| [07_validate_qcompile.py](07_validate_qcompile.py) | Esegue piccole prove dei compilatori RL e del percorso completo `qcompile`. Richiede modelli già pronti. |
| [08_audit_rl_models.py](08_audit_rl_models.py) | Raccoglie prove sullo stato dei modelli e delle compilazioni per decidere se continuare un addestramento o rifarlo. |

Le copie canoniche dei modelli sono negli artefatti dell'esperimento.
L'installazione delle dipendenze, da sola, non rende pronto `qcompile`.

## Corpus e Dataset Qiskit

| File | A cosa serve |
| --- | --- |
| [06_prepare_experiment_v2.py](06_prepare_experiment_v2.py) | Verifica il corpus congelato e prepara le copie train e validation della v2. Mantiene separato il test. |
| [07_prepare_qiskit_dataset.py](07_prepare_qiskit_dataset.py) | Prepara manifest, suddivisioni e piano dei tentativi del Dataset Qiskit. |
| [08_generate_qiskit_dataset.py](08_generate_qiskit_dataset.py) | Compila con le configurazioni Qiskit ammesse. Registra successi, errori e timeout e riprende il lavoro dai risultati salvati. |
| [09_build_qiskit_dataset_views.py](09_build_qiskit_dataset_views.py) | Riunisce le ripetizioni, calcola i riepiloghi e produce le viste e i resoconti per un dispositivo. Gli esempi per il RAG provengono dal train. |
| [10_aggregate_qiskit_dataset.py](10_aggregate_qiskit_dataset.py) | Unisce le viste dei dispositivi in un Dataset generale e prepara gli esempi RAG con dispositivo vincente, configurazioni ed evidenze. |

Il **Dataset** fornisce esempi al modello linguistico. Il **Training set** del
selettore MQT deriva invece dalle compilazioni RL del comando `04`.
La distinzione evita di confondere le due forme di apprendimento.

## Confronto sperimentale e accesso al test

| File | A cosa serve |
| --- | --- |
| [11_freeze_method_plan_v2.py](11_freeze_method_plan_v2.py) | Congela metodi, configurazioni e scelte casuali prima di consultare i punteggi da valutare. |
| [12_run_qcompile_v2.py](12_run_qcompile_v2.py) | Esegue le tre ripetizioni previste di `qcompile` per circuito, con tempo massimo e ripresa. |
| [13_import_llm_decisions_v2.py](13_import_llm_decisions_v2.py) | Controlla e sigilla le decisioni finali degli LLM senza leggere i punteggi di valutazione. |
| [14_evaluate_methods_v2.py](14_evaluate_methods_v2.py) | Confronta i metodi sullo stesso split dopo la chiusura delle decisioni e produce i risultati. |
| [15_release_test_v2.py](15_release_test_v2.py) | Verifica i prerequisiti del protocollo e consente l'apertura del test quando sono soddisfatti. |
| [16_run_pipeline_v2.py](16_run_pipeline_v2.py) | Coordina preparazione, addestramento RL, selettore MQT e Dataset Qiskit. Non introduce un secondo protocollo: richiama i comandi precedenti. |

La selezione sperimentale degli LLM ha i propri comandi in
[llm_selection/](../llm_selection/README.md).

## Recupero degli esempi e consultazione

| File | A cosa serve |
| --- | --- |
| [17_rag_v2.py](17_rag_v2.py) | Prepara e verifica l'indice Qdrant, cerca esempi e controlla il recupero sulla validation. Non chiama un LLM e non compila circuiti. |
| [18_qdrant_dashboard.py](18_qdrant_dashboard.py) | Copia e verifica gli esempi in un server Qdrant locale per consultarli nella dashboard. |

La [guida alla dashboard](../prototype/qdrant_dashboard/README.md) spiega
l'avvio. Le prove del recupero verificano che gli esempi siano corretti e
riproducibili; non misurano la qualità delle decisioni dell'LLM.

## Moduli di supporto

| File | A cosa serve |
| --- | --- |
| [mqt_predictor_protocol.py](mqt_predictor_protocol.py) | Centralizza le regole congelate, le impronte di circuiti e dispositivi e i controlli su split, versioni e apertura del test. |
| [mqt_model_artifacts.py](mqt_model_artifacts.py) | Controlla struttura e provenienza dei modelli RL e del selettore MQT. È usato dai comandi di verifica e sincronizzazione. |

Questi due file sono librerie condivise dagli altri comandi. Le cartelle
`__pycache__/`, quando presenti, contengono copie temporanee generate da Python.

[Torna alla guida del progetto](../README.md).

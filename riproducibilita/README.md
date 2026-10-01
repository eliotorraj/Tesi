# Riprodurre l'esperimento e costruire un nuovo prototipo

Questa è l'area operativa per ripartire dai circuiti e generare nuovi dati, modelli MQT, decisioni LLM e risultati. Tutti gli ingressi e i sorgenti necessari sono qui: i comandi non leggono `archivio/` né `prototipo/`. I pesi LLM e i modelli MQT addestrati non sono inclusi. Circuiti originali, versioni Python e schemi sono distribuiti.

Per cominciare leggere la [guida dall'inizio alla fine](documentazione/guida.md). Per distinguere una nuova esecuzione dagli esiti storici leggere [condizioni e riproducibilità](documentazione/condizioni.md).

| Cartella | Che cosa permette di fare |
| --- | --- |
| [mqt/](mqt/README.md) | Mostrare i Target, addestrare RL, generare il Training set e addestrare il selettore. |
| [circuiti/](circuiti/README.md) | Sostituire train, validation e test; contiene i 600 QASM originali e, separatamente, 50 QASMBench. |
| [dataset/](dataset/README.md) | Compilare sulla griglia Qiskit, aggregare gli score e costruire il Dataset RAG dal solo train. |
| [modelli_llm/](modelli_llm/README.md) | Inserire i propri GGUF e dichiarare identità, provenienza e parametri dei candidati. |
| [validation/](validation/README.md) | Scegliere modello e temperatura; valutare anche le profondità WL. |
| [test/](test/README.md) | Misurare i sistemi selezionati, conservare fallimenti e generare confronti. |
| [configurazioni/](configurazioni/README.md) | Scegliere ingressi, dispositivi, configurazioni, seed, griglie e metodi. |
| [comune/](comune/README.md) | Framework riutilizzabile, integrità, processi, resoconti ed esportazione. |
| [verifiche/](verifiche/README.md) | Collaudare il software con piccoli circuiti e un server LLM simulato. |
| [documentazione/](documentazione/README.md) | Sequenza operativa, condizioni e mappa delle dipendenze. |

`esperimento.py --help` mostra i comandi. `setup.sh`, `pyproject.toml`, `uv.lock` e `.python-version` preparano un ambiente dedicato. Gli output sono separati per `experiment_id`: in `esecuzioni/`, `mqt/artefatti/`, `dataset/artefatti/`, `validation/risultati/` e `test/risultati/`. I segnaposto sono versionati; i dati prodotti restano locali e vanno conservati separatamente.

**Dataset** indica gli esempi per RAG/LLM. **Training set** indica i dati circuito/dispositivo per il selettore MQT. Il progetto implementa il RAG; questa area non introduce il fine-tuning dell'LLM.

`esporta` crea un altro prototipo autonomo usando il train e il modello selezionato. La cartella `prototipo/` esistente mantiene i suoi contenuti.

I sorgenti storici restano come fotografie degli esperimenti precedenti. [provenienza_sorgenti.json](provenienza_sorgenti.json) elenca origini e impronte prima dell'adattamento. Sono riferimenti di provenienza, non dipendenze a runtime.

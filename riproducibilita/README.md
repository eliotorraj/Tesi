# Ricreare l'esperimento o costruire un nuovo prototipo

Questa è l'area operativa Linux per nuove esecuzioni: si scelgono circuiti e modelli, si generano dati, si selezionano le impostazioni sulla validation e si valutano sul Test. Gli strumenti non importano codice da `prototipo/` o `archivio/`. Pesi LLM e modelli MQT addestrati non sono inclusi.

Per **provare subito il prototipo selezionato**, anche su un PC Linux senza GPU, partire dalla [guida del prototipo](../prototipo/docs/guida_passo_passo.md). Per **rifare le fasi o scegliere altri modelli**, seguire la [guida di questa area](documentazione/guida.md). Sono obiettivi diversi: i 16 GB indicativi per la prova CPU non garantiscono le risorse per tutta la campagna.

Una GPU compatibile è consigliata per l'inferenza. Il kit usa un eseguibile llama.cpp Linux configurabile, senza dipendere dalla Radeon del fisso. Il fisso può continuare a usare il proprio server Windows da WSL con trasporto esplicito. Le differenze di hardware e contesto vanno dichiarate prima delle prove.

| Cartella | Funzione |
| --- | --- |
| [circuiti/](circuiti/README.md) | Ingressi train, validation e test sostituibili; 600 QASM distribuiti e 50 QASMBench separati. |
| [mqt/](mqt/README.md) | Target quantistici, politiche RL, Training set e selettore supervisionato. |
| [dataset/](dataset/README.md) | Griglia Qiskit, schemi, aggregati e Dataset RAG del solo train. |
| [modelli_llm/](modelli_llm/README.md) | Registro, cartelle per GGUF e avvio server CPU/GPU. |
| [validation/](validation/README.md) | Scelta di modello, temperatura e profondità WL. |
| [test/](test/README.md) | Metodi fissati, esiti e confronti. |
| [configurazioni/](configurazioni/README.md) | Identità, percorsi, dispositivi, parametri, seed e metodi. |
| [comune/](comune/README.md) | Integrità, processi, framework, report ed esportazione. |
| [verifiche/](verifiche/README.md) | Collaudi software con piccoli circuiti e server simulato. |
| [documentazione/](documentazione/README.md) | Sequenza operativa, condizioni e mappa dei moduli. |
| [esecuzioni/](esecuzioni/README.md) | Ingressi congelati, contratti e registri per identificativo. |
| [esportazioni/](esportazioni/README.md) | Nuovi prototipi autonomi, generati su richiesta. |

`setup.sh`, `pyproject.toml`, `uv.lock` e `.python-version` preparano l'ambiente dedicato. `esperimento.py --help` elenca le fasi. Tutti i risultati sono separati per `experiment_id`; i segnaposto sono nel clone, mentre pesi, ambienti e dati generati devono essere conservati separatamente da Git.

**Dataset** significa esempi per RAG/LLM. **Training set** significa dati circuito/dispositivo per MQT. Non è implementato il fine-tuning degli LLM. `esporta` costruisce un altro prototipo con train e configurazione selezionata, senza sovrascrivere quello distribuito.

[provenienza_sorgenti.json](provenienza_sorgenti.json) identifica le origini dei componenti. Non introduce dipendenze operative dall'archivio. Per limiti e condizioni scientifiche leggere [condizioni](documentazione/condizioni.md).

# Ricreare l'esperimento o costruire un nuovo prototipo

Questa è l'area operativa Linux per nuove esecuzioni: si scelgono circuiti e modelli, si generano dati, si selezionano le impostazioni sulla validation e si valutano sul Test. Gli strumenti non importano codice da `prototipo/` o `archivio/`. Pesi LLM e modelli MQT addestrati non sono inclusi.

Per **provare subito il prototipo selezionato**, anche su un PC Linux senza GPU, partire dalla [guida del prototipo](../prototipo/docs/guida_passo_passo.md). Per **rifare le fasi o scegliere altri modelli**, seguire la [guida di questa area](documentazione/guida.md). Sono obiettivi diversi: i 16 GB indicativi per la prova CPU non garantiscono le risorse per tutta la campagna.

Per configurare senza modificare JSON, da questa cartella e dopo il setup:

```bash
source .venv/bin/activate
python configura.py nuovo prova-cpu --profilo cpu
python configura.py mostra prova-cpu
python configura.py disponibili sistemi
```

`configura.py` permette di scegliere circuiti, LLM, sistemi Test, Target, opzioni Qiskit e risorse. `nuovo` parte da Qwen e tre sistemi senza MQT; tutti i Target e le configurazioni restano disponibili finché non li riduci. Prima di eseguire una campagna completa segui la [guida](documentazione/guida.md); per una modifica specifica consulta il [ricettario dei comandi](documentazione/configurazione.md). `esperimento.py --esperimento NOME stato` aiuta a ritrovare il punto raggiunto.

I nomi `nuovo`, `mostra`, `prepara` e `dataset` sono azioni dei rispettivi script. Per esempio, `python esperimento.py --esperimento prova-cpu prepara` controlla gli ingressi e conserva copie dei circuiti, catalogo e impostazioni della prova. È il passaggio che fissa le condizioni prima di generare il Dataset o addestrare; la guida indica quando eseguirlo e come iniziare una prova diversa.

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

`setup.sh`, `pyproject.toml`, `uv.lock` e `.python-version` preparano l'ambiente dedicato. `configura.py --help` elenca le modifiche disponibili; `esperimento.py --help` elenca le fasi. Le configurazioni nominate sono in `configurazioni/esperimenti/`; dopo la preparazione si duplicano per iniziare una prova diversa. Tutti i risultati sono separati per `experiment_id`; i segnaposto sono nel clone, mentre pesi, ambienti e dati generati devono essere conservati separatamente da Git.

**Dataset** significa esempi per RAG/LLM. **Training set** significa dati circuito/dispositivo per MQT. Non è implementato il fine-tuning degli LLM. `esporta` costruisce un altro prototipo con train e configurazione selezionata, senza sovrascrivere quello distribuito.

[provenienza_sorgenti.json](provenienza_sorgenti.json) identifica le origini dei componenti. Non introduce dipendenze operative dall'archivio. Per limiti e condizioni scientifiche leggere [condizioni](documentazione/condizioni.md).

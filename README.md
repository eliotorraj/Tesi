# Tesi — LLM e compilazione quantistica

Il progetto studia la scelta di dispositivo e configurazione per compilare circuiti quantistici, usando un LLM e gli esempi recuperati dal train. La repository separa l'uso del framework, la riproduzione e la storia degli esperimenti.

| Cartella | Da usare per |
| --- | --- |
| [prototipo/](prototipo/README.md) | Usare il framework selezionato, con i dati train distribuiti e Qwen3.5-4B Q8_0 a temperatura 0. |
| [riproducibilita/](riproducibilita/README.md) | Ripartire dai circuiti, addestrare MQT, generare il Dataset, scegliere altri LLM, fare validation/Test ed esportare un nuovo prototipo. |
| [archivio/](archivio/README.md) | Consultare sviluppo, decisioni, riorganizzazioni, sorgenti congelati ed evidenze degli esperimenti precedenti. |

Per usare l'assistente partire dalla [guida del prototipo](prototipo/docs/guida_passo_passo.md). Per rifare il percorso sperimentale partire dalla [guida alla riproduzione](riproducibilita/documentazione/guida.md). Il [protocollo corrente](prototipo/docs/protocollo_sperimentale.md) resta il riferimento scientifico; la nuova guida dichiara condizioni e differenze operative dei nuovi avviatori.

`prototipo/` e `riproducibilita/` funzionano senza leggere l'archivio. Il kit include sorgenti, schemi, lock e ingressi, ma non GGUF o modelli già addestrati. Ambienti, pesi e nuove esecuzioni richiedono un backup separato. **Dataset** indica gli esempi RAG/LLM; **Training set** indica i dati del selettore MQT.

I sorgenti della tesi, se presenti in `tesi/`, e l'indice locale `graphify-out/` sono strumenti di lavoro separati, esclusi da Git. I README spiegano dove cercare ogni funzione.

La [riorganizzazione del 1 ottobre](archivio/riorganizzazione_2026_10_01/README.md) documenta la separazione. Copie congelate di sorgenti e corpus restano nell'archivio per preservare manifest, hash e provenienza degli esiti storici.

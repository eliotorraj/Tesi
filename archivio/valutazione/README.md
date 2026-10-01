# Validation, Test e sviluppo sperimentale

> Area storica. Per nuove esecuzioni usare [riproducibilita/](../../riproducibilita/README.md). Le istruzioni seguenti restano associate alle campagne e agli artefatti conservati qui.


Questa area raccoglie gli strumenti e gli artefatti che servono a valutare o correggere il framework. L'uso ordinario del prototipo non dipende da questa cartella.

| Cartella | Contenuto |
| --- | --- |
| [test/](test/README.md) | Quattro metodi del confronto, controlli, risultati, analisi e documenti. |
| [test_qasmbench/](test_qasmbench/README.md) | Nuovo confronto LLM + RAG e MQT su 50 circuiti QASMBench (30 piccoli, 15 medi, 5 grandi); esecuzione separata. |
| [test_mqt_esplorativo/](test_mqt_esplorativo/README.md) | Prova MQT separata, con la propria configurazione e i propri esiti. |
| [addestramento/](addestramento/README.md) | Preparazione e verifica dei modelli MQT del confronto. |
| [verifiche_prototipo/](verifiche_prototipo/README.md) | Prove offline di sviluppo: caratteristiche train, recupero, risposte sintetiche e compilazione Bell. |
| [prove_prototipo/](prove_prototipo/README.md) | Registri del prototipo precedenti al riordino del 25 settembre. |
| [documentazione_storica/](documentazione_storica/README.md) | Comandi e resoconti legati alla preparazione del 20–21 settembre. |

La validation local-llm-v2 e le sue fonti restano nell'[esperimento v2](../esperimento_v2/README.md), con la struttura congelata. Non ne vengono riscritti i manifest o i riferimenti logici.

Al 25 settembre sono presenti 90 esiti per ciascuno dei metodi LLM+RAG, LLM senza RAG e Random. Non è presente un'esecuzione MQT ufficiale; la prova MQT esplorativa ha 90 esiti separati. Il conteggio degli esiti non è un conteggio dei successi. Lo stato e le regole sono nel [protocollo corrente](../../prototipo/docs/protocollo_sperimentale.md).

I programmi correnti utilizzano i moduli in `prototipo/` e le fonti congelate. La riorganizzazione conserva i file originali, ma modifica i percorsi e il codice degli avviatori: i contratti già congelati non devono essere riscritti per forzare una ripresa. I risultati esistenti restano analizzabili separatamente.

I dati voluminosi e i modelli esclusi da Git restano su disco e richiedono un trasferimento separato. Il [resoconto del riordino](../riorganizzazione_2026_09_25/README.md) documenta inventario e verifiche.

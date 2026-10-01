# Dati train necessari al RAG

Il clone contiene 396 esempi train unici, i QASM corrispondenti, la trasformazione numerica e il manifest delle 422 sorgenti train, inclusi gli alias. `rag_examples.jsonl` fornisce gli esempi; `transform.json` fissa la scala ricavata solo dal train; `catalog_original.json` conserva il catalogo di provenienza. I sigilli permettono di riconoscere dati alterati.

Il prototipo costruisce l'indice Qdrant locale sotto `runtime/rag/` durante `app.py prepare` o il setup. Validation e Test non vengono letti per decidere sul circuito nuovo. Il file `pstools_verified.json` serve esclusivamente al runtime Windows del fisso.

Questi dati sono ingressi già selezionati. Per sostituire corpus, rigenerare Dataset e scegliere un altro modello partire da [riproducibilita/](../../riproducibilita/README.md). Non aggiornare un hash soltanto per far accettare file diversi.

# Strutture e operazioni del framework

`models.py` definisce richieste, Target, esempi, raccomandazioni e artefatti di compilazione. `ports.py` descrive le interfacce delle operazioni. `adapters/` contiene le implementazioni concrete. `schema_validation.py` controlla il sottoinsieme JSON Schema impiegato dai contratti distribuiti.

L'esecuzione pubblica passa da `app.py` e usa RAG train, prompt TOON e facts v4. Le ulteriori interfacce Python non costituiscono comandi di avvio separati: partire dalla [mappa tecnica](../../docs/architettura_e_flusso.md) per capire quali vengono effettivamente chiamate.

Questi moduli non avviano un addestramento MQT e non aprono il Test scientifico. Per nuove campagne usare [riproducibilita/](../../../riproducibilita/README.md).

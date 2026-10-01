# Preparazione dei modelli di confronto

Questa cartella raccoglie gli strumenti sperimentali per addestrare i modelli
usati come termine di confronto. Non serve per avviare il framework Qwen.

[mqt/](mqt/README.md) contiene il selettore supervisionato MQT: selezione dei
circuiti train distinti, compilazioni con i modelli RL, costruzione del
Training set, addestramento e controlli. Conserva anche importazioni dal
portatile, prove, errori e artefatti necessari a ricostruire il lavoro.

Le fonti e i modelli RL congelati restano in `archivio/esperimento_v2/`.
Il [protocollo corrente](../../../prototipo/docs/protocollo_sperimentale.md)
distingue la procedura conforme dalla prova esplorativa con copertura ridotta.

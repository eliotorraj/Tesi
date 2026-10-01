# Separazione della riproduzione — 1 ottobre 2026

`riproducibilita/` è la nuova area operativa. Include circuiti train/validation/test, MQT, generazione Dataset, registro dei GGUF senza pesi, validation, Test, configurazioni, guide e verifica software. Le nuove esecuzioni hanno identificativi e output propri; l’esportazione produce un altro prototipo autonomo.

Il prototipo locale è rimasto invariato: le impronte dei suoi file sono state confrontate prima e dopo il lavoro. Sorgenti congelati, manifest e artefatti precedenti restano nell’archivio, come evidenza del codice usato nelle campagne passate. I moduli riutilizzabili sono copiati e adattati nel kit; nessun comando del kit richiede l’archivio o il prototipo esistente.

Le verifiche sono in [verifiche.json](verifiche.json). Il collaudo isolato comprende 18 compilazioni Qiskit per un piccolo Dataset, due candidati LLM simulati, selezione, sei varianti Test, oracle separato, ripresa senza duplicazioni, rifiuto di sovrapposizioni e modifiche al contratto, report LaTeX compilati e uso del prototipo esportato. Sono controlli software, non nuove misure scientifiche sugli LLM reali. Non sono stati addestrati RL né eseguite le campagne complete.

Sono stati verificati anche i 600 circuiti distribuiti, i cinque Target, le versioni fissate e gli avviatori MQT. Tutti i collaudi precedenti, inclusi quelli falliti durante lo sviluppo, restano in `collaudi/` nella copia locale. I dati prodotti e i vecchi pesi non sono inclusi nella pubblicazione del kit.

Il collegamento `.git` locale puntava a una cartella madre non più presente. È stato conservato e sostituito con metadati recuperati da GitHub, mantenendo tutti i file della cartella di lavoro. Il ramo di partenza recuperato è `riorganizzazione-prototipo`, commit `cb1532be23d7e28c2facf521011e657842216b79`; il lavoro prosegue sul ramo `riproducibilita-esperimenti`. Il recupero dei metadati remoti non ricostruisce eventuali commit locali non pubblicati della cartella madre mancante.

Le modifiche locali al prototipo e lo spostamento delle vecchie prove in `archivio/valutazione/` preesistenti a questa attività sono mantenuti. I file congelati mancanti nella copia locale non vengono cancellati dal remoto durante la pubblicazione di questa separazione.

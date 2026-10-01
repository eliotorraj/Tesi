# Nuovi prototipi autonomi

`esperimento.py esporta` crea una directory nuova con framework, Dataset train, catalogo e configurazione selezionata sulla validation. Non include i pesi GGUF né gli score validation/Test e non sovrascrive il prototipo distribuito.

Da `riproducibilita/`, dopo la selezione, usare `.venv/bin/python -B esperimento.py esporta esportazioni/mio-prototipo`. È ammessa anche una destinazione esterna nuova. L'output contiene istruzioni di preparazione Linux e il registro del modello; hardware e contesto devono permetterne l'avvio. Gli output di questa cartella restano esclusi da Git: conservarli o versionarli in una destinazione dedicata.

# Dataset per il RAG

`genera.py` pianifica i tentativi su train e validation. `qiskit_dataset/` conserva catalogo, compilazione, aggregazione e costruzione degli esempi. `schemi/` contiene i contratti JSON; `artefatti/<id>/` i tentativi e gli aggregati.

Avvio: `esperimento.py dataset`. Gli score validation servono al valutatore; soltanto train entra nel RAG. Il pacchetto sigillato del framework è in `esecuzioni/<id>/data/`. Questa generazione è distinta dal Training set del selettore MQT.

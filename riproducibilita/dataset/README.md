# Generazione del Dataset per il RAG

`genera.py` pianifica la griglia su train e validation. `qiskit_dataset/` contiene catalogo, compilazione, aggregazione e costruzione degli esempi. `schemi/` conserva i contratti JSON. I tentativi e gli aggregati finiscono in `artefatti/<id>/`.

Dopo setup e `prepara`, da `riproducibilita/` eseguire `.venv/bin/python -B esperimento.py dataset`. La procedura conserva successi, errori e timeout. Le mediane eleggibili richiedono i tre seed riusciti. Soltanto train entra negli esempi e nella trasformazione RAG; la matrice validation serve al valutatore dopo le decisioni.

Il pacchetto train sigillato è in `esecuzioni/<id>/data/`. `--split train`, `--split validation` e `--aggrega` permettono di separare le fasi. La generazione usa CPU e RAM per Qiskit, non il server Qwen. Il parallelismo va fissato prima della prova in base alla memoria. Questo Dataset è distinto dal Training set MQT.

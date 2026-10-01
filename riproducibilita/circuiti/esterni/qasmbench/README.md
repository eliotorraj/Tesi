# Circuiti esterni QASMBench

Questa cartella contiene la selezione di 50 OpenQASM 2 distribuita con il progetto: 30 in `small/`, 15 in `medium/` e 5 in `large/`. Non è un clone completo di QASMBench. `manifest.json` e `selezione.csv` descrivono gli ingressi e la provenienza; `LICENSE` e `NOTICE` conservano licenza e attribuzioni. La fonte è il progetto [PNNL QASMBench](https://github.com/pnnl/QASMBench).

Per usarli scegliere i file, copiarli in una propria radice con `train/`, `validation/` e `test/` e indicare quella radice nel campo `corpus`. Mettere i QASM direttamente dentro gli split, con nomi univoci e senza sovrapposizioni. La preparazione esegue i controlli della [guida](../../../documentazione/guida.md).

Conservare questa copia di riferimento e il suo manifest. Un circuito più largo può aumentare costi e incompatibilità con i Target; le categorie small/medium/large non garantiscono che la pipeline LLM sia eseguibile con 16 GB di RAM. Non utilizzare risultati di un Test esterno per scegliere retroattivamente la configurazione valutata.

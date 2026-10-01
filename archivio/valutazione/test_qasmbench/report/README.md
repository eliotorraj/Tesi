# Report del confronto QASMBench

Questa cartella ospita le analisi richieste dopo le esecuzioni.
Il confronto delle esecuzioni completate il 30 settembre 2026 è in [confronto_llm_rag_mqt/](confronto_llm_rag_mqt/): documento LaTeX, PDF compilato, tabelle, grafici e procedure di rigenerazione. Le analisi precedenti restano in `generati/`.

Dalla radice del progetto:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/analizza.py
```

Il comando legge soltanto questa campagna. Non avvia LLM, compilazioni o altri test.
Crea una nuova sottocartella in `generati/`, senza sovrascrivere analisi precedenti:
rapporto leggibile, dati JSON, tabella CSV e grafico PNG/SVG se matplotlib è disponibile.

Questo ulteriore test indipendente usa un selettore MQT addestrato su 384 dei 396 campioni train previsti, con 12 esclusi e una raccolta adattiva a 100/300 secondi. Nessun risultato precedente viene riutilizzato come esito QASMBench.

La qualità si confronta sui circuiti con successo di entrambi i metodi.
Successi, fallimenti, timeout, interruzioni e assenze conservano denominatori separati.
Le tabelle distinguono piccoli, medi e grandi. Un confronto incompleto è dichiarato.
Gli intervalli descrittivi ricampionano i circuiti con coppie complete; non dimostrano
superiorità sull'intera raccolta QASMBench. Gli score mancanti non diventano zero.

La provenienza comprende impronte di esiti, manifest e generatore. Prompt, risposte,
evidenze RAG, scelte e circuiti compilati rimangono nei registri delle esecuzioni.
L'analisi non modifica il Dataset RAG né il Training set di MQT.

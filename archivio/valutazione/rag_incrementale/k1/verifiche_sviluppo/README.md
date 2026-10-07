# Verifiche tecniche del confronto k=1

Il 3 ottobre 2026 sono state eseguite 40 verifiche automatiche:
15 sulla procedura e 5 sui report, per ciascun gruppo di circuiti.
Le prove usano risposte LLM e compilazioni simulate, in cartelle temporanee.
Non avviano server e non misurano la qualità sui Test.

I controlli riguardano:

- recupero di un solo esempio e citazioni limitate a E1;
- corrispondenza del primo vicino con i recuperi storici a memoria vuota;
- assenza di nuove osservazioni nel RAG fisso;
- indipendenza delle memorie, esclusione del circuito corrente e degli esiti futuri;
- ripresa, interruzioni e riconoscimento dei registri alterati;
- conservazione degli score zero ed esclusione dei fallimenti dall'ammissione;
- uso dei nuovi score k=1 come controllo, anche quando l'oracle contiene score storici k=5;
- denominatori comuni, confronti appaiati, scarti con segno e dati mancanti.

I comandi riproducibili sono:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/mqtbench90/test_incrementale.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/mqtbench90/test_report.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/qasmbench50/test_incrementale.py
.venv/bin/python -B archivio/valutazione/rag_incrementale/k1/qasmbench50/test_report.py
```

`verifica_impaginazione.py` genera soltanto anteprime con dati inventati,
marcate come sintetiche, in `temporanei/`. Verifica entrambi i formati con
20 grafici per MQT Bench e 12 per QASMBench. Non legge score sperimentali,
non chiama il LLM e non compila circuiti quantistici. Gli avvii dei test reali
e i quattro comandi destinati all'utente non sono stati eseguiti.

`prima.json` conserva le impronte dei file originali protetti.
`derivazione.json` identifica i sorgenti riutilizzati.
`verifica_finale.json` riassume controlli, artefatti tecnici e confronto
delle impronte. Il grafo non viene aggiornato.

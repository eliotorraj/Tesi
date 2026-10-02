# Supplemento sui fatti verificabili

`analisi_fatti.pdf` è un documento separato di sei pagine. Analizza 90 decisioni
finali per ciascuno dei tre sistemi: LLM + RAG, LLM senza RAG e LLM + Random RAG.
Le 418 risposte controllate comprendono anche i tentativi precedenti.
Le ipotesi in prosa non sono validate sul piano dei contenuti.

Il documento mostra quattro casi illustrativi di LLM + RAG:

- due fatti sostenuti dallo stesso esempio;
- coppia storica e uguaglianza dei qubit;
- un fatto non valido per attribuzione dell'evidenza non ammessa;
- due fatti validi sostenuti da E1 ed E2, cioè due record train diversi.

Il terzo caso conserva il primo tentativo di `qpeexact_indep_qiskit_13`.
Il quarto è la risposta finale di `routing_indep_qiskit_6`.
La tabella generale include la campagna Random RAG con seme 20260927:
35/90 risposte finali interamente valide e 125/180 fatti finali validi.
I 55 fatti non validi riguardano la capacità con un riferimento Ei non consentito,
non l'insufficienza reale della capacità. I 94 fatti storici finali sono validi.
Questi conteggi non misurano la qualità della compilazione.

## Modificare e compilare il PDF

Il sorgente modificabile è `analisi_fatti.tex`. Dalla radice:

```bash
cd archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti
pdflatex -interaction=nonstopmode -halt-on-error analisi_fatti.tex
pdflatex -interaction=nonstopmode -halt-on-error analisi_fatti.tex
```

Non rieseguire il vecchio generatore `analizza_fatti.py` sul report corrente:
mantiene i due sistemi e la selezione originaria. La nuova procedura raccoglie
solo dati JSON e lascia intatto il sorgente LaTeX.

## Riprodurre i controlli

Dalla radice, scegliere un file nuovo per conservare eventuali analisi diverse:

```bash
.venv/bin/python archivio/valutazione/test/report/analizza_fatti_esteso.py \
  --output /tmp/audit_fatti_esteso.json
```

`audit_fatti_esteso.json` conserva il risultato riproducibile della procedura.
`audit_fatti.json` aggiunge la storia delle revisioni e i dettagli già conservati
del campione di fallimento. Entrambi contengono conteggi, verifiche di tutti
i tentativi, quattro campioni, esempi integrali e impronte SHA-256 delle fonti.
Le quattro regole sono riapplicate dal validatore e con confronti separati sui
campi dei record. Si verificano anche alias, vista del modello, Dataset train
e corrispondenza fra risposta finale e decisione conservata.

Non vengono avviate nuove inferenze o compilazioni quantistiche. Non vengono
modificati i registri sperimentali né il PDF di confronto originale.
`revisioni/` conserva le versioni precedenti; la revisione immediatamente
precedente è in `revisioni/due_evidenze_random_20260928T002632Z/`.
Il grafo non viene aggiornato.

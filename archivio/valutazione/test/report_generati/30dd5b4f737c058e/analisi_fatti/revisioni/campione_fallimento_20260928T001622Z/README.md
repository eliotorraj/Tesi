# Supplemento sui fatti verificabili

`analisi_fatti.pdf` è un documento separato di cinque pagine. Il PDF originale
in `../confronto/latex/verifica.pdf` non è stato modificato.

Il supplemento analizza tutte le 90 risposte finali per ciascuno dei due
metodi LLM, con i tentativi precedenti, e mostra tre casi illustrativi.
Conserva output JSON, alias e campi degli esempi train. Le ipotesi libere
non sono validate sul piano dei contenuti.

`audit_fatti.json` contiene conteggi, verifiche sui tentativi, campioni
integrali e impronte delle fonti. `analisi_fatti.tex` è autonomo.
`revisioni/` conserva la prima impaginazione e il relativo audit.

Dalla radice:

```bash
.venv/bin/python archivio/valutazione/test/report/analizza_fatti.py
cd archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti
pdflatex -interaction=nonstopmode -halt-on-error analisi_fatti.tex
```

Se cambiano fonti o codice, il generatore rifiuta di sostituire un audit
diverso: usare `--output <nuova_cartella>`. È una rianalisi dei registri,
non una nuova inferenza o una nuova compilazione quantistica.

Il sorgente è stato aperto nell'editor integrato. Il compilatore dell'app
ha restituito un errore di ambiente (directory standard non trovate).
Il PDF è stato compilato con pdflatex disponibile in WSL e controllato
visivamente sulle immagini delle pagine.

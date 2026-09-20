# Resoconto esplicativo della validation conclusa

Aggiornamento del 20 settembre 2026. Il PDF è standalone.pdf; il testo
inseribile nella tesi è validation_selection.tex. Le figure sono in figures,
in PNG e SVG. Il rapporto originale resta nella cartella vicina report.

Questa versione chiarisce le due mediane (fra seed e fra circuiti), il boxplot,
i denominatori dei fatti verificati e il conteggio delle correzioni.
Aggiunge tempi e token di ingresso/uscita per modello e per temperatura.
Le medie del regret sono descrittive: non cambiano la selezione congelata.

Per rigenerare dalla radice del progetto:

    .venv/bin/python -m scripts.report_local_validation_v2 --study local-llm-v2

La procedura verifica i sigilli prima e dopo la generazione. Non chiama
modelli e non modifica risultati, configurazioni o vincitore. Le impronte
dei dati e della procedura sono in provenance.json. model_costs.csv e
trial_details.csv conservano i nuovi riepiloghi numerici.

I tempi sono quelli delle chiamate di generazione, non dell'intera esecuzione.
I token includono tutte le correzioni e il contesto ripetuto per ogni chiamata;
non sono conteggi di parole, token unici o importi monetari.

Verifiche eseguite: totali e dati mancanti, integrità degli input e della
selezione, compilazione LaTeX senza avvisi di impaginazione, controllo visivo
delle otto pagine del PDF.

## Modificare tutte le figure della validation

Le sette figure della validation si personalizzano in `llm_selection/v2/plots.py`.
La mappa `TEMPERATURE_LABELS` controlla assi e legende. Le personalizzazioni precedenti sono conservate.
Dalla radice del progetto: `.venv/bin/python llm_selection/v2/plots.py --pdf`.
Senza `--pdf` aggiorna solo le figure. Il comando non rigenera il testo LaTeX.
La figura storica sul confronto TOON resta nella propria analisi separata.

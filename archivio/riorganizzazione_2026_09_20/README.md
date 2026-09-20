# Riordino del 20 settembre 2026

Il lavoro è stato salvato prima degli spostamenti nel commit `e9f5155c` e nel
tag `pre-riorganizzazione-2026-09-20`, pubblicati su GitHub. `main` conserva
anche il vecchio ramo principale. I nomi con `codex/` sono stati sostituiti
solo dopo aver verificato che i commit restassero raggiungibili.

## Che cosa è cambiato

La vecchia radice è raccolta in `archivio/esperimento_v2/`, senza riscrivere
manifest o risultati. `prototipo/` è la nuova dimostrazione autonoma con soli
dati train. La stesura `tesi/` e l'ambiente `.venv/` rimangono locali nella radice.

| File | Funzione |
| --- | --- |
| `spostamenti.json` | Corrispondenza fra vecchie e nuove posizioni. |
| `branch_mapping.json` | Vecchi nomi Git, sostituti e commit preservati. |
| `publication_inventory.json` | Elenco e SHA-256 dei file del salvataggio iniziale. |
| `verifica_integrita.py` | Controllo riproducibile delle impronte dello studio ufficiale. |
| `integrita_*.json` | Esiti dei controlli, compreso quello iniziale non riuscito. |
| `ripristino_grafici.json` | Provenienza del ripristino della copia congelata dei grafici. |
| `plots_post_validation.py` | Versione dei grafici modificata prima di questo intervento, conservata senza perderla. |
| `unittest_archivio*` | Prove automatiche dopo lo spostamento; non sono valutazione sul Test. |

## Integrità e limiti

Prima del riordino `llm_selection/v2/plots.py` differiva già dal congelamento.
La versione modificata è conservata qui; nel codice sperimentale è stata
ripristinata la copia esatta protetta dallo SHA-256 dello studio.
Non sono stati ricalcolati punteggi né sostituiti risultati della validation.

La prima verifica rifiutava nove file di metadati modello perché i loro
collegamenti portano al disco esterno. Il controllo successivo verifica anche
quei file con le impronte originali e dichiara le dipendenze esterne.
I pesi, alcuni grandi dati esclusi da Git, le cache e la tesi non sono inclusi
nel backup GitHub. Le copie locali restano conservate.

Il protocollo consolidato rende esplicito che il controllo di apertura del
Test usa ancora la selezione v1. Va aggiornato con un intervento sperimentale
tracciato, prima di procedere. Il riordino non autorizza l'apertura del Test.

## Revisione degli script

La [rassegna](revisione_script/README.md) distingue la verifica statica di tutti
i 147 sorgenti dalla lettura manuale ancora parziale. Sono stati riprodotti due
problemi nella gestione del processo server e nei registri di timeout degli
strumenti storici. Non si alterano i sigilli per correggerli in-place.

## Esiti verificati

- 31.305 file dello studio ufficiale corrispondono alle impronte attese.
- 266 prove automatiche dell’ambiente archiviato superate dopo lo spostamento.
- 281.592 file già versionati hanno una destinazione conservata nel nuovo albero.
- Compilazione locale della tesi ripristinata: 39 pagine, bibliografia risolta,
  controllo visivo e nessun avviso finale LaTeX/Biber. La tesi resta esclusa da Git.
- GitHub attribuisce il commit su main all’account eliotorraj; la visualizzazione
  dei contributi dipende dall’aggiornamento del servizio.

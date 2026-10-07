# Report MQT Bench: memoria incrementale e oracle

Il report usa la stessa struttura e gli stessi grafici del report QASMBench.
Legge soltanto le quattro campagne dei 90 MQT Bench, il loro controllo LLM + RAG
con Dataset fisso e il loro oracle. Non chiama LLM, non compila circuiti e non
aggiorna la memoria.

Dalla radice della repository:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/report/genera.py \
  --experiment-id mqtbench90_incrementale_v1 --pdf
```

L'uscita viene salvata in una nuova sottocartella di
`risultati/mqtbench90_incrementale_v1/`. Le versioni precedenti sono conservate.
Il riferimento predefinito è il confronto MQT Bench in
`archivio/valutazione/oracle_test/confronto_llm_rag_k5/risultati/dati.json`.
`--oracle` permette di indicarne un'altra copia verificabile;
`--senza-oracle` genera esplicitamente un report privo del riferimento.

Il documento è orizzontale e sintetico: presenta i sistemi e il campione,
mostra subito lo scarto medio dall'oracle e i grafici per circuito, poi conclude
con le osservazioni sul campione e i loro limiti. Il RAG fisso è indicato da una
croce rossa grande. Tempi, token, memoria e confronti A/B restano nei dati e nei
grafici autonomi, senza ripetere queste analisi nel PDF principale.

Ogni ordinamento ha quattro pagine di dettaglio: 25, 25, 25 e 15 circuiti.
L'indice alfabetico e la scala degli scarti sono comuni. Gli scarti negativi
restano visibili; un dato mancante non diventa zero. Un asterisco distingue
l'oracle parziale. Le medie dichiarano i circuiti effettivamente confrontabili.

| File | Contenuto |
| --- | --- |
| `rapporto.tex`, `rapporto.pdf` | Documento autonomo; il PDF richiede `--pdf`. |
| `circuiti.csv` | Misure dei passaggi conclusi, nell'ordine di esecuzione. |
| `distanze_oracle.csv` | 90 righe per ordine, inclusi gli eventuali casi non eseguiti. |
| `riepilogo.csv` | Confronto di ciascun ordine con RAG fisso. |
| `confronto_ordinamenti.csv` | Medie sul sottoinsieme comune a tutti. |
| `confronti_appaiati.csv` | Sei confronti A/B e circuiti confrontati. |
| `dati.json` | Misure, riferimenti, metadati e denominatori. |
| `grafici/` | Venti figure autonome: sedici di dettaglio, due di confronto, qualità cumulativa e memoria. |
| `provenienza.json` | Impronte di fonti, generatori e risultati. |

Il report riusa la verifica storica MQT Bench: controlla le impronte dei 16.200
esiti oracle e ricostruisce i massimi. Rifiuta un riepilogo alterato, una diversa
selezione di circuiti o Target e versioni incompatibili. Il riferimento viene
letto soltanto durante l'analisi.

L'analisi ricontrolla i registri conclusi e il controllo storico. Le modifiche
riguardano il report; il codice e i contratti delle campagne restano invariati.
Le prove sintetiche rimangono in `../verifiche_sviluppo/temporanei/`.
Per le condizioni dell'esperimento leggere il [README principale](../README.md).

## Revisione dei PDF esistenti

La forma è condivisa con gli altri tre report in `sintesi.py`.
Per rivedere un report già generato, senza ripetere esperimenti:

```bash
.venv/bin/python -B archivio/valutazione/rag_incrementale/report/aggiorna_sintesi.py \
  PERCORSO_DELLA_CARTELLA_DEL_REPORT
```

La procedura conserva il documento precedente in `revisioni/`, ricompila
sorgenti e figure e verifica che `dati.json` e tutte le tabelle CSV restino
identici. `revisione_sintesi.json` e `provenienza.json` registrano le impronte.
Le conclusioni calcolano perdite e conteggi dai dati del report, distinguendo
differenze di score e perdita relativa rispetto al controllo.
Le unità percentuali sono mostrate con il simbolo percentuale (%). I quattro ordini
degli stessi circuiti non vengono presentati come repliche indipendenti.

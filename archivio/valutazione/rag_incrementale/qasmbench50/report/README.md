# Report QASMBench: memoria incrementale e oracle

`genera.py` legge le quattro campagne locali e gli esiti storici. Non chiama
l'LLM, non compila circuiti e non aggiorna memorie. La guida principale
contiene il comando di avvio e il riferimento oracle predefinito.

Il documento apre con una breve descrizione dei sistemi e dei 50 circuiti.
Seguono lo scarto medio dall'oracle e i grafici per circuito; le conclusioni
sono in fondo e distinguono risultati, interpretazione e limiti del campione.
I grafici conservano nomi, score affiancati e barra dello scarto R-S.
Una croce rossa grande indica il controllo fisso. Ogni ordine ha due pagine di 25 circuiti.
Scala e indice dei circuiti sono comuni ai quattro ordini. Gli scarti
negativi sono visibili; quelli mancanti sono trattini. Un asterisco
distingue il riferimento parziale.

Il confronto globale usa gli stessi successi di tutti gli ordini e del
controllo. Il grafico della media dello scarto dichiara il numero di
riferimenti disponibili. I sei confronti A/B hanno denominatori propri.

Ogni cartella di uscita conserva:

| File | Contenuto |
| --- | --- |
| `rapporto.tex`, `rapporto.pdf` | Documento autonomo; il PDF richiede `--pdf`. |
| `circuiti.csv` | Misure dei passaggi conclusi, nell'ordine di esecuzione. |
| `distanze_oracle.csv` | 50 righe per ordine, inclusi i casi non eseguiti. |
| `riepilogo.csv` | Confronto di ciascun ordine con RAG fisso. |
| `confronto_ordinamenti.csv` | Medie sul sottoinsieme comune a tutti. |
| `confronti_appaiati.csv` | Sei confronti A/B e circuiti confrontati. |
| `dati.json` | Misure, riferimenti, metadati e denominatori. |
| `grafici/` | Dodici figure autonome: otto per circuito, due di confronto, qualità cumulativa e memoria. |
| `provenienza.json` | Impronte di fonti, generatori e risultati. |

L'oracle viene verificato dagli esiti originali e dai circuiti compilati:
non si considera sufficiente il solo `dati.json`. Un riepilogo alterato,
fonti diverse o una differenza fra Target/versioni fermano l'analisi.
Si può usare `--senza-oracle` per produrre esplicitamente un report privo
del riferimento. L'assenza non viene nascosta.

Non si sovrascrive una versione esistente. Il codice dell'analisi può
evolvere mantenendo leggibili i registri conclusi; le impronte documentano
il generatore effettivamente usato. Le prove sintetiche rimangono in
`verifiche_sviluppo/temporanei/`, separate dai risultati.

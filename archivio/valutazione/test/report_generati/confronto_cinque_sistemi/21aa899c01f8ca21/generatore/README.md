# Report dei risultati Test

Questa cartella contiene i programmi di analisi. Legge i risultati già salvati e produce un report per ciascun
sistema disponibile e un report complessivo. Non avvia il Test, non chiama Qwen
e non richiede modelli MQT per analizzare gli altri sistemi.

Dalla radice del progetto, in WSL:

```bash
.venv/bin/python archivio/valutazione/test/report/genera.py
```

Il comando cerca MQT in `archivio/valutazione/test_mqt_esplorativo/risultati/mqt_predictor/`.
Quando il registro è presente, lo usa al posto dell'eventuale registro MQT in
`archivio/valutazione/test/risultati/`: le due esecuzioni non vengono sommate. Gli altri
sistemi continuano a provenire dall'area Test originale. Se manca il registro
esplorativo, resta supportata la precedente posizione MQT.

La prova separata conserva il proprio contratto e viene indicata come
**MQT Predictor (espl.)** nei grafici e nelle tabelle. Il report descrive il
Training set incompleto (384/396), le deroghe e il profilo di raccolta. Non la
presenta come completamento della valutazione conforme al contratto originale.
Si controllano il contratto della fonte, lo stesso manifest, gli SHA-256 dei
circuiti e tutti i criteri di valutazione condivisi, compreso il timeout Test
100 secondi. Non si disattivano i controlli sulle altre esecuzioni.

Per indicare un'altra area MQT separata con la stessa struttura:

```bash
.venv/bin/python archivio/valutazione/test/report/genera.py --mqt-area archivio/valutazione/test_mqt_esplorativo
```

L'area deve contenere `piano.json`, `preparazione/contratto_congelato.json` e
`risultati/mqt_predictor/esecuzione.json`. Un percorso esplicito mancante genera
un errore. Percorsi e impronte di ogni fonte sono conservati in `provenienza.json`.
Se una prova è parziale, il documento distingue casi conclusi e pendenti.

## Sorgenti

| File o cartella | Funzione |
| --- | --- |
| `genera.py` | Coordina la creazione dei documenti. |
| `dati.py` | Legge e aggrega esiti e misure. |
| `fonti.py` | Distingue il Test originale dalla fonte MQT esplorativa. |
| `confronto.py` | Costruisce il confronto fra metodi. |
| `impaginazione.py`, `pannelli.py` | Producono tabelle e figure LaTeX. |
| `verifiche/` | Controlli sintetici sui calcoli e sulle fonti. |

## Dove trovare i documenti

Aprire `archivio/valutazione/test/report_generati/README.md`: contiene i collegamenti
all'ultima versione. `ultimo.json` conserva gli stessi percorsi per gli strumenti.
Ogni versione ha una cartella identificata dall'impronta dei dati e del generatore:

```text
report_generati/<impronta>/
  provenienza.json                 impronte degli input e ambiente
  completato.json                  impronte degli output verificabili
  confronto.json                  risultati del confronto appaiato
  generatore/                     copia dei sorgenti usati
  sistemi/<metodo>/
    riepilogo.json
    tabelle/circuiti.csv           medie e coperture per circuito
    tabelle/episodi.csv            valori dei singoli episodi
    grafici/                      CSV e sorgenti PGFPlots
    latex/risultati.tex            frammento per la tesi
    latex/verifica.tex             documento autonomo
    latex/verifica.pdf
  confronto/
    tabelle/                      tutti i sistemi e differenze appaiate
    grafici/
    latex/risultati.tex
    latex/verifica.tex
    latex/verifica.pdf
```

Gli output e le prove di impaginazione restano separati dai sorgenti versionati.
I dati originali e i report precedenti non vengono sovrascritti. Gli hash
includono anche i registri di chiamata e le sessioni. Con gli stessi dati e
sorgenti, il comando riusa una versione conclusa solo se i file prodotti
conservano le impronte attese. La copia del generatore serve alla tracciabilità:
per riprodurla occorre la corrispondente struttura del repository e i dati.

Il report complessivo ha quattro sezioni: introduzione al Test, sistemi e
impostazioni, risultati, conclusioni. Le tabelle di riepilogo precedono tutti
i grafici. Ogni figura ha una pagina orizzontale con una spiegazione iniziale
e quattro pannelli: LLM + RAG, LLM no RAG, MQT e Random, in quest'ordine
per righe. Gli assi dei pannelli condividono la scala. Le misure LLM
non applicabili mantengono una cella esplicita, senza zeri inventati.

Le quattro torte usano come denominatore tutti i circuiti previsti. Distinguono
score almeno 0,8, score inferiore, casi senza score e pendenti, se presenti.
La soglia è descrittiva e successiva al Test. I conteggi esatti sono anche in
tabelle/soglia_score_080.csv.

L'appendice contiene una tabella per misura: nomi completi dei circuiti e dei
sistemi, senza indice numerico, e conteggi interi senza decimali. Gli score
sono stampati a sei decimali; i CSV conservano la precisione originale.
Una media non intera di eventuali repliche conserva i decimali.
I dettagli tecnici dell'ambiente rimangono in provenienza.json. Include tabelle per tutti i circuiti, grafici di score,
tempi, token, retry, successi/fallimenti e distribuzione degli score.
Ogni report individuale comprende anche token in ingresso e uscita,
numero di chiamate, cause dei fallimenti e copertura delle misure.

## Regole dei calcoli

- Successi e fallimenti sono conteggi degli episodi conclusi. Un caso pendente
  non è un fallimento. Errori, timeout e interruzioni terminali sono fallimenti.
- Le correzioni LLM non sono episodi nuovi: il retry conta le chiamate oltre la
  prima. Token e latenza LLM sommano tutte le chiamate dello stesso episodio.
- Se ci sono repliche dello stesso circuito, si calcola prima la media per
  circuito e poi la media fra circuiti. Ogni circuito ha lo stesso peso.
  Le somme dei costi contano invece tutti gli episodi misurati.
- Lo score usa solo gli episodi riusciti. I fallimenti restano nei conteggi,
  senza score uguale a zero. Le durate o i token sconosciuti restano mancanti.
  Ogni misura ha numero di episodi presenti e mancanti nel CSV.
- Il tempo totale comprende la procedura dal circuito all'esito misurato.
  La misura interna del compilatore è distinta dalla durata del processo.
  Nei timeout senza misura interna non si sostituisce il limite di 100 secondi.
- Il confronto di qualità usa gli stessi circuiti con score per entrambi i
  metodi: 10000 ricampionamenti appaiati, seed 20260901, intervallo percentile
  al 95%. È un'analisi descrittiva, come stabilito nel protocollo.
- Si controllano contratto, split, numero atteso, identità del circuito e
  SHA-256. Un esito riepilogativo annidato sopra altri esiti viene rifiutato
  per evitare di contarlo come replica. Il piano attuale prevede un episodio:
  il generatore non autorizza nuove ripetizioni del Test.

## LaTeX e inserimento nella tesi

Servono NumPy già presente nell'ambiente del progetto e TeX Live con PGFPlots,
Babel italiano, Latin Modern, booktabs, longtable, microtype, placeins, array,
pdflscape, caption e xurl.
Non occorrono Matplotlib, servizi esterni o download dei modelli.

Per produrre solo LaTeX e dati:

```bash
.venv/bin/python archivio/valutazione/test/report/genera.py --solo-sorgenti
```

Per una cartella alternativa usare `--output PERCORSO`. I documenti possono
essere compilati entrando nella rispettiva cartella `latex/` e lanciando due
volte `pdflatex -halt-on-error verifica.tex`.

Per inserire un frammento nella tesi, caricare i pacchetti indicati nel suo
`preambolo.tex`, adattando margini e lingua alla tesi. Poi usare:

```latex
\begingroup
\def\TestReportPath{percorso/al/report/confronto/}
\input{percorso/al/report/confronto/latex/risultati.tex}
\endgroup
```

Per un sistema singolo sostituire `confronto/` con `sistemi/llm_rag/`, per esempio.
Conservare le sottocartelle `grafici/` e `latex/`; il percorso deve terminare con `/`.

## Separazione dal codice congelato

La cartella `report/` è esterna all'insieme di file raccolti da `code_files()`
per il contratto Test. La sua modifica non cambia il contratto dei sistemi.
Il precedente `archivio/valutazione/test/analizza.py` e il generatore richiamato alla fine
delle esecuzioni rimangono disponibili; il comando qui sopra è quello generale
per i nuovi report completi. Non sono stati modificati protocollo, prompt,
regole di compilazione, registri o sorgenti nell'archivio congelato.

Verifiche sintetiche del nuovo generatore:

```bash
.venv/bin/python -m unittest discover -s archivio/valutazione/test/report/verifiche -v
```

Il [resoconto dello sviluppo](SVILUPPO.md) documenta decisioni e controlli.

## Riorganizzazione del 25 settembre 2026

I report precedenti, le copie del generatore e i loro metadati restano intatti.
I programmi correnti risolvono le fonti dalla nuova area
`archivio/valutazione/`; non usano i vecchi percorsi assoluti dei registri per
cercare gli esiti. Il contratto salvato resta confrontato con il piano e con
l'identità delle esecuzioni, senza richiedere che il codice di analisi abbia
l'impronta del vecchio motore sperimentale.

Una rigenerazione conserva una nuova versione con i percorsi e le impronte
correnti. Non riprende il Test e non cambia gli esiti o i contratti congelati.
Durante la riorganizzazione non vengono rigenerati i rapporti storici.

## Supplemento sui fatti verificabili

[analizza_fatti.py](analizza_fatti.py) rilegge le risposte già conservate,
verifica alias ed esempi e produce audit e sorgente LaTeX separati.
[testo_fatti.py](testo_fatti.py) contiene il testo e l'impaginazione.
L'output è in ../report_generati/30dd5b4f737c058e/analisi_fatti/.
Il PDF del confronto originale resta invariato.

## Report indipendente del recupero casuale

Il generatore genera_recupero_random.py produce soltanto il report di LLM +
cinque esempi casuali. Riusa impaginazione e misure dei report per sistema.
Legge il riepilogo della campagna seed_20260927 e ricalcola le misure dagli
esiti, verificando le impronte, il contratto separato e i registri del recupero.

Comando dalla radice del progetto:

    .venv/bin/python archivio/valutazione/test/report/genera_recupero_random.py

L'opzione --riepilogo permette di indicare un altro riepilogo della stessa
variante. --output cambia la cartella delle versioni. Il PDF, i sorgenti
LaTeX, i CSV e la provenienza finiscono in una nuova cartella di
report_generati/, sotto sistemi/llm_recupero_random/.
Il confronto precedente e il suo indice ultimo.json restano invariati.
La prova è descritta come estensione esplorativa con un solo seme.
Il comando non avvia modelli o compilazioni quantistiche e non aggiorna il grafo.

## Confronto esteso a cinque sistemi

    .venv/bin/python archivio/valutazione/test/report/genera_confronto_cinque.py

Genera una nuova versione in report_generati/confronto_cinque_sistemi/.
Il report 30dd5b4f737c058e resta intatto: tutte le sue impronte vengono
verificate prima e dopo. Gli esiti dei quattro sistemi devono coincidere
con quelli del report di riferimento; la nuova campagna ha controlli separati.

Tutti i dieci gruppi di grafici hanno cinque pannelli: due nella prima riga,
due nella seconda, quello di LLM + Random RAG centrato nella terza.
Anche tabelle e appendice includono il nuovo sistema.
Le nuove conclusioni usano le differenze reali e fasce di qubit descrittive
definite dopo il Test. Distinguono differenze assolute e percentuali relative.
I CSV conservano anche parità esatte e casi distanti al massimo 0,01.
Non vengono eseguite prove quantistiche né aggiornamenti del grafo.

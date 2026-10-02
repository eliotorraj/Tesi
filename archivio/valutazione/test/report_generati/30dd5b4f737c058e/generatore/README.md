# Report dei risultati Test

Questo programma legge i risultati già salvati e produce un report per ciascun
sistema disponibile e un report complessivo. Non avvia il Test, non chiama Qwen
e non richiede modelli MQT per analizzare gli altri sistemi.

Dalla radice del progetto, in WSL:

```bash
.venv/bin/python prototipo/test/report/genera.py
```

Il comando cerca MQT in `prototipo/test_mqt_esplorativo/risultati/mqt_predictor/`.
Quando il registro è presente, lo usa al posto dell'eventuale registro MQT in
`prototipo/test/risultati/`: le due esecuzioni non vengono sommate. Gli altri
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
.venv/bin/python prototipo/test/report/genera.py --mqt-area prototipo/test_mqt_esplorativo
```

L'area deve contenere `piano.json`, `preparazione/contratto_congelato.json` e
`risultati/mqt_predictor/esecuzione.json`. Un percorso esplicito mancante genera
un errore. Percorsi e impronte di ogni fonte sono conservati in `provenienza.json`.
Se una prova è parziale, il documento distingue casi conclusi e pendenti.

## Dove trovare i documenti

Aprire `prototipo/test/report_generati/README.md`: contiene i collegamenti
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
.venv/bin/python prototipo/test/report/genera.py --solo-sorgenti
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
Il precedente `prototipo/test/analizza.py` e il generatore richiamato alla fine
delle esecuzioni rimangono disponibili; il comando qui sopra è quello generale
per i nuovi report completi. Non sono stati modificati protocollo, prompt,
regole di compilazione, registri o sorgenti nell'archivio congelato.

Verifiche sintetiche del nuovo generatore:

```bash
.venv/bin/python -m unittest discover -s prototipo/test/report/verifiche -v
```

Il [resoconto dello sviluppo](SVILUPPO.md) documenta decisioni e controlli.

# Esperimento MQT Predictor e assistente quantistico

## Protocollo corrente: versione 2.0

La nuova pipeline usa MQT Predictor 2.4.0, MQT Bench 2.2.3, Qiskit 2.5.0 e
Python 3.12. Confronta LLM con e senza RAG, un LLM di frontiera, qcompile,
Qiskit predefinito, una scelta casuale e l'oracle esaustivo.

Il protocollo 1.0 e i risultati basati sulla pila 2.3.0 restano intatti. Tutti
gli output 2.0 hanno un nuovo identificativo e directory separate.

La guida completa, con dipendenze, protezioni contro il leakage, comandi di
training, popolamento, ripresa e apertura del test, è in
[docs/protocollo_sperimentale_v2.md](docs/protocollo_sperimentale_v2.md).

Stato attuale:

- è sicuro avviare il popolamento Qiskit full di train e validation;
- è sicuro avviare i cinque training RL;
- il test resta sigillato;
- qcompile non è ancora pronto, perché mancano i modelli addestrati;
- i tre modelli LLM devono ancora essere scelti e congelati.

## 1. Protocollo 1.0 conservato

Questo ramo, `qiskit_dataset`, raccoglie due parti collegate del progetto:

- la procedura sperimentale che compila circuiti direttamente con Qiskit e
  costruisce il Dataset per il RAG;
- il prototipo dell'assistente che riceve una richiesta strutturata, applica i
  vincoli hardware e prepara la scelta di un dispositivo e di una
  configurazione Qiskit.

Il Dataset contiene esempi etichettati ottenuti da compilazioni reali eseguite
in locale. Per ogni circuito confronta cinque dispositivi e dodici
configurazioni di `qiskit.transpile`, ripetute con tre seed. La misura usata è
`expected_fidelity`, calcolata sul Target sintetico di MQT Bench. Non è quindi
una misura raccolta su hardware quantistico reale.

Il prototipo usa lo stesso catalogo dei dispositivi e delle configurazioni.
Prima di interrogare il modello linguistico controlla la richiesta e costruisce
una maschera dei dispositivi utilizzabili. I vincoli scelti dall'utente possono
limitare fornitori, dispositivi ammessi, numero di qubit e gate nativi. Non
esiste un secondo elenco di dispositivi vietati.

Anche la risposta del modello viene controllata. Deve essere un singolo oggetto
JSON conforme allo schema, riferito alla richiesta e al catalogo correnti. Le
affermazioni e i riferimenti alle evidenze sono campi strutturati. Il modello non
fornisce una spiegazione libera: il testo mostrato all'utente viene costruito dal
prototipo dopo tutti i controlli. Se la risposta è errata, il sistema può
effettuare un numero limitato di nuovi tentativi.

I modelli RL e ML di MQT Predictor, i loro artefatti e la procedura storica
rimangono nel ramo `main`. Non fanno parte di questo ramo.

### Terminologia

- **Dataset**: insieme destinato al RAG o a un eventuale addestramento mirato
  del modello linguistico.
- **Training set**: coppie circuito-dispositivo usate per addestrare i modelli
  ML storici di MQT Predictor.

La guida specifica del Dataset è in
[`datasets/expected_fidelity/README.md`](datasets/expected_fidelity/README.md).
La guida del prototipo è in
[`prototype/README.md`](prototype/README.md).

Il protocollo sperimentale ufficiale, approvato e congelato, è in
[`docs/protocollo_sperimentale_definitivo.md`](docs/protocollo_sperimentale_definitivo.md).

## 2. Struttura del progetto e compito dei file

```text
configs/
  qiskit_dataset_configurations.json
datasets/expected_fidelity/
knowledge/
prototype/
qiskit_dataset/
report/
schemas/
scripts/
tests/
pyproject.toml
uv.lock
```

- `configs/qiskit_dataset_configurations.json` fissa dispositivi,
  configurazioni Qiskit, seed e misura usati negli esperimenti.
- `datasets/expected_fidelity/` contiene i circuiti, i risultati del campione
  pilota, le viste per dispositivo e la vista generale.
- `knowledge/` conserva le fonti e il riassunto usati come base locale del
  progetto.
- `prototype/` contiene il prototipo dell'assistente e la sua documentazione.
- `qiskit_dataset/` contiene l'implementazione della procedura sperimentale.
- `report/` contiene i documenti periodici sullo stato della tesi.
- `schemas/` contiene gli schemi JSON dei record del Dataset e dei dati del
  prototipo.
- `scripts/` contiene i comandi eseguibili per preparare l'ambiente e costruire
  il Dataset.
- `tests/` verifica sia la procedura sperimentale sia il prototipo.
- `pyproject.toml` e `uv.lock` fissano l'ambiente Python riproducibile.

### Moduli della procedura Qiskit

- `qiskit_dataset/catalog.py` legge e controlla il catalogo sperimentale.
- `qiskit_dataset/core.py` prepara i circuiti, le suddivisioni e i tentativi da
  eseguire.
- `qiskit_dataset/generation.py` compila i circuiti, controlla il risultato e
  salva punteggi o errori.
- `qiskit_dataset/views.py` aggrega i seed e costruisce gli esempi etichettati.
- `qiskit_dataset/aggregation.py` unisce i risultati dei diversi dispositivi
  senza modificare le viste di partenza.
- `qiskit_dataset/reporting.py` produce statistiche, tabelle e resoconti del
  campione pilota.

### Script

- `scripts/bootstrap_ubuntu.sh` crea l'ambiente virtuale e installa le versioni
  fissate delle dipendenze.
- `scripts/01_check_install.py` controlla l'ambiente e le funzioni MQT usate dal
  progetto.
- `scripts/02_list_devices.py` elenca i dispositivi disponibili in MQT Bench.
- `scripts/07_prepare_qiskit_dataset.py` prepara il corpus condiviso e i
  manifest per dispositivo.
- `scripts/08_generate_qiskit_dataset.py` esegue i tentativi di compilazione.
- `scripts/09_build_qiskit_dataset_views.py` costruisce aggregati, esempi RAG e
  resoconti per un dispositivo.
- `scripts/10_aggregate_qiskit_dataset.py` costruisce la vista generale con più
  dispositivi.

### Schemi JSON

- `schemas/qiskit_run.schema.json` descrive un singolo tentativo di
  compilazione.
- `schemas/qiskit_configuration_aggregate.schema.json` descrive l'aggregato dei
  tre seed per una configurazione.
- `schemas/qiskit_rag_example.schema.json` descrive un esempio etichettato per
  il RAG.
- `schemas/assistant_request.schema.json` descrive la richiesta inviata al
  prototipo.
- `schemas/hardware_catalog.schema.json` descrive l'istantanea versionata del
  catalogo hardware.
- `schemas/hardware_mask_result.schema.json` descrive la maschera dei
  dispositivi e le motivazioni di esclusione.
- `schemas/llm_recommendation.schema.json` descrive la raccomandazione
  strutturata, le affermazioni e i riferimenti che il modello linguistico deve
  restituire.

## 3. Implementazione

### Ambiente riproducibile del protocollo 1.0

L'ambiente di riferimento usa Ubuntu, oppure Ubuntu su WSL2, e Python 3.12. Le
versioni principali sono:

- `mqt.predictor==2.3.0`;
- `mqt.bench==2.0.0`;
- `qiskit==2.1.1`.

La preparazione iniziale è:

```bash
bash scripts/bootstrap_ubuntu.sh
source .venv/bin/activate
python scripts/01_check_install.py
python scripts/02_list_devices.py
```

### Costruzione del Dataset

La procedura ha quattro passaggi:

```text
07_prepare_qiskit_dataset.py
  -> corpus condiviso, suddivisioni e manifest per dispositivo
08_generate_qiskit_dataset.py
  -> compilazioni Qiskit, controlli, punteggi ed errori
09_build_qiskit_dataset_views.py
  -> aggregati dei seed, esempi RAG e resoconti per dispositivo
10_aggregate_qiskit_dataset.py
  -> Dataset generale con il confronto tra dispositivi
```

Ogni circuito appartiene a una sola suddivisione tra `train`, `validation` e
`test`. Solo `train` entra negli esempi destinati al RAG. Le altre due parti
restano separate per la valutazione.

Il Dataset generale sceglie il dispositivo la cui migliore configurazione
valida ha la mediana di `expected_fidelity` più alta. Conserva anche i dati che
permettono di ricostruire la scelta e le limitazioni scientifiche del
risultato.

### Preparazione della richiesta dell'assistente

La richiesta del prototipo contiene il circuito OpenQASM 2, la misura scelta,
l'identificativo del catalogo e gli eventuali vincoli hardware. I valori
vengono controllati prima di leggere il Dataset o chiamare il modello
linguistico.

La maschera assegna `1` ai dispositivi utilizzabili e `0` agli altri. Per ogni
zero conserva una motivazione. Se non rimane alcun dispositivo, il flusso si
ferma prima del RAG. La ricerca e la risposta del modello non possono quindi
aggirare i vincoli.

### Validazione della risposta del modello

Il collegamento al modello può restituire testo JSON oppure un oggetto già
letto dall'adattatore. Nel primo caso il testo deve contenere un solo oggetto,
senza prosa, blocchi Markdown, chiavi duplicate o valori non validi.

Lo schema chiuso controlla campi, tipi e intervalli. I controlli successivi
verificano l'identificativo della richiesta, l'istantanea del catalogo, il
dispositivo scelto, la maschera e la configurazione Qiskit. La stessa istanza
del catalogo delle configurazioni viene usata per costruire il catalogo
hardware, preparare la richiesta al modello e controllare la risposta.

Dopo la ricerca viene costruito un registro immutabile con i primi esempi
storici recuperati. Il registro conserva risultati, configurazioni,
affermazioni sorgente e limiti scientifici. Ogni riferimento prodotto dal
modello deve indicare un record presente in questo registro. Il validatore
controlla anche che le evidenze siano tutte e sole quelle collegate
all'affermazione storica e che dispositivo e configurazione coincidano con la
raccomandazione corrente.

La spiegazione finale non proviene dal testo del modello. Un componente
deterministico la costruisce usando soltanto affermazioni e riferimenti già
validati. I risultati storici vengono presentati come precedenti di circuiti
simili, mai come misure del circuito corrente. Se gli esempi nel formato
precedente non contengono evidenze, il sistema richiede una dichiarazione
strutturata di questa assenza e usa soltanto la compatibilità verificata dal
prototipo.

Gli errori contengono codice, percorso e messaggio. Anche gli errori nei
collegamenti tra affermazioni ed evidenze seguono questa politica. Il registro
viene costruito una sola volta e resta identico in tutti i tentativi. Gli errori
vengono inseriti nella richiesta successiva fino al limite configurato, pari a
tre tentativi nella configurazione predefinita. Errori del Dataset, del
catalogo, del collegamento al modello o del programma non vengono trasformati
in nuovi tentativi.

### Affidabilità e riproducibilità

Le principali garanzie sono:

- una sola copia dei circuiti per insieme `pilot` o `full`;
- riferimenti ai circuiti controllati tramite SHA-256;
- catalogo, seed e versioni software registrati nei risultati;
- salvataggio atomico dei singoli tentativi e ripresa dei lavori interrotti;
- controllo delle operazioni e della connettività del circuito compilato;
- separazione tra dati osservati e interpretazioni dei limiti temporali;
- aggregazione generale che legge le viste per dispositivo senza modificarle;
- validazione della richiesta, della risposta e dei collegamenti tra
  affermazioni ed evidenze prima della compilazione;
- compilazione consentita solo dopo la conferma esplicita dell'utente e con un
  risultato validato emesso dal servizio.

### Esecuzione del campione pilota

Esempio per un dispositivo:

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27 \
  --workers 2 --timeout-seconds 120
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope pilot --device ibm_falcon_27 --top-k 3
```

Dopo aver costruito le viste di tutti i dispositivi:

```bash
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope pilot --top-k 3 --require-all-supported
```

Il Dataset generale del campione pilota si trova in:

```text
datasets/expected_fidelity/pilot/global/rag_examples.jsonl
```

### Verifica

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q qiskit_dataset prototype scripts tests
git diff --check
```

### Sviluppi successivi del protocollo 1.0

I prossimi passi sono:

1. definire e verificare la misura di similarità tra circuiti;
2. integrare il RAG con la misura scelta;
3. congelare il protocollo sperimentale;
4. popolare il Dataset completo.

Queste parti non cambiano il contratto già definito per richiesta, catalogo e
maschera hardware.

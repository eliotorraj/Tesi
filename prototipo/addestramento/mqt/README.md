# Addestrare il selettore ML sul portatile

Usare **Ubuntu o WSL**, Python 3.12 e le versioni esatte dell'esperimento.
Il selettore usa i **396 circuiti train distinti per SHA-256**, ricavati dai
422 file originali verificati. I 26 alias byte-identici non vengono contati
come campioni aggiuntivi. La parte costosa è compilare
ogni coppia circuito-dispositivo mediante i cinque modelli RL; poi viene
addestrato il classificatore Random Forest.

## Aggiornare il codice da GitHub

Nel clone del portatile:

```bash
git status --short
git fetch origin
git switch riorganizzazione-prototipo
git pull --ff-only origin riorganizzazione-prototipo
```

Conservare eventuali modifiche locali prima di cambiare ramo.
Se la revisione operativa non è stata ancora pubblicata dal desktop,
`prototipo/addestramento/mqt/addestra.py` non comparirà con il solo pull.
In quel caso pubblicare prima le modifiche del ramo o trasferire la cartella
operativa insieme al repository. Non ricreare il vecchio ambiente contenente
i modelli: usare un ambiente nuovo dedicato.

Dalla radice del clone:

```bash
cd archivio/esperimento_v2
UV_PROJECT_ENVIRONMENT=.venv-selettore uv sync --frozen --python 3.12
cd ../..
```

## Dati e modelli da trasferire

Il pull trasferisce solo i file versionati. Servono anche questi dati
all'interno di `archivio/esperimento_v2/`:

- `artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/sources/train/`;
- `artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/manifests/source_circuits_v2.json`;
- il corpus originale in `archivio/protocollo_v1/datasets/expected_fidelity/full/`;
- `artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/models/rl/`.

L'ultima cartella deve contenere, per ognuno dei cinque dispositivi,
`model_expected_fidelity_<device>.zip` e
`model_expected_fidelity_<device>.metadata.json`.
I dispositivi sono ibm_falcon_27, ibm_heron_133, ibm_falcon_127,
ibm_heron_156 e quantinuum_h2_56. Non bastano i checkpoint incompleti.

## Controllare e avviare

Dalla radice del repository:

```bash
archivio/esperimento_v2/.venv-selettore/bin/python prototipo/addestramento/mqt/addestra.py --num-workers 1 --rf-workers 2 --dry-run

archivio/esperimento_v2/.venv-selettore/bin/python prototipo/addestramento/mqt/addestra.py --num-workers 1 --rf-workers 2
```

Il controllo verifica i modelli canonici. Il vero avvio li copia
nell'ambiente Python quando necessario, conservando copie runtime precedenti.
Un worker RL e due processi per il classificatore limitano la memoria sul portatile.

Il secondo comando costruisce il Training set e addestra il modello.
Può essere rilanciato per riprendere i checkpoint validi. Non cambiare seed,
timeout o limiti mantenendo la stessa cache. Un errore interno nel registro
viene segnalato. Una coda interrotta viene conservata e riparata.
Non usare `--allow-incomplete` per pubblicare un modello finale.

## Risultati dell'addestramento

Tutto il nuovo lavoro è dentro questa cartella:

| Percorso | Contenuto |
| --- | --- |
| `cache/sha256_396_spawn_v1/expected_fidelity/timeout_100/` | Compilazioni, tentativi e stato riprendibile |
| `registri/` | Log dei processi |
| `training_set/device_selector_expected_fidelity.json` | Training set leggibile da programma |
| `modelli/` | Classificatore finale e metadati |
| `precedenti/` | Copie di artefatti precedenti prima di sostituire le copie operative |

Il modello finale deve coprire esattamente i cinque dispositivi.
Il programma rifiuta la pubblicazione quando la copertura richiesta manca.
Non aggirare il controllo per ottenere un file apparentemente pronto.

Per usarlo sul desktop trasferire `modelli/`, Training set e registri nella
stessa posizione del clone, conservando anche i checkpoint per la riproducibilità.
Il classificatore deve essere installato anche nel runtime MQT del desktop;
usare `sincronizza.py` con quel Python. Poi eseguire il controllo e le sei prove
tecniche di [MQT Test](../../test/README.md).

## Provenienza e limiti

`motore_ml.py` deriva dallo script archiviato. `provenienza.json` ne conserva
origine, impronta e modifiche. Sono corretti SCR-02, SCR-03 e SCR-04 della
revisione del 21 settembre: coda JSONL, lettura dei risultati prima dell'uscita
dei processi, identità del timeout. Sono conservati gli artefatti precedenti.
La revisione non cambia l'algoritmo di apprendimento o i circuiti train.

La prova di sviluppo ha verificato i difetti con dati sintetici.
Non è stato eseguito un nuovo addestramento lungo. Nel clone desktop controllato
mancava la copia canonica di ibm_heron_133; ciò non stabilisce lo stato dei
modelli eventualmente presenti su altri computer.

## Correzione dei processi del 21 settembre

Usare sempre `addestra.py`, senza gli script diagnostici temporanei.
Il modello viene caricato nel worker avviato con `spawn`. La compilazione
avviene nello stesso processo, senza `fork`. Ogni circuito apre una nuova
connessione BQSKit; quella precedente viene chiusa senza essere riutilizzata.
Il processo principale interrompe e riavvia i worker che superano il timeout.
Il caricamento iniziale ha un limite separato di 240 secondi.

Il timeout ufficiale resta 100 secondi per coppia, con un massimo di tre tentativi.
Non è una stima del tempo necessario a tutti i circuiti: la prova breve non basta
per ottimizzarlo. Le vecchie prove e cache restano conservate. La nuova cache è
`cache/sha256_396_spawn_v1/expected_fidelity/timeout_100/` e registra anche il numero
di worker e le impostazioni dei thread. Non mescolare configurazioni diverse.

Sul portatile usare un worker RL e due worker per la ricerca dei parametri
Random Forest. Senza `--limit-circuits` vengono verificati tutti i 422 train:
poi si selezionano i 396 hash distinti, corrispondenti a **1878 coppie compatibili**.
`addestra.py` compila, costruisce il Training set e addestra il selettore.
Le prove `--compile-only` invece non producono un modello.

Per avvio e ripresa, dalla radice del repository:

```bash
archivio/esperimento_v2/.venv-selettore/bin/python -u prototipo/addestramento/mqt/addestra.py --num-workers 1 --rf-workers 2 --timeout 100
```

Tenere il portatile alimentato e impedire la sospensione. Ripetere lo stesso
comando per riprendere. I tentativi esauriti non vengono cancellati o azzerati:
se impediscono la copertura, esaminare gli errori prima di cambiare impostazioni.

Verifica tecnica del codice, senza training o accesso al Test:

```bash
archivio/esperimento_v2/.venv-selettore/bin/python prototipo/addestramento/mqt/verifiche/test_processi.py -v
```

## Selezione dei 396 campioni ML

Non passare `--limit-circuits 396`: la deduplicazione è automatica e precede
l'eventuale limite delle prove tecniche. Il rappresentante di ogni hash è il
file con nome lessicograficamente minimo. Il confronto avviene sui byte QASM,
non sulle feature o sull'equivalenza semantica.

La nuova cache contiene `selezione_train.json`: 396 gruppi con hash,
rappresentante e alias. La stessa mappa entra nel JSON del Training set e
nei metadati del modello. `source_circuit_count=422` indica il corpus originale;
`training_sample_count=396` indica i campioni richiesti per il selettore finale.
La copertura completa è di 1878 compilazioni, prima della scelta del vincitore
per ciascuno dei 396 campioni. Gli array vengono controllati prima del fit e
dell'esportazione, per impedire l'uso accidentale dei vecchi 422 campioni.

La sincronizzazione e il controllo MQT del Test rifiutano selettori privi della
nuova mappa. Le vecchie cache e gli artefatti restano conservati. I modelli RL
rimangono quelli già addestrati sui 422 file; questa modifica riguarda il ML.

```bash
archivio/esperimento_v2/.venv-selettore/bin/python prototipo/addestramento/mqt/verifiche/test_deduplica.py -v
```

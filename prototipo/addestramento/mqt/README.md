# Addestrare il selettore ML sul portatile

Usare **Ubuntu o WSL**, Python 3.12 e le versioni esatte dell'esperimento.
Il selettore usa soltanto i 422 circuiti train. La parte costosa è compilare
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
| `cache/expected_fidelity/timeout_100/` | Compilazioni, tentativi e stato riprendibile |
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

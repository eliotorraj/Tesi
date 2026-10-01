# Selettore supervisionato MQT

Questa cartella prepara il selettore del dispositivo per MQT Predictor 2.4.0.
Prima compila ogni coppia circuito-dispositivo con i modelli RL, poi costruisce
il Training set e addestra un classificatore Random Forest. È una parte della
valutazione sperimentale; il prototipo Qwen non la importa.

Il train originale contiene 422 file. I 26 alias con identici byte QASM vengono
raggruppati: restano 396 circuiti distinti e 1878 coppie compatibili.
Il rappresentante di ogni gruppo è il nome lessicograficamente minimo.
La procedura conserva i tentativi falliti e permette la ripresa dei soli
checkpoint compatibili con le impostazioni della raccolta.

## Struttura

| Percorso | Funzione |
| --- | --- |
| `addestra.py` | Ingresso per controllo, raccolta e addestramento. |
| `motore_ml.py` | Gestisce processi, compilazioni, registri e classificatore. |
| `deduplica.py` | Seleziona i 396 sorgenti distinti e controlla i campioni. |
| `validazione_selettore.py` | Controlla caratteristiche, classi e probabilità del modello. |
| `sincronizza.py` | Installa il modello verificato nel runtime MQT conservando le copie precedenti. |
| `verifiche/` | Prove sintetiche su processi, registri e deduplicazione. |
| `prove_tecniche/` | Tentativi tecnici e diagnosi conservati. |
| `importazioni/` | Copie del lavoro svolto sul portatile, con fonti, finalizzazioni e metadati originali. |
| `cache/` | Compilazioni, tentativi, selezione train e stato riprendibile, quando presenti. |
| `registri/` | Log dei processi, quando presenti. |
| `training_set/` | Training set esportato in JSON. |
| `modelli/` | Classificatore e metadati operativi, quando presenti. |
| `precedenti/` | Copie precedenti prima di sostituire artefatti operativi. |

`provenienza.json` e [SVILUPPO.md](SVILUPPO.md) descrivono l'origine dei
programmi e le correzioni. I loro vecchi percorsi restano riferimenti storici.
Le importazioni non vengono modificate per adattarle alla nuova struttura.

## Ambiente e dati necessari

Usare Ubuntu o WSL, Python 3.12 e le dipendenze esatte dell'esperimento.
Conservare sempre i modelli già presenti prima di ricreare un ambiente.
Per un nuovo ambiente dedicato, dalla radice del repository:

```bash
cd archivio/esperimento_v2
UV_PROJECT_ENVIRONMENT=.venv-selettore uv sync --frozen --python 3.12
cd ../..
```

Servono le fonti train, il manifest dei 600 circuiti, il corpus originale e i
cinque modelli RL canonici sotto `archivio/esperimento_v2/`. Ogni modello RL
richiede anche i propri metadati. Un clone Git non include necessariamente
questi artefatti voluminosi: devono essere trasferiti insieme ai registri.

La cache ufficiale usa `cache/sha256_396_spawn_v1/expected_fidelity/timeout_100/`.
La selezione `selezione_train.json` documenta rappresentanti e alias.
Il limite ufficiale è 100 secondi per coppia, con massimo tre tentativi;
il caricamento iniziale del modello ha un limite separato di 240 secondi.
Non cambiare questi parametri mantenendo la stessa identità della raccolta.

## Comandi

Dalla radice del repository, controllo senza addestramento:

```bash
archivio/esperimento_v2/.venv-selettore/bin/python archivio/valutazione/addestramento/mqt/addestra.py --num-workers 1 --rf-workers 2 --dry-run
```

Avvio esplicito della raccolta e dell'addestramento:

```bash
archivio/esperimento_v2/.venv-selettore/bin/python -u archivio/valutazione/addestramento/mqt/addestra.py --num-workers 1 --rf-workers 2 --timeout 100
```

Il comando può riprendere checkpoint compatibili. Non azzera errori o tentativi
esauriti e non rende completa una raccolta parziale. Non usare
`--allow-incomplete` per dichiarare conforme un modello finale.
`--limit-circuits 396` non serve: la deduplicazione è automatica.
I comandi `--compile-only` non producono un modello finale.

Verifiche del software, senza addestramento o accesso al Test:

```bash
.venv/bin/python -m unittest discover -s archivio/valutazione/addestramento/mqt/verifiche -v
```

## Stato e limiti

La copia importata dal portatile usata nella
[prova MQT esplorativa](../../test_mqt_esplorativo/README.md) ha 384 campioni
su 396 e combina raccolte a 100 e 300 secondi. Non è presentata come
completamento della procedura conforme. Le classi del classificatore sono
quelle effettivamente osservate: un dispositivo senza etichette vincenti
non deve essere aggiunto artificialmente.

La riorganizzazione cambia solo la posizione di questa area. Il motore legge
ancora le fonti congelate in `archivio/esperimento_v2/` e scrive nuovi artefatti
sotto questa cartella. Non avvia automaticamente raccolte, sincronizzazioni
o Test. Per i vincoli aggiornati leggere il
[protocollo sperimentale](../../../../prototipo/docs/protocollo_sperimentale.md).

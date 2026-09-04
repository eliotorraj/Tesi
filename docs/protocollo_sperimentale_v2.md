# Protocollo sperimentale 2.0

## Stato della pipeline

La pipeline 2.0 è pronta per avviare il popolamento Qiskit di train e
validation e i cinque addestramenti RL.

Non è ancora possibile dichiarare pronto qcompile. Mancano i cinque modelli RL
da 100000 step e il classificatore ML con cinque classi. Manca anche la scelta
definitiva dei tre metodi LLM. Per questo il test resta sigillato.

Il popolamento completo non è stato avviato in questa preparazione. Sono stati
eseguiti soltanto piccoli canary su circuiti train.

## Perché esiste una versione 2

Il protocollo 1.0 usa MQT Predictor 2.3.0, MQT Bench 2.0.0 e Qiskit 2.1.1.
Rimane intatto e va trattato come risultato pilota o legacy.

Il protocollo 2.0 usa MQT Predictor 2.4.0. La migrazione non è un semplice
aggiornamento di un pacchetto. MQT Predictor 2.4.0 usa MQT Bench 2 e i Target
Qiskit. La guida ufficiale richiede inoltre di addestrare un modello RL per
ogni dispositivo e poi il modello supervisionato prima di usare qcompile.
La guida di migrazione ufficiale indica anche cambiamenti nello spazio delle
azioni RL. I vecchi modelli non sono quindi accettati.

Queste sono informazioni del software ufficiale:

- [release MQT Predictor 2.4.0](https://github.com/munich-quantum-toolkit/predictor/releases/tag/v2.4.0);
- [guida ufficiale di migrazione](https://github.com/munich-quantum-toolkit/predictor/blob/main/UPGRADING.md);
- [preparazione dei modelli MQT Predictor](https://mqt.readthedocs.io/projects/predictor/en/stable/setup.html);
- [uso ufficiale di qcompile](https://mqt.readthedocs.io/projects/predictor/en/stable/quickstart.html);
- [pacchetto MQT Predictor su PyPI](https://pypi.org/project/mqt.predictor/2.4.0/).

Le regole sugli split, i timeout, i seed, i gate di apertura e il confronto
sono scelte ingegneristiche di questo progetto.

## Terminologia

- Dataset: dati destinati al RAG o a un eventuale adattamento del modello
  linguistico.
- Training set: coppie circuito-dispositivo usate dal classificatore ML di
  MQT Predictor.

## Identità e valori congelati

Identificativo:

    qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2

Versione del protocollo:

    2.0.0

Metrica primaria:

    mqt.predictor.reward.expected_fidelity

La metrica è una stima deterministica sul Target sintetico di MQT Bench. Non è
una misura raccolta su hardware reale.

Il corpus conserva i 600 circuiti del protocollo 1.0:

- 422 train;
- 88 validation;
- 90 test.

L'impronta del manifest sorgente legacy è:

    9037e08f529e6598f69cc8ffa524f593335d0e65757db771ce28b285479529ed

L'impronta semantica complessiva del corpus verificato è:

    e69ca13cd27642fe654ad4a350ba74dd6b2c539cc5667623fc58cfb1db516bb1

Il manifest v2 deterministico prodotto dalla pila congelata ha SHA-256:

    c599eab17b6f64528067016e3d175cbfed597334f779ef8e515cf8787a788f53

I controlli confrontano nomi, SHA-256 del file, hash semantico e gruppo di
leakage. Un alias che cambia soltanto nome di registro o barriere non può
attraversare gli split.

Ordine dei dispositivi e impronte dei Target:

| Dispositivo | SHA-256 Target |
| --- | --- |
| ibm_falcon_27 | b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104 |
| ibm_heron_133 | 2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3 |
| ibm_falcon_127 | 5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd |
| ibm_heron_156 | 207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003 |
| quantinuum_h2_56 | ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee |

La matrice Qiskit usa dodici configurazioni, seed 0, 1 e 2, due processi e un
timeout di 300 secondi per tentativo. Le opzioni fisse sono
approximation_degree uguale a 1 e num_processes uguale a 1.

Il piano casuale usa Python Random con MT19937 e seed 20260901. Le estrazioni
sono congelate prima degli score:

- validation: 264 estrazioni, piano
  e20ec9c7c5bca4e9eb682b6eccdd143b1417a841c16b1d9a69585907866a44b1;
- test: 270 estrazioni, piano
  93c813e2cba1352f22ab8096b53e753bb7b05dbc99f04cd7bae62ba7ff3f72a9.

## Dipendenze esatte

| Pacchetto | Versione |
| --- | --- |
| Python | 3.12 |
| mqt.predictor | 2.4.0 |
| mqt.bench | 2.2.3 |
| qiskit | 2.5.0 |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.47.0 |
| qiskit-qasm3-import | 0.6.0 |
| pytket | 2.18.1 |
| pytket-qiskit | 0.77.0 |
| bqskit | 1.2.1 |
| numpy | 2.5.1 |
| scikit-learn | 1.9.0 |
| sb3-contrib | 2.9.0 |
| stable-baselines3 | 2.9.0 |
| gymnasium | 1.3.0 |
| torch | 2.13.0 |
| joblib | 1.5.3 |
| tensorboard | 2.21.0 |

Il file uv.lock è l'unica risoluzione ammessa. Lo script di bootstrap usa
uv sync con il controllo frozen.

## Directory separate

Il protocollo 1.0 continua a usare:

    datasets/expected_fidelity/
    artifacts/qiskit_dataset_cache/expected_fidelity/

Il protocollo 2.0 usa:

    artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/
    datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/

Sotto artifacts si trovano manifest, sorgenti consentite, cache, checkpoint,
log, modelli, piani e risultati dei metodi. Sotto datasets si trovano il
Dataset Qiskit e il Training set del classificatore ML.

Queste directory sono escluse da Git perché possono diventare molto grandi.
Codice, cataloghi, schemi e istruzioni restano invece versionati.

## Bootstrap e controlli iniziali

Dalla radice del repository, dentro Ubuntu o WSL:

    bash scripts/bootstrap_ubuntu.sh
    source .venv/bin/activate
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    uv lock --check
    uv sync --frozen --python 3.12
    .venv/bin/python scripts/01_check_install.py --require-frozen-targets
    .venv/bin/python scripts/06_prepare_experiment_v2.py --check-only

Il controllo senza --require-models deve riuscire anche prima del training.
Deve però dire con chiarezza che i modelli non sono pronti.

Poi si prepara soltanto train e validation:

    .venv/bin/python scripts/06_prepare_experiment_v2.py
    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split validation
    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split test

Il comando 06 verifica tutti i 600 hash, ma materializza solo 422 train e 88
validation. Non estrae feature del test e non crea una directory test v2.

## Canary del Dataset Qiskit

I canary usano soltanto train e la stessa politica della prova completa:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split train \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 2 \
        --timeout-seconds 300 \
        --limit-runs 1
    done

Ripetendo lo stesso comando, il record già concluso è riconosciuto. Il limite
seleziona poi il primo tentativo mancante. Il popolamento completo può quindi
proseguire senza ricominciare.

## Popolamento Qiskit di train e validation

Questo è il comando completo da avviare sull'altro computer. Non comprende il
test:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split train \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 2 \
        --timeout-seconds 300
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split validation \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 2 \
        --timeout-seconds 300
      .venv/bin/python scripts/09_build_qiskit_dataset_views.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --top-k 3
    done

    .venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
      --scope full \
      --catalog configs/qiskit_dataset_configurations_v2.json \
      --top-k 3 \
      --require-all-supported

Prima del test sono previsti 87120 tentativi Qiskit. I device piccoli saltano
solo i circuiti incompatibili per larghezza. Un risultato con timeout o errore
resta nel Dataset e nel denominatore.

## Cinque training RL sequenziali

I modelli pubblicabili devono raggiungere esattamente 100000 step, usare seed
0, max_steps 64 e il profilo BQSKit registrato nei metadati. I comandi sono:

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_27 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-27-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_heron_133 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-heron-133-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_127 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-127-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_heron_156 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-heron-156-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device quantinuum_h2_56 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-quantinuum-h2-56-seed0

Ogni checkpoint ha un file metadata accanto. Una ripresa usa lo stesso target
finale di 100000 step:

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_27 \
      --timesteps 100000 --checkpoint-every 2048 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-27-seed0 \
      --resume-from PERCORSO_DEL_CHECKPOINT.zip

Un checkpoint senza metadati v2, con un altro split, seed, Target o profilo è
rifiutato. Non usare --allow-target-drift per risultati confermativi.

## Training set e classificatore ML

Dopo i cinque training RL:

    .venv/bin/python scripts/04_train_device_selector.py \
      --timeout 300 \
      --startup-timeout 240 \
      --rl-max-steps 64 \
      --seed 0 \
      --num-workers 1 \
      --max-attempts 3 \
      --rf-workers 1

Il comando usa soltanto i 422 circuiti train. Ogni coppia
circuito-dispositivo ha un checkpoint durevole. Sono accettate solo
compilazioni RL riuscite, terminate da terminate e valide sul Target. Non c'è
un fallback Qiskit pubblicabile.

La pubblicazione del classificatore richiede tutte e cinque le classi e 49
feature. Una copertura parziale può essere studiata con --allow-incomplete, ma
non produce il modello confermativo.

## Sincronizzazione e canary qcompile

    .venv/bin/python scripts/05_sync_models.py install --overwrite
    .venv/bin/python scripts/05_sync_models.py verify
    .venv/bin/python scripts/01_check_install.py \
      --require-frozen-targets --require-models
    .venv/bin/python scripts/07_validate_qcompile.py \
      --timeout 300 --max-steps 64

Il canary usa un circuito train. Esegue una compilazione RL diretta per ognuno
dei cinque device e una prova end-to-end di qcompile. Tutte e sei devono
riuscire. Una trace vuota, troncata o non conclusa da terminate fallisce.

Poi qcompile viene eseguito tre volte per ogni circuito validation:

    .venv/bin/python scripts/12_run_qcompile_v2.py \
      --split validation --timeout 300

Il runner usa un processo nuovo per ogni ripetizione. Salva subito successi,
timeout e fallimenti. --limit-circuits N esegue un piccolo lotto riprendibile.

## Metodi LLM

Il file configs/experiment_methods_v2.json è intenzionalmente non configurato.
Non vengono inventati nomi di modello o revisioni.

Prima della validation definitiva occorre compilare e poi congelare:

- provider;
- identificativo e revisione del modello;
- versione e SHA-256 del prompt;
- temperatura;
- timeout della richiesta;
- massimo numero di token in uscita.

LLM + RAG e lo stesso LLM senza RAG devono avere modello, revisione,
temperatura e budget identici. Cambia soltanto l'uso del RAG. Il RAG può leggere
esclusivamente il file rag_examples.jsonl costruito dai circuiti train.

Ogni esecutore esterno deve produrre un JSONL conforme a
schemas/method_decision_v2.schema.json. Per ogni circuito conserva anche hash
della configurazione metodi, hash della risposta grezza, tempi, uso e
fallimento. Il modello di frontiera ha un solo tentativo. Gli altri due ne
hanno al massimo tre.

Le decisioni di validation si congelano così:

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split validation --method llm_rag \
      --input PERCORSO_LLM_RAG_VALIDATION.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split validation --method llm_no_rag \
      --input PERCORSO_LLM_NO_RAG_VALIDATION.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split validation --method frontier_llm \
      --input PERCORSO_FRONTIER_VALIDATION.jsonl

Gli esecutori LLM e qcompile non devono leggere gli score Qiskit di validation.
Il valutatore controlla le loro decisioni prima di aprire la matrice che
contiene l'oracle.

## Valutazione comune

    .venv/bin/python scripts/14_evaluate_methods_v2.py --split validation

Il valutatore produce lo stesso record per:

- LLM + RAG;
- stesso LLM senza RAG;
- LLM di frontiera;
- MQT Predictor con qcompile;
- Qiskit livello 2 e 3, separato per device;
- scelta Qiskit casuale congelata;
- oracle esaustivo.

Lo score di una scelta Qiskit è la mediana dei tre seed. Tutte e tre le
ripetizioni devono riuscire. L'oracle è disponibile soltanto quando l'intera
matrice compatibile del circuito è riuscita. Se manca una combinazione, non
viene calcolato un falso massimo parziale.

Il riepilogo conserva successi, timeout, altri fallimenti, casi non applicabili,
denominatori e regret rispetto all'oracle.

## Gate che apre il test

Il comando di audit è:

    .venv/bin/python scripts/15_release_test_v2.py

Il test può essere aperto solo se sono veri tutti questi gate:

1. versioni software esatte;
2. cinque Target senza drift;
3. corpus e partizioni train/validation integri;
4. catalogo e configurazione LLM congelati;
5. piani validation e test identici a quelli ricalcolati;
6. matrice Qiskit validation completa;
7. indice RAG composto soltanto da train;
8. cinque modelli RL da 100000 step e classificatore ML a cinque classi;
9. cinque canary RL e un canary qcompile riusciti;
10. valutazione validation completa.

Solo dopo l'audit positivo:

    .venv/bin/python scripts/15_release_test_v2.py --release

Il record di apertura contiene le impronte dei file congelati. Se uno cambia,
ogni comando test torna a fallire.

## Procedura dopo l'apertura del test

Prima si materializza il test nei cinque manifest:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --include-test \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
    done

Poi si producono e si importano le tre decisioni LLM test. In questa fase non
devono ancora esistere score Qiskit test visibili agli esecutori:

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method llm_rag \
      --input PERCORSO_LLM_RAG_TEST.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method llm_no_rag \
      --input PERCORSO_LLM_NO_RAG_TEST.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method frontier_llm \
      --input PERCORSO_FRONTIER_TEST.jsonl

Si esegue qcompile:

    .venv/bin/python scripts/12_run_qcompile_v2.py \
      --split test --timeout 300

Solo dopo si popola la matrice Qiskit test:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split test \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 2 \
        --timeout-seconds 300
      .venv/bin/python scripts/09_build_qiskit_dataset_views.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --top-k 3
    done

    .venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
      --scope full \
      --catalog configs/qiskit_dataset_configurations_v2.json \
      --top-k 3 \
      --require-all-supported

    .venv/bin/python scripts/14_evaluate_methods_v2.py --split test

La ricostruzione delle viste non può aggiungere validation o test all'indice
RAG. Il file RAG congelato deve restare identico.

## Politica di ripresa

- Qiskit accetta una cache soltanto se coincidono esperimento, protocollo,
  schema, circuito, SHA-256, Target, versione, configurazione, seed, timeout e
  parallelismo.
- RL salva archivio e metadati in modo atomico. La ripresa rifiuta checkpoint
  senza provenienza v2.
- Il Training set ML salva un record per ogni coppia circuito-device. I worker
  hanno timeout reale e i processi discendenti vengono terminati.
- qcompile salva ogni ripetizione terminale. Un record fuori split o con
  identità diversa viene rifiutato.
- I risultati 2.3.0 non sono mai usati come cache 2.4.0.

## Verifiche locali

    .venv/bin/python -m unittest discover -s tests -v
    .venv/bin/python -m compileall -q qiskit_dataset prototype scripts tests
    .venv/bin/python scripts/01_check_install.py --require-frozen-targets
    .venv/bin/python scripts/06_prepare_experiment_v2.py --check-only
    git diff --check

Il comando seguente deve fallire fino al training completo:

    .venv/bin/python scripts/07_validate_qcompile.py \
      --timeout 300 --max-steps 64

Anche qualsiasi accesso test deve fallire prima del record di apertura,
compresa la modalità dry-run.

# Dataset Qiskit diretto per l'assistente LLM

Questo branch, `qiskit_dataset`, contiene la pipeline sperimentale che crea
esempi etichettati per scegliere un device e una configurazione di
`qiskit.transpile`. I modelli RL/ML, i loro artefatti e la pipeline storica
MQT Predictor rimangono nel branch `main` e non fanno parte di questo branch.

La guida completa al protocollo, agli split e ai file prodotti è in
[`datasets/expected_fidelity/README.md`](datasets/expected_fidelity/README.md).
Lo scheletro applicativo è descritto in
[`prototype/README.md`](prototype/README.md).

## Terminologia

- **Dataset**: esempi destinati al RAG o a un eventuale fine-tuning dell'LLM.
- **Training set**: coppie circuito-device usate dai modelli ML storici di MQT
  Predictor; non vengono generate in questo branch.

## Obiettivo

L'input del futuro assistente comprende:

- circuito OpenQASM e feature deterministiche;
- figure of merit;
- hardware compatibili;
- eventuali vincoli e preferenze dell'utente.

L'etichetta del Dataset generale comprende:

- device selezionato;
- tre migliori configurazioni Qiskit del device;
- claim in linguaggio naturale;
- evidence strutturata che collega ogni claim a score, seed, run, target e
  aggregato scientifico;
- caveat che impediscono di presentare stime offline come misure hardware o
  correlazioni come cause.

## Ambiente riproducibile

- Ubuntu o Ubuntu su WSL2;
- Python 3.12;
- `mqt.predictor==2.3.0`;
- `mqt.bench==2.0.0`;
- `qiskit==2.1.1`;
- dipendenze fissate in `pyproject.toml` e `uv.lock`.

Preparazione:

```bash
bash scripts/bootstrap_ubuntu.sh
source .venv/bin/activate
python scripts/01_check_install.py
python scripts/02_list_devices.py
```

## Pipeline

```text
07_prepare_qiskit_dataset.py
  -> corpus condiviso, split e manifest per-device
08_generate_qiskit_dataset.py
  -> tentativi Qiskit, cache, validazione, score e failure
09_build_qiskit_dataset_views.py
  -> aggregati seed, mini-Dataset RAG e report per-device
10_aggregate_qiskit_dataset.py
  -> Dataset generale multi-device, senza modificare i mini-Dataset
```

Esempio completo per un device:

```bash
.venv/bin/python scripts/07_prepare_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27
.venv/bin/python scripts/08_generate_qiskit_dataset.py \
  --scope pilot --device ibm_falcon_27 \
  --workers 2 --timeout-seconds 120
.venv/bin/python scripts/09_build_qiskit_dataset_views.py \
  --scope pilot --device ibm_falcon_27 --top-k 3
```

Dopo avere costruito le viste di tutti i device:

```bash
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
  --scope pilot --top-k 3 --require-all-supported
```

Il Dataset etichettato generale si trova in:

```text
datasets/expected_fidelity/pilot/global/rag_examples.jsonl
```

## Proprietà di affidabilità

- una sola copia dei circuiti per scope;
- manifest distinti per device e riferimenti verificati con SHA-256;
- catalogo e seed versionati;
- cache atomica per singolo tentativo;
- resume e retry espliciti;
- validazione basis/coupling/Target prima dello scoring;
- aggregazione generale read-only rispetto ai mini-Dataset;
- diagnostica timeout separata in osservazioni e inferenze;
- nessuna attribuzione causale automatica del timeout;
- RAG limitato allo split train; validation e test restano ground truth esterna.

## Verifica

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q qiskit_dataset prototype scripts tests
git diff --check
```

## Sviluppi successivi

La struttura è predisposta per:

1. popolare il Dataset completo dopo la conferma dei relatori;
2. formalizzare uno schema versionato dei vincoli utente;
3. congelare un protocollo sperimentale e una procedura di valutazione;
4. formalizzare la politica di retry dell'LLM in caso di risposta non valida.

Questi aspetti non sono anticipati con regole arbitrarie: il Dataset conserva
campi e provenance necessari, mentre policy e vincoli verranno versionati
quando saranno definiti.

# Esperimento MQT Predictor e assistente quantistico

Il progetto confronta un assistente LLM con e senza RAG, un LLM di frontiera,
MQT Predictor, configurazioni Qiskit fisse e una scelta casuale. La qualità è
stimata con `expected_fidelity` sui Target sintetici di MQT Bench.

Il riferimento unico è il [protocollo sperimentale](docs/protocollo_sperimentale.md).
Contiene le regole scientifiche, i comandi per i due computer, la ripresa dei
training e le condizioni per aprire il test. Si aggiorna sempre quel file.

## Esperimento attuale

Python 3.12, MQT Predictor 2.4.0, MQT Bench 2.2.3 e Qiskit 2.5.0.
Le dipendenze esatte sono fissate da `pyproject.toml` e `uv.lock`.

Identificativo:

    qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2

| Contenuto | Dove si trova |
| --- | --- |
| Protocollo unico | [docs/protocollo_sperimentale.md](docs/protocollo_sperimentale.md) |
| Catalogo attuale | [configs/qiskit_dataset_configurations_v2.json](configs/qiskit_dataset_configurations_v2.json) |
| Configurazione dei metodi LLM | [configs/experiment_methods_v2.json](configs/experiment_methods_v2.json) |
| Dataset attuale | `datasets/experiments/<identificativo>/expected_fidelity/full/` |
| Esempi indicizzati | `global/rag_examples.jsonl` dentro il Dataset attuale |
| Cache Qiskit attuale | `artifacts/experiments/<identificativo>/qiskit_dataset_cache/` |
| Modelli, checkpoint, log, manifest e piani | `artifacts/experiments/<identificativo>/` |
| Documentazione del prototipo | [prototype/README.md](prototype/README.md) |
| Fonti e contesto del progetto | [knowledge/riassunto_kb_mqt_predictor.md](knowledge/riassunto_kb_mqt_predictor.md) |
| Materiale storico | [archivio/README.md](archivio/README.md) |

Le cartelle dei cinque dispositivi e la vista `global/` sono parti dello stesso
Dataset. La vista globale sceglie il vincitore confrontando i risultati per
dispositivo: quelle cartelle servono a ricostruire e verificare la scelta.

**Dataset** indica gli esempi per RAG/LLM. **Training set** indica invece le
coppie circuito-dispositivo usate per il classificatore ML di MQT Predictor;
si trova sotto `datasets/experiments/<identificativo>/training_set/`.

## Stato verificato il 9 settembre 2026

Il Dataset train e validation è completo su questa macchina: 87120 tentativi,
82621 successi e 4499 timeout, con tutti e cinque i dispositivi. La vista
globale contiene 396 esempi RAG, tutti di train.

Il prototipo usa il parser e le impronte hardware della v2. I piani usano
100 secondi e sei processi. Qdrant locale persistente è integrato: ricerca
esatta Manhattan sulle 49 feature, con trasformazione log1p e divisori stimati
solo sui 396 esempi train. Il collegamento a un LLM reale resta da completare.

La suite supera 177 test. Il flusso RAG è verificato sugli 88 circuiti validation
fino al prompt, senza chiamate LLM o compilazioni del Dataset.

Il test resta sigillato. Su questa macchina non sono presenti i modelli finali
RL/ML né la verifica finale di qcompile. Scelta degli LLM e valutazione finale
sulla validation restano da completare prima del test.

## Comandi di riferimento

Da Ubuntu o WSL, nella radice del progetto:

```bash
.venv/bin/python scripts/16_run_pipeline_v2.py plan
.venv/bin/python scripts/06_prepare_experiment_v2.py --check-only
.venv/bin/python scripts/10_aggregate_qiskit_dataset.py --require-all-supported --check-only
.venv/bin/python scripts/17_rag_v2.py prepare
.venv/bin/python scripts/17_rag_v2.py verify
.venv/bin/python scripts/17_rag_v2.py validation
.venv/bin/python -m unittest discover -s tests -v
```

Database e manifest del recupero sono in `artifacts/experiments/<identificativo>/rag/`.
`scripts/17_rag_v2.py query --qasm PERCORSO.qasm --k 5` prepara prompt ed evidenze.
Aggiungere `--backend reference` per il riferimento esaustivo locale. Il protocollo
spiega trasformazione, limiti, ripetizione dell'indicizzazione e sincronizzazione.

L’ambiente si prepara con `bash scripts/bootstrap_ubuntu.sh`.
Per training, ripresa e valutazione seguire il protocollo unico. Dataset,
cache e modelli generati non vengono trasferiti tramite Git.

Le versioni precedenti, le diagnosi concluse, le copie di sicurezza e i
resoconti passati sono in `archivio/`. Il corpus originale conservato lì serve
ancora alla verifica della provenienza; i suoi vecchi risultati non alimentano
l’esperimento attuale.

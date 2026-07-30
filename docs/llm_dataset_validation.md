# Validazione e compatibilità QASM del dataset LLM

Il file JSON è standard e viene generato con `allow_nan=False`. La validazione
semantica consigliata per gli artefatti MQT è:

```bash
python scripts/09_validate_llm_dataset_qiskit.py \
  output/llm_dataset/mqt_pipeline_expected_fidelity.json
```

Il validatore controlla:

- conteggi top-level e identificativi univoci;
- presenza e ordine delle 49 feature;
- checksum SHA-256 dei QASM;
- parsing dei circuiti sorgente e compilato;
- coerenza tra lista dei pass e trace;
- presenza di `terminate` nei record riusciti;
- uguaglianza tra reward terminale e score ricalcolato;
- presenza del device selezionato nel ranking e nel catalogo hardware;
- struttura degli errori e dei timeout.

## Perché servono le estensioni legacy di Qiskit

Alcuni Target MQT usano gate come `rzz`. Qiskit li esporta in OpenQASM 2 come
istruzioni legacy incorporate, anche se non sono dichiarate nel `qelib1.inc`
standard visto dal parser stretto.

Per questo `scripts/08_validate_llm_dataset.py`, che usa il parser OpenQASM 2
stretto, funziona anche come controllo di portabilità e può segnalare:

```text
'rzz' is not defined in this scope
```

Il validatore `09_validate_llm_dataset_qiskit.py` usa invece
`LEGACY_CUSTOM_INSTRUCTIONS`, cioè la configurazione documentata da Qiskit per
rileggere correttamente l'output del suo esportatore storico. Questa è la
validazione appropriata per riprodurre la pipeline MQT Predictor 2.3.0.

Il JSON conserva comunque il nome dei gate, il Target, le metriche e il testo
QASM. Per uno scambio indipendente da Qiskit si potrà aggiungere in seguito
anche una rappresentazione QPY o OpenQASM 3, senza sostituire il QASM 2 usato
dalla pipeline originale.

# Indice ed evidenze RAG

[Indice dell’esperimento](../README.md)

Il RAG recupera casi precedenti simili al circuito richiesto.
Usa 396 esempi ricavati esclusivamente dal train. La somiglianza è calcolata
su 49 caratteristiche numeriche del circuito, con distanza Manhattan esatta.
Non usa la somiglianza del testo generata da un modello linguistico.

| File o gruppo | Funzione |
| --- | --- |
| `index/manifest.json` | Identità dell’indice, numero di punti, versioni e impronte dei dati di origine. |
| `index/transform.json` | Trasformazione delle caratteristiche e divisori calcolati solo sul train. |
| `index/qdrant/` | Archivio persistente Qdrant con vettori ed esempi associati. |
| `verification.json` | Esito della verifica di coerenza dell’indice. |
| `validation_check.json` | Controllo tecnico del recupero sui circuiti validation. Non misura la qualità delle scelte LLM. |
| `dashboard/verification.json` | Verifica della copia usata per ispezionare i dati. |
| `dashboard/inspect_copy.py` | Programma della prova di ispezione della copia. |
| `audit/` | Dati prima e dopo l’integrazione, confronti di integrità, comandi e registri delle verifiche. |
| `.index-build-*/` | Directory temporanee di costruzioni precedenti, da interpretare attraverso i registri. |

## Come leggere l’area delle verifiche

In `audit/`, i file JSON conservano inventari, confronti di impronte e
risultati dei controlli. I file `.log` conservano gli output dei comandi;
`uv_before.lock` e `git_before.bin` sono fotografie tecniche iniziali.

I programmi `baseline.py`, `probe_corpus.py`, `inspect_inputs.py`,
`assess_integrity.py`, `integrity_after.py`, `check_lock.py` e
`final_checks.py` documentano le verifiche di quella attività.
`update_legacy_tests.py`, `update_docs.py` e `fix_client_lifecycle.py`
sono strumenti delle modifiche svolte allora: non sono il punto di avvio
corrente del sistema.

Per costruire, verificare o interrogare il recupero si usano i comandi descritti
nella [guida del prototipo](../../../../prototype/README.md) e negli
[script](../../../../scripts/README.md).

# Dati storici

`expected_fidelity/` contiene le prime prove con la metrica di fedeltà attesa.
Il suo [README storico](expected_fidelity/README.md) descrive il periodo originale.

| Gruppo | Funzione |
| --- | --- |
| `expected_fidelity/pilot/` | Prova ridotta, viste per dispositivo e rapporti generati. |
| `expected_fidelity/full/split_manifest.json` | Partizione originale dei 600 circuiti, tuttora verificata dalla v2. |
| `expected_fidelity/full/circuits/` | Sorgenti QASM originali, divisi per partizione. |
| Cartelle dei dispositivi sotto `full/` | Risultati della fase precedente, conservati per ricostruirla. |
| `reports/`, CSV e JSON/JSONL | Resoconti, tabelle e registri generati dalle prove storiche. |

Le numerose cartelle di circuiti e risultati seguono lo stesso formato.
Non contengono nuovi componenti software da avviare. Il test rimane protetto
anche se i sorgenti originali sono fisicamente presenti.

# Modelli addestrati

[Indice dell’esperimento](../README.md)

Qui si conservano le copie canoniche dei modelli usati dal confronto MQT Predictor.
I salvataggi intermedi sono in [checkpoints/](../checkpoints/README.md).

| Gruppo | Funzione |
| --- | --- |
| `rl/model_expected_fidelity_<dispositivo>.zip` | Politica RL che sceglie i passi di compilazione per un dispositivo. |
| `rl/model_expected_fidelity_<dispositivo>.metadata.json` | Identità del modello, seed, passi compiuti, versioni, Target e provenienza dei circuiti. |

Il modello RL non sceglie tra dispositivi. Il classificatore supervisionato
di MQT Predictor dovrà imparare questa scelta dal Training set costruito
con i modelli RL dei cinque dispositivi.

Nella ricognizione del 15 settembre 2026 è presente il modello canonico
Quantinuum H2 56 con i suoi metadati; non risultano qui gli altri quattro
modelli finali o il classificatore ML. Vedere lo
[stato dell’esperimento](../README.md).

Gli archivi possono essere grandi e avere copie operative nel pacchetto
installato. Vanno preservati prima di ricreare l’ambiente Python.

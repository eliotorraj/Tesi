# Registri di esecuzione

[Indice dell’esperimento](../README.md)

I registri aiutano a capire come si è svolto un lavoro e dove si è interrotto.
Non sostituiscono i modelli finali o i risultati del Dataset.

| Gruppo | Contenuto |
| --- | --- |
| `rl/model_expected_fidelity_<dispositivo>/<esecuzione>/monitor.csv` | Ricompense, lunghezze e tempi degli episodi RL. |
| `rl/.../resume-*.monitor.csv` | Continuazione del monitor dopo una ripresa, distinta dal tentativo iniziale. |
| `rl/.../MaskablePPO_*/events.out.tfevents.*` | Misure leggibili con TensorBoard per seguire l’addestramento. |
| `qiskit/*.json` | Metadati delle invocazioni di generazione del Dataset. |
| `qiskit/*.log` | Messaggi prodotti durante quelle invocazioni. |

Un file iniziale o quasi vuoto dimostra solo che la registrazione è iniziata.
Per stabilire se un addestramento è concluso si controllano anche
[modello e metadati](../models/README.md).
I registri delle chiamate LLM sono in [llm_selection/](../llm_selection/README.md).

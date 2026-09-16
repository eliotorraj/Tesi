# Cache delle compilazioni Qiskit

[Indice dell’esperimento](../README.md)

Questa cartella conserva il lavoro già svolto per evitare di ripetere
compilazioni identiche. La cache appartiene a questo esperimento.

| Gruppo | Contenuto |
| --- | --- |
| `expected_fidelity/runs/run_<impronta>.json` | Esito di un tentativo identificato da circuito, Target, configurazione, seed e condizioni della prova. |
| `expected_fidelity/compiled_qasm/run_<impronta>.qasm` | Circuito compilato associato a un tentativo riuscito. |

Anche timeout ed errori sono risultati da conservare. Un timeout terminale
non è un tentativo mancante da ripetere automaticamente.

Gli script di generazione riuniscono questi record nei JSONL del
[Dataset](../../../../datasets/README.md). I risultati letti dalla cache
restano distinguibili dalle nuove esecuzioni, soprattutto nei tempi.

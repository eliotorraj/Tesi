# Dataset corrente: cinque dispositivi

Questa cartella raccoglie il confronto Qiskit usato per costruire il Dataset
RAG e per valutare le decisioni successive.

Si parte da un circuito e si provano dodici configurazioni su ogni dispositivo
compatibile. Ogni configurazione usa tre seed. Lo score stima la fedeltà attesa
sui Target sintetici di MQT Bench: non misura un’esecuzione su hardware reale.

## Come leggere le cartelle

Il contenuto attivo è in `expected_fidelity/full/`.
`expected_fidelity` indica la metrica; `full` indica il corpus dell’esperimento.
La parola `full` non significa che il test sia stato aperto.

| Percorso sotto `expected_fidelity/full/` | A cosa serve |
| --- | --- |
| `circuits/train/*.qasm` | Copie operative dei 422 circuiti train. |
| `circuits/validation/*.qasm` | Copie operative degli 88 circuiti validation. |
| `ibm_falcon_27/`, `ibm_falcon_127/`, `ibm_heron_133/`, `ibm_heron_156/`, `quantinuum_h2_56/` | Risultati separati per dispositivo. |
| `global/` | Vista riunita dei cinque dispositivi e Dataset RAG effettivamente usato. |
| `device_comparison.csv`, `device_comparison.md` | Confronti esportati a questo livello. Per la vista riunita usare i report in `global/reports/`. |

Il corpus originale comprende anche 90 circuiti test. I riferimenti sono nel
manifest degli [artefatti](../../../artifacts/README.md); i sorgenti originali
restano nell’archivio e i percorsi logici del manifest non vanno riscritti.

## File comuni alle cartelle dei dispositivi

| File o gruppo | A cosa serve |
| --- | --- |
| `split_manifest.json` | Identità dei circuiti e assegnazione a train, validation e test. |
| `qiskit_runs.jsonl` | Un record per tentativo: circuito, dispositivo, configurazione, seed, score, tempi ed esito. |
| `qiskit_configuration_aggregates.jsonl` | Riunisce i tre seed di una configurazione. Solo tre successi consentono uno score confrontabile. |
| `rag_examples.jsonl` | Esempi ricavati dai circuiti train. Le viste per dispositivo sono intermedie. |
| `generation_status.json` | Tentativi previsti, disponibili e mancanti; indica se la generazione è completa. |
| `dataset_statistics.json` | Conteggi e provenienza della vista prodotta. |
| `reports/full_summary.json`, `reports/full_report.md` | Riepilogo completo, leggibile da programma e da persona. |
| `reports/circuit_statistics.csv` | Una riga per circuito compatibile: copertura, successi, tempi e migliore configurazione disponibile. |
| `reports/configuration_statistics.csv` | Riepilogo per configurazione Qiskit. |
| `reports/failure_details.csv` | Elenco dei tentativi non riusciti, compresi i timeout. |

## Vista globale

`global/qiskit_runs.jsonl` e `global/qiskit_configuration_aggregates.jsonl`
riuniscono i risultati per dispositivo.
`global/rag_examples.jsonl` contiene gli esempi recuperati dal prototipo:
un esempio per sorgente train distinto, con dispositivo vincente e fino a tre
configurazioni valide di quel dispositivo.

`global/dataset_statistics.json` registra i conteggi della vista.
`global/reports/device_comparison.csv` e `.md` confrontano i dispositivi;
`failure_details.csv` conserva i fallimenti.

## Situazione verificata il 15 settembre 2026

- Corpus: 600 circuiti, divisi in 422 train, 88 validation e 90 test.
- Matrice Qiskit disponibile: 510 circuiti train e validation.
- Tentativi: 87.120, di cui 82.621 riusciti e 4.499 timeout; nessun tentativo mancante.
- Aggregati: 29.040, di cui 27.360 ammissibili al confronto.
- Dataset RAG globale: 396 esempi train; i 26 alias byte-identici non aggiungono altri esempi.
- Il sottoinsieme compatibile con tutti i cinque dispositivi comprende 410 circuiti.

Completare la matrice significa registrare tutti gli esiti, inclusi i timeout.
Non significa che ogni circuito abbia un riferimento esaustivo valido.
Il protocollo richiede tutti i tentativi riusciti per calcolare tale riferimento.
I risultati della selezione LLM e del confronto finale non sono questi conteggi.

Le regole complete sono nel [protocollo](../../../docs/protocollo_sperimentale.md).

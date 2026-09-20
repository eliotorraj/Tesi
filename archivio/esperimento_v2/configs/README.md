# Configurazioni dell’esperimento

Questa cartella raccoglie le scelte comuni che il codice deve rispettare.
I file JSON sono letti dai programmi; le regole e le motivazioni sono nel
[protocollo sperimentale](../docs/protocollo_sperimentale.md).

| File | A cosa serve |
| --- | --- |
| [qiskit_dataset_configurations_v2.json](qiskit_dataset_configurations_v2.json) | Definisce i cinque dispositivi, le dodici configurazioni Qiskit, i tre seed, la metrica, le versioni richieste e le impronte dei Target. Fissa anche 100 secondi per tentativo e sei processi. |
| [experiment_methods_v2.json](experiment_methods_v2.json) | Registra i tre ruoli LLM del confronto finale: modello locale con RAG, stesso modello senza RAG e modello di frontiera. Contiene anche il seed della scelta casuale. |

Una configurazione Qiskit combina livello di ottimizzazione, disposizione
iniziale dei qubit e metodo per rispettare i collegamenti del dispositivo.

Il file dei metodi finali contiene ancora valori da completare
(`status: unconfigured` nella ricognizione del 15 settembre 2026).
I profili delle prove tecniche LLM non costituiscono automaticamente la scelta
finale. Questa si decide sulla validation e si congela prima del test.

Le impostazioni delle singole prove e le revisioni scartate restano negli
[artefatti dell’esperimento](../artifacts/README.md).

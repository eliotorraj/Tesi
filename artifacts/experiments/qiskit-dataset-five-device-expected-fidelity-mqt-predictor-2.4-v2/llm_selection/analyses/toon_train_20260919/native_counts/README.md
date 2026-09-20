# Token dei prompt sui cinque circuiti train

Misure native per modello, template completo e schema incluso. Nessuna inferenza.
JSON ridotto: richieste realmente archiviate, verificate confrontando tutti gli ID dei token.
Originale: formato precedente v2 ricostruito; il campo original_v2_kind indica eventuali corrispondenze esatte.
TOON: richiesta preparata, non ancora inviata. Non si misura il consumo delle future risposte o correzioni.

| Modello | Circuito | Precedente v2 | JSON ridotto | Ridotto + TOON | Risparmio su JSON |
|---|---|---:|---:|---:|---:|
| qwen | ae_indep_qiskit_60 | 75193 | 11382 | 10436 | 8.31% |
| qwen | dj_indep_tket_2 | 34318 | 11667 | 10771 | 7.68% |
| qwen | portfoliovqe_indep_qiskit_6 | 36265 | 12692 | 11718 | 7.67% |
| qwen | su2random_indep_qiskit_50 | 90831 | 12458 | 11403 | 8.47% |
| qwen | su2random_indep_tket_50 | 91516 | 12488 | 11434 | 8.44% |
| phi | ae_indep_qiskit_60 | 59791 | 8657 | 8259 | 4.60% |
| phi | dj_indep_tket_2 | 28506 | 9063 | 8733 | 3.64% |
| phi | portfoliovqe_indep_qiskit_6 | 29961 | 9853 | 9436 | 4.23% |
| phi | su2random_indep_qiskit_50 | 75207 | 9636 | 9121 | 5.34% |
| phi | su2random_indep_tket_50 | 75895 | 9635 | 9121 | 5.33% |
| gemma | ae_indep_qiskit_60 | 77738 | 12078 | 10784 | 10.71% |
| gemma | dj_indep_tket_2 | 37296 | 12395 | 11169 | 9.89% |
| gemma | portfoliovqe_indep_qiskit_6 | 39276 | 13514 | 12293 | 9.04% |
| gemma | su2random_indep_qiskit_50 | 93871 | 13280 | 11986 | 9.74% |
| gemma | su2random_indep_tket_50 | 94833 | 13311 | 12017 | 9.72% |

Il JSON integrale senza alias, con la precedente regola esatta del grafo completo, è contato separatamente in original_full_json.
Conteggi e percentuali aggregate sono in report.json. Cinque circuiti train non misurano generalizzazione.

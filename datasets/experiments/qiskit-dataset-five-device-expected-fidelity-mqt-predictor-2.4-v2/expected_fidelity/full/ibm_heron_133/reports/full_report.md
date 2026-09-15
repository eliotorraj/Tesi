# Dataset Qiskit full — ibm_heron_133

Scheda generata automaticamente dagli artefatti del Dataset. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 133 |
| Hash target | 2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3 |
| Qiskit | 2.5.0 |
| MQT Bench | 2.2.3 |
| MQT Predictor | 2.4.0 |
| Circuiti totali | 510 |
| Circuiti compatibili | 510 |
| Circuiti incompatibili | 0 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker nei risultati | 6 |
| Timeout nei risultati (s) | 100 |
| Fonte dei parametri | run_provenance |
| Cache hit | 18360 |
| Durata invocazione | 8.200 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati. I parametri nei risultati provengono dai singoli tentativi, quando disponibili; per i vecchi dati senza questa informazione si usa lo stato della generazione.



## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 18360 | - |
| Osservati | 18360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 17108 | 93.2% |
| Failure | 0 | 0.0% |
| Timeout | 1252 | 6.8% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 17108 | 0.007 | 0.020 | 1.886 | 12.290 | 99.835 |
| Non-lookahead | 15299 | 0.007 | 0.019 | 0.137 | 0.271 | 22.098 |
| Lookahead | 1809 | 0.009 | 8.113 | 16.679 | 59.216 | 99.835 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 1530/1530 | 0 | 0.020 | 0.240 | 3.550 | 510 | 103 | 103 | 456 |
| o3_default_default | baseline | 3 | default | default | 1530/1530 | 0 | 0.027 | 2.545 | 19.659 | 510 | 390 | 467 | 504 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 1530/1530 | 0 | 0.015 | 0.162 | 0.480 | 510 | 2 | 2 | 119 |
| o2_dense_sabre | layout | 2 | dense | sabre | 1530/1530 | 0 | 0.018 | 0.085 | 0.360 | 510 | 9 | 9 | 126 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 1530/1530 | 0 | 0.015 | 0.086 | 0.455 | 510 | 0 | 0 | 22 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 1530/1530 | 0 | 0.018 | 0.259 | 1.448 | 510 | 3 | 4 | 117 |
| o3_dense_sabre | layout | 3 | dense | sabre | 1530/1530 | 0 | 0.021 | 0.167 | 0.645 | 510 | 3 | 12 | 117 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 1530/1530 | 0 | 0.017 | 0.196 | 0.898 | 510 | 0 | 0 | 38 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 903/1530 | 627 | 8.161 | 59.747 | 99.172 | 282 | 0 | 1 | 6 |
| o2_sabre_basic | routing | 2 | sabre | basic | 1529/1530 | 1 | 0.027 | 0.655 | 22.098 | 509 | 0 | 1 | 2 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 906/1530 | 624 | 7.858 | 59.077 | 99.835 | 286 | 0 | 2 | 18 |
| o3_sabre_basic | routing | 3 | sabre | basic | 1530/1530 | 0 | 0.029 | 1.186 | 12.915 | 510 | 0 | 2 | 5 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.045 | 0.305 | 0.314 | 10 | o3_default_default |
| ae_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.031 | 0.056 | 0.069 | 10 | o3_default_default |
| ae_indep_qiskit_12 | train | 12 | 30/36 | 6 | 0.038 | 0.076 | 0.088 | 10 | o3_default_default |
| ae_indep_qiskit_13 | train | 13 | 30/36 | 6 | 0.035 | 0.078 | 0.087 | 10 | o2_default_default |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.017 | 0.019 | 12 | o3_default_default |
| ae_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 5.658 | 5.899 | 12 | o3_default_default |
| ae_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.126 | 0.442 | 0.530 | 10 | o3_default_default |
| ae_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.018 | 17.114 | 19.718 | 12 | o2_dense_sabre |
| ae_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.146 | 0.634 | 0.725 | 10 | o3_default_default |
| ae_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.019 | 12.945 | 14.167 | 12 | o3_default_default |
| ae_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.294 | 7.552 | 7.731 | 10 | o2_default_default |
| ae_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.031 | 20.115 | 20.836 | 10 | o3_default_default |
| ae_indep_qiskit_60 | train | 60 | 29/36 | 7 | 0.311 | 12.684 | 14.065 | 9 | o3_default_default |
| ae_indep_qiskit_7 | train | 7 | 34/36 | 2 | 0.021 | 55.289 | 90.755 | 10 | o3_default_default |
| ae_indep_qiskit_8 | train | 8 | 32/36 | 4 | 0.017 | 25.887 | 60.427 | 10 | o3_default_default |
| ae_indep_qiskit_9 | train | 9 | 31/36 | 5 | 0.021 | 0.037 | 88.475 | 10 | o2_default_default |
| ae_indep_tket_10 | train | 10 | 30/36 | 6 | 0.020 | 0.050 | 0.053 | 10 | o3_default_default |
| ae_indep_tket_11 | train | 11 | 30/36 | 6 | 0.024 | 0.050 | 0.055 | 10 | o3_default_default |
| ae_indep_tket_12 | train | 12 | 30/36 | 6 | 0.023 | 0.053 | 0.063 | 10 | o3_default_default |
| ae_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.016 | 0.017 | 12 | o2_default_default |
| ae_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 5.617 | 5.864 | 12 | o3_default_default |
| ae_indep_tket_30 | train | 30 | 30/36 | 6 | 0.094 | 0.311 | 0.369 | 10 | o3_default_default |
| ae_indep_tket_4 | train | 4 | 36/36 | 0 | 0.018 | 17.597 | 19.163 | 12 | o3_default_default |
| ae_indep_tket_40 | train | 40 | 30/36 | 6 | 0.129 | 0.546 | 0.633 | 10 | o3_default_default |
| ae_indep_tket_5 | train | 5 | 36/36 | 0 | 0.017 | 13.322 | 14.544 | 12 | o3_default_default |
| ae_indep_tket_50 | train | 50 | 30/36 | 6 | 0.225 | 0.811 | 1.080 | 10 | o2_default_default |
| ae_indep_tket_6 | train | 6 | 36/36 | 0 | 0.020 | 22.230 | 28.013 | 12 | o3_default_default |
| ae_indep_tket_7 | train | 7 | 34/36 | 2 | 0.018 | 55.280 | 97.896 | 10 | o3_default_default |
| ae_indep_tket_8 | train | 8 | 32/36 | 4 | 0.018 | 23.741 | 60.854 | 10 | o3_default_default |
| ae_indep_tket_9 | train | 9 | 31/36 | 5 | 0.019 | 0.044 | 89.718 | 10 | o2_default_default |
| dj_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.017 | 14.908 | 15.251 | 12 | o2_default_default |
| dj_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.017 | 15.736 | 16.981 | 12 | o2_default_default |
| dj_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.018 | 18.226 | 18.888 | 12 | o2_default_default |
| dj_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.021 | 20.960 | 21.875 | 12 | o3_default_default |
| dj_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.021 | 26.227 | 27.134 | 12 | o3_default_default |
| dj_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.021 | 27.280 | 29.424 | 12 | o3_default_default |
| dj_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.022 | 28.911 | 29.464 | 12 | o3_default_default |
| dj_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.022 | 28.737 | 30.639 | 12 | o3_default_default |
| dj_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.023 | 34.728 | 36.908 | 12 | o3_default_default |
| dj_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.021 | 40.662 | 42.522 | 12 | o3_default_default |
| dj_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| dj_indep_qiskit_20 | train | 20 | 30/36 | 6 | 0.020 | 0.040 | 0.042 | 10 | o3_default_default |
| dj_indep_qiskit_21 | train | 21 | 32/36 | 4 | 0.019 | 18.740 | 42.168 | 10 | o3_default_default |
| dj_indep_qiskit_22 | train | 22 | 34/36 | 2 | 0.022 | 44.054 | 44.265 | 10 | o3_default_default |
| dj_indep_qiskit_23 | train | 23 | 34/36 | 2 | 0.021 | 45.385 | 46.688 | 10 | o3_default_default |
| dj_indep_qiskit_24 | train | 24 | 32/36 | 4 | 0.022 | 22.797 | 55.191 | 10 | o3_default_default |
| dj_indep_qiskit_25 | train | 25 | 34/36 | 2 | 0.022 | 60.313 | 60.898 | 10 | o3_default_default |
| dj_indep_qiskit_26 | train | 26 | 32/36 | 4 | 0.024 | 26.512 | 60.257 | 10 | o3_default_default |
| dj_indep_qiskit_27 | train | 27 | 32/36 | 4 | 0.027 | 28.343 | 63.715 | 10 | o3_default_default |
| dj_indep_qiskit_28 | train | 28 | 30/36 | 6 | 0.020 | 0.086 | 0.099 | 10 | o3_default_default |
| dj_indep_qiskit_29 | train | 29 | 34/36 | 2 | 0.026 | 67.190 | 72.863 | 10 | o3_default_default |
| dj_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 0.019 | 0.021 | 12 | o3_default_default |
| dj_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.019 | 0.123 | 0.139 | 10 | o3_default_default |
| dj_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| dj_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.024 | 0.573 | 0.677 | 10 | o3_default_default |
| dj_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 4.409 | 5.030 | 12 | o3_default_default |
| dj_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.023 | 2.710 | 2.875 | 10 | o3_default_default |
| dj_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.014 | 9.063 | 10.383 | 12 | o3_default_default |
| dj_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.028 | 8.726 | 12.344 | 10 | o3_default_default |
| dj_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.016 | 8.579 | 10.591 | 12 | o2_dense_sabre |
| dj_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.038 | 16.078 | 16.559 | 10 | o3_default_default |
| dj_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.016 | 8.174 | 34.641 | 12 | o2_default_default |
| dj_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.036 | 16.559 | 17.304 | 10 | o3_default_default |
| dj_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.015 | 12.761 | 19.897 | 12 | o3_default_default |
| dj_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.040 | 16.982 | 17.624 | 10 | o3_default_default |
| dj_indep_tket_10 | train | 10 | 36/36 | 0 | 0.016 | 15.753 | 16.039 | 12 | o2_default_default |
| dj_indep_tket_11 | train | 11 | 36/36 | 0 | 0.017 | 16.298 | 17.056 | 12 | o3_default_default |
| dj_indep_tket_12 | train | 12 | 36/36 | 0 | 0.017 | 17.519 | 19.105 | 12 | o2_default_default |
| dj_indep_tket_13 | train | 13 | 36/36 | 0 | 0.019 | 21.482 | 22.243 | 12 | o3_default_default |
| dj_indep_tket_14 | train | 14 | 36/36 | 0 | 0.020 | 27.114 | 28.697 | 12 | o3_default_default |
| dj_indep_tket_15 | train | 15 | 36/36 | 0 | 0.020 | 28.106 | 28.633 | 12 | o3_default_default |
| dj_indep_tket_16 | train | 16 | 36/36 | 0 | 0.022 | 28.742 | 29.014 | 12 | o3_default_default |
| dj_indep_tket_17 | train | 17 | 36/36 | 0 | 0.023 | 29.691 | 30.385 | 12 | o3_default_default |
| dj_indep_tket_18 | train | 18 | 36/36 | 0 | 0.022 | 35.215 | 36.011 | 12 | o3_default_default |
| dj_indep_tket_19 | train | 19 | 36/36 | 0 | 0.019 | 41.514 | 41.724 | 12 | o3_default_default |
| dj_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.016 | 0.019 | 12 | o3_default_default |
| dj_indep_tket_20 | train | 20 | 30/36 | 6 | 0.019 | 0.037 | 0.044 | 10 | o3_default_default |
| dj_indep_tket_21 | train | 21 | 32/36 | 4 | 0.020 | 19.451 | 43.446 | 10 | o3_default_default |
| dj_indep_tket_22 | train | 22 | 34/36 | 2 | 0.022 | 44.085 | 45.829 | 10 | o3_default_default |
| dj_indep_tket_23 | train | 23 | 34/36 | 2 | 0.020 | 45.698 | 46.251 | 10 | o3_default_default |
| dj_indep_tket_24 | train | 24 | 32/36 | 4 | 0.020 | 23.334 | 52.645 | 10 | o3_default_default |
| dj_indep_tket_25 | train | 25 | 34/36 | 2 | 0.022 | 56.983 | 59.485 | 10 | o3_default_default |
| dj_indep_tket_26 | train | 26 | 32/36 | 4 | 0.024 | 26.446 | 59.779 | 10 | o3_default_default |
| dj_indep_tket_27 | train | 27 | 32/36 | 4 | 0.020 | 27.018 | 60.976 | 10 | o3_default_default |
| dj_indep_tket_28 | train | 28 | 30/36 | 6 | 0.024 | 0.095 | 0.102 | 10 | o3_default_default |
| dj_indep_tket_29 | train | 29 | 34/36 | 2 | 0.023 | 69.442 | 71.803 | 10 | o3_default_default |
| dj_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 0.016 | 0.018 | 12 | o3_default_default |
| dj_indep_tket_30 | train | 30 | 30/36 | 6 | 0.025 | 0.139 | 0.156 | 10 | o3_default_default |
| dj_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| dj_indep_tket_40 | train | 40 | 30/36 | 6 | 0.027 | 0.547 | 0.686 | 10 | o3_default_default |
| dj_indep_tket_5 | train | 5 | 36/36 | 0 | 0.015 | 4.954 | 5.329 | 12 | o3_default_default |
| dj_indep_tket_50 | train | 50 | 30/36 | 6 | 0.027 | 2.716 | 2.796 | 10 | o3_default_default |
| dj_indep_tket_6 | train | 6 | 36/36 | 0 | 0.015 | 9.157 | 10.570 | 12 | o3_default_default |
| dj_indep_tket_60 | train | 60 | 30/36 | 6 | 0.030 | 9.834 | 12.635 | 10 | o3_default_default |
| dj_indep_tket_7 | train | 7 | 36/36 | 0 | 0.016 | 8.679 | 10.586 | 12 | o3_default_default |
| dj_indep_tket_70 | train | 70 | 30/36 | 6 | 0.037 | 16.198 | 16.819 | 10 | o3_default_default |
| dj_indep_tket_8 | train | 8 | 36/36 | 0 | 0.016 | 7.926 | 35.492 | 12 | o2_default_default |
| dj_indep_tket_80 | train | 80 | 30/36 | 6 | 0.036 | 16.490 | 16.857 | 10 | o3_default_default |
| dj_indep_tket_9 | train | 9 | 36/36 | 0 | 0.016 | 12.806 | 19.694 | 12 | o3_default_default |
| dj_indep_tket_90 | train | 90 | 30/36 | 6 | 0.034 | 16.513 | 17.170 | 10 | o3_default_default |
| graphstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.016 | 9.365 | 15.701 | 12 | o2_default_default |
| graphstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.018 | 11.521 | 14.215 | 12 | o3_default_default |
| graphstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.015 | 13.367 | 17.044 | 12 | o2_default_default |
| graphstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.018 | 11.070 | 13.210 | 12 | o3_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.018 | 18.480 | 19.844 | 12 | o3_default_default |
| graphstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.021 | 20.831 | 23.714 | 12 | o3_default_default |
| graphstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.019 | 19.356 | 30.965 | 12 | o3_default_default |
| graphstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.020 | 21.805 | 25.782 | 12 | o3_default_default |
| graphstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.020 | 24.128 | 32.577 | 12 | o3_default_default |
| graphstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.023 | 24.143 | 25.156 | 12 | o3_default_default |
| graphstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.021 | 41.081 | 47.936 | 12 | o2_default_default |
| graphstate_indep_qiskit_21 | train | 21 | 35/36 | 1 | 0.025 | 32.444 | 37.109 | 11 | o2_default_default |
| graphstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.024 | 37.710 | 39.819 | 12 | o3_default_default |
| graphstate_indep_qiskit_23 | train | 23 | 35/36 | 1 | 0.023 | 29.507 | 39.727 | 11 | o2_sabre_sabre |
| graphstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.025 | 44.605 | 51.333 | 12 | o2_default_default |
| graphstate_indep_qiskit_25 | train | 25 | 35/36 | 1 | 0.027 | 39.006 | 47.838 | 11 | o3_default_default |
| graphstate_indep_qiskit_26 | train | 26 | 35/36 | 1 | 0.026 | 53.394 | 79.152 | 11 | o3_default_default |
| graphstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.029 | 43.612 | 48.292 | 12 | o3_default_default |
| graphstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.027 | 50.565 | 61.770 | 12 | o3_default_default |
| graphstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.028 | 61.399 | 65.631 | 12 | o2_default_default |
| graphstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.014 | 3.125 | 3.360 | 12 | o3_default_default |
| graphstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.026 | 60.673 | 76.509 | 12 | o3_default_default |
| graphstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.015 | 5.890 | 6.320 | 12 | o3_default_default |
| graphstate_indep_qiskit_40 | train | 40 | 32/36 | 4 | 0.027 | 32.175 | 96.095 | 10 | o3_sabre_sabre |
| graphstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.016 | 7.082 | 7.941 | 12 | o2_dense_sabre |
| graphstate_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.031 | 0.145 | 0.346 | 10 | o3_sabre_sabre |
| graphstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 7.163 | 8.126 | 12 | o3_default_default |
| graphstate_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.035 | 16.889 | 18.093 | 10 | o3_default_default |
| graphstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.018 | 7.214 | 7.487 | 12 | o3_default_default |
| graphstate_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.033 | 18.140 | 18.430 | 10 | o3_default_default |
| graphstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 7.403 | 7.762 | 12 | o3_default_default |
| graphstate_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.062 | 1.295 | 1.317 | 10 | o3_default_default |
| graphstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.019 | 7.406 | 7.464 | 12 | o3_default_default |
| graphstate_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.070 | 18.924 | 19.542 | 10 | o3_default_default |
| graphstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.018 | 10.481 | 13.475 | 12 | o3_default_default |
| graphstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.020 | 15.658 | 16.704 | 12 | o3_default_default |
| graphstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.018 | 15.157 | 16.108 | 12 | o2_default_default |
| graphstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.019 | 17.046 | 19.908 | 12 | o3_default_default |
| graphstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.020 | 8.480 | 13.907 | 12 | o3_default_default |
| graphstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.018 | 15.571 | 16.953 | 12 | o3_default_default |
| graphstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.021 | 23.506 | 26.457 | 12 | o3_default_default |
| graphstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.020 | 21.632 | 26.229 | 12 | o3_default_default |
| graphstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.021 | 20.891 | 33.838 | 12 | o3_default_default |
| graphstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.021 | 27.508 | 30.116 | 12 | o2_default_default |
| graphstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.019 | 32.744 | 42.599 | 12 | o2_default_default |
| graphstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.024 | 27.757 | 35.007 | 12 | o3_default_default |
| graphstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.025 | 39.129 | 51.277 | 12 | o3_default_default |
| graphstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.024 | 42.793 | 46.662 | 12 | o3_default_default |
| graphstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.025 | 37.220 | 38.949 | 12 | o3_default_default |
| graphstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.026 | 39.732 | 41.754 | 12 | o3_default_default |
| graphstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.026 | 48.863 | 58.759 | 12 | o3_default_default |
| graphstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.026 | 38.355 | 69.772 | 12 | o3_default_default |
| graphstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.028 | 46.317 | 50.895 | 12 | o3_default_default |
| graphstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.029 | 47.779 | 54.090 | 12 | o2_default_default |
| graphstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 3.075 | 3.295 | 12 | o3_default_default |
| graphstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.029 | 60.739 | 71.903 | 12 | o3_default_default |
| graphstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 5.791 | 6.279 | 12 | o3_default_default |
| graphstate_indep_tket_40 | train | 40 | 33/36 | 3 | 0.024 | 92.607 | 96.567 | 10 | o3_default_default |
| graphstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.015 | 6.609 | 6.942 | 12 | o2_dense_sabre |
| graphstate_indep_tket_50 | train | 50 | 30/36 | 6 | 0.035 | 18.104 | 19.075 | 10 | o3_default_default |
| graphstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 7.026 | 43.831 | 12 | o3_default_default |
| graphstate_indep_tket_60 | train | 60 | 30/36 | 6 | 0.029 | 17.971 | 19.264 | 10 | o3_default_default |
| graphstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.015 | 7.103 | 10.053 | 12 | o3_default_default |
| graphstate_indep_tket_70 | train | 70 | 30/36 | 6 | 0.042 | 18.616 | 19.049 | 10 | o3_default_default |
| graphstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 7.550 | 7.982 | 12 | o3_default_default |
| graphstate_indep_tket_80 | train | 80 | 30/36 | 6 | 0.060 | 0.392 | 0.425 | 10 | o3_default_default |
| graphstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.018 | 7.463 | 7.843 | 12 | o2_default_default |
| graphstate_indep_tket_90 | train | 90 | 30/36 | 6 | 0.068 | 18.277 | 19.659 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 42.381 | 53.125 | 12 | o3_default_default |
| portfolioqaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.016 | 67.338 | 99.835 | 12 | o3_default_default |
| portfolioqaoa_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.028 | 0.033 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.017 | 0.037 | 0.042 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.019 | 0.042 | 0.046 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 40.081 | 52.759 | 12 | o3_default_default |
| portfolioqaoa_indep_tket_4 | train | 4 | 34/36 | 2 | 0.016 | 39.848 | 55.937 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_5 | train | 5 | 30/36 | 6 | 0.017 | 0.035 | 0.182 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_6 | train | 6 | 30/36 | 6 | 0.018 | 0.039 | 0.046 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_7 | train | 7 | 30/36 | 6 | 0.019 | 0.049 | 0.057 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.028 | 0.078 | 0.091 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.028 | 0.092 | 0.104 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.014 | 32.374 | 43.005 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.015 | 54.700 | 79.853 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.027 | 0.030 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.017 | 0.034 | 0.036 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.018 | 0.050 | 0.193 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.019 | 0.054 | 0.062 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.022 | 0.074 | 0.077 | 10 | o3_default_default |
| portfoliovqe_indep_tket_10 | train | 10 | 30/36 | 6 | 0.025 | 0.073 | 0.090 | 10 | o3_default_default |
| portfoliovqe_indep_tket_11 | train | 11 | 30/36 | 6 | 0.026 | 0.085 | 0.102 | 10 | o3_default_default |
| portfoliovqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 32.237 | 42.414 | 12 | o3_default_default |
| portfoliovqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.016 | 56.085 | 81.135 | 12 | o3_default_default |
| portfoliovqe_indep_tket_5 | train | 5 | 30/36 | 6 | 0.015 | 0.025 | 0.027 | 10 | o3_default_default |
| portfoliovqe_indep_tket_6 | train | 6 | 30/36 | 6 | 0.016 | 0.031 | 0.035 | 10 | o3_default_default |
| portfoliovqe_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.037 | 0.044 | 10 | o3_default_default |
| portfoliovqe_indep_tket_8 | train | 8 | 30/36 | 6 | 0.020 | 0.045 | 0.062 | 10 | o3_default_default |
| portfoliovqe_indep_tket_9 | train | 9 | 30/36 | 6 | 0.021 | 0.066 | 0.089 | 10 | o3_default_default |
| qaoa_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.017 | 25.134 | 26.750 | 12 | o3_default_default |
| qaoa_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.019 | 8.905 | 9.120 | 12 | o3_default_default |
| qaoa_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.018 | 17.144 | 54.606 | 12 | o3_default_default |
| qaoa_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.023 | 11.199 | 16.852 | 12 | o3_default_default |
| qaoa_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.026 | 47.443 | 48.959 | 12 | o3_default_default |
| qaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 20.027 | 20.908 | 12 | o3_default_default |
| qaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.015 | 7.492 | 7.619 | 12 | o3_default_default |
| qaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.017 | 11.951 | 12.906 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 20.127 | 24.084 | 12 | o3_default_default |
| qaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.018 | 9.934 | 10.110 | 12 | o3_default_default |
| qaoa_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.020 | 17.282 | 18.108 | 12 | o3_default_default |
| qaoa_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.021 | 17.620 | 18.450 | 12 | o3_default_default |
| qaoa_indep_tket_10 | train | 10 | 36/36 | 0 | 0.020 | 25.290 | 27.572 | 12 | o3_default_default |
| qaoa_indep_tket_11 | train | 11 | 36/36 | 0 | 0.022 | 9.137 | 9.970 | 12 | o3_default_default |
| qaoa_indep_tket_12 | train | 12 | 36/36 | 0 | 0.017 | 16.619 | 56.629 | 12 | o3_default_default |
| qaoa_indep_tket_13 | train | 13 | 36/36 | 0 | 0.022 | 11.292 | 16.265 | 12 | o3_default_default |
| qaoa_indep_tket_14 | train | 14 | 36/36 | 0 | 0.024 | 46.673 | 48.997 | 12 | o3_default_default |
| qaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 19.591 | 19.836 | 12 | o3_default_default |
| qaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 7.650 | 7.932 | 12 | o3_default_default |
| qaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.016 | 11.434 | 13.118 | 12 | o2_dense_sabre |
| qaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.019 | 20.553 | 23.731 | 12 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.019 | 10.009 | 10.140 | 12 | o3_default_default |
| qaoa_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 17.399 | 18.438 | 12 | o3_default_default |
| qaoa_indep_tket_9 | train | 9 | 36/36 | 0 | 0.020 | 17.304 | 17.671 | 12 | o3_default_default |
| qnn_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.010 | 0.014 | 0.015 | 12 | o3_default_default |
| qnn_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 15.692 | 16.379 | 12 | o3_default_default |
| qnn_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.162 | 0.940 | 1.113 | 10 | o3_default_default |
| qnn_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.019 | 23.160 | 23.730 | 12 | o3_default_default |
| qnn_indep_qiskit_5 | train | 5 | 34/36 | 2 | 0.019 | 60.296 | 93.553 | 10 | o3_default_default |
| qnn_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.018 | 84.278 | 85.833 | 10 | o3_default_default |
| qnn_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.018 | 0.043 | 0.056 | 10 | o3_default_default |
| qnn_indep_tket_2 | train | 2 | 36/36 | 0 | 0.010 | 0.013 | 0.014 | 12 | o3_default_default |
| qnn_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 15.052 | 16.279 | 12 | o3_default_default |
| qnn_indep_tket_30 | train | 30 | 30/36 | 6 | 0.167 | 0.787 | 0.967 | 10 | o3_default_default |
| qnn_indep_tket_4 | train | 4 | 36/36 | 0 | 0.019 | 23.617 | 24.568 | 12 | o3_default_default |
| qnn_indep_tket_5 | train | 5 | 34/36 | 2 | 0.017 | 60.348 | 93.829 | 10 | o3_default_default |
| qnn_indep_tket_6 | train | 6 | 34/36 | 2 | 0.018 | 85.368 | 87.692 | 10 | o3_default_default |
| qnn_indep_tket_7 | train | 7 | 30/36 | 6 | 0.019 | 0.051 | 0.057 | 10 | o3_default_default |
| random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.010 | 0.012 | 0.013 | 12 | o2_default_default |
| random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 22.791 | 24.459 | 12 | o3_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.314 | 1.296 | 1.733 | 10 | o2_dense_sabre |
| random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.019 | 31.847 | 38.099 | 12 | o3_default_default |
| random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.018 | 56.722 | 59.455 | 12 | o3_dense_sabre |
| random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.021 | 0.041 | 0.045 | 10 | o3_default_default |
| random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.021 | 0.058 | 0.059 | 10 | o3_default_default |
| random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.022 | 0.053 | 0.057 | 10 | o3_default_default |
| random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.010 | 0.012 | 0.012 | 12 | o2_default_default |
| random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 22.967 | 25.382 | 12 | o3_default_default |
| random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.305 | 1.373 | 1.486 | 10 | o3_dense_sabre |
| random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.024 | 31.798 | 38.047 | 12 | o3_default_default |
| random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.019 | 57.047 | 59.980 | 12 | o3_dense_sabre |
| random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.041 | 0.049 | 10 | o3_default_default |
| random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.051 | 0.056 | 10 | o3_default_default |
| random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.023 | 0.043 | 0.055 | 10 | o3_default_default |
| realamprandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.025 | 0.072 | 0.093 | 10 | o3_default_default |
| realamprandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.026 | 0.091 | 0.100 | 10 | o2_default_default |
| realamprandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.020 | 12 | o3_default_default |
| realamprandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 32.738 | 42.914 | 12 | o3_default_default |
| realamprandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.190 | 1.118 | 1.156 | 10 | o3_default_default |
| realamprandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.019 | 56.304 | 81.495 | 12 | o3_default_default |
| realamprandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.289 | 1.917 | 2.022 | 10 | o3_default_default |
| realamprandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.015 | 0.031 | 0.034 | 10 | o3_default_default |
| realamprandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.642 | 4.912 | 22.098 | 10 | o3_default_default |
| realamprandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.033 | 0.171 | 0.248 | 10 | o3_default_default |
| realamprandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.025 | 0.042 | 0.053 | 10 | o3_default_default |
| realamprandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.026 | 0.069 | 0.081 | 10 | o3_default_default |
| realamprandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.030 | 0.084 | 0.090 | 10 | o3_default_default |
| realamprandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.033 | 0.088 | 0.090 | 10 | o3_default_default |
| realamprandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.031 | 0.102 | 0.111 | 10 | o2_default_default |
| realamprandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.012 | 0.017 | 0.018 | 12 | o3_default_default |
| realamprandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 32.633 | 44.605 | 12 | o3_default_default |
| realamprandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.177 | 1.212 | 1.412 | 10 | o3_default_default |
| realamprandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 57.327 | 84.176 | 12 | o3_default_default |
| realamprandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.309 | 1.933 | 2.114 | 10 | o3_default_default |
| realamprandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.017 | 0.024 | 0.027 | 10 | o3_default_default |
| realamprandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.584 | 4.393 | 4.645 | 10 | o3_default_default |
| realamprandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.018 | 0.031 | 0.039 | 10 | o3_default_default |
| realamprandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.037 | 0.042 | 10 | o3_default_default |
| realamprandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.023 | 0.060 | 0.064 | 10 | o3_default_default |
| realamprandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.030 | 0.077 | 0.085 | 10 | o3_default_default |
| su2random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.016 | 0.017 | 12 | o3_default_default |
| su2random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 33.122 | 43.098 | 12 | o3_default_default |
| su2random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.263 | 1.058 | 1.108 | 10 | o3_default_default |
| su2random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.018 | 57.001 | 82.952 | 12 | o3_default_default |
| su2random_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.307 | 1.842 | 2.178 | 10 | o3_default_default |
| su2random_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.030 | 0.085 | 10 | o3_default_default |
| su2random_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.503 | 4.330 | 4.506 | 10 | o3_default_default |
| su2random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.018 | 0.034 | 0.040 | 10 | o3_default_default |
| su2random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.019 | 0.044 | 0.046 | 10 | o3_default_default |
| su2random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.022 | 0.061 | 0.065 | 10 | o3_default_default |
| su2random_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.029 | 0.084 | 0.098 | 10 | o3_default_default |
| su2random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.012 | 0.018 | 0.023 | 12 | o3_default_default |
| su2random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 33.876 | 44.697 | 12 | o3_default_default |
| su2random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.196 | 1.060 | 1.251 | 10 | o3_default_default |
| su2random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.019 | 58.599 | 86.449 | 12 | o3_default_default |
| su2random_indep_tket_40 | train | 40 | 30/36 | 6 | 0.301 | 1.856 | 2.041 | 10 | o3_default_default |
| su2random_indep_tket_5 | train | 5 | 30/36 | 6 | 0.019 | 0.034 | 0.050 | 10 | o3_default_default |
| su2random_indep_tket_50 | train | 50 | 30/36 | 6 | 0.519 | 4.467 | 4.659 | 10 | o3_default_default |
| su2random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.017 | 0.036 | 0.045 | 10 | o3_default_default |
| su2random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.040 | 0.053 | 10 | o3_default_default |
| su2random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.023 | 0.063 | 0.068 | 10 | o3_default_default |
| su2random_indep_tket_9 | train | 9 | 30/36 | 6 | 0.031 | 0.089 | 0.096 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.031 | 0.099 | 0.112 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.042 | 0.099 | 0.113 | 10 | o2_default_default |
| twolocalrandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.016 | 0.017 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 33.946 | 43.842 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.172 | 1.057 | 1.109 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.017 | 57.772 | 83.311 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.310 | 1.847 | 1.899 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.017 | 0.025 | 0.027 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.499 | 4.549 | 4.796 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.019 | 0.036 | 0.040 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.038 | 0.040 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.026 | 0.057 | 0.066 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.026 | 0.092 | 0.094 | 10 | o3_default_default |
| twolocalrandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.033 | 0.093 | 0.096 | 10 | o3_default_default |
| twolocalrandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.032 | 0.099 | 0.116 | 10 | o2_default_default |
| twolocalrandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.013 | 0.016 | 0.018 | 12 | o3_default_default |
| twolocalrandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 33.375 | 42.426 | 12 | o3_default_default |
| twolocalrandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.176 | 1.064 | 1.201 | 10 | o3_default_default |
| twolocalrandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.018 | 56.171 | 82.614 | 12 | o3_default_default |
| twolocalrandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.315 | 1.774 | 1.918 | 10 | o3_default_default |
| twolocalrandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.016 | 0.029 | 0.030 | 10 | o3_default_default |
| twolocalrandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.571 | 4.286 | 4.969 | 10 | o3_default_default |
| twolocalrandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.034 | 0.035 | 10 | o3_default_default |
| twolocalrandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.035 | 0.045 | 10 | o3_default_default |
| twolocalrandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.027 | 0.064 | 0.067 | 10 | o3_default_default |
| twolocalrandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.029 | 0.091 | 0.095 | 10 | o3_default_default |
| vqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.017 | 0.022 | 0.023 | 12 | o2_default_default |
| vqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.016 | 0.020 | 0.024 | 12 | o2_default_default |
| vqe_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.017 | 0.023 | 0.025 | 12 | o3_default_default |
| vqe_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.017 | 0.025 | 0.027 | 12 | o2_default_default |
| vqe_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.017 | 0.026 | 0.027 | 12 | o2_default_default |
| vqe_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.018 | 0.026 | 0.040 | 12 | o2_default_default |
| vqe_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.019 | 0.034 | 0.038 | 12 | o2_default_default |
| vqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.013 | 0.017 | 0.019 | 12 | o2_default_default |
| vqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 0.016 | 0.018 | 12 | o3_default_default |
| vqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 0.017 | 0.019 | 12 | o2_dense_sabre |
| vqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 0.020 | 0.026 | 12 | o2_default_default |
| vqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.014 | 0.022 | 0.200 | 12 | o2_default_default |
| vqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 0.021 | 0.030 | 12 | o3_default_default |
| vqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.015 | 0.020 | 0.021 | 12 | o3_default_default |
| vqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.016 | 0.020 | 0.023 | 12 | o2_default_default |
| vqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.016 | 0.023 | 0.025 | 12 | o2_default_default |
| vqe_indep_tket_12 | train | 12 | 36/36 | 0 | 0.015 | 0.020 | 0.022 | 12 | o2_default_default |
| vqe_indep_tket_13 | train | 13 | 36/36 | 0 | 0.016 | 0.021 | 0.027 | 12 | o3_default_default |
| vqe_indep_tket_14 | train | 14 | 36/36 | 0 | 0.017 | 0.032 | 0.035 | 12 | o2_default_default |
| vqe_indep_tket_15 | train | 15 | 36/36 | 0 | 0.017 | 0.030 | 0.036 | 12 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.020 | 0.027 | 0.028 | 12 | o2_default_default |
| vqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.013 | 0.018 | 0.020 | 12 | o2_default_default |
| vqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.013 | 0.017 | 0.019 | 12 | o2_default_default |
| vqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.014 | 0.020 | 0.023 | 12 | o2_dense_sabre |
| vqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 0.021 | 0.023 | 12 | o2_default_default |
| vqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.014 | 0.019 | 0.020 | 12 | o2_default_default |
| vqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.016 | 0.020 | 0.021 | 12 | o3_default_default |
| vqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.017 | 0.021 | 0.024 | 12 | o2_default_default |
| wstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.015 | 0.019 | 0.021 | 12 | o2_default_default |
| wstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.015 | 0.022 | 0.024 | 12 | o2_default_default |
| wstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.015 | 0.022 | 0.023 | 12 | o2_default_default |
| wstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.015 | 0.024 | 0.024 | 12 | o2_default_default |
| wstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.016 | 0.020 | 0.022 | 12 | o2_default_default |
| wstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.016 | 0.032 | 0.035 | 12 | o2_default_default |
| wstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.017 | 0.031 | 0.035 | 12 | o2_default_default |
| wstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.020 | 0.035 | 0.040 | 12 | o2_default_default |
| wstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.018 | 0.043 | 0.049 | 12 | o3_default_default |
| wstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.018 | 0.051 | 0.057 | 12 | o3_default_default |
| wstate_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.016 | 12 | o3_default_default |
| wstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.020 | 0.055 | 0.066 | 12 | o3_default_default |
| wstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.020 | 0.080 | 0.087 | 12 | o3_default_default |
| wstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.022 | 0.100 | 0.110 | 12 | o3_default_default |
| wstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.018 | 0.089 | 0.094 | 12 | o2_default_default |
| wstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.019 | 0.104 | 0.113 | 12 | o2_default_default |
| wstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.023 | 0.114 | 0.123 | 12 | o2_default_default |
| wstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.020 | 0.117 | 0.122 | 12 | o2_default_default |
| wstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.022 | 0.128 | 0.140 | 12 | o2_default_default |
| wstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.024 | 0.153 | 0.172 | 12 | o2_default_default |
| wstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.022 | 0.216 | 0.222 | 12 | o2_default_default |
| wstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 0.016 | 0.019 | 12 | o2_default_default |
| wstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.025 | 0.231 | 0.236 | 12 | o3_default_default |
| wstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 0.017 | 0.019 | 12 | o3_default_default |
| wstate_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.029 | 0.288 | 0.299 | 12 | o3_default_default |
| wstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 0.016 | 0.016 | 12 | o2_default_default |
| wstate_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.031 | 0.343 | 0.381 | 12 | o2_default_default |
| wstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.013 | 0.018 | 0.019 | 12 | o3_default_default |
| wstate_indep_qiskit_60 | train | 60 | 36/36 | 0 | 0.039 | 0.388 | 0.391 | 12 | o2_default_default |
| wstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.015 | 0.020 | 0.022 | 12 | o2_default_default |
| wstate_indep_qiskit_70 | train | 70 | 36/36 | 0 | 0.044 | 0.354 | 0.389 | 12 | o3_sabre_sabre |
| wstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 0.022 | 0.024 | 12 | o3_default_default |
| wstate_indep_qiskit_80 | train | 80 | 36/36 | 0 | 0.051 | 0.398 | 0.413 | 12 | o3_default_default |
| wstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.016 | 0.023 | 0.200 | 12 | o3_default_default |
| wstate_indep_qiskit_90 | train | 90 | 36/36 | 0 | 0.051 | 0.400 | 0.430 | 12 | o3_default_default |
| wstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.015 | 0.027 | 0.031 | 12 | o2_default_default |
| wstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.015 | 0.022 | 0.023 | 12 | o2_default_default |
| wstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.016 | 0.019 | 0.020 | 12 | o2_default_default |
| wstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.015 | 0.022 | 0.023 | 12 | o2_default_default |
| wstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.015 | 0.022 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.015 | 0.021 | 0.027 | 12 | o2_default_default |
| wstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.016 | 0.026 | 0.027 | 12 | o2_default_default |
| wstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.017 | 0.027 | 0.032 | 12 | o2_default_default |
| wstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.022 | 0.041 | 0.043 | 12 | o3_default_default |
| wstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.021 | 0.044 | 0.049 | 12 | o3_default_default |
| wstate_indep_tket_2 | train | 2 | 36/36 | 0 | 0.013 | 0.018 | 0.019 | 12 | o3_default_default |
| wstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.019 | 0.056 | 0.060 | 12 | o3_default_default |
| wstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.018 | 0.068 | 0.076 | 12 | o3_default_default |
| wstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.019 | 0.093 | 0.105 | 12 | o3_default_default |
| wstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.019 | 0.091 | 0.099 | 12 | o2_default_default |
| wstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.021 | 0.110 | 0.114 | 12 | o3_default_default |
| wstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.023 | 0.121 | 0.123 | 12 | o3_default_default |
| wstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.027 | 0.139 | 0.148 | 12 | o2_default_default |
| wstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.029 | 0.168 | 0.173 | 12 | o2_default_default |
| wstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.026 | 0.174 | 0.194 | 12 | o2_default_default |
| wstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.032 | 0.232 | 0.243 | 12 | o2_default_default |
| wstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 0.019 | 0.019 | 12 | o2_default_default |
| wstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.027 | 0.247 | 0.261 | 12 | o3_default_default |
| wstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 0.019 | 0.023 | 12 | o3_default_default |
| wstate_indep_tket_40 | train | 40 | 36/36 | 0 | 0.031 | 0.317 | 0.327 | 12 | o3_default_default |
| wstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.014 | 0.019 | 0.019 | 12 | o2_default_default |
| wstate_indep_tket_50 | train | 50 | 36/36 | 0 | 0.035 | 0.333 | 0.356 | 12 | o2_default_default |
| wstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.014 | 0.020 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_60 | train | 60 | 36/36 | 0 | 0.042 | 0.365 | 0.387 | 12 | o2_default_default |
| wstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.016 | 0.022 | 0.026 | 12 | o2_default_default |
| wstate_indep_tket_70 | train | 70 | 36/36 | 0 | 0.046 | 0.411 | 0.421 | 12 | o2_sabre_sabre |
| wstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 0.022 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_80 | train | 80 | 36/36 | 0 | 0.046 | 0.388 | 0.448 | 12 | o3_default_default |
| wstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.016 | 0.021 | 0.028 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 36/36 | 0 | 0.055 | 0.412 | 0.460 | 12 | o3_default_default |
| pricingcall_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.034 | 0.298 | 0.306 | 10 | o3_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.018 | 0.049 | 0.054 | 10 | o3_default_default |
| pricingcall_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.024 | 0.090 | 0.101 | 10 | o3_default_default |
| pricingcall_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.035 | 0.120 | 0.131 | 10 | o3_default_default |
| pricingcall_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.018 | 0.053 | 0.064 | 10 | o3_default_default |
| pricingcall_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.026 | 0.081 | 0.084 | 10 | o3_default_default |
| pricingcall_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.035 | 0.136 | 0.152 | 10 | o3_default_default |
| pricingput_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.040 | 0.171 | 0.195 | 10 | o3_default_default |
| pricingput_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.021 | 0.051 | 0.062 | 10 | o3_default_default |
| pricingput_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.026 | 0.087 | 0.099 | 10 | o3_default_default |
| pricingput_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.035 | 0.132 | 0.153 | 10 | o3_default_default |
| pricingput_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.023 | 0.053 | 0.058 | 10 | o3_default_default |
| pricingput_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.024 | 0.086 | 0.105 | 10 | o3_default_default |
| pricingput_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.038 | 0.148 | 0.294 | 10 | o3_default_default |
| qft_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.031 | 0.041 | 0.051 | 10 | o3_default_default |
| qft_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.035 | 0.058 | 0.060 | 10 | o3_default_default |
| qft_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.033 | 0.067 | 0.073 | 10 | o3_default_default |
| qft_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.037 | 0.070 | 0.232 | 10 | o3_default_default |
| qft_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.040 | 0.079 | 0.088 | 10 | o3_default_default |
| qft_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.044 | 0.098 | 0.120 | 10 | o2_default_default |
| qft_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.048 | 0.091 | 0.112 | 10 | o3_default_default |
| qft_indep_qiskit_17 | validation | 17 | 30/36 | 6 | 0.051 | 0.115 | 0.124 | 10 | o3_default_default |
| qft_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.015 | 12 | o2_default_default |
| qft_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.014 | 3.358 | 3.478 | 12 | o3_default_default |
| qft_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.128 | 0.454 | 0.521 | 10 | o3_default_default |
| qft_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.017 | 10.651 | 11.516 | 12 | o2_default_default |
| qft_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.122 | 0.771 | 1.020 | 10 | o3_default_default |
| qft_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.020 | 24.946 | 51.702 | 12 | o3_default_default |
| qft_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.256 | 1.336 | 1.518 | 10 | o3_default_default |
| qft_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.017 | 34.896 | 87.831 | 12 | o3_default_default |
| qft_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.201 | 1.618 | 2.097 | 10 | o3_default_default |
| qft_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.020 | 56.450 | 65.769 | 12 | o3_default_default |
| qft_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.244 | 2.213 | 2.263 | 10 | o2_default_default |
| qft_indep_qiskit_8 | validation | 8 | 32/36 | 4 | 0.023 | 21.279 | 59.744 | 10 | o3_default_default |
| qft_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.018 | 0.037 | 0.040 | 10 | o3_default_default |
| qft_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.022 | 0.039 | 0.041 | 10 | o3_default_default |
| qft_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.023 | 0.052 | 0.070 | 10 | o3_default_default |
| qft_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.027 | 0.053 | 0.058 | 10 | o3_default_default |
| qft_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.026 | 0.064 | 0.176 | 10 | o3_default_default |
| qft_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.026 | 0.067 | 0.073 | 10 | o3_default_default |
| qft_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o2_default_default |
| qft_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.014 | 2.829 | 3.430 | 12 | o3_default_default |
| qft_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.086 | 0.434 | 0.448 | 10 | o3_default_default |
| qft_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.016 | 9.765 | 10.355 | 12 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.127 | 0.790 | 1.044 | 10 | o3_default_default |
| qft_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.017 | 25.399 | 51.767 | 12 | o3_default_default |
| qft_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.176 | 1.332 | 1.540 | 10 | o3_default_default |
| qft_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.018 | 34.413 | 88.234 | 12 | o3_default_default |
| qft_indep_tket_60 | validation | 60 | 30/36 | 6 | 0.196 | 1.931 | 2.305 | 10 | o3_default_default |
| qft_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.018 | 58.662 | 65.985 | 12 | o3_default_default |
| qft_indep_tket_8 | validation | 8 | 32/36 | 4 | 0.019 | 21.208 | 59.188 | 10 | o3_default_default |
| qft_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.019 | 0.037 | 0.043 | 10 | o3_default_default |
| qftentangled_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.020 | 0.040 | 0.048 | 10 | o3_default_default |
| qftentangled_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.022 | 0.057 | 0.058 | 10 | o3_default_default |
| qftentangled_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.024 | 0.052 | 0.070 | 10 | o3_default_default |
| qftentangled_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.025 | 0.065 | 0.076 | 10 | o3_default_default |
| qftentangled_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.027 | 0.072 | 0.089 | 10 | o3_default_default |
| qftentangled_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.028 | 0.081 | 0.083 | 10 | o3_default_default |
| qftentangled_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.029 | 0.096 | 0.110 | 10 | o3_default_default |
| qftentangled_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.023 | 12 | o2_default_default |
| qftentangled_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.014 | 4.847 | 5.309 | 12 | o2_default_default |
| qftentangled_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.077 | 0.396 | 0.410 | 10 | o3_default_default |
| qftentangled_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.015 | 13.877 | 23.018 | 12 | o2_default_default |
| qftentangled_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.135 | 0.804 | 1.212 | 10 | o3_default_default |
| qftentangled_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.018 | 28.391 | 73.973 | 12 | o2_default_default |
| qftentangled_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.153 | 1.178 | 1.666 | 10 | o3_default_default |
| qftentangled_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.021 | 53.212 | 62.130 | 12 | o3_default_default |
| qftentangled_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.210 | 1.802 | 3.516 | 10 | o2_default_default |
| qftentangled_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.022 | 47.899 | 48.861 | 12 | o3_default_default |
| qftentangled_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.276 | 2.405 | 2.424 | 10 | o2_default_default |
| qftentangled_indep_qiskit_8 | validation | 8 | 31/36 | 5 | 0.020 | 0.038 | 87.797 | 10 | o3_default_default |
| qftentangled_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.018 | 0.035 | 0.046 | 10 | o3_default_default |
| qftentangled_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.021 | 0.045 | 0.050 | 10 | o3_default_default |
| qftentangled_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.022 | 0.049 | 0.064 | 10 | o3_default_default |
| qftentangled_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.025 | 0.058 | 0.063 | 10 | o3_default_default |
| qftentangled_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.024 | 0.073 | 0.200 | 10 | o3_default_default |
| qftentangled_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.027 | 0.074 | 0.088 | 10 | o3_default_default |
| qftentangled_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.014 | 0.014 | 12 | o2_default_default |
| qftentangled_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.015 | 5.128 | 5.342 | 12 | o2_default_default |
| qftentangled_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.091 | 0.445 | 0.462 | 10 | o3_default_default |
| qftentangled_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.018 | 13.432 | 23.629 | 12 | o2_default_default |
| qftentangled_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.129 | 0.801 | 1.168 | 10 | o3_default_default |
| qftentangled_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.016 | 28.724 | 74.398 | 12 | o2_default_default |
| qftentangled_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.153 | 1.053 | 1.456 | 10 | o3_default_default |
| qftentangled_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.018 | 50.953 | 59.163 | 12 | o3_default_default |
| qftentangled_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.017 | 47.369 | 47.980 | 12 | o3_default_default |
| qftentangled_indep_tket_8 | validation | 8 | 31/36 | 5 | 0.021 | 0.040 | 83.750 | 10 | o3_default_default |
| qftentangled_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.019 | 0.033 | 0.042 | 10 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 1252 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Esito ignoto alla soglia | Minimo timeout stimato |
| --- | --- | --- | --- | --- |
| 30 | 374 | 1252 | 0 | 1626 |
| 60 | 83 | 1252 | 0 | 1335 |
| 100 | 0 | 1252 | 0 | 1252 |
| 120 | 0 | 1252 | 1252 | 0 |
| 300 | 0 | 1252 | 1252 | 0 |
| 600 | 0 | 1252 | 1252 | 0 |
| 900 | 0 | 1252 | 1252 | 0 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta. Questi casi restano ignoti e non sono inclusi nel minimo stimato. La stima usa i tempi osservati e non prevede l'effetto di cambiare i worker.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 5667 |
| Non eleggibili | 453 |
| Esempi RAG | 396 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

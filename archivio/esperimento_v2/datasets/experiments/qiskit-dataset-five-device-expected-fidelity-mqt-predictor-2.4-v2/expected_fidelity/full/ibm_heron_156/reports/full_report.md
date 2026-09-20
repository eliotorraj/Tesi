# Dataset Qiskit full — ibm_heron_156

Scheda generata automaticamente dagli artefatti del Dataset. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 156 |
| Hash target | 207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003 |
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
| Cache hit | 15192 |
| Durata invocazione | 7183.721 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati. I parametri nei risultati provengono dai singoli tentativi, quando disponibili; per i vecchi dati senza questa informazione si usa lo stato della generazione.



## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 18360 | - |
| Osservati | 18360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 17053 | 92.9% |
| Failure | 0 | 0.0% |
| Timeout | 1307 | 7.1% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 17053 | 0.008 | 0.021 | 2.146 | 12.986 | 103.356 |
| Non-lookahead | 15300 | 0.008 | 0.020 | 0.148 | 0.282 | 23.824 |
| Lookahead | 1753 | 0.009 | 9.657 | 19.592 | 75.612 | 103.356 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 1530/1530 | 0 | 0.021 | 0.264 | 4.257 | 510 | 121 | 121 | 451 |
| o3_default_default | baseline | 3 | default | default | 1530/1530 | 0 | 0.029 | 2.923 | 23.824 | 510 | 365 | 432 | 506 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 1530/1530 | 0 | 0.016 | 0.155 | 0.586 | 510 | 0 | 0 | 102 |
| o2_dense_sabre | layout | 2 | dense | sabre | 1530/1530 | 0 | 0.020 | 0.091 | 0.311 | 510 | 19 | 19 | 194 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 1530/1530 | 0 | 0.015 | 0.083 | 0.222 | 510 | 0 | 0 | 6 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 1530/1530 | 0 | 0.018 | 0.260 | 0.821 | 510 | 1 | 2 | 101 |
| o3_dense_sabre | layout | 3 | dense | sabre | 1530/1530 | 0 | 0.022 | 0.168 | 0.596 | 510 | 4 | 23 | 127 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 1530/1530 | 0 | 0.018 | 0.167 | 0.538 | 510 | 0 | 0 | 6 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 869/1530 | 661 | 9.505 | 75.684 | 99.720 | 267 | 0 | 0 | 9 |
| o2_sabre_basic | routing | 2 | sabre | basic | 1530/1530 | 0 | 0.029 | 0.746 | 3.762 | 510 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 884/1530 | 646 | 10.097 | 74.098 | 103.356 | 274 | 0 | 0 | 23 |
| o3_sabre_basic | routing | 3 | sabre | basic | 1530/1530 | 0 | 0.032 | 1.088 | 3.937 | 510 | 0 | 0 | 5 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.031 | 0.264 | 0.270 | 10 | o3_default_default |
| ae_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.028 | 0.069 | 0.073 | 10 | o3_default_default |
| ae_indep_qiskit_12 | train | 12 | 30/36 | 6 | 0.031 | 0.072 | 0.074 | 10 | o2_default_default |
| ae_indep_qiskit_13 | train | 13 | 30/36 | 6 | 0.034 | 0.111 | 0.120 | 10 | o3_default_default |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.013 | 0.017 | 0.021 | 12 | o3_default_default |
| ae_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.018 | 6.874 | 7.228 | 12 | o3_default_default |
| ae_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.099 | 0.316 | 0.363 | 10 | o2_default_default |
| ae_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.020 | 12.479 | 16.043 | 12 | o3_default_default |
| ae_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.164 | 0.728 | 0.796 | 10 | o3_default_default |
| ae_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.019 | 17.510 | 18.771 | 12 | o3_dense_sabre |
| ae_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.216 | 0.952 | 1.212 | 10 | o2_default_default |
| ae_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.020 | 48.130 | 54.590 | 12 | o3_default_default |
| ae_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.255 | 1.190 | 1.291 | 10 | o3_default_default |
| ae_indep_qiskit_7 | train | 7 | 35/36 | 1 | 0.021 | 42.792 | 78.667 | 11 | o3_default_default |
| ae_indep_qiskit_8 | train | 8 | 33/36 | 3 | 0.020 | 73.902 | 80.071 | 10 | o3_default_default |
| ae_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.020 | 0.042 | 0.047 | 10 | o3_default_default |
| ae_indep_tket_10 | train | 10 | 30/36 | 6 | 0.022 | 0.050 | 0.053 | 10 | o3_default_default |
| ae_indep_tket_11 | train | 11 | 30/36 | 6 | 0.025 | 0.057 | 0.076 | 10 | o3_default_default |
| ae_indep_tket_12 | train | 12 | 30/36 | 6 | 0.025 | 0.060 | 0.068 | 10 | o2_default_default |
| ae_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.015 | 0.017 | 12 | o3_default_default |
| ae_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 6.780 | 6.840 | 12 | o3_default_default |
| ae_indep_tket_30 | train | 30 | 30/36 | 6 | 0.099 | 0.317 | 0.345 | 10 | o3_default_default |
| ae_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 12.041 | 15.206 | 12 | o3_default_default |
| ae_indep_tket_40 | train | 40 | 30/36 | 6 | 0.147 | 0.677 | 0.731 | 10 | o3_default_default |
| ae_indep_tket_5 | train | 5 | 36/36 | 0 | 0.017 | 16.020 | 18.529 | 12 | o3_dense_sabre |
| ae_indep_tket_50 | train | 50 | 30/36 | 6 | 0.172 | 0.798 | 1.162 | 10 | o2_default_default |
| ae_indep_tket_6 | train | 6 | 36/36 | 0 | 0.021 | 46.966 | 53.656 | 12 | o3_default_default |
| ae_indep_tket_7 | train | 7 | 35/36 | 1 | 0.021 | 44.512 | 75.912 | 11 | o3_default_default |
| ae_indep_tket_8 | train | 8 | 33/36 | 3 | 0.022 | 73.448 | 83.092 | 10 | o3_default_default |
| ae_indep_tket_9 | train | 9 | 30/36 | 6 | 0.020 | 0.043 | 0.047 | 10 | o2_default_default |
| dj_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.018 | 19.606 | 20.609 | 12 | o3_default_default |
| dj_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.018 | 20.532 | 21.115 | 12 | o3_default_default |
| dj_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.020 | 21.998 | 22.315 | 12 | o3_default_default |
| dj_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.020 | 27.183 | 27.310 | 12 | o2_default_default |
| dj_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.022 | 34.419 | 35.332 | 12 | o3_default_default |
| dj_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.021 | 35.239 | 36.999 | 12 | o3_default_default |
| dj_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.023 | 36.690 | 38.151 | 12 | o3_default_default |
| dj_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.022 | 36.966 | 38.119 | 12 | o3_default_default |
| dj_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.026 | 39.755 | 44.100 | 12 | o3_default_default |
| dj_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.025 | 53.490 | 79.927 | 12 | o3_default_default |
| dj_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.013 | 0.016 | 0.190 | 12 | o3_default_default |
| dj_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.028 | 84.154 | 86.555 | 12 | o3_default_default |
| dj_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.026 | 91.339 | 95.215 | 12 | o3_default_default |
| dj_indep_qiskit_22 | train | 22 | 35/36 | 1 | 0.029 | 53.931 | 99.058 | 11 | o3_default_default |
| dj_indep_qiskit_23 | train | 23 | 33/36 | 3 | 0.027 | 54.434 | 103.356 | 10 | o3_default_default |
| dj_indep_qiskit_24 | train | 24 | 32/36 | 4 | 0.026 | 25.181 | 57.158 | 10 | o3_default_default |
| dj_indep_qiskit_25 | train | 25 | 33/36 | 3 | 0.029 | 63.756 | 69.613 | 10 | o3_default_default |
| dj_indep_qiskit_26 | train | 26 | 32/36 | 4 | 0.025 | 32.105 | 73.595 | 10 | o3_default_default |
| dj_indep_qiskit_27 | train | 27 | 30/36 | 6 | 0.023 | 0.186 | 0.440 | 10 | o3_default_default |
| dj_indep_qiskit_28 | train | 28 | 30/36 | 6 | 0.027 | 0.213 | 0.379 | 10 | o3_default_default |
| dj_indep_qiskit_29 | train | 29 | 32/36 | 4 | 0.025 | 43.134 | 95.583 | 10 | o3_default_default |
| dj_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.014 | 0.018 | 0.019 | 12 | o3_default_default |
| dj_indep_qiskit_30 | train | 30 | 31/36 | 5 | 0.026 | 0.204 | 88.341 | 10 | o3_default_default |
| dj_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 0.020 | 5.492 | 12 | o2_default_default |
| dj_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.028 | 0.834 | 1.021 | 10 | o3_default_default |
| dj_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.016 | 6.032 | 8.288 | 12 | o3_default_default |
| dj_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.026 | 4.339 | 4.523 | 10 | o3_default_default |
| dj_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.018 | 8.759 | 11.627 | 12 | o2_default_default |
| dj_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.032 | 17.434 | 18.957 | 10 | o3_default_default |
| dj_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.017 | 11.322 | 14.588 | 12 | o3_default_default |
| dj_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.032 | 18.649 | 20.102 | 10 | o3_default_default |
| dj_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.016 | 17.583 | 18.560 | 12 | o2_default_default |
| dj_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.034 | 18.899 | 19.964 | 10 | o3_default_default |
| dj_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.019 | 11.549 | 18.280 | 12 | o3_default_default |
| dj_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.047 | 20.572 | 20.960 | 10 | o3_default_default |
| dj_indep_tket_10 | train | 10 | 36/36 | 0 | 0.018 | 19.216 | 20.104 | 12 | o3_default_default |
| dj_indep_tket_11 | train | 11 | 36/36 | 0 | 0.017 | 21.009 | 21.630 | 12 | o3_default_default |
| dj_indep_tket_12 | train | 12 | 36/36 | 0 | 0.020 | 22.354 | 22.869 | 12 | o3_default_default |
| dj_indep_tket_13 | train | 13 | 36/36 | 0 | 0.019 | 27.240 | 28.170 | 12 | o2_default_default |
| dj_indep_tket_14 | train | 14 | 36/36 | 0 | 0.022 | 33.771 | 34.747 | 12 | o3_default_default |
| dj_indep_tket_15 | train | 15 | 36/36 | 0 | 0.022 | 35.679 | 35.911 | 12 | o3_default_default |
| dj_indep_tket_16 | train | 16 | 36/36 | 0 | 0.022 | 35.886 | 36.870 | 12 | o3_default_default |
| dj_indep_tket_17 | train | 17 | 36/36 | 0 | 0.021 | 37.057 | 38.388 | 12 | o3_default_default |
| dj_indep_tket_18 | train | 18 | 36/36 | 0 | 0.021 | 39.838 | 44.135 | 12 | o3_default_default |
| dj_indep_tket_19 | train | 19 | 36/36 | 0 | 0.024 | 53.577 | 82.786 | 12 | o3_default_default |
| dj_indep_tket_2 | train | 2 | 36/36 | 0 | 0.012 | 0.016 | 0.020 | 12 | o3_default_default |
| dj_indep_tket_20 | train | 20 | 36/36 | 0 | 0.027 | 84.041 | 84.831 | 12 | o3_default_default |
| dj_indep_tket_21 | train | 21 | 36/36 | 0 | 0.023 | 90.937 | 91.148 | 12 | o2_default_default |
| dj_indep_tket_22 | train | 22 | 35/36 | 1 | 0.025 | 54.177 | 99.613 | 11 | o2_default_default |
| dj_indep_tket_23 | train | 23 | 32/36 | 4 | 0.022 | 24.904 | 56.288 | 10 | o3_default_default |
| dj_indep_tket_24 | train | 24 | 32/36 | 4 | 0.022 | 26.094 | 58.437 | 10 | o3_default_default |
| dj_indep_tket_25 | train | 25 | 33/36 | 3 | 0.025 | 64.005 | 73.096 | 10 | o3_default_default |
| dj_indep_tket_26 | train | 26 | 32/36 | 4 | 0.025 | 31.829 | 72.157 | 10 | o3_default_default |
| dj_indep_tket_27 | train | 27 | 30/36 | 6 | 0.020 | 0.176 | 0.449 | 10 | o3_default_default |
| dj_indep_tket_28 | train | 28 | 30/36 | 6 | 0.023 | 0.185 | 0.319 | 10 | o3_default_default |
| dj_indep_tket_29 | train | 29 | 32/36 | 4 | 0.026 | 41.606 | 93.891 | 10 | o3_default_default |
| dj_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 0.017 | 0.018 | 12 | o3_default_default |
| dj_indep_tket_30 | train | 30 | 31/36 | 5 | 0.022 | 0.204 | 87.249 | 10 | o3_default_default |
| dj_indep_tket_4 | train | 4 | 36/36 | 0 | 0.014 | 0.019 | 6.802 | 12 | o2_default_default |
| dj_indep_tket_40 | train | 40 | 30/36 | 6 | 0.028 | 0.876 | 1.052 | 10 | o3_default_default |
| dj_indep_tket_5 | train | 5 | 36/36 | 0 | 0.016 | 6.548 | 8.540 | 12 | o3_default_default |
| dj_indep_tket_50 | train | 50 | 30/36 | 6 | 0.026 | 3.835 | 4.095 | 10 | o3_default_default |
| dj_indep_tket_6 | train | 6 | 36/36 | 0 | 0.017 | 9.280 | 10.825 | 12 | o2_default_default |
| dj_indep_tket_60 | train | 60 | 30/36 | 6 | 0.030 | 17.791 | 18.281 | 10 | o3_default_default |
| dj_indep_tket_7 | train | 7 | 36/36 | 0 | 0.015 | 11.369 | 14.798 | 12 | o2_default_default |
| dj_indep_tket_70 | train | 70 | 30/36 | 6 | 0.036 | 18.500 | 19.490 | 10 | o3_default_default |
| dj_indep_tket_8 | train | 8 | 36/36 | 0 | 0.016 | 17.599 | 17.923 | 12 | o2_default_default |
| dj_indep_tket_80 | train | 80 | 30/36 | 6 | 0.038 | 20.202 | 21.479 | 10 | o2_default_default |
| dj_indep_tket_9 | train | 9 | 36/36 | 0 | 0.015 | 11.871 | 18.040 | 12 | o3_default_default |
| dj_indep_tket_90 | train | 90 | 30/36 | 6 | 0.047 | 20.209 | 21.987 | 10 | o3_default_default |
| graphstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.017 | 18.126 | 19.370 | 12 | o2_default_default |
| graphstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.019 | 18.897 | 19.859 | 12 | o3_default_default |
| graphstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.020 | 22.043 | 30.659 | 12 | o2_default_default |
| graphstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.018 | 10.443 | 10.729 | 12 | o3_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.021 | 20.916 | 22.415 | 12 | o3_default_default |
| graphstate_indep_qiskit_15 | train | 15 | 34/36 | 2 | 0.020 | 19.061 | 74.363 | 11 | o3_default_default |
| graphstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.021 | 29.759 | 34.295 | 12 | o3_default_default |
| graphstate_indep_qiskit_17 | train | 17 | 35/36 | 1 | 0.020 | 27.856 | 31.469 | 11 | o3_default_default |
| graphstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.024 | 21.281 | 42.916 | 12 | o2_default_default |
| graphstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.025 | 34.159 | 37.140 | 12 | o3_default_default |
| graphstate_indep_qiskit_20 | train | 20 | 35/36 | 1 | 0.021 | 32.237 | 50.917 | 11 | o3_default_default |
| graphstate_indep_qiskit_21 | train | 21 | 35/36 | 1 | 0.026 | 32.071 | 32.756 | 11 | o3_default_default |
| graphstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.028 | 45.255 | 55.576 | 12 | o3_default_default |
| graphstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.026 | 36.477 | 56.008 | 12 | o3_default_default |
| graphstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.027 | 54.806 | 62.411 | 12 | o3_default_default |
| graphstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.027 | 58.751 | 68.596 | 12 | o3_default_default |
| graphstate_indep_qiskit_26 | train | 26 | 34/36 | 2 | 0.025 | 41.870 | 80.535 | 10 | o3_default_default |
| graphstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.029 | 61.024 | 75.467 | 12 | o3_default_default |
| graphstate_indep_qiskit_28 | train | 28 | 34/36 | 2 | 0.024 | 71.561 | 78.513 | 10 | o3_default_default |
| graphstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.029 | 72.081 | 95.792 | 12 | o3_default_default |
| graphstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 3.817 | 4.103 | 12 | o2_default_default |
| graphstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.030 | 73.466 | 81.600 | 12 | o3_default_default |
| graphstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.017 | 6.330 | 7.103 | 12 | o3_default_default |
| graphstate_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.031 | 0.294 | 0.499 | 10 | o3_default_default |
| graphstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.017 | 8.979 | 12.597 | 12 | o2_dense_sabre |
| graphstate_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.029 | 0.161 | 0.233 | 10 | o3_default_default |
| graphstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 8.640 | 8.897 | 12 | o3_default_default |
| graphstate_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.033 | 19.792 | 20.773 | 10 | o3_default_default |
| graphstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.018 | 8.795 | 9.027 | 12 | o3_default_default |
| graphstate_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.038 | 20.636 | 20.929 | 10 | o3_default_default |
| graphstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.017 | 11.785 | 12.192 | 12 | o2_default_default |
| graphstate_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.062 | 1.857 | 1.996 | 10 | o3_default_default |
| graphstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.018 | 12.899 | 14.552 | 12 | o2_default_default |
| graphstate_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.051 | 22.984 | 23.824 | 10 | o3_sabre_sabre |
| graphstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.018 | 12.777 | 20.568 | 12 | o3_default_default |
| graphstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.020 | 18.827 | 19.521 | 12 | o3_default_default |
| graphstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.019 | 19.246 | 20.777 | 12 | o2_default_default |
| graphstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.021 | 22.833 | 29.657 | 12 | o3_default_default |
| graphstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.022 | 18.927 | 21.396 | 12 | o3_default_default |
| graphstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.022 | 20.130 | 21.724 | 12 | o3_default_default |
| graphstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.022 | 25.137 | 32.374 | 12 | o2_default_default |
| graphstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.022 | 25.045 | 31.125 | 12 | o3_default_default |
| graphstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.024 | 31.030 | 37.991 | 12 | o2_default_default |
| graphstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.023 | 31.679 | 32.559 | 12 | o3_default_default |
| graphstate_indep_tket_20 | train | 20 | 34/36 | 2 | 0.026 | 20.789 | 42.086 | 10 | o3_default_default |
| graphstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.025 | 43.850 | 45.865 | 12 | o3_default_default |
| graphstate_indep_tket_22 | train | 22 | 34/36 | 2 | 0.022 | 48.417 | 58.538 | 10 | o3_default_default |
| graphstate_indep_tket_23 | train | 23 | 35/36 | 1 | 0.023 | 62.409 | 72.661 | 11 | o3_default_default |
| graphstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.024 | 49.572 | 55.052 | 12 | o3_default_default |
| graphstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.028 | 37.021 | 62.149 | 12 | o3_default_default |
| graphstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.026 | 63.415 | 75.829 | 12 | o3_default_default |
| graphstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.030 | 60.602 | 69.067 | 12 | o3_default_default |
| graphstate_indep_tket_28 | train | 28 | 35/36 | 1 | 0.022 | 69.907 | 99.333 | 11 | o3_default_default |
| graphstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.030 | 59.614 | 62.350 | 12 | o3_default_default |
| graphstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 3.763 | 3.975 | 12 | o2_default_default |
| graphstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.032 | 66.306 | 76.081 | 12 | o3_default_default |
| graphstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 6.665 | 7.689 | 12 | o2_dense_sabre |
| graphstate_indep_tket_40 | train | 40 | 31/36 | 5 | 0.034 | 0.335 | 98.408 | 10 | o2_default_default |
| graphstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.017 | 8.153 | 8.488 | 12 | o2_dense_sabre |
| graphstate_indep_tket_50 | train | 50 | 30/36 | 6 | 0.032 | 20.094 | 21.542 | 10 | o3_default_default |
| graphstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 8.516 | 8.955 | 12 | o3_default_default |
| graphstate_indep_tket_60 | train | 60 | 30/36 | 6 | 0.042 | 19.887 | 19.969 | 10 | o3_default_default |
| graphstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.017 | 9.383 | 10.977 | 12 | o3_default_default |
| graphstate_indep_tket_70 | train | 70 | 30/36 | 6 | 0.035 | 21.530 | 23.193 | 10 | o3_default_default |
| graphstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 9.008 | 11.454 | 12 | o3_default_default |
| graphstate_indep_tket_80 | train | 80 | 30/36 | 6 | 0.049 | 0.377 | 0.469 | 10 | o2_default_default |
| graphstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.019 | 8.908 | 9.125 | 12 | o3_default_default |
| graphstate_indep_tket_90 | train | 90 | 30/36 | 6 | 0.054 | 21.814 | 22.127 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 48.977 | 55.427 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_qiskit_4 | train | 4 | 30/36 | 6 | 0.018 | 0.026 | 0.027 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.019 | 0.036 | 0.194 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.019 | 0.037 | 0.042 | 10 | o2_default_default |
| portfolioqaoa_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.022 | 0.047 | 0.051 | 10 | o2_default_default |
| portfolioqaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 50.075 | 57.895 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_tket_4 | train | 4 | 30/36 | 6 | 0.017 | 0.026 | 0.028 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_5 | train | 5 | 30/36 | 6 | 0.018 | 0.036 | 0.039 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.038 | 0.048 | 10 | o2_default_default |
| portfolioqaoa_indep_tket_7 | train | 7 | 30/36 | 6 | 0.022 | 0.061 | 0.065 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.028 | 0.081 | 0.101 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.029 | 0.088 | 0.097 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 40.639 | 45.578 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_4 | train | 4 | 34/36 | 2 | 0.017 | 95.176 | 99.720 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.018 | 0.028 | 0.030 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.017 | 0.032 | 0.035 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.045 | 0.051 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.026 | 0.058 | 0.060 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.024 | 0.058 | 0.070 | 10 | o3_default_default |
| portfoliovqe_indep_tket_10 | train | 10 | 30/36 | 6 | 0.026 | 0.070 | 0.073 | 10 | o2_default_default |
| portfoliovqe_indep_tket_11 | train | 11 | 30/36 | 6 | 0.029 | 0.088 | 0.109 | 10 | o3_default_default |
| portfoliovqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 41.092 | 46.124 | 12 | o3_default_default |
| portfoliovqe_indep_tket_4 | train | 4 | 34/36 | 2 | 0.016 | 95.110 | 99.167 | 10 | o3_default_default |
| portfoliovqe_indep_tket_5 | train | 5 | 30/36 | 6 | 0.018 | 0.026 | 0.029 | 10 | o3_default_default |
| portfoliovqe_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.032 | 0.041 | 10 | o3_default_default |
| portfoliovqe_indep_tket_7 | train | 7 | 30/36 | 6 | 0.023 | 0.049 | 0.050 | 10 | o2_default_default |
| portfoliovqe_indep_tket_8 | train | 8 | 30/36 | 6 | 0.023 | 0.059 | 0.246 | 10 | o2_default_default |
| portfoliovqe_indep_tket_9 | train | 9 | 30/36 | 6 | 0.023 | 0.063 | 0.092 | 10 | o3_default_default |
| qaoa_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.022 | 24.469 | 26.933 | 12 | o3_default_default |
| qaoa_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.024 | 25.886 | 34.355 | 12 | o3_default_default |
| qaoa_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.020 | 17.438 | 26.585 | 12 | o2_default_default |
| qaoa_indep_qiskit_13 | train | 13 | 35/36 | 1 | 0.027 | 23.720 | 80.133 | 11 | o3_default_default |
| qaoa_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.027 | 63.958 | 74.187 | 12 | o3_default_default |
| qaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 17.345 | 21.273 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.016 | 9.194 | 9.618 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.019 | 14.662 | 15.348 | 12 | o2_default_default |
| qaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.018 | 23.775 | 24.195 | 12 | o2_default_default |
| qaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.022 | 12.817 | 13.525 | 12 | o3_default_default |
| qaoa_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.021 | 22.261 | 22.636 | 12 | o2_default_default |
| qaoa_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.022 | 67.110 | 72.197 | 12 | o3_default_default |
| qaoa_indep_tket_10 | train | 10 | 36/36 | 0 | 0.021 | 24.586 | 26.991 | 12 | o3_default_default |
| qaoa_indep_tket_11 | train | 11 | 36/36 | 0 | 0.023 | 25.358 | 35.142 | 12 | o3_default_default |
| qaoa_indep_tket_12 | train | 12 | 36/36 | 0 | 0.019 | 17.847 | 26.506 | 12 | o2_default_default |
| qaoa_indep_tket_13 | train | 13 | 35/36 | 1 | 0.023 | 23.821 | 85.024 | 11 | o3_default_default |
| qaoa_indep_tket_14 | train | 14 | 36/36 | 0 | 0.026 | 63.070 | 73.321 | 12 | o3_default_default |
| qaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 17.685 | 21.138 | 12 | o2_dense_sabre |
| qaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 9.325 | 9.650 | 12 | o2_dense_sabre |
| qaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.018 | 14.326 | 15.465 | 12 | o2_default_default |
| qaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.019 | 23.983 | 24.560 | 12 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.022 | 12.725 | 12.998 | 12 | o3_default_default |
| qaoa_indep_tket_8 | train | 8 | 36/36 | 0 | 0.018 | 22.227 | 22.525 | 12 | o2_default_default |
| qaoa_indep_tket_9 | train | 9 | 36/36 | 0 | 0.023 | 67.511 | 72.550 | 12 | o3_default_default |
| qnn_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| qnn_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 18.608 | 20.010 | 12 | o3_default_default |
| qnn_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.160 | 0.992 | 1.240 | 10 | o3_default_default |
| qnn_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.022 | 32.456 | 34.245 | 12 | o3_default_default |
| qnn_indep_qiskit_5 | train | 5 | 34/36 | 2 | 0.019 | 62.746 | 78.055 | 10 | o3_default_default |
| qnn_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.018 | 0.042 | 0.048 | 10 | o3_default_default |
| qnn_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.051 | 0.062 | 10 | o2_default_default |
| qnn_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.015 | 0.166 | 12 | o3_default_default |
| qnn_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 19.398 | 20.541 | 12 | o3_default_default |
| qnn_indep_tket_30 | train | 30 | 30/36 | 6 | 0.139 | 0.913 | 1.201 | 10 | o3_default_default |
| qnn_indep_tket_4 | train | 4 | 36/36 | 0 | 0.020 | 34.076 | 34.178 | 12 | o3_default_default |
| qnn_indep_tket_5 | train | 5 | 35/36 | 1 | 0.018 | 78.523 | 96.846 | 11 | o3_default_default |
| qnn_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.046 | 0.055 | 10 | o3_default_default |
| qnn_indep_tket_7 | train | 7 | 30/36 | 6 | 0.021 | 0.055 | 0.059 | 10 | o2_default_default |
| random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.014 | 0.018 | 12 | o3_default_default |
| random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 22.745 | 23.123 | 12 | o3_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.320 | 1.664 | 1.848 | 10 | o3_default_default |
| random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.023 | 38.258 | 46.880 | 12 | o2_default_default |
| random_indep_qiskit_5 | train | 5 | 34/36 | 2 | 0.019 | 34.235 | 34.648 | 10 | o3_default_default |
| random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.021 | 0.042 | 0.044 | 10 | o2_dense_sabre |
| random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.022 | 0.066 | 0.075 | 10 | o2_default_default |
| random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.028 | 0.055 | 0.056 | 10 | o3_default_default |
| random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.019 | 12 | o3_default_default |
| random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 22.861 | 24.484 | 12 | o3_default_default |
| random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.282 | 1.325 | 1.656 | 10 | o3_default_default |
| random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.019 | 36.557 | 47.138 | 12 | o2_default_default |
| random_indep_tket_5 | train | 5 | 34/36 | 2 | 0.019 | 34.244 | 35.794 | 10 | o3_default_default |
| random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.020 | 0.044 | 0.046 | 10 | o2_dense_sabre |
| random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.023 | 0.052 | 0.071 | 10 | o2_default_default |
| random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.024 | 0.050 | 0.063 | 10 | o3_default_default |
| realamprandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.025 | 0.090 | 0.095 | 10 | o2_default_default |
| realamprandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.029 | 0.094 | 0.102 | 10 | o3_default_default |
| realamprandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.015 | 12 | o3_default_default |
| realamprandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.017 | 40.966 | 46.651 | 12 | o3_default_default |
| realamprandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.174 | 0.872 | 1.120 | 10 | o3_default_default |
| realamprandom_indep_qiskit_4 | train | 4 | 34/36 | 2 | 0.015 | 95.450 | 99.586 | 10 | o3_default_default |
| realamprandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.328 | 1.889 | 2.162 | 10 | o3_default_default |
| realamprandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.019 | 0.034 | 0.055 | 10 | o3_default_default |
| realamprandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.452 | 3.666 | 3.781 | 10 | o3_default_default |
| realamprandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.019 | 0.038 | 0.042 | 10 | o3_default_default |
| realamprandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.019 | 0.044 | 0.048 | 10 | o2_default_default |
| realamprandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.020 | 0.061 | 0.069 | 10 | o3_default_default |
| realamprandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.024 | 0.062 | 0.071 | 10 | o3_default_default |
| realamprandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.026 | 0.082 | 0.086 | 10 | o2_default_default |
| realamprandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.028 | 0.091 | 0.109 | 10 | o3_default_default |
| realamprandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.013 | 12 | o3_default_default |
| realamprandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 41.310 | 46.802 | 12 | o3_default_default |
| realamprandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.234 | 0.904 | 0.999 | 10 | o3_default_default |
| realamprandom_indep_tket_4 | train | 4 | 33/36 | 3 | 0.016 | 93.323 | 96.806 | 10 | o3_default_default |
| realamprandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.384 | 1.785 | 2.135 | 10 | o3_default_default |
| realamprandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.017 | 0.029 | 0.030 | 10 | o3_default_default |
| realamprandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.469 | 3.228 | 3.887 | 10 | o3_default_default |
| realamprandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.021 | 0.042 | 0.051 | 10 | o3_default_default |
| realamprandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.019 | 0.047 | 0.053 | 10 | o2_default_default |
| realamprandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.021 | 0.055 | 0.069 | 10 | o3_default_default |
| realamprandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.023 | 0.078 | 0.084 | 10 | o3_default_default |
| su2random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.015 | 12 | o3_default_default |
| su2random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 41.227 | 46.818 | 12 | o3_default_default |
| su2random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.193 | 0.882 | 0.979 | 10 | o3_default_default |
| su2random_indep_qiskit_4 | train | 4 | 33/36 | 3 | 0.016 | 95.319 | 97.099 | 10 | o3_default_default |
| su2random_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.331 | 1.739 | 2.104 | 10 | o3_default_default |
| su2random_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.018 | 0.027 | 0.030 | 10 | o3_default_default |
| su2random_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.463 | 3.355 | 3.769 | 10 | o3_default_default |
| su2random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.019 | 0.046 | 0.053 | 10 | o3_default_default |
| su2random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.049 | 0.053 | 10 | o2_default_default |
| su2random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.023 | 0.054 | 0.060 | 10 | o2_default_default |
| su2random_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.023 | 0.068 | 0.073 | 10 | o3_default_default |
| su2random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.014 | 12 | o3_default_default |
| su2random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 43.767 | 47.730 | 12 | o3_default_default |
| su2random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.181 | 0.897 | 1.038 | 10 | o3_default_default |
| su2random_indep_tket_4 | train | 4 | 32/36 | 4 | 0.016 | 42.880 | 96.485 | 10 | o3_default_default |
| su2random_indep_tket_40 | train | 40 | 30/36 | 6 | 0.326 | 1.786 | 2.043 | 10 | o3_default_default |
| su2random_indep_tket_5 | train | 5 | 30/36 | 6 | 0.018 | 0.035 | 0.038 | 10 | o3_default_default |
| su2random_indep_tket_50 | train | 50 | 30/36 | 6 | 0.473 | 3.461 | 3.937 | 10 | o3_default_default |
| su2random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.041 | 0.087 | 10 | o3_default_default |
| su2random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.019 | 0.049 | 0.049 | 10 | o2_default_default |
| su2random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.020 | 0.065 | 0.073 | 10 | o3_default_default |
| su2random_indep_tket_9 | train | 9 | 30/36 | 6 | 0.023 | 0.078 | 0.085 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.027 | 0.086 | 0.088 | 10 | o2_default_default |
| twolocalrandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.029 | 0.093 | 0.105 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.016 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 41.919 | 46.409 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.174 | 0.829 | 1.040 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_4 | train | 4 | 33/36 | 3 | 0.017 | 94.529 | 96.742 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.395 | 1.873 | 2.150 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.020 | 0.035 | 0.042 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.467 | 3.123 | 3.836 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.020 | 0.050 | 0.057 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.047 | 0.051 | 10 | o2_default_default |
| twolocalrandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.021 | 0.061 | 0.078 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.025 | 0.069 | 0.085 | 10 | o3_default_default |
| twolocalrandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.027 | 0.096 | 0.109 | 10 | o2_default_default |
| twolocalrandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.029 | 0.090 | 0.117 | 10 | o3_default_default |
| twolocalrandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.010 | 0.014 | 0.015 | 12 | o3_default_default |
| twolocalrandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.017 | 41.284 | 45.938 | 12 | o3_default_default |
| twolocalrandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.175 | 0.870 | 1.030 | 10 | o3_default_default |
| twolocalrandom_indep_tket_4 | train | 4 | 34/36 | 2 | 0.016 | 95.831 | 99.642 | 10 | o3_default_default |
| twolocalrandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.429 | 1.778 | 2.385 | 10 | o3_default_default |
| twolocalrandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.020 | 0.031 | 0.036 | 10 | o3_default_default |
| twolocalrandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.452 | 3.414 | 3.920 | 10 | o3_default_default |
| twolocalrandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.050 | 0.056 | 10 | o3_default_default |
| twolocalrandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.045 | 0.053 | 10 | o2_default_default |
| twolocalrandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.021 | 0.057 | 0.059 | 10 | o3_default_default |
| twolocalrandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.023 | 0.068 | 0.072 | 10 | o3_default_default |
| vqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.014 | 0.019 | 0.020 | 12 | o2_default_default |
| vqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.016 | 0.022 | 0.023 | 12 | o2_default_default |
| vqe_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.015 | 0.022 | 0.023 | 12 | o3_default_default |
| vqe_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.016 | 0.025 | 0.027 | 12 | o2_default_default |
| vqe_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.017 | 0.024 | 0.027 | 12 | o3_default_default |
| vqe_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.015 | 0.028 | 0.187 | 12 | o3_default_default |
| vqe_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.016 | 0.030 | 0.032 | 12 | o3_default_default |
| vqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 0.017 | 0.019 | 12 | o2_default_default |
| vqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 0.014 | 0.015 | 12 | o3_default_default |
| vqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.012 | 0.019 | 0.021 | 12 | o2_default_default |
| vqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.014 | 0.018 | 0.019 | 12 | o3_default_default |
| vqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.016 | 0.023 | 0.024 | 12 | o2_default_default |
| vqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.014 | 0.018 | 0.032 | 12 | o3_default_default |
| vqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.014 | 0.020 | 0.036 | 12 | o3_default_default |
| vqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.014 | 0.019 | 0.020 | 12 | o2_default_default |
| vqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.014 | 0.019 | 0.021 | 12 | o3_default_default |
| vqe_indep_tket_12 | train | 12 | 36/36 | 0 | 0.015 | 0.020 | 0.027 | 12 | o2_default_default |
| vqe_indep_tket_13 | train | 13 | 36/36 | 0 | 0.016 | 0.024 | 0.028 | 12 | o2_default_default |
| vqe_indep_tket_14 | train | 14 | 36/36 | 0 | 0.014 | 0.029 | 0.035 | 12 | o3_default_default |
| vqe_indep_tket_15 | train | 15 | 36/36 | 0 | 0.016 | 0.031 | 0.036 | 12 | o3_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.014 | 0.034 | 0.040 | 12 | o3_default_default |
| vqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 0.015 | 0.017 | 12 | o3_default_default |
| vqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.013 | 0.017 | 0.023 | 12 | o2_default_default |
| vqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 0.017 | 0.018 | 12 | o2_default_default |
| vqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.013 | 0.019 | 0.025 | 12 | o3_default_default |
| vqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.013 | 0.016 | 0.021 | 12 | o2_default_default |
| vqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.014 | 0.021 | 0.026 | 12 | o3_default_default |
| vqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.013 | 0.019 | 0.024 | 12 | o3_default_default |
| wstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.014 | 0.018 | 0.018 | 12 | o2_default_default |
| wstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.015 | 0.020 | 0.021 | 12 | o2_default_default |
| wstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.014 | 0.020 | 0.023 | 12 | o2_default_default |
| wstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.015 | 0.025 | 0.026 | 12 | o2_default_default |
| wstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.014 | 0.025 | 0.032 | 12 | o3_default_default |
| wstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.016 | 0.030 | 0.038 | 12 | o3_default_default |
| wstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.014 | 0.034 | 0.175 | 12 | o3_default_default |
| wstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.017 | 0.039 | 0.051 | 12 | o2_default_default |
| wstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.016 | 0.045 | 0.057 | 12 | o3_default_default |
| wstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.015 | 0.054 | 0.085 | 12 | o3_default_default |
| wstate_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.014 | 0.014 | 12 | o2_default_default |
| wstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.016 | 0.061 | 0.084 | 12 | o3_default_default |
| wstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.017 | 0.080 | 0.108 | 12 | o3_default_default |
| wstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.017 | 0.092 | 0.105 | 12 | o3_default_default |
| wstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.016 | 0.114 | 0.136 | 12 | o3_default_default |
| wstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.016 | 0.123 | 0.168 | 12 | o3_default_default |
| wstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.018 | 0.136 | 0.201 | 12 | o3_default_default |
| wstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.017 | 0.176 | 0.190 | 12 | o2_default_default |
| wstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.016 | 0.209 | 0.287 | 12 | o3_default_default |
| wstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.019 | 0.192 | 0.223 | 12 | o3_default_default |
| wstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.019 | 0.209 | 0.239 | 12 | o3_default_default |
| wstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.013 | 0.015 | 0.015 | 12 | o3_default_default |
| wstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.018 | 0.249 | 0.313 | 12 | o3_default_default |
| wstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 0.015 | 0.015 | 12 | o2_default_default |
| wstate_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.023 | 0.269 | 0.335 | 12 | o3_default_default |
| wstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 0.019 | 0.021 | 12 | o2_default_default |
| wstate_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.025 | 0.290 | 0.442 | 12 | o3_default_default |
| wstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.013 | 0.019 | 0.020 | 12 | o3_default_default |
| wstate_indep_qiskit_60 | train | 60 | 36/36 | 0 | 0.027 | 0.378 | 0.468 | 12 | o3_default_default |
| wstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.015 | 0.021 | 0.022 | 12 | o2_default_default |
| wstate_indep_qiskit_70 | train | 70 | 36/36 | 0 | 0.036 | 0.369 | 0.463 | 12 | o2_default_default |
| wstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.016 | 0.020 | 0.023 | 12 | o2_default_default |
| wstate_indep_qiskit_80 | train | 80 | 36/36 | 0 | 0.042 | 0.359 | 0.423 | 12 | o2_default_default |
| wstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.016 | 0.023 | 0.209 | 12 | o3_default_default |
| wstate_indep_qiskit_90 | train | 90 | 36/36 | 0 | 0.042 | 0.397 | 0.429 | 12 | o3_default_default |
| wstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.018 | 0.024 | 0.031 | 12 | o2_default_default |
| wstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.017 | 0.023 | 0.025 | 12 | o2_default_default |
| wstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.018 | 0.028 | 0.032 | 12 | o2_default_default |
| wstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.018 | 0.027 | 0.027 | 12 | o2_default_default |
| wstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.018 | 0.025 | 0.028 | 12 | o3_default_default |
| wstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.018 | 0.032 | 0.035 | 12 | o3_default_default |
| wstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.020 | 0.033 | 0.044 | 12 | o3_default_default |
| wstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.018 | 0.046 | 0.056 | 12 | o3_default_default |
| wstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.021 | 0.048 | 0.055 | 12 | o3_default_default |
| wstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.020 | 0.065 | 0.076 | 12 | o3_default_default |
| wstate_indep_tket_2 | train | 2 | 36/36 | 0 | 0.012 | 0.017 | 0.020 | 12 | o2_default_default |
| wstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.021 | 0.075 | 0.078 | 12 | o3_default_default |
| wstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.019 | 0.074 | 0.080 | 12 | o3_default_default |
| wstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.019 | 0.106 | 0.136 | 12 | o3_default_default |
| wstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.020 | 0.111 | 0.145 | 12 | o3_default_default |
| wstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.021 | 0.123 | 0.132 | 12 | o3_default_default |
| wstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.021 | 0.158 | 0.182 | 12 | o3_default_default |
| wstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.024 | 0.200 | 0.232 | 12 | o2_default_default |
| wstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.021 | 0.229 | 0.295 | 12 | o3_default_default |
| wstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.022 | 0.224 | 0.247 | 12 | o3_default_default |
| wstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.023 | 0.227 | 0.266 | 12 | o3_default_default |
| wstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 0.019 | 0.022 | 12 | o3_default_default |
| wstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.023 | 0.252 | 0.316 | 12 | o3_default_default |
| wstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.014 | 0.019 | 0.020 | 12 | o2_default_default |
| wstate_indep_tket_40 | train | 40 | 36/36 | 0 | 0.027 | 0.300 | 0.330 | 12 | o3_default_default |
| wstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.015 | 0.020 | 0.020 | 12 | o2_default_default |
| wstate_indep_tket_50 | train | 50 | 36/36 | 0 | 0.036 | 0.328 | 0.379 | 12 | o3_default_default |
| wstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.014 | 0.022 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_60 | train | 60 | 36/36 | 0 | 0.032 | 0.340 | 0.402 | 12 | o3_default_default |
| wstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.016 | 0.021 | 0.023 | 12 | o2_default_default |
| wstate_indep_tket_70 | train | 70 | 36/36 | 0 | 0.040 | 0.396 | 0.429 | 12 | o2_default_default |
| wstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.015 | 0.023 | 0.024 | 12 | o2_default_default |
| wstate_indep_tket_80 | train | 80 | 36/36 | 0 | 0.044 | 0.356 | 0.498 | 12 | o2_default_default |
| wstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.015 | 0.021 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 36/36 | 0 | 0.044 | 0.401 | 0.438 | 12 | o3_default_default |
| pricingcall_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.043 | 0.262 | 0.268 | 10 | o3_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.020 | 0.062 | 0.188 | 10 | o3_dense_sabre |
| pricingcall_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.028 | 0.102 | 0.116 | 10 | o2_dense_sabre |
| pricingcall_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.039 | 0.145 | 0.164 | 10 | o3_default_default |
| pricingcall_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.022 | 0.053 | 0.060 | 10 | o2_dense_sabre |
| pricingcall_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.026 | 0.104 | 0.122 | 10 | o2_dense_sabre |
| pricingcall_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.031 | 0.132 | 0.167 | 10 | o3_default_default |
| pricingput_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.041 | 0.190 | 0.202 | 10 | o3_default_default |
| pricingput_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.020 | 0.056 | 0.066 | 10 | o3_dense_sabre |
| pricingput_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.027 | 0.108 | 0.278 | 10 | o3_default_default |
| pricingput_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.034 | 0.158 | 0.333 | 10 | o3_default_default |
| pricingput_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.025 | 0.060 | 0.069 | 10 | o2_dense_sabre |
| pricingput_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.028 | 0.107 | 0.122 | 10 | o3_default_default |
| pricingput_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.036 | 0.142 | 0.155 | 10 | o3_default_default |
| qft_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.028 | 0.051 | 0.054 | 10 | o3_default_default |
| qft_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.031 | 0.059 | 0.060 | 10 | o3_default_default |
| qft_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.031 | 0.066 | 0.069 | 10 | o3_default_default |
| qft_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.038 | 0.071 | 0.092 | 10 | o3_default_default |
| qft_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.044 | 0.087 | 0.098 | 10 | o2_default_default |
| qft_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.048 | 0.096 | 0.108 | 10 | o2_default_default |
| qft_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.046 | 0.152 | 0.220 | 10 | o3_default_default |
| qft_indep_qiskit_17 | validation | 17 | 30/36 | 6 | 0.050 | 0.117 | 0.128 | 10 | o2_default_default |
| qft_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.014 | 0.016 | 12 | o3_default_default |
| qft_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.016 | 4.176 | 4.465 | 12 | o2_default_default |
| qft_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.124 | 0.480 | 0.495 | 10 | o2_default_default |
| qft_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.018 | 15.120 | 29.257 | 12 | o3_default_default |
| qft_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.170 | 0.870 | 1.086 | 10 | o2_default_default |
| qft_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.019 | 14.314 | 31.642 | 12 | o3_default_default |
| qft_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.193 | 1.347 | 1.535 | 10 | o3_default_default |
| qft_indep_qiskit_6 | validation | 6 | 35/36 | 1 | 0.019 | 41.132 | 74.716 | 11 | o3_default_default |
| qft_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.196 | 1.474 | 2.620 | 10 | o3_default_default |
| qft_indep_qiskit_7 | validation | 7 | 35/36 | 1 | 0.024 | 48.202 | 65.766 | 11 | o3_default_default |
| qft_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.224 | 1.963 | 2.544 | 10 | o3_default_default |
| qft_indep_qiskit_8 | validation | 8 | 34/36 | 2 | 0.020 | 68.777 | 71.685 | 10 | o3_default_default |
| qft_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.022 | 0.040 | 0.043 | 10 | o3_default_default |
| qft_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.021 | 0.046 | 0.048 | 10 | o3_default_default |
| qft_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.025 | 0.059 | 0.061 | 10 | o3_default_default |
| qft_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.023 | 0.059 | 0.064 | 10 | o3_default_default |
| qft_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.025 | 0.069 | 0.109 | 10 | o3_default_default |
| qft_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.032 | 0.075 | 0.078 | 10 | o2_default_default |
| qft_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.013 | 0.016 | 0.019 | 12 | o3_default_default |
| qft_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.016 | 3.963 | 4.195 | 12 | o2_default_default |
| qft_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.085 | 0.383 | 0.428 | 10 | o2_default_default |
| qft_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.018 | 14.706 | 28.234 | 12 | o3_default_default |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.130 | 0.782 | 0.989 | 10 | o2_default_default |
| qft_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.019 | 13.869 | 30.501 | 12 | o3_default_default |
| qft_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.185 | 1.350 | 1.544 | 10 | o3_default_default |
| qft_indep_tket_6 | validation | 6 | 35/36 | 1 | 0.020 | 40.498 | 75.110 | 11 | o3_default_default |
| qft_indep_tket_60 | validation | 60 | 30/36 | 6 | 0.197 | 1.595 | 2.378 | 10 | o3_default_default |
| qft_indep_tket_7 | validation | 7 | 35/36 | 1 | 0.022 | 47.256 | 66.740 | 11 | o3_default_default |
| qft_indep_tket_8 | validation | 8 | 34/36 | 2 | 0.019 | 70.184 | 73.264 | 10 | o3_default_default |
| qft_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.020 | 0.039 | 0.042 | 10 | o3_default_default |
| qftentangled_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.022 | 0.047 | 0.054 | 10 | o2_default_default |
| qftentangled_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.024 | 0.060 | 0.088 | 10 | o3_default_default |
| qftentangled_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.027 | 0.061 | 0.070 | 10 | o3_default_default |
| qftentangled_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.026 | 0.071 | 0.102 | 10 | o3_default_default |
| qftentangled_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.028 | 0.078 | 0.114 | 10 | o2_default_default |
| qftentangled_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.029 | 0.080 | 0.098 | 10 | o3_default_default |
| qftentangled_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.033 | 0.093 | 0.126 | 10 | o3_default_default |
| qftentangled_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.013 | 0.016 | 0.018 | 12 | o3_default_default |
| qftentangled_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.016 | 5.677 | 5.924 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.086 | 0.287 | 0.337 | 10 | o3_default_default |
| qftentangled_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.019 | 26.873 | 30.847 | 12 | o3_default_default |
| qftentangled_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.122 | 0.891 | 1.012 | 10 | o2_default_default |
| qftentangled_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.021 | 31.414 | 35.924 | 12 | o3_default_default |
| qftentangled_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.167 | 1.147 | 1.298 | 10 | o3_default_default |
| qftentangled_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.021 | 58.415 | 83.595 | 12 | o2_default_default |
| qftentangled_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.231 | 1.525 | 1.649 | 10 | o3_default_default |
| qftentangled_indep_qiskit_7 | validation | 7 | 31/36 | 5 | 0.022 | 0.034 | 66.331 | 10 | o2_default_default |
| qftentangled_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.313 | 2.391 | 2.573 | 10 | o3_default_default |
| qftentangled_indep_qiskit_8 | validation | 8 | 30/36 | 6 | 0.021 | 0.048 | 0.060 | 10 | o2_dense_sabre |
| qftentangled_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.023 | 0.053 | 0.075 | 10 | o3_default_default |
| qftentangled_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.026 | 0.049 | 0.064 | 10 | o2_default_default |
| qftentangled_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.028 | 0.072 | 0.087 | 10 | o3_default_default |
| qftentangled_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.031 | 0.068 | 0.068 | 10 | o3_default_default |
| qftentangled_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.031 | 0.107 | 0.128 | 10 | o3_default_default |
| qftentangled_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.043 | 0.097 | 0.102 | 10 | o2_default_default |
| qftentangled_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.015 | 0.019 | 0.020 | 12 | o3_default_default |
| qftentangled_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.018 | 6.181 | 6.318 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.094 | 0.374 | 0.386 | 10 | o3_default_default |
| qftentangled_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.018 | 26.478 | 30.638 | 12 | o3_default_default |
| qftentangled_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.120 | 1.036 | 1.188 | 10 | o2_default_default |
| qftentangled_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.019 | 32.272 | 36.625 | 12 | o3_default_default |
| qftentangled_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.169 | 1.073 | 1.159 | 10 | o3_default_default |
| qftentangled_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.020 | 58.131 | 82.928 | 12 | o2_default_default |
| qftentangled_indep_tket_7 | validation | 7 | 31/36 | 5 | 0.019 | 0.033 | 67.600 | 10 | o2_default_default |
| qftentangled_indep_tket_8 | validation | 8 | 30/36 | 6 | 0.019 | 0.036 | 0.039 | 10 | o2_dense_sabre |
| qftentangled_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.021 | 0.038 | 0.051 | 10 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 1307 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Esito ignoto alla soglia | Minimo timeout stimato |
| --- | --- | --- | --- | --- |
| 30 | 463 | 1307 | 0 | 1770 |
| 60 | 158 | 1307 | 0 | 1465 |
| 100 | 1 | 1307 | 0 | 1308 |
| 120 | 0 | 1307 | 1307 | 0 |
| 300 | 0 | 1307 | 1307 | 0 |
| 600 | 0 | 1307 | 1307 | 0 |
| 900 | 0 | 1307 | 1307 | 0 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta. Questi casi restano ignoti e non sono inclusi nel minimo stimato. La stima usa i tempi osservati e non prevede l'effetto di cambiare i worker.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 5641 |
| Non eleggibili | 479 |
| Esempi RAG | 396 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

# Dataset Qiskit full — ibm_falcon_27

Scheda generata automaticamente dagli artefatti del Dataset. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 27 |
| Hash target | b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104 |
| Qiskit | 2.5.0 |
| MQT Bench | 2.2.3 |
| MQT Predictor | 2.4.0 |
| Circuiti totali | 510 |
| Circuiti compatibili | 410 |
| Circuiti incompatibili | 100 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker nei risultati | 6 |
| Timeout nei risultati (s) | 100 |
| Fonte dei parametri | run_provenance |
| Cache hit | 14760 |
| Durata invocazione | 6.471 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati. I parametri nei risultati provengono dai singoli tentativi, quando disponibili; per i vecchi dati senza questa informazione si usa lo stato della generazione.



## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 14760 | - |
| Osservati | 14760 | 100.0% |
| Mancanti | 0 | - |
| Successi | 14278 | 96.7% |
| Failure | 0 | 0.0% |
| Timeout | 482 | 3.3% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 14278 | 0.005 | 0.013 | 1.305 | 5.389 | 96.334 |
| Non-lookahead | 12300 | 0.005 | 0.012 | 0.015 | 0.026 | 0.394 |
| Lookahead | 1978 | 0.006 | 3.726 | 9.329 | 41.602 | 96.334 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 1230/1230 | 0 | 0.011 | 0.021 | 0.359 | 410 | 98 | 98 | 253 |
| o3_default_default | baseline | 3 | default | default | 1230/1230 | 0 | 0.013 | 0.027 | 0.394 | 410 | 198 | 273 | 379 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 1230/1230 | 0 | 0.011 | 0.019 | 0.045 | 410 | 1 | 6 | 66 |
| o2_dense_sabre | layout | 2 | dense | sabre | 1230/1230 | 0 | 0.012 | 0.017 | 0.237 | 410 | 72 | 72 | 235 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 1230/1230 | 0 | 0.011 | 0.015 | 0.186 | 410 | 4 | 4 | 8 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 1230/1230 | 0 | 0.012 | 0.026 | 0.042 | 410 | 4 | 10 | 82 |
| o3_dense_sabre | layout | 3 | dense | sabre | 1230/1230 | 0 | 0.013 | 0.024 | 0.262 | 410 | 26 | 97 | 156 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 1230/1230 | 0 | 0.013 | 0.024 | 0.047 | 410 | 0 | 0 | 6 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 989/1230 | 241 | 3.826 | 39.495 | 94.926 | 302 | 0 | 0 | 6 |
| o2_sabre_basic | routing | 2 | sabre | basic | 1230/1230 | 0 | 0.014 | 0.037 | 0.204 | 410 | 0 | 0 | 1 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 989/1230 | 241 | 3.650 | 42.510 | 96.334 | 303 | 7 | 7 | 37 |
| o3_sabre_basic | routing | 3 | sabre | basic | 1230/1230 | 0 | 0.016 | 0.051 | 0.264 | 410 | 0 | 0 | 1 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.038 | 38.537 | 70.704 | 12 | o3_dense_sabre |
| ae_indep_qiskit_11 | train | 11 | 35/36 | 1 | 0.021 | 38.931 | 87.798 | 11 | o3_dense_sabre |
| ae_indep_qiskit_12 | train | 12 | 33/36 | 3 | 0.020 | 60.427 | 85.598 | 10 | o3_dense_sabre |
| ae_indep_qiskit_13 | train | 13 | 32/36 | 4 | 0.020 | 24.640 | 76.353 | 10 | o2_dense_sabre |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.009 | 0.013 | 0.015 | 12 | o2_default_default |
| ae_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 1.255 | 1.314 | 12 | o3_default_default |
| ae_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.010 | 1.697 | 2.062 | 12 | o3_default_default |
| ae_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.013 | 2.528 | 2.627 | 12 | o2_dense_sabre |
| ae_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.015 | 4.859 | 5.286 | 12 | o2_dense_sabre |
| ae_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.015 | 7.848 | 8.243 | 12 | o3_default_default |
| ae_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 11.622 | 12.926 | 12 | o3_default_default |
| ae_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.017 | 20.176 | 26.598 | 12 | o3_default_default |
| ae_indep_tket_10 | train | 10 | 36/36 | 0 | 0.018 | 44.960 | 79.352 | 12 | o3_dense_sabre |
| ae_indep_tket_11 | train | 11 | 34/36 | 2 | 0.019 | 38.491 | 42.626 | 11 | o3_dense_sabre |
| ae_indep_tket_12 | train | 12 | 33/36 | 3 | 0.021 | 65.218 | 92.298 | 10 | o3_dense_sabre |
| ae_indep_tket_2 | train | 2 | 36/36 | 0 | 0.009 | 0.012 | 0.020 | 12 | o2_default_default |
| ae_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 1.220 | 1.268 | 12 | o3_default_default |
| ae_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 2.044 | 2.199 | 12 | o3_default_default |
| ae_indep_tket_5 | train | 5 | 36/36 | 0 | 0.012 | 2.396 | 2.576 | 12 | o2_dense_sabre |
| ae_indep_tket_6 | train | 6 | 36/36 | 0 | 0.013 | 4.509 | 4.885 | 12 | o3_dense_sabre |
| ae_indep_tket_7 | train | 7 | 36/36 | 0 | 0.013 | 7.228 | 7.397 | 12 | o3_default_default |
| ae_indep_tket_8 | train | 8 | 36/36 | 0 | 0.015 | 10.622 | 12.179 | 12 | o3_default_default |
| ae_indep_tket_9 | train | 9 | 36/36 | 0 | 0.015 | 19.215 | 24.710 | 12 | o3_default_default |
| dj_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.011 | 3.908 | 3.953 | 12 | o2_dense_sabre |
| dj_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.011 | 5.464 | 5.734 | 12 | o2_default_default |
| dj_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.012 | 4.337 | 4.378 | 12 | o2_default_default |
| dj_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.011 | 4.562 | 4.746 | 12 | o2_default_default |
| dj_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.013 | 9.604 | 13.380 | 12 | o2_default_default |
| dj_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.012 | 8.980 | 9.477 | 12 | o3_default_default |
| dj_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.012 | 28.876 | 94.926 | 12 | o2_default_default |
| dj_indep_qiskit_17 | train | 17 | 34/36 | 2 | 0.012 | 8.191 | 20.813 | 10 | o3_default_default |
| dj_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.013 | 29.545 | 30.816 | 12 | o2_default_default |
| dj_indep_qiskit_19 | train | 19 | 35/36 | 1 | 0.012 | 12.648 | 32.446 | 11 | o2_default_default |
| dj_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.009 | 0.014 | 0.021 | 12 | o3_default_default |
| dj_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.015 | 28.930 | 32.208 | 12 | o3_default_default |
| dj_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.013 | 27.416 | 87.911 | 12 | o3_default_default |
| dj_indep_qiskit_22 | train | 22 | 34/36 | 2 | 0.013 | 15.606 | 19.133 | 10 | o3_default_default |
| dj_indep_qiskit_23 | train | 23 | 32/36 | 4 | 0.013 | 29.875 | 69.515 | 10 | o2_default_default |
| dj_indep_qiskit_24 | train | 24 | 35/36 | 1 | 0.012 | 45.690 | 86.014 | 11 | o3_sabre_sabre |
| dj_indep_qiskit_25 | train | 25 | 33/36 | 3 | 0.014 | 25.917 | 60.264 | 10 | o2_default_default |
| dj_indep_qiskit_26 | train | 26 | 34/36 | 2 | 0.014 | 35.980 | 49.206 | 10 | o3_sabre_sabre |
| dj_indep_qiskit_27 | train | 27 | 33/36 | 3 | 0.014 | 37.532 | 39.394 | 10 | o3_default_default |
| dj_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.009 | 0.012 | 0.016 | 12 | o3_default_default |
| dj_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.009 | 0.011 | 0.012 | 12 | o3_default_default |
| dj_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.010 | 0.848 | 0.892 | 12 | o2_default_default |
| dj_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.011 | 1.608 | 1.656 | 12 | o3_default_default |
| dj_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.011 | 1.720 | 1.770 | 12 | o2_default_default |
| dj_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.011 | 2.108 | 2.510 | 12 | o3_default_default |
| dj_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.011 | 2.182 | 2.881 | 12 | o2_default_default |
| dj_indep_tket_10 | train | 10 | 36/36 | 0 | 0.011 | 3.881 | 3.952 | 12 | o2_dense_sabre |
| dj_indep_tket_11 | train | 11 | 36/36 | 0 | 0.011 | 5.567 | 5.960 | 12 | o2_default_default |
| dj_indep_tket_12 | train | 12 | 36/36 | 0 | 0.011 | 4.379 | 4.607 | 12 | o3_default_default |
| dj_indep_tket_13 | train | 13 | 36/36 | 0 | 0.012 | 4.386 | 4.681 | 12 | o2_default_default |
| dj_indep_tket_14 | train | 14 | 36/36 | 0 | 0.012 | 9.323 | 14.606 | 12 | o2_default_default |
| dj_indep_tket_15 | train | 15 | 36/36 | 0 | 0.012 | 9.451 | 10.036 | 12 | o3_default_default |
| dj_indep_tket_16 | train | 16 | 35/36 | 1 | 0.014 | 7.345 | 94.073 | 11 | o3_default_default |
| dj_indep_tket_17 | train | 17 | 34/36 | 2 | 0.013 | 8.857 | 21.679 | 10 | o3_default_default |
| dj_indep_tket_18 | train | 18 | 36/36 | 0 | 0.013 | 30.435 | 33.289 | 12 | o2_default_default |
| dj_indep_tket_19 | train | 19 | 35/36 | 1 | 0.013 | 12.887 | 33.008 | 11 | o2_default_default |
| dj_indep_tket_2 | train | 2 | 36/36 | 0 | 0.008 | 0.011 | 0.012 | 12 | o3_default_default |
| dj_indep_tket_20 | train | 20 | 36/36 | 0 | 0.013 | 31.205 | 32.985 | 12 | o3_default_default |
| dj_indep_tket_21 | train | 21 | 36/36 | 0 | 0.013 | 28.146 | 90.847 | 12 | o3_default_default |
| dj_indep_tket_22 | train | 22 | 34/36 | 2 | 0.012 | 16.388 | 19.260 | 10 | o2_default_default |
| dj_indep_tket_23 | train | 23 | 32/36 | 4 | 0.013 | 30.911 | 70.364 | 10 | o2_default_default |
| dj_indep_tket_24 | train | 24 | 35/36 | 1 | 0.013 | 46.586 | 86.666 | 11 | o3_default_default |
| dj_indep_tket_25 | train | 25 | 33/36 | 3 | 0.013 | 27.330 | 60.665 | 10 | o2_default_default |
| dj_indep_tket_26 | train | 26 | 34/36 | 2 | 0.014 | 36.510 | 49.429 | 10 | o3_sabre_sabre |
| dj_indep_tket_27 | train | 27 | 33/36 | 3 | 0.014 | 38.101 | 41.607 | 10 | o3_default_default |
| dj_indep_tket_3 | train | 3 | 36/36 | 0 | 0.009 | 0.011 | 0.016 | 12 | o3_default_default |
| dj_indep_tket_4 | train | 4 | 36/36 | 0 | 0.009 | 0.011 | 0.011 | 12 | o3_default_default |
| dj_indep_tket_5 | train | 5 | 36/36 | 0 | 0.010 | 0.830 | 1.063 | 12 | o2_default_default |
| dj_indep_tket_6 | train | 6 | 36/36 | 0 | 0.010 | 1.623 | 1.641 | 12 | o3_default_default |
| dj_indep_tket_7 | train | 7 | 36/36 | 0 | 0.011 | 1.823 | 2.037 | 12 | o2_default_default |
| dj_indep_tket_8 | train | 8 | 36/36 | 0 | 0.010 | 2.137 | 2.461 | 12 | o3_default_default |
| dj_indep_tket_9 | train | 9 | 36/36 | 0 | 0.011 | 2.154 | 3.240 | 12 | o2_default_default |
| graphstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.011 | 1.834 | 1.925 | 12 | o3_default_default |
| graphstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.011 | 3.485 | 3.683 | 12 | o3_default_default |
| graphstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.012 | 2.244 | 3.152 | 12 | o2_default_default |
| graphstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.011 | 2.197 | 2.527 | 12 | o3_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.012 | 4.044 | 4.594 | 12 | o3_default_default |
| graphstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.012 | 3.572 | 4.591 | 12 | o3_sabre_lookahead |
| graphstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.012 | 4.679 | 5.230 | 12 | o3_default_default |
| graphstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.014 | 4.425 | 4.868 | 12 | o3_default_default |
| graphstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.013 | 4.579 | 4.665 | 12 | o3_default_default |
| graphstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.013 | 4.580 | 6.738 | 12 | o3_sabre_lookahead |
| graphstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.012 | 4.908 | 5.343 | 12 | o2_default_default |
| graphstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.014 | 7.706 | 8.047 | 12 | o3_default_default |
| graphstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.014 | 7.555 | 8.074 | 12 | o2_default_default |
| graphstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.014 | 7.815 | 7.948 | 12 | o3_sabre_lookahead |
| graphstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.014 | 7.913 | 9.245 | 12 | o3_sabre_lookahead |
| graphstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.015 | 8.824 | 11.559 | 12 | o3_default_default |
| graphstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.015 | 9.094 | 12.208 | 12 | o3_sabre_lookahead |
| graphstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.017 | 8.578 | 10.295 | 12 | o3_default_default |
| graphstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.010 | 0.628 | 0.788 | 12 | o3_default_default |
| graphstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.011 | 1.048 | 1.156 | 12 | o2_default_default |
| graphstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.011 | 1.459 | 1.630 | 12 | o2_dense_sabre |
| graphstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.012 | 1.767 | 1.951 | 12 | o2_default_default |
| graphstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.011 | 1.752 | 1.923 | 12 | o3_default_default |
| graphstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.012 | 1.905 | 1.949 | 12 | o3_default_default |
| graphstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.013 | 1.917 | 2.162 | 12 | o3_default_default |
| graphstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.013 | 2.155 | 2.787 | 12 | o3_default_default |
| graphstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.011 | 1.926 | 2.143 | 12 | o3_default_default |
| graphstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.012 | 2.135 | 2.187 | 12 | o2_default_default |
| graphstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.014 | 3.324 | 4.216 | 12 | o3_default_default |
| graphstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.012 | 2.075 | 2.414 | 12 | o3_default_default |
| graphstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.014 | 3.974 | 4.273 | 12 | o3_default_default |
| graphstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.013 | 3.980 | 4.226 | 12 | o3_default_default |
| graphstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.012 | 4.376 | 5.592 | 12 | o3_default_default |
| graphstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.012 | 4.512 | 4.980 | 12 | o3_default_default |
| graphstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.014 | 5.252 | 5.481 | 12 | o3_default_default |
| graphstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.013 | 4.658 | 8.628 | 12 | o2_default_default |
| graphstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.013 | 4.961 | 5.703 | 12 | o3_sabre_lookahead |
| graphstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.014 | 6.269 | 7.837 | 12 | o3_default_default |
| graphstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.015 | 6.178 | 7.895 | 12 | o3_default_default |
| graphstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.014 | 7.329 | 10.279 | 12 | o3_default_default |
| graphstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.014 | 7.911 | 8.503 | 12 | o3_default_default |
| graphstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.014 | 10.886 | 12.360 | 12 | o3_sabre_sabre |
| graphstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.016 | 11.302 | 12.293 | 12 | o2_sabre_sabre |
| graphstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.010 | 0.635 | 0.771 | 12 | o3_default_default |
| graphstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.011 | 1.110 | 1.122 | 12 | o3_default_default |
| graphstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.011 | 1.571 | 1.753 | 12 | o3_default_default |
| graphstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.011 | 1.778 | 1.996 | 12 | o3_default_default |
| graphstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.011 | 1.720 | 1.787 | 12 | o3_default_default |
| graphstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.012 | 1.826 | 1.950 | 12 | o3_default_default |
| graphstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.012 | 1.950 | 1.966 | 12 | o3_default_default |
| portfolioqaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 4.011 | 4.613 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 6.344 | 9.796 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 40.570 | 44.019 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.016 | 47.436 | 53.072 | 10 | o3_dense_sabre |
| portfolioqaoa_indep_qiskit_7 | train | 7 | 32/36 | 4 | 0.016 | 14.610 | 34.869 | 10 | o2_dense_sabre |
| portfolioqaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 4.167 | 4.759 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 6.608 | 10.296 | 12 | o3_dense_sabre |
| portfolioqaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.014 | 39.590 | 44.403 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_tket_6 | train | 6 | 34/36 | 2 | 0.015 | 48.163 | 56.618 | 10 | o2_dense_sabre |
| portfolioqaoa_indep_tket_7 | train | 7 | 32/36 | 4 | 0.016 | 15.096 | 35.089 | 10 | o2_dense_sabre |
| portfoliovqe_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.026 | 0.046 | 0.069 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.026 | 0.060 | 0.077 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 3.267 | 3.827 | 12 | o3_dense_sabre |
| portfoliovqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 4.946 | 7.619 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 31.909 | 37.413 | 12 | o2_dense_sabre |
| portfoliovqe_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.013 | 40.877 | 45.853 | 10 | o2_dense_sabre |
| portfoliovqe_indep_qiskit_7 | train | 7 | 32/36 | 4 | 0.016 | 12.546 | 28.014 | 10 | o2_dense_sabre |
| portfoliovqe_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.018 | 0.030 | 0.032 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.020 | 0.039 | 0.054 | 10 | o2_dense_sabre |
| portfoliovqe_indep_tket_10 | train | 10 | 30/36 | 6 | 0.024 | 0.050 | 0.056 | 10 | o3_default_default |
| portfoliovqe_indep_tket_11 | train | 11 | 30/36 | 6 | 0.025 | 0.071 | 0.244 | 10 | o3_default_default |
| portfoliovqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 3.351 | 4.071 | 12 | o2_dense_sabre |
| portfoliovqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 5.074 | 8.192 | 12 | o2_default_default |
| portfoliovqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.014 | 33.228 | 35.816 | 12 | o2_dense_sabre |
| portfoliovqe_indep_tket_6 | train | 6 | 34/36 | 2 | 0.015 | 41.258 | 46.462 | 10 | o2_dense_sabre |
| portfoliovqe_indep_tket_7 | train | 7 | 32/36 | 4 | 0.016 | 12.454 | 28.909 | 10 | o2_dense_sabre |
| portfoliovqe_indep_tket_8 | train | 8 | 30/36 | 6 | 0.018 | 0.034 | 0.038 | 10 | o2_default_default |
| portfoliovqe_indep_tket_9 | train | 9 | 30/36 | 6 | 0.022 | 0.039 | 0.054 | 10 | o2_dense_sabre |
| qaoa_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.013 | 4.882 | 5.563 | 12 | o3_default_default |
| qaoa_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.012 | 2.244 | 2.538 | 12 | o3_default_default |
| qaoa_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.012 | 2.404 | 2.832 | 12 | o2_default_default |
| qaoa_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.013 | 2.814 | 3.208 | 12 | o3_default_default |
| qaoa_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.021 | 8.727 | 11.101 | 12 | o3_default_default |
| qaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 1.875 | 2.011 | 12 | o3_dense_sabre |
| qaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.011 | 1.841 | 1.979 | 12 | o3_default_default |
| qaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.011 | 2.031 | 2.220 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.012 | 3.411 | 3.769 | 12 | o3_default_default |
| qaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.012 | 2.417 | 2.497 | 12 | o3_default_default |
| qaoa_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.014 | 3.738 | 3.974 | 12 | o3_default_default |
| qaoa_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.012 | 4.572 | 5.837 | 12 | o3_default_default |
| qaoa_indep_tket_10 | train | 10 | 36/36 | 0 | 0.014 | 5.364 | 5.538 | 12 | o3_default_default |
| qaoa_indep_tket_11 | train | 11 | 36/36 | 0 | 0.014 | 2.241 | 2.493 | 12 | o3_default_default |
| qaoa_indep_tket_12 | train | 12 | 36/36 | 0 | 0.013 | 2.809 | 2.863 | 12 | o2_default_default |
| qaoa_indep_tket_13 | train | 13 | 36/36 | 0 | 0.016 | 2.496 | 3.213 | 12 | o3_default_default |
| qaoa_indep_tket_14 | train | 14 | 36/36 | 0 | 0.018 | 9.843 | 11.637 | 12 | o3_default_default |
| qaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 2.002 | 2.205 | 12 | o3_dense_sabre |
| qaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.013 | 1.856 | 1.998 | 12 | o3_default_default |
| qaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.011 | 2.295 | 2.364 | 12 | o2_dense_sabre |
| qaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.012 | 3.431 | 3.643 | 12 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.011 | 2.469 | 2.722 | 12 | o3_default_default |
| qaoa_indep_tket_8 | train | 8 | 36/36 | 0 | 0.013 | 3.681 | 3.984 | 12 | o3_default_default |
| qaoa_indep_tket_9 | train | 9 | 36/36 | 0 | 0.013 | 4.412 | 5.761 | 12 | o3_default_default |
| qnn_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o3_default_default |
| qnn_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 2.290 | 2.608 | 12 | o2_dense_sabre |
| qnn_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 4.463 | 5.027 | 12 | o3_default_default |
| qnn_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 9.613 | 9.906 | 12 | o2_default_default |
| qnn_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.017 | 20.836 | 22.072 | 12 | o3_dense_sabre |
| qnn_indep_qiskit_7 | train | 7 | 34/36 | 2 | 0.018 | 37.325 | 57.831 | 10 | o2_dense_sabre |
| qnn_indep_tket_2 | train | 2 | 36/36 | 0 | 0.007 | 0.010 | 0.011 | 12 | o3_default_default |
| qnn_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 2.534 | 2.636 | 12 | o2_dense_sabre |
| qnn_indep_tket_4 | train | 4 | 36/36 | 0 | 0.013 | 4.216 | 4.635 | 12 | o3_default_default |
| qnn_indep_tket_5 | train | 5 | 36/36 | 0 | 0.016 | 9.656 | 9.996 | 12 | o2_default_default |
| qnn_indep_tket_6 | train | 6 | 36/36 | 0 | 0.014 | 21.458 | 22.326 | 12 | o2_dense_sabre |
| qnn_indep_tket_7 | train | 7 | 34/36 | 2 | 0.014 | 37.654 | 58.261 | 10 | o2_dense_sabre |
| random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o3_default_default |
| random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 3.213 | 3.310 | 12 | o2_dense_sabre |
| random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 4.075 | 4.993 | 12 | o2_dense_sabre |
| random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 7.750 | 8.421 | 12 | o3_default_default |
| random_indep_qiskit_6 | train | 6 | 32/36 | 4 | 0.015 | 12.691 | 28.313 | 10 | o2_dense_sabre |
| random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.016 | 0.028 | 0.034 | 10 | o3_default_default |
| random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.018 | 0.023 | 0.025 | 10 | o2_default_default |
| random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.007 | 0.010 | 0.014 | 12 | o3_default_default |
| random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 2.917 | 3.163 | 12 | o2_dense_sabre |
| random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 4.150 | 5.073 | 12 | o2_dense_sabre |
| random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 7.657 | 8.424 | 12 | o2_default_default |
| random_indep_tket_6 | train | 6 | 32/36 | 4 | 0.016 | 12.745 | 28.437 | 10 | o2_dense_sabre |
| random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.016 | 0.028 | 0.031 | 10 | o3_default_default |
| random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.018 | 0.027 | 0.028 | 10 | o2_default_default |
| realamprandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.021 | 0.053 | 0.062 | 10 | o3_default_default |
| realamprandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.025 | 0.054 | 0.078 | 10 | o3_default_default |
| realamprandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o2_default_default |
| realamprandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 3.204 | 3.582 | 12 | o2_dense_sabre |
| realamprandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 5.153 | 7.920 | 12 | o2_default_default |
| realamprandom_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.013 | 32.863 | 36.101 | 12 | o3_dense_sabre |
| realamprandom_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.013 | 40.362 | 45.281 | 10 | o2_dense_sabre |
| realamprandom_indep_qiskit_7 | train | 7 | 32/36 | 4 | 0.017 | 12.966 | 28.896 | 10 | o2_dense_sabre |
| realamprandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.018 | 0.029 | 0.033 | 10 | o3_default_default |
| realamprandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.020 | 0.038 | 0.044 | 10 | o3_dense_sabre |
| realamprandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.024 | 0.050 | 0.053 | 10 | o3_default_default |
| realamprandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.026 | 0.067 | 0.132 | 10 | o3_default_default |
| realamprandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.011 | 12 | o2_default_default |
| realamprandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 3.346 | 4.105 | 12 | o2_dense_sabre |
| realamprandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 5.236 | 7.917 | 12 | o2_default_default |
| realamprandom_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 33.291 | 36.934 | 12 | o3_dense_sabre |
| realamprandom_indep_tket_6 | train | 6 | 34/36 | 2 | 0.014 | 40.931 | 45.330 | 10 | o2_dense_sabre |
| realamprandom_indep_tket_7 | train | 7 | 32/36 | 4 | 0.017 | 12.642 | 28.844 | 10 | o2_dense_sabre |
| realamprandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.017 | 0.036 | 0.204 | 10 | o3_default_default |
| realamprandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.020 | 0.045 | 0.186 | 10 | o3_dense_sabre |
| su2random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o2_default_default |
| su2random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.011 | 3.388 | 4.081 | 12 | o2_dense_sabre |
| su2random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.011 | 5.230 | 7.755 | 12 | o2_default_default |
| su2random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.013 | 32.423 | 35.458 | 12 | o3_dense_sabre |
| su2random_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.014 | 41.465 | 46.040 | 10 | o2_dense_sabre |
| su2random_indep_qiskit_7 | train | 7 | 32/36 | 4 | 0.016 | 12.560 | 28.160 | 10 | o2_dense_sabre |
| su2random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.018 | 0.029 | 0.031 | 10 | o3_default_default |
| su2random_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.022 | 0.039 | 0.055 | 10 | o3_dense_sabre |
| su2random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o3_default_default |
| su2random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 3.464 | 4.583 | 12 | o2_dense_sabre |
| su2random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.011 | 5.572 | 8.323 | 12 | o2_default_default |
| su2random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 34.213 | 38.326 | 12 | o3_dense_sabre |
| su2random_indep_tket_6 | train | 6 | 34/36 | 2 | 0.015 | 43.312 | 46.697 | 10 | o2_dense_sabre |
| su2random_indep_tket_7 | train | 7 | 32/36 | 4 | 0.016 | 13.330 | 29.700 | 10 | o2_dense_sabre |
| su2random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.018 | 0.029 | 0.033 | 10 | o3_default_default |
| su2random_indep_tket_9 | train | 9 | 30/36 | 6 | 0.022 | 0.048 | 0.050 | 10 | o3_dense_sabre |
| twolocalrandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.022 | 0.055 | 0.063 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.026 | 0.052 | 0.093 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.012 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 3.401 | 3.763 | 12 | o2_dense_sabre |
| twolocalrandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.011 | 5.215 | 7.676 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.013 | 32.646 | 35.986 | 12 | o3_dense_sabre |
| twolocalrandom_indep_qiskit_6 | train | 6 | 34/36 | 2 | 0.014 | 40.937 | 45.007 | 10 | o2_dense_sabre |
| twolocalrandom_indep_qiskit_7 | train | 7 | 32/36 | 4 | 0.016 | 12.846 | 29.496 | 10 | o2_dense_sabre |
| twolocalrandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.017 | 0.031 | 0.033 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.020 | 0.038 | 0.044 | 10 | o3_dense_sabre |
| twolocalrandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.023 | 0.055 | 0.065 | 10 | o3_default_default |
| twolocalrandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.025 | 0.061 | 0.084 | 10 | o3_default_default |
| twolocalrandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.008 | 0.011 | 0.016 | 12 | o2_default_default |
| twolocalrandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 3.417 | 3.684 | 12 | o2_dense_sabre |
| twolocalrandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 5.253 | 7.851 | 12 | o2_default_default |
| twolocalrandom_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 32.353 | 36.938 | 12 | o3_dense_sabre |
| twolocalrandom_indep_tket_6 | train | 6 | 34/36 | 2 | 0.014 | 40.443 | 47.016 | 10 | o2_dense_sabre |
| twolocalrandom_indep_tket_7 | train | 7 | 32/36 | 4 | 0.017 | 13.131 | 29.332 | 10 | o2_dense_sabre |
| twolocalrandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.021 | 0.029 | 0.034 | 10 | o3_default_default |
| twolocalrandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.021 | 0.039 | 0.052 | 10 | o3_dense_sabre |
| vqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.010 | 0.463 | 2.555 | 12 | o3_default_default |
| vqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.010 | 0.015 | 2.335 | 12 | o3_default_default |
| vqe_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.010 | 2.274 | 3.395 | 12 | o3_default_default |
| vqe_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.012 | 3.247 | 3.842 | 12 | o3_default_default |
| vqe_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.011 | 3.800 | 3.987 | 12 | o2_default_default |
| vqe_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.013 | 3.222 | 3.668 | 12 | o2_default_default |
| vqe_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.013 | 3.499 | 7.473 | 12 | o3_default_default |
| vqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.009 | 0.010 | 0.011 | 12 | o2_default_default |
| vqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.009 | 0.015 | 0.016 | 12 | o3_default_default |
| vqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.009 | 0.012 | 0.012 | 12 | o3_default_default |
| vqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.010 | 0.014 | 0.016 | 12 | o3_default_default |
| vqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.010 | 0.012 | 0.012 | 12 | o3_default_default |
| vqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.010 | 0.013 | 0.015 | 12 | o2_default_default |
| vqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.011 | 0.013 | 0.014 | 12 | o3_default_default |
| vqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.011 | 0.441 | 2.682 | 12 | o3_default_default |
| vqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.011 | 0.018 | 3.168 | 12 | o3_default_default |
| vqe_indep_tket_12 | train | 12 | 36/36 | 0 | 0.011 | 2.148 | 3.251 | 12 | o3_default_default |
| vqe_indep_tket_13 | train | 13 | 36/36 | 0 | 0.011 | 3.286 | 3.482 | 12 | o3_default_default |
| vqe_indep_tket_14 | train | 14 | 36/36 | 0 | 0.012 | 3.718 | 4.062 | 12 | o2_default_default |
| vqe_indep_tket_15 | train | 15 | 36/36 | 0 | 0.012 | 3.277 | 3.650 | 12 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.013 | 3.568 | 7.666 | 12 | o3_default_default |
| vqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.009 | 0.011 | 0.012 | 12 | o2_default_default |
| vqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.010 | 0.014 | 0.015 | 12 | o3_default_default |
| vqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.011 | 0.013 | 0.015 | 12 | o3_default_default |
| vqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.012 | 0.021 | 0.027 | 12 | o2_default_default |
| vqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.012 | 0.014 | 0.014 | 12 | o3_default_default |
| vqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.012 | 0.015 | 0.022 | 12 | o2_default_default |
| vqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.012 | 0.014 | 0.015 | 12 | o3_default_default |
| wstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.013 | 0.542 | 2.646 | 12 | o3_default_default |
| wstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.011 | 1.536 | 2.360 | 12 | o2_default_default |
| wstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.013 | 2.653 | 2.698 | 12 | o2_default_default |
| wstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.012 | 2.632 | 2.871 | 12 | o2_default_default |
| wstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.014 | 2.762 | 3.732 | 12 | o3_default_default |
| wstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.013 | 3.126 | 5.927 | 12 | o2_default_default |
| wstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.013 | 3.560 | 6.442 | 12 | o2_default_default |
| wstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.014 | 4.544 | 9.157 | 12 | o2_default_default |
| wstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.013 | 3.690 | 4.242 | 12 | o2_default_default |
| wstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.015 | 6.587 | 7.133 | 12 | o2_default_default |
| wstate_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.008 | 0.011 | 0.012 | 12 | o3_default_default |
| wstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.014 | 6.276 | 22.716 | 12 | o2_default_default |
| wstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.015 | 7.084 | 15.816 | 12 | o2_default_default |
| wstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.018 | 7.531 | 10.057 | 12 | o3_default_default |
| wstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.014 | 14.817 | 47.040 | 12 | o3_default_default |
| wstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.016 | 8.310 | 10.592 | 12 | o3_default_default |
| wstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.015 | 10.156 | 15.449 | 12 | o3_default_default |
| wstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.016 | 11.800 | 13.004 | 12 | o3_sabre_lookahead |
| wstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.016 | 14.653 | 25.187 | 12 | o3_default_default |
| wstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.009 | 0.011 | 0.019 | 12 | o2_default_default |
| wstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.010 | 0.018 | 0.024 | 12 | o3_default_default |
| wstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.010 | 0.013 | 0.013 | 12 | o3_default_default |
| wstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.009 | 0.012 | 0.012 | 12 | o2_default_default |
| wstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.010 | 0.012 | 0.012 | 12 | o3_default_default |
| wstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.010 | 0.014 | 0.015 | 12 | o2_default_default |
| wstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.010 | 0.013 | 0.014 | 12 | o2_default_default |
| wstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.011 | 0.546 | 2.385 | 12 | o2_default_default |
| wstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.011 | 1.530 | 2.353 | 12 | o2_default_default |
| wstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.013 | 2.577 | 2.851 | 12 | o3_default_default |
| wstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.011 | 2.901 | 2.936 | 12 | o2_default_default |
| wstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.013 | 2.572 | 3.570 | 12 | o2_default_default |
| wstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.012 | 3.034 | 6.464 | 12 | o2_default_default |
| wstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.014 | 3.479 | 6.477 | 12 | o2_default_default |
| wstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.013 | 4.520 | 8.743 | 12 | o3_default_default |
| wstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.014 | 3.420 | 4.188 | 12 | o3_default_default |
| wstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.015 | 6.395 | 6.988 | 12 | o3_default_default |
| wstate_indep_tket_2 | train | 2 | 36/36 | 0 | 0.009 | 0.012 | 0.016 | 12 | o3_default_default |
| wstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.015 | 5.978 | 22.653 | 12 | o2_default_default |
| wstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.014 | 6.496 | 16.014 | 12 | o3_default_default |
| wstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.014 | 7.717 | 10.142 | 12 | o3_default_default |
| wstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.016 | 14.599 | 48.197 | 12 | o3_default_default |
| wstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.015 | 8.997 | 10.848 | 12 | o3_default_default |
| wstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.015 | 10.227 | 15.598 | 12 | o3_default_default |
| wstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.015 | 12.127 | 13.583 | 12 | o3_default_default |
| wstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.017 | 13.610 | 23.602 | 12 | o3_default_default |
| wstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.009 | 0.011 | 0.011 | 12 | o2_default_default |
| wstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.009 | 0.012 | 0.015 | 12 | o3_default_default |
| wstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.010 | 0.012 | 0.021 | 12 | o3_default_default |
| wstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.010 | 0.011 | 0.012 | 12 | o2_default_default |
| wstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.010 | 0.012 | 0.012 | 12 | o3_default_default |
| wstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.011 | 0.013 | 0.015 | 12 | o2_default_default |
| wstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.010 | 0.013 | 0.021 | 12 | o2_default_default |
| pricingcall_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.045 | 0.276 | 0.303 | 10 | o3_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 34/36 | 2 | 0.015 | 14.221 | 15.270 | 10 | o3_default_default |
| pricingcall_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.017 | 0.027 | 0.032 | 10 | o2_dense_sabre |
| pricingcall_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.024 | 0.042 | 0.053 | 10 | o2_trivial_sabre |
| pricingcall_indep_tket_5 | validation | 5 | 34/36 | 2 | 0.016 | 14.702 | 15.722 | 10 | o3_default_default |
| pricingcall_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.017 | 0.028 | 0.029 | 10 | o2_dense_sabre |
| pricingcall_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.021 | 0.039 | 0.048 | 10 | o2_trivial_sabre |
| pricingput_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.023 | 0.065 | 0.073 | 10 | o3_default_default |
| pricingput_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.012 | 16.664 | 21.781 | 12 | o3_default_default |
| pricingput_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.015 | 0.029 | 0.032 | 10 | o2_dense_sabre |
| pricingput_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.019 | 0.038 | 0.051 | 10 | o2_trivial_sabre |
| pricingput_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.013 | 16.536 | 21.362 | 12 | o3_default_default |
| pricingput_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.016 | 0.031 | 0.038 | 10 | o3_dense_sabre |
| pricingput_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.020 | 0.038 | 0.048 | 10 | o2_trivial_sabre |
| qft_indep_qiskit_10 | validation | 10 | 36/36 | 0 | 0.015 | 28.398 | 34.097 | 12 | o2_dense_sabre |
| qft_indep_qiskit_11 | validation | 11 | 33/36 | 3 | 0.016 | 45.407 | 77.085 | 10 | o3_default_default |
| qft_indep_qiskit_12 | validation | 12 | 31/36 | 5 | 0.016 | 0.034 | 93.714 | 10 | o3_default_default |
| qft_indep_qiskit_13 | validation | 13 | 31/36 | 5 | 0.019 | 0.039 | 94.336 | 10 | o3_default_default |
| qft_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.023 | 0.044 | 0.053 | 10 | o2_default_default |
| qft_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.023 | 0.054 | 0.074 | 10 | o3_default_default |
| qft_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.023 | 0.055 | 0.060 | 10 | o3_default_default |
| qft_indep_qiskit_17 | validation | 17 | 30/36 | 6 | 0.028 | 0.064 | 0.078 | 10 | o3_default_default |
| qft_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.011 | 12 | o2_default_default |
| qft_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.010 | 0.773 | 0.816 | 12 | o3_default_default |
| qft_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.011 | 1.705 | 1.760 | 12 | o2_default_default |
| qft_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.010 | 2.303 | 2.535 | 12 | o3_default_default |
| qft_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.012 | 4.227 | 4.244 | 12 | o3_default_default |
| qft_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.013 | 7.880 | 10.994 | 12 | o3_default_default |
| qft_indep_qiskit_8 | validation | 8 | 36/36 | 0 | 0.014 | 12.065 | 34.602 | 12 | o2_default_default |
| qft_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.016 | 22.542 | 25.385 | 12 | o3_default_default |
| qft_indep_tket_10 | validation | 10 | 36/36 | 0 | 0.015 | 29.073 | 32.070 | 12 | o2_dense_sabre |
| qft_indep_tket_11 | validation | 11 | 33/36 | 3 | 0.016 | 44.895 | 73.769 | 10 | o3_default_default |
| qft_indep_tket_12 | validation | 12 | 31/36 | 5 | 0.017 | 0.035 | 93.165 | 10 | o3_default_default |
| qft_indep_tket_13 | validation | 13 | 31/36 | 5 | 0.018 | 0.040 | 96.334 | 10 | o3_default_default |
| qft_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.023 | 0.048 | 0.059 | 10 | o2_default_default |
| qft_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.010 | 12 | o2_default_default |
| qft_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.010 | 0.782 | 1.031 | 12 | o3_default_default |
| qft_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.012 | 1.796 | 1.938 | 12 | o2_default_default |
| qft_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.012 | 2.140 | 2.633 | 12 | o3_default_default |
| qft_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.011 | 4.381 | 4.439 | 12 | o3_default_default |
| qft_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.013 | 7.621 | 11.495 | 12 | o3_default_default |
| qft_indep_tket_8 | validation | 8 | 36/36 | 0 | 0.013 | 11.690 | 35.491 | 12 | o2_default_default |
| qft_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.015 | 22.928 | 25.743 | 12 | o3_default_default |
| qftentangled_indep_qiskit_10 | validation | 10 | 35/36 | 1 | 0.015 | 37.490 | 50.253 | 11 | o2_dense_sabre |
| qftentangled_indep_qiskit_11 | validation | 11 | 35/36 | 1 | 0.016 | 49.392 | 50.800 | 11 | o3_default_default |
| qftentangled_indep_qiskit_12 | validation | 12 | 32/36 | 4 | 0.017 | 30.164 | 67.844 | 10 | o2_default_default |
| qftentangled_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.019 | 0.041 | 0.048 | 10 | o3_default_default |
| qftentangled_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.020 | 0.057 | 0.074 | 10 | o3_default_default |
| qftentangled_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.027 | 0.061 | 0.191 | 10 | o3_default_default |
| qftentangled_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.021 | 0.049 | 0.068 | 10 | o3_default_default |
| qftentangled_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.008 | 0.010 | 0.011 | 12 | o3_default_default |
| qftentangled_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.010 | 1.199 | 1.271 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.011 | 2.062 | 2.314 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.012 | 3.470 | 3.952 | 12 | o3_default_default |
| qftentangled_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.012 | 6.603 | 7.269 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.013 | 8.736 | 9.392 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_8 | validation | 8 | 36/36 | 0 | 0.013 | 23.122 | 24.445 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.014 | 38.937 | 46.721 | 12 | o3_default_default |
| qftentangled_indep_tket_10 | validation | 10 | 35/36 | 1 | 0.015 | 37.768 | 49.950 | 11 | o2_dense_sabre |
| qftentangled_indep_tket_11 | validation | 11 | 35/36 | 1 | 0.017 | 48.786 | 50.066 | 11 | o3_default_default |
| qftentangled_indep_tket_12 | validation | 12 | 32/36 | 4 | 0.018 | 29.254 | 67.666 | 10 | o2_default_default |
| qftentangled_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.022 | 0.044 | 0.053 | 10 | o3_default_default |
| qftentangled_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.021 | 0.051 | 0.064 | 10 | o3_default_default |
| qftentangled_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.008 | 0.011 | 0.015 | 12 | o3_default_default |
| qftentangled_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.010 | 1.149 | 1.280 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.010 | 2.071 | 2.496 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.011 | 3.570 | 3.664 | 12 | o3_default_default |
| qftentangled_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.011 | 6.587 | 7.315 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.012 | 8.749 | 9.651 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_8 | validation | 8 | 36/36 | 0 | 0.014 | 21.688 | 24.406 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.014 | 38.761 | 43.459 | 12 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 482 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Esito ignoto alla soglia | Minimo timeout stimato |
| --- | --- | --- | --- | --- |
| 30 | 196 | 482 | 0 | 678 |
| 60 | 33 | 482 | 0 | 515 |
| 100 | 0 | 482 | 0 | 482 |
| 120 | 0 | 482 | 482 | 0 |
| 300 | 0 | 482 | 482 | 0 |
| 600 | 0 | 482 | 482 | 0 |
| 900 | 0 | 482 | 482 | 0 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta. Questi casi restano ignoti e non sono inclusi nel minimo stimato. La stima usa i tempi osservati e non prevede l'effetto di cambiare i worker.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 4705 |
| Non eleggibili | 215 |
| Esempi RAG | 319 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

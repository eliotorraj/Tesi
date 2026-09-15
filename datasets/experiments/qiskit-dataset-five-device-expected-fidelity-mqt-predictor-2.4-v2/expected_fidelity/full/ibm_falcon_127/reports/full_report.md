# Dataset Qiskit full — ibm_falcon_127

Scheda generata automaticamente dagli artefatti del Dataset. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 127 |
| Hash target | 5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd |
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
| Durata invocazione | 8.518 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati. I parametri nei risultati provengono dai singoli tentativi, quando disponibili; per i vecchi dati senza questa informazione si usa lo stato della generazione.



## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 18360 | - |
| Osservati | 18360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 16902 | 92.1% |
| Failure | 0 | 0.0% |
| Timeout | 1458 | 7.9% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 16902 | 0.007 | 0.019 | 1.948 | 12.585 | 98.948 |
| Non-lookahead | 15300 | 0.007 | 0.019 | 0.094 | 0.229 | 19.177 |
| Lookahead | 1602 | 0.009 | 13.558 | 19.653 | 68.233 | 98.948 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 1530/1530 | 0 | 0.019 | 0.229 | 3.467 | 510 | 90 | 90 | 437 |
| o3_default_default | baseline | 3 | default | default | 1530/1530 | 0 | 0.024 | 0.747 | 19.177 | 510 | 371 | 440 | 494 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 1530/1530 | 0 | 0.015 | 0.149 | 0.706 | 510 | 4 | 4 | 110 |
| o2_dense_sabre | layout | 2 | dense | sabre | 1530/1530 | 0 | 0.018 | 0.073 | 0.228 | 510 | 32 | 34 | 146 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 1530/1530 | 0 | 0.015 | 0.073 | 0.476 | 510 | 4 | 4 | 53 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 1530/1530 | 0 | 0.017 | 0.214 | 1.253 | 510 | 5 | 5 | 135 |
| o3_dense_sabre | layout | 3 | dense | sabre | 1530/1530 | 0 | 0.020 | 0.146 | 0.753 | 510 | 4 | 38 | 95 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 1530/1530 | 0 | 0.017 | 0.150 | 0.669 | 510 | 0 | 4 | 34 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 793/1530 | 737 | 13.785 | 68.571 | 98.948 | 238 | 0 | 0 | 15 |
| o2_sabre_basic | routing | 2 | sabre | basic | 1530/1530 | 0 | 0.028 | 0.629 | 3.038 | 510 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 809/1530 | 721 | 12.995 | 67.316 | 98.399 | 249 | 0 | 0 | 11 |
| o3_sabre_basic | routing | 3 | sabre | basic | 1530/1530 | 0 | 0.031 | 0.933 | 4.162 | 510 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.029 | 0.274 | 0.298 | 10 | o3_default_default |
| ae_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.026 | 0.048 | 0.054 | 10 | o3_default_default |
| ae_indep_qiskit_12 | train | 12 | 30/36 | 6 | 0.028 | 0.058 | 0.065 | 10 | o3_default_default |
| ae_indep_qiskit_13 | train | 13 | 30/36 | 6 | 0.034 | 0.066 | 0.069 | 10 | o3_default_default |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.014 | 12 | o2_default_default |
| ae_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 5.333 | 5.413 | 12 | o3_default_default |
| ae_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.088 | 0.352 | 0.406 | 10 | o3_default_default |
| ae_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.017 | 15.975 | 17.709 | 12 | o3_default_default |
| ae_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.126 | 0.501 | 0.542 | 10 | o3_default_default |
| ae_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.017 | 12.213 | 12.416 | 12 | o3_default_default |
| ae_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.199 | 0.750 | 1.196 | 10 | o3_default_default |
| ae_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.022 | 29.754 | 31.222 | 12 | o3_default_default |
| ae_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.204 | 1.105 | 1.302 | 10 | o3_default_default |
| ae_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.018 | 34.596 | 50.392 | 12 | o3_default_default |
| ae_indep_qiskit_8 | train | 8 | 33/36 | 3 | 0.020 | 53.550 | 73.008 | 10 | o3_default_default |
| ae_indep_qiskit_9 | train | 9 | 33/36 | 3 | 0.021 | 81.860 | 90.174 | 10 | o3_default_default |
| ae_indep_tket_10 | train | 10 | 30/36 | 6 | 0.020 | 0.037 | 0.043 | 10 | o3_default_default |
| ae_indep_tket_11 | train | 11 | 30/36 | 6 | 0.021 | 0.046 | 0.051 | 10 | o3_default_default |
| ae_indep_tket_12 | train | 12 | 30/36 | 6 | 0.022 | 0.059 | 0.183 | 10 | o3_default_default |
| ae_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.016 | 0.022 | 12 | o2_default_default |
| ae_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 4.637 | 5.232 | 12 | o3_default_default |
| ae_indep_tket_30 | train | 30 | 30/36 | 6 | 0.083 | 0.337 | 0.459 | 10 | o3_default_default |
| ae_indep_tket_4 | train | 4 | 36/36 | 0 | 0.016 | 14.779 | 17.916 | 12 | o3_default_default |
| ae_indep_tket_40 | train | 40 | 30/36 | 6 | 0.113 | 0.456 | 0.554 | 10 | o3_default_default |
| ae_indep_tket_5 | train | 5 | 36/36 | 0 | 0.019 | 12.339 | 12.545 | 12 | o3_default_default |
| ae_indep_tket_50 | train | 50 | 30/36 | 6 | 0.155 | 0.723 | 1.232 | 10 | o3_default_default |
| ae_indep_tket_6 | train | 6 | 36/36 | 0 | 0.020 | 28.215 | 30.997 | 12 | o3_default_default |
| ae_indep_tket_7 | train | 7 | 36/36 | 0 | 0.018 | 35.443 | 50.428 | 12 | o3_default_default |
| ae_indep_tket_8 | train | 8 | 33/36 | 3 | 0.019 | 52.750 | 70.649 | 10 | o3_default_default |
| ae_indep_tket_9 | train | 9 | 33/36 | 3 | 0.018 | 83.072 | 92.206 | 10 | o3_default_default |
| dj_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.016 | 43.414 | 71.710 | 12 | o2_sabre_sabre |
| dj_indep_qiskit_11 | train | 11 | 33/36 | 3 | 0.016 | 14.660 | 14.842 | 10 | o3_default_default |
| dj_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.016 | 15.781 | 16.001 | 12 | o3_default_default |
| dj_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.016 | 90.589 | 91.304 | 12 | o3_sabre_sabre |
| dj_indep_qiskit_14 | train | 14 | 30/36 | 6 | 0.016 | 0.027 | 0.031 | 10 | o3_default_default |
| dj_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.016 | 21.319 | 21.442 | 12 | o3_default_default |
| dj_indep_qiskit_16 | train | 16 | 32/36 | 4 | 0.017 | 11.222 | 26.173 | 10 | o3_default_default |
| dj_indep_qiskit_17 | train | 17 | 30/36 | 6 | 0.019 | 0.029 | 0.030 | 10 | o3_default_default |
| dj_indep_qiskit_18 | train | 18 | 32/36 | 4 | 0.015 | 12.220 | 28.731 | 10 | o3_default_default |
| dj_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.019 | 29.643 | 30.557 | 12 | o3_default_default |
| dj_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.017 | 12 | o2_default_default |
| dj_indep_qiskit_20 | train | 20 | 34/36 | 2 | 0.018 | 32.209 | 34.897 | 10 | o3_default_default |
| dj_indep_qiskit_21 | train | 21 | 34/36 | 2 | 0.019 | 36.226 | 37.514 | 10 | o3_default_default |
| dj_indep_qiskit_22 | train | 22 | 33/36 | 3 | 0.018 | 41.082 | 43.493 | 11 | o3_default_default |
| dj_indep_qiskit_23 | train | 23 | 32/36 | 4 | 0.019 | 18.425 | 42.643 | 10 | o3_default_default |
| dj_indep_qiskit_24 | train | 24 | 30/36 | 6 | 0.019 | 0.040 | 0.045 | 10 | o3_default_default |
| dj_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.021 | 43.980 | 44.335 | 12 | o3_default_default |
| dj_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.021 | 50.914 | 52.552 | 12 | o3_default_default |
| dj_indep_qiskit_27 | train | 27 | 34/36 | 2 | 0.021 | 61.073 | 67.749 | 10 | o3_default_default |
| dj_indep_qiskit_28 | train | 28 | 30/36 | 6 | 0.020 | 0.051 | 0.054 | 10 | o3_default_default |
| dj_indep_qiskit_29 | train | 29 | 30/36 | 6 | 0.022 | 0.057 | 0.061 | 10 | o3_default_default |
| dj_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 0.016 | 0.017 | 12 | o3_default_default |
| dj_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.019 | 0.064 | 0.072 | 10 | o3_default_default |
| dj_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 0.016 | 0.017 | 12 | o3_default_default |
| dj_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.023 | 0.117 | 0.124 | 10 | o3_default_default |
| dj_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.014 | 4.172 | 4.418 | 12 | o2_default_default |
| dj_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.026 | 0.339 | 0.381 | 10 | o3_default_default |
| dj_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.015 | 8.939 | 10.034 | 12 | o3_default_default |
| dj_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.031 | 0.780 | 0.970 | 10 | o3_default_default |
| dj_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.016 | 9.729 | 10.842 | 12 | o2_default_default |
| dj_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.032 | 1.220 | 1.507 | 10 | o3_default_default |
| dj_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.017 | 8.926 | 11.738 | 12 | o2_sabre_sabre |
| dj_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.041 | 1.702 | 1.935 | 10 | o3_default_default |
| dj_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.018 | 10.744 | 14.978 | 12 | o3_default_default |
| dj_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.035 | 1.193 | 1.258 | 10 | o3_default_default |
| dj_indep_tket_10 | train | 10 | 36/36 | 0 | 0.016 | 42.570 | 74.312 | 12 | o2_sabre_sabre |
| dj_indep_tket_11 | train | 11 | 33/36 | 3 | 0.015 | 14.920 | 15.081 | 10 | o3_default_default |
| dj_indep_tket_12 | train | 12 | 36/36 | 0 | 0.016 | 16.426 | 17.610 | 12 | o3_default_default |
| dj_indep_tket_13 | train | 13 | 36/36 | 0 | 0.017 | 94.012 | 94.391 | 12 | o3_default_default |
| dj_indep_tket_14 | train | 14 | 30/36 | 6 | 0.016 | 0.028 | 0.030 | 10 | o3_default_default |
| dj_indep_tket_15 | train | 15 | 36/36 | 0 | 0.017 | 22.365 | 22.711 | 12 | o3_default_default |
| dj_indep_tket_16 | train | 16 | 32/36 | 4 | 0.016 | 11.448 | 25.596 | 10 | o3_default_default |
| dj_indep_tket_17 | train | 17 | 30/36 | 6 | 0.017 | 0.028 | 0.030 | 10 | o3_default_default |
| dj_indep_tket_18 | train | 18 | 32/36 | 4 | 0.016 | 12.467 | 27.709 | 10 | o3_default_default |
| dj_indep_tket_19 | train | 19 | 36/36 | 0 | 0.018 | 29.782 | 30.589 | 12 | o3_default_default |
| dj_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.015 | 12 | o2_default_default |
| dj_indep_tket_20 | train | 20 | 34/36 | 2 | 0.019 | 34.051 | 35.712 | 10 | o3_default_default |
| dj_indep_tket_21 | train | 21 | 34/36 | 2 | 0.017 | 37.814 | 38.312 | 10 | o3_default_default |
| dj_indep_tket_22 | train | 22 | 33/36 | 3 | 0.019 | 41.533 | 43.271 | 11 | o3_default_default |
| dj_indep_tket_23 | train | 23 | 32/36 | 4 | 0.018 | 18.509 | 42.177 | 10 | o3_default_default |
| dj_indep_tket_24 | train | 24 | 30/36 | 6 | 0.017 | 0.043 | 0.049 | 10 | o3_default_default |
| dj_indep_tket_25 | train | 25 | 36/36 | 0 | 0.022 | 44.648 | 45.406 | 12 | o3_default_default |
| dj_indep_tket_26 | train | 26 | 36/36 | 0 | 0.021 | 51.756 | 53.192 | 12 | o3_default_default |
| dj_indep_tket_27 | train | 27 | 34/36 | 2 | 0.021 | 63.978 | 68.873 | 10 | o3_default_default |
| dj_indep_tket_28 | train | 28 | 30/36 | 6 | 0.020 | 0.047 | 0.051 | 10 | o3_default_default |
| dj_indep_tket_29 | train | 29 | 30/36 | 6 | 0.020 | 0.050 | 0.062 | 10 | o3_default_default |
| dj_indep_tket_3 | train | 3 | 36/36 | 0 | 0.011 | 0.015 | 0.015 | 12 | o3_default_default |
| dj_indep_tket_30 | train | 30 | 30/36 | 6 | 0.018 | 0.058 | 0.079 | 10 | o3_default_default |
| dj_indep_tket_4 | train | 4 | 36/36 | 0 | 0.012 | 0.015 | 0.015 | 12 | o3_default_default |
| dj_indep_tket_40 | train | 40 | 30/36 | 6 | 0.022 | 0.130 | 0.157 | 10 | o3_default_default |
| dj_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 4.320 | 4.640 | 12 | o3_default_default |
| dj_indep_tket_50 | train | 50 | 30/36 | 6 | 0.026 | 0.313 | 0.433 | 10 | o2_default_default |
| dj_indep_tket_6 | train | 6 | 36/36 | 0 | 0.015 | 8.745 | 10.122 | 12 | o3_default_default |
| dj_indep_tket_60 | train | 60 | 30/36 | 6 | 0.027 | 0.691 | 0.726 | 10 | o3_default_default |
| dj_indep_tket_7 | train | 7 | 36/36 | 0 | 0.015 | 9.183 | 11.219 | 12 | o2_default_default |
| dj_indep_tket_70 | train | 70 | 30/36 | 6 | 0.028 | 1.191 | 1.818 | 10 | o3_default_default |
| dj_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 9.708 | 11.942 | 12 | o2_sabre_sabre |
| dj_indep_tket_80 | train | 80 | 30/36 | 6 | 0.029 | 1.838 | 1.978 | 10 | o2_default_default |
| dj_indep_tket_9 | train | 9 | 36/36 | 0 | 0.017 | 11.440 | 14.742 | 12 | o3_default_default |
| dj_indep_tket_90 | train | 90 | 30/36 | 6 | 0.036 | 1.108 | 1.406 | 10 | o3_default_default |
| graphstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.018 | 12.118 | 14.141 | 12 | o3_default_default |
| graphstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.018 | 14.405 | 14.609 | 12 | o3_default_default |
| graphstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.017 | 13.465 | 15.066 | 12 | o2_default_default |
| graphstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.019 | 8.910 | 10.679 | 12 | o3_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.020 | 16.487 | 21.704 | 12 | o3_default_default |
| graphstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.019 | 21.458 | 22.103 | 12 | o3_default_default |
| graphstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.019 | 22.578 | 24.528 | 12 | o3_default_default |
| graphstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.020 | 18.875 | 23.993 | 12 | o3_default_default |
| graphstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.021 | 26.738 | 27.025 | 12 | o3_default_default |
| graphstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.021 | 23.574 | 32.035 | 12 | o2_default_default |
| graphstate_indep_qiskit_20 | train | 20 | 35/36 | 1 | 0.019 | 32.663 | 35.372 | 11 | o2_default_default |
| graphstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.022 | 39.387 | 56.863 | 12 | o3_default_default |
| graphstate_indep_qiskit_22 | train | 22 | 35/36 | 1 | 0.022 | 29.164 | 39.063 | 11 | o3_default_default |
| graphstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.023 | 32.523 | 33.451 | 12 | o3_default_default |
| graphstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.021 | 35.250 | 36.646 | 12 | o3_default_default |
| graphstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.026 | 37.464 | 50.032 | 12 | o3_default_default |
| graphstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.024 | 36.328 | 44.539 | 12 | o3_default_default |
| graphstate_indep_qiskit_27 | train | 27 | 35/36 | 1 | 0.028 | 56.674 | 64.593 | 11 | o3_default_default |
| graphstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.026 | 43.530 | 56.255 | 12 | o3_default_default |
| graphstate_indep_qiskit_29 | train | 29 | 34/36 | 2 | 0.022 | 51.184 | 60.441 | 11 | o3_default_default |
| graphstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.013 | 3.058 | 3.233 | 12 | o3_default_default |
| graphstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.030 | 57.308 | 63.868 | 12 | o3_default_default |
| graphstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.014 | 5.368 | 5.601 | 12 | o3_default_default |
| graphstate_indep_qiskit_40 | train | 40 | 32/36 | 4 | 0.036 | 38.925 | 98.247 | 10 | o3_sabre_sabre |
| graphstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 6.273 | 6.427 | 12 | o2_default_default |
| graphstate_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.037 | 0.127 | 0.209 | 10 | o3_default_default |
| graphstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 6.690 | 13.524 | 12 | o3_default_default |
| graphstate_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.032 | 17.273 | 17.659 | 10 | o3_default_default |
| graphstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.017 | 6.359 | 6.881 | 12 | o3_default_default |
| graphstate_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.040 | 17.379 | 19.177 | 10 | o3_default_default |
| graphstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 6.786 | 7.493 | 12 | o2_default_default |
| graphstate_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.058 | 0.942 | 1.065 | 10 | o3_default_default |
| graphstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.017 | 7.276 | 7.694 | 12 | o3_default_default |
| graphstate_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.081 | 17.945 | 18.380 | 10 | o3_default_default |
| graphstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.019 | 9.762 | 10.815 | 12 | o3_default_default |
| graphstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.019 | 13.765 | 15.294 | 12 | o3_default_default |
| graphstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.017 | 15.564 | 16.047 | 12 | o2_default_default |
| graphstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.018 | 17.830 | 21.788 | 12 | o3_default_default |
| graphstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.020 | 14.585 | 14.804 | 12 | o3_default_default |
| graphstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.018 | 14.861 | 16.188 | 12 | o3_default_default |
| graphstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.020 | 22.742 | 23.034 | 12 | o3_default_default |
| graphstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.021 | 17.322 | 17.612 | 12 | o3_default_default |
| graphstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.022 | 18.244 | 32.953 | 12 | o3_default_default |
| graphstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.025 | 25.722 | 29.537 | 12 | o3_default_default |
| graphstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.018 | 32.730 | 36.375 | 12 | o2_default_default |
| graphstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.022 | 32.217 | 54.312 | 12 | o3_default_default |
| graphstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.023 | 40.828 | 44.342 | 12 | o3_default_default |
| graphstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.028 | 32.424 | 46.711 | 12 | o3_default_default |
| graphstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.023 | 34.426 | 42.953 | 12 | o3_default_default |
| graphstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.029 | 35.586 | 38.573 | 12 | o2_default_default |
| graphstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.031 | 44.221 | 80.428 | 12 | o3_default_default |
| graphstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.025 | 37.653 | 38.699 | 12 | o3_default_default |
| graphstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.026 | 35.809 | 53.212 | 12 | o3_default_default |
| graphstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.025 | 36.952 | 41.645 | 12 | o3_default_default |
| graphstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 2.973 | 3.165 | 12 | o3_default_default |
| graphstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.028 | 47.427 | 71.167 | 12 | o3_default_default |
| graphstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.014 | 5.395 | 5.509 | 12 | o3_default_default |
| graphstate_indep_tket_40 | train | 40 | 34/36 | 2 | 0.027 | 80.680 | 98.399 | 11 | o3_default_default |
| graphstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.014 | 5.702 | 5.992 | 12 | o2_default_default |
| graphstate_indep_tket_50 | train | 50 | 30/36 | 6 | 0.034 | 16.445 | 18.017 | 10 | o3_default_default |
| graphstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 6.737 | 6.964 | 12 | o2_default_default |
| graphstate_indep_tket_60 | train | 60 | 30/36 | 6 | 0.032 | 16.368 | 18.741 | 10 | o3_default_default |
| graphstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.016 | 6.576 | 9.078 | 12 | o3_default_default |
| graphstate_indep_tket_70 | train | 70 | 30/36 | 6 | 0.042 | 17.375 | 18.498 | 10 | o3_sabre_sabre |
| graphstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 7.147 | 7.765 | 12 | o3_default_default |
| graphstate_indep_tket_80 | train | 80 | 30/36 | 6 | 0.047 | 0.343 | 0.356 | 10 | o3_default_default |
| graphstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.017 | 6.772 | 7.241 | 12 | o3_default_default |
| graphstate_indep_tket_90 | train | 90 | 30/36 | 6 | 0.079 | 17.799 | 18.842 | 10 | o3_sabre_sabre |
| portfolioqaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.016 | 44.348 | 45.745 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.016 | 72.089 | 81.820 | 12 | o3_dense_sabre |
| portfolioqaoa_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.017 | 0.028 | 0.031 | 10 | o3_default_default |
| portfolioqaoa_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.016 | 0.034 | 0.046 | 10 | o2_default_default |
| portfolioqaoa_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.019 | 0.044 | 0.046 | 10 | o2_default_default |
| portfolioqaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 43.209 | 46.533 | 12 | o2_dense_sabre |
| portfolioqaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 76.261 | 83.835 | 12 | o3_dense_sabre |
| portfolioqaoa_indep_tket_5 | train | 5 | 30/36 | 6 | 0.015 | 0.033 | 0.041 | 10 | o3_default_default |
| portfolioqaoa_indep_tket_6 | train | 6 | 30/36 | 6 | 0.016 | 0.039 | 0.044 | 10 | o2_default_default |
| portfolioqaoa_indep_tket_7 | train | 7 | 30/36 | 6 | 0.017 | 0.045 | 0.048 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.023 | 0.079 | 0.095 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.029 | 0.089 | 0.097 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 35.194 | 36.881 | 12 | o3_dense_sabre |
| portfoliovqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.017 | 58.926 | 68.820 | 12 | o2_dense_sabre |
| portfoliovqe_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.031 | 0.036 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.014 | 0.035 | 0.036 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.018 | 0.035 | 0.042 | 10 | o2_default_default |
| portfoliovqe_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.020 | 0.051 | 0.065 | 10 | o3_default_default |
| portfoliovqe_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.022 | 0.059 | 0.071 | 10 | o3_default_default |
| portfoliovqe_indep_tket_10 | train | 10 | 30/36 | 6 | 0.025 | 0.075 | 0.080 | 10 | o3_default_default |
| portfoliovqe_indep_tket_11 | train | 11 | 30/36 | 6 | 0.030 | 0.085 | 0.109 | 10 | o3_default_default |
| portfoliovqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 35.587 | 37.189 | 12 | o3_dense_sabre |
| portfoliovqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 61.183 | 71.084 | 12 | o2_dense_sabre |
| portfoliovqe_indep_tket_5 | train | 5 | 30/36 | 6 | 0.016 | 0.023 | 0.027 | 10 | o2_default_default |
| portfoliovqe_indep_tket_6 | train | 6 | 30/36 | 6 | 0.016 | 0.036 | 0.040 | 10 | o2_default_default |
| portfoliovqe_indep_tket_7 | train | 7 | 30/36 | 6 | 0.018 | 0.036 | 0.044 | 10 | o2_default_default |
| portfoliovqe_indep_tket_8 | train | 8 | 30/36 | 6 | 0.019 | 0.052 | 0.054 | 10 | o3_default_default |
| portfoliovqe_indep_tket_9 | train | 9 | 30/36 | 6 | 0.023 | 0.058 | 0.063 | 10 | o3_default_default |
| qaoa_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.018 | 24.751 | 28.979 | 12 | o3_default_default |
| qaoa_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.018 | 8.685 | 8.957 | 12 | o3_default_default |
| qaoa_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.016 | 15.570 | 47.308 | 12 | o2_default_default |
| qaoa_indep_qiskit_13 | train | 13 | 35/36 | 1 | 0.020 | 9.803 | 49.124 | 11 | o3_default_default |
| qaoa_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.024 | 44.408 | 89.918 | 12 | o3_default_default |
| qaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.014 | 12.930 | 13.103 | 12 | o3_default_default |
| qaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 7.393 | 7.753 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 11.021 | 11.824 | 12 | o2_dense_sabre |
| qaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 12.575 | 15.035 | 12 | o2_default_default |
| qaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.017 | 10.063 | 10.215 | 12 | o3_default_default |
| qaoa_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.018 | 16.377 | 17.419 | 12 | o3_default_default |
| qaoa_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.019 | 17.558 | 49.153 | 12 | o3_default_default |
| qaoa_indep_tket_10 | train | 10 | 36/36 | 0 | 0.019 | 25.117 | 29.427 | 12 | o3_default_default |
| qaoa_indep_tket_11 | train | 11 | 36/36 | 0 | 0.020 | 8.365 | 8.940 | 12 | o3_default_default |
| qaoa_indep_tket_12 | train | 12 | 36/36 | 0 | 0.017 | 15.669 | 49.534 | 12 | o2_default_default |
| qaoa_indep_tket_13 | train | 13 | 35/36 | 1 | 0.021 | 9.981 | 47.339 | 11 | o3_default_default |
| qaoa_indep_tket_14 | train | 14 | 36/36 | 0 | 0.021 | 44.169 | 89.147 | 12 | o3_default_default |
| qaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.013 | 12.528 | 12.738 | 12 | o3_default_default |
| qaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.014 | 7.097 | 7.258 | 12 | o2_dense_sabre |
| qaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.015 | 11.035 | 11.585 | 12 | o2_dense_sabre |
| qaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 12.721 | 14.652 | 12 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.018 | 9.825 | 10.123 | 12 | o3_default_default |
| qaoa_indep_tket_8 | train | 8 | 36/36 | 0 | 0.018 | 16.518 | 16.954 | 12 | o3_default_default |
| qaoa_indep_tket_9 | train | 9 | 36/36 | 0 | 0.020 | 18.004 | 48.617 | 12 | o3_default_default |
| qnn_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.016 | 12 | o3_default_default |
| qnn_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 13.648 | 14.140 | 12 | o2_dense_sabre |
| qnn_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.137 | 0.855 | 0.895 | 10 | o3_default_default |
| qnn_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.018 | 22.704 | 26.871 | 12 | o2_dense_sabre |
| qnn_indep_qiskit_5 | train | 5 | 34/36 | 2 | 0.016 | 61.531 | 69.691 | 10 | o3_default_default |
| qnn_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.016 | 0.030 | 0.031 | 10 | o3_default_default |
| qnn_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.018 | 0.043 | 0.049 | 10 | o3_default_default |
| qnn_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.014 | 12 | o3_default_default |
| qnn_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 13.658 | 14.371 | 12 | o2_dense_sabre |
| qnn_indep_tket_30 | train | 30 | 30/36 | 6 | 0.130 | 0.807 | 0.823 | 10 | o3_default_default |
| qnn_indep_tket_4 | train | 4 | 36/36 | 0 | 0.018 | 23.524 | 26.154 | 12 | o2_dense_sabre |
| qnn_indep_tket_5 | train | 5 | 34/36 | 2 | 0.015 | 62.298 | 67.138 | 10 | o3_default_default |
| qnn_indep_tket_6 | train | 6 | 30/36 | 6 | 0.016 | 0.039 | 0.041 | 10 | o3_default_default |
| qnn_indep_tket_7 | train | 7 | 30/36 | 6 | 0.017 | 0.042 | 0.050 | 10 | o3_default_default |
| random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.010 | 0.012 | 0.013 | 12 | o3_default_default |
| random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 20.596 | 26.705 | 12 | o2_dense_sabre |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.321 | 1.053 | 1.232 | 10 | o2_default_default |
| random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.018 | 24.438 | 34.411 | 12 | o2_dense_sabre |
| random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.020 | 34.291 | 57.539 | 12 | o2_default_default |
| random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.018 | 0.035 | 0.040 | 10 | o3_default_default |
| random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.045 | 0.049 | 10 | o2_default_default |
| random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.025 | 0.053 | 0.061 | 10 | o3_default_default |
| random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.015 | 0.016 | 12 | o3_default_default |
| random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.016 | 20.872 | 26.188 | 12 | o2_dense_sabre |
| random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.422 | 0.919 | 1.110 | 10 | o2_default_default |
| random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.027 | 25.114 | 34.540 | 12 | o2_dense_sabre |
| random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.020 | 33.770 | 57.595 | 12 | o2_default_default |
| random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.031 | 0.038 | 10 | o3_default_default |
| random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.042 | 0.044 | 10 | o2_default_default |
| random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.020 | 0.042 | 0.052 | 10 | o3_default_default |
| realamprandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.025 | 0.071 | 0.094 | 10 | o3_default_default |
| realamprandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.027 | 0.084 | 0.086 | 10 | o3_default_default |
| realamprandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.012 | 0.019 | 0.028 | 12 | o2_default_default |
| realamprandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 35.882 | 36.468 | 12 | o2_dense_sabre |
| realamprandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.161 | 0.852 | 1.087 | 10 | o3_default_default |
| realamprandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.022 | 62.205 | 70.654 | 12 | o2_dense_sabre |
| realamprandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.311 | 1.847 | 2.008 | 10 | o3_default_default |
| realamprandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.017 | 0.032 | 0.037 | 10 | o3_default_default |
| realamprandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.575 | 3.872 | 4.162 | 10 | o3_default_default |
| realamprandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.018 | 0.033 | 0.040 | 10 | o3_default_default |
| realamprandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.020 | 0.041 | 0.050 | 10 | o3_default_default |
| realamprandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.023 | 0.063 | 0.066 | 10 | o3_default_default |
| realamprandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.032 | 0.065 | 0.080 | 10 | o3_default_default |
| realamprandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.036 | 0.085 | 0.092 | 10 | o3_default_default |
| realamprandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.042 | 0.105 | 0.108 | 10 | o3_default_default |
| realamprandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.020 | 12 | o2_default_default |
| realamprandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.018 | 36.643 | 37.287 | 12 | o2_dense_sabre |
| realamprandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.170 | 0.876 | 1.000 | 10 | o3_default_default |
| realamprandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 59.838 | 69.349 | 12 | o2_dense_sabre |
| realamprandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.336 | 1.942 | 2.060 | 10 | o3_default_default |
| realamprandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.016 | 0.027 | 0.035 | 10 | o3_default_default |
| realamprandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.619 | 3.638 | 3.843 | 10 | o3_default_default |
| realamprandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.021 | 0.040 | 0.045 | 10 | o3_default_default |
| realamprandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.020 | 0.041 | 0.057 | 10 | o3_default_default |
| realamprandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.023 | 0.061 | 0.068 | 10 | o3_default_default |
| realamprandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.030 | 0.058 | 0.060 | 10 | o3_default_default |
| su2random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.010 | 0.013 | 0.014 | 12 | o2_default_default |
| su2random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 35.178 | 36.502 | 12 | o2_dense_sabre |
| su2random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.171 | 0.856 | 0.931 | 10 | o3_default_default |
| su2random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.016 | 59.594 | 69.629 | 12 | o2_dense_sabre |
| su2random_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.333 | 1.649 | 2.175 | 10 | o3_default_default |
| su2random_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.029 | 0.030 | 10 | o3_default_default |
| su2random_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.490 | 3.342 | 3.562 | 10 | o3_default_default |
| su2random_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.019 | 0.033 | 0.035 | 10 | o3_default_default |
| su2random_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.018 | 0.036 | 0.203 | 10 | o3_default_default |
| su2random_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.020 | 0.054 | 0.060 | 10 | o3_default_default |
| su2random_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.023 | 0.060 | 0.062 | 10 | o3_default_default |
| su2random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.011 | 0.013 | 0.015 | 12 | o2_default_default |
| su2random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.015 | 37.702 | 38.107 | 12 | o2_dense_sabre |
| su2random_indep_tket_30 | train | 30 | 30/36 | 6 | 0.165 | 0.839 | 0.968 | 10 | o3_default_default |
| su2random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.017 | 60.594 | 71.804 | 12 | o2_dense_sabre |
| su2random_indep_tket_40 | train | 40 | 30/36 | 6 | 0.341 | 1.865 | 2.043 | 10 | o3_default_default |
| su2random_indep_tket_5 | train | 5 | 30/36 | 6 | 0.018 | 0.032 | 0.052 | 10 | o3_default_default |
| su2random_indep_tket_50 | train | 50 | 30/36 | 6 | 0.558 | 3.279 | 3.586 | 10 | o3_default_default |
| su2random_indep_tket_6 | train | 6 | 30/36 | 6 | 0.018 | 0.039 | 0.043 | 10 | o3_default_default |
| su2random_indep_tket_7 | train | 7 | 30/36 | 6 | 0.018 | 0.047 | 0.048 | 10 | o3_default_default |
| su2random_indep_tket_8 | train | 8 | 30/36 | 6 | 0.021 | 0.056 | 0.061 | 10 | o3_default_default |
| su2random_indep_tket_9 | train | 9 | 30/36 | 6 | 0.022 | 0.058 | 0.069 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_10 | train | 10 | 30/36 | 6 | 0.024 | 0.068 | 0.078 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_11 | train | 11 | 30/36 | 6 | 0.027 | 0.080 | 0.087 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.010 | 0.012 | 0.014 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 36.079 | 37.385 | 12 | o2_dense_sabre |
| twolocalrandom_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.171 | 0.852 | 0.905 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.016 | 60.428 | 68.625 | 12 | o2_dense_sabre |
| twolocalrandom_indep_qiskit_40 | train | 40 | 30/36 | 6 | 0.333 | 1.613 | 2.139 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_5 | train | 5 | 30/36 | 6 | 0.016 | 0.024 | 0.028 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.535 | 3.358 | 3.622 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_6 | train | 6 | 30/36 | 6 | 0.018 | 0.051 | 0.167 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_7 | train | 7 | 30/36 | 6 | 0.019 | 0.038 | 0.042 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_8 | train | 8 | 30/36 | 6 | 0.022 | 0.051 | 0.062 | 10 | o3_default_default |
| twolocalrandom_indep_qiskit_9 | train | 9 | 30/36 | 6 | 0.024 | 0.064 | 0.064 | 10 | o3_default_default |
| twolocalrandom_indep_tket_10 | train | 10 | 30/36 | 6 | 0.025 | 0.071 | 0.095 | 10 | o3_default_default |
| twolocalrandom_indep_tket_11 | train | 11 | 30/36 | 6 | 0.028 | 0.090 | 0.107 | 10 | o3_default_default |
| twolocalrandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.010 | 0.013 | 0.014 | 12 | o2_default_default |
| twolocalrandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 35.450 | 36.560 | 12 | o2_dense_sabre |
| twolocalrandom_indep_tket_30 | train | 30 | 30/36 | 6 | 0.170 | 0.945 | 1.017 | 10 | o3_default_default |
| twolocalrandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.018 | 59.592 | 69.790 | 12 | o2_dense_sabre |
| twolocalrandom_indep_tket_40 | train | 40 | 30/36 | 6 | 0.341 | 1.792 | 1.998 | 10 | o3_default_default |
| twolocalrandom_indep_tket_5 | train | 5 | 30/36 | 6 | 0.016 | 0.028 | 0.029 | 10 | o3_default_default |
| twolocalrandom_indep_tket_50 | train | 50 | 30/36 | 6 | 0.617 | 3.319 | 3.673 | 10 | o3_default_default |
| twolocalrandom_indep_tket_6 | train | 6 | 30/36 | 6 | 0.019 | 0.033 | 0.036 | 10 | o3_default_default |
| twolocalrandom_indep_tket_7 | train | 7 | 30/36 | 6 | 0.019 | 0.037 | 0.043 | 10 | o3_default_default |
| twolocalrandom_indep_tket_8 | train | 8 | 30/36 | 6 | 0.021 | 0.057 | 0.063 | 10 | o3_default_default |
| twolocalrandom_indep_tket_9 | train | 9 | 30/36 | 6 | 0.024 | 0.064 | 0.067 | 10 | o3_default_default |
| vqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.013 | 0.018 | 0.020 | 12 | o3_default_default |
| vqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.014 | 0.018 | 0.018 | 12 | o2_default_default |
| vqe_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.014 | 0.018 | 0.020 | 12 | o2_default_default |
| vqe_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.014 | 0.019 | 0.020 | 12 | o2_default_default |
| vqe_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.014 | 0.018 | 0.019 | 12 | o2_default_default |
| vqe_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.014 | 0.020 | 0.020 | 12 | o2_default_default |
| vqe_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.019 | 14.705 | 21.450 | 12 | o2_default_default |
| vqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.012 | 0.014 | 0.014 | 12 | o2_default_default |
| vqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| vqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| vqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.014 | 0.018 | 0.022 | 12 | o2_default_default |
| vqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.013 | 0.019 | 0.040 | 12 | o2_default_default |
| vqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.015 | 0.018 | 0.020 | 12 | o2_default_default |
| vqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.015 | 0.024 | 0.030 | 12 | o2_default_default |
| vqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.014 | 0.018 | 0.020 | 12 | o3_default_default |
| vqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.015 | 0.020 | 0.025 | 12 | o2_default_default |
| vqe_indep_tket_12 | train | 12 | 36/36 | 0 | 0.017 | 0.027 | 0.029 | 12 | o2_default_default |
| vqe_indep_tket_13 | train | 13 | 36/36 | 0 | 0.015 | 0.019 | 0.199 | 12 | o2_default_default |
| vqe_indep_tket_14 | train | 14 | 36/36 | 0 | 0.017 | 0.022 | 0.025 | 12 | o2_default_default |
| vqe_indep_tket_15 | train | 15 | 36/36 | 0 | 0.016 | 0.020 | 0.022 | 12 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.020 | 14.508 | 21.590 | 12 | o2_default_default |
| vqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.012 | 0.016 | 0.018 | 12 | o2_default_default |
| vqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.013 | 0.016 | 0.017 | 12 | o3_default_default |
| vqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.013 | 0.016 | 0.016 | 12 | o3_default_default |
| vqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.014 | 0.023 | 0.037 | 12 | o2_default_default |
| vqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.013 | 0.017 | 0.019 | 12 | o2_default_default |
| vqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.015 | 0.019 | 0.020 | 12 | o2_default_default |
| vqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.014 | 0.019 | 0.023 | 12 | o2_default_default |
| wstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.014 | 0.018 | 0.200 | 12 | o3_default_default |
| wstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.015 | 0.019 | 0.022 | 12 | o3_default_default |
| wstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.016 | 0.019 | 0.021 | 12 | o3_default_default |
| wstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.015 | 0.021 | 0.022 | 12 | o3_default_default |
| wstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.016 | 0.020 | 0.023 | 12 | o2_default_default |
| wstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.017 | 0.021 | 0.025 | 12 | o3_default_default |
| wstate_indep_qiskit_16 | train | 16 | 35/36 | 1 | 0.018 | 12.822 | 22.018 | 11 | o3_default_default |
| wstate_indep_qiskit_17 | train | 17 | 35/36 | 1 | 0.019 | 84.319 | 98.504 | 11 | o3_default_default |
| wstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.020 | 26.154 | 97.817 | 12 | o3_default_default |
| wstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.020 | 90.622 | 94.233 | 12 | o3_default_default |
| wstate_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.011 | 0.014 | 0.015 | 12 | o3_default_default |
| wstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.020 | 91.660 | 92.688 | 12 | o3_default_default |
| wstate_indep_qiskit_21 | train | 21 | 34/36 | 2 | 0.018 | 51.517 | 94.572 | 10 | o2_default_default |
| wstate_indep_qiskit_22 | train | 22 | 34/36 | 2 | 0.018 | 27.152 | 97.388 | 10 | o3_default_default |
| wstate_indep_qiskit_23 | train | 23 | 34/36 | 2 | 0.023 | 30.628 | 98.948 | 10 | o3_default_default |
| wstate_indep_qiskit_24 | train | 24 | 32/36 | 4 | 0.024 | 14.355 | 31.815 | 10 | o2_default_default |
| wstate_indep_qiskit_25 | train | 25 | 32/36 | 4 | 0.022 | 14.275 | 32.771 | 10 | o3_default_default |
| wstate_indep_qiskit_26 | train | 26 | 32/36 | 4 | 0.023 | 14.413 | 32.203 | 10 | o3_default_default |
| wstate_indep_qiskit_27 | train | 27 | 32/36 | 4 | 0.023 | 14.679 | 33.048 | 10 | o2_default_default |
| wstate_indep_qiskit_28 | train | 28 | 30/36 | 6 | 0.023 | 0.125 | 0.128 | 10 | o3_default_default |
| wstate_indep_qiskit_29 | train | 29 | 30/36 | 6 | 0.023 | 0.138 | 0.146 | 10 | o3_default_default |
| wstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.015 | 0.017 | 0.018 | 12 | o2_default_default |
| wstate_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.028 | 0.196 | 0.207 | 10 | o3_default_default |
| wstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.013 | 0.017 | 0.017 | 12 | o3_default_default |
| wstate_indep_qiskit_40 | train | 40 | 31/36 | 5 | 0.025 | 0.311 | 78.442 | 10 | o3_default_default |
| wstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.015 | 0.019 | 0.021 | 12 | o3_default_default |
| wstate_indep_qiskit_50 | train | 50 | 30/36 | 6 | 0.037 | 0.332 | 0.346 | 10 | o3_default_default |
| wstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.016 | 0.021 | 0.022 | 12 | o3_default_default |
| wstate_indep_qiskit_60 | train | 60 | 30/36 | 6 | 0.034 | 0.350 | 0.365 | 10 | o3_default_default |
| wstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.015 | 0.018 | 0.020 | 12 | o3_default_default |
| wstate_indep_qiskit_70 | train | 70 | 30/36 | 6 | 0.038 | 0.348 | 0.355 | 10 | o3_default_default |
| wstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.016 | 0.022 | 0.024 | 12 | o3_default_default |
| wstate_indep_qiskit_80 | train | 80 | 30/36 | 6 | 0.045 | 0.352 | 0.360 | 10 | o3_default_default |
| wstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.016 | 0.022 | 0.028 | 12 | o3_default_default |
| wstate_indep_qiskit_90 | train | 90 | 30/36 | 6 | 0.046 | 0.374 | 0.398 | 10 | o3_default_default |
| wstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.017 | 0.023 | 0.031 | 12 | o3_default_default |
| wstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.018 | 0.021 | 0.025 | 12 | o3_default_default |
| wstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.018 | 0.024 | 0.025 | 12 | o3_default_default |
| wstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.019 | 0.022 | 0.027 | 12 | o3_default_default |
| wstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.019 | 0.024 | 0.026 | 12 | o2_default_default |
| wstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.018 | 0.027 | 0.030 | 12 | o3_default_default |
| wstate_indep_tket_16 | train | 16 | 35/36 | 1 | 0.023 | 14.551 | 27.383 | 11 | o3_default_default |
| wstate_indep_tket_17 | train | 17 | 34/36 | 2 | 0.021 | 45.407 | 98.102 | 11 | o3_default_default |
| wstate_indep_tket_18 | train | 18 | 35/36 | 1 | 0.022 | 21.953 | 34.274 | 11 | o3_default_default |
| wstate_indep_tket_19 | train | 19 | 33/36 | 3 | 0.023 | 26.882 | 30.625 | 11 | o3_default_default |
| wstate_indep_tket_2 | train | 2 | 36/36 | 0 | 0.015 | 0.016 | 0.017 | 12 | o3_default_default |
| wstate_indep_tket_20 | train | 20 | 32/36 | 4 | 0.023 | 15.274 | 73.465 | 10 | o3_default_default |
| wstate_indep_tket_21 | train | 21 | 32/36 | 4 | 0.023 | 14.351 | 32.912 | 10 | o2_default_default |
| wstate_indep_tket_22 | train | 22 | 33/36 | 3 | 0.022 | 26.309 | 37.030 | 10 | o3_default_default |
| wstate_indep_tket_23 | train | 23 | 33/36 | 3 | 0.021 | 33.004 | 33.603 | 10 | o3_default_default |
| wstate_indep_tket_24 | train | 24 | 32/36 | 4 | 0.026 | 15.362 | 34.128 | 10 | o2_default_default |
| wstate_indep_tket_25 | train | 25 | 32/36 | 4 | 0.025 | 15.437 | 34.385 | 10 | o3_default_default |
| wstate_indep_tket_26 | train | 26 | 32/36 | 4 | 0.022 | 15.543 | 34.726 | 10 | o3_default_default |
| wstate_indep_tket_27 | train | 27 | 32/36 | 4 | 0.023 | 15.196 | 35.028 | 10 | o3_default_default |
| wstate_indep_tket_28 | train | 28 | 30/36 | 6 | 0.025 | 0.127 | 0.137 | 10 | o3_default_default |
| wstate_indep_tket_29 | train | 29 | 30/36 | 6 | 0.024 | 0.146 | 0.163 | 10 | o3_default_default |
| wstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.014 | 0.017 | 0.019 | 12 | o2_default_default |
| wstate_indep_tket_30 | train | 30 | 30/36 | 6 | 0.026 | 0.199 | 0.202 | 10 | o3_default_default |
| wstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.015 | 0.019 | 0.021 | 12 | o3_default_default |
| wstate_indep_tket_40 | train | 40 | 31/36 | 5 | 0.031 | 0.332 | 81.782 | 10 | o3_default_default |
| wstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.016 | 0.021 | 0.027 | 12 | o3_default_default |
| wstate_indep_tket_50 | train | 50 | 30/36 | 6 | 0.036 | 0.337 | 0.350 | 10 | o3_default_default |
| wstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.016 | 0.020 | 0.024 | 12 | o3_default_default |
| wstate_indep_tket_60 | train | 60 | 30/36 | 6 | 0.037 | 0.345 | 0.355 | 10 | o3_default_default |
| wstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.015 | 0.020 | 0.021 | 12 | o2_default_default |
| wstate_indep_tket_70 | train | 70 | 30/36 | 6 | 0.041 | 0.375 | 0.399 | 10 | o3_default_default |
| wstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.017 | 0.024 | 0.027 | 12 | o2_default_default |
| wstate_indep_tket_80 | train | 80 | 30/36 | 6 | 0.045 | 0.379 | 0.388 | 10 | o3_default_default |
| wstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.016 | 0.022 | 0.023 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 30/36 | 6 | 0.048 | 0.375 | 0.397 | 10 | o3_default_default |
| pricingcall_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.043 | 0.295 | 0.319 | 10 | o3_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.019 | 0.034 | 0.040 | 10 | o3_default_default |
| pricingcall_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.023 | 0.063 | 0.068 | 10 | o3_default_default |
| pricingcall_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.031 | 0.083 | 0.093 | 10 | o2_default_default |
| pricingcall_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.017 | 0.039 | 0.041 | 10 | o3_default_default |
| pricingcall_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.025 | 0.063 | 0.067 | 10 | o3_default_default |
| pricingcall_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.032 | 0.097 | 0.105 | 10 | o2_default_default |
| pricingput_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.044 | 0.142 | 0.173 | 10 | o3_default_default |
| pricingput_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.019 | 0.036 | 0.037 | 10 | o3_default_default |
| pricingput_indep_qiskit_7 | validation | 7 | 30/36 | 6 | 0.022 | 0.064 | 0.071 | 10 | o3_default_default |
| pricingput_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.033 | 0.102 | 0.113 | 10 | o3_default_default |
| pricingput_indep_tket_5 | validation | 5 | 30/36 | 6 | 0.022 | 0.038 | 0.051 | 10 | o3_default_default |
| pricingput_indep_tket_7 | validation | 7 | 30/36 | 6 | 0.025 | 0.063 | 0.070 | 10 | o3_default_default |
| pricingput_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.034 | 0.094 | 0.103 | 10 | o3_default_default |
| qft_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.024 | 0.043 | 0.052 | 10 | o3_default_default |
| qft_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.025 | 0.045 | 0.051 | 10 | o3_default_default |
| qft_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.030 | 0.052 | 0.053 | 10 | o3_default_default |
| qft_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.031 | 0.070 | 0.097 | 10 | o3_default_default |
| qft_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.035 | 0.072 | 0.085 | 10 | o3_default_default |
| qft_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.039 | 0.087 | 0.094 | 10 | o3_default_default |
| qft_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.045 | 0.120 | 0.137 | 10 | o3_default_default |
| qft_indep_qiskit_17 | validation | 17 | 30/36 | 6 | 0.054 | 0.105 | 0.142 | 10 | o3_default_default |
| qft_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.011 | 0.015 | 0.016 | 12 | o2_default_default |
| qft_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.014 | 3.352 | 3.712 | 12 | o3_default_default |
| qft_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.119 | 0.441 | 0.634 | 10 | o3_default_default |
| qft_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.017 | 16.614 | 18.761 | 12 | o2_dense_sabre |
| qft_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.143 | 0.773 | 1.128 | 10 | o3_default_default |
| qft_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.017 | 16.988 | 22.185 | 12 | o2_trivial_sabre |
| qft_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.126 | 1.141 | 1.602 | 10 | o3_default_default |
| qft_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.025 | 17.241 | 63.897 | 12 | o2_default_default |
| qft_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.214 | 2.142 | 2.469 | 10 | o3_default_default |
| qft_indep_qiskit_7 | validation | 7 | 32/36 | 4 | 0.016 | 24.331 | 61.145 | 10 | o3_default_default |
| qft_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.219 | 2.360 | 2.667 | 10 | o3_default_default |
| qft_indep_qiskit_8 | validation | 8 | 35/36 | 1 | 0.018 | 72.847 | 83.557 | 11 | o2_default_default |
| qft_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.018 | 0.038 | 0.045 | 10 | o2_default_default |
| qft_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.018 | 0.039 | 0.055 | 10 | o3_default_default |
| qft_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.019 | 0.041 | 0.044 | 10 | o3_default_default |
| qft_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.021 | 0.046 | 0.057 | 10 | o3_default_default |
| qft_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.023 | 0.058 | 0.068 | 10 | o3_default_default |
| qft_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.022 | 0.070 | 0.087 | 10 | o3_default_default |
| qft_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.010 | 0.013 | 0.014 | 12 | o2_default_default |
| qft_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.014 | 3.050 | 3.086 | 12 | o3_default_default |
| qft_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.076 | 0.467 | 0.524 | 10 | o3_default_default |
| qft_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.016 | 16.346 | 17.609 | 12 | o2_dense_sabre |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.119 | 0.847 | 1.067 | 10 | o3_default_default |
| qft_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.016 | 16.928 | 21.778 | 12 | o2_trivial_sabre |
| qft_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.194 | 1.127 | 1.771 | 10 | o3_default_default |
| qft_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.021 | 17.128 | 61.797 | 12 | o2_default_default |
| qft_indep_tket_60 | validation | 60 | 30/36 | 6 | 0.216 | 1.922 | 2.230 | 10 | o3_default_default |
| qft_indep_tket_7 | validation | 7 | 32/36 | 4 | 0.017 | 22.963 | 58.297 | 10 | o3_default_default |
| qft_indep_tket_8 | validation | 8 | 35/36 | 1 | 0.017 | 73.648 | 83.621 | 11 | o2_default_default |
| qft_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.017 | 0.036 | 0.040 | 10 | o2_default_default |
| qftentangled_indep_qiskit_10 | validation | 10 | 30/36 | 6 | 0.018 | 0.039 | 0.042 | 10 | o3_default_default |
| qftentangled_indep_qiskit_11 | validation | 11 | 30/36 | 6 | 0.022 | 0.045 | 0.052 | 10 | o3_default_default |
| qftentangled_indep_qiskit_12 | validation | 12 | 30/36 | 6 | 0.021 | 0.053 | 0.071 | 10 | o3_default_default |
| qftentangled_indep_qiskit_13 | validation | 13 | 30/36 | 6 | 0.022 | 0.058 | 0.071 | 10 | o3_default_default |
| qftentangled_indep_qiskit_14 | validation | 14 | 30/36 | 6 | 0.023 | 0.074 | 0.093 | 10 | o3_default_default |
| qftentangled_indep_qiskit_15 | validation | 15 | 30/36 | 6 | 0.024 | 0.083 | 0.205 | 10 | o3_default_default |
| qftentangled_indep_qiskit_16 | validation | 16 | 30/36 | 6 | 0.026 | 0.100 | 0.108 | 10 | o3_default_default |
| qftentangled_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.013 | 0.014 | 12 | o3_default_default |
| qftentangled_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.015 | 4.554 | 4.560 | 12 | o3_default_default |
| qftentangled_indep_qiskit_30 | validation | 30 | 30/36 | 6 | 0.081 | 0.348 | 0.375 | 10 | o3_default_default |
| qftentangled_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.018 | 11.101 | 17.362 | 12 | o2_dense_sabre |
| qftentangled_indep_qiskit_40 | validation | 40 | 30/36 | 6 | 0.155 | 0.611 | 0.806 | 10 | o3_default_default |
| qftentangled_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.016 | 24.019 | 28.225 | 12 | o2_trivial_sabre |
| qftentangled_indep_qiskit_50 | validation | 50 | 30/36 | 6 | 0.182 | 1.241 | 1.425 | 10 | o3_default_default |
| qftentangled_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.016 | 43.826 | 58.348 | 12 | o3_default_default |
| qftentangled_indep_qiskit_60 | validation | 60 | 30/36 | 6 | 0.206 | 1.111 | 1.820 | 10 | o3_sabre_sabre |
| qftentangled_indep_qiskit_7 | validation | 7 | 34/36 | 2 | 0.018 | 40.337 | 41.291 | 10 | o2_default_default |
| qftentangled_indep_qiskit_70 | validation | 70 | 30/36 | 6 | 0.205 | 1.458 | 1.740 | 10 | o3_default_default |
| qftentangled_indep_qiskit_8 | validation | 8 | 30/36 | 6 | 0.017 | 0.034 | 0.036 | 10 | o3_default_default |
| qftentangled_indep_qiskit_9 | validation | 9 | 30/36 | 6 | 0.018 | 0.033 | 0.039 | 10 | o3_default_default |
| qftentangled_indep_tket_10 | validation | 10 | 30/36 | 6 | 0.018 | 0.035 | 0.038 | 10 | o3_default_default |
| qftentangled_indep_tket_11 | validation | 11 | 30/36 | 6 | 0.023 | 0.047 | 0.052 | 10 | o3_default_default |
| qftentangled_indep_tket_12 | validation | 12 | 30/36 | 6 | 0.023 | 0.064 | 0.077 | 10 | o3_default_default |
| qftentangled_indep_tket_13 | validation | 13 | 30/36 | 6 | 0.025 | 0.057 | 0.068 | 10 | o3_default_default |
| qftentangled_indep_tket_14 | validation | 14 | 30/36 | 6 | 0.023 | 0.092 | 0.122 | 10 | o3_default_default |
| qftentangled_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.012 | 0.015 | 0.016 | 12 | o3_default_default |
| qftentangled_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.016 | 4.719 | 4.757 | 12 | o3_default_default |
| qftentangled_indep_tket_30 | validation | 30 | 30/36 | 6 | 0.081 | 0.308 | 0.396 | 10 | o3_default_default |
| qftentangled_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.017 | 10.894 | 16.637 | 12 | o2_dense_sabre |
| qftentangled_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.121 | 0.605 | 0.743 | 10 | o3_default_default |
| qftentangled_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.017 | 23.829 | 29.526 | 12 | o2_trivial_sabre |
| qftentangled_indep_tket_50 | validation | 50 | 30/36 | 6 | 0.155 | 1.029 | 1.115 | 10 | o3_default_default |
| qftentangled_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.018 | 44.371 | 58.393 | 12 | o3_default_default |
| qftentangled_indep_tket_7 | validation | 7 | 34/36 | 2 | 0.016 | 41.724 | 43.197 | 10 | o2_default_default |
| qftentangled_indep_tket_8 | validation | 8 | 30/36 | 6 | 0.016 | 0.030 | 0.030 | 10 | o3_default_default |
| qftentangled_indep_tket_9 | validation | 9 | 30/36 | 6 | 0.016 | 0.032 | 0.047 | 10 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 1458 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Esito ignoto alla soglia | Minimo timeout stimato |
| --- | --- | --- | --- | --- |
| 30 | 409 | 1458 | 0 | 1867 |
| 60 | 104 | 1458 | 0 | 1562 |
| 100 | 0 | 1458 | 0 | 1458 |
| 120 | 0 | 1458 | 1458 | 0 |
| 300 | 0 | 1458 | 1458 | 0 |
| 600 | 0 | 1458 | 1458 | 0 |
| 900 | 0 | 1458 | 1458 | 0 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta. Questi casi restano ignoti e non sono inclusi nel minimo stimato. La stima usa i tempi osservati e non prevede l'effetto di cambiare i worker.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 5587 |
| Non eleggibili | 533 |
| Esempi RAG | 396 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

# Dataset Qiskit full — quantinuum_h2_56

Scheda generata automaticamente dagli artefatti del Dataset. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 56 |
| Hash target | ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee |
| Qiskit | 2.5.0 |
| MQT Bench | 2.2.3 |
| MQT Predictor | 2.4.0 |
| Circuiti totali | 510 |
| Circuiti compatibili | 480 |
| Circuiti incompatibili | 30 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker nei risultati | 6 |
| Timeout nei risultati (s) | 100 |
| Fonte dei parametri | run_provenance |
| Cache hit | 14292 |
| Durata invocazione | 580.516 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati. I parametri nei risultati provengono dai singoli tentativi, quando disponibili; per i vecchi dati senza questa informazione si usa lo stato della generazione.



## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 17280 | - |
| Osservati | 17280 | 100.0% |
| Mancanti | 0 | - |
| Successi | 17280 | 100.0% |
| Failure | 0 | 0.0% |
| Timeout | 0 | 0.0% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 17280 | 0.014 | 0.025 | 0.656 | 2.881 | 35.084 |
| Non-lookahead | 14400 | 0.014 | 0.026 | 0.780 | 3.367 | 35.084 |
| Lookahead | 2880 | 0.015 | 0.024 | 0.031 | 0.070 | 0.447 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 1440/1440 | 0 | 0.083 | 0.467 | 0.726 | 480 | 386 | 386 | 386 |
| o3_default_default | baseline | 3 | default | default | 1440/1440 | 0 | 3.368 | 23.695 | 35.084 | 480 | 94 | 480 | 480 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 1440/1440 | 0 | 0.020 | 0.049 | 0.267 | 480 | 0 | 386 | 386 |
| o2_dense_sabre | layout | 2 | dense | sabre | 1440/1440 | 0 | 0.029 | 0.054 | 0.251 | 480 | 0 | 386 | 0 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 1440/1440 | 0 | 0.020 | 0.042 | 0.218 | 480 | 0 | 386 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 1440/1440 | 0 | 0.023 | 0.080 | 0.466 | 480 | 0 | 480 | 94 |
| o3_dense_sabre | layout | 3 | dense | sabre | 1440/1440 | 0 | 0.032 | 0.078 | 0.442 | 480 | 0 | 480 | 94 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 1440/1440 | 0 | 0.023 | 0.072 | 0.432 | 480 | 0 | 480 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 1440/1440 | 0 | 0.023 | 0.058 | 0.250 | 480 | 0 | 386 | 0 |
| o2_sabre_basic | routing | 2 | sabre | basic | 1440/1440 | 0 | 0.023 | 0.061 | 0.243 | 480 | 0 | 386 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 1440/1440 | 0 | 0.025 | 0.082 | 0.447 | 480 | 0 | 480 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 1440/1440 | 0 | 0.025 | 0.079 | 0.459 | 480 | 0 | 480 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.025 | 17.275 | 17.738 | 12 | o2_default_default |
| ae_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.026 | 19.680 | 20.810 | 12 | o2_default_default |
| ae_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.023 | 21.703 | 22.476 | 12 | o2_default_default |
| ae_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.024 | 23.471 | 24.094 | 12 | o2_default_default |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.018 | 0.026 | 0.028 | 12 | o2_default_default |
| ae_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.021 | 0.082 | 0.090 | 12 | o3_default_default |
| ae_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.039 | 22.126 | 23.937 | 12 | o2_default_default |
| ae_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.023 | 3.385 | 3.645 | 12 | o2_default_default |
| ae_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.060 | 12.193 | 12.578 | 12 | o3_default_default |
| ae_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.022 | 8.621 | 8.773 | 12 | o2_default_default |
| ae_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.067 | 4.133 | 4.165 | 12 | o3_default_default |
| ae_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.022 | 10.532 | 10.764 | 12 | o2_default_default |
| ae_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.026 | 12.618 | 13.216 | 12 | o2_default_default |
| ae_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.022 | 14.544 | 15.575 | 12 | o2_default_default |
| ae_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.021 | 16.513 | 17.628 | 12 | o2_default_default |
| ae_indep_tket_10 | train | 10 | 36/36 | 0 | 0.021 | 18.041 | 18.881 | 12 | o2_default_default |
| ae_indep_tket_11 | train | 11 | 36/36 | 0 | 0.024 | 19.504 | 21.015 | 12 | o2_default_default |
| ae_indep_tket_12 | train | 12 | 36/36 | 0 | 0.025 | 21.050 | 22.538 | 12 | o2_default_default |
| ae_indep_tket_2 | train | 2 | 36/36 | 0 | 0.018 | 0.028 | 0.030 | 12 | o2_default_default |
| ae_indep_tket_3 | train | 3 | 36/36 | 0 | 0.022 | 0.073 | 0.084 | 12 | o2_default_default |
| ae_indep_tket_30 | train | 30 | 36/36 | 0 | 0.042 | 17.597 | 18.635 | 12 | o3_default_default |
| ae_indep_tket_4 | train | 4 | 36/36 | 0 | 0.024 | 3.647 | 3.737 | 12 | o2_default_default |
| ae_indep_tket_40 | train | 40 | 36/36 | 0 | 0.062 | 9.701 | 10.021 | 12 | o3_default_default |
| ae_indep_tket_5 | train | 5 | 36/36 | 0 | 0.023 | 8.248 | 8.715 | 12 | o2_default_default |
| ae_indep_tket_50 | train | 50 | 36/36 | 0 | 0.071 | 3.170 | 3.345 | 12 | o3_default_default |
| ae_indep_tket_6 | train | 6 | 36/36 | 0 | 0.028 | 10.441 | 10.823 | 12 | o3_default_default |
| ae_indep_tket_7 | train | 7 | 36/36 | 0 | 0.023 | 12.525 | 13.050 | 12 | o2_default_default |
| ae_indep_tket_8 | train | 8 | 36/36 | 0 | 0.026 | 15.185 | 15.592 | 12 | o3_default_default |
| ae_indep_tket_9 | train | 9 | 36/36 | 0 | 0.023 | 16.932 | 17.199 | 12 | o2_default_default |
| dj_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.023 | 3.013 | 3.173 | 12 | o2_default_default |
| dj_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.023 | 3.044 | 3.238 | 12 | o2_default_default |
| dj_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.025 | 2.998 | 3.039 | 12 | o2_default_default |
| dj_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.024 | 2.929 | 2.988 | 12 | o2_default_default |
| dj_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.023 | 2.864 | 2.917 | 12 | o2_default_default |
| dj_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.024 | 2.810 | 2.882 | 12 | o2_default_default |
| dj_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.026 | 2.775 | 2.843 | 12 | o2_default_default |
| dj_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.023 | 2.651 | 2.699 | 12 | o2_default_default |
| dj_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.029 | 2.591 | 2.736 | 12 | o2_default_default |
| dj_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.023 | 2.557 | 2.620 | 12 | o2_default_default |
| dj_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.021 | 0.027 | 0.029 | 12 | o2_default_default |
| dj_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.024 | 2.432 | 2.568 | 12 | o2_default_default |
| dj_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.025 | 2.415 | 2.529 | 12 | o2_default_default |
| dj_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.025 | 2.385 | 2.442 | 12 | o2_default_default |
| dj_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.026 | 2.286 | 2.416 | 12 | o2_default_default |
| dj_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.026 | 2.265 | 2.290 | 12 | o2_default_default |
| dj_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.024 | 2.216 | 2.271 | 12 | o2_default_default |
| dj_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.025 | 2.090 | 2.289 | 12 | o2_default_default |
| dj_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.025 | 2.061 | 2.107 | 12 | o2_default_default |
| dj_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.025 | 2.050 | 2.066 | 12 | o2_default_default |
| dj_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.025 | 1.969 | 2.045 | 12 | o2_default_default |
| dj_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.021 | 0.055 | 0.055 | 12 | o2_default_default |
| dj_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.026 | 1.906 | 2.012 | 12 | o2_default_default |
| dj_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.024 | 1.584 | 1.607 | 12 | o2_default_default |
| dj_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.027 | 1.316 | 1.405 | 12 | o2_default_default |
| dj_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.022 | 3.332 | 3.443 | 12 | o2_default_default |
| dj_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.028 | 0.734 | 0.784 | 12 | o2_default_default |
| dj_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.023 | 3.300 | 3.398 | 12 | o2_default_default |
| dj_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 3.298 | 3.413 | 12 | o2_default_default |
| dj_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.023 | 3.205 | 3.444 | 12 | o2_default_default |
| dj_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.022 | 3.116 | 3.207 | 12 | o2_default_default |
| dj_indep_tket_10 | train | 10 | 36/36 | 0 | 0.026 | 3.077 | 3.215 | 12 | o3_default_default |
| dj_indep_tket_11 | train | 11 | 36/36 | 0 | 0.025 | 3.105 | 3.144 | 12 | o3_default_default |
| dj_indep_tket_12 | train | 12 | 36/36 | 0 | 0.025 | 3.045 | 3.073 | 12 | o3_default_default |
| dj_indep_tket_13 | train | 13 | 36/36 | 0 | 0.026 | 2.959 | 3.026 | 12 | o3_default_default |
| dj_indep_tket_14 | train | 14 | 36/36 | 0 | 0.024 | 2.822 | 2.999 | 12 | o3_default_default |
| dj_indep_tket_15 | train | 15 | 36/36 | 0 | 0.025 | 2.864 | 2.913 | 12 | o3_default_default |
| dj_indep_tket_16 | train | 16 | 36/36 | 0 | 0.028 | 2.809 | 2.827 | 12 | o3_default_default |
| dj_indep_tket_17 | train | 17 | 36/36 | 0 | 0.023 | 2.679 | 2.776 | 12 | o3_default_default |
| dj_indep_tket_18 | train | 18 | 36/36 | 0 | 0.026 | 2.653 | 2.784 | 12 | o3_default_default |
| dj_indep_tket_19 | train | 19 | 36/36 | 0 | 0.025 | 2.592 | 2.613 | 12 | o3_default_default |
| dj_indep_tket_2 | train | 2 | 36/36 | 0 | 0.021 | 0.028 | 0.030 | 12 | o3_default_default |
| dj_indep_tket_20 | train | 20 | 36/36 | 0 | 0.027 | 2.480 | 2.633 | 12 | o3_default_default |
| dj_indep_tket_21 | train | 21 | 36/36 | 0 | 0.025 | 2.359 | 2.463 | 12 | o3_default_default |
| dj_indep_tket_22 | train | 22 | 36/36 | 0 | 0.027 | 2.393 | 2.509 | 12 | o3_default_default |
| dj_indep_tket_23 | train | 23 | 36/36 | 0 | 0.026 | 2.343 | 2.396 | 12 | o3_default_default |
| dj_indep_tket_24 | train | 24 | 36/36 | 0 | 0.026 | 2.246 | 2.321 | 12 | o3_default_default |
| dj_indep_tket_25 | train | 25 | 36/36 | 0 | 0.027 | 2.196 | 2.274 | 12 | o3_default_default |
| dj_indep_tket_26 | train | 26 | 36/36 | 0 | 0.026 | 2.148 | 2.201 | 12 | o3_default_default |
| dj_indep_tket_27 | train | 27 | 36/36 | 0 | 0.027 | 2.094 | 2.128 | 12 | o3_default_default |
| dj_indep_tket_28 | train | 28 | 36/36 | 0 | 0.025 | 1.970 | 2.090 | 12 | o3_default_default |
| dj_indep_tket_29 | train | 29 | 36/36 | 0 | 0.026 | 1.976 | 2.000 | 12 | o3_default_default |
| dj_indep_tket_3 | train | 3 | 36/36 | 0 | 0.023 | 0.058 | 0.059 | 12 | o3_default_default |
| dj_indep_tket_30 | train | 30 | 36/36 | 0 | 0.029 | 1.975 | 2.107 | 12 | o3_default_default |
| dj_indep_tket_4 | train | 4 | 36/36 | 0 | 0.026 | 1.565 | 1.766 | 12 | o3_default_default |
| dj_indep_tket_40 | train | 40 | 36/36 | 0 | 0.030 | 1.370 | 1.385 | 12 | o3_default_default |
| dj_indep_tket_5 | train | 5 | 36/36 | 0 | 0.024 | 3.334 | 3.447 | 12 | o3_default_default |
| dj_indep_tket_50 | train | 50 | 36/36 | 0 | 0.031 | 0.730 | 0.793 | 12 | o3_default_default |
| dj_indep_tket_6 | train | 6 | 36/36 | 0 | 0.024 | 3.398 | 3.576 | 12 | o3_default_default |
| dj_indep_tket_7 | train | 7 | 36/36 | 0 | 0.025 | 3.259 | 3.352 | 12 | o3_default_default |
| dj_indep_tket_8 | train | 8 | 36/36 | 0 | 0.025 | 3.283 | 3.522 | 12 | o3_default_default |
| dj_indep_tket_9 | train | 9 | 36/36 | 0 | 0.025 | 3.227 | 3.344 | 12 | o3_default_default |
| graphstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.024 | 3.237 | 3.289 | 12 | o2_default_default |
| graphstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.023 | 3.047 | 3.167 | 12 | o2_default_default |
| graphstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.025 | 3.032 | 3.058 | 12 | o2_default_default |
| graphstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.025 | 2.942 | 3.144 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.024 | 2.943 | 2.994 | 12 | o2_default_default |
| graphstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.024 | 2.880 | 3.119 | 12 | o2_default_default |
| graphstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.024 | 2.643 | 2.777 | 12 | o2_default_default |
| graphstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.025 | 2.493 | 2.609 | 12 | o2_default_default |
| graphstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.025 | 2.650 | 2.856 | 12 | o2_default_default |
| graphstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.024 | 2.383 | 2.723 | 12 | o2_default_default |
| graphstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.025 | 2.369 | 2.514 | 12 | o2_default_default |
| graphstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.025 | 2.280 | 2.323 | 12 | o2_default_default |
| graphstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.027 | 2.206 | 2.280 | 12 | o2_default_default |
| graphstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.026 | 2.230 | 2.327 | 12 | o2_default_default |
| graphstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.025 | 1.953 | 2.111 | 12 | o2_default_default |
| graphstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.025 | 1.960 | 2.093 | 12 | o2_default_default |
| graphstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.027 | 1.842 | 1.880 | 12 | o2_default_default |
| graphstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.025 | 1.700 | 1.842 | 12 | o2_default_default |
| graphstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.026 | 1.725 | 1.901 | 12 | o2_default_default |
| graphstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.028 | 1.559 | 1.649 | 12 | o2_default_default |
| graphstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.023 | 0.081 | 0.087 | 12 | o2_default_default |
| graphstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.027 | 1.565 | 1.687 | 12 | o2_default_default |
| graphstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.030 | 2.887 | 2.914 | 12 | o2_default_default |
| graphstate_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.033 | 0.972 | 1.068 | 12 | o2_default_default |
| graphstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.026 | 3.841 | 3.930 | 12 | o2_default_default |
| graphstate_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.029 | 0.556 | 0.592 | 12 | o2_default_default |
| graphstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.023 | 3.575 | 3.838 | 12 | o2_default_default |
| graphstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 3.597 | 3.761 | 12 | o2_default_default |
| graphstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.025 | 3.492 | 3.763 | 12 | o2_default_default |
| graphstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.023 | 3.349 | 3.640 | 12 | o2_default_default |
| graphstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.024 | 3.297 | 3.399 | 12 | o2_default_default |
| graphstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.024 | 3.298 | 3.387 | 12 | o2_default_default |
| graphstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.024 | 3.019 | 3.106 | 12 | o2_default_default |
| graphstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.024 | 2.839 | 2.976 | 12 | o2_default_default |
| graphstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.025 | 3.043 | 3.155 | 12 | o2_default_default |
| graphstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.025 | 2.663 | 2.817 | 12 | o2_default_default |
| graphstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.026 | 2.604 | 2.710 | 12 | o2_default_default |
| graphstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.025 | 2.591 | 2.719 | 12 | o2_default_default |
| graphstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.024 | 2.617 | 2.728 | 12 | o2_default_default |
| graphstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.025 | 2.451 | 2.541 | 12 | o2_default_default |
| graphstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.024 | 2.455 | 2.546 | 12 | o2_default_default |
| graphstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.024 | 2.285 | 2.383 | 12 | o2_default_default |
| graphstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.021 | 2.068 | 2.288 | 12 | o2_default_default |
| graphstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.024 | 2.191 | 2.243 | 12 | o2_default_default |
| graphstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.021 | 1.954 | 2.109 | 12 | o2_default_default |
| graphstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.023 | 1.891 | 1.947 | 12 | o2_default_default |
| graphstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.022 | 1.881 | 1.909 | 12 | o2_default_default |
| graphstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.023 | 1.879 | 1.917 | 12 | o2_default_default |
| graphstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.024 | 1.688 | 1.749 | 12 | o2_default_default |
| graphstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.023 | 1.590 | 1.619 | 12 | o2_default_default |
| graphstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.021 | 0.074 | 0.078 | 12 | o2_default_default |
| graphstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.024 | 1.481 | 1.551 | 12 | o2_default_default |
| graphstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.020 | 2.533 | 2.601 | 12 | o2_default_default |
| graphstate_indep_tket_40 | train | 40 | 36/36 | 0 | 0.025 | 0.925 | 1.031 | 12 | o2_default_default |
| graphstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.019 | 3.868 | 4.009 | 12 | o2_default_default |
| graphstate_indep_tket_50 | train | 50 | 36/36 | 0 | 0.025 | 0.555 | 0.610 | 12 | o2_default_default |
| graphstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.023 | 3.523 | 3.795 | 12 | o2_default_default |
| graphstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.024 | 3.464 | 3.679 | 12 | o2_default_default |
| graphstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.023 | 3.441 | 3.545 | 12 | o2_default_default |
| graphstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.023 | 3.510 | 3.757 | 12 | o2_default_default |
| portfolioqaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.023 | 0.081 | 0.087 | 12 | o2_default_default |
| portfolioqaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.024 | 3.662 | 3.766 | 12 | o2_default_default |
| portfolioqaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.023 | 7.867 | 8.369 | 12 | o2_default_default |
| portfolioqaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.023 | 10.897 | 11.071 | 12 | o2_default_default |
| portfolioqaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 12.659 | 13.698 | 12 | o2_default_default |
| portfolioqaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.022 | 0.075 | 0.080 | 12 | o2_default_default |
| portfolioqaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.021 | 3.462 | 3.661 | 12 | o2_default_default |
| portfolioqaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.022 | 8.427 | 8.519 | 12 | o2_default_default |
| portfolioqaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.025 | 10.713 | 11.114 | 12 | o2_default_default |
| portfolioqaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.023 | 13.124 | 13.450 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.028 | 18.943 | 20.541 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.029 | 21.234 | 21.509 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.022 | 0.076 | 0.088 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.023 | 3.570 | 3.759 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.024 | 8.410 | 8.642 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.025 | 10.867 | 11.191 | 12 | o3_default_default |
| portfoliovqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.027 | 12.445 | 13.209 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.024 | 14.376 | 15.496 | 12 | o2_default_default |
| portfoliovqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.029 | 17.238 | 17.575 | 12 | o3_default_default |
| portfoliovqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.028 | 17.865 | 18.187 | 12 | o2_default_default |
| portfoliovqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.028 | 21.237 | 21.641 | 12 | o2_default_default |
| portfoliovqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.021 | 0.075 | 0.082 | 12 | o2_default_default |
| portfoliovqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.023 | 3.640 | 3.768 | 12 | o2_default_default |
| portfoliovqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.024 | 8.238 | 8.358 | 12 | o2_default_default |
| portfoliovqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.023 | 10.801 | 10.918 | 12 | o2_default_default |
| portfoliovqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.023 | 12.154 | 12.427 | 12 | o2_default_default |
| portfoliovqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.026 | 14.282 | 15.189 | 12 | o2_default_default |
| portfoliovqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.028 | 17.542 | 17.888 | 12 | o3_default_default |
| qaoa_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.021 | 3.239 | 3.350 | 12 | o2_default_default |
| qaoa_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.021 | 3.093 | 3.433 | 12 | o2_default_default |
| qaoa_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.022 | 3.166 | 3.277 | 12 | o2_default_default |
| qaoa_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.023 | 2.985 | 3.046 | 12 | o2_default_default |
| qaoa_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.023 | 2.799 | 2.905 | 12 | o2_default_default |
| qaoa_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.023 | 0.072 | 0.079 | 12 | o2_default_default |
| qaoa_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.019 | 2.478 | 2.514 | 12 | o2_default_default |
| qaoa_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.021 | 3.740 | 3.755 | 12 | o2_default_default |
| qaoa_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.021 | 3.552 | 3.592 | 12 | o2_default_default |
| qaoa_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.021 | 3.311 | 3.646 | 12 | o2_default_default |
| qaoa_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.023 | 3.391 | 3.504 | 12 | o2_default_default |
| qaoa_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.020 | 3.227 | 3.342 | 12 | o2_default_default |
| qaoa_indep_tket_10 | train | 10 | 36/36 | 0 | 0.020 | 3.113 | 3.378 | 12 | o2_default_default |
| qaoa_indep_tket_11 | train | 11 | 36/36 | 0 | 0.024 | 3.148 | 3.178 | 12 | o2_default_default |
| qaoa_indep_tket_12 | train | 12 | 36/36 | 0 | 0.021 | 3.215 | 3.269 | 12 | o2_default_default |
| qaoa_indep_tket_13 | train | 13 | 36/36 | 0 | 0.024 | 2.899 | 3.075 | 12 | o2_default_default |
| qaoa_indep_tket_14 | train | 14 | 36/36 | 0 | 0.022 | 2.777 | 2.834 | 12 | o2_default_default |
| qaoa_indep_tket_3 | train | 3 | 36/36 | 0 | 0.019 | 0.074 | 0.079 | 12 | o2_default_default |
| qaoa_indep_tket_4 | train | 4 | 36/36 | 0 | 0.020 | 2.458 | 2.621 | 12 | o2_default_default |
| qaoa_indep_tket_5 | train | 5 | 36/36 | 0 | 0.023 | 3.735 | 3.860 | 12 | o2_default_default |
| qaoa_indep_tket_6 | train | 6 | 36/36 | 0 | 0.022 | 3.559 | 3.708 | 12 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.021 | 3.546 | 3.625 | 12 | o2_default_default |
| qaoa_indep_tket_8 | train | 8 | 36/36 | 0 | 0.023 | 3.418 | 3.505 | 12 | o2_default_default |
| qaoa_indep_tket_9 | train | 9 | 36/36 | 0 | 0.022 | 3.373 | 3.457 | 12 | o2_default_default |
| qnn_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.020 | 0.027 | 0.030 | 12 | o2_default_default |
| qnn_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.023 | 0.080 | 0.086 | 12 | o3_default_default |
| qnn_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.066 | 30.982 | 32.532 | 12 | o2_default_default |
| qnn_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.024 | 3.414 | 3.475 | 12 | o2_default_default |
| qnn_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.024 | 7.786 | 7.970 | 12 | o2_default_default |
| qnn_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.024 | 10.083 | 10.244 | 12 | o2_default_default |
| qnn_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.021 | 12.020 | 12.213 | 12 | o2_default_default |
| qnn_indep_tket_2 | train | 2 | 36/36 | 0 | 0.019 | 0.024 | 0.028 | 12 | o2_default_default |
| qnn_indep_tket_3 | train | 3 | 36/36 | 0 | 0.022 | 0.079 | 0.085 | 12 | o2_default_default |
| qnn_indep_tket_30 | train | 30 | 36/36 | 0 | 0.066 | 32.520 | 32.957 | 12 | o2_default_default |
| qnn_indep_tket_4 | train | 4 | 36/36 | 0 | 0.022 | 3.468 | 3.664 | 12 | o2_default_default |
| qnn_indep_tket_5 | train | 5 | 36/36 | 0 | 0.023 | 8.221 | 8.761 | 12 | o2_default_default |
| qnn_indep_tket_6 | train | 6 | 36/36 | 0 | 0.024 | 10.335 | 11.007 | 12 | o2_default_default |
| qnn_indep_tket_7 | train | 7 | 36/36 | 0 | 0.026 | 12.576 | 13.502 | 12 | o2_default_default |
| random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.022 | 0.029 | 0.031 | 12 | o2_default_default |
| random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.025 | 0.074 | 0.078 | 12 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.095 | 34.786 | 35.084 | 12 | o3_default_default |
| random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.025 | 5.491 | 5.636 | 12 | o2_default_default |
| random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.028 | 6.259 | 6.427 | 12 | o3_default_default |
| random_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.023 | 8.915 | 9.433 | 12 | o2_default_default |
| random_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.029 | 12.062 | 12.323 | 12 | o2_default_default |
| random_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.030 | 12.185 | 12.668 | 12 | o3_default_default |
| random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.021 | 0.032 | 0.033 | 12 | o2_default_default |
| random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.026 | 0.073 | 0.078 | 12 | o2_default_default |
| random_indep_tket_30 | train | 30 | 36/36 | 0 | 0.084 | 34.148 | 34.549 | 12 | o2_default_default |
| random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.025 | 5.453 | 5.648 | 12 | o2_default_default |
| random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.024 | 6.150 | 6.507 | 12 | o2_default_default |
| random_indep_tket_6 | train | 6 | 36/36 | 0 | 0.027 | 9.102 | 9.251 | 12 | o2_default_default |
| random_indep_tket_7 | train | 7 | 36/36 | 0 | 0.028 | 12.171 | 12.207 | 12 | o3_default_default |
| random_indep_tket_8 | train | 8 | 36/36 | 0 | 0.030 | 11.848 | 12.329 | 12 | o2_default_default |
| realamprandom_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.028 | 17.931 | 19.605 | 12 | o2_default_default |
| realamprandom_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.026 | 19.397 | 21.577 | 12 | o2_default_default |
| realamprandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.019 | 0.031 | 0.191 | 12 | o2_default_default |
| realamprandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.025 | 0.080 | 0.095 | 12 | o2_default_default |
| realamprandom_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.077 | 32.643 | 32.981 | 12 | o3_default_default |
| realamprandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.025 | 3.499 | 3.628 | 12 | o2_default_default |
| realamprandom_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.208 | 23.284 | 25.222 | 12 | o3_default_default |
| realamprandom_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.022 | 8.340 | 8.927 | 12 | o2_default_default |
| realamprandom_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.273 | 11.657 | 12.530 | 12 | o3_default_default |
| realamprandom_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.019 | 10.460 | 10.872 | 12 | o2_default_default |
| realamprandom_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.026 | 12.693 | 13.654 | 12 | o2_default_default |
| realamprandom_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.024 | 14.543 | 15.512 | 12 | o2_default_default |
| realamprandom_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.023 | 16.485 | 17.306 | 12 | o2_default_default |
| realamprandom_indep_tket_10 | train | 10 | 36/36 | 0 | 0.026 | 19.034 | 19.705 | 12 | o2_default_default |
| realamprandom_indep_tket_11 | train | 11 | 36/36 | 0 | 0.026 | 19.578 | 20.838 | 12 | o2_default_default |
| realamprandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.020 | 0.029 | 0.031 | 12 | o2_default_default |
| realamprandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.020 | 0.073 | 0.086 | 12 | o2_default_default |
| realamprandom_indep_tket_30 | train | 30 | 36/36 | 0 | 0.091 | 32.246 | 33.088 | 12 | o3_default_default |
| realamprandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.023 | 3.515 | 3.619 | 12 | o2_default_default |
| realamprandom_indep_tket_40 | train | 40 | 36/36 | 0 | 0.209 | 23.044 | 25.459 | 12 | o3_default_default |
| realamprandom_indep_tket_5 | train | 5 | 36/36 | 0 | 0.022 | 8.199 | 8.669 | 12 | o2_default_default |
| realamprandom_indep_tket_50 | train | 50 | 36/36 | 0 | 0.311 | 11.666 | 12.670 | 12 | o3_default_default |
| realamprandom_indep_tket_6 | train | 6 | 36/36 | 0 | 0.023 | 10.117 | 11.052 | 12 | o2_default_default |
| realamprandom_indep_tket_7 | train | 7 | 36/36 | 0 | 0.024 | 12.626 | 13.592 | 12 | o2_default_default |
| realamprandom_indep_tket_8 | train | 8 | 36/36 | 0 | 0.024 | 14.352 | 15.870 | 12 | o2_default_default |
| realamprandom_indep_tket_9 | train | 9 | 36/36 | 0 | 0.026 | 17.552 | 18.090 | 12 | o2_default_default |
| su2random_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.019 | 0.028 | 0.204 | 12 | o2_default_default |
| su2random_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.022 | 0.071 | 0.079 | 12 | o2_default_default |
| su2random_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.072 | 30.437 | 32.826 | 12 | o2_default_default |
| su2random_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.026 | 3.440 | 3.717 | 12 | o2_default_default |
| su2random_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.140 | 22.695 | 23.136 | 12 | o3_default_default |
| su2random_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.024 | 7.891 | 8.970 | 12 | o2_default_default |
| su2random_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.160 | 11.175 | 11.790 | 12 | o2_default_default |
| su2random_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.024 | 10.188 | 11.460 | 12 | o2_default_default |
| su2random_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 12.519 | 13.677 | 12 | o2_default_default |
| su2random_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.024 | 14.594 | 16.243 | 12 | o2_default_default |
| su2random_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.023 | 16.096 | 17.440 | 12 | o2_default_default |
| su2random_indep_tket_2 | train | 2 | 36/36 | 0 | 0.018 | 0.025 | 0.035 | 12 | o2_default_default |
| su2random_indep_tket_3 | train | 3 | 36/36 | 0 | 0.024 | 0.075 | 0.083 | 12 | o2_default_default |
| su2random_indep_tket_30 | train | 30 | 36/36 | 0 | 0.068 | 32.771 | 33.043 | 12 | o2_default_default |
| su2random_indep_tket_4 | train | 4 | 36/36 | 0 | 0.023 | 3.544 | 3.623 | 12 | o2_default_default |
| su2random_indep_tket_40 | train | 40 | 36/36 | 0 | 0.109 | 22.531 | 24.911 | 12 | o2_default_default |
| su2random_indep_tket_5 | train | 5 | 36/36 | 0 | 0.027 | 8.293 | 8.544 | 12 | o3_default_default |
| su2random_indep_tket_50 | train | 50 | 36/36 | 0 | 0.154 | 11.283 | 11.960 | 12 | o2_default_default |
| su2random_indep_tket_6 | train | 6 | 36/36 | 0 | 0.025 | 10.449 | 11.201 | 12 | o2_default_default |
| su2random_indep_tket_7 | train | 7 | 36/36 | 0 | 0.026 | 13.153 | 13.662 | 12 | o2_default_default |
| su2random_indep_tket_8 | train | 8 | 36/36 | 0 | 0.025 | 15.718 | 15.950 | 12 | o2_default_default |
| su2random_indep_tket_9 | train | 9 | 36/36 | 0 | 0.028 | 17.104 | 18.457 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.026 | 20.048 | 20.299 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.031 | 20.862 | 21.931 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.021 | 0.030 | 0.031 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.024 | 0.073 | 0.076 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.084 | 32.565 | 33.335 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.025 | 3.482 | 3.665 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.264 | 23.210 | 24.855 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.024 | 8.506 | 8.909 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.317 | 11.668 | 12.839 | 12 | o3_default_default |
| twolocalrandom_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.025 | 10.417 | 11.143 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 12.474 | 13.435 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.024 | 14.198 | 15.528 | 12 | o2_default_default |
| twolocalrandom_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.026 | 16.743 | 17.635 | 12 | o2_default_default |
| twolocalrandom_indep_tket_10 | train | 10 | 36/36 | 0 | 0.024 | 18.332 | 20.035 | 12 | o2_default_default |
| twolocalrandom_indep_tket_11 | train | 11 | 36/36 | 0 | 0.026 | 20.138 | 21.627 | 12 | o2_default_default |
| twolocalrandom_indep_tket_2 | train | 2 | 36/36 | 0 | 0.019 | 0.028 | 0.031 | 12 | o2_default_default |
| twolocalrandom_indep_tket_3 | train | 3 | 36/36 | 0 | 0.022 | 0.075 | 0.081 | 12 | o2_default_default |
| twolocalrandom_indep_tket_30 | train | 30 | 36/36 | 0 | 0.089 | 31.066 | 33.546 | 12 | o3_default_default |
| twolocalrandom_indep_tket_4 | train | 4 | 36/36 | 0 | 0.023 | 3.609 | 3.809 | 12 | o2_default_default |
| twolocalrandom_indep_tket_40 | train | 40 | 36/36 | 0 | 0.164 | 24.894 | 25.390 | 12 | o3_default_default |
| twolocalrandom_indep_tket_5 | train | 5 | 36/36 | 0 | 0.025 | 8.063 | 8.591 | 12 | o2_default_default |
| twolocalrandom_indep_tket_50 | train | 50 | 36/36 | 0 | 0.308 | 12.526 | 12.870 | 12 | o3_default_default |
| twolocalrandom_indep_tket_6 | train | 6 | 36/36 | 0 | 0.023 | 10.064 | 10.292 | 12 | o2_default_default |
| twolocalrandom_indep_tket_7 | train | 7 | 36/36 | 0 | 0.026 | 12.378 | 13.284 | 12 | o2_default_default |
| twolocalrandom_indep_tket_8 | train | 8 | 36/36 | 0 | 0.026 | 14.320 | 14.572 | 12 | o2_default_default |
| twolocalrandom_indep_tket_9 | train | 9 | 36/36 | 0 | 0.028 | 17.252 | 17.927 | 12 | o2_default_default |
| vqe_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.023 | 2.098 | 2.151 | 12 | o2_default_default |
| vqe_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.024 | 1.986 | 2.118 | 12 | o2_default_default |
| vqe_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.024 | 1.925 | 2.021 | 12 | o2_default_default |
| vqe_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.023 | 1.906 | 1.976 | 12 | o2_default_default |
| vqe_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.024 | 1.843 | 1.953 | 12 | o2_default_default |
| vqe_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.025 | 1.809 | 1.918 | 12 | o2_default_default |
| vqe_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.025 | 1.835 | 1.886 | 12 | o2_default_default |
| vqe_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.026 | 0.054 | 0.059 | 12 | o2_default_default |
| vqe_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.023 | 1.575 | 1.621 | 12 | o2_default_default |
| vqe_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.023 | 2.329 | 2.544 | 12 | o2_default_default |
| vqe_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.024 | 2.228 | 2.538 | 12 | o2_default_default |
| vqe_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.024 | 2.197 | 2.419 | 12 | o2_default_default |
| vqe_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.023 | 2.243 | 2.386 | 12 | o2_default_default |
| vqe_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.025 | 2.108 | 2.190 | 12 | o2_default_default |
| vqe_indep_tket_10 | train | 10 | 36/36 | 0 | 0.024 | 2.194 | 2.251 | 12 | o2_default_default |
| vqe_indep_tket_11 | train | 11 | 36/36 | 0 | 0.026 | 2.089 | 2.235 | 12 | o3_default_default |
| vqe_indep_tket_12 | train | 12 | 36/36 | 0 | 0.025 | 1.942 | 2.073 | 12 | o2_default_default |
| vqe_indep_tket_13 | train | 13 | 36/36 | 0 | 0.024 | 1.950 | 2.002 | 12 | o2_default_default |
| vqe_indep_tket_14 | train | 14 | 36/36 | 0 | 0.024 | 1.841 | 2.050 | 12 | o2_default_default |
| vqe_indep_tket_15 | train | 15 | 36/36 | 0 | 0.025 | 1.822 | 1.970 | 12 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.026 | 1.799 | 1.859 | 12 | o2_default_default |
| vqe_indep_tket_3 | train | 3 | 36/36 | 0 | 0.023 | 0.054 | 0.058 | 12 | o2_default_default |
| vqe_indep_tket_4 | train | 4 | 36/36 | 0 | 0.023 | 1.529 | 1.548 | 12 | o2_default_default |
| vqe_indep_tket_5 | train | 5 | 36/36 | 0 | 0.024 | 2.405 | 2.580 | 12 | o2_default_default |
| vqe_indep_tket_6 | train | 6 | 36/36 | 0 | 0.025 | 2.355 | 2.474 | 12 | o2_default_default |
| vqe_indep_tket_7 | train | 7 | 36/36 | 0 | 0.023 | 2.249 | 2.438 | 12 | o2_default_default |
| vqe_indep_tket_8 | train | 8 | 36/36 | 0 | 0.024 | 2.206 | 2.367 | 12 | o2_default_default |
| vqe_indep_tket_9 | train | 9 | 36/36 | 0 | 0.025 | 2.149 | 2.203 | 12 | o2_default_default |
| wstate_indep_qiskit_10 | train | 10 | 36/36 | 0 | 0.026 | 3.541 | 3.581 | 12 | o3_default_default |
| wstate_indep_qiskit_11 | train | 11 | 36/36 | 0 | 0.025 | 3.294 | 3.619 | 12 | o2_default_default |
| wstate_indep_qiskit_12 | train | 12 | 36/36 | 0 | 0.025 | 3.242 | 3.376 | 12 | o3_default_default |
| wstate_indep_qiskit_13 | train | 13 | 36/36 | 0 | 0.025 | 3.147 | 3.158 | 12 | o2_default_default |
| wstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.029 | 2.975 | 3.125 | 12 | o3_default_default |
| wstate_indep_qiskit_15 | train | 15 | 36/36 | 0 | 0.028 | 2.889 | 3.023 | 12 | o2_default_default |
| wstate_indep_qiskit_16 | train | 16 | 36/36 | 0 | 0.025 | 2.827 | 2.997 | 12 | o2_default_default |
| wstate_indep_qiskit_17 | train | 17 | 36/36 | 0 | 0.025 | 2.673 | 2.869 | 12 | o2_default_default |
| wstate_indep_qiskit_18 | train | 18 | 36/36 | 0 | 0.026 | 2.658 | 2.679 | 12 | o2_default_default |
| wstate_indep_qiskit_19 | train | 19 | 36/36 | 0 | 0.027 | 2.409 | 2.668 | 12 | o2_default_default |
| wstate_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.021 | 0.029 | 0.031 | 12 | o2_default_default |
| wstate_indep_qiskit_20 | train | 20 | 36/36 | 0 | 0.028 | 2.568 | 2.588 | 12 | o3_default_default |
| wstate_indep_qiskit_21 | train | 21 | 36/36 | 0 | 0.026 | 2.290 | 2.312 | 12 | o2_default_default |
| wstate_indep_qiskit_22 | train | 22 | 36/36 | 0 | 0.029 | 2.228 | 2.275 | 12 | o2_default_default |
| wstate_indep_qiskit_23 | train | 23 | 36/36 | 0 | 0.029 | 2.244 | 2.392 | 12 | o3_default_default |
| wstate_indep_qiskit_24 | train | 24 | 36/36 | 0 | 0.028 | 2.085 | 2.174 | 12 | o2_default_default |
| wstate_indep_qiskit_25 | train | 25 | 36/36 | 0 | 0.026 | 1.925 | 2.040 | 12 | o2_default_default |
| wstate_indep_qiskit_26 | train | 26 | 36/36 | 0 | 0.031 | 1.909 | 2.039 | 12 | o3_default_default |
| wstate_indep_qiskit_27 | train | 27 | 36/36 | 0 | 0.032 | 1.823 | 1.970 | 12 | o3_default_default |
| wstate_indep_qiskit_28 | train | 28 | 36/36 | 0 | 0.026 | 1.737 | 1.762 | 12 | o2_default_default |
| wstate_indep_qiskit_29 | train | 29 | 36/36 | 0 | 0.031 | 1.663 | 1.810 | 12 | o3_default_default |
| wstate_indep_qiskit_3 | train | 3 | 36/36 | 0 | 0.023 | 0.085 | 0.088 | 12 | o2_default_default |
| wstate_indep_qiskit_30 | train | 30 | 36/36 | 0 | 0.029 | 1.618 | 1.744 | 12 | o2_default_default |
| wstate_indep_qiskit_4 | train | 4 | 36/36 | 0 | 0.023 | 2.648 | 2.675 | 12 | o2_default_default |
| wstate_indep_qiskit_40 | train | 40 | 36/36 | 0 | 0.033 | 0.920 | 1.080 | 12 | o2_default_default |
| wstate_indep_qiskit_5 | train | 5 | 36/36 | 0 | 0.024 | 4.127 | 4.329 | 12 | o2_default_default |
| wstate_indep_qiskit_50 | train | 50 | 36/36 | 0 | 0.030 | 0.512 | 0.586 | 12 | o2_default_default |
| wstate_indep_qiskit_6 | train | 6 | 36/36 | 0 | 0.023 | 3.860 | 4.039 | 12 | o2_default_default |
| wstate_indep_qiskit_7 | train | 7 | 36/36 | 0 | 0.025 | 3.667 | 3.915 | 12 | o3_default_default |
| wstate_indep_qiskit_8 | train | 8 | 36/36 | 0 | 0.024 | 3.725 | 3.824 | 12 | o2_default_default |
| wstate_indep_qiskit_9 | train | 9 | 36/36 | 0 | 0.025 | 3.599 | 3.737 | 12 | o2_default_default |
| wstate_indep_tket_10 | train | 10 | 36/36 | 0 | 0.025 | 3.363 | 3.439 | 12 | o2_default_default |
| wstate_indep_tket_11 | train | 11 | 36/36 | 0 | 0.025 | 3.267 | 3.469 | 12 | o3_default_default |
| wstate_indep_tket_12 | train | 12 | 36/36 | 0 | 0.024 | 3.236 | 3.301 | 12 | o2_default_default |
| wstate_indep_tket_13 | train | 13 | 36/36 | 0 | 0.025 | 3.197 | 3.289 | 12 | o3_default_default |
| wstate_indep_tket_14 | train | 14 | 36/36 | 0 | 0.026 | 2.984 | 3.072 | 12 | o2_default_default |
| wstate_indep_tket_15 | train | 15 | 36/36 | 0 | 0.026 | 2.982 | 3.019 | 12 | o2_default_default |
| wstate_indep_tket_16 | train | 16 | 36/36 | 0 | 0.026 | 2.803 | 2.923 | 12 | o2_default_default |
| wstate_indep_tket_17 | train | 17 | 36/36 | 0 | 0.026 | 2.634 | 2.720 | 12 | o2_default_default |
| wstate_indep_tket_18 | train | 18 | 36/36 | 0 | 0.026 | 2.490 | 2.820 | 12 | o2_default_default |
| wstate_indep_tket_19 | train | 19 | 36/36 | 0 | 0.025 | 2.535 | 2.696 | 12 | o2_default_default |
| wstate_indep_tket_2 | train | 2 | 36/36 | 0 | 0.021 | 0.044 | 0.053 | 12 | o2_default_default |
| wstate_indep_tket_20 | train | 20 | 36/36 | 0 | 0.026 | 2.408 | 2.606 | 12 | o2_default_default |
| wstate_indep_tket_21 | train | 21 | 36/36 | 0 | 0.027 | 2.449 | 2.525 | 12 | o3_default_default |
| wstate_indep_tket_22 | train | 22 | 36/36 | 0 | 0.027 | 2.069 | 2.279 | 12 | o2_default_default |
| wstate_indep_tket_23 | train | 23 | 36/36 | 0 | 0.027 | 2.182 | 2.333 | 12 | o2_default_default |
| wstate_indep_tket_24 | train | 24 | 36/36 | 0 | 0.027 | 2.024 | 2.078 | 12 | o2_default_default |
| wstate_indep_tket_25 | train | 25 | 36/36 | 0 | 0.027 | 1.956 | 2.128 | 12 | o2_default_default |
| wstate_indep_tket_26 | train | 26 | 36/36 | 0 | 0.030 | 1.788 | 1.848 | 12 | o3_default_default |
| wstate_indep_tket_27 | train | 27 | 36/36 | 0 | 0.028 | 1.842 | 1.928 | 12 | o2_default_default |
| wstate_indep_tket_28 | train | 28 | 36/36 | 0 | 0.027 | 1.745 | 1.767 | 12 | o2_default_default |
| wstate_indep_tket_29 | train | 29 | 36/36 | 0 | 0.027 | 1.703 | 1.780 | 12 | o2_default_default |
| wstate_indep_tket_3 | train | 3 | 36/36 | 0 | 0.024 | 0.072 | 0.090 | 12 | o2_default_default |
| wstate_indep_tket_30 | train | 30 | 36/36 | 0 | 0.028 | 1.603 | 1.715 | 12 | o2_default_default |
| wstate_indep_tket_4 | train | 4 | 36/36 | 0 | 0.022 | 2.615 | 2.700 | 12 | o2_default_default |
| wstate_indep_tket_40 | train | 40 | 36/36 | 0 | 0.032 | 0.990 | 1.013 | 12 | o3_default_default |
| wstate_indep_tket_5 | train | 5 | 36/36 | 0 | 0.025 | 4.036 | 4.164 | 12 | o2_default_default |
| wstate_indep_tket_50 | train | 50 | 36/36 | 0 | 0.029 | 0.512 | 0.575 | 12 | o2_default_default |
| wstate_indep_tket_6 | train | 6 | 36/36 | 0 | 0.025 | 3.902 | 4.059 | 12 | o2_default_default |
| wstate_indep_tket_7 | train | 7 | 36/36 | 0 | 0.024 | 3.803 | 3.966 | 12 | o2_default_default |
| wstate_indep_tket_8 | train | 8 | 36/36 | 0 | 0.024 | 3.666 | 3.744 | 12 | o2_default_default |
| wstate_indep_tket_9 | train | 9 | 36/36 | 0 | 0.026 | 3.298 | 3.399 | 12 | o3_default_default |
| pricingcall_indep_qiskit_11 | validation | 11 | 36/36 | 0 | 0.033 | 4.439 | 4.570 | 12 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.027 | 5.244 | 5.664 | 12 | o2_default_default |
| pricingcall_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.029 | 5.238 | 5.561 | 12 | o2_default_default |
| pricingcall_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.031 | 6.068 | 6.283 | 12 | o2_default_default |
| pricingcall_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.026 | 5.229 | 5.460 | 12 | o2_default_default |
| pricingcall_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.029 | 5.423 | 5.652 | 12 | o2_default_default |
| pricingcall_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.031 | 6.051 | 6.180 | 12 | o3_default_default |
| pricingput_indep_qiskit_11 | validation | 11 | 36/36 | 0 | 0.039 | 4.462 | 4.586 | 12 | o2_default_default |
| pricingput_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.030 | 5.146 | 5.724 | 12 | o3_default_default |
| pricingput_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.028 | 5.522 | 5.779 | 12 | o2_default_default |
| pricingput_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.029 | 5.972 | 6.036 | 12 | o2_default_default |
| pricingput_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.031 | 5.298 | 5.507 | 12 | o3_default_default |
| pricingput_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.029 | 5.293 | 5.495 | 12 | o2_default_default |
| pricingput_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.034 | 6.150 | 6.277 | 12 | o3_default_default |
| qft_indep_qiskit_10 | validation | 10 | 36/36 | 0 | 0.024 | 18.399 | 19.655 | 12 | o2_default_default |
| qft_indep_qiskit_11 | validation | 11 | 36/36 | 0 | 0.022 | 19.461 | 21.494 | 12 | o2_default_default |
| qft_indep_qiskit_12 | validation | 12 | 36/36 | 0 | 0.020 | 21.297 | 22.998 | 12 | o2_default_default |
| qft_indep_qiskit_13 | validation | 13 | 36/36 | 0 | 0.023 | 22.739 | 24.302 | 12 | o2_default_default |
| qft_indep_qiskit_14 | validation | 14 | 36/36 | 0 | 0.022 | 24.055 | 25.794 | 12 | o2_default_default |
| qft_indep_qiskit_15 | validation | 15 | 36/36 | 0 | 0.025 | 26.679 | 26.959 | 12 | o2_default_default |
| qft_indep_qiskit_16 | validation | 16 | 36/36 | 0 | 0.029 | 27.925 | 29.292 | 12 | o2_default_default |
| qft_indep_qiskit_17 | validation | 17 | 36/36 | 0 | 0.028 | 27.309 | 29.515 | 12 | o2_default_default |
| qft_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.019 | 0.027 | 0.030 | 12 | o2_default_default |
| qft_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.024 | 0.075 | 0.081 | 12 | o2_default_default |
| qft_indep_qiskit_30 | validation | 30 | 36/36 | 0 | 0.031 | 21.900 | 23.542 | 12 | o2_default_default |
| qft_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.021 | 3.478 | 3.725 | 12 | o2_default_default |
| qft_indep_qiskit_40 | validation | 40 | 36/36 | 0 | 0.048 | 12.096 | 12.276 | 12 | o2_default_default |
| qft_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.024 | 8.390 | 8.727 | 12 | o2_default_default |
| qft_indep_qiskit_50 | validation | 50 | 36/36 | 0 | 0.055 | 3.492 | 3.585 | 12 | o2_default_default |
| qft_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.022 | 10.815 | 11.151 | 12 | o2_default_default |
| qft_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.023 | 13.051 | 13.304 | 12 | o2_default_default |
| qft_indep_qiskit_8 | validation | 8 | 36/36 | 0 | 0.024 | 15.265 | 15.919 | 12 | o2_default_default |
| qft_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.021 | 17.205 | 17.362 | 12 | o2_default_default |
| qft_indep_tket_10 | validation | 10 | 36/36 | 0 | 0.027 | 18.519 | 19.945 | 12 | o3_default_default |
| qft_indep_tket_11 | validation | 11 | 36/36 | 0 | 0.024 | 19.177 | 21.244 | 12 | o3_default_default |
| qft_indep_tket_12 | validation | 12 | 36/36 | 0 | 0.027 | 20.956 | 23.057 | 12 | o3_default_default |
| qft_indep_tket_13 | validation | 13 | 36/36 | 0 | 0.032 | 22.214 | 24.363 | 12 | o3_default_default |
| qft_indep_tket_14 | validation | 14 | 36/36 | 0 | 0.031 | 23.534 | 26.964 | 12 | o3_default_default |
| qft_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.020 | 0.029 | 0.210 | 12 | o2_default_default |
| qft_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.022 | 0.072 | 0.079 | 12 | o2_default_default |
| qft_indep_tket_30 | validation | 30 | 36/36 | 0 | 0.045 | 16.736 | 17.894 | 12 | o3_default_default |
| qft_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.020 | 3.450 | 3.698 | 12 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 36/36 | 0 | 0.059 | 7.443 | 7.724 | 12 | o3_default_default |
| qft_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.024 | 8.268 | 8.503 | 12 | o3_default_default |
| qft_indep_tket_50 | validation | 50 | 36/36 | 0 | 0.105 | 2.218 | 2.344 | 12 | o3_default_default |
| qft_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.024 | 10.736 | 11.140 | 12 | o2_default_default |
| qft_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.025 | 12.524 | 13.594 | 12 | o2_default_default |
| qft_indep_tket_8 | validation | 8 | 36/36 | 0 | 0.024 | 15.033 | 15.752 | 12 | o3_default_default |
| qft_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.023 | 17.549 | 18.077 | 12 | o3_default_default |
| qftentangled_indep_qiskit_10 | validation | 10 | 36/36 | 0 | 0.024 | 18.351 | 19.746 | 12 | o2_default_default |
| qftentangled_indep_qiskit_11 | validation | 11 | 36/36 | 0 | 0.021 | 21.170 | 21.547 | 12 | o2_default_default |
| qftentangled_indep_qiskit_12 | validation | 12 | 36/36 | 0 | 0.025 | 21.305 | 23.091 | 12 | o2_default_default |
| qftentangled_indep_qiskit_13 | validation | 13 | 36/36 | 0 | 0.022 | 24.304 | 25.231 | 12 | o2_default_default |
| qftentangled_indep_qiskit_14 | validation | 14 | 36/36 | 0 | 0.024 | 25.516 | 26.376 | 12 | o2_default_default |
| qftentangled_indep_qiskit_15 | validation | 15 | 36/36 | 0 | 0.026 | 27.003 | 27.547 | 12 | o2_default_default |
| qftentangled_indep_qiskit_16 | validation | 16 | 36/36 | 0 | 0.028 | 28.239 | 29.477 | 12 | o2_default_default |
| qftentangled_indep_qiskit_2 | validation | 2 | 36/36 | 0 | 0.022 | 0.030 | 0.037 | 12 | o2_default_default |
| qftentangled_indep_qiskit_3 | validation | 3 | 36/36 | 0 | 0.023 | 0.072 | 0.086 | 12 | o2_default_default |
| qftentangled_indep_qiskit_30 | validation | 30 | 36/36 | 0 | 0.033 | 21.799 | 23.695 | 12 | o2_default_default |
| qftentangled_indep_qiskit_4 | validation | 4 | 36/36 | 0 | 0.022 | 3.489 | 3.673 | 12 | o2_default_default |
| qftentangled_indep_qiskit_40 | validation | 40 | 36/36 | 0 | 0.041 | 11.520 | 12.441 | 12 | o2_default_default |
| qftentangled_indep_qiskit_5 | validation | 5 | 36/36 | 0 | 0.023 | 8.040 | 8.955 | 12 | o2_default_default |
| qftentangled_indep_qiskit_50 | validation | 50 | 36/36 | 0 | 0.050 | 3.622 | 3.796 | 12 | o2_default_default |
| qftentangled_indep_qiskit_6 | validation | 6 | 36/36 | 0 | 0.024 | 10.948 | 11.253 | 12 | o2_default_default |
| qftentangled_indep_qiskit_7 | validation | 7 | 36/36 | 0 | 0.024 | 12.472 | 13.818 | 12 | o2_default_default |
| qftentangled_indep_qiskit_8 | validation | 8 | 36/36 | 0 | 0.022 | 15.297 | 15.492 | 12 | o2_default_default |
| qftentangled_indep_qiskit_9 | validation | 9 | 36/36 | 0 | 0.023 | 17.148 | 18.196 | 12 | o2_default_default |
| qftentangled_indep_tket_10 | validation | 10 | 36/36 | 0 | 0.023 | 17.837 | 19.180 | 12 | o2_default_default |
| qftentangled_indep_tket_11 | validation | 11 | 36/36 | 0 | 0.024 | 21.051 | 21.902 | 12 | o2_default_default |
| qftentangled_indep_tket_12 | validation | 12 | 36/36 | 0 | 0.025 | 22.974 | 23.197 | 12 | o2_default_default |
| qftentangled_indep_tket_13 | validation | 13 | 36/36 | 0 | 0.027 | 22.096 | 24.812 | 12 | o2_default_default |
| qftentangled_indep_tket_14 | validation | 14 | 36/36 | 0 | 0.028 | 23.592 | 25.313 | 12 | o2_default_default |
| qftentangled_indep_tket_2 | validation | 2 | 36/36 | 0 | 0.021 | 0.031 | 0.032 | 12 | o2_default_default |
| qftentangled_indep_tket_3 | validation | 3 | 36/36 | 0 | 0.020 | 0.074 | 0.080 | 12 | o2_default_default |
| qftentangled_indep_tket_30 | validation | 30 | 36/36 | 0 | 0.044 | 16.171 | 16.311 | 12 | o2_default_default |
| qftentangled_indep_tket_4 | validation | 4 | 36/36 | 0 | 0.021 | 3.483 | 3.757 | 12 | o2_default_default |
| qftentangled_indep_tket_40 | validation | 40 | 36/36 | 0 | 0.056 | 7.402 | 7.597 | 12 | o2_default_default |
| qftentangled_indep_tket_5 | validation | 5 | 36/36 | 0 | 0.025 | 8.591 | 8.881 | 12 | o2_default_default |
| qftentangled_indep_tket_50 | validation | 50 | 36/36 | 0 | 0.076 | 2.048 | 2.201 | 12 | o2_default_default |
| qftentangled_indep_tket_6 | validation | 6 | 36/36 | 0 | 0.023 | 10.184 | 11.169 | 12 | o2_default_default |
| qftentangled_indep_tket_7 | validation | 7 | 36/36 | 0 | 0.021 | 12.281 | 13.304 | 12 | o2_default_default |
| qftentangled_indep_tket_8 | validation | 8 | 36/36 | 0 | 0.021 | 14.494 | 15.341 | 12 | o2_default_default |
| qftentangled_indep_tket_9 | validation | 9 | 36/36 | 0 | 0.022 | 16.110 | 16.934 | 12 | o2_default_default |

## Failure e timeout

Nessun failure o timeout osservato.

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Esito ignoto alla soglia | Minimo timeout stimato |
| --- | --- | --- | --- | --- |
| 30 | 30 | 0 | 0 | 30 |
| 60 | 0 | 0 | 0 | 0 |
| 100 | 0 | 0 | 0 | 0 |
| 120 | 0 | 0 | 0 | 0 |
| 300 | 0 | 0 | 0 | 0 |
| 600 | 0 | 0 | 0 | 0 |
| 900 | 0 | 0 | 0 | 0 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta. Questi casi restano ignoti e non sono inclusi nel minimo stimato. La stima usa i tempi osservati e non prevede l'effetto di cambiare i worker.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 5760 |
| Non eleggibili | 0 |
| Esempi RAG | 371 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

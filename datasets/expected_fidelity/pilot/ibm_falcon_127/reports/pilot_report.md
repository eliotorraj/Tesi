# Pilot Qiskit — ibm_falcon_127

Scheda generata automaticamente dagli artefatti del pilot. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 127 |
| Hash target | 225e5f6fd85af0b37a1dd7c6306dd046a8c7ca585f135dda6e6418dd16f76b48 |
| Qiskit | 2.1.1 |
| MQT Bench | 2.0.0 |
| MQT Predictor | 2.3.0 |
| Circuiti totali | 10 |
| Circuiti compatibili | 10 |
| Circuiti incompatibili | 0 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker | 2 |
| Timeout richiesto | 900.000 s |
| Cache hit | 360 |
| Durata invocazione | 0.452 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 360 | - |
| Osservati | 360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 335 | 93.1% |
| Failure | 0 | 0.0% |
| Timeout | 25 | 6.9% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 335 | 0.008 | 0.139 | 10.863 | 12.494 | 538.369 |
| Non-lookahead | 300 | 0.008 | 0.108 | 1.469 | 4.733 | 72.559 |
| Lookahead | 35 | 0.012 | 7.538 | 91.382 | 499.198 | 538.369 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.030 | 2.372 | 2.491 | 10 | 4 | 4 | 9 |
| o3_default_default | baseline | 3 | default | default | 30/30 | 0 | 0.728 | 71.404 | 72.559 | 10 | 3 | 5 | 8 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.021 | 0.435 | 0.465 | 10 | 1 | 1 | 5 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.017 | 0.156 | 0.168 | 10 | 2 | 3 | 3 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.013 | 0.147 | 0.163 | 10 | 0 | 0 | 1 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 30/30 | 0 | 0.642 | 8.412 | 10.854 | 10 | 0 | 0 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.067 | 0.687 | 0.727 | 10 | 0 | 3 | 3 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 30/30 | 0 | 0.475 | 4.696 | 4.722 | 10 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 19/30 | 11 | 7.188 | 319.278 | 538.369 | 6 | 0 | 0 | 1 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.029 | 0.893 | 0.992 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 16/30 | 14 | 19.081 | 496.857 | 531.971 | 4 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 30/30 | 0 | 0.935 | 7.813 | 10.055 | 10 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.018 | 0.151 | 0.156 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 35/36 | 1 | 0.046 | 14.187 | 19.942 | 11 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 34/36 | 2 | 0.029 | 7.083 | 12.577 | 11 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 0.657 | 1.259 | 1.475 | 10 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.261 | 77.868 | 81.883 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 36/36 | 0 | 1.822 | 496.857 | 538.369 | 12 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 32/36 | 4 | 0.032 | 45.396 | 105.444 | 10 | o2_dense_sabre |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.396 | 0.732 | 1.471 | 10 | o2_default_default |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 0.586 | 1.451 | 1.594 | 10 | o2_sabre_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.034 | 1.796 | 1.889 | 12 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 25 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 14 | 25 | 39 |
| 60 | 14 | 25 | 39 |
| 100 | 8 | 25 | 33 |
| 120 | 6 | 25 | 31 |
| 300 | 4 | 25 | 29 |
| 600 | 0 | 25 | 25 |
| 900 | 0 | 25 | 25 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 110 |
| Non eleggibili | 10 |
| Esempi RAG | 6 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

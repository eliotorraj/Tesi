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
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 2227.972 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 360 | - |
| Osservati | 360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 321 | 89.2% |
| Failure | 0 | 0.0% |
| Timeout | 39 | 10.8% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 321 | 0.008 | 0.153 | 1.591 | 10.198 | 30.255 |
| Non-lookahead | 297 | 0.008 | 0.126 | 1.095 | 7.080 | 15.498 |
| Lookahead | 24 | 0.011 | 5.283 | 7.732 | 27.110 | 30.255 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.049 | 3.137 | 3.376 | 10 | 4 | 4 | 9 |
| o3_default_default | baseline | 3 | default | default | 27/30 | 3 | 0.980 | 10.557 | 11.697 | 9 | 3 | 5 | 7 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.032 | 0.867 | 1.146 | 10 | 1 | 1 | 6 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.022 | 0.315 | 0.407 | 10 | 2 | 3 | 3 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.019 | 0.225 | 0.262 | 10 | 0 | 0 | 1 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 30/30 | 0 | 1.099 | 8.870 | 11.278 | 10 | 0 | 0 | 1 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.079 | 0.955 | 1.107 | 10 | 0 | 3 | 3 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 30/30 | 0 | 0.832 | 6.925 | 7.660 | 10 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 15/30 | 15 | 10.634 | 15.506 | 16.363 | 5 | 0 | 0 | 0 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.045 | 1.390 | 1.422 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 9/30 | 21 | 0.338 | 29.708 | 30.255 | 2 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 30/30 | 0 | 1.406 | 13.013 | 15.498 | 10 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.015 | 0.066 | 0.157 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 35/36 | 1 | 0.047 | 20.120 | 30.255 | 11 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 34/36 | 2 | 0.058 | 10.854 | 17.043 | 11 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 1.056 | 1.919 | 2.039 | 10 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 33/36 | 3 | 0.340 | 10.687 | 11.000 | 11 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 27/36 | 9 | 0.189 | 3.164 | 3.376 | 9 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.041 | 0.070 | 0.088 | 10 | o2_dense_sabre |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.612 | 1.307 | 1.831 | 10 | o2_default_default |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 0.900 | 2.057 | 2.423 | 10 | o2_sabre_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.048 | 2.804 | 3.022 | 12 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 39 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 1 | 39 | 40 |
| 60 | 0 | 39 | 39 |
| 100 | 0 | 39 | 39 |
| 120 | 0 | 39 | 39 |
| 300 | 0 | 39 | 39 |
| 600 | 0 | 39 | 39 |
| 900 | 0 | 39 | 39 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 106 |
| Non eleggibili | 14 |
| Esempi RAG | 6 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

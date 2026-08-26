# Pilot Qiskit — ibm_heron_133

Scheda generata automaticamente dagli artefatti del pilot. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 133 |
| Hash target | 804f28754ad200e42a328ba910639c9d6fd3233dff35035e7f3cb85a2fc5168a |
| Qiskit | 2.1.1 |
| MQT Bench | 2.0.0 |
| MQT Predictor | 2.3.0 |
| Circuiti totali | 10 |
| Circuiti compatibili | 10 |
| Circuiti incompatibili | 0 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker | 6 |
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 825.071 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 360 | - |
| Osservati | 360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 320 | 88.9% |
| Failure | 0 | 0.0% |
| Timeout | 40 | 11.1% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 320 | 0.012 | 0.202 | 2.262 | 12.320 | 35.222 |
| Non-lookahead | 291 | 0.012 | 0.204 | 1.989 | 9.187 | 35.222 |
| Lookahead | 29 | 0.017 | 0.137 | 5.002 | 21.017 | 23.636 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.041 | 1.250 | 1.811 | 10 | 7 | 7 | 8 |
| o3_default_default | baseline | 3 | default | default | 27/30 | 3 | 1.204 | 20.722 | 21.552 | 9 | 0 | 4 | 8 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.038 | 1.003 | 1.192 | 10 | 0 | 0 | 4 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.027 | 0.424 | 0.498 | 10 | 1 | 1 | 6 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.022 | 0.518 | 0.851 | 10 | 0 | 0 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 27/30 | 3 | 1.290 | 33.324 | 35.222 | 9 | 0 | 0 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.212 | 2.920 | 5.061 | 10 | 2 | 3 | 3 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 30/30 | 0 | 0.992 | 4.662 | 27.054 | 10 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 18/30 | 12 | 0.060 | 21.403 | 23.636 | 6 | 0 | 0 | 1 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.051 | 3.578 | 5.003 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 11/30 | 19 | 0.411 | 20.450 | 21.023 | 3 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 27/30 | 3 | 2.401 | 29.785 | 31.125 | 9 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.022 | 0.222 | 0.230 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 33/36 | 3 | 0.045 | 33.272 | 35.222 | 11 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 35/36 | 1 | 0.062 | 14.861 | 21.023 | 11 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 1.872 | 4.752 | 5.003 | 10 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.251 | 1.272 | 1.296 | 12 | o2_default_default |
| wstate_indep_tket_90 | train | 90 | 24/36 | 12 | 0.124 | 3.887 | 27.054 | 8 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.049 | 0.091 | 0.096 | 10 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.723 | 2.384 | 2.492 | 10 | o3_dense_sabre |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 1.979 | 8.176 | 12.300 | 10 | o3_dense_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.086 | 0.422 | 0.471 | 12 | o2_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 40 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 5 | 40 | 45 |
| 60 | 0 | 40 | 40 |
| 100 | 0 | 40 | 40 |
| 120 | 0 | 40 | 40 |
| 300 | 0 | 40 | 40 |
| 600 | 0 | 40 | 40 |
| 900 | 0 | 40 | 40 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 106 |
| Non eleggibili | 14 |
| Esempi RAG | 6 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

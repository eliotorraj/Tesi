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
| Worker | 2 |
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 2359.432 s |

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
| Tutti | 320 | 0.009 | 0.126 | 2.084 | 10.816 | 37.226 |
| Non-lookahead | 291 | 0.009 | 0.133 | 1.824 | 8.390 | 37.226 |
| Lookahead | 29 | 0.014 | 0.115 | 4.692 | 19.884 | 23.923 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.043 | 0.884 | 0.891 | 10 | 7 | 7 | 8 |
| o3_default_default | baseline | 3 | default | default | 27/30 | 3 | 1.200 | 17.428 | 19.689 | 9 | 0 | 4 | 8 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.037 | 0.849 | 0.880 | 10 | 0 | 0 | 4 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.026 | 0.328 | 0.380 | 10 | 1 | 1 | 6 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.018 | 0.413 | 0.537 | 10 | 0 | 0 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 27/30 | 3 | 1.156 | 33.574 | 37.226 | 9 | 0 | 0 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.139 | 2.523 | 4.100 | 10 | 2 | 3 | 3 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 30/30 | 0 | 0.833 | 3.969 | 26.318 | 10 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 18/30 | 12 | 0.065 | 21.393 | 23.923 | 6 | 0 | 0 | 1 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.060 | 1.888 | 2.181 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 11/30 | 19 | 0.353 | 18.290 | 18.291 | 3 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 27/30 | 3 | 2.010 | 32.791 | 34.196 | 9 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.019 | 0.071 | 0.185 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 33/36 | 3 | 0.057 | 34.228 | 37.226 | 11 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 35/36 | 1 | 0.053 | 13.579 | 18.291 | 11 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 1.424 | 3.403 | 4.289 | 10 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.194 | 1.208 | 1.289 | 12 | o2_default_default |
| wstate_indep_tket_90 | train | 90 | 24/36 | 12 | 0.108 | 3.495 | 26.318 | 8 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.050 | 0.083 | 0.099 | 10 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.721 | 2.148 | 2.278 | 10 | o3_dense_sabre |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 1.738 | 6.286 | 10.494 | 10 | o3_dense_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.053 | 0.344 | 0.363 | 12 | o2_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 40 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 6 | 40 | 46 |
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

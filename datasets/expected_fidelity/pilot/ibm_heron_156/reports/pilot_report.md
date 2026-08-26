# Pilot Qiskit — ibm_heron_156

Scheda generata automaticamente dagli artefatti del pilot. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 156 |
| Hash target | a30f41e65c03fb900a4b8852261a8407c56c389560f4031ecb43099c1bec5089 |
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
| Durata invocazione | 2693.291 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 360 | - |
| Osservati | 360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 317 | 88.1% |
| Failure | 0 | 0.0% |
| Timeout | 43 | 11.9% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 317 | 0.010 | 0.119 | 3.284 | 21.691 | 87.897 |
| Non-lookahead | 290 | 0.010 | 0.121 | 3.153 | 15.574 | 87.897 |
| Lookahead | 27 | 0.019 | 0.113 | 4.691 | 23.970 | 34.519 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.047 | 0.954 | 1.263 | 10 | 3 | 3 | 7 |
| o3_default_default | baseline | 3 | default | default | 27/30 | 3 | 1.948 | 25.604 | 33.924 | 9 | 5 | 6 | 8 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.045 | 0.926 | 0.974 | 10 | 1 | 1 | 4 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.025 | 0.273 | 0.316 | 10 | 1 | 1 | 4 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.021 | 0.327 | 0.331 | 10 | 0 | 0 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 27/30 | 3 | 1.946 | 54.188 | 87.897 | 9 | 0 | 0 | 1 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.110 | 2.180 | 2.416 | 10 | 0 | 1 | 5 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 29/30 | 1 | 0.815 | 35.088 | 50.687 | 9 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 18/30 | 12 | 0.080 | 26.011 | 34.519 | 6 | 0 | 0 | 1 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.060 | 1.848 | 2.005 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 9/30 | 21 | 0.271 | 1.355 | 1.443 | 3 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 27/30 | 3 | 1.637 | 50.300 | 77.606 | 9 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.025 | 0.085 | 0.213 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 33/36 | 3 | 0.076 | 65.025 | 87.897 | 11 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 33/36 | 3 | 0.045 | 12.844 | 14.369 | 11 | o3_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 1.585 | 3.532 | 4.516 | 10 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.065 | 1.429 | 1.577 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 23/36 | 13 | 0.107 | 32.228 | 50.687 | 7 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.055 | 0.113 | 0.174 | 10 | o2_dense_sabre |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.909 | 30.771 | 34.079 | 10 | o3_default_default |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 1.390 | 6.692 | 9.387 | 10 | o2_sabre_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.045 | 0.311 | 0.333 | 12 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 43 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 12 | 43 | 55 |
| 60 | 2 | 43 | 45 |
| 100 | 0 | 43 | 43 |
| 120 | 0 | 43 | 43 |
| 300 | 0 | 43 | 43 |
| 600 | 0 | 43 | 43 |
| 900 | 0 | 43 | 43 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 105 |
| Non eleggibili | 15 |
| Esempi RAG | 6 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

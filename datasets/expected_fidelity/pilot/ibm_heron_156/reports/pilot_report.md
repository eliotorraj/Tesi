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
| Worker | 6 |
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 915.526 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 360 | - |
| Osservati | 360 | 100.0% |
| Mancanti | 0 | - |
| Successi | 318 | 88.3% |
| Failure | 0 | 0.0% |
| Timeout | 42 | 11.7% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 318 | 0.012 | 0.212 | 3.678 | 24.092 | 95.108 |
| Non-lookahead | 291 | 0.012 | 0.221 | 3.523 | 21.083 | 95.108 |
| Lookahead | 27 | 0.020 | 0.095 | 5.350 | 25.181 | 38.652 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 30/30 | 0 | 0.055 | 1.086 | 1.597 | 10 | 3 | 3 | 7 |
| o3_default_default | baseline | 3 | default | default | 27/30 | 3 | 2.443 | 26.984 | 37.065 | 9 | 5 | 6 | 8 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 30/30 | 0 | 0.043 | 0.997 | 1.182 | 10 | 1 | 1 | 4 |
| o2_dense_sabre | layout | 2 | dense | sabre | 30/30 | 0 | 0.087 | 0.472 | 0.549 | 10 | 1 | 1 | 4 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 30/30 | 0 | 0.027 | 0.463 | 0.515 | 10 | 0 | 0 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 27/30 | 3 | 2.671 | 54.776 | 78.386 | 9 | 0 | 0 | 1 |
| o3_dense_sabre | layout | 3 | dense | sabre | 30/30 | 0 | 0.097 | 2.592 | 2.646 | 10 | 0 | 1 | 5 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 30/30 | 0 | 1.256 | 44.654 | 95.108 | 10 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 18/30 | 12 | 0.072 | 27.695 | 38.652 | 6 | 0 | 0 | 1 |
| o2_sabre_basic | routing | 2 | sabre | basic | 30/30 | 0 | 0.082 | 2.445 | 2.653 | 10 | 0 | 0 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 9/30 | 21 | 0.486 | 1.649 | 1.652 | 3 | 0 | 0 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 27/30 | 3 | 2.190 | 41.674 | 68.807 | 9 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.027 | 0.237 | 0.244 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 33/36 | 3 | 0.077 | 61.698 | 78.386 | 11 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 33/36 | 3 | 0.059 | 16.002 | 16.898 | 11 | o3_default_default |
| random_indep_qiskit_30 | train | 30 | 30/36 | 6 | 1.691 | 5.799 | 7.002 | 10 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.086 | 2.145 | 2.294 | 12 | o3_default_default |
| wstate_indep_tket_90 | train | 90 | 24/36 | 12 | 0.102 | 48.772 | 95.108 | 8 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 30/36 | 6 | 0.069 | 0.122 | 0.296 | 10 | o2_dense_sabre |
| qft_indep_tket_40 | validation | 40 | 30/36 | 6 | 0.877 | 31.279 | 34.039 | 10 | o3_default_default |
| qpeexact_indep_tket_60 | test | 60 | 30/36 | 6 | 1.647 | 8.420 | 10.419 | 10 | o2_sabre_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.056 | 0.476 | 0.487 | 12 | o3_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 42 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 13 | 42 | 55 |
| 60 | 3 | 42 | 45 |
| 100 | 0 | 42 | 42 |
| 120 | 0 | 42 | 42 |
| 300 | 0 | 42 | 42 |
| 600 | 0 | 42 | 42 |
| 900 | 0 | 42 | 42 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 106 |
| Non eleggibili | 14 |
| Esempi RAG | 6 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

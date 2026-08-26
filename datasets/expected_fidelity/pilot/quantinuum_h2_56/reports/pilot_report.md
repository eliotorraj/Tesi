# Pilot Qiskit — quantinuum_h2_56

Scheda generata automaticamente dagli artefatti del pilot. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 56 |
| Hash target | 8c5576ac2f280a98f797dceb53186f97500e901d9784cc328187e156cbbe9b8f |
| Qiskit | 2.1.1 |
| MQT Bench | 2.0.0 |
| MQT Predictor | 2.3.0 |
| Circuiti totali | 10 |
| Circuiti compatibili | 8 |
| Circuiti incompatibili | 2 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker | 6 |
| Timeout richiesto | 200.000 s |
| Cache hit | 177 |
| Durata invocazione | 3713.820 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 288 | - |
| Osservati | 288 | 100.0% |
| Mancanti | 0 | - |
| Successi | 183 | 63.5% |
| Failure | 0 | 0.0% |
| Timeout | 105 | 36.5% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 183 | 0.020 | 0.050 | 6.296 | 18.556 | 155.959 |
| Non-lookahead | 156 | 0.020 | 0.053 | 7.364 | 20.547 | 155.959 |
| Lookahead | 27 | 0.024 | 0.041 | 0.126 | 0.368 | 0.656 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 24/24 | 0 | 0.043 | 0.367 | 0.430 | 8 | 6 | 6 | 6 |
| o3_default_default | baseline | 3 | default | default | 24/24 | 0 | 17.477 | 151.571 | 155.959 | 8 | 0 | 6 | 6 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 24/24 | 0 | 0.044 | 0.355 | 0.367 | 8 | 0 | 6 | 8 |
| o2_dense_sabre | layout | 2 | dense | sabre | 24/24 | 0 | 0.043 | 0.335 | 0.387 | 8 | 2 | 8 | 2 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 24/24 | 0 | 0.032 | 0.339 | 0.348 | 8 | 0 | 5 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 3/24 | 21 | 0.076 | 0.088 | 0.090 | 1 | 0 | 1 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 3/24 | 21 | 0.083 | 0.094 | 0.096 | 1 | 0 | 1 | 0 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 3/24 | 21 | 0.073 | 0.083 | 0.084 | 1 | 0 | 1 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 24/24 | 0 | 0.039 | 0.370 | 0.656 | 8 | 0 | 6 | 2 |
| o2_sabre_basic | routing | 2 | sabre | basic | 24/24 | 0 | 0.038 | 0.357 | 0.360 | 8 | 0 | 6 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 3/24 | 21 | 0.108 | 0.110 | 0.111 | 1 | 0 | 1 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 3/24 | 21 | 0.104 | 0.123 | 0.125 | 1 | 0 | 1 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.064 | 0.109 | 0.125 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 21/36 | 15 | 0.028 | 20.895 | 21.066 | 7 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 21/36 | 15 | 0.039 | 11.957 | 11.973 | 7 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 21/36 | 15 | 0.289 | 151.590 | 155.959 | 7 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 21/36 | 15 | 0.033 | 17.460 | 18.669 | 7 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 21/36 | 15 | 0.053 | 12.170 | 12.220 | 7 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 21/36 | 15 | 0.360 | 145.350 | 146.242 | 7 | o2_dense_sabre |
| routing_indep_qiskit_12 | test | 12 | 21/36 | 15 | 0.038 | 17.494 | 17.542 | 7 | o2_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 105 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 6 | 105 | 111 |
| 60 | 6 | 105 | 111 |
| 100 | 6 | 105 | 111 |
| 120 | 6 | 105 | 111 |
| 300 | 0 | 105 | 105 |
| 600 | 0 | 105 | 105 |
| 900 | 0 | 105 | 105 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 61 |
| Non eleggibili | 35 |
| Esempi RAG | 5 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

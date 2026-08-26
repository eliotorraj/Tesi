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
| Worker | 2 |
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 5707.835 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 288 | - |
| Osservati | 288 | 100.0% |
| Mancanti | 0 | - |
| Successi | 177 | 61.5% |
| Failure | 0 | 0.0% |
| Timeout | 111 | 38.5% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 177 | 0.018 | 0.037 | 1.154 | 9.574 | 20.529 |
| Non-lookahead | 150 | 0.018 | 0.039 | 1.345 | 9.761 | 20.529 |
| Lookahead | 27 | 0.022 | 0.034 | 0.095 | 0.313 | 0.424 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 24/24 | 0 | 0.040 | 0.312 | 0.335 | 8 | 6 | 6 | 6 |
| o3_default_default | baseline | 3 | default | default | 18/24 | 6 | 9.594 | 20.411 | 20.529 | 6 | 0 | 6 | 6 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 24/24 | 0 | 0.035 | 0.335 | 0.351 | 8 | 0 | 6 | 8 |
| o2_dense_sabre | layout | 2 | dense | sabre | 24/24 | 0 | 0.037 | 0.266 | 0.476 | 8 | 2 | 8 | 2 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 24/24 | 0 | 0.027 | 0.271 | 0.293 | 8 | 0 | 5 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 3/24 | 21 | 0.106 | 0.110 | 0.110 | 1 | 0 | 1 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 3/24 | 21 | 0.102 | 0.104 | 0.104 | 1 | 0 | 1 | 0 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 3/24 | 21 | 0.091 | 0.092 | 0.092 | 1 | 0 | 1 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 24/24 | 0 | 0.034 | 0.320 | 0.424 | 8 | 0 | 6 | 2 |
| o2_sabre_basic | routing | 2 | sabre | basic | 24/24 | 0 | 0.034 | 0.277 | 0.472 | 8 | 0 | 6 | 0 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 3/24 | 21 | 0.097 | 0.101 | 0.101 | 1 | 0 | 1 | 0 |
| o3_sabre_basic | routing | 3 | sabre | basic | 3/24 | 21 | 0.107 | 0.109 | 0.109 | 1 | 0 | 1 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.070 | 0.107 | 0.110 | 12 | o2_default_default |
| graphstate_indep_qiskit_14 | train | 14 | 21/36 | 15 | 0.037 | 20.390 | 20.529 | 7 | o2_default_default |
| qaoa_indep_tket_7 | train | 7 | 21/36 | 15 | 0.034 | 9.869 | 10.158 | 7 | o2_default_default |
| random_indep_qiskit_30 | train | 30 | 18/36 | 18 | 0.289 | 0.431 | 0.472 | 6 | o2_dense_sabre |
| vqe_indep_tket_16 | train | 16 | 21/36 | 15 | 0.028 | 16.858 | 17.126 | 7 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 21/36 | 15 | 0.029 | 6.480 | 6.786 | 7 | o2_default_default |
| qft_indep_tket_40 | validation | 40 | 18/36 | 18 | 0.253 | 0.306 | 0.476 | 6 | o2_dense_sabre |
| routing_indep_qiskit_12 | test | 12 | 21/36 | 15 | 0.024 | 9.526 | 9.560 | 7 | o2_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 111 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 0 | 111 | 111 |
| 60 | 0 | 111 | 111 |
| 100 | 0 | 111 | 111 |
| 120 | 0 | 111 | 111 |
| 300 | 0 | 111 | 111 |
| 600 | 0 | 111 | 111 |
| 900 | 0 | 111 | 111 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 59 |
| Non eleggibili | 37 |
| Esempi RAG | 5 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

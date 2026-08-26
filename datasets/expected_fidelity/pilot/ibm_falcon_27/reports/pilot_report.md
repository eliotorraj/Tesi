# Pilot Qiskit — ibm_falcon_27

Scheda generata automaticamente dagli artefatti del pilot. I tempi descrivono soltanto i tentativi riusciti e sono censurati dai timeout.

## Impostazione

| Campo | Valore |
| --- | --- |
| Figure of merit | expected_fidelity |
| Qubit device | 27 |
| Hash target | f30536987677ef5017fe3a89b8b4ee0a3e7252a1a226cc3db95fd9b2e822d991 |
| Qiskit | 2.1.1 |
| MQT Bench | 2.0.0 |
| MQT Predictor | 2.3.0 |
| Circuiti totali | 10 |
| Circuiti compatibili | 6 |
| Circuiti incompatibili | 4 |
| Configurazioni | 12 |
| Seed | 0, 1, 2 |
| Worker | 2 |
| Timeout richiesto | 100.000 s |
| Cache hit | 0 |
| Durata invocazione | 215.981 s |

La durata invocazione riguarda il comando corrente. Se Cache hit è maggiore di zero, i record conservano i tempi delle esecuzioni originali e non sono stati ricompilati.

## Esito complessivo

| Tentativi | N | Percentuale su osservati |
| --- | --- | --- |
| Pianificati | 216 | - |
| Osservati | 216 | 100.0% |
| Mancanti | 0 | - |
| Successi | 214 | 99.1% |
| Failure | 0 | 0.0% |
| Timeout | 2 | 0.9% |

## Tempi di transpilation dei successi

| Gruppo | N | Min s | Mediana s | Media s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- |
| Tutti | 214 | 0.007 | 0.018 | 0.806 | 4.124 | 28.908 |
| Non-lookahead | 180 | 0.007 | 0.016 | 0.027 | 0.125 | 0.287 |
| Lookahead | 34 | 0.008 | 3.192 | 4.932 | 21.084 | 28.908 |

I timeout non hanno un tempo di transpilation concluso e non entrano nella tabella: il timeout rate va sempre letto insieme ai tempi.

## Configurazioni

| Config | Studio | O | Layout | Routing | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Eleggibili | Vittorie | Co-vittorie | Top 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| o2_default_default | baseline | 2 | default | default | 18/18 | 0 | 0.012 | 0.022 | 0.022 | 6 | 3 | 3 | 6 |
| o3_default_default | baseline | 3 | default | default | 18/18 | 0 | 0.025 | 0.152 | 0.192 | 6 | 1 | 4 | 4 |
| o2_sabre_sabre | layout | 2 | sabre | sabre | 18/18 | 0 | 0.012 | 0.021 | 0.022 | 6 | 0 | 0 | 2 |
| o2_dense_sabre | layout | 2 | dense | sabre | 18/18 | 0 | 0.012 | 0.016 | 0.017 | 6 | 2 | 2 | 2 |
| o2_trivial_sabre | layout | 2 | trivial | sabre | 18/18 | 0 | 0.010 | 0.039 | 0.161 | 6 | 0 | 0 | 0 |
| o3_sabre_sabre | layout | 3 | sabre | sabre | 18/18 | 0 | 0.029 | 0.168 | 0.287 | 6 | 0 | 0 | 0 |
| o3_dense_sabre | layout | 3 | dense | sabre | 18/18 | 0 | 0.018 | 0.030 | 0.030 | 6 | 0 | 2 | 2 |
| o3_trivial_sabre | layout | 3 | trivial | sabre | 18/18 | 0 | 0.017 | 0.039 | 0.040 | 6 | 0 | 0 | 0 |
| o2_sabre_lookahead | routing | 2 | sabre | lookahead | 17/18 | 1 | 2.825 | 17.848 | 25.150 | 5 | 0 | 0 | 0 |
| o2_sabre_basic | routing | 2 | sabre | basic | 18/18 | 0 | 0.015 | 0.030 | 0.033 | 6 | 0 | 0 | 1 |
| o3_sabre_lookahead | routing | 3 | sabre | lookahead | 17/18 | 1 | 3.569 | 20.898 | 28.908 | 5 | 0 | 0 | 1 |
| o3_sabre_basic | routing | 3 | sabre | basic | 18/18 | 0 | 0.035 | 0.128 | 0.144 | 6 | 0 | 0 | 0 |

Le vittorie applicano il tie-break del catalogo; le co-vittorie considerano score uguali con rel_tol=1e-12 e abs_tol=1e-15.

## Circuiti

| Circuito | Split | Qubit | Ok/Obs | Timeout | Mediana s | P95 s | Max s | Config eleggibili | Migliore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ae_indep_qiskit_2 | train | 2 | 36/36 | 0 | 0.009 | 0.015 | 0.022 | 12 | o2_dense_sabre |
| graphstate_indep_qiskit_14 | train | 14 | 36/36 | 0 | 0.014 | 3.578 | 3.902 | 12 | o3_default_default |
| qaoa_indep_tket_7 | train | 7 | 36/36 | 0 | 0.019 | 2.289 | 6.920 | 12 | o2_default_default |
| vqe_indep_tket_16 | train | 16 | 36/36 | 0 | 0.020 | 4.732 | 7.117 | 12 | o2_default_default |
| pricingcall_indep_qiskit_5 | validation | 5 | 34/36 | 2 | 0.022 | 21.084 | 28.908 | 10 | o2_dense_sabre |
| routing_indep_qiskit_12 | test | 12 | 36/36 | 0 | 0.023 | 1.420 | 5.762 | 12 | o2_default_default |

## Failure e timeout

| Fase | Categoria | Eccezione | N |
| --- | --- | --- | --- |
| transpilation | timeout | AttemptTimeoutError | 2 |

## Sensibilità a soglie alternative

| Soglia s | Successi sopra soglia | Timeout già osservati | Lower bound timeout |
| --- | --- | --- | --- |
| 30 | 0 | 2 | 2 |
| 60 | 0 | 2 | 2 |
| 100 | 0 | 2 | 2 |
| 120 | 0 | 2 | 2 |
| 300 | 0 | 2 | 2 |
| 600 | 0 | 2 | 2 |
| 900 | 0 | 2 | 2 |

La stima è conservativa: un run già interrotto è censurato e non rivela se sarebbe terminato con una soglia più alta.

## Copertura ranking

| Aggregati | N |
| --- | --- |
| Eleggibili | 70 |
| Non eleggibili | 2 |
| Esempi RAG | 4 |

La expected_fidelity è una stima deterministica sul Target sintetico di MQT Bench, non una misura raccolta su hardware quantistico reale.

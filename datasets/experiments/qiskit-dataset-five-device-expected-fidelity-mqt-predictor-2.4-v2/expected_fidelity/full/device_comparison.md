# Confronto Dataset Qiskit full per dispositivo

La prima tabella usa tutti i circuiti compatibili con ciascun device. La seconda usa soltanto l'intersezione comune di 410 circuiti.

## Tutti i circuiti compatibili

| Device | Qubit | Worker | Timeout s | Circuiti | Ok/Obs | Timeout | Successo | Mediana s | P95 s | Max s | Aggregati eleggibili |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 127 | 6 | 100 | 510 | 16902/18360 | 1458 | 92.1% | 0.019 | 12.585 | 98.948 | 5587 |
| ibm_falcon_27 | 27 | 6 | 100 | 410 | 14278/14760 | 482 | 96.7% | 0.013 | 5.389 | 96.334 | 4705 |
| ibm_heron_133 | 133 | 6 | 100 | 510 | 17108/18360 | 1252 | 93.2% | 0.020 | 12.290 | 99.835 | 5667 |
| ibm_heron_156 | 156 | 6 | 100 | 510 | 17053/18360 | 1307 | 92.9% | 0.021 | 12.986 | 103.356 | 5641 |
| quantinuum_h2_56 | 56 | 6 | 100 | 480 | 17280/17280 | 0 | 100.0% | 0.025 | 2.881 | 35.084 | 5760 |

## Sottoinsieme comune

| Device | Circuiti | Ok/Obs | Failure | Timeout | Successo | Mediana s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 410 | 13860/14760 | 0 | 900 | 93.9% | 0.018 | 14.926 | 98.948 |
| ibm_falcon_27 | 410 | 14278/14760 | 0 | 482 | 96.7% | 0.013 | 5.389 | 96.334 |
| ibm_heron_133 | 410 | 13952/14760 | 0 | 808 | 94.5% | 0.018 | 14.937 | 99.835 |
| ibm_heron_156 | 410 | 13905/14760 | 0 | 855 | 94.2% | 0.019 | 16.589 | 103.356 |
| quantinuum_h2_56 | 410 | 14760/14760 | 0 | 0 | 100.0% | 0.024 | 2.917 | 29.515 |

Per tempi confrontabili, usare lo stesso timeout e numero di worker ed evitare altre compilazioni concorrenti. Con soglie diverse (per esempio 300 s e 100 s), anche sul sottoinsieme comune i tempi e i tassi di successo non sono un confronto a parità di condizioni.

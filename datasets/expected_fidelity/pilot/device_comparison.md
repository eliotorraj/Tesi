# Confronto pilot per device

La prima tabella usa tutti i circuiti compatibili con ciascun device. La seconda usa soltanto l'intersezione comune di 6 circuiti.

## Tutti i circuiti compatibili

| Device | Qubit | Worker | Timeout s | Circuiti | Ok/Obs | Timeout | Successo | Mediana s | P95 s | Max s | Aggregati eleggibili |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 127 | 2 | 100.000 | 10 | 321/360 | 39 | 89.2% | 0.153 | 10.198 | 30.255 | 106 |
| ibm_falcon_27 | 27 | 2 | 100.000 | 6 | 214/216 | 2 | 99.1% | 0.018 | 4.124 | 28.908 | 70 |
| ibm_heron_133 | 133 | 2 | 100.000 | 10 | 320/360 | 40 | 88.9% | 0.126 | 10.816 | 37.226 | 106 |
| ibm_heron_156 | 156 | 2 | 100.000 | 10 | 317/360 | 43 | 88.1% | 0.119 | 21.691 | 87.897 | 105 |
| quantinuum_h2_56 | 56 | 2 | 100.000 | 8 | 177/288 | 111 | 61.5% | 0.037 | 9.574 | 20.529 | 59 |

## Sottoinsieme comune

| Device | Circuiti | Ok/Obs | Failure | Timeout | Successo | Mediana s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 6 | 204/216 | 0 | 12 | 94.4% | 0.039 | 11.276 | 30.255 |
| ibm_falcon_27 | 6 | 214/216 | 0 | 2 | 99.1% | 0.018 | 4.124 | 28.908 |
| ibm_heron_133 | 6 | 206/216 | 0 | 10 | 95.4% | 0.038 | 18.078 | 37.226 |
| ibm_heron_156 | 6 | 204/216 | 0 | 12 | 94.4% | 0.044 | 20.911 | 87.897 |
| quantinuum_h2_56 | 6 | 141/216 | 0 | 75 | 65.3% | 0.034 | 9.869 | 20.529 |

Per tempi confrontabili, usare lo stesso timeout e numero di worker ed eseguire i pilot senza altri pilot concorrenti.

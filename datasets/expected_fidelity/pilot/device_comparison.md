# Confronto pilot per device

La prima tabella usa tutti i circuiti compatibili con ciascun device. La seconda usa soltanto l'intersezione comune di 6 circuiti.

## Tutti i circuiti compatibili

| Device | Qubit | Worker | Timeout s | Circuiti | Ok/Obs | Timeout | Successo | Mediana s | P95 s | Max s | Aggregati eleggibili |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 127 | 2 | 900.000 | 10 | 335/360 | 25 | 93.1% | 0.139 | 12.494 | 538.369 | 110 |
| ibm_falcon_27 | 27 | 6 | 100.000 | 6 | 216/216 | 0 | 100.0% | 0.021 | 5.686 | 80.908 | 72 |
| ibm_heron_133 | 133 | 6 | 100.000 | 10 | 320/360 | 40 | 88.9% | 0.202 | 12.320 | 35.222 | 106 |
| ibm_heron_156 | 156 | 6 | 100.000 | 10 | 318/360 | 42 | 88.3% | 0.212 | 24.092 | 95.108 | 106 |
| quantinuum_h2_56 | 56 | 6 | 200.000 | 8 | 183/288 | 105 | 63.5% | 0.050 | 18.556 | 155.959 | 61 |

## Sottoinsieme comune

| Device | Circuiti | Ok/Obs | Failure | Timeout | Successo | Mediana s | P95 s | Max s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm_falcon_127 | 6 | 209/216 | 0 | 7 | 96.8% | 0.028 | 10.770 | 105.444 |
| ibm_falcon_27 | 6 | 216/216 | 0 | 0 | 100.0% | 0.021 | 5.686 | 80.908 |
| ibm_heron_133 | 6 | 206/216 | 0 | 10 | 95.4% | 0.041 | 20.748 | 35.222 |
| ibm_heron_156 | 6 | 204/216 | 0 | 12 | 94.4% | 0.056 | 21.305 | 78.386 |
| quantinuum_h2_56 | 6 | 141/216 | 0 | 75 | 65.3% | 0.039 | 17.361 | 21.066 |

Per tempi confrontabili, usare lo stesso timeout e numero di worker ed eseguire i pilot senza altri pilot concorrenti.

# Sorgenti operativi

[Indice dell’esperimento](../README.md)

Questa cartella offre agli strumenti le copie dei circuiti già assegnati
a una partizione:

| Gruppo | Funzione |
| --- | --- |
| `train/*.qasm` | I 422 circuiti per costruire i dati di apprendimento e svolgere le prove tecniche ammesse. |
| `validation/*.qasm` | Gli 88 circuiti riservati alla scelta della configurazione sperimentale. |

Ogni QASM descrive un circuito ancora indipendente dal dispositivo finale.
Nomi e contenuti vengono confrontati con il [manifest](../manifests/README.md).

Il corpus originale resta nell’archivio. Non si spostano circuiti tra
partizioni per facilitare una prova. Il test viene predisposto soltanto
secondo la procedura di apertura prevista dal protocollo.

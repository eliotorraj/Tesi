# Piani del confronto

[Indice dell’esperimento](../README.md)

I piani fissano il lavoro previsto prima di osservare gli esiti.
Servono anche a ritrovare le stesse scelte dopo una ripresa.

| File o gruppo | Funzione |
| --- | --- |
| `validation_method_plan.json` | Piano riferito agli 88 circuiti validation. |
| `test_method_plan.json` | Piano riferito ai 90 circuiti test, ancora soggetto alla procedura di apertura. |
| `history/*.json` | Copie dei piani precedenti, conservate quando sono state riallineate le condizioni operative. |
| `history/*.alignment.json` | Traccia del riallineamento e delle impronte coinvolte. |

I piani registrano dispositivi, configurazioni, seed Qiskit, ripetizioni
qcompile, condizioni di esecuzione e scelte casuali già estratte.
La presenza di un piano non significa che sia stato eseguito.

La selezione locale dei modelli LLM ha un ambito proprio, definito dal
[protocollo](../../../../docs/protocollo_sperimentale.md).
Il piano storico del confronto finale non impone di eseguire tutti i metodi
durante quella selezione.

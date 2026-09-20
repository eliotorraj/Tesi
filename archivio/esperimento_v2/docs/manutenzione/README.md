# Manutenzione del repository

Questa cartella documenta interventi su Git, conservazione e trasferimento dei
file. Non contiene prove di qualità dei modelli.

| Cartella | Contenuto |
| --- | --- |
| [rimozione_lfs_2026-09-15/](rimozione_lfs_2026-09-15/README.md) | Rimozione di Git LFS dalla cronologia e istruzioni per trasferire separatamente i dati pesanti. |

Dentro l'intervento del 15 settembre:

| File | Funzione |
| --- | --- |
| `README.md` | Motivo, operazioni, controlli e trasferimento sull'altro computer. |
| `oggetti_lfs.json` | Inventario degli oggetti LFS. |
| `percorsi_esclusi.txt` | Percorsi rimossi dalla cronologia. |
| `verifica_cronologia.json` | Risultati dei controlli sulla cronologia riscritta. |
| `richiesta_supporto.md` | Testo predisposto per il supporto GitHub; la presenza del file non implica l'invio. |

Il solo clone del repository non ricostruisce i dati e i modelli esterni.

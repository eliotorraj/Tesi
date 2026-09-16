# Archivio del progetto

Qui conserviamo le fasi precedenti, per ricostruire le scelte e confrontare
il lavoro svolto. Per eseguire l'esperimento attuale usare il
[README principale](../README.md) e il [protocollo corrente](../docs/protocollo_sperimentale.md).

| Cartella | Funzione |
| --- | --- |
| [protocollo_v1/](protocollo_v1/README.md) | Dati, configurazioni e cache delle prime prove. |
| [documentazione/](documentazione/README.md) | Copie dei documenti sostituiti dal protocollo unico. |
| [resoconti/](resoconti/README.md) | Relazioni periodiche preparate per la tesi. |
| [sviluppo/](sviluppo/README.md) | Diagnosi, copie intermedie e salvataggi locali; esclusi da Git. |

## Il corpus originale serve ancora

I 600 QASM e `protocollo_v1/datasets/expected_fidelity/full/split_manifest.json`
sono la fonte originale del corpus. Il codice v2 verifica le loro impronte e
prepara le copie ammesse di train e validation. Non riusa gli score storici.

I vecchi nomi dei percorsi nei manifest sono riferimenti logici, risolti dal
codice. Non vanno riscritti. La presenza dei sorgenti test nell'archivio non
ne autorizza l'uso prima dell'apertura del test.

## Come leggere i documenti storici

Versioni, comandi, conteggi dei test e frasi come “da fare” descrivono il periodo
di scrittura. Non rappresentano automaticamente lo stato attuale.
Il precedente README dell'archivio è conservato nel
[resoconto del riordino del 9 settembre](../docs/resoconti/2026-09-09_riordino_archivio.md).

Il corpus e parte dei risultati sono in Git; i materiali locali o pesanti
possono richiedere un trasferimento separato. Consultare la
[guida di manutenzione](../docs/manutenzione/rimozione_lfs_2026-09-15/README.md).

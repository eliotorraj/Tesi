> Resoconto storico del riordino del 9 settembre, conservato dal precedente README dell’archivio.
> Gli stati descritti si riferiscono a quella data.

# Archivio del progetto

Questa cartella raccoglie il materiale storico separato il 9 settembre 2026.
Per il lavoro attuale usare il [protocollo unico](../protocollo_sperimentale.md)
e il [README del progetto](../../README.md). I documenti qui conservati possono
contenere percorsi e istruzioni non più attuali.

| Cartella | Contenuto |
| --- | --- |
| `protocollo_v1/datasets/expected_fidelity/` | Pilota, vecchi risultati full e corpus originale. |
| `protocollo_v1/artifacts/qiskit_dataset_cache/` | Cache Qiskit precedente alla separazione dell’esperimento attuale. |
| `protocollo_v1/configs/` | Catalogo della versione precedente. |
| `documentazione/20260909/` | Copie dei protocolli, della procedura, della verifica pre-Qdrant e del vecchio README. |
| `sviluppo/diagnostics/` | Diagnosi e verifiche delle interruzioni di training. |
| `sviluppo/snapshots/` | Copie dei risultati con impostazioni precedenti. |
| `sviluppo/runtime_policy_changes/` | Copie delle precedenti politiche di esecuzione. |
| `sviluppo/backups/` | Copie di sicurezza e verifiche di sincronizzazione. |
| `resoconti/` | Documenti periodici sullo stato della tesi. |

## Il corpus originale serve ancora

I 600 QASM e `full/split_manifest.json` sotto `protocollo_v1/datasets/expected_fidelity/`
sono la fonte congelata del corpus attuale. Il codice li usa per verificare gli
hash e preparare le copie consentite di train e validation. Non usa i punteggi
storici. Questa cartella va conservata anche nelle nuove installazioni.

I nomi dei percorsi dentro i manifest congelati non sono stati riscritti.
Il codice li risolve qui, conservando le impronte di corpus, piani e modelli.
Il test mantiene le protezioni dell’esperimento attuale. La presenza dei
sorgenti originali non ne autorizza la compilazione o l’inclusione nel RAG.

## Conservazione e sincronizzazione

Gli spostamenti non hanno eliminato file. Le impronte di tutti i file spostati
sono state confrontate prima e dopo. Il registro locale `riordino_20260909.json`
conserva vecchi e nuovi percorsi e le impronte dei file attuali controllati.
Le copie dei documenti conservano il testo originale, inclusi i vecchi percorsi.

Il corpus e il materiale già versionato, compresa la vecchia cache Qiskit,
restano destinati a Git nei nuovi percorsi. Le diagnosi locali, le copie di
sicurezza e il registro del riordino sono esclusi da Git. Sull’altro computer quei materiali vanno spostati o trasferiti
separatamente; un aggiornamento del codice non li sincronizza.

Gli script Qiskit usano ora il catalogo v2 e `full` come valori predefiniti.
Per consultare i risultati del pilota con gli strumenti di aggregazione occorre
indicare esplicitamente `--scope pilot` e
`--catalog archivio/protocollo_v1/configs/qiskit_dataset_configurations.json`.
Le vecchie compilazioni richiedono il loro ambiente originale e non vanno
mescolate con l’esperimento attuale.

## Verifica del riordino

Sono passati 154 test automatici. I 585 file attivi controllati, compresi
risultati, configurazioni e piani, sono rimasti identici. Il manifest v2 si
ricostruisce con la stessa impronta anche leggendo i sorgenti dall’archivio.
L’aggregazione conferma 87120 tentativi e 396 esempi RAG del solo train.

Il test resta chiuso. I controlli ancora in attesa sono gli stessi di prima:
configurazione dei modelli LLM, modelli finali MQT, verifica di qcompile e
valutazione finale sulla validation. Il riordino non ha aggiunto Qdrant.

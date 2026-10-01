# Archivio del progetto

Questa cartella conserva gli esperimenti, lo sviluppo e le decisioni che hanno portato al framework. I sorgenti conservati documentano le condizioni di quelle prove. Per una nuova esecuzione usare [riproducibilita/](../riproducibilita/README.md). Non è necessaria al normale utilizzo di `prototipo/`.

| Cartella | Contenuto |
| --- | --- |
| [esperimento_v2/](esperimento_v2/README.md) | Ambiente congelato, corpus, Dataset, Training set, validation, articoli e documentazione storica. |
| [valutazione/](valutazione/README.md) | Campagne Test, prove, addestramento MQT e verifiche precedenti, con sorgenti e risultati. |
| [riorganizzazione_2026_09_20/](riorganizzazione_2026_09_20/README.md) | Primo riordino: inventari, controlli e stato della consegna. |
| [riorganizzazione_2026_09_21/](riorganizzazione_2026_09_21/README.md) | Revisione degli script e verifiche successive. |
| [riorganizzazione_2026_09_25/](riorganizzazione_2026_09_25/README.md) | Separazione del framework dagli esperimenti e verifiche dei nuovi percorsi. |
| `workspace_locale/` | Copie locali precedenti, già raccolte in `.workspace_archive/`; contenuti esclusi da Git. |

## Struttura dell'esperimento congelato

In `esperimento_v2/`, `datasets/` contiene i Dataset e `artifacts/` gli esiti e i modelli. `knowledge/` raccoglie le fonti; `docs/` spiega le decisioni storiche. Le cartelle `prototype/`, `qiskit_dataset/`, `llm_selection/`, `scripts/` e `tests/` conservano il codice originale. L'ulteriore cartella `archivio/` interna custodisce il protocollo v1 e il corpus originale.

Questa struttura resta invariata: i manifest hanno riferimenti logici usati dai controlli di provenienza. Non spostare singoli file congelati e non sostituire punteggi o tentativi sfavorevoli.

## Quale documentazione usare

Il [protocollo corrente](../prototipo/docs/protocollo_sperimentale.md) è l'unica guida alle regole attuali. Le copie interne all'archivio descrivono il loro momento storico. Per usare il framework partire invece dalla [guida del prototipo](../prototipo/docs/guida_passo_passo.md).

Gli avviatori storici mantengono i riferimenti della loro epoca. I nuovi strumenti in `riproducibilita/` hanno ingressi e moduli propri. I vecchi contratti e registri restano immutati; un codice modificato non autorizza una ripresa che mescoli condizioni diverse.

I file esclusi da Git restano conservati sul computer. Per trasferire gli esperimenti occorre copiare separatamente dati, modelli e registri; un clone Git contiene soltanto ciò che è versionato.

Il [riordino del 1 ottobre](riorganizzazione_2026_10_01/README.md) separa riproduzione e storia. Le copie congelate attestano quale codice accompagnava gli esperimenti precedenti, anche quando esiste un modulo riutilizzabile nella nuova area.

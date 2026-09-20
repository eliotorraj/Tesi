# Come è nato il progetto

Questa cartella conserva il lavoro svolto, compresi tentativi falliti,
versioni superate e risultati originali. Il prototipo da provare è in
[prototipo/](../prototipo/README.md); il protocollo corrente è nella sua
[documentazione](../prototipo/docs/protocollo_sperimentale.md).

## Percorso di lettura

| Fase | Dove leggere | Che cosa trovi |
| --- | --- | --- |
| 1. Studio iniziale | [Fonti](esperimento_v2/knowledge/README.md) e [cronologia](esperimento_v2/docs/resoconti/cronologia_progetto_fino_al_9_settembre_2026.md) | Articoli, concetti e decisioni iniziali. |
| 2. Prime versioni | [Archivio precedente](esperimento_v2/archivio/README.md) | MQT 2.3.0, protocollo v1 e primi prototipi. Il corpus originale serve ancora alla provenienza. |
| 3. Esperimento MQT 2.4.0 | [Configurazioni](esperimento_v2/configs/README.md), [Dataset](esperimento_v2/datasets/README.md), [artefatti](esperimento_v2/artifacts/README.md) | Corpus, partizioni, matrice Qiskit, Training set e modelli. |
| 4. Costruzione del prototipo | [Prototipo originale](esperimento_v2/prototype/README.md) e [approfondimenti](esperimento_v2/docs/approfondimenti/README.md) | RAG, contratti, architettura e revisioni del prompt. |
| 5. Prima selezione locale | [Selezione storica](esperimento_v2/llm_selection/README.md) | Prove tecniche, local-llm-v1 e vincitore storico t=0,7. |
| 6. Validation ufficiale v2 | [Regole e comandi](esperimento_v2/llm_selection/v2/README.md) | local-llm-v2, Qwen t=0, rapporti e sigilli. |
| 7. Riordino attuale | [Riordino del 20 settembre](riorganizzazione_2026_09_20/README.md) | Mappa dei trasferimenti, controlli di integrità e revisione degli script. |

Gli studi e i rapporti delle fasi 5 e 6 sono in
`esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/studies/`.
Aprire `local-llm-v2/report_explained/standalone.pdf` per il rapporto ufficiale
con spiegazioni, denominatori e grafici; il rapporto originario resta in `report/`.

## Perché l'esperimento resta raccolto in una cartella

`esperimento_v2/` mantiene l'intera vecchia radice, incluso il precedente archivio.
Così riferimenti relativi, manifest e copie di codice rimangono verificabili.
Non è una cartella di soli file eliminabili: contiene anche gli strumenti per
preparare e svolgere il futuro confronto finale. I suoi README descrivono
l'epoca in cui furono scritti; lo stato corrente è nella radice del progetto.

Per usare i comandi Python storici, entrare in `esperimento_v2/` e usare
l'ambiente congelato. Su questo PC `.venv` è un collegamento all'ambiente
preservato nella radice; su un'altra macchina ricostruire da `uv.lock`
solo dopo aver trasferito e protetto i modelli necessari.
Non modificare gli script sigillati per ottimizzazioni cosmetiche.

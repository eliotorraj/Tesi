# Dati necessari al recupero degli esempi

Questa cartella rende autonomo il RAG del prototipo. Contiene solo dati train, con le informazioni necessarie a verificarne origine e integrità. Non contiene risultati validation o Test e non è il Training set del selettore MQT.

| Elemento | Contenuto |
| --- | --- |
| `rag_examples.jsonl` | 396 esempi train unici con scelte e compilazioni precedenti. |
| `circuits/train/` | I 396 circuiti OpenQASM 2 corrispondenti agli esempi. |
| `train_manifest.json` | Le 422 sorgenti train originarie, inclusi gli alias con lo stesso contenuto. |
| `transform.json` | Trasformazione delle 49 caratteristiche, derivata soltanto dal train. |
| `catalog_original.json` | Catalogo originale per la provenienza. |
| `seal.json` | Impronte dei dati, dei cataloghi e degli schemi controllati dal programma. |
| `pstools_verified.json` | Impronta del programma PsSuspend usato dall'avviatore desktop Windows. |

L'indice Qdrant non è una fonte: viene ricreato in `runtime/rag/`. Non modificare i file sigillati per aggirare un controllo. Il [documento tecnico](../docs/architettura_e_flusso.md) spiega estrazione, trasformazione e recupero.

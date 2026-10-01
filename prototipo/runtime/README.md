# Componenti locali di esecuzione

Questa cartella ospita programmi installati e dati ricostruibili. Su Git è distribuito solo questo README: i programmi e l'indice dipendono dal computer.

| Sottocartella | Funzione |
| --- | --- |
| `cpu/` | llama.cpp b10930 per il server Windows su CPU. |
| `desktop/` | llama.cpp b10930 con Vulkan per il desktop previsto dagli avviatori. |
| `pstools/` | PsSuspend verificato, usato dal controllo termico desktop. |
| `node/` | Eventuale copia locale di Node.js 22; in alternativa si usa Node nel PATH. |
| `rag/` | Indice Qdrant e informazioni derivate dai dati train distribuiti. |
| `models/` | Posizione facoltativa per i GGUF forniti separatamente; si può passare un percorso esterno. |

`setup.ps1 -DownloadRuntime` può installare i runtime Windows. Non scarica i pesi. `app.py prepare` prepara il RAG. Non copiare ambienti Python e indici tra sistemi operativi diversi. Il codec TOON è installato nella propria cartella `prototype/prompting/toon_runtime/`, tramite il lock npm.

Seguire la [guida](../docs/guida_passo_passo.md) e i [dettagli dei profili](../docs/installazione_e_runtime.md).

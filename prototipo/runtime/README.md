# Componenti locali di esecuzione

Nel clone è presente questo README. Gli altri contenuti vengono preparati sul PC e restano esclusi da Git.

| Sottocartella | Funzione |
| --- | --- |
| `llama.cpp/` | Sorgenti b10930 e compilazioni Linux CPU, Vulkan o CUDA, secondo la guida. |
| `server-runs/` | Log e controlli RAM dell'avviatore Linux `server.py`. |
| `models/` | Posizione facoltativa del GGUF; si può indicare un percorso esterno. |
| `rag/` | Indice Qdrant derivato dal train, ricreato per il sistema corrente. |
| `node/` | Eventuale runtime Node; in Linux normalmente si usa Node 22 nel PATH. |
| `cpu/`, `desktop/`, `pstools/` | Runtime Windows conservati per gli avviatori `.ps1`. |

`setup.sh` prepara il client, mentre la [guida](../docs/guida_passo_passo.md) mostra come compilare il server e procurarsi i pesi. `setup.ps1 -DownloadRuntime` riguarda i programmi Windows. Non copiare `.venv`, indici o eseguibili tra piattaforme incompatibili. I log del client sono nella distinta cartella `runs/`.

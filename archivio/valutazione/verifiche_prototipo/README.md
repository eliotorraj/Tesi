# Verifiche offline del framework

Questa cartella conserva la batteria di sviluppo che prima era `prototipo/checks.py`. Controlla le 396 estrazioni train, il recupero Qdrant rispetto al calcolo diretto, il contratto v4 con risposte sintetiche, il limite di contesto e la compilazione del Bell.

Dalla radice della repository, usando l'ambiente Python 3.12 già preparato:

```bash
.venv/bin/python archivio/valutazione/verifiche_prototipo/checks.py
```

In Windows usare `prototipo\.venv\Scripts\python.exe` come interprete. `--quick` limita a cinque le query confrontate; l'estrazione delle caratteristiche train resta completa.

`risultati/` conserva un nuovo resoconto per ogni controllo concluso o fallito. `runtime/` ospita i file temporanei delle risposte simulate. L'indice RAG usato è quello del prototipo. Queste prove non interrogano Qwen e non aprono il Test sperimentale.

Per il normale controllo dell'installazione basta `app.py check`, descritto nella [guida](../../../prototipo/docs/guida_passo_passo.md).

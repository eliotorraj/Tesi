# Verifiche software

Dopo il setup eseguire `.venv/bin/python -B verifiche/checks.py` da riproducibilita. Il controllo copia il kit in una directory temporanea, genera piccoli QASM e avvia un server HTTP sintetico. Prova Dataset, isolamento train, selezione, varianti Test, ripresa, contratti ed esportazione. Se disponibile compila anche i report LaTeX.

Non carica GGUF reali e non addestra politiche RL. Conserva e stampa la directory dei risultati; `--directory /percorso/nuovo` permette di sceglierla. Il codec TOON deve essere già installato. Le verifiche storiche del prototipo restano nell’archivio.

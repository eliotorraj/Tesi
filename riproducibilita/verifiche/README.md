# Collaudo del kit

Dopo il setup, da `riproducibilita/`, eseguire:

```bash
.venv/bin/python -B verifiche/checks.py
```

Il controllo copia il kit in una directory temporanea, genera piccoli QASM e avvia un server HTTP simulato. Prova Dataset, separazione train/validation/Test, selezione, varianti Test, ripresa, contratti ed esportazione. Se LaTeX è disponibile compila anche i report. Non richiede GPU o GGUF reali e non addestra politiche RL.

La cartella dei risultati viene stampata e conservata; `--directory /percorso/nuovo` ne sceglie la destinazione. Il codec TOON deve essere installato e Node 22 raggiungibile. Il successo del collaudo verifica il software, non la disponibilità del backend GPU, i tempi della CPU o la qualità dei modelli. Per controllare l'inferenza reale seguire la [prima prova del prototipo](../../prototipo/docs/guida_passo_passo.md).

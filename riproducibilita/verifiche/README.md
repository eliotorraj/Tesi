# Collaudo del kit

Dopo il setup, da `riproducibilita/`, eseguire:

```bash
.venv/bin/python -B verifiche/checks.py
```

Il controllo copia il kit in una directory temporanea, genera piccoli QASM e avvia un server HTTP simulato. Prova Dataset, separazione train/validation/Test, selezione, varianti Test, ripresa, contratti ed esportazione. Se LaTeX è disponibile compila anche i report. Non richiede GPU o GGUF reali e non addestra politiche RL.

La cartella dei risultati viene stampata e conservata; `--directory /percorso/nuovo` ne sceglie la destinazione. Il codec TOON deve essere installato e Node 22 raggiungibile. Il successo del collaudo verifica il software, non la disponibilità del backend GPU, i tempi della CPU o la qualità dei modelli. Per controllare l'inferenza reale seguire la [prima prova del prototipo](../../prototipo/docs/guida_passo_passo.md).

## Configuratore e percorso nominato

Da `riproducibilita/`, con l'ambiente attivato:

```bash
python -B -m unittest discover -s verifiche -p test_configuratore.py -v
python -B verifiche/checks.py --configuratore
```

Le verifiche mirate controllano errori senza modifica parziale, revisioni, selezione dei candidati, impronte, percorsi con spazi, blocco dopo preparazione anche su output esterni e indipendenza fra configurazioni. Usano directory temporanee e nessun peso reale.

`--configuratore` estende il collaudo completo: crea una configurazione tramite CLI, avvia un eseguibile LLM sintetico per verificare gli argomenti CPU, controlla il server simulato e attraversa Dataset, validation, sei sistemi Test, report ed esportazione con piccoli circuiti reali. I registri si conservano nella directory stampata. Senza l'opzione resta disponibile il controllo dell'interfaccia tradizionale `--config`. Queste prove verificano il software, non la qualità di nuovi LLM o modelli MQT.

Il collaudo tecnico limita a uno i processi Qiskit e i thread BLAS e usa timeout di 300 secondi per compilazione, per contenere il carico su macchine condivise. Questi limiti sono registrati nell’esito e non cambiano i valori distribuiti per gli esperimenti. Un timeout resta un esito fallito del collaudo: i registri non vengono cancellati per riprovare.

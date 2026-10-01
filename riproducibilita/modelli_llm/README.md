# Registro e avvio dei modelli LLM

`qwen/`, `phi/` e `gemma/` sono cartelle predisposte per GGUF forniti dall'utente. Il clone non contiene pesi. `modelli.json` elenca i candidati con identità, file, revisione, hash, contesto, temperatura, budget e trasporto. `provenienza_originale.json` conserva gli URL e gli hash dei tre GGUF distribuiti come riferimento.

Il campo `file` è relativo al registro oppure assoluto. Tutti i candidati dichiarati devono essere disponibili al congelamento: per provare soltanto Qwen mantenere soltanto quella voce prima di `prepara`. Per altri pesi aggiornare identità e impronta, oppure indicare `sha256: null` per calcolarla al congelamento. Rispettare le licenze delle fonti.

Su Linux, da `riproducibilita/`, usare un eseguibile llama.cpp compatibile:

```bash
.venv/bin/python -B modelli_llm/server.py --bin /percorso/llama-server --list-devices
.venv/bin/python -B modelli_llm/server.py qwen --bin /percorso/llama-server --gpu-layers 0
```

Il secondo comando forza CPU e `device=none`. Per GPU scegliere `--gpu-layers 999` o un numero di strati compatibile con la memoria; `--device` accetta un identificativo restituito dal backend. Il server non incorpora il nome della GPU del fisso. `--threads` imposta i thread; contesto, cache e batch provengono dal registro. Sono necessari gli endpoint `/health`, `/props`, `/apply-template`, `/tokenize` e `/completion` con schema JSON.

Il server conserva versione, impronte, dispositivi esposti, comando e log in `esecuzioni/<id>/servers/`. Non installa driver e non misura temperatura o memoria GPU. Una GPU adeguata è consigliata; il contesto predefinito 60.000 non è una configurazione CPU garantita su 16 GB. Prima del congelamento valutare 16.384, batch 128, microbatch 64 e un candidato per una prova ridotta.

Per server Linux usare `transport: "native"`, anche in WSL. Il server Windows del fisso richiede `transport: "windows"`, `curl.exe` e un GGUF accessibile dal client, per esempio tramite `/mnt/d/`. I `.ps1` del prototipo restano conservati per Qwen sul fisso; non sono avviatori universali dei tre candidati. Le istruzioni complete sono nella [guida](../documentazione/guida.md).

# Modelli LLM e avvio del server

`qwen/`, `phi/` e `gemma/` sono destinazioni predisposte per GGUF forniti dall'utente. Il clone non contiene pesi. `modelli.json` fornisce i candidati iniziali; `provenienza_originale.json` conserva URL, revisioni e impronte dei file di riferimento.

Per un esperimento nominato, seleziona i candidati e collega i file tramite il configuratore. Esempi da `riproducibilita/`, con ambiente attivato:

```bash
python configura.py modelli mia-prova qwen
python configura.py modello mia-prova qwen --file /percorso/Qwen3.5-4B-Q8_0.gguf
python configura.py risorse mia-prova --server-bin /percorso/llama-server --gpu-layers 0
python configura.py verifica mia-prova
```

Gli altri candidati diventano inattivi, mantenendo le proprie impostazioni; i loro pesi non sono richiesti. Per un LLM nuovo o una quantizzazione diversa usa `aggiungi-modello`: servono un GGUF locale, provenienza, revisione e precisione. Il programma ne calcola SHA-256 senza caricarlo. Cambiare il percorso di Qwen non sostituisce la sua impronta con quella di qualunque altro file. I dettagli sono nel [ricettario](../documentazione/configurazione.md#registrare-un-altro-llm).

L'avviatore legge il registro dell'esperimento e le risorse salvate:

```bash
python esperimento.py --esperimento mia-prova server qwen --list-devices
python esperimento.py --esperimento mia-prova server qwen
```

Il server mantiene occupato il terminale. Da un secondo terminale, con lo stesso ambiente, `server qwen --controlla` verifica identità e contesto senza inferenza. Ctrl+C ferma il server avviato. Sono richiesti gli endpoint llama.cpp `/props`, `/apply-template`, `/tokenize` e `/completion` con schema JSON; `/health` permette anche il controllo manuale del caricamento.

Il profilo CPU usa zero strati GPU e passa `device=none`; i profili GPU chiedono accelerazione. `--list-devices` espone gli identificativi del backend, senza nomi Radeon incorporati. La compatibilità dipende da modello, memoria, driver e backend. I profili non garantiscono che una campagna completa entri in 16 GB.

Versione, impronte, dispositivi, comando e log sono in `esecuzioni/<nome>/servers/`, sotto la radice risultati scelta. L'avviatore non misura temperatura, energia o memoria GPU. Le opzioni dirette `--bin`, `--gpu-layers`, `--device`, `--threads` prevalgono sui valori salvati e sono registrate; per condizioni pianificate configura prima di `prepara`.

Il server Linux usa `native`, anche in WSL. Sul fisso puoi mantenere il server Windows con `modello NOME qwen --trasporto windows`, `curl.exe` e un GGUF accessibile da WSL. I `.ps1` del prototipo restano conservati. L'avvio Windows è esterno a questo script; `server qwen --controlla` verifica anche quel trasporto. Per l'interfaccia tradizionale resta `modelli_llm/server.py`, con `RIPRO_CONFIG` e `RIPRO_OUTPUT` se servono configurazioni diverse da quella distribuita.

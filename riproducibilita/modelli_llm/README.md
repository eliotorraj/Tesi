# Modelli LLM forniti dall'utente

Le cartelle `qwen/`, `phi/` e `gemma/` sono segnaposto: nessun peso è incluso o scaricato. `modelli.json` identifica i tre GGUF Q8_0 originali, ma si può sostituire l'elenco. Ogni candidato ha ID, percorso, provenienza/revisione, precisione, hash, URL locale, contesto, budget e temperature.

`file` è relativo al registro: il valore iniziale è `<id>/modello.gguf`, ma sono ammessi percorsi assoluti. Per un file diverso aggiornare `sha256`, oppure impostarlo a `null` per calcolarlo al congelamento. Tutti i candidati dichiarati devono essere presenti. Non basta cambiare il nome commerciale mantenendo l'hash precedente.

`provenienza_originale.json` riporta revisioni e URL registrati per i pesi iniziali. Le licenze dei modelli si applicano ai download autonomi.

`server.py ID --bin /percorso/llama-server` avvia un eseguibile esterno e registra versione, impronte e argomenti. Il runtime storico è llama.cpp b10930 Windows Vulkan; revisioni o piattaforme diverse costituiscono nuove condizioni. Servono `/props`, `/apply-template`, `/tokenize` e `/completion`, schema JSON vincolato e template corretto. Il client controlla l'identità del GGUF realmente servito.

`--gpu-layers 0` permette un avvio CPU; `--threads` sceglie i thread. Non è incluso il precedente supervisore termico specifico del desktop. Dichiarare contesto, quantizzazione e risorse prima del congelamento.

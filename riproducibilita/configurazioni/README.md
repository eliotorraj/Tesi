# Impostazioni da decidere prima della prova

`esperimento.json` sceglie identificativo, corpus, catalogo, registro LLM, griglie e metodi. `catalogo.json` definisce Target quantistici, impronte, configurazioni Qiskit, seed e limiti dei processi. `generazione_llm.json` definisce prompt e parametri comuni della generazione.

Il PC che esegue Qwen si configura nel registro `modelli_llm/modelli.json` e negli argomenti del server, non cambiando i Target IBM/Quantinuum. Su Linux CPU partire da un candidato e valutare contesto 16.384, batch 128 e microbatch 64; sono condizioni ridotte da dichiarare, non una promessa che la campagna completa entri in 16 GB. Ridurre `execution_policy.workers` del catalogo se la RAM richiede meno compilazioni parallele.

Cambiare tutto prima di `prepara`; per modifiche successive usare un nuovo `experiment_id`. `esperimento.py hardware` mostra i Target disponibili e le loro impronte, non rileva la GPU del PC. Aggiungere un nuovo Target richiede anche il codice per costruirlo. Percorsi e sequenza sono nella [guida](../documentazione/guida.md).

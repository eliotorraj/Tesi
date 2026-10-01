# Configurazioni della nuova esecuzione

`esperimento.json` sceglie identità, ingressi, seed, griglie e metodi. `catalogo.json` elenca Target, impronte, configurazioni Qiskit, tre seed e limiti operativi. `generazione_llm.json` conserva i parametri fissi della generazione e del prompt.

Modificarli prima di `prepara`. Il catalogo prodotto in `esecuzioni/<id>/` ha una nuova identità. Per cambiare dispositivi usare Target disponibili nella versione MQT fissata e aggiornarne le impronte con `esperimento.py hardware`. Un dispositivo completamente nuovo richiede anche il codice che lo costruisce, non soltanto un nome nel JSON.

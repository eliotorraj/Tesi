# Copia nativa del controllore desktop

Il progetto di sviluppo e in WSL. Per evitare di eseguire DLL da un percorso
UNC, e stata preparata una copia tecnica in `D:\Tesi-mqt\prototipo-native`.
Contiene `server-desktop.ps1`, `server-desktop-internal.ps1`,
`verify-model.ps1`, `AmdSensors.cs`, `config.json` e i soli runtime
`runtime/desktop` e `runtime/pstools`. I pesi sono rimasti nel percorso
Windows preesistente; non sono stati scaricati.

Su un'altra macchina copiare questi stessi file in una cartella Windows
locale, oppure copiare tutto il prototipo come descritto nel README.
Avviare il controllore da quella cartella con un `ModelPath` locale.
Non copiare l'indice Qdrant creato su Linux: viene ricostruito da `app.py prepare`.

La copia nativa ha completato il trasferimento, ma in questa sessione il
controllore e rimasto bloccato prima dei registri e dell'avvio del server.
Sono stati tentati PowerShell 5.1 e 7; i soli processi posseduti sono stati
fermati. Nessuna risposta Qwen reale e stata ottenuta. La causa del blocco
resta da diagnosticare; non attribuiamo il problema a pesi o compilazione.

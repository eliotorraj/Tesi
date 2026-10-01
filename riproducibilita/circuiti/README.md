# Circuiti sostituibili

`train/`, `validation/` e `test/` contengono 422, 88 e 90 OpenQASM 2 originali. Si possono sostituire prima di creare una nuova esecuzione. I nomi devono essere univoci fra split; stessi contenuti o sequenze di istruzioni non possono comparire in split diversi. Gli alias train restano nel manifest ma non aggiungono esempi RAG né campioni ML.

`manifest_originale.json` è la provenienza del corpus iniziale: non va aggiornato per i nuovi ingressi. `esterni/qasmbench/` contiene cinquanta circuiti opzionali con licenza e manifest. Le copie congelate sono generate sotto `esecuzioni/<id>/`. La partizione scientifica è responsabilità di chi prepara il corpus: i controlli non dimostrano disgiunzione delle famiglie.

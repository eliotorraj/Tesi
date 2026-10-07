# Verifiche della procedura incrementale

Le prove di sviluppo sono separate dalle campagne sui 90 circuiti.
Le risposte LLM sono simulate. Una prova compila realmente Bell per controllare
salvataggio, score e ammissione nella memoria.

Esito della consegna del 2 ottobre: **11 verifiche automatiche superate**. Le quattro campagne sono preparate, con 90 circuiti ciascuna e zero esiti sperimentali. Il report sintetico e i due grafici autonomi compilano; le due pagine del documento sono state controllate visivamente.

I controlli riguardano:

- collegamento nativo o Windows al server e identità del modello;
- corrispondenza con tutti i 90 recuperi storici quando la memoria è vuota;
- quattro permutazioni riproducibili;
- esclusione del circuito corrente e delle osservazioni future;
- distinzione tra una singola osservazione e una migliore configurazione;
- codec TOON e controllo dei fatti;
- separazione delle memorie e ripresa senza ripetere esiti;
- conservazione di interruzioni, errori e score zero validi;
- rilevazione di registri modificati;
- medie appaiate e denominatori dei dati mancanti.

`test_incrementale.py` esegue i controlli automatici.
`verifica_report.py --pdf` genera l'anteprima con dati interamente sintetici
in `temporanei/`, distinta dai report delle campagne.

Le verifiche sono prove tecniche; non dimostrano un miglioramento degli score.
I registri riassuntivi di questa consegna sono conservati accanto a questo README.

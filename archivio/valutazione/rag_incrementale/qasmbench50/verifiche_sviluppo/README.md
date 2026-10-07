# Verifiche QASMBench50

Questa cartella documenta i controlli tecnici. Non contiene esiti delle
nuove decisioni sui 50 QASMBench.

Esito del 2 ottobre: **15 verifiche automatiche superate**, 50 recuperi storici
riprodotti, 9.000 esiti oracle verificati. Le quattro campagne sono preparate
con memorie vuote e zero decisioni sperimentali. Il PDF sintetico di 12 pagine
e le dodici figure autonome compilano; tutte le pagine sono state controllate
visivamente. Dettagli e avvisi del compilatore sono in `verifiche.json`.

- `derivazione.json` registra i sorgenti MQT Bench da cui deriva la copia autonoma.
- `test_incrementale.py`, nella cartella superiore, controlla procedura, ripresa, memoria e recuperi storici; l'LLM è simulato.
- `test_report.py` controlla abbinamenti per circuito, denominatori, scarti negativi, valori zero, dati mancanti, figure complete e rifiuto di un riepilogo oracle alterato.
- `oracle_*.json` registra la verifica in sola lettura dell'oracle reale.
- `temporanei/` conserva le anteprime sintetiche e i controlli visivi, esclusi da Git.

Una sola prova tecnica compila Bell: non è una compilazione di uno dei
cinquanta circuiti della campagna. Le anteprime sono marcate come sintetiche
su ogni pagina e in ciascuna figura autonoma. Non dimostrano qualità delle scelte.

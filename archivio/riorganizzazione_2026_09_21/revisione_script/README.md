# Revisione manuale completa degli script

Il 21 settembre sono stati letti integralmente i **132 script ancora da leggere**
e completato quello letto solo in parte. Con i 14 gia conclusi il 20 settembre,
la copertura e di **147 script operativi, 34.625 righe attuali**. La differenza
rispetto alle 34.750 righe del primo inventario dipende dal ripristino della
versione congelata di `llm_selection/v2/plots.py`, gia documentato nel riordino.

La lettura segue scopo, dipendenze, ingressi e uscite, gestione degli errori,
ripresa delle esecuzioni, separazione degli split, uso degli score, percorsi
legati alla macchina e possibili miglioramenti. Ogni file ha una scheda:
[rassegna navigabile](rassegna_147_script.md) e [inventario completo](inventario_completo.json).
Le schede distinguono difetti dimostrati, limiti noti e proposte di miglioramento.
La copertura non e ricavata dal solo controllo sintattico.

## Risultato e priorita

La revisione e conclusa; **i difetti elencati non sono tutti corretti**.
I 147 sorgenti coincidono con il riferimento congelato. Le correzioni vanno
portate in una nuova versione operativa e verificate prima di riusare i comandi
coinvolti. Cosi restano ricostruibili le prove gia svolte.

Prima di preparare il Test occorre affrontare questi gruppi di problemi:

1. **Collegamento alla selezione ufficiale.** I comandi storici di valutazione
   e apertura consultano ancora la prima selezione. Devono recepire
   `local-llm-v2`, Qwen a temperatura zero e il contratto corretto senza RAG.
2. **Identita degli artefatti.** Alcuni controlli MQT e delle prove canary non
   legano completamente il risultato ai manifest e ai modelli correnti. Il
   generatore Qiskit non riconfronta i byte del QASM con l'impronta prevista
   subito prima della compilazione.
3. **Chiusura e rapporto della validation.** Il sigillo v2 non rifiuta un file
   aggiunto dopo la chiusura. Il rapporto v2 non verifica le impronte separate
   delle analisi che legge. Vanno controllati insieme elenco dei file e contenuto.
4. **Interruzioni e ripetizioni.** Sono stati riprodotti casi di perdita o
   sostituzione dei registri, risultati ancora in coda classificati come errore,
   budget cambiati non riconosciuti e fine del processo senza record terminale.
5. **Portabilita e chiarezza.** Restano assunzioni Windows/WSL e percorsi dei
   checkpoint non condivisi tra avviatore e addestramento. Alcuni riepiloghi
   devono dichiarare meglio denominatori e regole delle parita.

Questi rilievi non dimostrano che i risultati congelati siano alterati.
I rapporti indicano quando il difetto riguarda un controllo autonomo ma il
flusso completo contiene altre protezioni. Non e stata rifatta la validation.
Il precedente controllo d'integrita degli artefatti rimane una verifica distinta.

## Rapporti dettagliati

| Gruppo | Copertura nuova | Documento | Schede |
| --- | ---: | --- | --- |
| Comandi e addestramento | 23 file, 8.496 righe | [scripts.md](scripts.md) | [scripts.json](scripts.json) |
| Prototipo e Dataset | 38 file, 13.399 righe | [prototype_data.md](prototype_data.md) | [prototype_data.json](prototype_data.json) |
| Selezione LLM e test | 72 file, 11.278 righe | [llm_tests.md](llm_tests.md) | [llm_tests.json](llm_tests.json) |

I due rilievi del 20 settembre sul ciclo di vita del server e sul timeout del
trasporto restano nel [rapporto precedente](../../riorganizzazione_2026_09_20/revisione_script/revisione_script.md).
La revisione precedente resta conservata come documento di quella data.

## Ottimizzazione e commenti

Per i moduli lunghi le schede propongono separazioni precise tra preparazione,
esecuzione, verifica e salvataggio. Per il recupero dei dati si puo valutare
una copia verificata in memoria, legata alle impronte, prima di ottimizzare i
controlli ripetuti. Non sono dichiarati miglioramenti di velocita senza misure.
Le costanti scientifiche, le regole dei pareggi e le verifiche di integrita
non vanno eliminate per rendere il codice piu breve.

Le spiegazioni del funzionamento sono nelle schede accanto ai sorgenti
conservati. Non sono stati aggiunti commenti dentro i file congelati, perche
anche un commento cambierebbe le loro impronte. La documentazione distingue
l'originale, il dimostratore attuale e le proposte da realizzare.

## Controlli svolti

Le prove nuove sono brevi e circoscritte: funzioni con dipendenze simulate,
file temporanei, record sintetici e un solo Bell tecnico compilato. Non sono
stati caricati modelli LLM o MQT addestrati, ne usati circuiti validation/Test.
I test completi del progetto non sono stati ripetuti: i 266 superati il
20 settembre restano un risultato della consegna precedente.

Per il gruppo scripts sono conservati [riproduttore](scripts_reproductions.py)
e [risultati](scripts_simulations.json). Per gli altri gruppi metodo ed esiti
sono nelle singole schede; le esecuzioni inline non sono presentate come
programmi autonomi gia versionati. I difetti dedotti dal flusso del codice
sono distinti dai casi eseguiti.

Il [controllo di copertura](verifica_copertura.json) confronta SHA256, numero di
righe, intervalli e insieme dei file con il riferimento del 20 settembre.
Si puo ripeterlo senza eseguire esperimenti:

```bash
python3 archivio/riorganizzazione_2026_09_21/revisione_script/verifica_copertura.py
```

Per rigenerare inventario e rassegna a partire dalle tre schede di gruppo:

```bash
python3 archivio/riorganizzazione_2026_09_21/revisione_script/consolida_revisione.py
```

Questo controllo verifica la tracciabilita dichiarata; non dimostra da solo
la correttezza della lettura o l'assenza di difetti.

## Prove lasciate all'utente

I [comandi manuali](../../../prototipo/docs/comandi_verifica_manuale.md) includono
backup e aggiornamento Graphify, avvio Qwen sul fisso, controllo del server,
prova completa dal client WSL e variante CPU sul portatile. La sintassi dei
comandi e i percorsi locali sono stati controllati; non e stata eseguita una
nuova inferenza. La nuova `.graphifyignore` evita copie e runtime ripetuti e
mantiene nel perimetro sorgenti e documenti del progetto.

- [Verifica dei comandi](verifica_comandi.json).
- [Verifica delle esclusioni del grafo](verifica_esclusioni_graphify.json).

Il Test resta chiuso. La prossima prova con Bell e una verifica tecnica del
prototipo, non il confronto sperimentale finale.

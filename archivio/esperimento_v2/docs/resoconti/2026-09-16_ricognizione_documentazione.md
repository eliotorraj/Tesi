# Ricognizione e riordino della documentazione — 15–16 settembre 2026

## Perché questo intervento

Le informazioni erano distribuite tra un README fermo al 9 settembre, guide
operative lunghe e resoconti di singole modifiche. Era difficile distinguere
che cosa fa il sistema da che cosa è stato verificato.

Abbiamo organizzato tre livelli: README generale; README delle cartelle con
responsabilità e inventario dei file; approfondimenti e resoconti tecnici in
`docs/`. I rapporti generati restano accanto ai dati e sono collegati da un
indice centrale.

## Fonti confrontate

La ricognizione ha confrontato codice, protocollo, manifest, statistiche già
prodotte, metadati dei modelli e registri delle prove. Non ha rieseguito
compilazioni, addestramenti, inferenze o valutazioni sperimentali.

| Evidenza osservata il 15 settembre | Interpretazione |
| --- | --- |
| Manifest: 600 circuiti, 422 train / 88 validation / 90 test | Il corpus e le partizioni sono definiti. |
| Statistiche Qiskit: 87.120 esiti, 82.621 successi, 4.499 timeout | Il popolamento train/validation è completo, inclusi gli esiti negativi. |
| 29.040 aggregati, 27.360 ammissibili | Alcune coppie circuito-configurazione hanno tutti i tre seed riusciti; questo non implica un oracle per ogni circuito. |
| Vista globale: 396 esempi train | I duplicati byte per byte non aumentano gli esempi recuperabili. |
| Verifiche RAG e audit di 93 prompt (5 train, 88 validation) | Recupero e conservazione degli input controllati; nessuna conclusione sulla qualità LLM in validation. |
| Modello canonico Quantinuum: 100.352 passi, obiettivo 100.000 | Completamento registrato dell'addestramento di quel modello; il confronto MQT richiede gli altri modelli e le verifiche. |
| Nessun completamento della selezione o record di apertura del test nei percorsi previsti | Non è ancora possibile dichiarare conclusa la selezione o svolto il test. |
| Ultima prova automatica Qwen `qwen-prompt-v2-02` | Un solo circuito train DJ, tre chiamate: scelta corretta ma tre risposte semanticamente non valide. |

I registri tecnici LLM ispezionati contenevano 30 decisioni terminali: 16
fallimenti e 14 timeout. Questo conteggio non include necessariamente tutti
gli avvii o le chiamate fisiche: alcune esecuzioni si interrompono prima della
decisione finale. Non è una classifica tra modelli.

Il sottoinsieme di 410 circuiti compatibili con tutti i dispositivi indica
la compatibilità hardware. Non va confuso con il numero di riferimenti
esaustivi validi: questi richiedono tutti i tentativi della matrice compatibile
riusciti, come stabilito dal protocollo.

L'utente ha comunicato l'avvio del training `ibm_falcon_27`.
Nell'albero ispezionato erano visibili anche log iniziali Falcon 127; questi
non identificano da soli tutti i processi attivi e non dimostrano che il
training dichiarato non esista. L'intervento documentale non ha modificato
processi, checkpoint o impostazioni di addestramento.

## Che cosa è stato riorganizzato

| Prima | Adesso |
| --- | --- |
| README principale con stato vecchio | Presentazione della tesi, flusso, mappa, avvio, demo e stato datato. |
| Molte cartelle senza guida | README con responsabilità e descrizione di file o gruppi omogenei. |
| `prototype/README.md` con storia tecnica | Guida generale; contenuto precedente conservato nell'approfondimento del prototipo. |
| `llm_selection/README.md` molto operativo | Panoramica e inventario; procedura negli approfondimenti. |
| `llm_selection/CHAT_QWEN.md` | Guida chat negli approfondimenti e diagnosi nei resoconti. |
| `llm_selection/PROMPT_COMPATTO.md` | Resoconto datato sul prompt compatto. |
| README storico del Dataset v1 | Guida breve locale; descrizione tecnica conservata nei resoconti. |
| Note locali `GITHUB.md` e `Latex.md` | Storia della pubblicazione e istruzioni di relazione nelle rispettive sezioni. |
| KB con oltre 6.000 righe di conversazioni | Riassunto iniziale breve; testo precedente integralmente nella cronologia. |
| `tesi/LEGGIMI.md` | `tesi/README.md`; nota della prima consegna conservata nelle note di redazione. |

Il testo originale della KB è conservato integralmente dopo l'avviso iniziale.
SHA-256 del contenuto originario:
`7d334011cc9fcb1cff0f9b5ba3c5cad8e208e159b26d8efe17217ad27709173c`.

Non sono state spostate copie del codice delle prove, dati congelati, circuiti,
cache, pesi, checkpoint o risultati. Le cartelle ripetitive di esecuzioni e
circuiti sono descritte dal README del gruppo: non ricevono nuovi file al loro
interno.

La cartella locale `tesi/` e il materiale locale `archivio/sviluppo/` restano
esclusi da Git. Le guide dei modelli e dei checkpoint sono invece ammesse tramite
eccezioni limitate ai README; i rispettivi dati restano esclusi.

## Correzioni di descrizioni superate

Il vecchio README diceva che mancavano il collegamento LLM e tutti i modelli
finali locali. Sono stati distinti collegamento funzionante, risposte non ancora
valide e presenza del modello canonico Quantinuum.

Il protocollo riportava ancora soglie del monitor LLM precedenti a quelle
del codice. La descrizione è stata allineata ai valori già presenti:
105/100 °C per pausa/ripresa hotspot, 108/95 °C per arresto hotspot/edge.
Il limite di risposta corrente è 4096 token; i vecchi tentativi possono usare
2048. Le impostazioni registrate in ciascuna prova restano la fonte per
interpretarla. Nessuna soglia o parametro è stato cambiato da questo riordino.

## Verifiche e limiti

Sono stati controllati i collegamenti locali in **72 documenti** della
navigazione e delle guide: nessun collegamento mancante. L’inventario non
lascia file operativi senza descrizione nelle cartelle di codice, configurazioni
e schemi. La conservazione integrale della vecchia KB è verificata contro Git.
`git diff --check` non segnala errori di spaziatura. Una revisione indipendente
ha confermato numeri e descrizioni e ha fatto correggere gli esempi di avvio
che riusavano nomi di prove già esistenti. Le verifiche automatiche del software non sono state
rieseguite durante il training. Non si attribuiscono a questa attività i
conteggi delle suite eseguite in sessioni precedenti.

Le relazioni Word/PDF storiche e i capitoli della tesi sono stati catalogati,
non riscritti o nuovamente impaginati. La bozza LaTeX richiede ancora la verifica
del PDF. Le fotografie storiche possono conservare percorsi e comandi
superati, esplicitamente segnalati come tali.

Le modifiche concorrenti allo script di training e la modifica già presente
al resoconto di manutenzione sono rimaste separate dall'intervento documentale.

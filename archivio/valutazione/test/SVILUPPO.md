# Preparazione dei Test indipendenti — 21 settembre 2026

Richiesta: quattro avvii autonomi, risultati separati e MQT non vincolante per
gli altri metodi. Il confronto corrente è LLM+RAG, stesso LLM senza RAG,
MQT Predictor e Random. Oracle facoltativo come riferimento osservato.
I modelli di frontiera e le dieci configurazioni fisse non appartengono più
al confronto finale. La storia della validation è conservata integralmente.

## Che cosa è cambiato

Il nuovo controllo legge espressamente lo studio local-llm-v2 e verifica i
legami tra studio, selezione, configurazione finale e sigilli dei tre modelli.
Verifica anche le fonti analitiche della validation tramite le loro impronte.
Non importa llm_selection.finalize, non chiama il vecchio release e non scrive
il vecchio record di apertura. I riferimenti logici nell'archivio sono invariati.

Il contratto si congela soltanto al primo avvio ufficiale. Ciascun metodo
ha una propria esecuzione e può iniziare quando soddisfa i suoi requisiti.
MQT richiede i propri modelli, la loro provenienza e sei prove tecniche.
I due LLM verificano il GGUF realmente dichiarato dal server e il contesto.

La variante senza RAG non apre il Dataset né l'indice. Usa lo stesso modello
e contratto v4; riceve un'istruzione esplicita per il solo fatto di capacità.
Con RAG il testo del prompt rimane invariato quando ci sono esempi.

La nuova unità operativa è una compilazione per circuito: seed Qiskit 0.
Questo emendamento sostituisce i tre seed del vecchio piano Test; la validation
non viene ricalcolata. Il nuovo score non è la mediana storica dei tre seed.

## Prove e correzioni conservate

- Verifica delle fonti: 600 circuiti, partizioni 422/88/90, cinque Target,
  396 esempi RAG, 31.307 riferimenti dei sigilli v2 verificati.
- La prima verifica dei sigilli ha rifiutato un modello esterno perché
  risolto fuori dalla cartella. Il controllo ora ammette solo riferimenti
  relativi esplicitamente sigillati e ne verifica sempre lo SHA-256.
- Il primo caricamento delle regressioni ha trovato una parentesi mancante
  nel generatore del rapporto. Corretto prima delle prove riuscite.
- La prima prova Random su Bell è fallita: mancava il campo opzionale delle
  configurazioni ammesse. Il caso è conservato in
  `prove_tecniche/random/e38295ff90bf4482a061a1ca92ed60ad/`.
  Ora l'assenza di restrizioni significa tutte le configurazioni del catalogo.
- La prova successiva è riuscita, con compilazione reale, score e rapporto:
  `prove_tecniche/random/e02cb548a51a4c568356fa167e68b6a3/`.
  È una prova tecnica, non evidenza di qualità sul Test.
- Regressioni: isolamento senza RAG, compilazione Random, timeout e uscita
  senza risultato, immutabilità dei registri, interruzione senza ripetizione,
  token parziali, denominatori, equivalenza numerica dello score con MQT
  su due Target, coda JSONL, corruzione interna e timeout del selettore.
- Il PDF della prova sintetica è compilato con TeX Live/PGFPlots e controllato
  tramite immagine della pagina. Le analisi conservano sorgenti, tabelle e grafici.

## Correzione del controllo contesto — 21 settembre 2026

L'avvio LLM+RAG segnalato dall'utente alle 13:37 UTC ha superato i controlli
statici, poi si è fermato prima della valutazione: il server era avviato con
`-c 60000`, ma `/props` dichiarava 60.160. Il confronto esatto con 60.000
rifiutava quindi un valore compatibile. Il tentativo fallito rimane nel registro
`preparazione/verifiche/`; non va cancellato.

Il [codice di llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-context.cpp)
arrotonda il contesto al multiplo successivo di 256: per 60.000 risulta 60.160.
La verifica ora accetta solo il valore nominale del profilo desktop e quello
allineato. Il limite applicativo per prompt e risposta resta 60.000.
I nuovi registri distinguono `context_requested` e `context_reported` e
conservano la risposta originale di `/props`. Questo controllo non dimostra
da solo quale argomento sia stato passato al processo: per quello resta
necessario il registro di avvio del server.

Verifica tecnica: quattro regressioni in
`verifiche/test_server.py`, eseguite con
`.venv/bin/python prototipo/test/verifiche/test_server.py`, tutte riuscite.
Usano un piccolo file sintetico e risposte simulate, anche per il ponte WSL.
Controllano i due contesti validi, valori e tipi non ammessi, modello fornito
errato e modello servito diverso. Nessuna chiamata reale al server e nessun
avvio del Test. Anche `git diff --check` è riuscito.

Limiti degli strumenti durante la correzione: la shell Windows non partiva
per un errore di inizializzazione della sandbox. LeanCTX ha consentito modifica
e prove; ha invece bloccato graphify tramite la propria lista dei comandi
ammessi. Il grafo non è stato aggiornato. Il primo comando unittest con filtro
`-p` è stato rifiutato dal controllo dello strumento; l'esecuzione diretta
del file di verifica è riuscita.

## Limiti e operazioni non svolte

Non sono stati aperti i 90 circuiti alla valutazione: nessuna inferenza o
compilazione Test. Non è stata eseguita una nuova inferenza Qwen.
Le regressioni LLM usano risposte simulate. Non è stato completato un nuovo
addestramento ML lungo né verificata sperimentalmente la memoria del portatile.

Nel clone controllato manca il modello canonico ibm_heron_133. Il selettore
resta quindi non pronto in questo ambiente. Non si deduce lo stato degli
artefatti su altri computer.

Il timeout del processo include l'avvio dell'interprete e delle dipendenze.
Il tempo della sola compilazione è misurato all'interno del processo quando
disponibile; per timeout senza risultato rimane mancante. Non si attribuisce
artificialmente l'intero timeout alla sola compilazione.

Il piano corrente usa intervalli descrittivi appaiati, senza dichiarare
superiorità statistica con il vecchio insieme di 14 confronti. L'oracle
non è generato automaticamente. Memoria e consumi energetici non sono misurati.

La revisione operativa del selettore è una copia dichiarata del motore storico:
non è una riscrittura completa dell'addestramento. Le tre correzioni prioritarie
e la provenienza sono documentate nella sua cartella.

# Correzione del trainer ML — 21 settembre 2026

## Problema e prove sul portatile

Con il fork dopo il caricamento del modello, la prova dei primi 10 circuiti
sui cinque dispositivi ha prodotto 27 successi e 23 timeout a 300 secondi.
La traccia di Falcon 27 restava in SabreLayout. Senza fork lo stesso caso
è riuscito in 3,438 secondi. QiskitO3 è poi riuscito su Falcon 127 e Quantinuum.

La prima diagnostica su più circuiti ha rivelato un secondo difetto:
la funzione BQSKit veniva avvolta ripetutamente e riutilizzava una connessione
chiusa. Corretto anche questo, l'utente ha fornito 50 successi su 50 coppie,
tutte eseguibili sui target. Sono 10 circuiti, non 50 circuiti distinti.
I tempi registrati vanno da 0,178 a 4,188 secondi. Ogni sequenza contiene
due azioni di compilazione e terminate: questo non dimostra qualità ottimale.

Le diagnostiche iniziali basate su runpy non attivavano la traccia nei processi
spawn. Una successiva variante senza fork falliva per doppia chiamata a setsid.
Queste prove non stabiliscono nulla sulla qualità RL. Tutti gli esiti precedenti
vanno conservati, compresi errori di connessione e timeout.

## Modifica operativa

addestra.py resta l'avvio ufficiale. Il motore compila nel worker spawn che
possiede il modello, inizializza la sessione una sola volta e apre una connessione
BQSKit per ogni circuito. Il supervisore controlla il limite della compilazione,
termina il gruppo di processi bloccato e riprende i lavori ancora disponibili.
I risultati oltre il limite non vengono accettati. Gli output non verificati
vengono conservati in non_verificati, fuori dai checkpoint riutilizzabili.
La nuova cache separa queste esecuzioni dalle vecchie e congela thread e worker.

## Verifica e limiti

Le regressioni usano dati sintetici: compilazioni consecutive nello stesso
processo, riapertura BQSKit, timeout con un processo spawn reale, riavvio sul
lavoro successivo e ripresa senza ripetere tentativi esauriti.
La prova RL di 50 coppie è stata eseguita sul portatile con la variante
diagnostica, non nuovamente con il trainer definitivo sul desktop.
Nessun nuovo training completo o Test ufficiale è stato avviato in questa modifica.
Il limite di 100 secondi rimane quello dell'esperimento; il piccolo campione non
basta per scegliere un timeout diverso. Nessun modello RL è stato riaddestrato.

Esito dei controlli: tre regressioni sui processi e tre sulla cache superate.
Graphify: aggiornamento completo interrotto durante la scansione; anche il
tentativo incrementale è stato interrotto dopo mancata risposta di WSL.
Il completamento dell’aggiornamento del grafo non è confermato.

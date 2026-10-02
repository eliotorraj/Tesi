# Controllo della revisione del report Test

Documento finale: ../../30dd5b4f737c058e/confronto/latex/verifica.pdf

Sono state controllate visivamente tutte le 45 pagine del confronto e le
tabelle modificate dei documenti individuali. Le dieci figure occupano
ciascuna una sola pagina, con il testo introduttivo e tutti e quattro i pannelli.
La cartella finale conserva anteprime e verifica.json.

I 22 controlli del generatore passano. Riepiloghi, confronti appaiati e tabelle
numeriche coincidono byte per byte con la versione 675f715bb32595bf.
Le impronte degli input sono identiche. Sono valide anche le impronte di
tutti gli output della versione originale e di quella finale.
Nessun documento genera avvisi di righe o blocchi oltre i margini.

La prima versione di impaginazione è 07789c58670ba212, la seconda
c43b19a521770daa. La seconda aveva ancora una didascalia isolata, risolta nella
versione finale. Le cartelle prima, seconda e finale conservano le anteprime.

La shell Windows ordinaria e il lettore immagini non erano avviabili per un
errore di preparazione del sandbox. Sono stati usati i comandi locali WSL
autorizzati e la lettura delle immagini renderizzate. Non sono stati avviati
esperimenti, modelli o compilazioni quantistiche.

L'aggiornamento graphify sulla radice ha tentato di analizzare anche le
dipendenze (166424 file non in cache). È stato interrotto prima della
pubblicazione; è stata avviata la procedura AST incrementale sui cinque
sorgenti Python modificati del report.

Il controllo conclusivo del grafo conferma che graph.json e GRAPH_REPORT.md
contengono i cinque sorgenti aggiornati, incluse le nuove funzioni dei pannelli
e la verifica della soglia. Il passaggio successivo di rigenerazione della
vista HTML è stato interrotto perché troppo lento; la vecchia vista HTML
non va usata come verifica di questa revisione. Il grafo interrogabile e
il rapporto testuale sono aggiornati.

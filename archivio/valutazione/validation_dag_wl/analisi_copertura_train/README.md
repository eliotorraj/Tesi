# Copertura WL dei circuiti train

Questa analisi misura quanti giri WL servono perché ciascun nodo possa ricevere
informazione iniziale da tutti gli altri nodi della stessa componente connessa.

L'implementazione WL aggiorna da predecessori e successori, conservandone il ruolo.
Per la sola distanza di propagazione basta quindi il grafo senza direzione.
Il diametro di una componente è la massima distanza minima fra due suoi nodi.
Archi paralleli non cambiano questa distanza. Restano tutti i nodi originali,
compresi ingressi, uscite, misure e barriere.

Si misura il massimo diametro delle componenti di ogni circuito.
Il massimo fra tutti i circuiti train è il limite superiore da includere
in una nuova esplorazione del parametro h per ottenere questa copertura.

## Dati e controlli

Il manifest contiene 422 elementi train, corrispondenti a 396 sorgenti QASM
distinti nell'indice RAG. Le identità sono controllate tramite gli hash dei file.
Ogni grafo viene anche ricostruito dal suo QASM e confrontato con quello
dell'indice congelato. Non vengono letti score validation o Test.

Il diametro è esatto: networkx.diameter con usebounds=True usa limiti inferiori
e superiori per accelerare il calcolo, non una stima approssimata.
Per tutti i circuiti che raggiungono il massimo, un secondo calcolo tramite
distanze da tutti i nodi conferma il risultato e conserva un percorso testimone.

Documentazione:
https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.distance_measures.diameter.html

## Riprodurre

Dalla radice del progetto, in WSL:

    .venv/bin/python archivio/valutazione/validation_dag_wl/analisi_copertura_train/calcola_diametri.py --output archivio/valutazione/validation_dag_wl/analisi_copertura_train/esecuzioni/diametri_v2

Usare una cartella di esecuzione nuova. Le esecuzioni esistenti non sono sovrascritte.
La cartella contiene avvio.json, circuiti.jsonl, diametri_train.csv,
riepilogo.json, testimoni_massimo.json e provenienza.json.

## Interpretazione e limiti

La copertura non garantisce una rappresentazione completa o univoca della struttura.
WL può ancora confondere grafi differenti e ulteriori giri possono cambiare
le etichette anche dopo la copertura. Il parametro migliore per il recupero
deve essere valutato sulla validation.

La soglia riguarda solo il train. Non certifica la copertura di validation,
Test o circuiti futuri. Eventuali componenti scollegate non comunicano
a nessun numero di giri.

Questa analisi non avvia inferenza LLM o compilazioni quantistiche.
Non modifica l'indice, la configurazione selezionata h=24, i limiti dello script
di validation attuale o il grafo graphify.

## Risultato della prima misura

Il massimo è **h=110**, raggiunto da su2random_indep_tket_50:
50 qubit, 4.326 nodi, 207 livelli di dipendenza, diametro 110.
Il massimo è confermato anche dal calcolo indipendente delle distanze
fra tutte le coppie di nodi. Tutti i 396 grafi risultano connessi.

| Giri | Sorgenti distinti coperti | Elementi train coperti |
| --- | --- | --- |
| 24 | 360/396 (90,9%) | 376/422 |
| 30 | 375/396 (94,7%) | 395/422 |
| 110 | 396/396 (100%) | 422/422 |

Il diametro minimo è 5; la mediana è 10.
Il circuito con profondità maggiore non è necessariamente quello con
diametro maggiore: il diametro misura distanze minime, non il cammino diretto
più lungo.

110 è la soglia minima uniforme che garantisce la copertura definita qui
per l'intero train. Non è un limite oltre il quale WL smette necessariamente
di cambiare, né una garanzia di qualità. Per la prossima validation si può
includere h=110 come estremo della ricerca; gli script sperimentali attuali
mantengono il precedente limite h=30.

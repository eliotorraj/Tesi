# Salvataggi intermedi RL

[Indice dell’esperimento](../README.md)

Durante l’addestramento RL il programma può salvare lo stato del modello.
Questi salvataggi permettono di riprendere un lavoro interrotto senza
ripartire da zero.

La struttura è `rl/<dispositivo>/<esecuzione>/`.
Gli archivi ZIP rappresentano lo stato della politica; gli eventuali
metadati associati identificano il salvataggio e le condizioni della prova.
Un file con suffisso `latest_rollout` indica un punto di ripresa
registrato dal programma.

Alcuni salvataggi Quantinuum sono stati trasferiti su D:.
La presenza della directory locale non prova che i file siano ancora
disponibili al suo interno: prima di una ripresa va controllato il percorso
effettivo. Il modello finale di riferimento si trova in
[models/](../models/README.md).

Questa guida non modifica i salvataggi o i collegamenti esistenti.

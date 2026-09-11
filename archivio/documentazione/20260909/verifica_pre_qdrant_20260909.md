# Verifica prima di Qdrant — 9 settembre 2026

## Esito

Possiamo passare all'integrazione di Qdrant. I problemi del parser, del
catalogo hardware e dei piani sperimentali sono stati corretti.
Qdrant non è stato installato e nessun esempio è stato indicizzato.
Il test sperimentale resta chiuso.

## Decisioni adottate

- Manteniamo la distanza tra i vettori di 49 feature. Un'altra euristica
  potrà essere confrontata in seguito.
- Ogni esempio conserva il solo dispositivo vincente e le sue configurazioni.
  Non aggiungiamo due dispositivi ulteriori e non bilanciamo le etichette.
- Se i vincoli escludono tutti i vincitori storici, il sistema può proseguire
  dichiarando che non dispone di evidenze storiche per quella richiesta.
- Conserviamo i due esempi train equivalenti. Possono dare più peso a un
  precedente nel recupero, ma non duplicano osservazioni nella valutazione.
  Questa ridondanza è accettata; non è una prova che ogni possibile
  quasi-duplicato del corpus sia stato escluso.

## Correzioni

Il parser usa le istruzioni OpenQASM riconosciute dalla pipeline del Dataset.
Restano i controlli che consentono soltanto l'include Qiskit `qelib1.inc`.

Il prototipo usa il catalogo v2. Le impronte hardware provengono dalla stessa
funzione usata dal Dataset. Versioni o Target diversi da quelli congelati
producono un errore di integrità. Il contratto del catalogo hardware passa a
`2.0.0`: le richieste devono usare lo snapshot corrente.

I piani validation e test usano 100 secondi e 6 processi. Non sono cambiate le
264 e 270 estrazioni casuali. Gli originali e il resoconto del riallineamento
sono nella directory `plans/history/` dell'esperimento. La procedura è ripetibile
con l'opzione `--align-execution-policy` dello script 11. Non ammette altri
cambiamenti e si blocca se il test è già aperto.

## Verifiche eseguite

| Verifica | Esito |
| --- | --- |
| Suite automatica | 149 test superati |
| Lettura dei circuiti reali | 422 train e 88 validation, senza errori |
| Feature del prototipo rispetto al Dataset | Nessuna differenza rilevata |
| Impronte Target | Tutte e cinque coincidono con quelle v2 |
| Stabilità dello snapshot tra processi | Verificata |
| Ricerca, evidenze e prompt sui casi validation | 88 su 88 riusciti, senza chiamare LLM |
| Esempi accettati dal registro delle evidenze | 396 su 396 |
| Audit dei piani validation e test | Entrambi conformi |
| Matrice Qiskit validation | 15048 tentativi, 5016 aggregati |
| Separazione dei dati RAG | 396 esempi train, nessun hash di validation o test |

Il Dataset globale conserva 87120 tentativi: 82621 successi e 4499 timeout.
Non sono state ripetute compilazioni o modificate etichette, punteggi e split.

## Lavori successivi

L'integrazione di Qdrant dovrà applicare la lista ammessa degli hash train e
verificare versione del Dataset, catalogo e Target. I 396 esempi esistenti sono
la sorgente; validation e test restano esterni all'indice.

La distanza corrente normalizza ogni componente rispetto alla coppia di
vettori. Non coincide direttamente con euclidea o coseno sui vettori grezzi:
l'integrazione dovrà conservarla oppure rendere esplicita una nuova scelta.

Prima dell'esperimento finale restano necessari modelli RL/ML verificati,
prova di qcompile, scelta e congelamento degli LLM e valutazione finale.
L'audit di apertura del test segnala ancora questi requisiti mancanti su questa
macchina. Non impediscono di lavorare su Qdrant.

Con le regole attuali, solo 18 degli 88 circuiti validation hanno tutte le
compilazioni riuscite e quindi un oracle disponibile. I confronti sul regret
dovranno riportare il numero effettivo di casi utilizzabili.

# Oracle separato dei 90 circuiti Test

Questo programma misura il massimo noto nello spazio Qiskit dell'esperimento.
Non sceglie un nuovo modello e non modifica RAG, prompt, Dataset o Training set.
I risultati sono scritti fuori dal progetto. La generazione va avviata dall'utente.

## Quale riferimento esisteva prima

Gli aggregati correnti contengono:
- 24.024 coppie circuito/dispositivo/configurazione train, su 422 circuiti;
- 5.016 coppie validation, su 88 circuiti;
- nessuna coppia Test.

Il regret della validation è calcolato rispetto alla migliore **mediana** tra
le coppie compatibili con tutti i seed 0, 1 e 2 riusciti.
Il riferimento osservato esiste per 88/88 circuiti; la matrice è completa per
18/88. Negli altri 70 casi il riferimento è parziale.
La validation WL usa questi stessi aggregati.

I report correnti sui 90 Test confrontano gli score delle singole esecuzioni.
Non usano una matrice esaustiva Test già disponibile negli aggregati correnti.
Gli esiti dei sistemi e i dati storici v1 non sono importati da questo programma.
Il piano Test ammette un riferimento osservato facoltativo, esterno ai metodi.

Le fonti precise e il conteggio sono in stato_riferimento_attuale.json.

## La nuova etichetta richiesta: massimo, non mediana

Per ogni circuito c e ogni coppia dispositivo/configurazione p:

    etichetta(c, p) = max(score(c, p, seed=0),
                          score(c, p, seed=1),
                          score(c, p, seed=2))

Il riferimento del circuito è:

    oracle(c) = max(etichetta(c, p) per tutte le coppie compatibili)

Le parità conservano tutte le coppie e tutti i seed vincenti.
Non si sceglie il primo seed né la mediana dei tre.
La validation precedente conserva il suo criterio originale.

Un errore, timeout o interruzione è un dato mancante, non uno score zero.
Se soltanto alcuni seed riescono, il massimo disponibile viene conservato.
Un riferimento è dichiarato esaustivo soltanto quando **tutte** le compilazioni
compatibili dei tre seed sono riuscite. Aver terminato tutti i tentativi
non significa aver ottenuto una matrice completa di score.

## Piano congelato

- I 90 circuiti Test e i loro SHA-256 dal manifest corrente.
- I cinque Target sintetici: IBM Falcon 27 e 127, IBM Heron 133 e 156,
  Quantinuum H2 56.
- Le dodici configurazioni del catalogo train/validation.
- Seed transpiler 0, 1 e 2.
- expected_fidelity MQT Predictor 2.4.0, arrotondata a dieci decimali.
- Python 3.12, Qiskit 2.5.0, MQT Bench 2.2.3 e NumPy 2.5.1.
- approximation_degree=1.0 e num_processes=1.
- Sei compilazioni esterne contemporanee per impostazione predefinita.
- Limite di 100 secondi per tentativo.

La matrice ha **16.200 celle**: 90 × 5 × 12 × 3.
Di queste, **15.336** richiedono compilazione; **864** sono incompatibili
per il numero di qubit e vengono registrate senza invocare il compilatore.

| Dispositivo | Compilazioni |
| --- | ---: |
| ibm_falcon_27 | 2.592 |
| ibm_heron_133 | 3.240 |
| ibm_falcon_127 | 3.240 |
| ibm_heron_156 | 3.240 |
| quantinuum_h2_56 | 3.024 |

Il controllo iniziale verifica file, versioni, opzioni e impronte dei Target.
Le copie dei cataloghi archivio/prototipo hanno la stessa griglia e gli stessi
parametri; differiscono nella lista delle dipendenze, ridotta nel prototipo.

Il calcolo di fedeltà e il controllo del circuito compilato sono quelli del
Test corrente. Ogni compilazione viene eseguita in un processo nuovo.
Il limite comprende caricamento QASM/Target, compilazione, validazione,
calcolo dello score e salvataggio QASM. Come nel generatore train/validation,
gli import iniziali sono esterni ai 100 secondi. Un controllo separato ferma
un avvio bloccato dopo 60 secondi. Un secondo controllo termina il processo
se il limite interno non risponde: il secondo aggiuntivo serve soltanto
a salvare l'errore, mai ad accettare uno score oltre 100 secondi.
I tempi di processo comprendono anche gli import.

Il ciclo di vita dei processi e il salvataggio differiscono dalla vecchia
raccolta con processi riutilizzati. I tempi non sono repliche identiche dei
tempi train/validation. Le variabili dei thread riprendono il Test corrente
e sono registrate nel contratto. Memoria ed energia non sono misurate.

## Dove vengono salvati i risultati

Percorso predefinito in questo ambiente:

    /home/elio/oracoli_mqt_test/test_max3_v1

Il programma rifiuta percorsi interni al progetto o ad altre repository,
anche se ottenuti tramite un collegamento simbolico della cartella di output.
Non aggiorna il grafo graphify e non crea copie dei risultati nel prototipo.
Nessun sistema di selezione viene modificato per leggere questa cartella.

Questa è la separazione dalle pipeline scelta dall'utente.
Non è un divieto di accesso per altri programmi avviati dallo stesso utente Linux.
La cartella va usata per l'analisi successiva, non inserita fra le fonti RAG.

## Comandi, dalla radice del progetto in WSL

Controlli senza scrivere risultati e senza compilare:

    .venv/bin/python archivio/valutazione/oracle_test/genera_oracle_test.py --verifica

Preparazione facoltativa: congela il piano e copia i QASM, senza compilare:

    .venv/bin/python archivio/valutazione/oracle_test/genera_oracle_test.py --prepara

Avvio della generazione:

    .venv/bin/python archivio/valutazione/oracle_test/genera_oracle_test.py --esegui

Lo stesso comando riprende la campagna dopo una interruzione.
È possibile specificare un'altra cartella esterna con --output.
Per usare meno processi, aggiungere ad esempio --workers 3 fin dalla preparazione.
La quantità di processi fa parte del contratto e non può cambiare nella stessa
campagna. I risultati di campagne differenti non vengono mescolati.

Per creare un nuovo riepilogo senza eseguire compilazioni:

    .venv/bin/python archivio/valutazione/oracle_test/genera_oracle_test.py --analizza

Non lanciare altre campagne pesanti durante la misura dei tempi.
Non occorre avviare il server LLM né caricare modelli MQT addestrati.

## Interruzioni e ripresa

Ogni tentativo conserva la propria identità prima di iniziare.
Uno stesso output non può essere usato contemporaneamente da due generatori.

- Successi, errori e timeout già salvati vengono saltati.
- Un tentativo iniziato senza esito viene conservato come interrotto e non ripetuto.
- Una risposta del processo già pubblicata integralmente viene recuperata.
- I tentativi non ancora iniziati proseguono alla ripresa.
- Nessun --force o nuovo seed viene usato per ottenere un risultato migliore.
- Un cambio di codice, dati, Target, versioni o contratto blocca la ripresa.

Dopo Ctrl+C i processi attivi sono fermati e viene prodotto un riepilogo parziale.
Anche una chiusura improvvisa del supervisore termina i suoi processi diretti
tramite la protezione Linux sul processo padre.
Un'interruzione può quindi lasciare la matrice incompleta; è un esito dichiarato.

## File esterni prodotti

- contratto.json: dati, catalogo, versioni, impostazioni, hash del codice e piano.
- sorgenti/: copie verificate dei 90 QASM.
- provenienza/: copie del codice usato.
- sessioni/: avvii, fine e interruzioni.
- tentativi/<id>/: inizio, seed, configurazione, tempi delle fasi, diagnostica,
  stdout/stderr, QASM compilato e risultato durevole.
- analisi/<data_id>/riepilogo.json: copertura e stati.
- analisi/<data_id>/oracle_test.json e .csv: massimo noto per ciascun circuito.
- analisi/<data_id>/configurazioni.json: tutti i massimi per coppia e gli score dei tre seed.
- analisi/<data_id>/tentativi.csv: matrice completa, anche incompatibilità e dati mancanti.
- analisi/<data_id>/provenienza.json: hash degli esiti letti.

Ogni analisi crea una nuova cartella. Gli esiti precedenti non vengono sovrascritti.
Il campo principale è reference_score; reference_is_exhaustive segnala la copertura.
best_seed0_score è soltanto un riferimento secondario, utile per confrontare
le esecuzioni LLM che usavano seed 0. Non sostituisce il massimo sui tre seed.

## Confronto successivo con i sistemi

Lo scarto è:

    scarto = reference_score - score_del_sistema

Non va tagliato a zero. Un valore negativo indica che il sistema ha superato
il massimo della griglia osservata.
Questo è possibile per MQT Predictor: il compilatore RL può produrre sequenze
diverse dalle dodici configurazioni Qiskit. L'oracle non è un massimo assoluto
fra tutti i compilatori possibili.

Il massimo di tre seed è un riferimento ottimistico rispetto alla singola
compilazione dei sistemi Test. Tale differenza va dichiarata nei confronti.
Su matrici incomplete, anche un massimo osservato è soltanto un limite
inferiore del miglior risultato che potrebbe esistere nella griglia.

## Verifiche svolte prima della consegna

Sono stati eseguiti il controllo statico completo e i test di sviluppo.
I test usano dati fittizi, un compilatore simulato e un semplice processo
in attesa per verificare la terminazione per timeout.
**Non è stata eseguita alcuna compilazione quantistica dell'oracle.**

Per ripeterli:

    .venv/bin/python -B archivio/valutazione/oracle_test/test_oracle.py

I registri delle verifiche sono in verifiche_sviluppo/.

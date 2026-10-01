# Scelta della similarità DAG/WL

Questa campagna usa esclusivamente gli **88 circuiti validation** per confrontare
il recupero Manhattan attuale con WL a **tutti gli interi da 1 a 30 iterazioni**, sempre con **5 esempi**.
Gli esempi provengono dai 396 record train già distribuiti col prototipo.
Non chiama l'LLM e non compila circuiti. Riutilizza gli aggregati validation
congelati dello stesso esperimento, verificati tramite il sigillo local-llm-v2.
Non legge score Test.

È una misura indiretta della qualità del recupero. Non sostituisce il confronto
finale fra i due sistemi LLM. Gli stessi esempi possono aiutare il modello in
modo diverso dal semplice trasferimento della prima configurazione.

## Estensione fino a 30 iterazioni

Le campagne wl_v1 (h=1..3) e wl_v2 (h=1..6) restano intatte.
La nuova campagna wl_v3 prova tutti gli interi h=1..30, sempre con k=5,
oltre a Manhattan. Ha indice e contratto propri. L'estensione è stata chiesta
dopo aver letto wl_v2: è una validation adattiva sugli stessi 88 casi.
La rappresentazione, le etichette, la formula e la sintesi non cambiano.
Nessun h è scelto automaticamente. Le revisioni precedenti dei sorgenti
e le impronte dei risultati sono conservate in revisioni_codice/.
Non riprendere wl_v1 o wl_v2 con il codice esteso: i contratti rifiutano
correttamente di mescolare revisioni.

Gli istogrammi WL vengono costruiti una volta fino a 30 e poi riutilizzati.
Le graduatorie per ciascun h vengono calcolate separatamente, così le misure
di durata restano confrontabili con la procedura precedente; aumentano tempo
totale, dimensione degli indici e memoria richiesta. Non si interrompono
le iterazioni anticipatamente. Il report usa una curva per h=1..30, una
linea di riferimento Manhattan e una tabella su più pagine.

## Comandi iniziali

Dalla radice della repository, in Ubuntu/WSL:

~~~bash
.venv/bin/python archivio/valutazione/validation_dag_wl/valida.py --verifica
.venv/bin/python archivio/valutazione/validation_dag_wl/valida.py --esegui --run-id wl_v3
~~~

Non servono server, GPU o percorso GGUF. Usare un solo processo per campagna.
Il secondo comando costruisce il proprio indice train e registra tutti gli 88
casi. Lo stesso comando riprende i casi non iniziati. Gli errori e le interruzioni
restano conservati: non si ripetono di nascosto. Dopo averne corretto la causa,
usare un nuovo run-id, per esempio wl_v4; il codice cambiato impedisce la ripresa
mescolata di una campagna precedente.

I file da discutere sono:

- esecuzioni/wl_v3/riepilogo.json: tutti i denominatori e le statistiche;
- esecuzioni/wl_v3/confronto.csv: tabella compatta;
- esecuzioni/wl_v3/report_validation.tex: documento autonomo con tabella e grafico;
- esecuzioni/wl_v3/circuiti/: DAG, ordinamenti completi ed esiti per circuito;
- esecuzioni/wl_v3/contratto.json: parametri, codice e fonti congelati;
- esecuzioni/wl_v3/indice/: indice train privato della validation.

## Cosa viene misurato

Il primo indicatore trasferisce sul circuito validation la coppia dispositivo /
configurazione in posizione 1 dell'esempio recuperato per primo. Lo score è la
mediana dei seed 0, 1, 2 già eseguiti sul circuito validation.

Il regret è la differenza rispetto al migliore score osservato fra le coppie
compatibili con tutti e tre i seed riusciti. Il riferimento non è un ottimo
esaustivo quando la matrice contiene timeout. Le matrici incomplete sono contate.

Una coppia con seed incompleti non riceve uno score zero: resta non osservabile.
Il riepilogo presenta sia i denominatori di ciascun metodo sia mean e median
del regret sugli stessi circuiti osservabili in tutti e 31 i metodi.
Le coperture devono essere lette prima delle medie.

Il secondo indicatore guarda la migliore coppia osservata nell'unione delle
configurazioni mostrate dai cinque esempi, incluse le parità esplicitamente
mostrate. È un indicatore ottimistico della disponibilità di buoni suggerimenti:
**non è lo score dell'LLM**, e non è una regola di scelta che potrà consultare
gli score del circuito corrente. La graduatoria degli esempi viene salvata prima
del calcolo di questi indicatori.

Si registrano anche tempi del confronto, costo separato del DAG/WL e dimensioni
relative degli esempi. Le durate del recupero Manhattan qui misurano il calcolo
esatto delle stesse distanze, senza l'avvio e le verifiche Qdrant; non sono i tempi
completi della vecchia pipeline. Il costo dell'indice è separato e non va nascosto.
Gli istogrammi dei passi 0..30 sono costruiti insieme e conservati per riprodurre
il confronto; anche gli avvii Test conservano tutti questi passi. Il tempo di questa
preparazione comune non rappresenta tre misure separate del costo di costruzione.

## Parametri fissati prima della validation

La griglia varia solo h = 1, 2, ..., 30; si sommano sempre i contributi 0..h.
Il kernel è normalizzato, senza correzione aggiuntiva per la dimensione.
Le porte del QASM originale non vengono decomposte né ottimizzate.
I nodi di ingresso/uscita, i qubit inattivi, le misure e le barriere sono conservati.
Le etichette delle porte includono nome, arità, stato dei controlli e parametri
numerici discretizzati in intervalli di pi/8, arrotondati al più vicino con
parità lontano dallo zero, senza riduzione periodica. È una scelta ingegneristica
fissa, non selezionata sui Test. I parametri originali sono salvati nel DAG.
Non è una prova di equivalenza funzionale.

Gli archi sono diretti e multipli. Le etichette degli archi distinguono filo
classico/quantistico e posizione locale degli operandi alle due estremità.
La posizione assoluta del qubit non entra nelle etichette; le porte barriera
usano un ruolo simmetrico. Le etichette WL sono SHA-256 di descrizioni canoniche,
condivise fra tutti i grafi. Il confronto usa i conteggi di queste etichette,
non la distanza fra stringhe hash.

La ricerca considera tutti i record train con gli stessi filtri di esperimento,
obiettivo e dispositivo vincente compatibile usati dal metodo classico.
Le parità sono ordinate per rag_id. Nessun candidato viene prefiltrato con Manhattan.

## Dopo la discussione dei risultati

Nessun h viene scelto automaticamente. Confrontare prima la copertura, poi regret
medio e mediano sui circuiti comuni, disponibilità di buone coppie nei cinque
esempi e costi. A risultati equivalenti preferire h più piccolo. La decisione
finale e la motivazione vengono registrate esplicitamente.

Solo dopo la discussione, sostituire H_SCELTO con un intero da 1 a 30:

~~~bash
.venv/bin/python archivio/valutazione/validation_dag_wl/valida.py \
  --congela --run-id wl_v3 --h H_SCELTO \
  --motivazione "Motivazione concordata dopo la lettura della validation"
~~~

Il comando crea selezioni/wl_v3/wl_hH_SCELTO.json, senza sovrascrivere.
Richiede tutti gli 88 casi riusciti e lo stesso codice della validation.
Entrambi i nuovi Test devono usare esattamente questo file; nessun Test parte
senza una selezione valida. Le verifiche tecniche su Bell possono invece usare
un h provvisorio senza aprire il Test.

I Test restano estensioni sul corpus già esposto. La nuova validation non
rende quei 90 circuiti una nuova conferma indipendente.

## Fonti e verifiche

La variante diretta con ruoli degli archi è un adattamento per questa campagna.
Fonti: [WL, JMLR 2011](https://jmlr.org/papers/v12/shervashidze11a.html) e
[DAGCircuit Qiskit](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.dagcircuit.DAGCircuit).
Versioni software e Target restano quelle del protocollo corrente.

Verifiche di sviluppo, senza LLM e senza Test:

~~~bash
.venv/bin/python -m unittest discover \
  -s archivio/valutazione/test/verifiche -p test_dag_wl.py -v
~~~

I casi delle verifiche sono sintetici. I dati sperimentali della validation
non vengono generati da questa suite. Il grafo graphify non viene aggiornato.

Il report LaTeX viene generato a fine validation. Per compilarlo, dalla radice:

~~~bash
cd archivio/valutazione/validation_dag_wl/esecuzioni/wl_v3
pdflatex -interaction=nonstopmode -halt-on-error report_validation.tex
~~~

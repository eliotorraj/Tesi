# Oracle separato dei 50 circuiti QASMBench

Questi script preparano il riferimento per confrontare gli esiti LLM + RAG con il massimo osservato sui cinquanta circuiti esterni già selezionati. La generazione deve essere avviata dall'utente. Durante la preparazione sono stati eseguiti soltanto controlli e prove con dati fittizi.

## Avvio in WSL

Dopo la predisposizione su questo computer:

```bash
bash /home/elio/oracoli_qasmbench_test/avvia.sh
```

Il comando genera o riprende l'oracle e, al termine, produce automaticamente il confronto LaTeX con gli esiti RAG QASMBench già presenti. Non occorre avviare il server LLM né caricare modelli MQT addestrati.

Il comando equivalente, dalla radice della repository, è:

```bash
.venv/bin/python -B riproducibilita/test/oracle_qasmbench/genera_oracle_test.py --esegui
```

L'ambiente utilizzato è quello completo già presente nella repository: Python 3.12, MQT Predictor 2.4.0, Qiskit 2.5.0, MQT Bench 2.2.3 e NumPy 2.5.1. Non ricreare l'ambiente o i modelli per questa attività.

Per controllare i requisiti senza generare risultati:

```bash
bash /home/elio/oracoli_qasmbench_test/avvia.sh --verifica
```

`--prepara` congela il contratto e copia i QASM, senza compilare. `--esegui --workers 3` riduce i processi: il valore va scelto prima del congelamento e mantenuto alla ripresa. Il valore predefinito è sei. `--output /percorso/esterno/nuova_campagna` sceglie una destinazione diversa. La destinazione deve restare esterna alle repository.

## Metodo e provenienza

I sorgenti sono le copie originali distribuite in `riproducibilita/circuiti/esterni/qasmbench/`: 30 piccoli, 15 medi e 5 grandi. L'impronta del manifest è la stessa del Test QASMBench già svolto. Si verifica ogni QASM e il numero di qubit. Non si scaricano o rigenerano i circuiti.

La griglia è quella dell'oracle dei 90 Test: cinque Target sintetici, dodici configurazioni e seed 0, 1 e 2. Il catalogo locale è una copia fissata, verificata per SHA-256; non segue eventuali modifiche delle configurazioni di altri esperimenti. I Target vengono verificati tramite impronta e capacità.

La matrice contiene **9.000 celle**, di cui **8.604 compilazioni compatibili** e **396 incompatibilità**:

| Target | Compilazioni |
| --- | ---: |
| ibm_falcon_27 | 1.620 |
| ibm_heron_133 | 1.764 |
| ibm_falcon_127 | 1.764 |
| ibm_heron_156 | 1.800 |
| quantinuum_h2_56 | 1.656 |

Per ogni coppia si prende il **massimo** degli score riusciti dei tre seed, poi il massimo tra coppie. Non si usa la mediana. Tutti i pari merito sono conservati. Errori, timeout e interruzioni restano dati mancanti; uno score zero valido rimane zero. Il riferimento è esaustivo soltanto se tutte le compilazioni compatibili sono riuscite.

Si mantengono `approximation_degree=1.0`, `num_processes=1`, il limite di 100 secondi e un processo nuovo per tentativo. Gli import iniziali sono esclusi dal limite, con controllo separato dell'avvio a 60 secondi. Si conservano score arrotondato a dieci decimali, log-score, tempi, errori, QASM compilato e impronte. Memoria ed energia non sono misurate.

Il generatore importa soltanto componenti del kit operativo. L'archivio viene letto esclusivamente dall'analisi per confrontare gli esiti RAG storici: non si importano i vecchi runner e non si riesegue l'LLM. `provenienza_codice.json` registra la derivazione dal generatore e dal confronto dei 90 Test.

## Risultati e ripresa

La destinazione predefinita è `/home/elio/oracoli_qasmbench_test/qasmbench50_max3_v1` (più in generale, `~/oracoli_qasmbench_test/qasmbench50_max3_v1`). È separata dall'oracle MQT Bench dei 90 circuiti.

- `contratto.json`, `sorgenti/` e `provenienza/`: impostazioni e copie degli ingressi e del codice.
- `sessioni/` e `tentativi/`: avvii, esiti, diagnostica e circuiti compilati.
- `analisi/<data_id>/`: massimi, copertura, configurazioni, CSV dei tentativi e impronte degli esiti.
- `analisi/<data_id>/confronto_llm_rag_k5/risultati/`: confronto LaTeX, `dati.json`, `confronto_50_circuiti.csv`, provenienza e grafici TikZ autonomi.

Ripetere il comando iniziale riprende soltanto i tentativi mai iniziati. Successi, errori, timeout e interruzioni non vengono ripetuti. Un risultato già pubblicato dal processo viene recuperato. Due generatori non possono usare contemporaneamente la stessa campagna. Un cambio di sorgenti, codice, versioni, Target o impostazioni blocca la ripresa, senza sovrascrivere i risultati precedenti.

Ogni analisi crea una nuova cartella. Per rifare soltanto riepilogo e confronto, anche dopo un'interruzione:

```bash
bash /home/elio/oracoli_qasmbench_test/avvia.sh --analizza
```

Il confronto verifica gli hash degli esiti oracle, ricalcola tutti i massimi e la copertura e controlla le fonti RAG, il recupero k=5, le decisioni, gli score, i Target e le versioni condivise. Tiene conto della normalizzazione CRLF/LF effettuata dal runner RAG storico. I riepiloghi da soli non vengono considerati una prova sufficiente.

Se il confronto non riesce, gli esiti oracle e la nuova analisi restano conservati; il programma esce con codice 2. Correggere l'accesso agli esiti RAG e ripetere `--analizza`, senza ricompilare. `--rag-root` permette di indicare una copia integra della cartella storica `test_qasmbench`.

## Documento del confronto

Il nome è `confronto_oracle_rag5.tex`. La struttura riprende il documento dei 90 circuiti: sintesi e definizioni; scarto della coppia e del seed; dieci scarti maggiori ed esempi; grafici per tutti i circuiti; tabelle complete; fonti, controlli e limiti. Con cinquanta circuiti sono previste due pagine di grafici e due di tabelle, con un massimo di trenta righe per pagina. Non si trasferiscono valori o conclusioni del vecchio confronto.

Lo scarto è `R - S`, senza tagliare i valori negativi. La scomposizione usa `R - P` e `P - S`, dove P è il massimo osservato della coppia scelta. Il rapporto relativo non è definito quando R è zero. Si dichiarano i denominatori effettivi; circuiti mancanti o falliti restano nelle tabelle. La riproduzione dello score al seed 0 viene verificata: differenze fra esecuzioni non sono attribuite automaticamente al solo seed.

Il massimo di tre seed favorisce l'oracle rispetto alla singola compilazione RAG. Una griglia incompleta fornisce soltanto un massimo osservato. La selezione da una fonte esterna non esclude equivalenze semantiche con MQT Bench o presenza nel preaddestramento dell'LLM.

Il LaTeX è autonomo, con grafici TikZ incorporati. Per ottenere il PDF dopo la generazione, entrare nella cartella `risultati` stampata dal comando e usare `pdflatex -interaction=nonstopmode -halt-on-error confronto_oracle_rag5.tex` due volte. Non sono necessarie immagini esterne.

## Verifiche di sviluppo

```bash
.venv/bin/python -B riproducibilita/test/oracle_qasmbench/test_oracle.py
.venv/bin/python -B riproducibilita/test/oracle_qasmbench/test_confronto.py
```

I test usano dati fittizi e un compilatore simulato. Il controllo del timeout usa anche un semplice processo in attesa. Nessuna compilazione quantistica oracle viene avviata. In `verifiche_sviluppo/` restano i registri e un'anteprima fittizia, contrassegnata su ogni pagina, che serve soltanto a controllare l'impaginazione. Non è un risultato sperimentale.

Il grafo graphify non viene aggiornato. I risultati non vengono aggiunti al Dataset, al Training set o al recupero RAG.

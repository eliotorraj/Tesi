# Ulteriore test indipendente su QASMBench

Questa cartella prepara un nuovo confronto fra **LLM + RAG** e **MQT Predictor**.
Contiene 50 circuiti sorgente di QASMBench: **30 piccoli, 15 medi e 5 grandi**.
Il test non è stato avviato durante la predisposizione. Entrambi gli avvii hanno superato i controlli preliminari; il solo selettore MQT è stato anche verificato su un Bell sintetico.

| Fascia QASMBench | Numero | Quota | Qubit nella selezione |
| --- | ---: | ---: | --- |
| Piccoli | 30 | 60% | 2–10 |
| Medi | 15 | 30% | 11–27 |
| Grandi | 5 | 10% | 28, 63, 98, 111, 140 |

Fonte: [PNNL QASMBench](https://github.com/pnnl/QASMBench), revisione
`357b942396d5c2b7cbc1c229c585a6ef5ccaebac`.
I file sono copie originali, non varianti già compilate.
Il manifest e `selezione.csv` elencano nomi, fascia, qubit, profondità, operazioni, provenienza e SHA-256.
Licenza, NOTICE e documentazione della fonte sono in `circuiti/`.

## Criteri e limiti della selezione

La selezione è ragionata e precede gli score. Include famiglie diverse: aritmetica,
ricerca, trasformata di Fourier, simulazione, reti neurali e preparazione di stati.
Si scelgono circuiti statici leggibili dall'ambiente fissato del progetto.
I grandi restano entro i 156 qubit del Target più capiente; quattro superano 56 qubit.
Non sono rappresentati tutti i circuiti di QASMBench né i suoi casi con milioni di gate.

Quattro candidati sono stati esclusi per incompatibilità statica, non per lo score:
`inverseqft_n4` e `square_root_n18` contengono operazioni dinamiche;
`bb84_n8` riutilizza qubit dopo misure; `vqe_uccsd_n4` usa un registro
non definito alla riga 225. Copie e registri sono in `verifiche/`.
I sostituti sono adder_n10, gcm_n13 e sat_n7; bb84 era un sostituto intermedio.

Non ci sono file byte-identici fra i cinquanta né rispetto ai 600 circuiti del corpus MQT.
Questo controllo non esclude circuiti semanticamente equivalenti o algoritmi condivisi.
Non possiamo escludere QASMBench dal preaddestramento dell'LLM.
È un test esterno per fonte, non una prova di novità assoluta.

## Cartelle

- `circuiti/`: i cinquanta QASM originali e i documenti della fonte.
- `manifest.json`, `piano.json`: selezione e impostazioni della campagna.
- `llm_rag.py`, `mqt_predictor.py`: avvii indipendenti.
- `strumenti/`: controlli, registrazione, processi di compilazione e score.
- `runtime/`: copia del selettore ML scelto e dei metadati; da conservare nei backup.
- `preparazione/`: verifiche e contratto congelato al primo avvio.
- `prove_tecniche/`: prove sintetiche Bell, separate dai circuiti esterni.
- `risultati/<metodo>/`: esecuzioni, tentativi, prompt, risposte, tempi ed esiti.
- `report/`: spiegazione e destinazione delle analisi future.
- `verifiche/`: controlli di sviluppo e registro della preparazione.

Gli strumenti usano il framework in `prototipo/` e gli artefatti addestrati già presenti.
Non dipendono dai registri degli altri test e non ricopiano modelli voluminosi.
La derivazione iniziale degli strumenti è registrata in `provenienza_codice.json`.
Il codice congelato in `archivio/esperimento_v2/` rimane invariato.

## Verificare senza avviare il test

Eseguire dalla radice del progetto in WSL, con Python 3.12 dell'ambiente completo:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/prepara.py
.venv/bin/python archivio/valutazione/test_qasmbench/llm_rag.py --verifica
.venv/bin/python archivio/valutazione/test_qasmbench/mqt_predictor.py --verifica
```

`prepara.py` verifica i file già presenti; `--scarica` permette di recuperarli dalla
stessa revisione. Non sovrascrive file o manifest diversi.
`--verifica` conserva il controllo dei requisiti e non chiama l'LLM né compila i circuiti.
LLM e MQT hanno prerequisiti specifici: l'assenza dei modelli MQT non blocca LLM + RAG.

## Avviare quando si vuole eseguire il confronto

LLM usa Qwen3.5-4B Q8_0, temperatura 0, selezione local-llm-v2 e contratto 4.0.0.
Il RAG recupera cinque esempi dal solo train esistente.
Avviare prima il server locale secondo la guida corrente del prototipo.
Sostituire il percorso di esempio con quello del GGUF effettivamente usato:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/llm_rag.py --tecnico --model-path /percorso/Qwen.gguf
.venv/bin/python archivio/valutazione/test_qasmbench/llm_rag.py --esegui --model-path /percorso/Qwen.gguf
```

Il server predefinito è `http://127.0.0.1:8089`; si cambia con `--url`.
L'avvio controlla impronta del GGUF e contesto dichiarato dal server.

MQT usa Predictor 2.4.0, le cinque politiche RL esistenti e il **selettore corrente da 384 campioni**, scelto esplicitamente dall'utente. Una copia locale è in `runtime/`, con impronta e provenienza in `selettore_mqt.json`. Non viene installata nella `.venv`.

Questo è un **ulteriore test indipendente**. Il Training set del selettore copre 384 dei 396 campioni previsti, con 12 esclusi e 1.853 compilazioni riuscite sulle 1.878 coppie. La raccolta combina limiti di 100 e 300 secondi. Questi limiti sono riportati anche nei report. Il nuovo test QASMBench usa invece sempre 100 secondi per compilazione.
Le cinque prove RL e la prova completa su Bell devono riuscire con gli stessi modelli:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/mqt_predictor.py --tecnico
.venv/bin/python archivio/valutazione/test_qasmbench/mqt_predictor.py --esegui
```

I due metodi si avviano separatamente, preferibilmente in sequenza per confrontare i tempi.
Il primo avvio congela il contratto. Ripetere lo stesso comando riprende solo i circuiti
mai iniziati; errori, timeout e interruzioni restano esiti terminali.
Codice, piano, manifest e modelli diversi impediscono la ripresa mescolata.
Non cancellare i registri per ripetere casi sfavorevoli.

Si esegue una compilazione per circuito, con timeout esterno di 100 secondi.
Qiskit usa seed 0 e un processo. Anche il campionamento della politica MQT usa seed 0. La richiesta LLM ha timeout di 3600 secondi e al massimo
tre risposte complete, secondo le regole correnti. Non si usa un oracle per scegliere.
Lo score è expected_fidelity sui Target sintetici, arrotondato a 10 decimali;
si conserva anche il log-score per distinguere arrotondamento e underflow.
Questa misura non deriva da esecuzioni su hardware quantistico.

I registri conservano versioni, impronte, configurazioni, prompt, risposte, evidenze,
scelte, passaggi RL, tempi in secondi, chiamate e token quando misurabili.
La memoria di picco non è raccolta e viene dichiarata mancante.
Per generare il confronto in seguito usare `analizza.py`: [guida ai report](report/README.md).

# Protocollo della campagna incrementale

## Domanda e condizioni

Si valuta se gli esiti di compilazione raccolti durante l'uso mantengano o
migliorino la qualità delle decisioni successive. I pesi dell'LLM restano fissi.
La crescita riguarda il Dataset consultabile e non un nuovo addestramento.

Questa è una nuova valutazione sequenziale sui 90 circuiti Test MQT Bench già
esaminati. Non è una ripetizione del Test a Dataset congelato e non costituisce
un nuovo Test indipendente dalle scelte di sviluppo. Gli originali restano
invariati. Il confronto è ufficiale nelle condizioni qui dichiarate.

Il controllo consiste nei 90 esiti LLM + RAG con cinque esempi già registrati.
Non viene rieseguito. Il nuovo sistema mantiene Qwen3.5-4B Q8_0 a temperatura zero,
le dodici configurazioni Qiskit, i cinque Target sintetici e expected fidelity.
La compilazione usa seed 0 e limite iniziale di 100 secondi. La risposta ammette
al massimo tre tentativi, come il contratto facts v4. Un'ipotesi libera non è
certificata; una coppia ammessa con fatti non verificati può essere accettata
al terzo tentativo, dichiarandolo.

## Sequenza e separazione

Sono fissati quattro ordini: manifest, inverso, permutazione con seed 20261002
e permutazione con seed 20261003. Non vengono scelti dopo aver osservato gli score.
Ogni ordine parte dagli stessi 396 esempi train e da una propria memoria vuota.
Una sola decisione è attiva per volta; gli ordini vengono eseguiti in sequenza.

Prima di ciascuna decisione si recuperano cinque esempi dall'unione del train
originale e delle osservazioni concluse dello stesso ordine. La distanza è
Manhattan in precisione float64; le parità si risolvono per identificativo.
Logaritmo e divisori rimangono quelli del train originale. La ricerca è esaustiva
in memoria e riproduce il criterio canonico, senza modificare Qdrant nel prototipo.
Si applicano la compatibilità del dispositivo e l'esclusione dell'hash del
circuito corrente. Non si impone una quota tra esempi iniziali e incrementali.

Il nuovo circuito viene prima deciso, poi compilato e valutato, infine ammesso
alla memoria. La decisione non vede il proprio score. Nessuno score storico
del medesimo Test e nessun vincitore oracle entrano nella decisione o
nell'ammissione. I metadati conservano lo split originale test e dichiarano il
ruolo di osservazione passata del flusso; i record non sono rietichettati train.

## Ammissione

Si ammette un solo record per hash QASM non già presente. Occorrono una compilazione
riuscita, i controlli previsti del circuito e uno score finito fra zero e uno.
Non si applica una soglia di qualità assoluta. Una compilazione fallita o
interrotta resta nei registri e non aggiunge un esempio.

Ogni record conserva caratteristiche, dispositivo, configurazione, score,
seed, metrica, Target e provenienza. Descrive una sola coppia e un solo seed.
Non contiene la spiegazione generata dall'LLM e non attribuisce alla scelta
un rango o una mediana. Nel prompt le osservazioni sono distinte dagli esempi
originali, ottenuti confrontando alternative. Il fatto
`selected_pair_among_reported_best` non è sostenuto da una singola osservazione;
gli altri fatti v4 restano controllabili quando pertinenti.

La vicinanza tra circuiti e la riuscita tecnica non garantiscono che la scelta
sia buona per un altro circuito. La memoria può rafforzare preferenze errate
e le osservazioni ridondanti possono occupare il recupero. Questa prima campagna
misura anche tali effetti; non include nuove compilazioni per esplorare alternative.

## Registri e conservazione

Il contratto congela sequenza, modello, configurazione, dipendenze, Target,
trasformazione, fonti e codice. Si verificano gli artefatti selezionati
effettivamente usati. I vecchi prompt della validation non sono richiesti
per avviare questa nuova prova.

Per ogni posizione si salvano memoria precedente, recuperi e distanze,
prompt canonico e vista inviata, chiamate e risposte, verifiche dei fatti,
decisione prima della compilazione, circuito compilato, score, errori,
token e tempi. Un giornale con impronte collega i passaggi e le osservazioni.
La memoria per la ripresa viene ricostruita solo dai passaggi conclusi.

Errori, timeout e interruzioni non vengono sostituiti. Una ripresa completa
l'ammissione di un esito già salvato, oppure registra come interrotto un
tentativo senza esito finale. I file pendenti non diventano evidenza.
Le memorie dei quattro ordini e delle diverse campagne restano separate.

## Misure e interpretazione

L'unità è il circuito. Si riportano per ciascun ordine:
successi e fallimenti; score su coppie confrontabili; differenze per circuito,
media, mediana e peggioramento massimo; frequenza di miglioramenti, parità e
peggioramenti; crescita della memoria e casi che la usano; tempi e token
con i rispettivi denominatori. Un fallimento non riceve score zero.
Le parità sugli score arrotondati usano tolleranza 1e-12.

Il grafico cumulativo usa la differenza rispetto al controllo storico sullo
stesso circuito. I circuiti a una data posizione differiscono tra gli ordini.
Le quattro sequenze dipendono dagli stessi 90 circuiti e non diventano 360
osservazioni indipendenti. Non si calcolano intervalli che fingano indipendenza
tra tutti i passaggi, né si sceglie solo l'ordine migliore per la conclusione.

Se si fornisce l'oracle, lo scarto è massimo osservato meno score del sistema,
senza taglio a zero. Si conservano la provenienza del riepilogo e i denominatori
dei riferimenti completi e parziali. Il massimo di tre seed è favorevole
all'oracle rispetto alla singola esecuzione del sistema.

Il confronto con gli esiti storici non isola perfettamente il solo aumento
del numero di esempi: quando compaiono osservazioni cambia anche la loro
rappresentazione nel prompt. Inoltre cambiano data e gestione del recupero;
i tempi storici e nuovi non vanno presentati come misure simultanee in condizioni
identiche. Il caricamento iniziale e le verifiche della campagna restano fuori
dai tempi per circuito; l'esecuzione mantiene il corpus train caricato in memoria.
RAM, energia e temperatura non sono misurate da questi script.

Un miglioramento deve emergere dai nuovi esiti, includendo quelli sfavorevoli.
La maggiore vicinanza agli esempi, da sola, non dimostra maggiore qualità.

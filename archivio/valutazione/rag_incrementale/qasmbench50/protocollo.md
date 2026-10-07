# Protocollo della campagna incrementale QASMBench50

## Domanda e fonti

Si valuta se le osservazioni accumulate durante l'uso migliorano le decisioni
successive. Si riutilizzano i 50 sorgenti originali del Test QASMBench:
revisione PNNL `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`, 30 piccoli,
15 medi e 5 grandi. Il manifest è fissato da SHA-256. Ogni sorgente viene
verificato senza riscriverlo, anche quando contiene terminatori CRLF.

Questi circuiti sono già stati valutati. Questa è una nuova valutazione
sequenziale, non un nuovo Test mai esaminato. La fonte esterna non esclude
algoritmi condivisi, equivalenze semantiche o presenza nel preaddestramento.

## Impostazioni e sequenza

Qwen3.5-4B Q8_0 e configurazione selezionata local-llm-v2; temperatura zero;
contesto 60000; al massimo tre risposte complete; cinque esempi per richiesta.
Si usa la distanza Manhattan su 49 caratteristiche, con trasformazione fissata
sul train. La ricerca esatta considera i 396 esempi iniziali e le sole
osservazioni già concluse dell'ordine corrente.

I quattro ordini sono manifest, inverso e due permutazioni deterministiche
con seed 20261002 e 20261003. Le memorie partono vuote e non vengono unite.
I seed delle permutazioni non sono seed della compilazione.

Per ogni circuito: si fotografa la memoria, si recuperano gli esempi,
si registra la decisione, si esegue la coppia scelta e si salva l'esito.
La compilazione Qiskit usa seed 0 e limite esterno di 100 secondi, attraverso
lo stesso worker del Test QASMBench. La metrica è expected_fidelity sui
Target sintetici. Il log-score è conservato dal compilatore quando disponibile.

Dopo un esito riuscito, validato e con score finito in [0,1], si ammette
un'osservazione del circuito mai presente. Uno score zero valido viene ammesso.
Errori, timeout e interruzioni non vengono trasformati in esempi riusciti.
L'identità usa il contenuto del sorgente, non una prova di equivalenza semantica.

L'osservazione indica coppia, score e unico seed eseguito. Non contiene una
mediana, una classifica di coppie non provate o un'etichetta di ottimalità.
I controlli dei fatti consentono di distinguere il nuovo dato dagli esempi
train. Il prompt cambia quando recupera queste osservazioni.

## Registrazione e ripresa

I passaggi conclusi formano una sequenza verificata con impronte. La memoria
si ricostruisce soltanto da tale sequenza; non basta la presenza di un file.
Le osservazioni correnti o future sono escluse. Una memoria di un altro
ordinamento non è ammessa. Si conservano anche scelte sfavorevoli ed errori.

Una ripresa non ripete un tentativo già iniziato dall'esito incerto. Un esito
salvato prima dell'interruzione viene invece completato nel registro. Le
impronte di codice, dipendenze, configurazioni, train, Target e sorgenti
impediscono di mescolare campagne diverse.

## Confronti

Il controllo fisso riutilizza i cinquanta esiti LLM + RAG già conservati.
Per ogni ordine si misura S_incrementale - S_fisso sui successi comuni
alla coppia, dichiarando il denominatore. Tempi e token storici non sono
misure simultanee: anche la ricerca esatta differisce dall'indice storico.

L'oracle entra solo nell'analisi. Il report verifica i suoi 9.000 esiti,
i QASM compilati, i massimi per coppia e circuito, la copertura e le fonti
RAG storiche. Verifica anche Target, versioni e identità dei cinquanta circuiti.
Le analisi possono essere parziali; la copertura è sempre conservata.

R è il massimo osservato fra dispositivi e configurazioni compatibili e
seed 0, 1 e 2. Lo scarto è R-S, mantenendo il segno. La perdita relativa è
100(R-S)/R soltanto quando R è positivo. La parità usa tolleranza 1e-12.
Un oracle incompleto è un riferimento parziale; il massimo di tre seed
favorisce il riferimento rispetto alla singola esecuzione del sistema.

Le medie del confronto globale fra quattro ordini e controllo usano
l'intersezione dei loro successi. Per gli scarti si richiede anche l'oracle.
I sei confronti fra coppie di ordini usano ciascuno la propria intersezione.
Non si uniscono le 200 decisioni come osservazioni indipendenti. La posizione
nel flusso non identifica lo stesso circuito nei quattro ordini; i grafici
per circuito usano quindi un indice alfabetico comune.

I report conservano fallimenti, dati mancanti, denominatori, fonti e misure
per circuito. Memoria di picco ed energia non sono misurate. Crescita del
Dataset e maggiore copertura non dimostrano da sole un miglioramento:
il recupero può anche rafforzare scelte mediocri o sostituire esempi utili.

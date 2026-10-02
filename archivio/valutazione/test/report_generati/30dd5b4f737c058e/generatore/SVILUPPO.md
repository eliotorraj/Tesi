# Sviluppo del report Test - 23 settembre 2026

## Richiesta e scelta

Il selettore ML di MQT è ancora in preparazione su un'altra macchina. Si raccolgono
quindi i Test conclusi di LLM + RAG, LLM senza RAG e Random. Il report della
validation `local-llm-v2/report_explained/standalone.pdf` è il riferimento per
la spiegazione della procedura e per lo stile del documento.

Il vecchio generatore produceva un breve documento per sistema. Il confronto
produceva soltanto JSON. È stato aggiunto un generatore dedicato che usa gli
stessi esiti e il piano descrittivo già congelato. La nuova cartella è fuori
dall'elenco del codice vincolato dal contratto. Questa scelta evita di cambiare
il contratto solo per ampliare i documenti prima del Test MQT.

I registri originali e le analisi precedenti rimangono intatti. Non si avviano
Test, nuove chiamate LLM o compilazioni quantistiche. Le sole compilazioni
eseguite durante questo lavoro sono quelle dei documenti LaTeX.

## Che cosa viene aggiunto

Ogni sistema ha conteggi di successi e fallimenti, score, tempo totale, tempo
del compilatore e del processo. I due LLM hanno anche token in ingresso e uscita,
retry, chiamate e latenza cumulativa. Sono pubblicati dati per circuito e
aggregati, sempre con coperture. Eventuali repliche sono prima mediate per
circuito; le chiamate correttive restano nello stesso episodio.

Il documento comune spiega procedura, assunzioni, impostazioni, aggregazioni,
confronti appaiati e limiti. Aggiunge grafici descrittivi senza cambiare le
regole di scelta o il piano dei confronti. Le tabelle complete mantengono lo
stesso indice del circuito in tutti i documenti.

MQT viene incluso automaticamente quando il suo registro compatibile compare.
La verifica sintetica controlla che la sua aggiunta non cambi il precedente
confronto RAG-Random. I metodi incompleti conservano il conteggio dei pendenti.

## Dati osservati

I tre sistemi hanno 90 esiti ciascuno. RAG e senza RAG hanno 90 successi; Random
ha 80 successi e 10 timeout. I tempi interni dei dieci timeout sono mancanti,
mentre i tempi del processo e totali sono presenti. Il nuovo report non inventa
le misure interne. RAG ha 36 retry, senza RAG zero. Le somme dei token sono
rispettivamente 1480707 e 774754.

La media dello score sui successi è 0,79837881407 per RAG,
0,6347778020322222 senza RAG e 0,68266412515625 per Random.
Queste tre medie non hanno tutte lo stesso denominatore. Il documento
usa separatamente il confronto appaiato e dichiara i circuiti comuni.

## Controlli e problemi incontrati

L'avvio della shell nel sandbox Windows non funzionava. È stato usato WSL
tramite la shell autorizzata. La ricerca graphify ha individuato `summary()`
e `llm_metrics()` come punti iniziali per leggere il flusso delle misure.

La prima compilazione LaTeX si è interrotta per l'espansione dei caratteri
con font non scalabili. Il registro è conservato nella prima cartella di
prova sotto `report_generati/`. È stato corretto il preambolo, usando Latin
Modern e disattivando l'espansione. Il controllo successivo ha individuato
righe troppo larghe nella provenienza: sono stati abilitati gli a capo nei
percorsi e i parametri LLM sono diventati una tabella.

Le verifiche automatiche usano dati inventati: pesi uguali fra circuiti con
repliche diverse, fallimenti e interruzioni, misure parziali, zeri validi,
assenza di metriche LLM per Random/MQT, appaiamento, riproducibilità degli
intervalli, aggiunta di MQT e rifiuto di split, contratti o impronte errati.
Il controllo dei PDF comprende compilazione, ricerca di errori di impaginazione
e ispezione delle pagine renderizzate. Le versioni intermedie restano conservate.

Un controllo indipendente sui 180 episodi LLM ha ricalcolato token, numero di
chiamate, retry e latenza a partire da context.json, response_raw.json e timing.json.
Tutti i valori coincidono con gli esiti: 126 chiamate RAG e 90 senza RAG.
Il confronto tra code_files() e contratto_congelato.json non trova differenze.
La prima ispezione delle pagine ha suggerito di accorpare le tabelle dei tempi
e dei costi LLM nel confronto e di evitare un grafico dei retry isolato in una
pagina dei rapporti individuali. I retry restano nelle tabelle e nel grafico comune.

## Lettura del Test MQT separato - 24 settembre 2026

Il generatore legge ora MQT da `prototipo/test_mqt_esplorativo/` quando il registro
è presente. Gli altri tre sistemi mantengono la fonte originale. Si può indicare
un'altra area con `--mqt-area`. L'eventuale esecuzione MQT originale non viene
sommata a quella esplorativa.

La nuova fonte ha un contratto distinto. Il programma verifica il suo hash,
l'identità del manifest e dei circuiti e l'uguaglianza dei criteri di valutazione.
Le sole differenze ammesse nel piano sono l'identità della prova e le deroghe
esplorative dichiarate. I percorsi reali sono usati anche nel controllo finale
contro modifiche degli input durante la generazione.

I documenti e il JSON del confronto dichiarano la natura esplorativa. Il
selettore ha 384 campioni su 396; la raccolta train include recuperi a 300 secondi,
mentre il Test conserva il limite di 100 secondi. I 90 esiti MQT letti comprendono
75 successi e 15 timeout. Nessun registro è stato spostato o modificato e non
sono stati avviati modelli o Test. Il grafo non viene aggiornato.

Le nuove regressioni verificano scelta della cartella, assenza di doppio conteggio,
posizione precedente, percorso esplicito, fonti mancanti, contratti errati e
rifiuto di timeout, split o metrica diversi. I rapporti precedenti restano conservati.

## Struttura discorsiva e confronto a quattro pannelli - 24 settembre 2026

Il report complessivo è stato riorganizzato in quattro sezioni: introduzione,
sistemi, risultati e conclusioni. Le aspettative indicate dall'autore sono
presentate come aspettative di lavoro ricostruite nella revisione, senza
trasformarle in ipotesi preregistrate. Ogni sistema ha una descrizione delle
assunzioni e dei parametri; quelli del classificatore MQT sono letti dai
metadati conservati, inclusi nella provenienza della nuova analisi.

Tutti i riepiloghi vengono prima dei grafici. Ogni figura occupa una pagina
orizzontale, preceduta da una spiegazione. La griglia mantiene RAG e no RAG
sopra, MQT e Random sotto; gli assi sono uguali. I grafici delle misure LLM
conservano due celle esplicitamente non applicabili. Le torte dividono tutti
i 90 circuiti fra score almeno 0,8, score inferiore e assenza di score;
eventuali pendenti restano separati. I conteggi sopra soglia sono 70, 45, 65 e
44. Nessun fallimento riceve uno score fittizio.

Le conclusioni riportano 71 miglioramenti su 90 confronti con no RAG e 65 su
80 con Random. La copertura di 90 successi osservati non diventa una garanzia
generale. MQT ha il tempo medio totale maggiore, ma una mediana inferiore a
RAG. Si mantiene esplicita la natura esplorativa della sua prova. L'ampliamento
delle dodici configurazioni è una possibilità da verificare. La minore
necessità di addestramento specifico del RAG viene distinta da un confronto
quantitativo dei costi di preparazione, che questo Test non misura.

L'appendice separa le misure in tabelle leggibili, con nomi completi di sistemi
e circuiti. I conteggi effettivi non hanno decimali; le eventuali medie non
intere restano medie. Versioni, impronte e informazioni dell'ambiente sono
conservate nei dati di provenienza, senza lunghi registri tecnici nella prosa.

La prima generazione di verifica (07789c58670ba212) ha mostrato a capo
indesiderati nella griglia e intestazioni troppo larghe. La seconda
(c43b19a521770daa) ha corretto questi problemi; il controllo delle immagini
ha individuato una didascalia delle torte isolata. È stato ridotto lo spazio
vuoto dei pannelli delle torte e semplificata l'etichetta interna alle fette.
Le prove intermedie restano conservate in report_generati, così come il report
originale 675f715bb32595bf. Le anteprime di controllo sono sotto
report_generati/controlli/revisione_struttura/.

Le verifiche comprendono le regressioni del generatore, il controllo della
soglia inclusiva con score mancante, fallimento e caso pendente, e il confronto
dei riepiloghi e delle tabelle originali con quelli rigenerati. L'ispezione del
PDF verifica ordine delle sezioni, griglia, leggibilità e assenza di righe oltre
i margini. Sono compilati solo documenti; non si avviano Test o modelli.

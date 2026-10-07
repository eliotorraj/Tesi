# Report MQT Bench con il formato QASMBench

Il 3 ottobre 2026 il generatore del report sui 90 MQT Bench è stato adattato alla forma del report sui 50 QASMBench. Sono stati ripresi impaginazione, tabelle, grafici della distanza dall’oracle e confronti fra i quattro ordinamenti. I dati provengono soltanto dalle campagne MQT Bench.

Ogni ordine ha quattro pagine di dettaglio, con 25, 25, 25 e 15 circuiti. Gli assi arrivano a 90; indici e scale sono comuni. I confronti conservano i denominatori, gli scarti negativi e i dati mancanti.

I sei test del report sono passati. Sono stati verificati 360 risultati incrementali, 90 risultati del controllo e 16.200 esiti dell’oracle MQT Bench. Tutti i 90 circuiti sono confrontabili nei quattro ordini. Il PDF finale ha 20 pagine e sono disponibili 20 figure separate.

La prima impaginazione aveva una pagina quasi vuota. La versione finale compatta il testo dei limiti e corregge la larghezza dei grafici. Le due versioni restano conservate; i loro dati coincidono. I sorgenti precedenti del generatore sono in precedente/.

prima.json registra le impronte iniziali; verifica_finale.json documenta controlli, provenienza e percorso del documento finale. Il contenuto delle campagne e il report QASMBench sono invariati. Non sono state eseguite nuove chiamate al LLM o compilazioni quantistiche.

Il compilatore dell’editor integrato non era disponibile in questo ambiente. Il PDF è stato compilato con pdfLaTeX e controllato sulle immagini delle 20 pagine.

# Riduzione del prompt e uso della GPU: proposta da discutere

14 settembre 2026. Le modifiche descritte non sono state applicate al sistema.
Nessun server è stato riavviato e nessuna nuova generazione è stata richiesta.
I conteggi usano soltanto /apply-template e /tokenize del Qwen già avviato.

## Perché scendono i token al secondo

La velocità visualizzata è la media dall'inizio della lettura. Nei livelli di
attenzione completa, ogni nuovo blocco deve confrontarsi con un contesto crescente.
La cache conserva dati già calcolati, ma non elimina questi confronti.
Qwen3.5-4B è ibrido: 8 dei suoi 32 livelli usano attenzione completa.
Questa parte del costo cresce approssimativamente in modo quadratico con la
lunghezza; il tempo totale non segue necessariamente la stessa legge.

| Token elaborati | Vecchia prova dj | Chat osservata |
|---:|---:|---:|
| 10.240 | 28,52 s | 30,24 s |
| 20.480 | 84,30 s | 89,73 s |
| 40.960, circa 51% | 357,51 s | 367,27 s |
| 50.688, circa 63% | 557,18 s | 568,67 s |
| 61.440, circa 76% | 816,62 s | 837,30 s |

Nella vecchia prova la lettura completa richiedeva 1.378,92 secondi.
Il 51% dei token dopo circa sei minuti non implica la fine dopo dodici minuti.
A 54.784 token la chat mostrava una media di 82,34 token/s, ma l'ultimo blocco
da 512 token procedeva a circa 41,46 token/s.

## Come usare più memoria GPU

Nel controllo della chat il server occupava circa 7,0 GiB di memoria GPU dedicata
e 0,67 GiB condivisa. Attività della scheda 99%, nessuna pausa termica.
Il rallentamento non coincide con l'esaurimento della VRAM. Attività al 99%
non dimostra che tutte le operazioni siano eseguite con la massima efficienza.

Il profilo richiede già tutti i livelli sulla GPU e Flash Attention attiva.
Non è imposto un limite volontario a 7 GiB. Occupare altra memoria non accelera
da solo: bisogna impiegarla per una configurazione utile.

L'utente autorizza un uso maggiore, con un obiettivo indicativo di 10 GB su 12.
Dopo la conversazione corrente propongo prove distinte:

1. Micro-batch 128 -> 256, poi 512, lasciando il batch almeno altrettanto grande.
   Blocchi più grandi possono sfruttare meglio la GPU, ma serve misurare il vantaggio.
2. Con micro-batch fissato, confrontare cache q8_0 e f16, mantenendo i pesi Q8_0.
   La cache f16 può ridurre il lavoro sulla rappresentazione quantizzata, ma aumenta
   il traffico in memoria. Il risultato dipende dalle operazioni Vulkan.
3. Dopo aver ridotto il prompt, verificare un contesto allocato più piccolo.
   Un contesto 32.768 è ammissibile solo se contiene prompt, uscita e correzioni.
   Non deve essere usato per troncare silenziosamente il testo.

Stima della sola cache K/V dei livelli di attenzione completa:
2 x 8 livelli x 147.456 token x 4 teste KV x 256 dimensioni.
Con f16: circa 4,50 GiB. Con q8_0: circa 2,39 GiB.
Differenza teorica: 2,11 GiB. Pesi, memoria ricorrente e buffer si aggiungono.
Un totale nell'ordine di 9–10 GiB è plausibile, ma non è una misura e va verificato
rispetto al budget indicativo in GB e alla memoria degli altri processi.
I profili proposti non sono stati eseguiti. Un parametro alla volta, stesso prompt
e cache iniziale equivalente; conservare tempi e picchi di memoria.

## Che cosa occupa il prompt dj

| Sezione | Token contati separatamente |
|---|---:|
| Cinque esempi RAG completi | 53.840 |
| Registro delle evidenze | 15.611 |
| Richiesta e dispositivi | 9.214 |
| Schema e valori richiesti | 1.098 |
| Catalogo configurazioni | 404 |
| Regole | 183 |

Il messaggio completo contiene 80.612 token. I conteggi delle sezioni non sono
perfettamente additivi ai confini. Esempi e registro valgono circa l'86%.
Lo schema non è la causa principale della lunghezza.
Ci sono 737 occorrenze di identificativi/impronte con 64 cifre esadecimali:
circa 51.282 caratteri, spesso ripetuti.

## Bozze misurate

| Variante | Esempi | Token | Riduzione |
|---|---:|---:|---:|
| Originale | 5 | 80.612 | — |
| Originale, due esempi | 2 | 38.729 | 52,0% |
| Compatta | 5 | 29.391 | 63,5% |
| Compatta | 2 | 17.602 | 78,2% |
| Compatta, identificativi brevi | 5 | 18.372 | 77,2% |
| Compatta, identificativi brevi | 2 | 13.182 | 83,6% |

Sono conteggi per dj_indep_tket_2, non misure di qualità o velocità delle bozze.

Nella variante compatta:

- il circuito corrente resta completo, QASM incluso;
- i gate_count a zero sono omessi con una regola esplicita che li ricostruisce;
- affermazioni sorgenti, configurazioni ed evidenze compaiono nel registro canonico;
- restano punteggi aggregati, numero di osservazioni, successo, minimo, massimo e dispersione;
- metrica e avvertenze comuni compaiono una volta;
- identificativi delle esecuzioni, osservazioni per seed e provenienza dettagliata restano nei file originali;
- restano dispositivi, porte native, connettività, configurazioni consentite e schema di risposta.

Non è una compressione senza perdita dell'intero Dataset: è una selezione di ciò
che mostriamo al modello. Anche alcuni campi secondari delle graduatorie storiche
restano soltanto nei dati originali. Prima di adottarla va deciso quali dettagli
possano incidere sulla scelta. Il QASM e tutti i valori già presenti nel registro
canonico sono stati verificati come conservati.

Gli identificativi brevi sostituiscono evidence_<64 caratteri> con E1, e analogamente
record, affermazioni e riepiloghi. La mappa inversa resta fuori dal prompt.
La reversibilità è verificata. Occorre un adattatore prima del controllo semantico,
anche per le correzioni: questa variante non è già integrata nel prototipo.

## Proposta

Partirei dalla forma compatta e dagli identificativi brevi mantenendo cinque esempi.
Cinque esempi così rappresentati occupano meno di due nel formato originale.
Poi confronterei cinque e due esempi compatti. Non sappiamo ancora se due bastino.

Da mantenere: caratteristiche del circuito, dispositivi ammessi, configurazioni,
obiettivo, esempi confrontabili, punteggi aggregati con affidabilità, riferimenti
verificabili e forma della risposta. Le evidenze storiche non sono misure del
circuito corrente.

Una seconda modifica possibile, separata dalle bozze, è fornire al modello solo
caratteristiche strutturali e relazioni tra qubit, lasciando il QASM completo al
compilatore. Potrebbe bastare per scegliere dispositivo e configurazione, ma le
49 feature possono perdere informazione sull'ordine delle porte. Serve una prova.
Anche sostituire gli archi hardware con proprietà riassuntive del grafo comporta
perdita di informazione sulla topologia. Nessuna delle sei bozze fa questi tagli.

## Artefatti

- counts.json: conteggi esatti delle sei varianti.
- section_counts.json: conteggi per sezione.
- *.txt e *.json: bozze testuali e strutturate.
- *_aliases_map.json: corrispondenze reversibili.
- audit_*: formattazione e conteggio conservati.
- probe.py: procedura usata; checks.json: verifiche.
- timing_observations.json: curva della vecchia prova, osservazioni della chat fino
  al controllo e un campione delle risorse con data e ora.

Il caso train può recuperare se stesso; questa analisi non misura generalizzazione.
Non è stato letto alcuno score di validation o test.

Fonti ufficiali:
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B),
[llama.cpp b10930](https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md).

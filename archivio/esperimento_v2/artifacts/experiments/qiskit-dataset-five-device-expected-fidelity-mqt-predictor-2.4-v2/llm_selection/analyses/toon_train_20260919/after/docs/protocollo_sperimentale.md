# Protocollo sperimentale

Questo è l’unico protocollo operativo del progetto. Si aggiorna questo file.
Versione sperimentale: **2.0.0**, MQT Predictor **2.4.0**.
Ultimo riordino della documentazione: **15 settembre 2026**.
Emendamento della selezione LLM: **13 settembre 2026**. Questo emendamento
separa la selezione locale sulla validation dal confronto finale sul test.
La versione 2.0.0 continua a identificare corpus, Target e matrice Qiskit:
non si invalidano gli artefatti precedenti. La copia del protocollo precedente
è conservata in `llm_selection/preparation/protocollo_pre_selezione.md`
sotto la directory degli artefatti dell’esperimento.

Le copie precedenti sono conservate nell’[archivio](../archivio/README.md).
Il riordino dei file non cambia le condizioni dell’esperimento.

## Stato della pipeline

Il quadro sintetico aggiornato è nel [README principale](../README.md#che-cosa-abbiamo-fatto-e-dove-siamo).
Al 15 settembre 2026 il Dataset Qiskit di train e validation è completo:
87120 tentativi, 82621 successi e 4499 timeout. Il RAG usa 396 esempi train;
Qdrant e la preparazione dei prompt sugli 88 validation sono verificati.

Il collegamento LLM locale è implementato e le prove tecniche sul train sono
in corso. Nell'ultima prova Qwen sul circuito DJ, nessuna delle tre risposte
è interamente valida: dispositivo e configurazione sono corretti, ma rimangono
errori nei riferimenti alle evidenze. Questo non è un risultato della selezione
sulla validation. Si conserva il [resoconto della prova](resoconti/2026-09-15_prompt_compatto.md).

È presente un modello RL canonico Quantinuum con 100352 passi registrati.
L'utente ha comunicato l'avvio del training `ibm_falcon_27` durante questa
ricognizione; non viene dedotto un completamento dal solo avvio.
I cinque modelli finali, il classificatore ML e le verifiche qcompile non
risultano tutti completati e verificati su questa macchina.
La posizione dei pesi e dei checkpoint esterni su D: va verificata prima
dei futuri controlli; la loro presenza in un registro non basta.

Il test resta sigillato. La selezione locale può procedere indipendentemente
dal completamento del ramo MQT, che resta necessario per il confronto finale.
Il riordino documentale non avvia, arresta o modifica gli esperimenti.

## Ambiente dell’esperimento

I risultati precedenti usavano MQT Predictor 2.3.0, MQT Bench 2.0.0 e
Qiskit 2.1.1. Sono conservati in `archivio/protocollo_v1/` e non alimentano
il Dataset o la cache dell’esperimento attuale.

Il protocollo 2.0 usa MQT Predictor 2.4.0. La migrazione non è un semplice
aggiornamento di un pacchetto. MQT Predictor 2.4.0 usa MQT Bench 2 e i Target
Qiskit. La guida ufficiale richiede inoltre di addestrare un modello RL per
ogni dispositivo e poi il modello supervisionato prima di usare qcompile.
La guida di migrazione ufficiale indica anche cambiamenti nello spazio delle
azioni RL. I vecchi modelli non sono quindi accettati.

Queste sono informazioni del software ufficiale:

- [release MQT Predictor 2.4.0](https://github.com/munich-quantum-toolkit/predictor/releases/tag/v2.4.0);
- [guida ufficiale di migrazione](https://github.com/munich-quantum-toolkit/predictor/blob/main/UPGRADING.md);
- [preparazione dei modelli MQT Predictor](https://mqt.readthedocs.io/projects/predictor/en/stable/setup.html);
- [uso ufficiale di qcompile](https://mqt.readthedocs.io/projects/predictor/en/stable/quickstart.html);
- [pacchetto MQT Predictor su PyPI](https://pypi.org/project/mqt.predictor/2.4.0/).

Le regole sugli split, i timeout, i seed, i gate di apertura e il confronto
sono scelte ingegneristiche di questo progetto.

## Terminologia

- Dataset: dati destinati al RAG o a un eventuale adattamento del modello
  linguistico.
- Training set: coppie circuito-dispositivo usate dal classificatore ML di
  MQT Predictor.

## Scopo

L'esperimento valuta se il sistema completo LLM + RAG sceglie un dispositivo e
una configurazione Qiskit che producono circuiti compilati di buona qualità, con
tempi e affidabilità accettabili.

La scelta riguarda congiuntamente:

1. il dispositivo sul quale compilare;
2. una delle dodici configurazioni Qiskit ammesse.

La qualità è stimata fuori linea sui Target sintetici di MQT Bench. Non vengono
eseguiti circuiti su hardware quantistico reale.

## Domande di ricerca

- **RQ1.** Il sistema completo LLM + RAG riduce il regret rispetto allo stesso
  LLM senza RAG?
- **RQ2.** Il sistema completo supera un LLM di frontiera usato senza il
  prototipo?
- **RQ3.** Come si confronta il sistema completo con MQT Predictor, con le
  configurazioni Qiskit fisse e con la scelta casuale?
- **RQ4.** Quanto si avvicina ogni metodo all'oracle esaustivo?
- **RQ5.** Quali sono affidabilità, tipi di fallimento, latenza e costo dei
  metodi?
- **RQ6.** I risultati cambiano per famiglia di circuito o numero di qubit?

## Ipotesi

Le ipotesi sono fissate prima dell'apertura del test.

- **H1, contributo del RAG.** Il sistema completo ha regret assoluto mediano
  inferiore allo stesso LLM senza RAG e non ha un tasso di successo inferiore.
- **H2, contributo del prototipo.** Il sistema completo ha regret assoluto
  mediano inferiore al LLM di frontiera senza prototipo e non ha un tasso di
  successo inferiore.
- **H3, confronto con MQT Predictor.** Il sistema completo ha regret assoluto
  mediano inferiore a MQT Predictor, tenendo separato il confronto di
  affidabilità.
- **H4, confronto con le baseline semplici.** Il sistema completo ha regret
  assoluto mediano inferiore alla baseline casuale e alle baseline Qiskit fisse.

Per ogni confronto, l'ipotesi nulla è che la distribuzione appaiata delle
differenze sia centrata a zero. Il mancato rifiuto dell'ipotesi nulla non sarà
presentato come prova di equivalenza.

## Disegno sperimentale e unità di analisi

Tutti i metodi sono applicati agli stessi circuiti sorgente. Il circuito, non la
singola compilazione, è l'unità primaria dell'analisi statistica. I tre seed non
sono tre circuiti indipendenti e non possono aumentare artificialmente la
numerosità.

Ogni record elementare deve essere identificato almeno da:

`experiment_id`, `method_id`, `circuit_sha256`, `repetition_index`,
`qiskit_seed`, `attempt_index` e `run_id`.

Un `run_id` concluso non può essere eseguito di nuovo perché ha dato un risultato
sfavorevole. Un'attività interrotta prima di produrre un esito terminale può
essere ripresa con lo stesso `run_id`; la ripresa e la sua causa devono essere
registrate.

### Richiesta canonica

Per ogni circuito viene costruita meccanicamente una sola richiesta. Contiene il
file OpenQASM esatto, l'obiettivo `expected_fidelity`, l'impronta del catalogo e
i cinque dispositivi iniziali. Non attiva preferenze facoltative per fornitore,
costo, latenza o dispositivo. La maschera del prototipo elimina poi i candidati
incompatibili con circuito e Target. La richiesta è identica per sistema completo
e variante senza RAG; il LLM di frontiera riceve lo stesso circuito e lo stesso
spazio di scelta, ma non la maschera calcolata.

La richiesta canonica conserva il sorgente e le impronte. Dal 18 settembre 2026
la vista inviata al sistema LLM con/senza RAG omette QASM e provenienza e usa
le caratteristiche numeriche complete. Gli artefatti originali non cambiano.
La stessa rappresentazione di circuito e catalogo si applica al confronto
con/senza RAG. Il prompt diretto del modello di frontiera resta quello distinto
previsto sotto; questa modifica non ridefinisce automaticamente quel metodo.

## Metodi e spazio di scelta

La fonte normativa delle dodici configurazioni è il
[catalogo v2](../configs/qiskit_dataset_configurations_v2.json).
Non sono ammesse configurazioni inventate dal modello. I valori predefiniti
non impongono a Qiskit un algoritmo esplicito di layout o instradamento.

| Metodo | Regola |
| --- | --- |
| LLM + RAG | Richiesta, maschera hardware, feature, esempi train, registro delle evidenze e controlli del prototipo. |
| Stesso LLM senza RAG | Stesso modello, richiesta, maschera, parametri, schema e controlli. Recupero disattivato ed evidenze vuote. |
| LLM di frontiera | Prompt diretto con circuito, cinque dispositivi e dodici configurazioni. Nessuna maschera applicativa, RAG o correzione guidata. |
| MQT Predictor | Classificatore per scegliere il dispositivo e policy RL associata per compilare. |
| Qiskit predefinito | Livelli 2 e 3 su ciascuno dei cinque dispositivi: dieci baseline distinte. Non si sceglie a posteriori il dispositivo migliore. |
| Casuale | Una coppia dispositivo compatibile–configurazione estratta uniformemente per ripetizione. Nessuna nuova estrazione dopo un fallimento. |
| Oracle | Massimo esaustivo della matrice compatibile, disponibile solo se tutti i tentativi sono riusciti. |

Il LLM di frontiera deve restituire soltanto
`{"selected_device": "ibm_falcon_27", "config_id": "o2_default_default"}`
con identificativi del catalogo. I nomi non vengono corretti automaticamente.
Il controllo meccanico di compatibilità registra l’esito senza dare risposte
correttive al modello.

A parità numerica l’oracle usa prima l’ordine dei dispositivi e poi quello
delle configurazioni del catalogo. Le quasi parità (`rel_tol=1e-12`,
`abs_tol=1e-15`) sono segnalate senza cambiare il vincitore.
La v2 richiede la matrice interamente riuscita: un massimo su risultati
parziali non viene chiamato oracle.

## Regole degli esempi RAG e della similarità

Solo `global/rag_examples.jsonl` del Dataset attuale alimenta Qdrant.
Deve contenere soltanto train e al massimo un esempio per SHA-256 del sorgente.
Il file corrente contiene 396 esempi: i 26 alias byte-identici dei 422 circuiti
train non aggiungono altre righe recuperabili.

Ogni esempio conserva il dispositivo vincente e fino a tre configurazioni
valide di quel dispositivo. Non si aggiungono i primi tre dispositivi e non
si bilanciano artificialmente le etichette. L’assenza di vincitori Falcon 27 è
un risultato, non un errore del Dataset. Una maschera può lasciare zero esempi:
in quel caso la risposta dichiara l’assenza di evidenze storiche.

I due esempi `realamprandom_indep_qiskit_2` e `realamprandom_indep_tket_2`
hanno la stessa impronta semantica e restano entrambi nel train. La possibile
ridondanza nel recupero è accettata. Non duplicano circuiti di validation o test.
La verifica di hash, impronta semantica e gruppi tra gli split resta obbligatoria.

La raccolta usa **Qdrant locale persistente 1.19.0**, tramite il client
ufficiale. Non richiede un server, un account cloud o un modello di embedding.
Il solo ingresso è il JSONL globale train. Qdrant ne conserva una copia derivata,
ricostruibile: non è un secondo Dataset operativo.

Per esplorare i 396 esempi è disponibile anche una
[dashboard Qdrant locale](../prototype/qdrant_dashboard/README.md).
Usa un server Docker separato e una copia verificata dei punti train.
Questa vista non cambia il recupero del prototipo né il protocollo sperimentale.

Per ogni esempio vengono memorizzati un UUID deterministico, le 49 feature
trasformate, l'identificativo RAG, l'esperimento, lo split, il dispositivo
vincente e il record originale con provenienza ed evidenze. Dispositivo,
configurazioni, score, testo e altre etichette non entrano nel vettore.
Prima dell'inserimento si verificano schema, hash train, unicità per hash
sorgente, identità, Target, feature ed evidenze. Gli esempi devono coincidere
con quelli ricostruiti in memoria dagli aggregati train. La preparazione
ricalcola inoltre le feature dai circuiti train, senza compilarli.

### Trasformazione e distanza

La versione del recupero è `circuit49-log1p-train-maxabs-manhattan/1`.
L'ordine esplicito delle 49 coordinate è in
`prototype/quantum_assistant/adapters/rag_features.py` e in
`rag/index/transform.json`. Non dipende dall'ordine delle chiavi JSON.

Per una coordinata `i`:

```text
t_i(x) = log1p(x_i)   per gate_count_*, depth e num_qubits
t_i(x) = x_i          per gli altri cinque indicatori
d_i    = max assoluto di t_i nei soli 396 esempi train; se zero, vale 1
z_i(x) = t_i(x) / d_i
D(q,c) = somma_i abs(z_i(q) - z_i(c))
```

Si usa `Distance.MANHATTAN`: una distanza minore indica maggiore vicinanza.
Non si centra, non si tagliano i valori e non si normalizza la lunghezza del
vettore. Un ingresso oltre il massimo train può quindi superare 1.
I divisori si stimano solo sui 396 esempi train e restano identici per
validation, test e richieste successive. Valori mancanti, inattesi, non finiti,
conteggi negativi o frazionari e indicatori fuori [0, 1] vengono rifiutati.
Il numero di qubit deve essere almeno 1.

Il logaritmo riduce la prevalenza dei conteggi molto grandi. La divisione
rende confrontabili le scale delle coordinate sul train. È una scelta
progettuale, non un risultato dei paper MQT né una prova che questi vicini
portino alle raccomandazioni migliori. Le molte coordinate dei gate possono
avere un peso complessivo maggiore dei cinque indicatori. Le correlazioni
tra feature e la distribuzione sbilanciata dei vincitori restano limiti.

Questa formula **sostituisce** la precedente media di
`abs(q_i-c_i)/(1+max(abs(q_i),abs(c_i)))`. Le due formule non sono equivalenti.
La precedente scala dipendeva dalla coppia confrontata; ora la scala è fissa
e stimata sul train. Non esiste un ripiego automatico alla vecchia formula.

### Ricerca esatta, filtri e parità

I filtri per esperimento, train, obiettivo e dispositivo vincente ammesso
dalla maschera sono passati alla ricerca Qdrant. La scelta dei primi `k`
avviene dopo questi filtri. Il valore predefinito è **5 esempi**; le **3
configurazioni** del vincitore sono invece dati interni a ciascun esempio.

La modalità locale esegue una ricerca esaustiva. Non usa HNSW e non accelera
i filtri con indici dei dati associati. Il parametro `exact=True` non aggiunge
effetti in questa modalità, che è già esatta. Queste proprietà sono confermate
dal [codice ufficiale del client 1.19.0](https://github.com/qdrant/qdrant-client/blob/v1.19.0/qdrant_client/local/qdrant_local.py)
e dalla [documentazione della modalità locale](https://pypi.org/project/qdrant-client/1.19.0/).

Qdrant conserva vettori a precisione float32. Per questo piccolo Dataset
si recuperano tutti i candidati filtrati e si controllano tutte le distanze
contro la formula float64. La tolleranza segue `math.isclose`:
errore assoluto 1e-5 oppure relativo 1e-6. Uno scarto superiore è un errore.
Il risultato viene ordinato per distanza canonica float64 e poi per
identificativo RAG originale. La tolleranza non raggruppa le quasi-parità.
Questo passaggio gestisce anche le parità sul confine dei primi `k`.
Il costo è una seconda scansione dei candidati: non rivendichiamo un aumento
di velocità rispetto al riferimento locale.

Zero candidati compatibili è ammesso e produce un registro vuoto. Una raccolta
assente, incompleta, incompatibile o alterata ferma invece il flusso.
Un blocco o guasto del database produce un errore distinto e non attiva
automaticamente un altro recupero.

### Verifiche dell'integrazione del 9 settembre 2026

La raccolta reale contiene 396 punti train. La suite completa supera 177 test.
Le prove includono filtri, nessun candidato, k oltre la numerosità disponibile,
parità anche al confine, coordinate nulle o costanti, valori oltre il massimo
train, feature errate, dati alterati, raccolte incomplete, riapertura e
indicizzazione ripetuta. I test usano anche istanze locali Qdrant reali.

Tutti gli 88 circuiti validation superano il flusso fino al prompt. Le distanze
canoniche coincidono con il calcolo indipendente; il massimo scarto osservato
degli score Qdrant è circa 1,61e-7, entro la tolleranza dichiarata.
Questa verifica non comprende chiamate LLM, nuove compilazioni del Dataset
o valutazione della qualità delle raccomandazioni.

Il confronto delle impronte riguarda 229874 file preesistenti: 229870 sono
invariati. Le sole quattro differenze sono checkpoint e log del training
Quantinuum già avviato alle 11:35, prima della fotografia iniziale delle 18:44.
Quel processo è rimasto attivo e non è stato riavviato o interrotto.
Dataset, sorgenti, risultati Qiskit, catalogo e piani congelati sono invariati.
Il confronto originale e la spiegazione sono in `rag/audit/`.

### Artefatti, comandi e sincronizzazione

Tutti gli artefatti sono sotto
`artifacts/experiments/<identificativo>/rag/`:

- `index/qdrant/`: database persistente;
- `index/transform.json`: ordine, trasformazioni, divisori e impronta;
- `index/manifest.json`: fonte JSONL, provenienza train, impronta dei punti,
  metrica, dimensione, numero di punti, versioni software e impronta di uv.lock;
- `verification.json`: verifica della raccolta;
- `validation_check.json`: prova tecnica sugli 88 circuiti validation;
- `audit/`: registrazioni delle verifiche e del confronto con i file iniziali.

Dalla radice, dentro WSL o Ubuntu:

```bash
.venv/bin/python scripts/17_rag_v2.py prepare
.venv/bin/python scripts/17_rag_v2.py verify
.venv/bin/python scripts/17_rag_v2.py validation
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO_CIRCUITO.qasm --k 5
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO_CIRCUITO.qasm --k 5 --backend reference
```

`query` prepara il prompt e le evidenze senza chiamare un LLM. Si può
aggiungere `--devices ibm_falcon_127` per provare una maschera ristretta.
Queste prove rifiutano i circuiti test noti prima del parsing.
`validation` legge solo i sorgenti validation: non usa i loro score o vincitori.
Controlla parsing, maschera, recupero, registro, prompt e confronto indipendente
delle distanze. Non misura la qualità delle raccomandazioni LLM.

`prepare` crea l'indice in una cartella temporanea, lo verifica, lo riapre e
solo allora lo rende disponibile. Se l'indice esiste già, lo verifica senza
riscriverlo: la ripetizione non aggiunge punti. Se non coincide con la fonte
o con la trasformazione, il comando fallisce. Per ricostruirlo deliberatamente,
chiudere i processi che lo usano, conservare la vecchia cartella `rag/index/`
con un altro nome e rieseguire `prepare`. Le cartelle temporanee lasciate da
una preparazione fallita servono alla diagnosi e non vengono usate dal servizio.
Non ricostruire un indice già congelato per il test.

Sull'altro computer usare lo stesso codice, uv.lock e versione Python indicata
nel manifest. Per aggiungere le dipendenze senza ricreare l'ambiente:
`uv sync --frozen --inexact --python 3.12`. Sincronizzare il Dataset corrente
completo, il manifest sorgente e gli artefatti necessari alle verifiche.
È preferibile ricostruire Qdrant dal JSONL con `prepare`, poi confrontare
manifest e trasformazione e lanciare `verify`. In alternativa copiare
`rag/index/` per intero a database chiuso. Non unire file SQLite di due copie
e non aprire contemporaneamente la stessa cartella da più processi.
La modalità locale consente un solo client aperto su quella cartella.

Il recupero locale `reference` usa il JSONL e la stessa trasformazione
verificata, senza interrogare il database. Si seleziona esplicitamente con
`retrieval_backend="reference"` nella factory. Il valore predefinito è
`"qdrant"`; `"none"` serve alla variante senza RAG. Un nome sconosciuto fallisce.
Il vecchio nome `JsonDatasetContextRetriever` ora indica il riferimento v2:
non accetta più JSON storici senza provenienza train.

## Ripetizioni e tentativi

Ogni metodo LLM produce una sola raccomandazione valida per circuito. Il primo
output valido è definitivo; non si seleziona il migliore tra più risposte.
La coppia scelta viene compilata con i tre seed Qiskit 0, 1 e 2.

I due metodi del prototipo ammettono al massimo tre chiamate totali, solo per
correggere risposte non conformi. Richiesta, maschera, evidenze e parametri
restano identici. Il modello di frontiera ha una sola chiamata. Eventuali
ripetizioni di trasporto devono essere disattivate oppure congelate e contate;
ogni chiamata fatturata contribuisce a token e costo.

qcompile viene invocato tre volte, ogni volta in un nuovo processo. Gli indici
0, 1 e 2 sono ripetizioni, non seed Qiskit controllati. Il record conserva la
politica di campionamento e gli eventuali seed effettivamente disponibili.

## Metriche

### Qualità primaria

`expected_fidelity` è calcolata con
`mqt.predictor.reward.expected_fidelity` sul circuito compilato e sul Target
sintetico versionato. È una stima deterministica per una coppia circuito
compilato-Target; non è una misura sperimentale su hardware reale.

Per una coppia fissa, il valore del circuito è la mediana dei tre seed, purché
tutti abbiano successo. Per un metodo LLM la coppia è quella dell'unica
raccomandazione valida. Per la baseline casuale, che può scegliere tre coppie
diverse, il valore del circuito è la mediana dei tre risultati soltanto se tutte
e tre le ripetizioni sono riuscite. Per MQT Predictor è la mediana delle tre
invocazioni, sempre con requisito tre su tre.

### Regret

Per ogni circuito con metodo e oracle disponibili:

```text
regret_assoluto = expected_fidelity_oracle - expected_fidelity_metodo
regret_relativo = regret_assoluto / expected_fidelity_oracle
```

Il regret relativo è non disponibile se il valore dell'oracle è zero. Il regret
non viene limitato artificialmente a zero: un valore negativo deve essere
conservato e indagato, perché può indicare un errore, una differenza di spazio di
ricerca o, per MQT Predictor, un compilatore esterno alle dodici configurazioni.

### Rappresentazione logaritmica

La misura primaria resta `expected_fidelity`. Per controllare sottosoglia e forte
asimmetria si registra anche
`log_expected_fidelity = ln(expected_fidelity)` quando il valore è positivo. Se
il prodotto va numericamente a zero, il log può essere calcolato direttamente
come somma dei log dei fattori del medesimo stimatore. Se questi fattori non sono
disponibili, il log è `null` con causa `numeric_underflow`; non si sostituisce la
misura con un valore arbitrario.

### Affidabilità, scelta, tempo e costo

Per ogni metodo si registrano almeno:

- percentuale di compilazioni riuscite e completamento tre su tre per circuito;
- numero e categoria dei fallimenti;
- tempo attivo della raccomandazione, somma dei tempi delle chiamate LLM e tempo
  del recupero;
- tempo di ogni compilazione e tempo totale dell'episodio;
- numero di tentativi e di chiamate effettive al servizio LLM;
- dispositivo e configurazione scelti;
- accuratezza del dispositivo, della configurazione e della coppia rispetto
  alla coppia unica scelta dal tie-break dell'oracle;
- token di ingresso, uscita, cache e ragionamento, quando forniti;
- costo per chiamata e costo totale, con valuta e listino congelato.

L'accuratezza del dispositivo vale 1 quando il dispositivo scelto coincide con
quello dell'oracle. L'accuratezza della configurazione vale 1 quando coincide il
`config_id`, indipendentemente dal dispositivo; l'accuratezza della coppia
richiede entrambe le coincidenze. I denominatori comprendono soltanto scelte
valide con oracle disponibile e sono sempre dichiarati. MQT Predictor ha
accuratezza del dispositivo, ma non della configurazione: la politica RL non è
una delle dodici configurazioni Qiskit e il campo è quindi non applicabile.

Il tempo di raccomandazione è misurato una volta e non viene sommato tre volte.
Il tempo totale di un episodio LLM è il tempo della raccomandazione più la somma
dei tre tempi di compilazione. Il tempo di attesa in coda viene registrato a
parte. Per MQT Predictor il tempo di selezione e compilazione è integrato nel
tempo di `qcompile`; il tempo LLM non è applicabile.

## Trattamento dei fallimenti

Nessun fallimento viene eliminato o trasformato in una nuova scelta. Le categorie
minime del resoconto sperimentale sono:

- `compilation_timeout`;
- `compiler_error`;
- `incompatible_device`;
- `invalid_configuration`;
- `llm_output_unparseable`;
- `llm_output_invalid_after_retries`;
- `llm_service_error`;
- `dataset_or_retrieval_error`;
- `mqt_predictor_error`;
- `target_validation_error`;
- `scoring_error`;
- `experiment_infrastructure_error`.

`not_applicable_width` è uno stato di non applicabilità, non un fallimento. È
usato per le baseline dispositivo-specifiche e non entra nel loro denominatore
di successo. Il numero dei casi non applicabili deve comunque essere mostrato.

Ogni categoria conserva il tipo di eccezione, un messaggio ripulito da segreti,
la fase, il tempo trascorso e l'identificativo del tentativo. Il timeout Qiskit
per singola compilazione è fissato a 100 secondi, con sei processi esterni e `num_processes=1` per Qiskit. Dopo il timeout il processo viene terminato e il risultato è
un fallimento; non viene rilanciato con un seed diverso.

Se uno dei tre seed o una delle tre invocazioni MQT fallisce, l'aggregato primario
del circuito per quel metodo è non disponibile. Di conseguenza anche i regret
assoluto e relativo sono `null`, con un campo `regret_unavailable_reason`. Tutte
le esecuzioni riuscite restano nelle statistiche descrittive sui singoli
tentativi e il circuito entra come non completato nelle statistiche di
resilienza.

La qualità condizionata ai soli successi deve essere mostrata sempre accanto alla
probabilità di successo e alla numerosità comune. Non è consentito confrontare
ciascun metodo sul proprio sottoinsieme favorevole senza presentare anche il
confronto appaiato sul medesimo insieme di circuiti completati.

## Analisi statistica

L'analisi viene eseguita una sola volta con uno script versionato e un piano
congelato. Il seed delle analisi e del bootstrap è `20260901`.

Per ogni metodo si riportano:

- numerosità totale, applicabile, completata e usata nel confronto appaiato;
- media, mediana, deviazione standard e intervallo interquartile;
- intervalli di confidenza bootstrap al 95%;
- tasso di successo per ripetizione e tasso di completamento tre su tre;
- distribuzione per famiglia;
- distribuzione per classi di qubit `1-10`, `11-27`, `28-56` e `57-90`.

La deviazione standard è quella campionaria, con denominatore `n-1`. L'intervallo
interquartile è `Q3-Q1`, con quantili lineari. I valori mancanti non vengono
imputati. Ogni tabella mostra il proprio denominatore e, per i confronti, il
numero di circuiti completi per entrambi i metodi.

Il bootstrap usa 10.000 ricampionamenti del circuito con rimpiazzo per media,
mediana, regret, tasso di successo e differenze appaiate. Nei confronti
appaiati, le due osservazioni dello stesso circuito vengono ricampionate insieme.
Si usa l'intervallo percentile al 95% e si registrano versione della libreria e
seed. Le classi con meno di cinque circuiti sono mostrate, ma indicate come
puramente descrittive.

Il confronto confermativo tra il sistema completo e ciascuna baseline usa il
test dei ranghi con segno di Wilcoxon, bilaterale, sul regret assoluto a livello
di circuito. Si usa la convenzione `zero_method="pratt"`; l'algoritmo effettivo
del calcolo e la versione della libreria vengono congelati. Il livello di
significatività è `alpha=0,05`.

La famiglia di confronti primari contiene:

- stesso LLM senza RAG;
- LLM di frontiera;
- MQT Predictor;
- baseline casuale;
- le dieci coppie formate dalle due configurazioni fisse e dai cinque
  dispositivi.

I valori *p* di questa famiglia sono corretti con il metodo di Holm. Un confronto
predefinito non eseguibile resta nella famiglia con valore convenzionale 1, così
la sua assenza non rende meno severa la correzione. L'oracle è il riferimento per
il regret e non è trattato come un metodo realistico nel test di superiorità.

Il completamento tre su tre è confrontato separatamente con un test di McNemar
esatto sui circuiti appaiati. Anche questa famiglia usa la correzione di Holm e
`alpha=0,05`. Le analisi per famiglia, qubit, logaritmo, latenza, token e costo
sono analisi secondarie o di sensibilità e devono essere indicate come tali.

## Criteri decisionali

Un confronto è dichiarato favorevole al sistema completo soltanto se:

1. il valore *p* corretto con Holm è inferiore a 0,05;
2. mediana ed effetto stimato hanno la direzione prevista;
3. l'intervallo bootstrap al 95% della differenza non include zero;
4. la numerosità appaiata e tutti i fallimenti sono mostrati;
5. sullo stesso insieme applicabile, il tasso osservato di completamento del
   sistema completo non è inferiore; il test di McNemar viene comunque riportato.

Il contributo del RAG è sostenuto soltanto dal confronto predefinito tra sistema
completo e stesso LLM senza RAG. Un buon confronto con un'altra baseline non può
sostituirlo. Qualità, affidabilità, tempo e costo restano dimensioni separate;
non viene costruito dopo il test un punteggio composito favorevole.

Se i criteri non sono soddisfatti, il risultato viene descritto come non
conclusivo o sfavorevole, secondo il segno osservato. Non si cambia test, soglia,
sottoinsieme o metrica primaria.

## Separazione dei dati e limiti già noti

Validation e test non entrano in vettori, payload, esempi di riserva o evidenze
RAG. L’indice deve essere verificato contro gli hash train ammessi. Prompt,
modelli e parametri finali si verificano sulla validation e si congelano prima
del test. La trasformazione RAG qui definita stima i divisori solo sul train. Cache e registri delle decisioni di
valutazione restano separati per split.

Il pilota storico aveva già compilato `qpeexact_indep_tket_60.qasm` e
`routing_indep_qiskit_12.qasm`, presenti nel test. L’archiviazione non cancella
questa esposizione. Punteggi e vincitori storici non possono guidare le scelte.
Prima del test va registrata la ricostruzione delle decisioni prese; se non è
possibile escluderne l’influenza, il limite deve essere dichiarato.

Non si può escludere che circuiti MQT Bench fossero nei dati di addestramento
di un LLM commerciale. I controlli locali non eliminano questo limite.

Le regole statistiche qui riportate definiscono l’analisi finale da eseguire.
La presenza del valutatore comune non attesta da sola che l’intera analisi
statistica sia già stata prodotta. Versione dello script di analisi, librerie,
seed, denominatori e deviazioni vanno congelati e riportati nei risultati.

## Identità e valori congelati

Identificativo:

    qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2

Versione del protocollo:

    2.0.0

Metrica primaria:

    mqt.predictor.reward.expected_fidelity

La metrica è una stima deterministica sul Target sintetico di MQT Bench. Non è
una misura raccolta su hardware reale.

Il corpus conserva i 600 circuiti del protocollo 1.0:

- 422 train;
- 88 validation;
- 90 test.

L'impronta del manifest sorgente legacy è:

    9037e08f529e6598f69cc8ffa524f593335d0e65757db771ce28b285479529ed

L'impronta semantica complessiva del corpus verificato è:

    e69ca13cd27642fe654ad4a350ba74dd6b2c539cc5667623fc58cfb1db516bb1

Il manifest v2 deterministico prodotto dalla pila congelata ha SHA-256:

    c599eab17b6f64528067016e3d175cbfed597334f779ef8e515cf8787a788f53

I controlli confrontano nomi, SHA-256 del file, hash semantico e gruppo di
leakage. Un alias che cambia soltanto nome di registro o barriere non può
attraversare gli split.

Ordine dei dispositivi e impronte dei Target:

| Dispositivo | SHA-256 Target |
| --- | --- |
| ibm_falcon_27 | b9120f471bd90ef5aae03606ebc1e421478cd50f7b65ff4fb115f64c5148c104 |
| ibm_heron_133 | 2de960a68a2d3c77d1c8284fc2f89c2ec26a565994024c6ea329e7a5b7bf2df3 |
| ibm_falcon_127 | 5b91130482b02e3029bf550d88ec2cf732b52f023137c0f1ec7e059facb1debd |
| ibm_heron_156 | 207fcb68d097a924aa681ca5d4545d2f5eed04f9783a91021dffb59bcff43003 |
| quantinuum_h2_56 | ceb17d2f893cad6d8f78572def3c73dee3b7f3c2cc55dcb4feddc9e292e2aeee |

La matrice Qiskit usa dodici configurazioni, seed 0, 1 e 2, sei processi e un
timeout di 100 secondi per tentativo. Le opzioni fisse sono
approximation_degree uguale a 1 e num_processes uguale a 1.

Il piano casuale usa Python Random con MT19937 e seed 20260901. Le estrazioni
sono congelate prima degli score:

- validation: 264 estrazioni, piano
  952c4fcfa64308735a0c00688bdfc6d94b4c6c4d82732e8498da2e274dee7e18;
- test: 270 estrazioni, piano
  3c625ea7bc6f91d6d8df446159ffa288710668818d52c0a729b48d30ae869695.

Il riallineamento del 9 settembre corregge i metadati dei piani rimasti a
300 secondi e 2 processi. Le estrazioni non cambiano. Gli originali e le
impronte dei file sono conservati in `plans/history/` nell'esperimento v2.
Su un'altra macchina con i vecchi piani, usare esplicitamente:

    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split validation --align-execution-policy
    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split test --align-execution-policy

Il comando rifiuta cambiamenti ai circuiti o alle estrazioni e non può
modificare i piani dopo l'apertura del test. Ripeterlo su piani già allineati
non cambia i file. Non modifica Dataset, seed o versione del protocollo.

## Dipendenze esatte

| Pacchetto | Versione |
| --- | --- |
| Python | 3.12 |
| mqt.predictor | 2.4.0 |
| mqt.bench | 2.2.3 |
| qiskit | 2.5.0 |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.47.0 |
| qiskit-qasm3-import | 0.6.0 |
| pytket | 2.18.1 |
| pytket-qiskit | 0.77.0 |
| bqskit | 1.2.1 |
| numpy | 2.5.1 |
| scikit-learn | 1.9.0 |
| sb3-contrib | 2.9.0 |
| stable-baselines3 | 2.9.0 |
| gymnasium | 1.3.0 |
| torch | 2.13.0 |
| joblib | 1.5.3 |
| tensorboard | 2.21.0 |
| qdrant-client | 1.19.0 |

Il file uv.lock è l'unica risoluzione ammessa. Lo script di bootstrap usa
uv sync con il controllo frozen.

## Dove lavorare

L’unico Dataset attuale si trova in:

    datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/expected_fidelity/full/

Il file da usare per il RAG è `global/rag_examples.jsonl` sotto questa cartella.
Le cinque cartelle dei dispositivi contengono i risultati da cui deriva la vista
globale: sono parti dello stesso Dataset e vanno conservate. Validation e test
servono alla valutazione e non entrano negli esempi recuperabili.

L’unica area degli artefatti attuali è:

    artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/

La cache Qiskit è `qiskit_dataset_cache/expected_fidelity/` al suo interno.
Manifest, sorgenti consentite, checkpoint, log, modelli, piani e risultati dei
metodi rimangono nella stessa area. `plans/history/` conserva la provenienza
dei piani attuali e non rappresenta un altro esperimento da eseguire.

Il Training set del classificatore, una volta prodotto, si trova in:

    datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/training_set/device_selector_expected_fidelity.json

Il catalogo attuale è `configs/qiskit_dataset_configurations_v2.json`.
Gli script Qiskit 07–10 usano per impostazione predefinita questo catalogo e
lo scope `full`. I dati storici richiedono il catalogo esplicito in
`archivio/protocollo_v1/configs/` e restano sotto l’archivio.

### Perché conservare il corpus originale nell’archivio

`archivio/protocollo_v1/datasets/expected_fidelity/full/` contiene i 600 QASM
originali e il manifest che ne attesta la provenienza. La preparazione v2 legge
solo questi sorgenti e il manifest per verificarne gli hash. Non legge i vecchi
punteggi. I percorsi scritti nei manifest congelati restano nomi logici originali;
il codice li risolve nella nuova cartella. Non rinominare questi riferimenti a
mano: cambierebbero anche le impronte dei piani e la provenienza dei modelli.

I vecchi risultati, le vecchie cache e le copie della documentazione sono tutti
in `archivio/`. Le istruzioni al suo interno descrivono il passato. La mappa dei
materiali è nel [README dell’archivio](../archivio/README.md).

Dataset e artefatti attuali generati sono esclusi da Git. Le copie di sicurezza e le diagnosi archiviate restano locali.
Il materiale storico già versionato, compresa la sua cache, conserva invece
la possibilità di essere seguito da Git nel nuovo percorso. Un aggiornamento del codice
non trasferisce quei file tra i due computer.

## Sequenza operativa sui due computer

Eseguire i comandi dalla radice del progetto, dentro Ubuntu o WSL. I due
computer devono usare lo stesso commit e lo stesso `uv.lock`. Il comando
`git rev-parse HEAD` permette di confrontare i commit.

Dopo i controlli iniziali, l’orchestratore mostra e prepara la sequenza:

    .venv/bin/python scripts/16_run_pipeline_v2.py plan
    .venv/bin/python scripts/16_run_pipeline_v2.py prepare

La preparazione verifica ambiente, Target e corpus, materializza train e
validation e congela i piani. Se i vecchi piani riportano 300 secondi e due
processi, usare prima il riallineamento descritto sopra.

Sul **PC Dataset**:

    .venv/bin/python scripts/16_run_pipeline_v2.py qiskit-canary
    .venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full

Questa produzione è già completa sulla macchina verificata il 9 settembre.
Per controllarla senza rigenerare risultati:

    .venv/bin/python scripts/10_aggregate_qiskit_dataset.py --require-all-supported --check-only

Sul **PC Modelli**, indipendentemente dal popolamento Qiskit:

    .venv/bin/python scripts/16_run_pipeline_v2.py rl --group models
    .venv/bin/python scripts/16_run_pipeline_v2.py ml-canary
    .venv/bin/python scripts/16_run_pipeline_v2.py ml --timeout 100

Il comando RL allena i cinque dispositivi in sequenza. Salta i modelli finali
conformi e riprende il checkpoint valido più avanzato. Il comando ML parte dopo
i cinque RL e usa un worker per le compilazioni RL e uno per la Random Forest.
Il limite di sei processi riguarda il popolamento Qiskit, non questi training.

Per riunire i risultati sul PC Dataset, copiare dal PC Modelli la directory
`models/` completa dell’esperimento e il relativo `training_set/`. Conservare
sempre ogni modello insieme ai suoi metadati. Verificare gli hash prima di
sostituire file presenti. Checkpoint e log possono restare sul PC Modelli.

## Bootstrap e controlli iniziali

Dalla radice del repository, dentro Ubuntu o WSL:

    bash scripts/bootstrap_ubuntu.sh
    source .venv/bin/activate
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    uv lock --check
    uv sync --frozen --python 3.12
    .venv/bin/python scripts/01_check_install.py --require-frozen-targets
    .venv/bin/python scripts/06_prepare_experiment_v2.py --check-only

Il controllo senza --require-models deve riuscire anche prima del training.
Deve però dire con chiarezza che i modelli non sono pronti.

Poi si prepara soltanto train e validation:

    .venv/bin/python scripts/06_prepare_experiment_v2.py
    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split validation
    .venv/bin/python scripts/11_freeze_method_plan_v2.py --split test

Il comando 06 verifica tutti i 600 hash, ma materializza solo 422 train e 88
validation. Non estrae feature del test e non crea una directory test v2.

## Canary del Dataset Qiskit

I canary usano soltanto train e la stessa politica della prova completa:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split train \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 6 \
        --timeout-seconds 100 \
        --limit-runs 1
    done

Ripetendo lo stesso comando, il record già concluso è riconosciuto. Il limite
seleziona poi il primo tentativo mancante. Il popolamento completo può quindi
proseguire senza ricominciare.

## Popolamento Qiskit di train e validation

Questa fase si avvia sul PC Dataset e può procedere in parallelo ai training RL
sul PC Modelli. Non dipende dai modelli RL/ML e non comprende il test. Il
comando operativo è:

    .venv/bin/python scripts/16_run_pipeline_v2.py qiskit-full

La sequenza esplicita equivalente richiamata dall'orchestratore è:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split train \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 6 \
        --timeout-seconds 100
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split validation \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 6 \
        --timeout-seconds 100
      .venv/bin/python scripts/09_build_qiskit_dataset_views.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --top-k 3
    done

    .venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
      --scope full \
      --catalog configs/qiskit_dataset_configurations_v2.json \
      --top-k 3 \
      --require-all-supported

Prima del test sono previsti 87120 tentativi Qiskit. I device piccoli saltano
solo i circuiti incompatibili per larghezza. Un risultato con timeout o errore
resta nel Dataset e nel denominatore.

## Cinque training RL sequenziali

I modelli pubblicabili ricevono un target di 100000 step, usano seed 0,
max_steps 64 e il profilo BQSKit registrato nei metadati. PPO lavora con
rollout da 2048 step e completa l'ultimo rollout: il contatore finale atteso è
100352. I checkpoint sono allineati ogni 10240 step, cioè ogni cinque rollout.
Un singolo latest_rollout viene inoltre sovrascritto dopo ogni aggiornamento
PPO completo: limita lo spazio occupato ma permette una ripresa precisa. Gli
snapshot interrupted sono diagnostici e non sono candidati di ripresa.

Sul PC Modelli il comando operativo sequenziale è:

    .venv/bin/python scripts/16_run_pipeline_v2.py rl --group models

I comandi espliciti equivalenti richiamati dall'orchestratore sono:

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_27 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-27-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_heron_133 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-heron-133-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_127 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-127-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_heron_156 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-heron-156-seed0

    .venv/bin/python scripts/03_train_rl_model.py \
      --device quantinuum_h2_56 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-quantinuum-h2-56-seed0

Ogni checkpoint ha un file metadata accanto. Una ripresa usa lo stesso target
richiesto di 100000 step; il modello conforme termina comunque con contatore
100352:

    .venv/bin/python scripts/03_train_rl_model.py \
      --device ibm_falcon_27 \
      --timesteps 100000 --checkpoint-every 10240 \
      --max-steps 64 --bqskit-action-timeout 60 \
      --seed 0 --run-name v2-ibm-falcon-27-seed0 \
      --resume-from PERCORSO_DEL_CHECKPOINT.zip

Un checkpoint senza metadati v2, con un altro split, seed, Target o profilo è
rifiutato. Non usare --allow-target-drift per risultati confermativi.

### Riprendere un training RL interrotto

Per Quantinuum, dalla cartella del progetto:

~~~bash
.venv/bin/python scripts/16_run_pipeline_v2.py rl --devices quantinuum_h2_56
~~~

Il comando cerca automaticamente il checkpoint valido più avanzato e mantiene
il nome della run. TensorBoard continua nella stessa cartella MaskablePPO già
usata, con il contatore dei passi del checkpoint. Può comparire un nuovo file
di eventi nella stessa cartella: TensorBoard lo mostra come parte dello stesso
allenamento. Non usare `--no-auto-resume` per questa operazione.

Ripartono solo i passi successivi all'ultimo rollout salvato. Il file
`interrupted.zip`, quando presente, serve alla diagnosi e non alla ripresa.
Ogni ripresa conserva il CSV precedente e scrive gli episodi in un nuovo file
`resume-*.monitor.csv` dentro la stessa run. I CSV conservano anche i tentativi
successivi al checkpoint poi scartati: non vanno sommati come passi del modello.
Il riferimento per il progresso acquisito resta il contatore del checkpoint.

### Limite della ricerca VF2 durante il training RL

Dall'8 settembre 2026, i nuovi training limitano VF2Layout a 10000
estensioni della ricerca e usano il seed della run. Senza questo limite,
la ricerca sul target Quantinuum poteva occupare una CPU per ore e fermare
il contatore a 419 passi. Il timeout di BQSKit non copre questa operazione.

Il limite è applicato nello script di training, senza modificare i pacchetti
installati. Le azioni RL restano le stesse. Se VF2 non trova un layout entro
il limite, l'ambiente può scegliere un'altra azione. La ricerca può quindi
fermarsi prima di trovare il layout migliore: è una scelta di tempo di calcolo,
non una garanzia di qualità. I metadati riportano `qiskit_vf2_layout` con
profilo, limite e seed. La ripresa accetta solo salvataggi con lo stesso profilo,
per evitare di mescolare due condizioni di training nella stessa run.
I modelli già completati conservano le loro condizioni originali.

### Limite dei qubit su Heron

MQT Predictor 2.4.0 dichiara uno spazio per il numero di qubit che arriva a
127. La mappatura può invece allargare un circuito ai 133 o 156 qubit fisici
di Heron. Questo provocava l'errore
`Class values must be smaller than num_classes` durante il training.

Lo script 03 adatta ora questo limite al dispositivo prima di creare o
ricaricare PPO. Conserva il numero reale di qubit e registra il limite nei
metadati del modello. La policy salvata conserva anche lo spazio corretto,
che viene usato nelle predizioni successive. Per Falcon e Quantinuum lo spazio
resta identico: Falcon 27 già completato non richiede un nuovo training.
Dopo questa correzione basta rilanciare lo stesso comando del gruppo.

### Log e arresto del training

Per interrompere un training premere Ctrl+C una volta e attendere il salvataggio
diagnostico. Per riprendere, rilanciare lo stesso comando dell’orchestratore.
Lo snapshot `interrupted` non è un checkpoint di ripresa.

Per visualizzare i log, dalla radice del progetto:

    .venv/bin/tensorboard --logdir artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/logs/rl/ --host 127.0.0.1 --port 6006

Ogni modello finale deve avere insieme il file
`model_expected_fidelity_<device>.zip` e il corrispondente `.metadata.json`
nella directory `models/rl/` dell’esperimento.

## Training set e classificatore ML

Dopo i cinque training RL si esegue prima un lotto compile-only riutilizzabile:

    .venv/bin/python scripts/16_run_pipeline_v2.py ml-canary

Non esistono ancora misure ML pregresse pertinenti; i tempi Qiskit non sono
trasferibili alla compilazione tramite policy RL. Il canary usa i primi 10
circuiti train, un worker, un tentativo e un limite di 100 secondi.
Registra stato e duration_seconds nel manifest durevole:

    artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/cache/ml/expected_fidelity/manifest.jsonl

Il limite concordato è 100 secondi anche per la generazione completa.
Il valore viene registrato nei metadati della run.

Il run completo è:

    .venv/bin/python scripts/16_run_pipeline_v2.py ml --timeout 100

Il comando usa soltanto i 422 circuiti train. Ogni coppia
circuito-dispositivo ha un checkpoint durevole. Sono accettate solo
compilazioni RL riuscite, terminate da terminate e valide sul Target. Non c'è
un fallback Qiskit pubblicabile.

La pubblicazione del classificatore richiede tutte e cinque le classi e 49
feature. Una copertura parziale può essere studiata con --allow-incomplete, ma
non produce il modello confermativo.

## Sincronizzazione e canary qcompile

    .venv/bin/python scripts/05_sync_models.py install --overwrite
    .venv/bin/python scripts/05_sync_models.py verify
    .venv/bin/python scripts/01_check_install.py \
      --require-frozen-targets --require-models
    .venv/bin/python scripts/07_validate_qcompile.py \
      --timeout 100 --max-steps 64

Il canary usa un circuito train. Esegue una compilazione RL diretta per ognuno
dei cinque device e una prova end-to-end di qcompile. Tutte e sei devono
riuscire. Una trace vuota, troncata o non conclusa da terminate fallisce.

L’esecuzione completa di qcompile sulla validation non è richiesta.
qcompile partecipa al confronto finale sul test, dopo i controlli sopra indicati.
Il runner mantiene processi nuovi per ogni ripetizione e conserva subito
successi, timeout e fallimenti.

## Selezione locale LLM sulla validation

La procedura operativa è in [guida della selezione LLM](approfondimenti/selezione_llm.md).
 L’infrastruttura offre controllo dello stato,
pausa dopo il circuito corrente, ripresa e generazione delle analisi.
Alla consegna del codice la validation non è ancora eseguita: non esistono
una configurazione finale scelta o risultati sperimentali da dichiarare.
Le impostazioni suggerite nella guida sono profili tecnici da verificare.

La selezione riguarda Qwen3.5-4B, Phi-4-mini-instruct e Gemma 4 E4B-it.
Gemma E2B-it resta un’alternativa se E4B non è sostenibile. Prima delle prove
si registrano repository, revisioni, impronte dei pesi e provenienza della
conversione GGUF. Una revisione del modello originale osservata oggi non
dimostra da sola quale revisione sia stata usata dal convertitore.

I pesi risiedono in D:/Tesi-mqt/llm-selection/, nella sottodirectory
dell’esperimento. Il percorso Linux negli artefatti resta utilizzabile tramite
un collegamento. Il disco D: dispone dello spazio necessario; il limite della
RAM e quello della memoria video sono valutati separatamente.
L’esecutore llama.cpp b10930 per Windows usa Vulkan sulla Radeon RX 6750 XT.
Il codice MQT resta nel suo ambiente Python 3.12 con uv.lock invariato.

Le prove tecniche usano soltanto richieste sintetiche o circuiti train.
Misurano caricamento, contesto, generazione e validazione delle risposte.
Non sono risultati della selezione. I pesi originali sono provati quando
sostenibili. Una cache a precisione ridotta è registrata separatamente dalla
precisione dei pesi. Le richieste complete sono contate con il tokenizer
effettivo. Fino al 17 settembre non si eliminavano contenuti dal prompt. Un caso che supera
il contesto nativo resta un fallimento di contesto, con zero chiamate LLM.
Non si estende arbitrariamente il contesto nativo di Gemma per nascondere
questo limite. Per i soli grafi completi, l’elenco ordinato degli archi viene
sostituito da una regola esatta che consente di ricostruire tutti gli archi
nello stesso ordine. Il programma controlla la reversibilità. I prompt originali
restano conservati. Il requisito storico di conservare ogni contenuto nel
prompt è superato dalla vista essenziale descritta sotto.

Nella revisione storica del 15 settembre la rappresentazione degli input usa identificativi brevi
delle fonti, oggetti condivisi per i valori ripetuti e tabelle con intestazioni
comuni. La decodifica deve ricostruire esattamente ogni campo e valore originale,
compresi QASM, metrica e cinque esempi RAG. Lo schema di risposta 2.0.0 rimane
invariato. Le sigle delle fonti vengono ripristinate prima della validazione,
senza inventare campi o correggere scelte. Istruzioni più esplicite chiariscono
le relazioni fra claim, riferimenti e fonti. È corretto il salvataggio degli
errori contenenti dizionari immutabili, che impediva la normale correzione
delle risposte. Il validatore semantico conserva tutti i suoi vincoli.

Il controllo su 93 prompt preparati (5 train, 88 validation) conferma la
reversibilità. Il recupero è stato rieseguito sui cinque train: l'esempio dello
stesso sorgente e della stessa metrica compare sempre a distanza zero, al primo
posto in quattro casi e al secondo per `portfoliovqe_indep_qiskit_6`, che ha
più risultati a pari distanza. L'ordine del RAG resta quello originale.
Il controllo non apre gli score validation o il test. Le prove train registrano
se la risposta valida cita quell'esempio per entrambe le scelte e distingue
l'etichetta principale dalle configurazioni a pari merito. Questo verifica
il funzionamento su esempi già presenti nel Dataset, non la generalizzazione.
Misure, comandi e limiti sono in [resoconto sul prompt compatto](resoconti/2026-09-15_prompt_compatto.md).
I nuovi prompt richiedono nuovi nomi delle prove; gli esiti precedenti restano.
Dal 16 settembre codifica e messaggi sono centralizzati in `prototype/prompting/`,
come descritto nella [guida comune](approfondimenti/compattazione_prompt.md).
La centralizzazione conserva i messaggi precedenti e non modifica Dataset,
recupero, schema di risposta o parametri della selezione. La scelta del modello
nella [chat manuale](approfondimenti/chat_locale.md) resta separata dalla selezione.
Alla ripresa era già presente un limite di uscita di 4096 token, conservato:
il confronto con le prove iniziali da 2048 deve dichiarare tale differenza.

Il controllo SHA-256 dei pesi prima dell’avvio usa Windows sul percorso nativo
per evitare una lettura dei grandi file attraverso la cache WSL. Il registro
conserva impronta, dimensione, metodo e durata. Questa modifica del 14 settembre
segue l’arresto tecnico `qwen-prova-01`, avvenuto per RAM libera insufficiente
prima di qualsiasi generazione. I tentativi precedenti restano conservati.

Dal tentativo successivo a `qwen-prova-03`, i nuovi registri del server e del
monitor Windows sono scritti direttamente sul disco D. Nel progetto rimane
un collegamento per ogni esecuzione; gli artefatti precedenti non sono spostati.
La modifica segue un errore `Flush(true)` sulla condivisione WSL: il salvataggio
forzato è mantenuto e sono aggiunti operazione, percorso, tipo di eccezione
e ultimo campione salvato alla diagnostica. La causa interna dell’annullamento
non è stata dimostrata. Il controllo breve su D verifica soltanto il nuovo
percorso di scrittura, non la stabilità di un’intera inferenza.

Il server usa il caricamento senza mappatura del file in memoria. Il monitor
campiona le risorse circa ogni secondo. I valori predefiniti rilevati nel codice
il 15 settembre (`llm_selection/hardware.py` e `serve.ps1`) sono: pausa a
105 °C di hotspot, ripresa sotto 100 °C, arresto a 108 °C di hotspot o 95 °C
di edge; arresto per RAM libera sotto 1,5 GiB per tre campioni consecutivi.
La precedente descrizione riportava 80/65 °C per pausa/ripresa e 95/85 °C per
arresto hotspot/edge: era rimasta indietro rispetto al codice già presente.
Il riordino aggiorna questa descrizione, senza cambiare le impostazioni.
Per interpretare una prova valgono i parametri salvati nel suo registro.
Questi limiti operativi non sono una diagnosi dello spegnimento del PC.
Le pause sono registrate e contribuiscono ai tempi e al timeout.
Non vengono modificate frequenze, tensioni o ventole.

Prima di consultare gli score si congela una griglia piccola e comune.
La griglia in preparazione confronta tre configurazioni per ciascuna famiglia:
prompt di base con temperatura 0; stesso prompt con temperatura 0,7;
prompt con istruzioni di controllo più esplicite e temperatura 0.
Le prove train possono correggere problemi tecnici prima del congelamento.
Tutti i tentativi precedenti restano conservati e distinti.

Le condizioni comuni comprendono gli stessi 88 circuiti, i cinque dispositivi,
le dodici configurazioni Qiskit, la maschera di compatibilità, cinque esempi
RAG e la stessa regola Manhattan sulle 49 feature. Il contenuto informativo
resta uguale fra famiglie; ciascuna usa il proprio formato di chat.
La generazione usa lo schema JSON; il validatore del prototipo verifica anche
compatibilità, piano e correttezza delle evidenze. L’applicazione del formato
di chat è separata dalla generazione nativa per evitare il problema osservato
fra lo schema e il prefisso di ragionamento Qwen. Non si altera quel prefisso.

La configurazione congelata registra temperatura, top_p, top_k di generazione,
min_p, penalità, seed, cache, contesto, limite di uscita, timeout e ragionamento.
Il top_k di generazione non è il numero k di esempi RAG. Il limite iniziale
di uscita era 2048 token; il codice corrente usa 4096. Ogni prova conserva
il proprio limite e i confronti devono dichiarare la differenza. Il timeout
predefinito è 3600 secondi per chiamata. Il ragionamento esteso è disabilitato.
La cache riusa soltanto prefissi identici. L’ordine delle tre configurazioni
ruota fra circuiti; tempi e token riutilizzati restano visibili. Non si inserisce
nel prompt la risposta valida ottenuta da un’altra configurazione.

Il primo output valido è definitivo. Sono ammesse al massimo tre chiamate,
solo per correggere risposte non conformi. I tentativi di trasporto non sono
ripetuti automaticamente. Un’interruzione con esito incerto è registrata;
non viene nascosta rilanciando la chiamata. Ogni esito terminale è conservato.
La raccolta parte prima delle chiamate e comprende input, output, evidenze,
errori, token, tempi, memoria e provenienza. I dati mancanti restano null,
con metodo di misura e causa. Non si inventano costi energetici.

Il programma di generazione non apre la matrice Qiskit della validation.
Tutte le decisioni delle configurazioni vengono sigillate prima della
valutazione. Il valutatore controlla identità, completezza e impronte, poi
riusa la matrice già prodotta. I tempi Qiskit storici restano distinguibili
dai tempi delle nuove chiamate LLM.

La scelta mantiene l’ordine previsto: completamento valido e compilabile,
regret assoluto mediano sui circuiti confrontabili, validità al primo
tentativo, numero di chiamate, latenza e token. Non si assegna un regret
inventato ai fallimenti. Si mostrano sia i denominatori di ogni configurazione
sia gli insiemi comuni dei confronti. L’unità statistica è il circuito:
i tre seed Qiskit e le correzioni non diventano osservazioni indipendenti.
I risultati della validation motivano la scelta; non provano una superiorità
definitiva del modello.

La configurazione vincente viene congelata insieme a modelli, prompt,
retrieval, regole di correzione e ambiente. Lo stesso modello e le stesse
impostazioni saranno usati senza RAG sul test, senza una seconda selezione.
Prima del test sono ammesse solo prove tecniche senza RAG su train.
La scelta del modello di frontiera e i suoi parametri devono essere dichiarati
prima del test. La loro assenza non blocca questa selezione locale.

Il file configs/experiment_methods_v2.json mantiene i tre ruoli finali.
Il congelamento locale può essere completo mentre il ruolo di frontiera
è ancora da configurare: in quel caso il file complessivo non viene dichiarato
congelato e il test resta chiuso. I piani già estratti conservano le scelte
casuali originali. Le liste dei metodi finali contenute nel piano storico
non impongono l’esecuzione di quei metodi nella selezione locale: il manifest
della selezione dichiara esplicitamente questo ambito ridotto.

### Vista essenziale e citazioni locali — 18 settembre 2026

La vista introdotta con `minimal-v3-20260918` usa JSON, senza TOON.
Conserva cinque esempi, ordine del recupero, tutte le feature e valori originali.
Elimina dal testo LLM QASM, hash, manifest, metadati e ripetizioni delle evidenze.
Il catalogo hardware compare una volta; gli esempi ne indicano solo i nomi.
Il registro completo rimane interno al prototipo.

La risposta v3 richiede `selected_device`, `config_id`, `claim` ed `evidence`.
Il claim è testo libero breve; evidence contiene alias E1...E5 degli esempi.
I parametri Qiskit derivano dal catalogo. Il seed del piano singolo è il primo
seed previsto, attualmente 0; le ripetizioni sperimentali restano governate dal
protocollo. Metadati della richiesta e versione sono assegnati dal programma.

Il validatore controlla scelta compatibile, configurazione ammessa e citazioni
risolvibili nel contesto della richiesta. Rifiuta riferimenti sconosciuti o
ripetuti. Non richiede claim/caveat strutturati né ID multilivello.
La risoluzione delle citazioni non prova l'uso causale degli esempi e non
verifica semanticamente ogni affermazione libera. Questo limite va riportato
nelle analisi; i successi v3 non sono direttamente equivalenti ai successi del
vecchio controllo semantico v2. Senza RAG le evidenze sono vuote.

Il documento canonico, le mappe, le richieste inviate e le risposte restano
conservati. Nessun vecchio tentativo viene riscritto o dichiarato riuscito
secondo il nuovo contratto. Serve una nuova etichetta per nuove esecuzioni.
Le misure su tre casi train del 18 settembre riguardano soltanto i token;
non costituiscono selezione sulla validation o prova di qualità.
Vedere la [guida del prompt essenziale](approfondimenti/compattazione_prompt.md).

La revisione `minimal-v3-repair1-20260918` modifica solo le correzioni:
una frase indica il campo errato e il catalogo o gli esempi dai quali scegliere.
I messaggi di uno stesso tipo sono accorpati; una sola istruzione finale chiede
il JSON completo per il circuito corrente. Non si copiano cataloghi, risposte
errate o identificativi canonici. Senza RAG si chiede evidence vuota.
Il primo prompt, gli esempi, le feature e il massimo di tre tentativi restano
invariati. Una revisione diversa richiede una nuova etichetta anche per una
prova interrotta. L'efficacia delle nuove correzioni richiede nuove inferenze;
i fallimenti storici restano conservati.



### Codifica TOON — 19 settembre 2026

La revisione `minimal-v3-toon1-20260919` codifica in TOON i dati della vista
essenziale. Lo schema leggibile e la risposta richiesta restano JSON.
Usa l'encoder ufficiale `@toon-format/toon` 4.1.1, con runtime locale
e versioni fissate. Le feature condividono una tabella; gli archi hardware
possono essere raggruppati per sorgente. Ogni conversione è decodificata
e ricostruita prima dell'invio, verificando valori, zeri e ordine degli archi.
Non cambia il recupero, il numero di esempi, i controlli o le correzioni.

Sui cinque circuiti train, i tokenizer nativi misurano una riduzione aggiuntiva
rispetto al JSON essenziale pari a 8,12% per Qwen, 4,64% per Phi e 9,80% per
Gemma. Sono somme di token di ingresso, con template di chat e schema inclusi;
non sono misure di qualità o consumo delle risposte.
Le nuove richieste sono preparate e contate, non ancora eseguite.
Le prove tecniche useranno nuove etichette prima del congelamento della
selezione sulla validation. Il test resta separato.

Il [resoconto](resoconti/2026-09-19_prompt_toon.md) collega il documento completo,
le figure, i 15 confronti per circuito, le richieste originali o ricostruite,
i token misurati e le procedure riproducibili.

## Valutazione della selezione e confronto finale

Il valutatore della selezione non richiede qcompile, il modello di frontiera
o la variante senza RAG. Usa le scelte LLM con RAG e i riferimenti Qiskit.
Lo score di una coppia è la mediana dei tre seed 0, 1 e 2, soltanto quando
tutti riescono. L’oracle esiste soltanto se l’intera matrice compatibile
del circuito è riuscita. I timeout restano terminali; non si calcola un
massimo parziale facendolo passare per oracle.

Il confronto finale sul test mantiene tutti i metodi previsti:

- LLM scelto con RAG e stesso LLM senza RAG;
- modello di frontiera;
- MQT Predictor con qcompile;
- Qiskit livello 2 e 3 per ciascun dispositivo;
- scelta Qiskit casuale congelata e oracle esaustivo.

Il codice rifiuta una valutazione test che escluda un metodo richiesto.
Le analisi confermative, inclusa la verifica del contributo del RAG, riguardano
il test. Le analisi della selezione sono descrittive, con intervalli bootstrap
a livello di circuito, seed e denominatori dichiarati.

Per la tesi si conservano dati originali JSON/JSONL, riepiloghi esportabili,
procedure di analisi e figure. Il resoconto LaTeX include impostazioni,
tentativi scartati, risultati, motivazione della scelta e limiti. Sono previsti
un sorgente inseribile tramite input nella tesi e una compilazione autonoma
controllata visivamente.

## Gate che apre il test

Il comando di audit è:

    .venv/bin/python scripts/15_release_test_v2.py

Il test può essere aperto solo se sono veri tutti questi gate:

1. versioni software esatte;
2. cinque Target senza drift;
3. corpus e partizioni train/validation integri;
4. catalogo e configurazione LLM congelati;
5. piani validation e test identici a quelli ricalcolati;
6. matrice Qiskit validation completa;
7. JSONL solo train e raccolta Qdrant effettiva completa, con vettori, dati
   associati, impronte e divisori coerenti; verifica tecnica sugli 88 validation
   riferita alla stessa raccolta e a `k=5`;
8. cinque modelli RL con target 100000, contatore 100352 e classificatore ML a cinque classi;
9. cinque canary RL e un canary qcompile riusciti;
10. selezione locale validation completa, con tutti i sigilli verificati,
    risultati canonici e prova `llm_selection/selection_complete.json` integra.

Solo dopo l'audit positivo:

    .venv/bin/python scripts/15_release_test_v2.py --release

Il record di apertura include manifest, trasformazione, file persistenti Qdrant
(escluso il blocco di accesso) e resoconto tecnico validation. Se uno cambia,
ogni comando test torna a fallire.

## Procedura dopo l'apertura del test

Prima si materializza il test nei cinque manifest:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/07_prepare_qiskit_dataset.py \
        --scope full \
        --include-test \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device
    done

Poi si producono e si importano le tre decisioni LLM test. In questa fase non
devono ancora esistere score Qiskit test visibili agli esecutori:

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method llm_rag \
      --input PERCORSO_LLM_RAG_TEST.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method llm_no_rag \
      --input PERCORSO_LLM_NO_RAG_TEST.jsonl

    .venv/bin/python scripts/13_import_llm_decisions_v2.py \
      --split test --method frontier_llm \
      --input PERCORSO_FRONTIER_TEST.jsonl

Si esegue qcompile:

    .venv/bin/python scripts/12_run_qcompile_v2.py \
      --split test --timeout 100

Solo dopo si popola la matrice Qiskit test:

    for device in ibm_falcon_27 ibm_heron_133 ibm_falcon_127 ibm_heron_156 quantinuum_h2_56
    do
      .venv/bin/python scripts/08_generate_qiskit_dataset.py \
        --scope full \
        --split test \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --workers 6 \
        --timeout-seconds 100
      .venv/bin/python scripts/09_build_qiskit_dataset_views.py \
        --scope full \
        --catalog configs/qiskit_dataset_configurations_v2.json \
        --device $device \
        --top-k 3
    done

    .venv/bin/python scripts/10_aggregate_qiskit_dataset.py \
      --scope full \
      --catalog configs/qiskit_dataset_configurations_v2.json \
      --top-k 3 \
      --require-all-supported

    .venv/bin/python scripts/14_evaluate_methods_v2.py --split test

La ricostruzione delle viste non può aggiungere validation o test all'indice
RAG. Il file RAG congelato deve restare identico.

## Politica di ripresa

- Qiskit accetta una cache soltanto se coincidono esperimento, protocollo,
  schema, circuito, SHA-256, Target, versione, configurazione, seed, timeout e
  parallelismo.
- RL salva archivio e metadati in modo atomico. La ripresa rifiuta checkpoint
  senza provenienza v2.
- Il Training set ML salva un record per ogni coppia circuito-device. I worker
  hanno timeout reale e i processi discendenti vengono terminati.
- qcompile salva ogni ripetizione terminale. Un record fuori split o con
  identità diversa viene rifiutato.
- I risultati 2.3.0 non sono mai usati come cache 2.4.0.

## Verifiche locali

    .venv/bin/python -m unittest discover -s tests -v
    .venv/bin/python -m compileall -q qiskit_dataset prototype scripts tests
    .venv/bin/python scripts/01_check_install.py --require-frozen-targets
    .venv/bin/python scripts/06_prepare_experiment_v2.py --check-only
    git diff --check

Il comando seguente deve fallire fino al training completo:

    .venv/bin/python scripts/07_validate_qcompile.py \
      --timeout 100 --max-steps 64

Anche qualsiasi accesso test deve fallire prima del record di apertura,
compresa la modalità dry-run.

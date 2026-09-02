# Protocollo sperimentale definitivo

| Campo | Valore |
| --- | --- |
| Versione | 1.0 |
| Stato | approvato e congelato |
| Unità primaria di analisi | circuito sorgente |
| Metrica primaria di qualità | `expected_fidelity` |

Questo documento è la fonte ufficiale del protocollo. Le descrizioni presenti nel
resto del repository spiegano codice e artefatti, ma non possono cambiare le
regole definite qui.

## 1. Scopo

L'esperimento valuta se il sistema completo LLM + RAG sceglie un dispositivo e
una configurazione Qiskit che producono circuiti compilati di buona qualità, con
tempi e affidabilità accettabili.

La scelta riguarda congiuntamente:

1. il dispositivo sul quale compilare;
2. una delle dodici configurazioni Qiskit ammesse.

La qualità è stimata fuori linea sui Target sintetici di MQT Bench. Non vengono
eseguiti circuiti su hardware quantistico reale.

## 2. Termini e confini dell'esperimento

Nel protocollo i termini seguenti non sono intercambiabili.

- **Dataset**: esempi ottenuti dalle compilazioni Qiskit e destinati al RAG. La
  parte di training può essere indicizzata in Qdrant. Le parti di validation e
  test restano separate dall'indice.
- **Training set di MQT Predictor**: coppie circuito-dispositivo e relativi dati
  usati per addestrare il classificatore supervisionato e i modelli RL. Non è il
  Dataset del RAG.
- **Training**: 422 circuiti usati per costruire il Dataset e l'indice RAG.
- **Validation**: 88 circuiti usati soltanto per scegliere modelli e parametri.
- **Test**: 90 circuiti usati una sola volta per la valutazione finale, dopo il
  congelamento di tutte le scelte.
- **Ripetizione sperimentale**: una nuova esecuzione programmata del compilatore.
- **Seed Qiskit**: il valore controllato che rende identificabile la casualità di
  una ripetizione Qiskit.
- **Tentativo LLM**: una chiamata al modello. Un nuovo tentativo dovuto a una
  risposta non valida non è una nuova ripetizione sperimentale.

L'aggiunta di circuiti esterni a MQT Bench è rinviata a un esperimento separato.

## 3. Domande di ricerca

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

## 4. Ipotesi

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

## 5. Disegno sperimentale e unità di analisi

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

### 5.1 Richiesta canonica

Per ogni circuito viene costruita meccanicamente una sola richiesta. Contiene il
file OpenQASM esatto, l'obiettivo `expected_fidelity`, l'impronta del catalogo e
i cinque dispositivi iniziali. Non attiva preferenze facoltative per fornitore,
costo, latenza o dispositivo. La maschera del prototipo elimina poi i candidati
incompatibili con circuito e Target. La richiesta è identica per sistema completo
e variante senza RAG; il LLM di frontiera riceve lo stesso circuito e lo stesso
spazio di scelta, ma non la maschera calcolata.

## 6. Dataset e suddivisioni

Il manifesto corrente contiene 600 file OpenQASM 2:

| Suddivisione | Circuiti | Uso consentito |
| --- | ---: | --- |
| training | 422 | costruzione del Dataset e dell'indice RAG |
| validation | 88 | scelta e regolazione dei componenti |
| test | 90 | valutazione finale dopo il congelamento |

I circuiti di test sono quelli in
[`datasets/expected_fidelity/full/circuits/test/`](../datasets/expected_fidelity/full/circuits/test/).
Non è permesso sostituirli dopo aver osservato i risultati.

Il controllo attuale degli hash rileva 574 contenuti unici. I 26 alias esatti
sono tutti nel training. Non risultano hash OpenQASM identici tra training,
validation e test. Gli alias nel training possono essere conservati su disco,
ma in Qdrant deve esistere al massimo un esempio recuperabile per ogni hash del
circuito sorgente. Gli alias devono essere elencati nel manifesto e non devono
aumentare il peso di un esempio nel recupero.

La famiglia è ricavata dal nome canonico del circuito, prima del segmento
`_indep_`. Questa regola viene applicata prima del test e non viene corretta in
base ai risultati.

La generazione avviene per fasi:

1. training e validation possono essere compilati prima del congelamento;
2. soltanto il training può alimentare Qdrant;
3. i risultati della validation possono essere letti per scegliere i parametri;
4. i risultati del test e l'oracle possono essere prodotti solo dopo il
   congelamento.

## 7. Hardware

Sono ammessi esclusivamente i dispositivi seguenti, nell'ordine del catalogo
versionato:

1. `ibm_falcon_27`;
2. `ibm_heron_133`;
3. `ibm_falcon_127`;
4. `ibm_heron_156`;
5. `quantinuum_h2_56`.

L'ordine è importante perché partecipa al tie-break dell'oracle. Non va sostituito
con l'ordine alfabetico o con quello usato nel testo introduttivo.

Un dispositivo è candidato soltanto se `num_qubits` del circuito è minore o
uguale alla sua capacità. Dopo la compilazione devono inoltre essere verificati
il Target, i gate di base e i vincoli di connettività. Un circuito troppo largo
per un dispositivo è **non applicabile**, non è una compilazione fallita.

Nel test corrente le compatibilità basate sulla larghezza sono:

| Dispositivo | Circuiti di test compatibili |
| --- | ---: |
| `ibm_falcon_27` | 72 |
| `ibm_falcon_127` | 90 |
| `ibm_heron_133` | 90 |
| `ibm_heron_156` | 90 |
| `quantinuum_h2_56` | 84 |

I Target sono quelli sintetici prodotti da MQT Bench per gli identificativi del
catalogo. Le loro impronte devono essere calcolate e congelate nel manifesto.
Non è consentito sostituirli con backend IBM o Quantinuum correnti.

## 8. Spazio delle configurazioni Qiskit

La fonte normativa è
[`configs/qiskit_dataset_configurations.json`](../configs/qiskit_dataset_configurations.json).
Lo spazio contiene esattamente dodici configurazioni:

| Ordine | `config_id` | Livello | Layout | Instradamento |
| ---: | --- | ---: | --- | --- |
| 1 | `o2_default_default` | 2 | predefinito | predefinito |
| 2 | `o3_default_default` | 3 | predefinito | predefinito |
| 3 | `o2_sabre_sabre` | 2 | `sabre` | `sabre` |
| 4 | `o2_dense_sabre` | 2 | `dense` | `sabre` |
| 5 | `o2_trivial_sabre` | 2 | `trivial` | `sabre` |
| 6 | `o3_sabre_sabre` | 3 | `sabre` | `sabre` |
| 7 | `o3_dense_sabre` | 3 | `dense` | `sabre` |
| 8 | `o3_trivial_sabre` | 3 | `trivial` | `sabre` |
| 9 | `o2_sabre_lookahead` | 2 | `sabre` | `lookahead` |
| 10 | `o2_sabre_basic` | 2 | `sabre` | `basic` |
| 11 | `o3_sabre_lookahead` | 3 | `sabre` | `lookahead` |
| 12 | `o3_sabre_basic` | 3 | `sabre` | `basic` |

Le opzioni fisse sono `approximation_degree=1.0` e `num_processes=1`. Per i
campi predefiniti non deve essere passato un algoritmo esplicito a Qiskit. Non
sono ammesse configurazioni costruite dal modello o dalla baseline casuale.

## 9. Metodi confrontati

### 9.1 Sistema completo LLM + RAG

È il sistema proposto. Riceve la richiesta strutturata, il catalogo e la maschera
hardware. Calcola le feature del circuito e recupera da Qdrant esempi storici del
solo training. Il recupero usa una distanza tra vettori di feature. Prompt,
evidenze, claim, schema di uscita, controlli e tentativi sono quelli congelati.

La trasformazione delle feature, la distanza, la normalizzazione, `k` e tutti i
parametri dell'indice sono scelti soltanto sulla validation. Il recupero locale
provvisorio del prototipo non è l'implementazione finale richiesta da questo
metodo.

Dopo una raccomandazione valida, la coppia scelta viene compilata con i seed 0,
1 e 2. Non viene cercata una coppia alternativa se una compilazione fallisce.

### 9.2 Stesso LLM senza RAG

Usa esattamente lo stesso `selected_llm`, gli stessi parametri, la stessa
richiesta, lo stesso catalogo, la stessa maschera, lo stesso schema, gli stessi
controlli e lo stesso limite di tentativi. Sono disattivati soltanto il recupero
e le evidenze storiche. Il campo delle evidenze deve essere vuoto secondo la
variante congelata dello schema; non può contenere esempi inseriti manualmente.

La compilazione successiva è identica a quella del sistema completo.

### 9.3 LLM di frontiera senza prototipo

Usa `frontier_llm_baseline` con un prompt diretto. Il prompt contiene il circuito,
i cinque dispositivi e le dodici configurazioni ammesse. Non usa RAG, vettori di
feature, maschera applicativa, registro delle evidenze, controlli guidati o
tentativi guidati dagli errori.

Il formato minimo è un unico oggetto JSON, senza testo, blocchi Markdown o campi
aggiuntivi:

```json
{"selected_device": "ibm_falcon_27", "config_id": "o2_default_default"}
```

Il lettore accetta soltanto stringhe che coincidono esattamente con il catalogo.
Non corregge mai nomi, maiuscole, configurazioni o dispositivi. Dopo la lettura,
un controllo meccanico registra l'eventuale incompatibilità; non fornisce
feedback al modello e non avvia un nuovo tentativo. Una risposta assente, non
interpretabile o incompatibile è un fallimento.

### 9.4 MQT Predictor

MQT Predictor deve usare il classificatore supervisionato per scegliere il
dispositivo e il modello RL associato per compilare. Il metodo è ammesso nella
valutazione confermativa soltanto se, prima dell'apertura del test, sono
verificate tutte queste condizioni:

- il classificatore è addestrato e può restituire tutti e cinque i dispositivi;
- sono presenti e caricabili cinque modelli RL per `expected_fidelity`;
- ogni modello è legato in modo verificabile al dispositivo dichiarato;
- `qcompile` supera un controllo funzionale nell'ambiente congelato;
- la provenienza del Training set è documentata e non contiene i 90 circuiti di
  test né loro duplicati non dichiarati.

La presenza dei file non basta. Non si può addestrare, riparare o scegliere un
modello usando i risultati del test.

### 9.5 Qiskit `o2_default_default`

La configurazione è eseguita separatamente su ciascun dispositivo compatibile.
Le cinque coppie dispositivo-configurazione sono cinque baseline distinte. Non
si seleziona, circuito per circuito, il dispositivo con il risultato migliore.

### 9.6 Qiskit `o3_default_default`

Vale la stessa regola, con `optimization_level=3`. Anche in questo caso le cinque
coppie sono baseline distinte.

### 9.7 Baseline casuale

Per ciascuno dei tre indici di ripetizione viene estratta uniformemente una
coppia tra:

`(dispositivo compatibile, configurazione del catalogo)`.

La lista dei candidati segue prima l'ordine dei dispositivi e poi quello delle
configurazioni nel catalogo. Il generatore, il seed e la versione della libreria
sono registrati. La lista completa delle 270 estrazioni viene creata e firmata
prima dell'apertura del test. Ogni estrazione viene compilata una sola volta con
il seed Qiskit associato all'indice di ripetizione: 0, 1 o 2. Non si estrae di
nuovo dopo un fallimento.

Il seed principale previsto per la selezione casuale è `20260901`. Se una
limitazione tecnica obbliga a cambiarlo prima del test, il nuovo valore richiede
una nuova versione del manifesto, senza consultare risultati di test.

### 9.8 Oracle esaustivo

L'oracle è un riferimento superiore fuori linea, non un metodo utilizzabile in
produzione. La sua definizione è nella sezione successiva.

## 10. Oracle

Per ogni circuito di test l'oracle:

1. considera tutti i dispositivi compatibili;
2. considera le dodici configurazioni;
3. compila con i seed 0, 1 e 2;
4. rende eleggibile una coppia soltanto se tutti e tre i seed hanno successo;
5. calcola la mediana di `expected_fidelity` per la coppia;
6. sceglie la mediana numericamente più alta.

Il tie-break è deterministico. A parità numerica si usa prima l'ordine dei
dispositivi del catalogo e poi l'ordine delle configurazioni. Gli identificativi
alfabetici servono soltanto come ulteriore garanzia di stabilità. La tolleranza
`rel_tol=1e-12`, `abs_tol=1e-15` segnala una quasi parità nei resoconti, ma non
sostituisce l'ordinamento numerico e non cambia il vincitore.

Se nessuna coppia ha tre successi, l'oracle del circuito è non disponibile. Il
circuito resta nelle statistiche di affidabilità, ma non può avere un regret.

L'oracle viene calcolato esclusivamente sul test, dopo il congelamento. I suoi
risultati restano non consultabili fino a quando tutte le raccomandazioni e le
estrazioni casuali sono state salvate e firmate. Non può influenzare modello,
prompt, trasformazione delle feature, indice o `k`.

## 11. Ripetizioni, seed e tentativi

Per i metodi LLM viene richiesta una sola raccomandazione per circuito. La
raccomandazione valida è poi compilata in tre ripetizioni indipendenti, con seed
Qiskit 0, 1 e 2. In questo modo la stessa coppia è aggregata come nell'oracle.
La variabilità della decodifica LLM non viene trasformata in una ricerca tra più
risposte: parametri e, se disponibile, seed del modello sono congelati.

Il sistema completo e la variante senza RAG ammettono al massimo tre tentativi
LLM totali, cioè il primo tentativo e al massimo due nuovi tentativi. È il limite
attuale del prototipo. I nuovi tentativi servono soltanto a correggere una
risposta non conforme mediante gli errori strutturati previsti. Non consentono
di cambiare circuito, maschera, evidenze o parametri. Il primo output valido è la
raccomandazione definitiva: non si chiedono altre risposte per scegliere la
migliore.

Il LLM di frontiera esegue una sola chiamata e non riceve correzioni. I tentativi
automatici di trasporto del fornitore devono essere disattivati oppure congelati
e contati separatamente. Ogni chiamata fatturata entra nel conteggio di token e
costo.

### Regola specifica per MQT Predictor

Nella versione 2.3.0 verificata, `qcompile` non espone un seed. L'ambiente RL viene
reimpostato internamente con seed 0, mentre `predict` usa il comportamento
stocastico predefinito e i modelli dichiarano `seed=None`. Non si può quindi
applicare onestamente la terna dei seed Qiskit.

MQT Predictor viene eseguito tre volte da zero per ogni circuito. Si registra
`repetition_index` 0, 1 e 2, ma `qiskit_seed`, `mqt_sampling_seed` e un eventuale
seed della politica restano `null`. Si registrano inoltre
`mqt_env_reset_seed=0` e `policy_deterministic=false`. I tre indici non devono
essere descritti come seed controllati. Se una versione futura espone seed reali,
il cambiamento richiede una nuova versione del protocollo prima del test.

## 12. Metriche

### 12.1 Qualità primaria

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

### 12.2 Regret

Per ogni circuito con metodo e oracle disponibili:

```text
regret_assoluto = expected_fidelity_oracle - expected_fidelity_metodo
regret_relativo = regret_assoluto / expected_fidelity_oracle
```

Il regret relativo è non disponibile se il valore dell'oracle è zero. Il regret
non viene limitato artificialmente a zero: un valore negativo deve essere
conservato e indagato, perché può indicare un errore, una differenza di spazio di
ricerca o, per MQT Predictor, un compilatore esterno alle dodici configurazioni.

### 12.3 Rappresentazione logaritmica

La misura primaria resta `expected_fidelity`. Per controllare sottosoglia e forte
asimmetria si registra anche
`log_expected_fidelity = ln(expected_fidelity)` quando il valore è positivo. Se
il prodotto va numericamente a zero, il log può essere calcolato direttamente
come somma dei log dei fattori del medesimo stimatore. Se questi fattori non sono
disponibili, il log è `null` con causa `numeric_underflow`; non si sostituisce la
misura con un valore arbitrario.

### 12.4 Affidabilità, scelta, tempo e costo

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

## 13. Trattamento dei fallimenti

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
per singola compilazione è fissato a 100 secondi, come nell'ultima esecuzione
uniforme del pilota. Dopo il timeout il processo viene terminato e il risultato è
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

## 14. Analisi statistica

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

## 15. Controllo del leakage

Prima di creare l'indice e prima di aprire il test devono essere superati questi
controlli:

1. Qdrant contiene soltanto record con `split=training` e hash presenti nella
   lista ammessa del manifesto;
2. gli hash di validation e test sono assenti sia dai vettori sia dai payload e
   dagli esempi di riserva;
3. i prompt non contengono label, punteggi, vincitori o informazioni dell'oracle
   relative al test;
4. cache e registri di evidenze sono separati per suddivisione;
5. prompt, `k`, temperatura, modello, trasformazione delle feature e parametri
   dell'indice sono scelti soltanto sulla validation;
6. le raccomandazioni di test vengono firmate prima di rendere visibile
   l'oracle;
7. l'addestramento e la provenienza degli artefatti MQT Predictor sono verificati
   contro gli hash dei 90 circuiti di test.

Il controllo esistente copre i duplicati byte-identici mediante SHA-256, ma non
copre ancora i quasi-duplicati strutturali. Prima del test deve essere eseguito un
controllo congelato che confronti almeno forma canonica OpenQASM, famiglia,
numero di qubit, numero e tipi di gate e distanza tra feature. Soglia e regola di
decisione devono essere definite sulla validation, non sui risultati di test.
Ogni gruppo che attraversa le suddivisioni deve essere pubblicato. Se richiede
una correzione delle suddivisioni, la correzione deve avvenire prima del test e
incrementare la versione del protocollo.

Non è possibile escludere che MQT Bench o circuiti simili siano comparsi nei dati
di pre-addestramento di un LLM commerciale. Questo limite va dichiarato per
`selected_llm` e `frontier_llm_baseline`; non è una prova di leakage osservato e
non può essere rimosso con i controlli locali.

### Esposizione preesistente del pilota

Il pilota contiene due file che coincidono per nome e SHA-256 con il test:
`qpeexact_indep_tket_60.qasm` e `routing_indep_qiskit_12.qasm`. Le relative
compilazioni sono già presenti negli artefatti del pilota. Il test non è quindi
completamente mai osservato in senso retroattivo.

Questi risultati possono essere usati soltanto per stimare tempo e affidabilità
operativa, come richiesto da questo protocollo. Punteggi, configurazioni vincenti
e graduatorie dei due circuiti devono essere messi in quarantena e non possono
influenzare alcuna scelta. Prima del test deve essere firmata una dichiarazione
che elenca le decisioni già prese e conferma che non derivano da quei risultati.
Se questa ricostruzione non è possibile, la limitazione diventa una deviazione
confermativa e non può essere nascosta.

## 16. Scelta e congelamento degli LLM

I due ruoli sono:

- `selected_llm`: usato sia dal sistema completo sia dalla variante senza RAG;
- `frontier_llm_baseline`: usato soltanto nel prompt diretto senza prototipo.

I nomi concreti saranno scelti esclusivamente sulla validation. Per ogni
candidato si misurano qualità della raccomandazione, aderenza al JSON, tasso di
fallimento, tentativi, latenza, token e costo.

La regola di selezione è applicata nello stesso ordine a tutti i candidati:

1. massimizzare il completamento valido e compilabile;
2. minimizzare il regret assoluto mediano sulla validation;
3. massimizzare la validità JSON al primo tentativo;
4. minimizzare numero di tentativi, latenza, token e costo, in quest'ordine;

`selected_llm` viene scelto usando il sistema completo e poi riutilizzato senza
RAG senza una nuova selezione. `frontier_llm_baseline` viene scelto con il prompt
diretto che userà nel test.

Prima dell'apertura del test si congelano identificativo completo, fornitore,
versione o snapshot, endpoint, parametri di decodifica, seed se supportato,
timeout, politica dei tentativi, prompt di sistema e utente, schemi e listino.
Una modifica silenziosa del fornitore rende l'esecuzione non conforme.

## 17. Riproducibilità e manifesto

Il manifesto dell'esperimento è immutabile e deve contenere almeno:

- identificativo e versione del protocollo;
- commit Git del codice sperimentale e commit del ramo `main` usato per MQT
  Predictor;
- stato della directory di lavoro e impronte degli artefatti non tracciati;
- versione e SHA-256 degli schemi;
- versione del Dataset, manifesto delle suddivisioni e hash di ogni circuito;
- identificativo, versione e impronta del catalogo;
- identificativi e impronte dei cinque Target;
- versioni di Python, Qiskit, MQT Bench e MQT Predictor;
- hash e metadati dei modelli MQT Predictor;
- ruoli, identificativi, fornitore, snapshot e parametri dei LLM;
- seed Qiskit, seed casuale, seed statistico e seed dei LLM disponibili;
- timeout del compilatore, del servizio e dell'esecuzione complessiva;
- due lavoratori esterni per coda di dispositivo e `num_processes=1` dentro
  Qiskit;
- data e ora in UTC e nel fuso locale;
- identificativo della macchina, CPU, RAM e sistema operativo;
- versione Qdrant, modalità locale o server, raccolta, distanza, dimensione,
  filtri, parametri dell'indice e impronta dell'esportazione;
- versione, codice e parametri della trasformazione delle feature;
- `k` del recupero e regola di tie-break;
- `max_llm_attempts=3` per i due metodi del prototipo e 1 per il LLM di
  frontiera;
- ordine o piano di esecuzione, identificativi delle code e politica di ripresa;
- valuta, data e fonte del listino usato per il costo.

Il timeout Qiskit e il numero di lavoratori sono già fissati dal protocollo. Il
timeout del servizio LLM viene scelto sulla validation perché dipende dal
fornitore, poi viene congelato. I segreti non entrano nel manifesto.

## 18. Stima delle risorse

### 18.1 Dati osservati nel pilota

L'ultima esecuzione uniforme del pilota ha usato due lavoratori e un timeout di
100 secondi. Comprende 1.584 tentativi. I tempi medi seguenti includono i timeout
e sono quindi adatti alla pianificazione:

| Dispositivo | Tentativi | Successi | Timeout | Successo | Tempo medio per tentativo |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ibm_falcon_27` | 216 | 214 | 2 | 99,1% | 1,729 s |
| `ibm_falcon_127` | 360 | 321 | 39 | 89,2% | 12,312 s |
| `ibm_heron_133` | 360 | 320 | 40 | 88,9% | 13,056 s |
| `ibm_heron_156` | 360 | 317 | 43 | 88,1% | 14,919 s |
| `quantinuum_h2_56` | 288 | 177 | 111 | 61,5% | 39,269 s |

Il pilota contiene soltanto dieci circuiti e può sottostimare il costo dei
circuiti più grandi o difficili. Per questo la stima prudente aggiunge un margine
del 50%. È una riserva di pianificazione, non una correzione dei dati.

### 18.2 Popolamento completo del Dataset

Le compatibilità correnti producono 2.846 coppie circuito-dispositivo. Con dodici
configurazioni e tre seed il totale è esattamente **102.456 compilazioni**.

| Dispositivo | Compilazioni | Ore cumulative stimate | Ore con 2 lavoratori | Ore prudenti con 2 lavoratori |
| --- | ---: | ---: | ---: | ---: |
| `ibm_falcon_27` | 17.352 | 8,33 | 4,17 | 6,25 |
| `ibm_falcon_127` | 21.600 | 73,87 | 36,93 | 55,40 |
| `ibm_heron_133` | 21.600 | 78,33 | 39,17 | 58,75 |
| `ibm_heron_156` | 21.600 | 89,51 | 44,76 | 67,14 |
| `quantinuum_h2_56` | 20.304 | 221,48 | 110,74 | 166,11 |
| **Totale** | **102.456** | **471,53** | **235,76** | **353,65** |

Con le cinque code di dispositivo eseguite davvero in parallelo, due lavoratori
per coda, il limite teorico è il dispositivo più lento: 110,74 ore, oppure
166,11 ore con il margine. Servono però dieci lavoratori. Sulla macchina del
pilota, con 6 core fisici e 8 GB di RAM, questa è soltanto una stima teorica e va
prima verificata sulla validation. Con una sola coda da due lavoratori alla volta
la stima prudente è circa 14,7 giorni.

### 18.3 Oracle di test

Il conteggio ricavato dai 90 circuiti correnti è:

`(72 + 90 + 90 + 90 + 84) × 12 × 3 = 15.336`.

| Dispositivo | Compilazioni | Ore cumulative stimate | Ore con 2 lavoratori | Ore prudenti con 2 lavoratori |
| --- | ---: | ---: | ---: | ---: |
| `ibm_falcon_27` | 2.592 | 1,24 | 0,62 | 0,93 |
| `ibm_falcon_127` | 3.240 | 11,08 | 5,54 | 8,31 |
| `ibm_heron_133` | 3.240 | 11,75 | 5,87 | 8,81 |
| `ibm_heron_156` | 3.240 | 13,43 | 6,71 | 10,07 |
| `quantinuum_h2_56` | 3.024 | 32,99 | 16,49 | 24,74 |
| **Totale** | **15.336** | **70,49** | **35,24** | **52,87** |

Con tutte le code in parallelo il limite teorico è 16,49 ore, oppure 24,74 ore
con il margine. Il valore di circa 16.056 indicato nella pianificazione iniziale
è superiore di 720 compilazioni e non coincide con la maschera corrente. Può
restare come riserva di capacità, ma non come conteggio operativo dell'oracle.

La parte test del Dataset, se prodotta dopo il congelamento con gli stessi hash,
Target, opzioni e seed, può costituire la matrice dell'oracle. Non va compilata
una seconda volta solo per duplicare la qualità. Le misure temporali devono però
indicare chiaramente da quale esecuzione provengono.

### 18.4 Raccomandazioni e chiamate LLM

Per ciascuno dei tre metodi LLM sono previste 90 raccomandazioni, una per
circuito. Le tre ripetizioni Qiskit successive non generano nuove raccomandazioni.

| Metodo | Raccomandazioni | Tentativi massimi per raccomandazione | Chiamate massime |
| --- | ---: | ---: | ---: |
| LLM + RAG | 90 | 3 | 270 |
| stesso LLM senza RAG | 90 | 3 | 270 |
| LLM di frontiera | 90 | 1 | 90 |
| **Totale** | **270** | — | **630** |

Se tutte le raccomandazioni sono valide, i tre metodi LLM producono 810
compilazioni Qiskit. La baseline casuale produce 270 compilazioni. MQT Predictor
esegue 270 invocazioni di `qcompile`. Le due configurazioni Qiskit fisse
richiedono 1.278 compilazioni ciascuna, ma i loro risultati di qualità possono
essere ricavati dalla stessa matrice esaustiva quando identificativi e tempi
sono conservati senza ambiguità.

Il costo monetario delle 630 chiamate possibili sarà calcolato dopo la scelta dei
modelli, usando i token reali di ogni tentativo e il listino congelato.

## 19. Criteri decisionali

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

## 20. Procedura operativa

1. **Controllo iniziale.** Verificare ambiente, spazio disco, catalogo, Target,
   schemi, circuiti, hash e assenza di risultati residui nel nuovo
   `experiment_id`.
2. **Preparazione delle suddivisioni.** Rigenerare i manifesti per dispositivo e
   verificare conteggi, compatibilità, duplicati esatti e quasi-duplicati.
3. **Dataset di training e validation.** Generare o verificare i record senza
   leggere né compilare il test. Conservare tutti i fallimenti.
4. **Indice RAG.** Creare una nuova raccolta Qdrant soltanto con gli hash ammessi
   del training. Eseguire un controllo negativo con tutti gli hash di validation
   e test.
5. **Scelta sulla validation.** Scegliere LLM, prompt, parametri, trasformazione,
   distanza, indice, `k`, timeout del servizio e ogni altra regolazione.
6. **Verifica MQT Predictor.** Controllare Training set, cinque classi, cinque
   modelli, caricamento e funzionamento di `qcompile`, senza circuiti di test.
7. **Congelamento.** Salvare manifesto, prompt, schemi, piani casuali, ambiente e
   impronte. Eseguire i controlli automatici e firmare gli artefatti.
8. **Apertura del test.** Nell'`experiment_id` confermativo, il test finale si
   considera aperto alla prima tra queste azioni: presentare un circuito di test
   a un metodo, compilare un circuito di test o rendere visibile una sua label.
   Da questo momento non si modifica il protocollo. Il pilota preesistente resta
   l'esposizione dichiarata nella sezione 15 e non diventa retroattivamente il
   test confermativo.
9. **Raccomandazioni cieche.** Ottenere e firmare tutte le raccomandazioni LLM,
   le scelte MQT e il piano casuale senza rendere visibile l'oracle.
10. **Compilazioni.** Eseguire il piano congelato. Salvare subito esiti, tempi,
    errori e utilizzo. Non correggere manualmente le risposte.
11. **Oracle.** Completare la matrice esaustiva o verificare la parte test del
    Dataset generata dopo il congelamento. Applicare il tie-break automatico.
12. **Chiusura e analisi.** Firmare i dati grezzi, rendere visibile l'oracle ed
    eseguire una volta lo script statistico congelato.
13. **Resoconto.** Pubblicare risultati completi, fallimenti, deviazioni, costi,
    manifesto e numeri effettivamente analizzati.

L'ordine dei lavori può essere distribuito tra code, ma nessuna parallelizzazione
può cambiare candidati, seed o regole. Le metriche temporali escludono l'attesa in
coda e includono soltanto il tempo attivo; l'attesa è registrata separatamente.

## 21. Condizioni necessarie prima di avviare il test

### 21.1 Prima di popolare il Dataset

Prima del popolamento completo occorre:

- assegnare una nuova directory di uscita e impedire il riuso implicito del
  pilota;
- rigenerare i manifesti per dispositivo nel formato corrente, mantenendo gli
  split 422/88/90 e gli hash approvati;
- congelare e verificare impronta del catalogo, Target, schemi e ambiente;
- verificare spazio disco, terminazione dei processi al timeout, due lavoratori
  esterni per dispositivo e `num_processes=1`;
- eseguire prima training e validation; la parte test resta chiusa fino al
  congelamento dell'esperimento.

Il nome storico `qiskit_expected_fidelity_pilot_v1` può essere conservato solo se
il manifesto chiarisce che è l'identificativo del catalogo, non del Dataset. Un
eventuale nuovo identificativo deve essere assegnato prima della generazione e
produce una nuova impronta.

### 21.2 Prima di aprire il test

Il test finale non può iniziare finché non sono soddisfatte tutte le condizioni
seguenti:

- Dataset di training e validation completo o con fallimenti terminali
  documentati;
- raccolta Qdrant costruita e controllo negativo del leakage superato;
- trasformazione delle feature, distanza, indice e `k` congelati;
- `selected_llm` e `frontier_llm_baseline` scelti e identificati in modo
  immutabile;
- prompt, schemi, parametri, timeout del servizio e listino congelati;
- esecutore sperimentale e schema dei risultati implementati e collaudati su
  circuiti non di test;
- esecutore proprietario dei seed Qiskit e delle opzioni fisse del catalogo;
- audit dei quasi-duplicati concluso;
- piano casuale delle 270 estrazioni creato e firmato;
- MQT Predictor verificato secondo la sezione 9.4 oppure dichiarato non
  disponibile prima del test;
- quarantena e dichiarazione sull'esposizione dei due circuiti del pilota;
- risorse, spazio disco, code e politica di ripresa verificati;
- manifesto completo, controllato e firmato.

## 22. Coerenza con il repository e incompatibilità concrete

La verifica di questo protocollo ha confermato nel repository i 422/88/90
circuiti, i cinque dispositivi, le dodici configurazioni, i tre seed, il totale
di 102.456 compilazioni e la regola che rende eleggibile una configurazione solo
con tre seed riusciti. I modelli sono stati controllati in sola lettura su `main`
e `origin/main`, entrambi al commit
`06528f62cf6212c4285db5351f2b7d6f4504f7c4`.

Restano le incompatibilità o carenze concrete seguenti:

1. **Conteggio oracle.** Con le larghezze correnti il totale è 15.336, non
   16.056. L'esecutore deve usare la maschera reale e registrare il conteggio.
2. **Classificatore MQT incompleto.** Il classificatore presente in `main` ha
   soltanto le classi `ibm_falcon_127`, `ibm_falcon_27` e
   `quantinuum_h2_56`. Non può applicare il protocollo a cinque dispositivi.
3. **Sovrapposizione del Training set MQT.** I dati locali del classificatore
   coincidono per nome e hash con tutti i 90 circuiti di test. La directory di
   training RL coincide con 72 dei 90. Gli artefatti correnti non possono essere
   presentati come baseline indipendente dal test.
4. **Modelli RL non ancora verificati funzionalmente.** In `main` esistono cinque
   file per `expected_fidelity` e nell'ambiente sono materializzati, ma nomi e
   metadati non provano da soli associazione, qualità e funzionamento di
   `qcompile`.
5. **Seed MQT non controllabile.** L'API 2.3.0 non espone i tre seed. Si applica
   quindi la regola specifica della sezione 11 e si dichiara il limite.
6. **Qdrant assente dal prototipo corrente.** Il recupero attuale legge JSON o
   JSONL e usa una distanza provvisoria. Servono integrazione Qdrant e parametri
   scelti sulla validation.
7. **Seed e opzioni nel compilatore del prototipo.** Lo schema LLM corrente fa
   scegliere `seed_transpiler` al modello; il compilatore lo usa direttamente e
   non applica ancora `approximation_degree=1.0` e `num_processes=1`. Prima del
   test il seed deve appartenere all'esecutore e tutte le opzioni del catalogo
   devono essere applicate.
8. **Schema sperimentale assente.** Gli schemi attuali descrivono il Dataset e il
   prototipo, ma non tutti i metodi, retry, token, costi, regret e fallimenti di
   questo esperimento. L'esecutore non è ancora implementato, come previsto.
9. **Audit dei quasi-duplicati assente.** Il codice controlla gli hash esatti ma
   non applica ancora il controllo strutturale richiesto.
10. **Manifesti completi da riallineare.** Il manifesto generale esistente usa
    una versione precedente, mentre il codice corrente produce manifesti per
    dispositivo. Prima del popolamento vanno rigenerati e firmati senza
    modificare le suddivisioni approvate.
11. **Metadato del catalogo.** L'identificativo corrente contiene ancora la
    parola `pilot`. Non impedisce l'esecuzione, ma il manifesto deve evitare di
    confonderlo con la versione del Dataset. Un'eventuale rinomina deve precedere
    la generazione e produrre una nuova impronta.
12. **Esposizione del test nel pilota.** Due circuiti di test hanno già risultati
    completi nel pilota. Vale la quarantena definita nella sezione 15.
13. **Timeout documentato in modo non uniforme.** Alcuni esempi precedenti
    indicano 120 secondi, mentre l'ultima esecuzione uniforme del pilota usa 100.
    Questo protocollo rende normativo il valore osservato di 100 secondi.

I punti 2, 3, 4, 6, 7, 8 e 9 impediscono oggi di eseguire il confronto finale
completo come definito. Il punto 10 deve essere risolto prima di popolare il
Dataset completo; il punto 11 è un'incoerenza di metadati non bloccante. Nessuno
di questi punti riapre le decisioni metodologiche del protocollo.

## 23. Elementi rinviati a esperimenti futuri

Non fanno parte dell'esperimento principale:

- circuiti non provenienti da MQT Bench;
- esecuzioni su hardware quantistico reale;
- dispositivi diversi dai cinque fissati;
- configurazioni fuori dalle dodici del catalogo;
- addestramento mirato o fine-tuning del LLM;
- misure diverse usate come nuovo obiettivo primario;
- cambiamenti a MQT Predictor per esporre seed controllabili;
- studi di ablazione diversi dal confronto LLM + RAG contro lo stesso LLM senza
  RAG.

Questi studi richiedono protocolli e risultati separati.

## 24. Stato del protocollo

Il protocollo è **approvato e congelato nella versione 1.0**.

Le modifiche sono consentite soltanto prima dell'apertura del test. Ogni modifica
deve incrementare la versione, indicare data, autore e motivazione e conservare
la versione precedente. Dopo la prima analisi dei risultati di test non sono
consentite modifiche retroattive.

Ogni deviazione operativa deve essere registrata separatamente, con causa,
impatto, circuiti coinvolti e momento in cui è stata scoperta. Le deviazioni non
possono essere nascoste né incorporate retroattivamente nel protocollo.

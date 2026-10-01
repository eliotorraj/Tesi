# Architettura e flusso del prototipo

Stato del codice verificato il **25 settembre 2026**.
Questo documento descrive il comportamento dei sorgenti distribuiti in
`prototipo/`. Per avviare il programma usare la
[guida passo passo](guida_passo_passo.md). Le regole di confronto tra metodi
sono nel [protocollo sperimentale](protocollo_sperimentale.md).

## 1. Scopo e confini

Il programma riceve un circuito OpenQASM 2 e propone una coppia composta da
un dispositivo e una configurazione Qiskit. Il modello linguistico vede le
caratteristiche del circuito e, nel percorso ordinario, esempi di compilazioni
del train. La compilazione è facoltativa e avviene solo con `--compile`.

```text
QASM e vincoli
    → lettura del circuito e 49 caratteristiche
    → controllo della richiesta e maschera hardware
    → recupero di massimo 5 esempi train
    → registro delle evidenze e vista essenziale TOON
    → modello locale → JSON → controllo di coppia e fatti
    → eventuali correzioni, fino a 3 tentativi
    → proposta accettata → compilazione Qiskit facoltativa
```

[app.py](../app.py) coordina le fasi. Le strutture dati e le operazioni concrete
sono in [prototype/quantum_assistant/](../prototype/quantum_assistant/README.md).
[prototype/prompting/](../prototype/prompting/README.md) costruisce il messaggio
e controlla la risposta. I cataloghi e i dati distribuiti sono locali.

Il prototipo non esegue circuiti su hardware quantistico reale e non addestra
modelli MQT. Usa Target sintetici di MQT Bench e una copia portabile
[dell'estrattore di caratteristiche](../portable_features.py) derivata da MQT
Predictor 2.4.0. La licenza è conservata in
[LICENSE-MQT-Predictor](../LICENSE-MQT-Predictor).
Questo percorso è distinto dall'architettura MQT Predictor che seleziona un
dispositivo con un modello supervisionato e compila con una politica RL.

## 2. Ingresso e lettura del circuito

Il comando `run` legge un file QASM UTF-8. L'opzione ripetibile `--device`
limita gli identificativi ammessi. La funzione `prepare` costruisce una
`UiSubmission` di compatibilità e la passa a `QasmRequestParser`.
Il campo storico `user_text` è vuoto e non viene usato per interpretare
vincoli in linguaggio naturale.

Il [lettore della richiesta](../prototype/quantum_assistant/adapters/request.py)
accetta anche `UserRequest`, oggetti Python e JSON conformi allo
[schema di ingresso](../schemas/assistant_request.schema.json). L'interfaccia
strutturata può esprimere fornitori ammessi, dispositivi ammessi, minimo e
massimo di qubit fisici, gate nativi richiesti e identificativo dello snapshot
hardware. Il comando pubblico espone solo il filtro `--device`.
La sola metrica ammessa è `expected_fidelity`.

La lettura applica questi controlli:

1. Verifica struttura e limiti della richiesta. La decodifica JSON rifiuta
   chiavi duplicate, valori numerici non finiti e oggetti superiori a
   2.100.000 byte UTF-8. Il sorgente QASM deve essere non vuoto e rispettare
   i limiti applicati dal lettore e dallo schema.
2. Esamina gli `include`, dopo aver escluso i commenti. Ammette solo
   `qelib1.inc`, risolto nella libreria fornita con Qiskit.
3. Carica il testo con `qiskit.qasm2.loads`, con istruzioni e funzioni
   classiche di compatibilità Qiskit e `strict=False`. Quest'ultima opzione
   riguarda la sintassi QASM accettata, non elimina i controlli applicativi.
4. Richiede almeno un qubit ed estrae larghezza, profondità, nomi delle
   operazioni, vettore numerico e SHA-256 del sorgente.
5. Controlla lunghezza e finitezza del vettore. Un errore interrompe il flusso
   prima del recupero degli esempi e della chiamata al modello.

Il risultato è una `ParsedRequest`. Il circuito originale resta disponibile
per la compilazione successiva; il suo testo non viene inviato all'LLM.

## 3. Le 49 caratteristiche

[portable_features.py](../portable_features.py) calcola il vettore senza
chiamare un modello MQT addestrato. L'ordine è fissato anche in
[rag_features.py](../prototype/quantum_assistant/adapters/rag_features.py).

| Gruppo | Numero | Significato |
| --- | ---: | --- |
| `gate_count_*` | 42 | Conteggi delle operazioni della lista OpenQASM fissata nell'estrattore; i conteggi assenti valgono zero. |
| `num_qubits`, `depth` | 2 | Numero di qubit dichiarati e profondità restituita da Qiskit. |
| Indicatori strutturali | 5 | Comunicazione, profondità critica, rapporto di operazioni a due qubit, parallelismo e attività. |

Il conteggio usa le operazioni presenti nel circuito caricato. Non esegue
una decomposizione preliminare universale: un nome fuori dalla lista dei 42
gate non ottiene un contatore dedicato. I nomi effettivi delle operazioni
sono conservati separatamente.

Per i cinque indicatori viene costruito il grafo aciclico del circuito e
vengono rimosse le barriere. Indicando con `n` il numero di qubit e con `D`
la profondità di questo grafo:

| Indicatore | Calcolo implementato |
| --- | --- |
| `program_communication` | Somma dei gradi del grafo non diretto delle interazioni a due qubit, divisa per `n × (n − 1)`; zero con un solo qubit. |
| `critical_depth` | Conteggio sul cammino più lungo dei nomi delle operazioni a due qubit, diviso per il numero totale di operazioni a due qubit; zero se queste sono assenti. |
| `entanglement_ratio` | Numero di operazioni a due qubit diviso per il numero di nodi gate; zero se non ci sono gate. |
| `parallelism` | `max(((numero_gate / D) − 1) / (n − 1), 0)`; zero con un qubit o profondità nulla. |
| `liveness` | Numero di celle attive della matrice qubit-per-livello, diviso per `n × D`; zero con profondità nulla. |

L'estrattore controlla che questi indicatori siano tra zero e uno.
`depth` nel vettore proviene dal circuito originale: non va confuso con `D`,
calcolato dopo la rimozione delle barriere per gli indicatori strutturali.

## 4. Catalogo e mascheramento hardware

[MqtHardwareCatalog](../prototype/quantum_assistant/adapters/hardware.py)
combina il [catalogo delle configurazioni](../configs/qiskit_dataset_configurations_v2.json)
con i Target caricati tramite `mqt.bench.targets.get_device`.
Controlla versioni richieste, dispositivi, gate nativi, numero di qubit,
collegamenti e impronta dei Target. Lo snapshot risultante contiene un
identificativo derivato dai dati hardware e dalla provenienza.
Un'incoerenza del catalogo produce un errore. Un Target che non può essere
caricato per altri motivi viene segnato come non disponibile.

`RequestSemanticValidator` verifica gli identificativi rispetto allo snapshot.
Nell'ingresso strutturato lo snapshot richiesto deve coincidere con quello
corrente; l'adattatore `UiSubmission` viene invece legato allo snapshot
appena costruito. I gate richiesti sono normalizzati in minuscolo, con
`cnot → cx` e `i → id`. Il controllo rifiuta valori sconosciuti, duplicati
dopo la normalizzazione, intervalli incoerenti e conflitti tra dispositivo
e fornitore richiesti.

`HardwareMaskBuilder` ordina i dispositivi per identificativo e applica
contemporaneamente tutte le condizioni:

- fornitore e dispositivo nelle eventuali liste ammesse;
- qubit sufficienti per il circuito e compresi nell'eventuale intervallo utente;
- presenza di tutti i gate nativi esplicitamente richiesti;
- metrica supportata e Target disponibile.

La maschera conserva sia i dispositivi ammessi sia i motivi di esclusione.
Se non resta alcun dispositivo, `app.prepare` termina prima della chiamata
LLM. Questo filtro non pretende che ogni gate del sorgente sia già nativo:
Qiskit può decomporlo durante la compilazione. Il controllo di compatibilità
precede la compilazione e non è una prova completa della sua riuscita.

Il mascheramento è quindi un filtro di ammissibilità. Non anonimizza i nomi
dei dispositivi. Gli alias E1–E5 descritti più avanti riguardano gli esempi.

## 5. Fonte RAG, trasformazione e recupero

[rag_dataset.py](../prototype/quantum_assistant/adapters/rag_dataset.py)
accetta esclusivamente il Dataset distribuito in
[data/rag_examples.jsonl](../data/rag_examples.jsonl): **396 esempi train**
nella vista `global_multi_device`. Verifica le impronte elencate nel sigillo,
il manifest train, gli identificativi dei circuiti, le versioni del protocollo,
le caratteristiche, i Target e la provenienza delle evidenze. Identificativi
RAG e impronte dei circuiti sorgente devono essere unici.
La verifica opzionale `verify_features=True` ricalcola inoltre le caratteristiche
dai QASM train e le confronta con quelle salvate.

La trasformazione del recupero è fissata in
[rag_features.py](../prototype/quantum_assistant/adapters/rag_features.py):

1. Applica `log(1 + x)` ai 42 conteggi, al numero di qubit e alla profondità.
2. Lascia invariati i cinque indicatori strutturali.
3. Divide ogni componente per il massimo valore assoluto di quella componente
   nel solo train. Se il massimo è zero, usa il divisore uno.
4. Usa la somma delle differenze assolute, cioè la distanza Manhattan.

Non applica centratura, taglio dei valori o normalizzazione L2. Un nuovo
circuito può quindi superare uno in una componente scalata. I divisori
ricalcolati devono coincidere con [data/transform.json](../data/transform.json).

[qdrant_context.py](../prototype/quantum_assistant/adapters/qdrant_context.py)
conserva l'indice locale in `runtime/rag/index/`. L'indice contiene vettori
float32, record e metadati verificabili. Prima dell'uso vengono confrontati
manifest, versione del software, numero e identità dei punti, vettori e dati
associati. Un indice esistente viene verificato; non viene sovrascritto in
silenzio. Un nuovo indice viene preparato in una cartella temporanea e reso
disponibile dopo verifica e riapertura.

La ricerca filtra per esperimento, split train, metrica e **dispositivo
vincente storico appartenente ai dispositivi ora ammessi**. Non richiede
che l'esempio abbia lo stesso numero di qubit del circuito corrente.
Interroga tutti i candidati filtrati, ricalcola le distanze in float64 e
verifica gli score Qdrant con tolleranza assoluta `1e-5` e relativa `1e-6`.
Ordina infine per distanza e, a parità esatta, per `rag_id`. Il programma
prende al massimo cinque esempi, senza usare score del circuito corrente.

I componenti `LocalReferenceContextRetriever` e `DisabledContextRetriever`
sono disponibili nel modulo per un uso esplicito. Il comando ordinario usa
Qdrant e non passa automaticamente a questi componenti in caso di errore.
La funzione `prepare(..., rag=False)` permette un ingresso senza esempi;
questa opzione non è esposta dal comando pubblico `run`.

## 6. Dal documento completo al testo TOON

[context.py](../prototype/quantum_assistant/adapters/context.py) costruisce un
registro delle evidenze dei soli esempi recuperati. Controlla risultati
storici, configurazioni, classifiche, etichetta vincente e collegamenti tra
affermazioni ed evidenze. Un record incoerente non viene scartato tacitamente.
Il registro completo e il documento della richiesta restano nei registri locali.

[model_input](../prototype/prompting/minimal.py) ricava una vista essenziale:

| Parte | Informazioni mostrate al modello |
| --- | --- |
| Circuito corrente | Nome, larghezza, profondità, operazioni e tutte le caratteristiche disponibili. |
| Hardware compatibile | Identificativi reali, qubit, operazioni, collegamenti e restrizioni di configurazione. |
| Catalogo | `config_id`, livello di ottimizzazione, metodo di layout e metodo di routing. |
| Esempi train | Alias E1–E5, caratteristiche, dispositivi compatibili, vincitore storico e prime tre righe della classifica con mediane e parità esplicite. |
| Vincoli | Vincoli normalizzati, se presenti. |

La vista esclude il sorgente QASM, gli hash, la provenienza estesa, le distanze
di recupero e il registro completo delle evidenze. Conserva però gli
identificativi e i metadati descrittivi del circuito storico previsti dalla
lista esplicita del modulo, per esempio `circuit_id` e famiglia del circuito.
Non è quindi una procedura di anonimizzazione generale.
I valori numerici delle caratteristiche non vengono arrotondati o selezionati
in base alla loro importanza. Le mediane mostrate appartengono agli esempi
train e non descrivono il circuito da compilare.

Gli alias dipendono dall'ordine recuperato: E1 indica il primo record di quella
richiesta. `citation_context` mantiene localmente la mappa verso i record,
l'identità della richiesta e le impronte dei dati. Sono ammessi al massimo
cinque esempi distinti.

[toon.py](../prototype/prompting/toon.py) effettua una seconda trasformazione:
le caratteristiche sono disposte per righe con colonne `current`, `E1`…`E5`
quando la struttura è uniforme. Gli archi hardware diventano liste di
adiacenza solo se è possibile ricostruirne anche l'ordine originale.
Una topologia completamente connessa e nell'ordine atteso può essere
rappresentata mediante una descrizione compatta esplicita.

L'encoder ufficiale `@toon-format/toon` 4.1.1 viene chiamato tramite Node.js 22.
La codifica è seguita da decodifica e ricostruzione: entrambe devono restituire
esattamente i dati della vista essenziale. Il controllo riguarda questa vista,
non la ricostruzione del documento completo, dal quale alcuni campi sono stati
intenzionalmente esclusi.

Il messaggio effettivo è costruito da
[facts.messages](../prototype/prompting/facts.py): istruzioni, blocco TOON,
regole dei fatti e schema JSON v4, con eventuali errori da correggere.
Il documento intermedio di `StructuredPromptBuilder` conserva ancora un
`response_contract` v3. Quel campo non è il contratto inviato da `app.decide`:
quest'ultimo usa esplicitamente lo schema v4 di `facts.py`.

## 7. Chiamata al modello e disponibilità del contesto

Il client di [app.py](../app.py) accetta un server HTTP su `127.0.0.1` o
`localhost`. In WSL usa `curl.exe` per raggiungere il server Windows; negli
altri ambienti usa `urllib`. Conserva le richieste e le risposte delle tre
operazioni di ogni tentativo:

1. `/apply-template` applica il modello di conversazione del server con
   `enable_thinking=False` e `reasoning_effort=none`.
2. `/tokenize` conta i token del testo realmente formattato.
3. `/completion` genera con schema JSON v4, temperatura `0.0` e massimo
   4096 token di uscita, usando gli altri parametri fissati in
   [config.json](../config.json).

Il profilo desktop prevede 60.000 token di contesto; il profilo laptop 16.384.
Prima della generazione il programma verifica `token_ingresso + 4096 ≤ contesto`.
Se non c'è spazio termina senza eliminare esempi e senza generare.
Il client usa una risposta non trasmessa a frammenti (`stream=False`), anche
se la configurazione di origine contiene impostazioni di streaming.

Temperatura zero, seed fissato e catalogo chiuso riducono le variazioni.
Non costituiscono da soli una garanzia di identità dei risultati tra versioni,
modelli, hardware o librerie diversi.

## 8. Parsing e validazione della risposta v4

La risposta prevista dallo
[schema v4](../schemas/llm_recommendation_v4.schema.json) contiene esattamente
`selected_device`, `config_id`, `facts` e `hypothesis`. Non contiene codice
Qiskit da eseguire né parametri arbitrari di compilazione.

[verify](../prototype/prompting/facts.py) separa tre controlli:

1. **JSON e schema.** Richiede un oggetto JSON completo entro 65.536 byte,
   senza chiavi duplicate o numeri non finiti. Rifiuta campi aggiuntivi.
   Richiede uno o due fatti distinti e un'ipotesi non vuota entro 1000 caratteri.
2. **Coppia ammessa.** Il dispositivo deve essere fra quelli compatibili;
   `config_id` deve appartenere al catalogo ed essere ammesso dal dispositivo.
   Ricontrolla anche la sufficienza dei qubit.
3. **Fatti.** Ogni fatto viene confrontato con i dati forniti in questa stessa
   richiesta. Gli alias sono risolti nei record correnti, mai in esempi esterni.

| Affermazione ammessa | Condizione verificata |
| --- | --- |
| `selected_pair_among_reported_best` | La coppia scelta compare insieme nelle righe storiche mostrate dell'esempio, incluse le configurazioni dichiarate a pari punteggio. Non significa necessariamente primo posto o vincitore unico. |
| `selected_device_matches_example` | Il dispositivo scelto coincide con il vincitore storico dell'esempio. Non afferma nulla sulla configurazione. |
| `same_qubit_count_as_example` | Circuito corrente ed esempio hanno esattamente lo stesso numero di qubit. Non dimostra somiglianza della topologia o delle prestazioni. |
| `selected_device_has_enough_qubits` | Il dispositivo scelto contiene almeno i qubit del circuito. Questo fatto non usa `example_id` e non dimostra qualità di compilazione. |

Il modello può proporre qualunque coppia ammessa, anche assente dalle
classifiche storiche. La sola disponibilità di esempi non obbliga la scelta
a copiare una coppia del train.

`hypothesis` resta testo libero: il verificatore ne controlla forma e lunghezza,
ma non la verità. L'istruzione di evitare alias come E1 nell'ipotesi è una
regola del messaggio; la loro eventuale presenza viene registrata, senza
costituire da sola un errore bloccante. Il risultato dichiara
`explanation_fully_verified=False` e, dopo l'accettazione,
`hypothesis_status=not_semantically_verified`.

Il modulo [schema_validation.py](../prototype/quantum_assistant/schema_validation.py)
implementa soltanto il sottoinsieme JSON Schema necessario ai file distribuiti.
Rifiuta schemi che richiedono parole chiave non supportate: non è un validatore
generale dell'intero standard.

## 9. Correzioni, accettazione e arresto

`app.decide` esegue al massimo tre tentativi. Dopo una risposta non accettata,
invia gli errori del verificatore insieme agli stessi dati del problema e
chiede una nuova risposta JSON completa. Non reinvia il testo grezzo della
risposta precedente come nuovo messaggio. Per i fatti errati, gli errori
contengono i dati osservati e la regola violata. La coppia può restare la stessa
se era già ammessa.

| Esito | Comportamento |
| --- | --- |
| Schema valido, coppia ammessa e tutti i fatti verificati | Accetta subito con `status=success`. |
| Schema valido e coppia ammessa, ma fatti non verificati nei primi due tentativi | Richiede una correzione. |
| Schema valido e coppia ammessa al terzo tentativo, ma fatti ancora non verificati | Accetta con `status=accepted_with_unverified_facts` e mantiene i fatti non verificati nel registro. |
| Nessuna coppia con schema valido e ammessa al termine | Interrompe con errore. |
| Errore di trasporto, contesto insufficiente o risposta segnalata come troncata | Interrompe l'esecuzione; il comando dimostrativo non implementa riprese automatiche. |

Non viene scelta automaticamente una coppia casuale o predefinita in caso
di fallimento. Nemmeno un problema del recupero diventa automaticamente una
richiesta senza RAG. L'accettazione al terzo tentativo è una regola esplicita
sui fatti, non una certificazione dell'ipotesi o della qualità prevista.
Con `--compile`, anche una proposta accettata con fatti non verificati può
passare alla compilazione, perché la coppia è stata comunque controllata.

Le procedure sperimentali archiviate possono applicare politiche aggiuntive
di registrazione e ripresa. Non vanno attribuite automaticamente al comando
`app.py run`.

## 10. Risoluzione della scelta e compilazione

`app.compile_decision` risolve `config_id` nel
[catalogo locale](../qiskit_dataset/catalog.py). Recupera livello di
ottimizzazione, layout e routing; aggiunge il seed scelto con
`--seed-transpiler` (zero se omesso). Questi valori formano la raccomandazione
passata a [QiskitDeterministicCompiler](../prototype/quantum_assistant/adapters/compilation.py).

Il compilatore ricontrolla metrica e numero di qubit, rilegge il QASM originale
con `QuantumCircuit.from_qasm_str` e chiama `qiskit.transpile` con il Target.
I metodi di layout e routing nulli vengono omessi, lasciando i valori
predefiniti di Qiskit. Non esegue codice prodotto dal modello.

Dopo la compilazione controlla:

- operazioni presenti nel Target, con le barriere ammesse separatamente;
- base di gate tramite `GatesInBasis(target=...)`;
- collegamenti tramite `CheckMap`, quando il Target ha una mappa esplicita.

Se un controllo fallisce, non restituisce un circuito come valido.
Altrimenti esporta OpenQASM 2 e registra profondità, dimensione, conteggi
delle operazioni e opzioni di compilazione. Questi controlli non sono una
prova formale di equivalenza al circuito sorgente e non misurano la fedeltà
su un dispositivo reale. Il comando dimostrativo non calcola uno score
`expected_fidelity` del circuito corrente.

## 11. Registri e interpretazione dei risultati

Ogni invocazione `run` crea una cartella distinta sotto `runs/`, con data e
suffisso casuale. La funzione `save` usa creazione esclusiva dei JSON e
rifiuta di sovrascrivere un documento già presente.

| Registro | Contenuto |
| --- | --- |
| `input.qasm`, `begin.json` | Sorgente, impronta, profilo, parametri, seed di compilazione, sistema, versioni e impronte dei sorgenti Python. |
| `prompt.json`, `retrieval.json`, `encoding.json` | Documento completo, esempi recuperati con distanze, tempi e identità della vista del modello. |
| `attempt_N/` | Richieste e risposte di formattazione, conteggio token e generazione; tempo, contesto e risultato della validazione. |
| `decision.json` | Risposta accettata, stato dei fatti, numero di tentativi e parametri di compilazione risolti. |
| `compiled.qasm`, `compilation.json` | Eventuale circuito compilato e relativo riepilogo. |
| `end.json` oppure `failure.json` | Fine dell'esecuzione o errore con tempo trascorso; i sottopassi HTTP possono avere propri registri di errore. |

I risultati d'uso del prototipo sono marcati come `technical_prototype` e
`user_input_not_experimental_test`. Non equivalgono alla valutazione sul Test
sperimentale. Tempo di recupero, tempi delle chiamate e token sono registrati
quando disponibili; memoria di processo e potenza dell'host sono dichiarate
come misure mancanti dal comando dimostrativo.

Un fatto storico corretto non dimostra che la scelta sia ottima sul nuovo
circuito. Una compilazione riuscita dimostra che quella procedura ha prodotto
un circuito conforme ai controlli sul Target, non che superi gli altri metodi.
Le conclusioni comparative richiedono il
[protocollo sperimentale](protocollo_sperimentale.md) e i dati conservati in
[archivio/](../../archivio/README.md).

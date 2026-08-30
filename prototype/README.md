# Prototipo dell'assistente quantistico
<img width="1444" height="736" alt="Gemini_Generated_Image_uxvjltuxvjltuxvj" src="https://github.com/user-attachments/assets/74cb16d9-e73e-4484-ab68-6f6494885862" />

## 1. Spiegazione generale

Il prototipo prepara una raccomandazione di compilazione per un circuito
quantistico. L'utente invia un circuito OpenQASM 2, sceglie la misura da
ottimizzare e può restringere i dispositivi utilizzabili.

Il sistema controlla la richiesta con regole deterministiche. Poi legge
un'istantanea del catalogo hardware e costruisce una maschera dei dispositivi
ammessi. Solo dopo questi controlli può cercare esempi nel Dataset e interrogare
il modello linguistico.

Il flusso completo previsto dal codice è:

```text
richiesta strutturata
  -> controllo del formato e del circuito
  -> controllo dei vincoli hardware
  -> maschera dei dispositivi utilizzabili
       -> nessun dispositivo: arresto del flusso
       -> almeno un dispositivo: ricerca nel Dataset
  -> richiesta all'LLM
  -> controllo della raccomandazione
  -> conferma dell'utente
  -> compilazione deterministica con Qiskit
```

Il modello propone un dispositivo, una configurazione Qiskit e una spiegazione.
Non genera codice da eseguire e non compila direttamente il circuito. La
compilazione avviene in un passaggio separato e solo dopo la conferma
dell'utente.

La preparazione della richiesta, il catalogo e la maschera hardware sono
completi. Il codice comprende anche la ricerca locale nel Dataset, la
costruzione della richiesta per il modello, il controllo della risposta e la
compilazione finale. Queste ultime parti permettono di provare l'intero flusso,
ma la misura definitiva di similarità e il collegamento a un LLM
reale devono ancora essere completati e valutati.

## 2. Struttura della directory e compito dei file

```text
prototype/
  README.md
  __init__.py
  quantum_assistant/
    __init__.py
    controller.py
    errors.py
    factory.py
    models.py
    ports.py
    schema_validation.py
    services.py
    adapters/
      __init__.py
      compilation.py
      context.py
      hardware.py
      llm.py
      parsing.py
      request.py
      validation.py
```

- `prototype/__init__.py` rende il prototipo importabile dal progetto.
- `quantum_assistant/models.py` definisce le strutture della richiesta, del
  catalogo, della maschera, della raccomandazione e della compilazione.
- `quantum_assistant/ports.py` definisce i confini tra le diverse parti del
  sistema. In questo modo catalogo, ricerca e modello linguistico possono essere
  sostituiti senza cambiare il coordinamento generale.
- `quantum_assistant/errors.py` raccoglie gli errori strutturati della richiesta.
- `quantum_assistant/schema_validation.py` controlla localmente gli schemi JSON
  usati dal prototipo.
- `quantum_assistant/services.py` coordina preparazione, ricerca,
  raccomandazione e compilazione.
- `quantum_assistant/controller.py` espone le operazioni utili a una futura
  interfaccia utente e conserva le raccomandazioni già controllate.
- `quantum_assistant/factory.py` collega le implementazioni locali e lascia
  sostituibile il collegamento all'LLM.
- `quantum_assistant/__init__.py` espone le classi pubbliche del modulo.

La directory `adapters/` contiene le implementazioni concrete:

- `request.py` legge il JSON, controlla OpenQASM 2, calcola le caratteristiche
  del circuito e normalizza i vincoli;
- `hardware.py` costruisce il catalogo MQT e la maschera hardware;
- `context.py` legge esempi JSON o JSONL dal Dataset, ordina quelli più vicini e
  prepara il contenuto per il modello;
- `llm.py` definisce un collegamento configurabile al modello linguistico;
- `validation.py` controlla che la risposta proponga solo dispositivi e
  configurazioni consentiti;
- `compilation.py` esegue `qiskit.transpile` dopo la conferma e controlla il
  circuito prodotto;
- `parsing.py` conserva le importazioni usate dalla versione precedente del
  prototipo;
- `__init__.py` raccoglie gli adattatori pubblici.

Tre schemi nella directory principale `schemas/` fanno parte dello stesso
modulo:

- `assistant_request.schema.json` descrive la richiesta dell'utente;
- `hardware_catalog.schema.json` descrive l'istantanea del catalogo;
- `hardware_mask_result.schema.json` descrive la maschera e la diagnostica dei
  dispositivi.

I controlli principali si trovano in `tests/test_request_constraints.py`. Le
prove dell'intero flusso si trovano in
`tests/test_prototype_architecture.py`.

## 3. Implementazione

### 3.1 Richiesta strutturata

L'utente non scrive i vincoli in una frase libera. Li sceglie tramite campi
predefiniti, popolati con il catalogo restituito dal sistema.

I vincoli disponibili sono:

- fornitori ammessi;
- dispositivi ammessi;
- numero minimo e massimo di qubit fisici;
- gate nativi obbligatori.

`allowed_device_ids` è l'unica lista che restringe direttamente i dispositivi.
Il prototipo non accetta una lista complementare di dispositivi vietati. Se un
vincolo non serve, il campo corrispondente viene omesso. Se una lista è
presente, deve contenere almeno un valore e non può avere duplicati.

La misura viene scelta a parte. La versione corrente supporta solo
`expected_fidelity`.

Esempio di richiesta:

```json
{
  "schema_version": "1.0.0",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "catalog_snapshot_id": "hardware_catalog_0000000000000000000000000000000000000000000000000000000000000000",
  "circuit": {
    "format": "openqasm2",
    "name": "bell",
    "source": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];"
  },
  "figure_of_merit_id": "expected_fidelity",
  "hardware_constraints": {
    "allowed_provider_ids": ["ibm"],
    "allowed_device_ids": ["ibm_falcon_127"],
    "device_qubits": {
      "min": 50,
      "max": 150
    },
    "required_native_gate_ids": ["cx"]
  }
}
```

L'identificativo mostrato nell'esempio è solo un segnaposto. La richiesta reale
deve usare il `catalog_snapshot_id` restituito dal catalogo corrente.

### 3.2 Controllo e normalizzazione

Il primo controllo riguarda la forma della richiesta. Verifica, tra le altre
cose:

- che il contenuto sia un singolo oggetto JSON valido;
- che non ci siano chiavi duplicate, valori non finiti o campi sconosciuti;
- che identificativi, tipi e liste rispettino lo schema;
- che il circuito sia OpenQASM 2 valido e usi almeno un qubit;
- che gli `include` non leggano file arbitrari dal sistema;
- che le caratteristiche del circuito siano complete e finite.

Lo schema è chiuso. Per questo ogni campo non previsto viene rifiutato,
invece di essere ignorato.

Il secondo controllo confronta la richiesta con l'istantanea corrente del
catalogo. Verifica che fornitori, dispositivi, gate e misura esistano. Controlla
anche l'intervallo dei qubit, l'appartenenza dei dispositivi ai fornitori
ammessi e la corrispondenza dell'identificativo del catalogo.

Gli alias dei gate vengono trasformati nel nome comune. Eventuali collisioni
create dalla normalizzazione vengono segnalate. Gli errori sono restituiti con
un codice, il percorso del campo e un messaggio. Il flusso si ferma prima del
Dataset e del modello linguistico.

### 3.3 Catalogo e maschera hardware

Il catalogo unisce i Target di MQT Bench al catalogo delle dodici
configurazioni Qiskit. Per ciascun dispositivo conserva:

- fornitore e numero di qubit;
- operazioni e gate nativi selezionabili;
- connettività;
- disponibilità del Target;
- misura supportata;
- configurazioni Qiskit utilizzabili;
- versioni e impronta dei dati da cui deriva il Target.

L'impronta rende l'istantanea stabile e collegabile ai risultati storici del
Dataset. La stessa istantanea viene usata dalla validazione e dalla maschera, in
modo che le due fasi non lavorino su cataloghi diversi.

La maschera applica insieme tutti i vincoli. Tiene conto anche del numero di
qubit usati dal circuito, che non può essere ridotto dall'utente.

```text
1 = dispositivo utilizzabile
0 = dispositivo non utilizzabile
```

L'uscita contiene `excluded_devices`, ma questo campo non è un vincolo
dell'utente. È solo la diagnostica dei dispositivi ai quali la maschera ha
assegnato zero. Le cause possono essere, per esempio, dispositivo fuori
dall'elenco ammesso, fornitore diverso, qubit insufficienti, gate mancante o
Target non disponibile.

Se tutti i valori sono zero, il sistema restituisce l'esito terminale
`NO_ELIGIBLE_DEVICE`. In questo caso non avvia né la ricerca né il modello
linguistico.

### 3.4 Ricerca, raccomandazione e compilazione

La ricerca locale legge sia il formato JSON precedente sia gli esempi JSONL del
Dataset corrente. Gli esempi vengono filtrati in base alla misura e ai
dispositivi rimasti nella maschera. Poi vengono ordinati con una distanza
semplice tra le caratteristiche numeriche dei circuiti.

Questa distanza permette di collaudare il flusso, ma non rappresenta ancora la
misura finale di similarità della tesi. La misura definitiva dovrà essere
confrontata con il trasferimento della scelta del dispositivo e della
configurazione.

La richiesta per il modello contiene:

- circuito e caratteristiche;
- misura da ottimizzare;
- soli dispositivi utilizzabili;
- esempi storici recuperati, con scelta, affermazioni, prove e limiti;
- le dodici configurazioni Qiskit consentite;
- il formato atteso della risposta.

Il collegamento a un modello concreto viene fornito dall'esterno. Il prototipo
include anche un adattatore locale utile per le prove e un adattatore che
segnala chiaramente quando nessun modello è stato configurato.

La risposta viene accettata solo se sceglie un dispositivo rimasto nella
maschera, usa `expected_fidelity` e propone una delle dodici configurazioni
Qiskit. Una risposta errata può essere ripetuta fino al limite configurato,
riportando al tentativo successivo gli errori trovati.

Dopo una risposta valida, il sistema attende la conferma dell'utente. Solo
allora esegue la configurazione già controllata con `qiskit.transpile`. Infine
verifica che il circuito rispetti operazioni e connettività del Target.

### 3.5 Stato e sviluppi successivi

La base applicativa è quindi funzionante dall'ingresso strutturato fino alla
compilazione confermata. Prima dell'esperimento finale restano da completare:

1. scelta e valutazione della similarità tra circuiti;
2. integrazione del sistema RAG definitivo;
3. collegamento al modello linguistico scelto;
4. formato finale delle spiegazioni e delle prove;
5. valutazione comune di qualità, errori, tempi e costi.

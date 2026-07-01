# Riassunto KB — MQT Predictor, dataset, RL compiler e confronto con TuniQ

## Contesto della conversazione

Questa chat riguarda lo studio di paper e codice relativi a **MQT Predictor** e al precedente lavoro del 2023 su predizione di buone opzioni di compilazione per circuiti quantistici. L’obiettivo dell’utente è costruire una **Knowledge Base** consultabile da un modello agentico, utile soprattutto per capire:

- come sono costruiti i dataset usati nei paper;
- che cosa rappresentano le label nei modelli supervisionati;
- come si collega il modello supervisionato di scelta del device al modello di Reinforcement Learning usato per la compilazione;
- cosa restituisce la funzione `qcompile` di MQT Predictor oltre al circuito compilato;
- che rapporto esiste tra MQT Predictor e TuniQ;
- quali limiti emergono quando si aggiunge un nuovo dispositivo hardware.

---

## Organizzazione della Knowledge Base

Per usare materiale come KB aggiuntiva in un progetto agentico, conviene inserire i documenti in una cartella dedicata, ad esempio:

```text
knowledge/
docs/kb/
```

Il modello può consultare Markdown, testo, PDF, Word, CSV e codice. Per far sì che l’agente usi automaticamente la KB, è utile creare un file `AGENTS.md` con istruzioni operative, ad esempio:

- cercare nella KB prima di rispondere;
- usare le fonti locali come riferimento principale;
- non inventare dettagli se non presenti nella KB;
- distinguere tra informazioni tratte dai paper, inferenze e ipotesi progettuali.

`AGENTS.md` non dovrebbe contenere tutta la conoscenza, ma solo indice, regole d’uso e convenzioni. Per una KB riutilizzabile tra più progetti si può valutare una skill con una cartella `references/`. Per fonti esterne o aggiornate spesso si possono usare connector, MCP, Notion, Google Drive, database o sistemi RAG. Le memorie sono utili per preferenze e convenzioni personali, ma non vanno trattate come KB autorevole.

---

## Idea centrale del dataset

Il principio fondamentale del dataset è imitare una ricerca esaustiva costosa.

Per ogni circuito quantistico target-independent:

1. si parte da un circuito non ancora adattato ad alcun hardware specifico;
2. offline, il circuito viene compilato o valutato rispetto a tutte le alternative considerate;
3. ogni alternativa riceve uno score secondo una **figure of merit**;
4. l’alternativa con punteggio migliore diventa la label supervisionata;
5. il modello supervisionato impara a predire quella label usando solo caratteristiche del circuito originale.

Schema concettuale:

```text
Circuito target-independent
        │
        ├──> estrazione feature vector X
        │
        └──> compilazione/valutazione con tutti i candidati
                    │
                    └──> calcolo score secondo figure of merit
                                │
                                └──> argmax(score) = label y

Campione supervisionato = (X, y)
```

Una riga del dataset ML non corrisponde a una singola compilazione. Corrisponde invece a un circuito sorgente, associato alla label del candidato migliore. I circuiti compilati sono artefatti intermedi necessari per costruire la ground truth.

Il modello impara quindi una regola del tipo:

```text
Dato questo circuito, quale opzione/dispositivo vincerebbe secondo questa metrica e questa configurazione sperimentale?
```

La label non è una verità assoluta: dipende da dispositivi disponibili, metrica scelta, calibrazioni hardware, pass di compilazione e pipeline usata.

---

## Differenza tra paper 2023 e MQT Predictor 2025

I due lavori sono collegati, ma non descrivono esattamente lo stesso dataset.

### Paper 2023 — “Predicting Good Quantum Circuit Compilation Options”

Nel paper del 2023 il modello supervisionato predice l’intera configurazione di compilazione:

```text
tecnologia + dispositivo + compilatore + impostazioni
```

Caratteristiche principali:

- circuiti da MQT Bench;
- circa 3.000 circuiti sorgente;
- range indicativo: 2–127 qubit;
- 30 combinazioni candidate;
- compilatori/pipeline basati su Qiskit e TKET;
- split ML: 2.100 circuiti per training e 900 per test;
- 38.672 circuiti compilati e valutati come artefatti intermedi.

I 38.672 circuiti compilati non generano 38.672 campioni ML finali. Producono 3.000 campioni supervisionati, uno per circuito sorgente. Non si arriva a `3000 × 30` compilazioni perché alcune combinazioni non sono applicabili, ad esempio per limiti di capacità del dispositivo, oppure superano un timeout di 300 secondi.

### MQT Predictor 2025

Nel paper MQT Predictor più recente la logica viene modificata: la scelta del dispositivo e la compilazione sono separate.

Il modello supervisionato predice solo il dispositivo:

```text
device
```

La compilazione viene poi svolta da un modello di Reinforcement Learning specifico per il dispositivo selezionato.

Caratteristiche principali:

- oltre 500 circuiti;
- 7 dispositivi candidati;
- circuiti 2–30 qubit per il training RL;
- circuiti 2–90 qubit per la scelta del device;
- split supervisionato 70% / 30%;
- circuiti compilati e punteggi persistiti per ciascun dispositivo.

In MQT Predictor compaiono due processi di apprendimento distinti:

1. **Reinforcement Learning**: non usa label classiche. Osserva il circuito, sceglie pass di compilazione e riceve ricompense in base al risultato.
2. **Machine Learning supervisionato**: usa come label il dispositivo che, dopo la compilazione RL, ottiene lo score migliore.

---

## Significato di “target-independent”

Un circuito target-independent è un circuito non ancora adattato a uno specifico hardware.

In particolare, non è ancora:

- tradotto nei gate nativi del dispositivo;
- mappato sui qubit fisici;
- modificato per rispettare la topologia e la connettività hardware;
- ottimizzato rispetto a errori, durate o vincoli del backend.

Questo è importante perché la feature vector deve descrivere il circuito originale senza incorporare già una preferenza verso un device specifico. MQT Bench distingue questo livello da circuiti già convertiti in native gates o già mapped.

---

## Struttura concettuale di un campione ML

Un campione del dataset supervisionato può essere descritto così:

```text
name   = identificativo del circuito
X      = feature del circuito originale target-independent
scores = punteggi ottenuti dai candidati
y      = candidato/dispositivo con score massimo
```

Nel caso del paper 2023, `y` rappresenta una configurazione completa. Nel caso di MQT Predictor 2025, `y` rappresenta solo il dispositivo.

Le feature considerate includono:

- numero di qubit;
- profondità del circuito;
- conteggio dei gate;
- conteggio per tipo di gate;
- program communication;
- critical depth;
- entanglement ratio;
- parallelism;
- liveness.

Descrizione delle feature composite:

- **program communication**: densità o intensità delle interazioni tra coppie di qubit;
- **critical depth**: frazione dei gate a due qubit situati sul percorso critico;
- **entanglement ratio**: rapporto tra gate a due qubit e gate totali;
- **parallelism**: misura di quante operazioni possono essere eseguite contemporaneamente;
- **liveness**: frazione della matrice qubit-tempo in cui i qubit sono attivi.

Nel paper 2023 restano 31 feature dopo aver eliminato gate count sempre nulli. Nel codice stabile più recente si costruiscono invece 49 valori:

```text
42 conteggi OpenQASM
+ numero di qubit
+ depth
+ 5 feature composite
= 49 valori
```

La struttura concreta è collegata al codice, in particolare a `ml/helper.py`.

---

## Figure of merit e significato di “migliore”

La label del dataset dipende dalla figure of merit scelta. Cambiare metrica può cambiare il candidato migliore.

### Expected fidelity

Per `expected_fidelity`, il punteggio è essenzialmente una stima moltiplicativa:

```text
F = prodotto delle fidelities dei gate × prodotto delle fidelities di readout
```

Questa non è una misura ottenuta eseguendo realmente il circuito su hardware. È una stima basata su errori di gate e lettura. Implicitamente assume che gli errori possano essere combinati in modo indipendente/moltiplicativo.

### Critical depth

La `critical_depth` grezza misura quanto il circuito è sequenziale. Un valore alto indica poca parallelizzabilità. Nel codice attuale viene usato `1 - critical_depth`, così anche in questo caso “più alto è meglio”.

### Conseguenza importante

Se cambiano:

- la metrica;
- le calibrazioni hardware;
- i dispositivi disponibili;
- i pass di compilazione;
- le pipeline di compilazione;
- il compilatore RL usato;

allora cambiano gli score e possono cambiare anche le label. I modelli supervisionati devono quindi essere aggiornati o riaddestrati. Conservare circuiti compilati e score serve proprio a poter ricalcolare le label senza rifare tutto da zero.

---

## Oggetti restituiti da `qcompile`

L’uso concettuale è:

```python
qc_compiled, compilation_information, quantum_device = qcompile(...)
```

Oltre al circuito compilato, vengono restituiti due oggetti importanti.

### `compilation_information`

`compilation_information` è una `list[str]`.

Contiene la sequenza ordinata dei pass scelti ed eseguiti dall’agente RL. Esempio:

```python
[
    "Optimize1qGatesDecomposition",
    "BasisTranslator",
    "SabreMapping",
    "CommutativeCancellation",
    "terminate",
]
```

Questa lista è una traccia delle decisioni del compilatore RL. Non contiene:

- score finale;
- probabilità assegnate ai device;
- feature vector;
- dettagli completi del classificatore supervisionato.

Il codice aggiunge il nome di ogni azione durante la compilazione, in particolare nella parte RL del predictor.

### `quantum_device`

`quantum_device` è, nell’implementazione effettiva, un `qiskit.transpiler.Target`.

Descrive l’hardware usato dal compilatore:

- nome o descrizione del dispositivo;
- numero di qubit;
- gate e istruzioni supportate;
- qubit sui quali ogni gate è applicabile;
- topologia;
- coupling map;
- errori delle istruzioni;
- durate delle istruzioni;
- proprietà dei qubit;
- eventuali vincoli temporali.

Un `Target` descrive l’ISA e i vincoli del dispositivo. Non è un job di esecuzione e non è un risultato ottenuto da hardware reale.

È stata notata una piccola incongruenza: `qcompile.py` annota il terzo valore come `str`, ma la funzione di selezione restituisce effettivamente un `Target`. Questo sembra un errore di type annotation o documentazione.

Esempio di ispezione:

```python
print(compilation_information)

print(type(quantum_device))
print(quantum_device.description)
print(quantum_device.num_qubits)
print(quantum_device.operation_names)
print(quantum_device.build_coupling_map())
```

Importante: `qcompile` non restituisce le probabilità assegnate ai vari dispositivi né il punteggio finale. Il classificatore le calcola internamente, sceglie il primo dispositivo compatibile per numero di qubit e poi scarta il ranking.

---

## Flusso completo di MQT Predictor

Il flusso MQT Predictor può essere sintetizzato così:

```text
Circuito non compilato
        ↓
Estrazione feature dal circuito target-independent
        ↓
Modello supervisionato
        ↓
Predizione del device più promettente
        ↓
Caricamento del modello RL specifico per quel device
        ↓
Scelta sequenziale dei pass di compilazione
        ↓
Circuito compilato per quell’hardware
```

Quindi sì: MQT Predictor mantiene l’idea supervisionata del lavoro 2023, ma restringe la label.

Nel 2023:

```text
label = device + compilatore + impostazioni
```

In MQT Predictor 2025:

```text
label = device
```

La compilazione non è più parte della label supervisionata, ma viene svolta dopo da un agente RL specifico.

I due modelli sono separati ma accoppiati:

- il modello supervisionato sceglie il dispositivo;
- esiste tipicamente un modello RL per ogni coppia `device × figure_of_merit`;
- anche il classificatore supervisionato è addestrato rispetto a una specifica figure of merit;
- le label del classificatore sono state generate compilando preventivamente ogni circuito con tutti i modelli RL e scegliendo il device con score migliore.

Il modello supervisionato impara quindi una funzione concettuale del tipo:

```text
Dato questo circuito, quale compilatore RL specifico per hardware produrrebbe il risultato migliore?
```

“Miglior hardware” significa migliore tra i dispositivi considerati nel training e secondo la metrica scelta. Non significa miglior dispositivo esistente in assoluto.

---

## Relazione tra MQT Predictor e TuniQ

TuniQ, indicato con riferimento `arXiv:2605.11375`, è metodologicamente correlato al modello RL usato in MQT Predictor, ma non riusa lo stesso modello addestrato.

TuniQ cita il precedente lavoro di Quetschlich, Burgholzer e Wille su **Compiler Optimization for Quantum Computing Using Reinforcement Learning**, da cui deriva la componente RL poi integrata in MQT Predictor.

### Cosa condividono

MQT Predictor e TuniQ condividono il paradigma generale:

- modellano la compilazione come un Markov Decision Process;
- un’azione corrisponde alla scelta di un pass di compilazione;
- il pass viene applicato al circuito;
- il circuito cambia stato;
- il modello osserva il nuovo stato e sceglie l’azione successiva;
- usano PPO, in particolare una variante MaskablePPO;
- usano action masking per evitare azioni non valide;
- producono dinamicamente una sequenza di pass specifica per il circuito.

Schema comune:

```text
circuito corrente
        ↓
osservazione dello stato
        ↓
scelta del pass
        ↓
applicazione del pass
        ↓
nuovo circuito
        ↓
ripetizione fino a terminazione
```

### Differenze principali

MQT Predictor:

- usa il RL come compilatore dopo che il device è stato scelto;
- usa una policy separata per ogni coppia `device × figure_of_merit`;
- rappresenta lo stato con feature compatte e pochi stati di eseguibilità;
- usa una reward prevalentemente sparsa: il segnale significativo arriva quando il circuito diventa eseguibile e viene valutato con la figure of merit;
- incorpora le caratteristiche del device nei pesi del modello specifico;
- ha un device selector supervisionato separato.

TuniQ:

- riceve il backend come input;
- usa una policy condizionata su hardware e rumore;
- mira a generalizzare tra backend diversi senza addestrare un modello separato per ciascun dispositivo;
- usa uno stato molto più ricco;
- impiega un dual encoder:
  - pre-layout encoder per interazioni spazio-temporali tra qubit logici;
  - post-layout encoder per qubit fisici, coupling graph, errori, `T1/T2` e calibrazione;
- considera sei stadi Qiskit:
  - init;
  - layout;
  - routing;
  - translate;
  - optimize;
  - cleanup;
- introduce reward intermedie sagomate, tra cui:
  - LQ, layout quality;
  - RQ, routing quality;
  - ESP, estimated success probability;
  - reward finale relativa a Qiskit Level 3, con contributi di gate count e depth.

La differenza più sostanziale è che MQT Predictor usa una reward più sparsa, mentre TuniQ introduce reward intermedie per assegnare meglio il merito alle decisioni iniziali, ad esempio nella scelta del layout.

---

## Rapporto concettuale tra MQT Predictor e TuniQ

Il confronto corretto è:

```text
MQT Predictor:
ML device selector → RL specifico del device → circuito compilato

TuniQ:
backend fornito → RL hardware/noise-conditioned → circuito compilato
```

TuniQ corrisponde concettualmente alla seconda metà di MQT Predictor, cioè alla parte di compilazione RL. Non effettua la scelta del dispositivo.

Un possibile sistema ibrido sarebbe:

```text
MQT ML device selector → TuniQ → circuito compilato
```

Tuttavia, per costruire correttamente questo ibrido, bisognerebbe rigenerare il dataset e riaddestrare il selettore supervisionato. Le label del selettore MQT dipendono infatti dagli score ottenuti dai compilatori RL originali. Se si sostituisce il compilatore con TuniQ, potrebbe cambiare quale dispositivo risulta migliore per ciascun circuito.

Sintesi: TuniQ è un’evoluzione dello stesso paradigma RL-per-selezione-dei-pass, con stato più ricco, reward meno sparsa e policy condizionata dinamicamente sull’hardware. Non emerge un riuso diretto dei pesi o del codice MQT.

---

## Aggiunta di un nuovo dispositivo in MQT Predictor

Nell’architettura attuale di MQT Predictor serve un modello RL distinto per ogni coppia:

```text
device × figure_of_merit
```

Se viene introdotto un nuovo dispositivo, ad esempio un nuovo device a ioni intrappolati diverso da quelli già noti, bisogna:

1. descriverlo come `Qiskit Target`, includendo qubit, gate nativi, connettività, errori, durate e vincoli;
2. addestrare un nuovo modello RL specifico per quel device e per la metrica scelta;
3. usare il nuovo modello RL per compilare i circuiti di training destinati alla scelta del device;
4. calcolare gli score del nuovo dispositivo;
5. aggiungere il nuovo dispositivo tra le possibili label;
6. riaddestrare il classificatore supervisionato.

“Creare un nuovo compilatore” non significa implementare da zero un compilatore. Significa addestrare una nuova policy RL che impari a scegliere e ordinare pass già disponibili per quello specifico hardware.

Se si supportano due metriche, ad esempio:

```text
expected_fidelity
critical_depth
```

servono idealmente due policy per il nuovo device:

```text
RL(nuovo_device, expected_fidelity)
RL(nuovo_device, critical_depth)
```

Non è sempre necessario ricompilare i circuiti per tutti i vecchi dispositivi, se i circuiti compilati e gli score precedenti sono già stati conservati. Si può aggiungere una nuova “colonna” di score per il nuovo device:

```text
Circuito       Device A   Device B   Nuovo device
circuito_1       0.82       0.76        0.91
circuito_2       0.64       0.88        0.79
...
```

Poi si ricalcola il vincitore di ogni riga e si riaddestra il classificatore supervisionato.

Questo è uno dei limiti che TuniQ cerca di superare: invece di incorporare il device nei pesi di una policy specifica, TuniQ inserisce caratteristiche e calibrazione del backend nello stato osservato dalla policy, con l’obiettivo di usare lo stesso modello su dispositivi differenti.

---

## Punti chiave da ricordare per un agente LLM

1. Il paper 2023 e MQT Predictor 2025 sono collegati, ma non usano lo stesso identico schema di dataset.
2. Nel paper 2023 la label è una configurazione completa: device, compilatore e impostazioni.
3. In MQT Predictor 2025 la label supervisionata è solo il device.
4. In MQT Predictor la compilazione viene gestita separatamente da un modello RL specifico per device e figure of merit.
5. Il dataset supervisionato non contiene una riga per ogni compilazione, ma una riga per ogni circuito sorgente.
6. I circuiti compilati sono artefatti intermedi usati per generare score e label.
7. La label dipende dalla figure of merit e non rappresenta una verità assoluta.
8. `qcompile` restituisce:
   - circuito compilato;
   - lista dei pass scelti dal modello RL;
   - `Qiskit Target` del device selezionato.
9. `qcompile` non restituisce score finale, probabilità del classificatore o ranking completo dei dispositivi.
10. TuniQ è affine alla parte RL di MQT Predictor, ma usa una policy condizionata su hardware e rumore, pensata per generalizzare tra backend.
11. TuniQ non sostituisce direttamente il sistema completo MQT Predictor perché non fa device selection.
12. Se si sostituisce il compilatore RL di MQT con TuniQ, bisogna rigenerare gli score e riaddestrare il selettore supervisionato.
13. Nell’architettura MQT attuale, un nuovo device richiede un nuovo modello RL per ogni metrica supportata e un riaddestramento del selettore supervisionato.
14. Conservare score e circuiti compilati permette di aggiornare le label aggiungendo nuovi dispositivi senza ricompilare necessariamente tutto il passato.
15. “Miglior device” significa migliore tra quelli presenti nel dataset e secondo la metrica scelta, non migliore in assoluto.

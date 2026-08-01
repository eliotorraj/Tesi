# Riassunto KB — MQT Predictor, dataset, RL compiler e confronto con TuniQ

> **Nota sul layout corrente (31 luglio 2026).** Questo documento conserva
> anche riferimenti storici a esperimenti e script rimossi. I comandi operativi
> aggiornati sono soltanto quelli nel `README.md` alla root. Il dataset corrente
> è `datasets/device_selector_expected_fidelity.json`; i modelli finali sono in
> `artifacts/models/`; i QASM compilati sono una cache intermedia in
> `artifacts/cache/`; tutti i log sono in `artifacts/logs/`. Gli script correnti
> sono numerati da `01` a `05`.

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

---

# Continuazione KB — setup sperimentale MQT Predictor, WSL, training RL, report e protocollo

## Contesto della continuazione

Questa sezione continua la Knowledge Base precedente con le informazioni emerse nella conversazione operativa successiva. Il focus non è più solo teorico, ma anche pratico/sperimentale:

- scelta dell’ambiente di lavoro per MQT Predictor;
- creazione di script per testare `qcompile` e addestrare modelli;
- chiarimento su quale dataset viene usato per il training RL;
- gestione di checkpoint per RL e classificatore ML;
- preparazione di una cartella separata da mostrare ai relatori;
- aggiunta di riferimenti al codice nel report;
- origine dei pass di compilazione presenti in `compilation_information`;
- spiegazione semplice del protocollo sperimentale proposto.

L’obiettivo rimane costruire una KB utile a un agente/LLM che deve assistere l’utente nel progetto di tesi su MQT Predictor, compilazione quantistica, device selection e possibile integrazione LLM.

---

## Scelta dell’ambiente: Ubuntu 24.04 su WSL2

Per lavorare con MQT Predictor è stata consigliata la configurazione:

```text
Windows 11 host
└── WSL2
    └── Ubuntu 24.04
```

Motivazione:

- Windows è supportato, ma Linux è più comodo per PyTorch, RL e training parallelo;
- Ubuntu/WSL2 evita molte incompatibilità tipiche di ambienti Python scientifici su Windows;
- il progetto può comunque stare su disco Windows o in home Linux, ma per performance e pulizia è preferibile lavorare direttamente in `~/Tesi` dentro WSL.

L’utente aveva già installato Ubuntu e ha impostato la distribuzione predefinita con:

```powershell
wsl --set-default Ubuntu
```

Il nome corretto della distribuzione, nel caso dell’utente, è semplicemente:

```text
Ubuntu
```

non `Ubuntu-24.04`.

Comandi utili:

```powershell
wsl --list --verbose
wsl --set-default Ubuntu
wsl -d Ubuntu
```

---

## Struttura iniziale del progetto MQT-Predictor-understanding

Nella prima fase era stata usata la cartella Windows:

```text
C:\Users\elioe\Documents\MQT-Predictor-understanding
```

Dentro questa cartella sono stati preparati diversi file e script:

```text
README.md
AGENTS.md
.gitignore
.python-version
pyproject.toml
uv.lock
scripts/
```

Script citati nella conversazione:

```text
scripts/bootstrap_ubuntu.sh
scripts/bootstrap_windows.ps1
scripts/01_diagnose_environment.py
scripts/02_list_devices.py
scripts/03_train_smoke_models.py
scripts/04_test_qcompile.py
scripts/05_train_rl_model.py
scripts/06_train_device_selector.py
scripts/model_store.py
```

Scopo generale degli script:

- preparare l’ambiente Python;
- installare dipendenze compatibili;
- diagnosticare ambiente e device disponibili;
- addestrare modelli smoke/minimali;
- testare `qcompile`;
- avviare training RL reale;
- addestrare il selettore supervisionato di device;
- esportare/importare modelli addestrati.

Nota importante: MQT Predictor 2.x non include modelli preaddestrati utilizzabili direttamente per tutti gli esperimenti. Prima di usare `qcompile` in modo significativo bisogna disporre dei modelli RL e, per il flusso completo, anche del device selector.

---

## Spostamento del progetto in `~/Tesi`

Successivamente l’utente ha spostato il lavoro nella cartella Linux:

```text
~/Tesi
```

Questa cartella è stata collegata a una repository privata su GitHub.

Nella nuova posizione sono stati eseguiti:

```bash
bash scripts/bootstrap_ubuntu.sh
source .venv/bin/activate
python scripts/01_diagnose_environment.py
python scripts/02_list_devices.py
python scripts/03_train_smoke_models.py
python scripts/04_test_qcompile.py
```

La cartella `~/Tesi` contiene l’ambiente virtuale locale:

```text
~/Tesi/.venv/
```

Il prompt mostrato durante gli esperimenti era del tipo:

```text
(mqt-predictor-understanding) elioe@LenovodiIda:~/Tesi$
```

---

## Risultato dello smoke test con `qcompile`

Lo smoke test ha validato la pipeline end-to-end, ma non ha valore scientifico come modello addestrato bene.

Risultati principali:

```text
Device selezionato: ibm_falcon_127
Tipo oggetto device: qiskit.transpiler.Target
Circuito test: GHZ a 5 qubit
Output qcompile: circuito compilato + compilation_information + Target
```

Artefatti generati:

```text
artifacts/results/ghz_5_expected_fidelity.json
artifacts/results/ghz_5_expected_fidelity.qasm
```

È emersa un’incongruenza iniziale sul valore della profondità finale:

```text
valore riportato inizialmente nel report: depth finale 8
valore presente nel JSON: depth finale 12
```

Il valore corretto da considerare, perché coerente con l’artefatto JSON, è:

```text
profondità compilata = 12
```

Anche il conteggio dei pass richiede attenzione:

```text
30 pass effettivi + terminate = 31 elementi nella lista JSON
```

`terminate` non è un pass di compilazione classico, ma un’azione di controllo che indica la terminazione della sequenza scelta dalla policy.

---

## Pulizia di artefatti vecchi o superflui

Nella fase iniziale erano rimasti alcuni artefatti pesanti o duplicati, soprattutto su filesystem Windows/NTFS.

Elementi indicati come eliminabili o superflui:

```text
.venv/ vecchia e incompleta su NTFS, circa 3.7 GiB
model_expected_fidelity_ibm_falcon_127/ in root, duplicato rispetto ad artifacts/smoke/
tmp/mqt_predictor-2.3.0.tar.gz
tmp/pdfs/
```

Comandi PowerShell suggeriti per rimuovere vecchi artefatti dalla cartella Windows:

```powershell
Remove-Item -LiteralPath .venv -Recurse -Force
Remove-Item -LiteralPath model_expected_fidelity_ibm_falcon_127 -Recurse -Force
Remove-Item -LiteralPath tmp\mqt_predictor-2.3.0.tar.gz -Force
```

---

## Training RL reale su `quantinuum_h2_56`

L’utente ha avviato un training RL reale con:

```bash
python scripts/05_train_rl_model.py --device quantinuum_h2_56
```

Parametri esplicitati o impliciti:

```text
device = quantinuum_h2_56
figure of merit = expected_fidelity
training step target = 100000
hardware di training = CPU
```

Output iniziale osservato:

```text
Training RL reale: device=quantinuum_h2_56, metrica=expected_fidelity, passi=100000
mqt-predictor - INFO - Init env: expected_fidelity
Using cpu device
Wrapping the env with a Monitor wrapper
Wrapping the env in a DummyVecEnv.
Logging to ./model_expected_fidelity_quantinuum_h2_56/PPO_1
```

È comparso più volte il warning:

```text
SmallSampleWarning: One or more sample arguments is too small; all returned values will be NaN.
```

Origine del warning:

```text
bqskit/passes/synthesis/leap.py
linregress(best_layers, best_dists)
```

Interpretazione:

- il warning viene da una regressione interna del pass LEAP di BQSKit;
- non è necessariamente fatale;
- il codice prosegue se gestisce i NaN;
- diventa problematico solo se appare un traceback, se il training si blocca definitivamente o se i risultati diventano inutilizzabili.

---

## Dataset usato dal training RL

Il training RL, se non viene specificato un dataset alternativo, usa i circuiti bundled dentro il pacchetto installato di MQT Predictor.

Percorso indicato nella conversazione:

```text
~/Tesi/.venv/lib/python3.12/site-packages/mqt/predictor/rl/training_data/training_circuits/
```

Contenuto:

```text
500 circuiti QASM target-independent
range: 2–30 qubit
255 esportati tramite Qiskit
245 esportati tramite TKET
file originale: training_data_compilation.zip
```

Poiché il device scelto è:

```text
quantinuum_h2_56
```

ed è un device a 56 qubit, tutti i 500 circuiti del dataset bundled sono eleggibili dal punto di vista del numero di qubit.

Durante il training:

```text
ad ogni episodio MQT seleziona casualmente uno dei circuiti disponibili
```

Il dataset RL non coincide con il dataset supervisionato del device selector. Il dataset RL serve a insegnare alla policy a scegliere sequenze di pass di compilazione per un device e una metrica. Il dataset supervisionato, invece, serve a predire quale device è migliore per un circuito.

---

## Tempo di training e salvataggio del modello RL

Il training RL su CPU può essere molto lento.

Osservazione emersa dalla conversazione:

```text
100000 step su CPU possono richiedere giorni
l’ETA iniziale è poco affidabile
alcuni pass BQSKit possono richiedere minuti
```

PPO effettua un aggiornamento reale della rete dopo avere raccolto un rollout di dimensione tipica:

```text
2048 environment step
```

Per questo motivo ha senso valutare e salvare checkpoint a multipli di 2048 step:

```text
2048
4096
6144
8192
10240
...
```

Nella configurazione iniziale, il modello veniva salvato solo alla fine del training, nel percorso interno del pacchetto:

```text
~/Tesi/.venv/lib/python3.12/site-packages/mqt/predictor/rl/training_data/trained_model/model_expected_fidelity_quantinuum_h2_56.zip
```

Problema:

```text
se il training viene interrotto prima della fine, il lavoro corrente rischia di andare perso
```

Raccomandazione:

```text
aggiungere checkpoint periodici e ripristino prima di investire giorni di training
```

---

## Log TensorBoard del training RL

I log TensorBoard sono stati indicati in:

```text
~/Tesi/artifacts/training_logs/model_expected_fidelity_quantinuum_h2_56/PPO_1
```

Comando per monitorarli:

```bash
cd ~/Tesi
source .venv/bin/activate
tensorboard --logdir artifacts/training_logs
```

---

## Checkpoint per RL e classificatore ML

### Checkpoint RL

Per il modello RL i checkpoint hanno senso perché:

- il training è lungo;
- il training è iterativo;
- PPO migliora o peggiora nel tempo;
- è utile confrontare checkpoint diversi su validation set;
- è utile riprendere il training dopo interruzioni;
- si può decidere a quanti step fermarsi.

### Checkpoint del classificatore ML

Per il classificatore ML di MQT Predictor, invece, un checkpoint durante il training ha poco senso nel caso standard, perché il selettore è una Random Forest.

Motivi:

```text
la Random Forest non procede per episodi come PPO
non ha un vero early stopping interno come una rete neurale
il fitting è normalmente molto più veloce del training RL
salvare una foresta “a metà” offre poco vantaggio
```

La parte costosa non è il fit della Random Forest, ma la costruzione del dataset supervisionato:

```text
circuito × device → compilazione RL → score → scelta del device migliore
```

Conviene quindi salvare progressivamente:

- circuiti già compilati;
- score ottenuti per coppia circuito-device;
- feature già estratte;
- label già calcolate;
- split train/validation/test;
- configurazione dell’esperimento;
- seed;
- versioni di pacchetti, MQT Predictor, Qiskit, TKET, BQSKit.

Un checkpoint ML diventerebbe utile soprattutto se il classificatore venisse sostituito con un modello iterativo, per esempio:

```text
rete neurale
boosting con early stopping
modello incrementale
```

---

## Script che genera il dataset del device selector

Lo script citato per il device selector è:

```text
scripts/06_train_device_selector.py
```

Questo script non genera solo il dataset: esegue l’intera pipeline del classificatore supervisionato.

Pipeline concettuale:

```text
legge circuiti QASM
        ↓
per ogni circuito e per ogni device candidato usa il relativo modello RL
        ↓
compila il circuito
        ↓
calcola lo score secondo la figure of merit
        ↓
sceglie il device con score migliore
        ↓
crea feature X e label y
        ↓
addestra la Random Forest
```

Esempio di comando:

```bash
python scripts/06_train_device_selector.py \
  --devices quantinuum_h2_56 altro_device \
  --metric expected_fidelity \
  --uncompiled-circuits dataset/qasm \
  --compiled-circuits artifacts/device_selector/compiled
```

Funzione MQT sottostante:

```text
setup_device_predictor(...)
```

Conclusione importante:

```text
nella versione discussa non c’è ancora uno script separato che genera soltanto il dataset;
06_train_device_selector.py genera dati e addestra il classificatore nella stessa esecuzione.
```

---

## Cartella separata per i relatori

L’utente ha creato una cartella diversa dalla cartella WSL, sul Desktop Windows:

```text
C:\Users\elioe\Desktop\Tesi
```

Scopo della cartella:

```text
contenere solo ciò che può essere mostrato ai relatori
```

L’utente vuole escludere da questa cartella:

- Knowledge Base usata dall’AI;
- `AGENTS.md`;
- file e cartelle pensati solo per agenti o assistenti AI;
- riferimenti espliciti a ChatGPT/Codex;
- materiale non necessario alla valutazione del progetto.

Durante il controllo è stato verificato che nella cartella non risultavano:

```text
AGENTS.md
knowledge/
.codex
riferimenti espliciti a ChatGPT/Codex
```

Sono però emersi alcuni punti da sistemare o dichiarare:

1. Il `README.md` citava ancora `knowledge/` e “risultati discussi nella KB”. Questi riferimenti andavano rimossi o riscritti.
2. Il report riportava una profondità finale 8, mentre il JSON riportava profondità compilata 12.
3. I checkpoint pesavano molto:
   ```text
   checkpoint a 2048 step: circa 488 MB
   checkpoint interrotto a 2248 step: circa 1.46 GB
   cartella complessiva: circa 1.96 GB
   ```
4. Il checkpoint da 2248 step contiene anche lo stato dell’optimizer ed è quindi più utile per riprendere il training.
5. Il modello ML e il dataset del classificatore non erano ancora presenti perché lo script 06 non era ancora stato completato.
6. Se i relatori devono solo esaminare il lavoro, la cartella è sufficiente.
7. Se i relatori devono eseguire subito `qcompile` senza rifare smoke training, serve esportare i modelli con:
   ```bash
   python scripts/model_store.py export
   ```

Regola operativa importante emersa dalla conversazione:

```text
non aggiungere file o modifiche nella cartella da condividere senza consenso esplicito dell’utente
```

---

## Modifiche fatte al README e al report

È stato poi sistemato il `README.md` della cartella Desktop `Tesi`.

Modifiche principali al README:

- rimossi riferimenti a KB/knowledge;
- aggiunta struttura della cartella;
- dichiarato lo stato reale dell’esperimento;
- chiariti log e checkpoint;
- indicato che il training RL per `quantinuum_h2_56` era stato interrotto a 2248 step;
- indicato che modello RL definitivo e selettore ML non erano ancora definitivi.

È stato anche aggiornato il report sul Desktop aggiungendo riferimenti mirati al codice MQT 2.3.0 per migliorare comprensione e fact-checking.

Versione salvata:

```text
C:\Users\elioe\Desktop\Report_MQT_Predictor_Tesi_aggiornato.docx
```

Motivo del salvataggio separato:

```text
l’originale era aperto in Word
```

Riferimenti al codice aggiunti nel report:

- `qcompile`;
- costruzione delle feature;
- campionamento dei QASM nel training RL;
- reward;
- campi `X`, `y`, `names`, `scores` nella pipeline del device selector.

Correzione importante:

```text
profondità smoke test corretta: 12
```

Controlli indicati:

```text
controlli strutturali superati
controllo visivo automatico non possibile perché LibreOffice non era installato
```

---

## Origine dei pass in `compilation_information`

L’utente ha mostrato una lista di pass restituiti in `compilation_information`, tra cui:

```text
Optimize1qGatesDecomposition
CommutativeInverseCancellation
OptimizeCliffords
InverseCancellation
CommutativeCancellation
RemoveRedundancies
CliffordSimp
RemoveDiagonalGatesBeforeMeasure
PeepholeOptimise2Q
QiskitO3
SabreMapping
terminate
```

Chiarimento principale:

```text
la sequenza non è la pipeline predefinita di Qiskit
```

MQT costruisce un catalogo di azioni. La policy PPO sceglie dinamicamente da questo catalogo quale azione applicare allo stato corrente del circuito.

I singoli pass provengono da più fonti:

| Azione | Origine concettuale |
|---|---|
| `Optimize1qGatesDecomposition` | Qiskit |
| `CommutativeInverseCancellation` | Qiskit |
| `OptimizeCliffords` | Qiskit |
| `InverseCancellation` | Qiskit, configurato da MQT con specifiche coppie di gate |
| `CommutativeCancellation` | Qiskit |
| `RemoveDiagonalGatesBeforeMeasure` | Qiskit |
| `RemoveRedundancies` | TKET |
| `CliffordSimp` | TKET |
| `PeepholeOptimise2Q` | TKET |
| `SabreMapping` | azione MQT che usa `SabreLayout` di Qiskit |
| `QiskitO3` | azione composta da MQT usando più pass Qiskit |
| `terminate` | azione di controllo creata da MQT |

`QiskitO3` non è un singolo pass standard di Qiskit. È un’azione composta assemblata da MQT, che usa pass Qiskit come:

```text
Collect2qBlocks
ConsolidateBlocks
UnitarySynthesis
Optimize1qGatesDecomposition
```

Flusso di selezione dei pass:

```text
catalogo MQT di azioni
        ↓
MQT elimina le azioni non valide nello stato corrente
        ↓
la policy PPO sceglie una delle azioni rimaste
        ↓
MQT esegue il pass Qiskit/TKET/BQSKit corrispondente
        ↓
il nome dell’azione viene aggiunto a compilation_information
```

Riferimenti al codice indicati nella conversazione:

```text
rl/actions.py, righe 149-163: registro delle azioni
rl/predictorenv.py, righe 106-147: costruzione dello spazio delle azioni
rl/predictorenv.py, righe 425-448: azioni ammesse secondo lo stato del circuito
rl/predictor.py, righe 73-82: PPO sceglie l’azione e MQT salva il nome
```

Le ripetizioni nella sequenza sono possibili perché:

```text
un pass può creare nuove opportunità per applicare di nuovo lo stesso pass o un pass simile
```

Nel caso dello smoke model, però, una sequenza lunga e ripetitiva va interpretata con cautela:

```text
dimostra che la pipeline funziona, non che la policy abbia imparato una strategia ottimale
```

Sintesi:

```text
i singoli algoritmi provengono soprattutto da Qiskit e TKET;
MQT costruisce catalogo, wrapper, regole di validità e sistema RL;
la sequenza finale è scelta dalla policy PPO, non da Qiskit di default.
```

---

## Protocollo sperimentale proposto, spiegato in modo semplice

La sezione 5.2 del report descriveva un protocollo per capire se il modello RL sta davvero imparando e quando conviene fermare il training.

### 1. Dividere i circuiti in train, validation e test

Esempio con 100 circuiti:

```text
70 circuiti per train
15 circuiti per validation
15 circuiti per test finale
```

Significato:

- train: il modello impara su questi circuiti;
- validation: si controlla periodicamente se il modello migliora;
- test: si usa solo alla fine per valutare il risultato finale.

Regola fondamentale:

```text
lo stesso circuito non deve comparire in più split
```

Altrimenti la valutazione sarebbe falsata, perché il modello potrebbe essere testato su circuiti già visti.

### 2. Valutare i checkpoint ogni 2048 step

PPO aggiorna la rete dopo aver raccolto circa 2048 step. Per questo ha senso salvare e valutare checkpoint a multipli di 2048:

```text
2048
4096
6144
8192
10240
...
```

Ogni checkpoint va valutato sugli stessi circuiti di validation, così il confronto è equo.

Domanda a cui risponde questa procedura:

```text
il checkpoint a 8192 step è davvero migliore di quello a 4096?
```

### 3. Misurare la qualità dei circuiti compilati

Per ogni checkpoint bisogna misurare:

- `expected_fidelity`: più è alta, meglio è;
- eseguibilità: il circuito rispetta gate nativi e connessioni del device?
- numero di gate;
- profondità;
- tempo di compilazione;
- confronto con baseline come Qiskit O3 e TKET.

Il confronto con baseline è essenziale perché uno score isolato dice poco.

Esempio:

```text
se RL ottiene fidelity 0.80 e Qiskit ottiene 0.70, RL è interessante;
se RL ottiene fidelity 0.80 e Qiskit ottiene 0.90, RL è ancora peggiore.
```

### 4. Fermarsi quando la validation non migliora più

Esempio:

```text
Checkpoint 2048  → fidelity media 0.74
Checkpoint 4096  → fidelity media 0.79
Checkpoint 6144  → fidelity media 0.82
Checkpoint 8192  → fidelity media 0.82
Checkpoint 10240 → fidelity media 0.81
```

Interpretazione:

```text
dopo 6144 step il modello non migliora più in modo significativo
```

Continuare fino a 100000 step potrebbe quindi consumare giorni senza vantaggio reale.

### 5. Ripetere con seed differenti

Il training RL contiene casualità:

- scelta casuale dei circuiti;
- inizializzazione casuale della rete;
- esplorazione casuale delle azioni;
- possibile variabilità nei tempi e nei pass scelti.

Per evitare conclusioni basate su un singolo esperimento fortunato o sfortunato, conviene ripetere il training con più seed, per esempio:

```text
seed 1
seed 2
seed 3
```

Se i risultati sono simili tra seed diversi, la conclusione è più solida.

### 6. Conservare le migliori trace per l’LLM

Una trace è la storia completa di una compilazione:

```text
circuito iniziale
        ↓
pass scelto
        ↓
nuovo circuito
        ↓
altro pass
        ↓
...
        ↓
terminate
        ↓
reward finale
```

Le trace migliori possono diventare esempi utili per un LLM.

Esempio di uso futuro:

```text
Dato questo circuito e questo device, quale pass conviene scegliere adesso?
```

Le trace migliori possono quindi alimentare:

- prompt few-shot;
- KB tecnica;
- dataset di esempi;
- spiegazioni interpretative del comportamento della policy.

---

## Sintesi operativa aggiuntiva

Punti chiave emersi nella continuazione:

1. L’ambiente consigliato è Ubuntu 24.04 su WSL2.
2. Il progetto principale è stato spostato in `~/Tesi` e collegato a una repository privata GitHub.
3. Gli script 01–04 sono stati testati.
4. Lo smoke test valida la pipeline, ma non produce un modello scientificamente significativo.
5. Il valore corretto della profondità compilata dello smoke test GHZ è 12, non 8.
6. Per il training RL su `quantinuum_h2_56` viene usato il dataset bundled di MQT Predictor con 500 QASM target-independent da 2 a 30 qubit.
7. Il warning BQSKit `SmallSampleWarning` non è necessariamente fatale.
8. Il training RL su CPU può richiedere giorni.
9. Per RL servono checkpoint periodici, idealmente ogni 2048 step.
10. Per la Random Forest del device selector non servono checkpoint intermedi del modello.
11. La parte costosa del device selector è generare dataset, score e label, non addestrare la Random Forest.
12. Lo script `06_train_device_selector.py` genera dataset e addestra il classificatore nella stessa pipeline.
13. Nella cartella per i relatori non devono comparire KB, `AGENTS.md`, `.codex` o riferimenti espliciti a ChatGPT/Codex.
14. Il report è stato aggiornato con riferimenti mirati al codice MQT 2.3.0.
15. I pass in `compilation_information` non sono la pipeline default di Qiskit: sono azioni scelte dalla policy PPO da un catalogo MQT.
16. Il catalogo MQT combina pass Qiskit, TKET, BQSKit, azioni composte e azioni di controllo.
17. `QiskitO3` è un’azione composta di MQT, non un singolo pass standard.
18. `terminate` è un’azione di controllo, non un pass di compilazione tradizionale.
19. Il protocollo sperimentale serve a confrontare checkpoint, evitare overfitting sui circuiti visti e scegliere quando fermare il training.
20. Le trace migliori del modello RL possono diventare esempi utili per un futuro componente LLM.

---

# Continuazione KB — feedback dei relatori, revisione del report, figure of merit e reward sparse

## Contesto della nuova continuazione

Questa sezione estende la Knowledge Base con gli argomenti emersi dopo l’invio ai relatori del report e del lavoro svolto su MQT Predictor.

Materiale di partenza della conversazione:

- markdown locale in `Ubuntu/home/elioe/Tesi/knowledge`;
- report inviato ai relatori in `Desktop/Report_MQT_Predictor.pdf`;
- feedback ricevuto via mail dai relatori;
- successiva riscrittura proposta del report;
- chiarimenti concettuali su:
  - figure of merit;
  - score;
  - reward del modello RL;
  - differenza tra training e inferenza;
  - sparse reward;
  - credit assignment;
  - collegamento con TuniQ.

Il punto centrale della conversazione è che il lavoro tecnico non è stato giudicato “sbagliato”, ma il report risultava poco leggibile per un lettore esterno. I relatori hanno chiesto una struttura più chiara, meno densa e più esplicita nel filo logico.

---

## Feedback ricevuto dai relatori

I relatori hanno letto report e codice, ma hanno segnalato difficoltà nel seguire con precisione:

```text
cosa è stato fatto
perché è stato fatto
quale fosse il filo logico del lavoro
quali test siano stati eseguiti
quali risultati siano stati ottenuti
quali conclusioni si possano trarre
```

Critiche principali:

1. La **figure of merit** non era definita con chiarezza.
2. Non era chiaro come fosse effettuato il training:
   - quali metriche venissero calcolate;
   - quali score venissero usati;
   - cosa venisse ottimizzato;
   - con quale criterio.
3. La sezione 2.3 non risultava ben collegata al resto del documento.
4. In diversi punti non emergeva chiaramente:
   - cosa fosse stato fatto dall’utente;
   - perché fosse stato fatto;
   - quali conclusioni fossero state tratte.
5. Mancavano esempi pratici su:
   - dataset;
   - trace;
   - feature;
   - metriche;
   - output attesi.
6. La sezione 3.1 era troppo densa e compatta.
7. Le azioni descritte nella sezione 3.1 andavano spiegate meglio.
8. Il report conteneva molti elenchi e tabelle, rendendo meno fluido il ragionamento.
9. I dettagli implementativi minuti erano troppo presenti rispetto al contesto e alle conclusioni.
10. Tutti i concetti importanti dovevano essere definiti esplicitamente.

Interpretazione del feedback:

```text
Il problema non era necessariamente il lavoro tecnico, ma la narrazione del lavoro.
```

Il report partiva troppo “a valle”, cioè spiegava script, dettagli e componenti MQT senza guidare prima il lettore attraverso:

```text
stato iniziale
        ↓
domanda di ricerca / dubbio da chiarire
        ↓
scelte fatte
        ↓
test eseguiti
        ↓
risultati osservati
        ↓
limiti
        ↓
prossimi passi verso la tesi con LLM
```

---

## Problema principale del report originale

Il report originale tendeva a descrivere:

- cosa esiste in MQT Predictor;
- quali script sono stati realizzati;
- quali file sono presenti;
- quali componenti tecniche sono state ispezionate.

Ma non costruiva abbastanza bene il filo logico:

```text
Perché questo lavoro è utile per la tesi?
Quale domanda sperimentale si vuole chiarire?
Che cosa è stato verificato concretamente?
Cosa si può concludere dai risultati?
Cosa non è ancora dimostrato?
```

Il report doveva quindi essere reso più guidato, non necessariamente più lungo.

Formula utile:

```text
Meglio un report di 6-8 pagine chiaro e lineare
che un report più lungo, denso e pieno di dettagli implementativi.
```

---

## Correzioni urgenti individuate

### 1. Correggere “figure of metric” in “figure of merit”

La forma corretta è:

```text
figure of merit
```

Definizione da inserire subito:

```text
La figure of merit è una funzione di scoring che assegna un valore numerico a un circuito compilato.
Il candidato con score migliore diventa il vincitore secondo quella metrica.
```

Questa definizione è fondamentale perché collega:

- reward RL;
- score dei circuiti compilati;
- label del device selector;
- criterio di confronto tra alternative.

---

### 2. Collegare la sezione sulle metriche al resto del documento

La sezione 2.3 non doveva rimanere una tabella isolata.

Va introdotta dicendo che le metriche sono usate in due punti:

```text
1. come reward / criterio di qualità nel training RL;
2. come criterio per costruire score e label del device selector supervisionato.
```

Quindi la figure of merit non è un dettaglio accessorio: definisce cosa significa “buon circuito compilato”.

---

### 3. Riscrivere la sezione 3.1

La sezione 3.1 andava riscritta quasi da zero.

Ordine consigliato:

```text
1. spiegare cos’è una trace;
2. mostrare un esempio concreto di trace;
3. spiegare perché una trace è più informativa di una sola label;
4. spiegare perché le trace possono essere utili a un LLM;
5. collegare la trace al possibile obiettivo della tesi.
```

Una trace non è solo la lista finale dei pass. È la storia della compilazione:

```text
circuito iniziale
        ↓
stato osservato
        ↓
azione/pass scelto
        ↓
nuovo circuito
        ↓
nuovo stato osservato
        ↓
...
        ↓
terminate
        ↓
score finale
```

Per un LLM, una trace è più utile di una label perché contiene esempi di decisione sequenziale:

```text
Dato questo stato del circuito,
per questo device e questa metrica,
è stato scelto questo pass.
```

---

### 4. Separare training RL e training supervisionato

Nel report originale, il training RL e il training supervisionato del device selector risultavano troppo vicini e potevano sembrare un unico training.

Bisogna separarli chiaramente.

#### Training RL

Obiettivo:

```text
addestrare una policy che sceglie sequenze di pass di compilazione
per una specifica coppia device × figure_of_merit
```

Esempio:

```text
policy per quantinuum_h2_56 + expected_fidelity
```

Input concettuale:

```text
circuito nello stato corrente
device fissato
metrica fissata
azioni disponibili
```

Output:

```text
sequenza di pass di compilazione
circuito compilato finale
reward finale basata sulla figure of merit
```

#### Training supervisionato del device selector

Obiettivo:

```text
predire quale device sia più promettente per un circuito target-independent
secondo una certa figure of merit
```

Input:

```text
feature X del circuito target-independent
```

Label:

```text
device che ottiene lo score migliore dopo compilazione
```

Output:

```text
modello supervisionato, nel caso discusso una Random Forest
```

---

### 5. Spostare gli script dopo il ragionamento

Gli script non devono essere il centro narrativo del report.

Ruolo corretto degli script:

```text
strumenti usati per verificare e riprodurre il lavoro
```

Non:

```text
punto di partenza della spiegazione
```

Nel report, prima va spiegato:

```text
che cosa si vuole verificare
perché
con quale metodo
```

Solo dopo si può dire:

```text
quale script implementa o automatizza quel controllo
```

---

### 6. Aggiungere una tabella “test / input / output / conclusione”

Per rispondere direttamente al feedback dei relatori, è utile una tabella sintetica del tipo:

| Test | Input | Output osservato | Conclusione |
|---|---|---|---|
| Diagnostica ambiente | ambiente Python/WSL | dipendenze e device disponibili | l’ambiente è riproducibile |
| Lista device | API MQT Predictor | device supportati | si può scegliere un backend target |
| Smoke test `qcompile` | circuito GHZ 5 qubit | circuito compilato, trace, Target | pipeline end-to-end funzionante |
| Training RL reale | `quantinuum_h2_56`, `expected_fidelity` | checkpoint/log iniziali | training avviabile ma costoso |
| Ispezione dataset RL | cartella QASM bundled | 500 circuiti 2–30 qubit | dataset RL identificato |
| Proposta trace LLM | output `compilation_information` + score | formato di esempi sequenziali | base per KB/dataset LLM |

Questa tabella serve a chiarire rapidamente:

```text
cosa ho fatto
con quali input
cosa ho ottenuto
cosa posso concludere
```

---

## Struttura consigliata per il report rivisto

La struttura proposta per la nuova versione del report era:

```text
1. Obiettivo del lavoro

2. Stato iniziale: cosa fa MQT Predictor

3. Concetti minimi
   3.1 Circuito target-independent
   3.2 Figure of merit, score e label
   3.3 Device selector supervisionato
   3.4 Compilatore RL device-specific

4. Cosa ho fatto
   4.1 Ambiente riproducibile
   4.2 Ispezione di device, feature e dataset
   4.3 Smoke test qcompile
   4.4 Avvio training RL reale
   4.5 Proposta di formato trace per LLM

5. Esempi pratici
   dataset
   feature
   metriche
   trace
   output atteso

6. Risultati e limiti

7. Conclusioni e prossimi passi
```

Questa struttura risponde direttamente alla richiesta dei relatori:

```text
da quale stato iniziale sei partito
che cosa hai deciso di fare
perché hai seguito quella strada
quali test hai eseguito
quali risultati hai ottenuto
quali conclusioni trai
```

---

## Risposta suggerita ai relatori

Era stata proposta una risposta breve ai relatori, con tono collaborativo:

```text
Grazie per il feedback, mi è molto utile. Rileggendo il report mi rendo conto che ho compresso troppo il passaggio tra contesto, lavoro svolto e motivazione sperimentale, dando per scontati concetti come figure of merit, score, training RL e dataset del device selector.

Ristrutturerò il documento partendo dallo stato iniziale, poi chiarirò cosa ho deciso di verificare, quali test ho eseguito, quali risultati ho ottenuto e quali conclusioni si possono trarre. In particolare riscriverò la sezione 3.1 con esempi concreti di dataset, feature, trace, metriche e output attesi, e separerò meglio training RL e training supervisionato.

Vi mando una versione rivista appena pronta.
```

Questa risposta riconosce il problema senza difendersi troppo, e mostra un piano concreto di correzione.

---

## Report revisionato prodotto

Su richiesta dell’utente, è stata preparata una nuova bozza revisionabile del report.

Percorso indicato:

```text
C:/Users/elioe/Documents/MQT-Predictor-understanding/output/documents/Report_MQT_Predictor_rivisto.docx
```

La nuova bozza è stata riscritta con struttura più lineare:

```text
obiettivo
stato iniziale
concetti minimi
dataset
lavoro svolto
test
risultati
limiti
protocollo sperimentale
```

Concetti chiariti esplicitamente:

- figure of merit;
- score;
- label;
- training RL;
- training supervisionato;
- trace per LLM.

Controlli effettuati:

```text
struttura DOCX valida
titoli Word reali
audit accessibilità/tabelle senza finding
```

Limite dichiarato:

```text
non è stato possibile fare render visuale in PNG perché mancava LibreOffice/soffice nel runtime
```

Raccomandazione:

```text
aprire il file in Word e fare controllo visivo finale di impaginazione
```

---

## Chiarimento: cos’è davvero una figure of merit

L’utente ha chiesto se la figure of merit sia una “generale funzione di reward del modello RL”.

Risposta corretta:

```text
La figure of merit non è semplicemente “la reward generale” in senso astratto.
È la funzione di qualità usata da MQT Predictor per assegnare uno score a un circuito compilato.
```

Nel training RL, questo score viene usato come segnale di reward o come parte centrale della reward.

La stessa figure of merit viene usata anche per costruire le label del device selector supervisionato.

Quindi la figure of merit ha un doppio ruolo:

```text
1. definisce l’obiettivo del compilatore RL;
2. definisce il criterio con cui si sceglie il device migliore per il dataset supervisionato.
```

Formula utile per il report:

```text
La figure of merit definisce cosa significa “buon circuito compilato” nell’esperimento.
Se cambio figure of merit, cambio il criterio di qualità, quindi posso ottenere sequenze di pass diverse, reward diverse e label diverse per il device selector.
```

---

## Correzione importante: il modello RL non riceve dinamicamente device e metrica come input generale

L’utente aveva formulato l’idea:

```text
Il modello prende in input un circuito target-independent,
il device su cui si deve allenare
e la figure of merit.
```

Precisazione importante:

```text
In MQT Predictor non c’è un unico modello RL generale che riceve dinamicamente device + figure_of_merit come input e generalizza su tutti i casi.
```

Nella logica discussa, si addestra una policy specifica per ogni coppia:

```text
device × figure_of_merit
```

Esempi:

```text
policy per ibm_falcon_127 + expected_fidelity
policy per ibm_falcon_127 + critical_depth
policy per quantinuum_h2_56 + expected_fidelity
```

Quindi il device e la metrica sono fissati nella scelta/addestramento della policy.

La policy impara un comportamento specializzato per quell’hardware e per quell’obiettivo di ottimizzazione.

---

## Come scegliere una figure of merit

La scelta della figure of merit non dipende solo dal circuito logico, ma soprattutto da cosa l’utente vuole ottimizzare.

Non esiste una figure of merit migliore in assoluto.

Esempi pratici:

| Obiettivo dell’utente | Figure of merit sensata |
|---|---|
| Massimizzare una stima della probabilità che le operazioni vadano bene | `expected_fidelity` |
| Ottenere circuiti più paralleli e meno sequenziali | `critical_depth` |
| Tenere conto di tempi, idle time, `T1/T2` e decoerenza | `estimated_success_probability` |
| Valutare quanto la distribuzione di output resta vicina a quella ideale | `hellinger_distance` o `estimated_hellinger_distance` |

Esempio su `critical_depth`:

```text
Se si sceglie critical_depth, un circuito molto sequenziale viene valutato peggio di uno più parallelizzabile.
```

Nel codice MQT viene usato:

```text
1 - critical_depth
```

così il criterio rimane coerente con la convenzione:

```text
più alto è meglio
```

Per la tesi, se si vuole confrontare PPO e LLM come decisori dei pass, conviene fissare una metrica, ad esempio:

```text
expected_fidelity
```

e dichiarare:

```text
Tengo fissi circuito, device e figure of merit.
Cambio solo il decisore dei pass.
```

In questo modo le differenze osservate dipendono dal decisore, non dal criterio di valutazione.

Poi, come esperimento successivo, si può ripetere con `critical_depth` per mostrare che cambiando obiettivo cambia anche il comportamento desiderato.

---

## Figure of merit durante training e inferenza

L’utente ha chiesto:

```text
Durante il training la figure of merit assegna reward.
Quando il modello è già allenato e viene usato, a cosa serve la figure of merit?
```

Risposta:

durante il training e durante l’uso la figure of merit ha ruoli collegati ma diversi.

---

### Durante il training RL

La figure of merit definisce l’obiettivo da ottimizzare.

Nel caso discusso di MQT Predictor 2.3.0, la reward è abbastanza sparsa:

```text
per i pass intermedi la reward è 0
quando la policy sceglie terminate, viene calcolata la figure of merit sul circuito finale
```

Flusso semplificato:

```text
stato iniziale: circuito non compilato
        ↓
pass 1 scelto dalla policy → reward 0
        ↓
pass 2 scelto dalla policy → reward 0
        ↓
...
        ↓
terminate
        ↓
calcolo figure of merit sul circuito finale
        ↓
reward finale
```

Quindi non è corretto immaginare necessariamente che la figure of merit venga calcolata dopo ogni singolo pass.

---

### Durante l’inferenza / uso del modello già addestrato

Quando il modello è già addestrato, la figure of merit serve soprattutto in due modi.

#### 1. Selezionare quale modello caricare

Se si usa:

```text
expected_fidelity
```

MQT cerca/carica una policy addestrata per:

```text
device + expected_fidelity
```

Se si usa:

```text
critical_depth
```

MQT cerca/carica una policy diversa:

```text
device + critical_depth
```

Durante l’inferenza la figure of merit non “premia” più passo per passo le azioni: la policy ha già imparato un comportamento coerente con quella metrica.

---

#### 2. Valutare il circuito compilato finale

Dopo avere ottenuto il circuito finale, si può riapplicare la stessa funzione per ottenere uno score:

```text
score = figure_of_merit(circuito_compilato, device)
```

Esempi:

```text
expected_fidelity(circuito_compilato, target)
critical_depth(circuito_compilato)
estimated_success_probability(circuito_compilato, target)
```

Attenzione:

```text
qcompile normalmente non restituisce direttamente lo score.
```

Restituisce:

```text
circuito compilato
lista dei pass scelti
device / Target selezionato
```

Se serve lo score, va calcolato separatamente applicando la funzione di reward/figure of merit al circuito compilato.

---

## Esempio completo di uso della figure of merit

Esempio con `expected_fidelity`:

```text
utente sceglie expected_fidelity
        ↓
MQT usa/seleziona il device predictor addestrato per expected_fidelity
        ↓
il device selector sceglie un device
        ↓
MQT carica la policy RL per quel device + expected_fidelity
        ↓
la policy produce una sequenza di pass
        ↓
MQT restituisce circuito compilato, compilation_information e Target
        ↓
se voglio lo score, calcolo expected_fidelity sul circuito finale
```

Sintesi:

```text
Durante il training:
la figure of merit definisce la reward finale che insegna alla policy cosa ottimizzare.

Durante l’uso:
la figure of merit seleziona il modello già addestrato per quell’obiettivo
e può essere riapplicata al circuito compilato per assegnargli uno score.
```

---

## Come può imparare il modello se i pass intermedi ricevono reward 0?

L’utente ha chiesto:

```text
Come fa il modello ad imparare i passi migliori se a ogni passo riceve 0 come reward?
```

Risposta:

```text
impara per assegnazione ritardata del merito
```

In inglese, questo è il problema del:

```text
credit assignment
```

Anche se il premio arriva solo alla fine, PPO osserva l’intera traiettoria:

```text
stato_0, azione_0
stato_1, azione_1
stato_2, azione_2
...
stato_finale, terminate, reward_finale
```

Poi aggiorna la policy cercando di:

```text
aumentare la probabilità delle sequenze che hanno portato a reward finali alte
diminuire la probabilità delle sequenze che hanno portato a reward finali basse
```

Il modello non impara che un singolo pass è buono in assoluto.

Impara piuttosto una regola statistica del tipo:

```text
in stati simili, scegliere certi pass aumenta la probabilità
di arrivare a un circuito finale con score alto
```

---

## Esempio intuitivo di credit assignment

Esempio:

```text
Sequenza A:
Optimize1q → SabreMapping → BasisTranslator → terminate
score finale = 0.91

Sequenza B:
BasisTranslator → Optimize1q → SabreMapping → terminate
score finale = 0.72
```

PPO vede molte sequenze su molti episodi.

Se certe scelte compaiono spesso in traiettorie con score alto, la policy tenderà a rinforzarle.

Però il problema resta difficile:

```text
se la sequenza è lunga, la reward finale dice poco su quale azione specifica sia stata decisiva
```

Questa è la difficoltà del credit assignment.

---

## Sparse reward e limite di MQT Predictor

Una reward solo finale viene chiamata:

```text
sparse reward
```

oppure:

```text
reward ritardata
```

Vantaggio:

```text
è semplice da definire, perché basta valutare il circuito finale
```

Svantaggio:

```text
rende l’apprendimento più lento e difficile,
perché il modello deve capire da solo quali azioni intermedie hanno contribuito davvero al risultato
```

Formulazione utile per la tesi:

```text
MQT Predictor usa una reward principalmente finale: la qualità della sequenza di pass viene valutata quando il circuito compilato è terminato. Questo rende l’apprendimento possibile, ma introduce un problema di credit assignment, perché non è immediato attribuire il merito o la colpa ai singoli pass intermedi.
```

---

## Collegamento con TuniQ

Questo chiarimento è importante anche per il confronto con TuniQ.

Uno dei motivi per cui TuniQ è interessante è che introduce reward intermedie più ricche.

Idea:

```text
invece di aspettare solo la fine,
il modello riceve segnali intermedi sulla qualità delle decisioni prese
```

Esempi di segnali intermedi discussi in precedenza:

- layout quality;
- routing quality;
- estimated success probability;
- reward finale relativa a Qiskit Level 3;
- contributi legati a gate count e depth.

Questi segnali aiutano il modello a capire prima se una scelta di layout, routing o ottimizzazione sta andando nella direzione giusta.

Differenza concettuale:

```text
MQT Predictor:
reward prevalentemente finale → credit assignment più difficile

TuniQ:
reward intermedie più informative → apprendimento potenzialmente più guidato
```

Questo punto è utile per motivare perché un approccio LLM o ibrido potrebbe cercare di sfruttare le trace non solo come lista finale di azioni, ma anche come spiegazione intermedia delle decisioni.

---

## Implicazioni per la tesi con LLM

I chiarimenti su figure of merit, sparse reward e trace suggeriscono una possibile direzione sperimentale più chiara.

Obiettivo pulito:

```text
fissare circuito, device e figure of merit
e confrontare diversi decisori dei pass
```

Esempio:

```text
circuito = GHZ / circuito benchmark
device = quantinuum_h2_56
figure_of_merit = expected_fidelity

decisore A = PPO / policy RL MQT
decisore B = LLM guidato da KB/trace
baseline C = Qiskit O3 / TKET
```

In questo modo si evita di confondere più variabili:

```text
non sto cambiando metrica
non sto cambiando device
non sto cambiando circuito
sto cambiando solo il modo in cui viene scelta la sequenza di pass
```

Output da confrontare:

- circuito compilato finale;
- trace dei pass scelti;
- score secondo la figure of merit;
- profondità;
- numero di gate;
- eseguibilità sul device;
- tempo di compilazione;
- confronto con baseline.

Conclusione possibile:

```text
L’esperimento non deve dimostrare subito che l’LLM è migliore.
Può iniziare dimostrando se l’LLM riesce a produrre sequenze plausibili,
spiegabili e confrontabili con PPO e baseline classiche.
```

---

## Cosa deve ricordare un agente LLM da questa continuazione

1. Il feedback dei relatori riguarda soprattutto chiarezza, struttura e filo logico del report.
2. I relatori vogliono capire stato iniziale, scelte, motivazioni, test, risultati e conclusioni.
3. La figure of merit va definita subito come funzione di scoring su un circuito compilato.
4. La figure of merit determina cosa significa “buon circuito compilato”.
5. In MQT Predictor la figure of merit è usata sia per la reward RL sia per costruire score e label del device selector.
6. Non esiste una figure of merit migliore in assoluto: dipende dall’obiettivo sperimentale.
7. In MQT Predictor non c’è un unico modello RL generale per tutti i device e tutte le metriche; si usano policy specifiche per coppie `device × figure_of_merit`.
8. Durante il training RL discusso, i pass intermedi possono ricevere reward 0 e la reward significativa arriva al `terminate`.
9. Durante l’inferenza la figure of merit seleziona il modello/policy coerente con quell’obiettivo e può essere riapplicata per calcolare uno score finale.
10. `qcompile` non restituisce normalmente lo score: restituisce circuito compilato, `compilation_information` e device/Target.
11. Se serve lo score, va calcolato separatamente sul circuito compilato.
12. Il modello RL può imparare anche con reward finale grazie al credit assignment su intere traiettorie.
13. La reward sparsa rende però l’apprendimento più difficile, soprattutto con sequenze lunghe.
14. TuniQ è rilevante perché usa reward intermedie più informative e quindi affronta meglio il problema del credit assignment.
15. Per confrontare PPO e LLM conviene fissare circuito, device e figure of merit, cambiando solo il decisore dei pass.
16. Le trace sono importanti perché permettono di passare da una singola label finale a esempi sequenziali utili per un LLM.
17. Il report rivisto deve essere più breve, lineare e spiegato, non necessariamente più dettagliato.
18. Gli script vanno presentati come strumenti di verifica, non come centro narrativo.
19. Una tabella test/input/output/conclusione può rispondere direttamente alle richieste dei relatori.
20. La tesi può valorizzare il limite della reward sparsa come motivazione per trace, spiegabilità e possibili approcci LLM/ibridi.

---

# Continuazione KB — export dataset device selector, file `.npy`, training ML, checkpoint RL e generazione Excel portabile

## Contesto della continuazione

Questa sezione estende la Knowledge Base con gli argomenti emersi nella conversazione successiva sul progetto MQT Predictor in `~/Tesi`.

Il focus è diventato più operativo e riguarda soprattutto:

- riallineamento al contesto già salvato nella cartella `knowledge/`;
- esportazione del dataset del device selector in JSON ed Excel;
- ruolo dei file `.npy` prodotti dalla pipeline ML;
- differenza tra smoke test, training RL e training del device selector;
- possibilità o meno di allenare RL e ML in parallelo;
- gestione di checkpoint RL corrotti;
- tentativo di addestramento del device selector con più device;
- addestramento riuscito del device selector con un solo device;
- creazione di una procedura portabile per generare l’Excel senza dipendenze da Codex.

L’obiettivo pratico è rendere il progetto più leggibile e riproducibile, soprattutto per generare artefatti come tabelle Excel comprensibili ai relatori e per chiarire che cosa viene prodotto da ciascuna fase della pipeline.

---

## Riallineamento al contesto nella cartella `knowledge/`

All’inizio della conversazione è stato richiesto di rileggere il riassunto del contesto presente nella cartella:

```text
~/Tesi/knowledge/
```

Il file effettivamente presente era:

```text
knowledge/riassunto_kb_mqt_predictor.md
```

non:

```text
knowledge/riassunto_kb_mqt_predictor_tuniq.md
```

Dalla rilettura sono stati confermati i punti principali:

1. Il paper 2023 e MQT Predictor 2025 vanno distinti.
2. Nel dataset supervisionato una riga corrisponde a un circuito sorgente, non a una singola compilazione.
3. La label è il miglior candidato/device secondo la `figure_of_merit`.
4. In MQT Predictor 2025:
   - il device selector è supervisionato;
   - la compilazione viene eseguita da policy RL specifiche per `device × figure_of_merit`.
5. `qcompile` restituisce:
   - circuito compilato;
   - trace/lista dei pass;
   - `Target` del device.
6. `qcompile` non restituisce:
   - score finale;
   - probabilità del classificatore;
   - ranking completo dei device.
7. TuniQ è affine alla parte RL, ma condiziona la policy su hardware e rumore e non fa device selection.
8. Lo smoke test GHZ aveva prodotto profondità corretta pari a 12.
9. Il training RL su `quantinuum_h2_56` andava gestito con checkpoint ogni 2048 step.
10. Per il report andavano chiariti figure of merit, reward sparsa, training RL, training supervisionato, trace e protocollo sperimentale.

---

## Script per esportare il dataset del device selector in Excel

Nella cartella:

```text
tmp/mqt_dataset_export/
```

era presente uno script che genera un Excel partendo da un JSON.

L’obiettivo era modificare l’output per renderlo simile al file di riferimento:

```text
C:\Users\elioe\Documents\MQT-Predictor-understanding\output\spreadsheets\MQT_device_selector_dataset_expected_fidelity.xlsx
```

Richieste principali:

- spostare i gate count più a destra nella tabella;
- formattare i gate count senza decimali;
- salvare l’Excel generato dentro la cartella del progetto `~/Tesi`;
- rendere il risultato più leggibile e coerente con il file di riferimento.

Sono stati aggiornati due script:

```text
tmp/mqt_dataset_export/export_device_selector_dataset.py
tmp/mqt_dataset_export/build_dataset_workbook.mjs
```

Modifiche rilevanti:

1. Il JSON viene scritto dentro il progetto corrente, non più nella vecchia cartella Windows.
2. L’Excel viene salvato in:

   ```text
   output/spreadsheets/
   ```

3. Nel foglio `Dataset`, i gate count sono stati spostati più a destra.
4. La colonna degli score è stata rinominata da `score_0` a `score`.
5. Le colonne numeriche sono state formattate in modo diverso:
   - `num_qubits`, `depth` e `gate_count_*` senza decimali;
   - feature strutturali con 6 decimali;
   - `score` con 10 decimali.
6. È stato verificato che:
   - `liveness` si trova in colonna `K`;
   - i `gate_count_*` iniziano più a destra, per esempio `gate_count_u3` in colonna `L`;
   - i gate count hanno formato numerico `0`.

Output atteso:

```text
output/spreadsheets/MQT_device_selector_dataset_expected_fidelity.xlsx
```

---

## Ruolo dei file `.npy`

È stata chiarita la differenza tra i vari script rispetto alla produzione dei file `.npy`.

I file `.npy` rilevanti sono quelli del device selector supervisionato:

```text
training_data_expected_fidelity.npy
names_list_expected_fidelity.npy
scores_list_expected_fidelity.npy
```

Significato:

```text
training_data_expected_fidelity.npy
    contiene le coppie (X, y), cioè feature vector e label

names_list_expected_fidelity.npy
    contiene i nomi/identificativi dei circuiti

scores_list_expected_fidelity.npy
    contiene gli score associati ai circuiti/device
```

Percorso osservato nell’ambiente:

```text
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_data_aggregated/
```

Punto importante:

```text
i file .npy non sono prodotti dal training RL
```

Sono prodotti dalla fase ML del device selector, cioè quando viene generato il dataset supervisionato e poi addestrata la Random Forest.

---

## Differenza tra smoke training, qcompile smoke test, training RL e training ML

È importante distinguere quattro fasi diverse.

### 1. Smoke training

Lo script:

```text
scripts/03_train_smoke_models.py
```

può generare anche file `.npy`, ma solo nella parte in cui richiama la pipeline del device selector supervisionato.

In particolare, i `.npy` vengono generati quando vengono chiamate funzioni concettualmente equivalenti a:

```text
selector.generate_training_data(...)
selector.train_random_forest_model()
```

Questa fase produce dati ML del device selector, non dati RL.

### 2. Smoke test di `qcompile`

Lo script:

```text
scripts/04_test_qcompile.py
```

non genera feature vector `.npy`.

Genera invece artefatti di test come:

```text
artifacts/results/*.json
artifacts/results/*.qasm
```

Quindi lo smoke test di `qcompile` serve a verificare che la pipeline di compilazione funzioni, ma non costruisce il dataset supervisionato.

### 3. Training RL

Lo script:

```text
scripts/05_train_rl_model.py
```

allena una policy PPO per una coppia:

```text
device × figure_of_merit
```

Alla fine salva un modello RL, per esempio:

```text
model_expected_fidelity_quantinuum_h2_56.zip
```

Non genera i `.npy` del device selector.

Sintesi:

```text
Training RL → salva .zip della policy RL
```

### 4. Training device selector supervisionato

Lo script:

```text
scripts/06_train_device_selector.py
```

costruisce il dataset supervisionato e addestra la Random Forest.

Sintesi:

```text
Training device selector → genera .npy + salva Random Forest
```

---

## Come funziona lo script Excel rispetto ai `.npy`

Lo script di export non prende “tutti i file `.npy` presenti”.

Prende esattamente i tre file `.npy` corrispondenti alla metrica impostata nello script.

Esempio con:

```python
METRIC = "expected_fidelity"
```

vengono letti:

```text
training_data_expected_fidelity.npy
names_list_expected_fidelity.npy
scores_list_expected_fidelity.npy
```

Se invece la metrica fosse:

```python
METRIC = "critical_depth"
```

lo script dovrebbe leggere:

```text
training_data_critical_depth.npy
names_list_critical_depth.npy
scores_list_critical_depth.npy
```

È stata notata una possibile incoerenza da evitare:

```text
METRIC = "critical_depth"
```

ma output chiamato ancora:

```text
device_selector_dataset_expected_fidelity.json
```

Questa situazione va riallineata perché nome del file, metrica e contenuto devono essere coerenti.

---

## Parallelizzare training RL e training ML

È stata posta la domanda se fosse possibile allenare il modello ML nello stesso momento in cui si allena il modello RL.

Risposta concettuale:

```text
tecnicamente sì, ma il modello ML definitivo dipende dai modelli RL già addestrati
```

Il device selector ML ha bisogno di score e label costruiti così:

```text
circuito sorgente
        ↓
compilazione con modello RL per ogni device candidato
        ↓
calcolo score per ogni device
        ↓
label = device con score migliore
```

Quindi, se la policy RL di un device è ancora in training, il device selector non può usare quel modello come risultato definitivo.

Casi possibili:

### Caso 1 — ML in parallelo usando solo device già pronti

È possibile allenare un device selector su device per cui i modelli RL sono già disponibili e stabili.

Esempio:

```text
si allena RL per quantinuum_h2_56
nel frattempo si allena ML usando solo altri device già pronti
```

### Caso 2 — ML provvisorio usando checkpoint RL intermedi

È possibile usare un checkpoint intermedio del modello RL, ma il risultato va dichiarato come provvisorio.

In questo caso:

```text
le label sono generate da una policy RL non definitiva
```

Quindi il dataset supervisionato non rappresenta ancora il risultato finale.

### Caso 3 — Preparazione delle parti indipendenti

Mentre il training RL gira, ha senso preparare:

- QASM sorgenti;
- feature vector indipendenti dagli score;
- nomi dei circuiti;
- split train/validation/test;
- struttura delle cartelle;
- script di export.

Tuttavia la label `y` definitiva richiede lo score finale dei modelli RL.

Conclusione:

```text
per una pipeline scientificamente pulita, prima si addestrano o fissano le policy RL, poi si usa il loro output per costruire il dataset del device selector ML.
```

---

## Checkpoint RL corrotto e ripartenza da checkpoint valido

Durante il tentativo di riprendere un training RL è stato usato il comando:

```bash
python scripts/05_train_rl_model.py \
  --device quantinuum_h2_56 \
  --metric expected_fidelity \
  --timesteps 2720 \
  --resume-from artifacts/checkpoints/quantinuum_h2_56/model_expected_fidelity_quantinuum_h2_56_interrupted_2717_steps.zip
```

Errore osservato:

```text
RuntimeError: PytorchStreamReader failed locating file data/2: file not found
```

Interpretazione:

```text
il checkpoint interrupted_2717_steps.zip era corrotto o incompleto
```

Sono stati distinti:

```text
OK     model_expected_fidelity_quantinuum_h2_56_2048_steps.zip
BROKEN model_expected_fidelity_quantinuum_h2_56_interrupted_2717_steps.zip
```

Comando consigliato per ripartire dal checkpoint periodico valido:

```bash
python scripts/05_train_rl_model.py \
  --device quantinuum_h2_56 \
  --metric expected_fidelity \
  --timesteps 4096 \
  --resume-from artifacts/checkpoints/quantinuum_h2_56/model_expected_fidelity_quantinuum_h2_56_2048_steps.zip
```

Motivo per puntare a 4096 step:

```text
PPO lavora con rollout da 2048 step;
4096 è il multiplo successivo naturale dopo 2048.
```

È stato aggiornato anche:

```text
scripts/05_train_rl_model.py
```

con due miglioramenti:

1. intercettare checkpoint corrotti con un messaggio più leggibile;
2. salvare checkpoint da `KeyboardInterrupt` in modo atomico:
   - prima su file temporaneo;
   - poi rinominando il file finale.

Questo riduce il rischio di lasciare file `.zip` incompleti se il training viene interrotto durante il salvataggio.

---

## Tentativo di training del device selector con più device

È stato eseguito un tentativo di training del device selector con più device, tra cui:

```text
quantinuum_h2_56
ibm_falcon_127
```

Durante questa fase lo script era ancora nella parte di generazione del dataset:

```text
compilazione dei circuiti per ogni device candidato
```

Non era ancora arrivato al training finale della Random Forest.

Sono stati osservati file compilati per `quantinuum_h2_56`, per esempio:

```text
compiled_small/qft_indep_qiskit_4_expected_fidelity-quantinuum_h2_56.qasm
compiled_small/twolocalrandom_indep_tket_4_expected_fidelity-quantinuum_h2_56.qasm
compiled_small/routing_indep_tket_2_expected_fidelity-quantinuum_h2_56.qasm
compiled_small/qpeinexact_indep_qiskit_6_expected_fidelity-quantinuum_h2_56.qasm
```

Non risultavano invece file corrispondenti a:

```text
...expected_fidelity-ibm_falcon_127.qasm
```

Il timeout avveniva durante la compilazione per `ibm_falcon_127`.

Motivo probabile:

```text
il modello RL di ibm_falcon_127 era uno smoke/minimale e fragile
```

Un modello smoke può scegliere pass pesanti o poco adatti, soprattutto BQSKit, e quindi anche circuiti piccoli possono andare in timeout.

Conclusione operativa:

```text
il problema non era il parallelismo;
il problema era la qualità/robustezza dei modelli RL disponibili.
```

Per costruire un dataset supervisionato utile servono modelli RL abbastanza stabili per ogni device candidato. Se una policy fallisce spesso o va in timeout, il dataset diventa incompleto o sbilanciato.

---

## Quando il classificatore ML è davvero addestrato

È stato chiarito che il classificatore non è addestrato finché lo script `06_train_device_selector.py` non arriva alla fine.

Indicatore positivo nel log:

```text
Random Forest model is trained and saved.
Device selector salvato: ...
```

Finché si vede solo la fase di compilazione dei circuiti, lo script sta ancora generando dati e score.

Nel tentativo fallito con più device, la situazione era:

```text
modello RL quantinuum_h2_56 → esiste
modello RL ibm_falcon_127 → esiste, ma è smoke/debole
dataset device selector completo → no
classificatore supervisionato nuovo → no
```

File utile per verificare la presenza del classificatore salvato:

```text
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/trained_model/trained_clf_expected_fidelity.joblib
```

o, in alcune versioni/nomenclature:

```text
model_expected_fidelity.joblib
```

Il nome effettivo osservato nel log della sessione riuscita è:

```text
trained_clf_expected_fidelity.joblib
```

---

## Training riuscito del device selector con un solo device

Poiché il modello smoke di `ibm_falcon_127` era fragile, è stato rimosso `ibm_falcon_127` e il device selector è stato allenato solo con:

```text
quantinuum_h2_56
```

Comando eseguito:

```bash
python scripts/06_train_device_selector.py \
  --devices quantinuum_h2_56 \
  --metric expected_fidelity \
  --uncompiled-circuits artifacts/device_selector/uncompiled_small \
  --compiled-circuits artifacts/device_selector/compiled_small \
  --num-workers 2 \
  --timeout 120
```

Output decisivo:

```text
mqt-predictor - INFO - Random Forest model is trained and saved.
Device selector salvato: /home/elioe/Tesi/.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/trained_model/trained_clf_expected_fidelity.joblib
```

Quindi sì:

```text
il classificatore supervisionato è stato addestrato correttamente
```

Configurazione del classificatore addestrato:

```text
figure_of_merit = expected_fidelity
device candidato = quantinuum_h2_56
dataset = artifacts/device_selector/uncompiled_small
numero righe dataset esportate successivamente = 4
numero feature = 49
```

Limite importante:

```text
avendo un solo device candidato, il classificatore è banalissimo
```

Tutte le label saranno:

```text
quantinuum_h2_56
```

Quindi il modello non ha imparato davvero a scegliere tra più dispositivi. Ha però validato la pipeline end-to-end:

```text
QASM sorgenti
        ↓
compilazione con modello RL quantinuum_h2_56
        ↓
calcolo score
        ↓
generazione dataset supervisionato
        ↓
training Random Forest
        ↓
salvataggio modello ML
```

Conclusione utile per il report:

```text
È stata verificata la pipeline supervisionata end-to-end su un subset controllato:
partendo dai QASM, MQT Predictor compila i circuiti con il modello RL disponibile,
calcola gli score, costruisce feature vector e label, e salva il classificatore Random Forest.
```

Dopo il training, è stato consigliato di eseguire subito il backup:

```bash
python scripts/model_store.py export
```

---

## Export JSON del dataset e generazione Excel

Dopo il training riuscito del device selector, è stato eseguito:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py
```

Output:

```text
tmp/mqt_dataset_export/device_selector_dataset_expected_fidelity.json
rows=4 features=49
```

Questo comando crea solo il JSON, non l’Excel.

Flusso corretto iniziale:

```text
.npy
  ↓
export_device_selector_dataset.py
  ↓
.json
  ↓
build_dataset_workbook.mjs
  ↓
.xlsx
```

Quindi:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py
```

non basta per generare l’Excel.

Con il builder `.mjs`, il secondo passaggio era:

```bash
node tmp/mqt_dataset_export/build_dataset_workbook.mjs
```

Output previsto:

```text
output/spreadsheets/MQT_device_selector_dataset_expected_fidelity.xlsx
```

---

## Problema del percorso Codex e necessità di una procedura portabile

Per lanciare il builder `.mjs` era stato inizialmente suggerito un comando che usava percorsi interni a Codex, per esempio:

```text
C:\Users\elioe\.cache\codex-runtimes\codex-primary-runtime\...
```

Questo non è adatto a un progetto riproducibile perché:

```text
funziona solo su una macchina con quell’ambiente Codex configurato
```

L’utente ha chiarito che il progetto deve poter essere usato anche da chi non ha Codex.

Conclusione:

```text
il builder .mjs non è ideale come procedura pubblica/riproducibile se dipende da artifact_tool o percorsi Codex.
```

---

## Builder Excel portabile in Python

Per rendere la procedura riproducibile, è stato creato un builder Python portabile:

```text
tmp/mqt_dataset_export/build_dataset_workbook.py
```

È stata aggiunta anche la dipendenza:

```text
openpyxl==3.1.5
```

nel file:

```text
pyproject.toml
```

oppure installabile manualmente con:

```bash
python -m pip install openpyxl==3.1.5
```

Con il nuovo builder, il flusso da terminale Ubuntu diventa:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py
python tmp/mqt_dataset_export/build_dataset_workbook.py
```

Output:

```text
output/spreadsheets/MQT_device_selector_dataset_expected_fidelity.xlsx
```

Questa è la procedura da preferire per il progetto condivisibile con i relatori.

Sintesi:

```text
lasciare perdere il .mjs per l’uso pubblico;
usare il builder .py con openpyxl;
evitare dipendenze da Codex.
```

---

## Stato degli artefatti dopo questa fase

Artefatti principali prodotti o aggiornati:

```text
tmp/mqt_dataset_export/export_device_selector_dataset.py
tmp/mqt_dataset_export/build_dataset_workbook.mjs
tmp/mqt_dataset_export/build_dataset_workbook.py
pyproject.toml
output/spreadsheets/MQT_device_selector_dataset_expected_fidelity.xlsx
tmp/mqt_dataset_export/device_selector_dataset_expected_fidelity.json
```

Artefatti ML/RL rilevanti:

```text
artifacts/checkpoints/quantinuum_h2_56/model_expected_fidelity_quantinuum_h2_56_2048_steps.zip
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/trained_model/trained_clf_expected_fidelity.joblib
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_data_aggregated/training_data_expected_fidelity.npy
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_data_aggregated/names_list_expected_fidelity.npy
.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/training_data_aggregated/scores_list_expected_fidelity.npy
```

Attenzione:

```text
i percorsi dentro .venv sono utili per capire dove MQT salva i file,
ma per condividere il progetto conviene esportare o copiare gli artefatti rilevanti in cartelle versionate del progetto.
```

---

## Sintesi operativa aggiuntiva

Punti chiave di questa continuazione:

1. Il file di contesto nella KB locale è `knowledge/riassunto_kb_mqt_predictor.md`.
2. Lo script Excel è stato riallineato al formato del file di riferimento.
3. I gate count nell’Excel sono stati spostati più a destra e formattati senza decimali.
4. L’Excel viene salvato in `output/spreadsheets/`.
5. I file `.npy` del device selector non sono prodotti dal training RL.
6. I `.npy` vengono prodotti dalla pipeline del device selector supervisionato.
7. `scripts/04_test_qcompile.py` genera JSON/QASM, non feature vector `.npy`.
8. `scripts/05_train_rl_model.py` salva una policy PPO `.zip`, non il dataset ML.
9. `scripts/06_train_device_selector.py` genera dataset supervisionato e addestra la Random Forest.
10. Lo script di export prende i tre `.npy` della metrica selezionata, non tutti i `.npy`.
11. Nome del file, metrica e contenuto devono restare coerenti.
12. RL e ML possono girare in parallelo solo in casi limitati, ma il device selector definitivo dipende da policy RL già fissate.
13. Un checkpoint RL interrotto può essere corrotto; è meglio ripartire da checkpoint periodici atomici.
14. PPO lavora naturalmente a multipli di 2048 step nel setup discusso.
15. Il tentativo con `ibm_falcon_127` è fallito perché il modello smoke era fragile, non perché il training ML fosse concettualmente sbagliato.
16. Il training del device selector con solo `quantinuum_h2_56` è riuscito.
17. Con un solo device candidato, il classificatore è banale ma valida la pipeline end-to-end.
18. Il log decisivo per il training ML riuscito è `Random Forest model is trained and saved`.
19. `export_device_selector_dataset.py` crea il JSON, non l’Excel.
20. Il builder `.mjs` dipendeva da strumenti/percorso Codex e non era ideale per condivisione.
21. È stato creato un builder Python portabile con `openpyxl`.
22. Il comando riproducibile per generare l’Excel è:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py
python tmp/mqt_dataset_export/build_dataset_workbook.py
```

23. Per uso pubblico/progetto condivisibile va preferito il builder `.py`, non il `.mjs`.

---

# Continuazione KB — export Excel, TensorBoard, valutazione offline, compatibilità device e Git

## Contesto della nuova continuazione

Questa sezione aggiunge alla Knowledge Base i punti emersi nella conversazione successiva, legata soprattutto alla rifinitura degli artefatti sperimentali e alla gestione dei problemi pratici incontrati durante il training RL.

I temi principali sono:

- revisione dello script che genera l’Excel del dataset del device selector;
- significato dell’opzione `--all-available`;
- interpretazione dei log TensorBoard `PPO_1` e `PPO_2`;
- limite pratico del training RL a 4096 step;
- proposta di valutazione offline dei checkpoint;
- fallimenti di training su `rigetti_ankaa_84` e `ionq_aria_25`;
- distinzione tra device supportato come `Target` e device realmente robusto nella pipeline RL;
- gestione Git del branch `working-branch` e push errato su `main`.

Questa parte è importante perché chiarisce diversi limiti operativi del lavoro: non basta che un device sia disponibile in MQT Predictor; perché sia utilizzabile nel training RL standard devono essere compatibili anche i pass del catalogo, le librerie di compilazione sottostanti e le traduzioni verso la base nativa del backend.

---

## Revisione dello script di produzione dell’Excel

L’utente ha notato che il file Excel prodotto dallo script aveva alcuni artefatti visivi:

```text
prima riga bloccata in alto;
prime due colonne fisse durante lo scroll orizzontale;
comportamento simile a freeze panes non desiderato.
```

L’obiettivo era rendere l’Excel più pulito, leggibile e generico.

### Modifiche apportate

Lo script Excel portabile è stato sistemato con queste modifiche:

1. Rimozione dei `freeze_panes`.
2. Nessun foglio blocca più righe o colonne.
3. `export_device_selector_dataset.py` accetta ora:
   - `--metric`;
   - `--all-available`.
4. `build_dataset_workbook.py` salva il file con nome dinamico:
   ```text
   MQT_device_selector_dataset_<metric>.xlsx
   ```
5. La formattazione numerica è stata resa più robusta:
   - `score`: 10 decimali;
   - `num_qubits`: senza decimali;
   - `depth`: senza decimali;
   - `gate_count_*`: senza decimali;
   - feature strutturali: 6 decimali.
6. I gate count restano spostati a destra nel foglio `Dataset`.
7. Il file generato viene salvato nella cartella del progetto:
   ```text
   output/spreadsheets/
   ```

Al momento della verifica, nei `.npy` locali era disponibile solo la metrica:

```text
expected_fidelity
```

Quindi l’output effettivo generato era:

```text
output/spreadsheets/MQT_device_selector_dataset_expected_fidelity.xlsx
```

### Verifiche effettuate

Le verifiche citate nella conversazione includono:

```text
sintassi Python corretta;
generazione JSON/XLSX riuscita;
controllo strutturale del workbook;
freeze_panes=None su tutti i fogli;
nessun errore formula trovato;
render tecnico delle anteprime non vuoto.
```

Conclusione:

```text
lo script è ora più adatto a essere incluso nel progetto e condiviso, perché non dipende da comportamenti visivi strani e produce file coerenti con la figure of merit scelta.
```

---

## Significato di `--all-available`

L’opzione:

```bash
--all-available
```

serve a generare automaticamente gli artefatti per tutte le figure of merit per cui esistono già i tre file `.npy` necessari.

Per ogni metrica, lo script cerca una terna completa:

```text
training_data_<metric>.npy
names_list_<metric>.npy
scores_list_<metric>.npy
```

Se la terna è presente, lo script può esportare i dati per quella metrica.

Esempio: se in futuro esistessero sia `expected_fidelity` sia `critical_depth`, i comandi:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py --all-available
python tmp/mqt_dataset_export/build_dataset_workbook.py --all-available
```

produrrebbero:

```text
device_selector_dataset_expected_fidelity.json
device_selector_dataset_critical_depth.json

MQT_device_selector_dataset_expected_fidelity.xlsx
MQT_device_selector_dataset_critical_depth.xlsx
```

Senza `--all-available`, lo script lavora su una sola metrica:

```bash
python tmp/mqt_dataset_export/export_device_selector_dataset.py --metric expected_fidelity
python tmp/mqt_dataset_export/build_dataset_workbook.py --metric expected_fidelity
```

Se non viene specificata alcuna metrica, il comportamento discusso era di usare come default:

```text
expected_fidelity
```

Sintesi:

```text
--metric = lavora su una figure of merit specifica;
--all-available = lavora su tutte le metriche per cui trova i .npy completi.
```

---

## TensorBoard: perché si vedeva solo `PPO_2`

L’utente ha osservato che in TensorBoard si vedeva solo il run `PPO_2`, anche se nella cartella `training_logs` esisteva anche `PPO_1`.

Il caso riguardava un training con checkpoint a:

```text
2048 step → PPO_1
4096 step → PPO_2
```

Il controllo dei log ha mostrato:

```text
PPO_1 event file: circa 88 byte
PPO_2 event file: circa 696 byte
```

Inoltre:

```text
PPO_1: nessuno scalar utile;
PPO_2: time/fps, train/loss, train/value_loss, train/approx_kl, ...
```

Interpretazione:

```text
PPO_1 esiste come cartella, ma il suo event file è praticamente vuoto.
```

Questo può accadere perché il training si è fermato o ha salvato il checkpoint a 2048 step proprio al limite del primo rollout. In Stable-Baselines3/PPO, molte metriche `train/*` compaiono solo dopo un aggiornamento completo del modello. Quindi il checkpoint a 2048 può essere valido come artefatto, anche se TensorBoard non contiene ancora curve scalari interessanti.

`PPO_2`, invece, rappresenta il run ripreso e contiene metriche agli step successivi. In particolare, può contenere:

```text
time/fps agli step 2048 e 4096;
metriche train/* allo step 4096.
```

Conclusione:

```text
la mancanza di curve TensorBoard per PPO_1 non implica necessariamente che il checkpoint a 2048 sia inutilizzabile.
```

---

## Limite pratico: training RL costoso e pochi checkpoint informativi

L’utente ha impiegato circa:

```text
3 ore e mezza
```

per addestrare un modello RL per soli:

```text
4096 step
```

Questo rende insostenibile, almeno nell’immediato, aumentare molto il numero di step solo per ottenere curve TensorBoard più complete.

Punto importante:

```text
salvare checkpoint a 2048 e 4096 non significa automaticamente avere due risultati scientificamente confrontabili.
```

Il checkpoint a 2048 è utile per:

- riprendere il training;
- conservare un artefatto intermedio;
- documentare l’avanzamento.

Ma non basta da solo a dimostrare miglioramento, se non viene valutato sugli stessi circuiti del checkpoint a 4096.

---

## Valutazione offline dei checkpoint

Per mostrare un miglioramento senza dover proseguire il training per molte altre ore, è stata proposta una valutazione offline dei checkpoint.

Invece di affidarsi solo a TensorBoard, si possono confrontare direttamente i file `.zip` dei checkpoint:

```text
checkpoint 2048
checkpoint 4096
```

su uno stesso insieme piccolo e fisso di circuiti di validazione.

Metriche consigliate per la mini-valutazione:

- score secondo la figure of merit scelta;
- depth finale;
- gate count;
- tempo di compilazione;
- trace/pass scelti;
- successo o fallimento della compilazione;
- confronto con baseline Qiskit/TKET, se fattibile.

Esempio di tabella:

```text
Checkpoint | Circuito | Score | Depth | Gate count | Tempo | Esito
2048       | qft_4    | ...   | ...   | ...        | ...   | OK
4096       | qft_4    | ...   | ...   | ...        | ...   | OK
```

Questa valutazione è più significativa delle sole curve TensorBoard perché misura direttamente la qualità del compilatore ottenuto, non solo metriche interne del training.

Formulazione consigliata per il report:

```text
A causa del costo computazionale elevato, il training è stato limitato a 4096 step. I checkpoint a 2048 e 4096 sono stati conservati; tuttavia TensorBoard contiene metriche scalari complete solo per il secondo run. Per questo motivo il confronto tra checkpoint viene impostato tramite valutazione offline sugli stessi circuiti di validazione, invece che tramite sole curve TensorBoard.
```

---

## Fallimento del training su `rigetti_ankaa_84`

L’utente ha provato ad avviare:

```bash
python scripts/05_train_rl_model.py \
  --device rigetti_ankaa_84 \
  --metric expected_fidelity \
  --timesteps 4096
```

Il training è fallito quasi subito, dopo pochi step.

Errore principale:

```text
ValueError: The 'rxpi' gate of device 'rigetti_ankaa_84' is not supported in BQSKIT.
```

### Interpretazione

L’errore non dipendeva dal comando né dal numero di step. Era una incompatibilità concreta tra:

```text
device Rigetti ankaa 84
        +
azioni BQSKit presenti nello spazio azioni RL
        +
parser/conversione MQT verso BQSKit
```

Durante il training, la policy ha scelto quasi subito un’azione BQSKit. MQT ha provato a costruire un `MachineModel` BQSKit usando i gate nativi del device Rigetti. Tra questi gate era presente:

```text
rxpi
```

ma il parser MQT/BQSKit non sapeva tradurlo in un gate BQSKit supportato.

Il messaggio finale legato a `tqdm`/`rich` e allo shutdown di Python è stato interpretato come rumore secondario, non come causa del problema.

### Conclusione operativa

Nel setup MQT Predictor 2.3.0 discusso, `rigetti_ankaa_84` non è allenabile “out of the box” se nello spazio azioni restano abilitate le azioni BQSKit.

Opzioni possibili:

1. Non usare Rigetti per i checkpoint dimostrativi.
2. Documentare il fallimento come limite tecnico.
3. Patchare la pipeline per escludere azioni BQSKit su quel device.
4. Non aspettarsi che cambiare metrica risolva il problema.

Cambiare figure of merit, ad esempio da `expected_fidelity` a `critical_depth`, non elimina automaticamente le azioni incompatibili dallo spazio delle azioni. La metrica cambia la reward, non la compatibilità dei pass.

Finding utile per la tesi:

```text
alcuni device disponibili come Target in MQT Predictor possono fallire nel training RL perché non tutti i gate nativi sono supportati da tutte le librerie di compilazione usate internamente.
```

---

## Fallimento del training su `ionq_aria_25`

L’utente ha poi provato:

```bash
python scripts/05_train_rl_model.py \
  --device ionq_aria_25 \
  --metric expected_fidelity \
  --timesteps 4096
```

Anche questo training è fallito dopo pochissimi step.

Errore principale:

```text
Unable to translate the operations in the circuit:
["u3", "cx", "barrier", "measure"]

to the backend target basis:
{"gpi", "rz", "measure", "ms", "gpi2", "reset", "barrier", ...}
```

L’eccezione proviene da Qiskit `BasisTranslator`.

### Interpretazione

Il circuito di training contieneva gate Qiskit/OpenQASM generici, ad esempio:

```text
u3
cx
barrier
measure
```

Il device IonQ, invece, esponeva una base nativa con gate del tipo:

```text
gpi
gpi2
ms
rz
measure
reset
```

Durante il training, la policy ha scelto un’azione Qiskit che passa dal `BasisTranslator`. Qiskit non è riuscito a trovare una catena di equivalenze valida per tradurre automaticamente `u3` e `cx` nella base nativa IonQ presente nel `Target`.

Quindi il problema non era:

```text
expected_fidelity;
numero di step;
comando usato.
```

Il problema era una incompatibilità tra circuito, pass scelto e base nativa del device.

### Confronto con Rigetti

I due fallimenti hanno cause diverse, ma mostrano lo stesso pattern:

```text
rigetti_ankaa_84:
    fallisce perché BQSKit non supporta il gate nativo rxpi.

ionq_aria_25:
    fallisce perché Qiskit BasisTranslator non trova una traduzione da u3/cx alla base gpi/gpi2/ms.
```

Conclusione:

```text
MQT può esporre più device come Target, ma non tutti sono robusti per il training RL standard con l’intero catalogo di azioni.
```

---

## Device supportato come `Target` non significa training RL robusto

Un punto concettuale importante emerso dai tentativi falliti è la distinzione tra:

```text
device disponibile in MQT Predictor come Qiskit Target
```

e:

```text
device realmente utilizzabile senza modifiche nella pipeline RL standard
```

Un `Target` può descrivere correttamente:

- gate nativi;
- qubit;
- connessioni;
- durate;
- errori;
- proprietà hardware.

Ma il training RL richiede anche che ogni azione scelta dalla policy sia applicabile o gestibile con quel device. Questo coinvolge:

- Qiskit;
- TKET;
- BQSKit;
- conversioni tra circuiti;
- equivalence library;
- supporto ai gate nativi;
- basis translation;
- action masking;
- gestione degli errori dei pass.

Se anche uno solo dei pass ammessi produce un errore non gestito, il training può interrompersi.

Formula utile per il report:

```text
Il supporto di un backend come Qiskit Target non garantisce automaticamente la compatibilità con tutti i pass del catalogo RL. Alcuni backend falliscono perché la base nativa non è traducibile automaticamente dai pass Qiskit usati, oppure perché alcuni gate nativi non sono supportati da BQSKit.
```

Per ottenere checkpoint mostrabili, conviene usare un device meno problematico, anche se meno “interessante”.

---

## Cosa documentare sui tentativi falliti

I tentativi su Rigetti e IonQ non vanno considerati tempo perso. Possono essere documentati come risultati negativi informativi.

Esempio di tabella per il report o per la KB:

```text
Device           | Esito training | Errore principale                         | Interpretazione
rigetti_ankaa_84 | fallito         | rxpi non supportato in BQSKIT             | incompatibilità gate nativo/BQSKit
ionq_aria_25     | fallito         | BasisTranslator non traduce u3/cx         | equivalenze mancanti verso base IonQ
quantinuum_h2_56 | riuscito/lento  | warning BQSKit non fatale                 | device utilizzabile ma costoso
```

Conclusione sperimentale:

```text
la scelta del device per gli esperimenti non dipende solo dal numero di qubit o dall’interesse hardware, ma anche dalla robustezza della pipeline di compilazione usata dal training RL.
```

---

## Gestione Git: branch `working-branch` e push su `main`

L’utente ha aggiunto forzatamente gli artefatti con:

```bash
git add -f artifacts/
```

Poi ha committato:

```bash
git commit -m "added artifacts"
```

Il commit è stato creato sul branch:

```text
working-branch
```

Il log di `git status` indicava:

```text
On branch working-branch
Your branch is ahead of 'origin/working-branch' by 1 commit.
```

Tuttavia l’utente ha poi provato a fare:

```bash
git push origin main
```

ottenendo:

```text
! [rejected] main -> main (fetch first)
```

### Interpretazione

Il problema principale è che l’utente era su:

```text
working-branch
```

ma ha tentato di pushare:

```text
main
```

Quindi Git ha provato ad aggiornare il branch remoto `main`, non il branch in cui era stato creato il commit degli artefatti.

Il comando corretto per pubblicare il commit appena fatto era:

```bash
git push origin working-branch
```

Il messaggio `fetch first` su `main` non riguardava direttamente il commit appena creato, ma indicava che:

```text
il main locale era indietro rispetto a origin/main
```

### Nota sulle modifiche non staged

Dopo il commit risultavano ancora modifiche non staged, in particolare cancellazioni di log TensorBoard per alcuni tentativi falliti:

```text
artifacts/training_logs/model_expected_fidelity_ionq_aria_25/...
artifacts/training_logs/model_expected_fidelity_ionq_forte_36/...
artifacts/training_logs/model_expected_fidelity_iqm_crystal_54/...
artifacts/training_logs/model_expected_fidelity_rigetti_ankaa_84/...
```

Il commit effettuato includeva invece solo:

```text
artifacts/checkpoints/ibm_falcon_127/model_expected_fidelity_ibm_falcon_127_2048_steps.zip
artifacts/training_logs/model_expected_fidelity_ibm_falcon_127/PPO_1/events...
```

Conclusione operativa:

```text
per pubblicare il commit già fatto: git push origin working-branch
```

Se invece l’obiettivo è aggiornare `main`, non bisogna farlo alla cieca: occorre prima decidere se unire `working-branch` in `main`, fare merge/rebase e integrare le modifiche remote.

---

## Sintesi aggiuntiva da ricordare

1. Lo script Excel è stato reso più pulito rimuovendo i `freeze_panes`.
2. L’Excel ora usa nomi dinamici basati sulla figure of merit.
3. `--all-available` genera JSON/XLSX per tutte le metriche che hanno una terna `.npy` completa.
4. Al momento era disponibile solo `expected_fidelity`.
5. TensorBoard mostrava solo `PPO_2` perché `PPO_1` aveva un event file quasi vuoto.
6. Un checkpoint può essere valido anche se TensorBoard non contiene scalar utili per quel run.
7. Per dimostrare miglioramenti tra checkpoint è meglio una valutazione offline su circuiti fissi.
8. Il training RL a 4096 step ha richiesto circa 3 ore e mezza, quindi aumentare gli step era poco sostenibile.
9. `rigetti_ankaa_84` fallisce per incompatibilità del gate `rxpi` con BQSKit.
10. `ionq_aria_25` fallisce perché Qiskit non traduce automaticamente `u3/cx` nella base IonQ `gpi/gpi2/ms`.
11. La figure of merit non risolve incompatibilità di pass o gate nativi.
12. Un device disponibile come `Target` non è necessariamente robusto nella pipeline RL standard.
13. I fallimenti su device diversi sono risultati negativi utili da documentare.
14. Per artefatti dimostrativi conviene usare device stabili, anche se meno interessanti.
15. Il commit degli artefatti era su `working-branch`, quindi il push corretto era `git push origin working-branch`.
16. Un push su `main` richiede prima di capire lo stato di `origin/main` e integrare eventuali modifiche remote.

---
# Continuazione KB — training robusto su 600 circuiti, pulizia del workspace e dataset LLM

## Contesto di questa continuazione

Questa sezione riassume la conversazione operativa più recente. Il lavoro è
partito dalla necessità di capire se il classificatore per
`expected_fidelity` installato nella `.venv` fosse ancora il vecchio modello
addestrato sul mini dataset di 8 circuiti oppure il nuovo modello costruito sul
corpus completo di 600 circuiti.

La conversazione ha poi riguardato:

- i fallimenti della generazione del dataset del device selector;
- i messaggi di race condition, chiusura delle connessioni e crash BQSKit;
- la necessità di parallelizzare un lavoro stimato inizialmente in circa 237 ore;
- timeout esterni, worker isolati, ripartenza e checkpoint;
- il completamento della cache per tre dispositivi;
- il fitting finale della Random Forest su tutti i 600 circuiti;
- la produzione di un unico JSON leggibile;
- la semplificazione del workspace;
- la distinzione tra dataset del device selector e futuro dataset per l'LLM.

---

## Dal mini dataset al corpus da 600 circuiti

MQT Predictor 2.3.0 salva i modelli usati a runtime dentro il pacchetto
installato nella `.venv`. Questo rende facile confondere:

```text
vecchio modello smoke / mini dataset
nuovo modello completo
copia canonica conservata nel progetto
copia runtime installata nella .venv
```

Per eliminare l'ambiguità è stata adottata questa convenzione:

```text
artifacts/models/ = copia canonica e persistente
.venv/.../mqt/predictor/ = mirror runtime richiesto da MQT Predictor
```

La `.venv` non è quindi l'archivio autorevole. Se viene ricreata, i modelli
canonici devono essere reinstallati con lo script di sincronizzazione.

Il controllo finale ha confermato che il classificatore
`expected_fidelity` corrente è il nuovo modello addestrato sui 600 circuiti,
non quello del mini dataset da 8.

---

## Perché la generazione si interrompeva

L'utente aveva avviato durante la notte la costruzione del dataset su più
dispositivi, ciascuno già dotato di policy RL. L'esecuzione era però fallita e
nella CLI apparivano messaggi simili a:

```text
OS terminating due to race condition
Closing connection to remote server
```

La parte costosa non era il fitting della Random Forest, ma:

```text
600 circuiti sorgente
        ×
dispositivi compatibili
        ↓
compilazione tramite policy RL
        ↓
pass Qiskit, TKET e BQSKit
        ↓
score expected_fidelity
```

Alcuni pass, soprattutto quelli di sintesi BQSKit, possono durare molto,
creare processi o connessioni interne, terminare male durante lo shutdown,
lasciare il chiamante in attesa o fallire su blocchi troppo grandi. Un solo
caso patologico poteva quindi bloccare un'esecuzione lunga molte ore.

---

## Modifiche allo script del device selector

Lo script originariamente chiamato `06_train_device_selector.py`, ora
`scripts/04_train_device_selector.py`, è stato reso riprendibile e robusto.

Modifiche principali:

1. Cache persistente per ogni coppia circuito-device.
2. Manifest append-only con esito, timeout, errore e provenienza.
3. Worker separati per device.
4. Timeout esterno per terminare un processo realmente bloccato.
5. Riavvio del worker conservando tutti i risultati già validi.
6. Scritture atomiche degli artefatti.
7. Modalità separate:
   - `--compile-only`;
   - `--finalize-only`;
   - `--export-json-only`.
8. Fallback Qiskit sullo stesso device quando RL va in timeout o fallisce.

Il checkpoint importante del device selector non è una Random Forest
addestrata a metà. È la cache delle compilazioni già completate, dalla quale
dataset e modello possono essere ricostruiti velocemente.

---

## Timeout e lavoro parallelo

Un comando usato nella prima fase è stato:

```bash
python scripts/06_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --num-workers 2 \
  --compile-only \
  --timeout 120 \
  --max-attempts 1
```

L'esecuzione è stata interrotta dopo circa due ore, ma le compilazioni già
valide sono rimaste riutilizzabili.

Con timeout esterno di 30 secondi il log mostrava ripetutamente timeout e
riavvii, con uno stato intermedio di:

```text
613/1646 checkpoint validi
```

Abbassare ancora il timeout non era consigliato: se quasi ogni job viene
terminato prematuramente, il sistema passa il tempo a creare e distruggere
processi senza avanzare. La soluzione adottata è stata isolare i processi,
salvare ogni progresso e usare una fallback finita per i casi patologici.

---

## Fallback Qiskit

La fallback Qiskit non cambia hardware. Cambia soltanto il compilatore usato
per lo stesso circuito e lo stesso `Target`:

```text
circuito + device fissato
        ↓
tentativo con policy RL del device
        ↓
timeout / crash / errore
        ↓
qiskit.transpile(..., optimization_level=1) sullo stesso Target
        ↓
circuito compilato valido per lo stesso device
```

Serve a completare il dataset, ma una compilazione fallback non è un risultato
della policy RL. Manifest e JSON distinguono quindi `RL`,
`qiskit_fallback` e `legacy`.

---

## Problema BQSKit e valutazione dell'upgrade

BQSKit è usato da alcune azioni RL per sintesi matematiche complesse. La ricerca
di una decomposizione può diventare molto costosa oppure superare i limiti
configurati. È stato osservato anche:

```text
ValueError: Unable to compile circuit with gate larger than max_synthesis_size.
```

Questo errore riguarda il blocco sottoposto a sintesi, non la Random Forest.

È stata valutata l'idea di aggiornare a MQT Predictor 2.4.0. L'upgrade non è
stato considerato una soluzione necessaria o garantita: eventuali correzioni
non eliminano automaticamente la complessità di BQSKit, i timeout o tutte le
incompatibilità dei pass. Inoltre avrebbe modificato la baseline riproducibile
del progetto. Per questa fase si è mantenuto Python 3.12 con
`mqt.predictor==2.3.0`, risolvendo il problema operativamente nello script.

---

## Stato finale della cache

La compilazione si è conclusa con:

```text
600 circuiti sorgente
3 dispositivi:
  ibm_falcon_27
  ibm_falcon_127
  quantinuum_h2_56
1646 coppie circuito-device compatibili completate
```

Provenienza:

```text
610  compilazioni RL
1031 compilazioni Qiskit fallback
5    output legacy validi senza voce originaria nel manifest
```

Ripartizione:

```text
ibm_falcon_127:   37 RL, 558 fallback, 5 legacy
ibm_falcon_27:    35 RL, 447 fallback
quantinuum_h2_56: 538 RL, 26 fallback
```

Conclusione scientifica importante: il dataset è **ibrido**. È utile per
validare e usare la pipeline completa, ma non è un confronto puro tra tre
policy RL. La maggioranza degli output IBM proviene da Qiskit; quelli
Quantinuum provengono prevalentemente dalla policy RL.

---

## Dataset supervisionato e label

Per ogni circuito sono stati calcolati gli score `expected_fidelity`; la label
è il device compatibile con score massimo.

```text
quantinuum_h2_56: 522
ibm_falcon_127:     67
ibm_falcon_27:      11
totale:            600
```

Il dataset è fortemente sbilanciato verso `quantinuum_h2_56`. Ogni record
contiene circuito, 49 feature, score per device, label, riferimenti agli output
compilati e provenienza. È stato verificato che tutte le label coincidano con
l'argmax degli score registrati.

---

## Fitting finale della Random Forest

La pipeline originaria usava uno split 70/30 e lasciava come modello finale
quello addestrato sul solo 70%, circa 420 circuiti. Lo script è stato corretto:

1. split stratificato 70/30 per selezionare gli iperparametri;
2. `GridSearchCV` sul training split;
3. scelta dei migliori parametri;
4. nuovo fit finale su tutti i 600 campioni;
5. salvataggio della stessa copia nell'area canonica e nel runtime MQT.

Risultato verificato:

```text
modello: RandomForestClassifier
campioni del fit finale: 600
feature: 49
classi: tutti e tre i device
GridSearchCV: 5 fold, 216 candidati, 1080 fit
migliore accuratezza CV: 0.9333
```

Parametri principali:

```text
n_estimators = 100
max_depth = 14
min_samples_leaf = 2
min_samples_split = 2
bootstrap = True
```

Le copie canonica e runtime coincidono:

```text
SHA-256:
2481a764db5c4f0740788f3b852febea88595cbb37a27aeda95f467861fcaf16
dimensione: 672369 byte
```

---

## JSON canonico

Il dataset supervisionato leggibile è:

```text
datasets/device_selector_expected_fidelity.json
```

Contiene 600 record, 49 feature per record e circa 2,35 MB. Include metadati,
dispositivi, distribuzione delle label, provenienza, nomi delle feature, score e
record individuali.

Il JSON non sostituisce la cache QASM: la cache conserva gli output costosi,
mentre il JSON descrive il dataset supervisionato derivato da tali output.

Rigenerazione del solo JSON:

```bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --export-json-only
```

Rigenerazione di modello e JSON dalla cache:

```bash
python scripts/04_train_device_selector.py \
  --devices ibm_falcon_27 ibm_falcon_127 quantinuum_h2_56 \
  --metric expected_fidelity \
  --finalize-only
```

La finalizzazione dalla cache ha richiesto circa 132 secondi, perché non ha
ripetuto le compilazioni RL/BQSKit.

---

## Pulizia del workspace

Il workspace era diventato confusionario: troppi script alternativi, mini
dataset obsoleto, documentazione dispersa, modelli duplicati, log separati e
artefatti smoke già validati.

La struttura visibile è stata ridotta a:

```text
scripts/
  01_check_install.py
  02_list_devices.py
  03_train_rl_model.py
  04_train_device_selector.py
  05_sync_models.py

datasets/
  device_selector_expected_fidelity.json

artifacts/
  models/rl/
  models/device_selector/
  cache/device_selector/expected_fidelity/
  checkpoints/rl/
  logs/rl/
  logs/device_selector/expected_fidelity/

knowledge/
README.md
```

Ruoli:

- `datasets/`: dataset finali leggibili;
- `artifacts/models/`: copie canoniche dei modelli;
- `artifacts/cache/`: intermedi costosi riutilizzabili;
- `artifacts/checkpoints/`: stati intermedi dei training lunghi;
- `artifacts/logs/`: log;
- `.venv`: runtime, non archivio canonico.

Il materiale obsoleto è stato tolto dalla vista principale ma conservato in
modo recuperabile in:

```text
.workspace_archive/20260731_before_cleanup/
```

La cartella è ignorata da Git e non è stata cancellata definitivamente. La
documentazione operativa aggiornata è ora nel `README.md` della root; questa
KB conserva invece anche la storia degli esperimenti.

Le copie canoniche correnti sono:

```text
artifacts/models/rl/*.zip
artifacts/models/device_selector/trained_clf_expected_fidelity.joblib
```

Dopo avere ricreato la `.venv`:

```bash
python scripts/05_sync_models.py install
```

---

## Chiarimento finale: non è ancora il dataset LLM

Il JSON prodotto è il dataset del **device selector supervisionato**. Insegna
alla Random Forest:

```text
feature del circuito target-independent
        ↓
device con expected_fidelity stimata più alta
```

Non è ancora il dataset definitivo da fornire a un LLM. È però la materia prima
verificata:

```text
600 circuiti sorgente
49 feature per circuito
score per device
label del device migliore
1646 output compilati
provenienza RL/fallback
```

Il formato finale dipende dal compito dell'LLM.

### Compito 1 — scelta del device

```text
input  = QASM sorgente e/o feature
output = device migliore
```

Si possono derivare circa 600 esempi.

### Compito 2 — compilazione per un device

```text
input  = QASM sorgente + device + figure of merit
output = QASM compilato e/o sequenza di pass
```

Si possono derivare fino a 1646 coppie, ma bisogna decidere se usare soltanto
le 610 compilazioni RL o includere le fallback marcandone la provenienza. Un
dataset LLM autosufficiente dovrà contenere direttamente il testo QASM, non
soltanto percorsi locali.

### Compito 3 — decisione sequenziale e spiegabile

```text
input  = circuito, device, feature e stato corrente
output = pass successivo, motivazione, score previsto o trace
```

Per questo obiettivo il dataset corrente non basta: conserva output finali e
provenienza, ma non necessariamente tutti gli stati intermedi delle trace RL.

Conclusione:

```text
È stato completato il dataset supervisionato del device selector e la relativa
infrastruttura robusta di compilazione/cache.

Il prossimo passo è definire il task preciso dell'LLM e creare un unico
esportatore JSON o JSONL autosufficiente per quel task.
```

---

## Punti chiave da ricordare

1. Il modello finale `expected_fidelity` usa tutti i 600 circuiti, non gli 8
   del mini dataset.
2. La parte lenta era la compilazione circuito-device, non la Random Forest.
3. La cache contiene 1646 output e rende il lavoro riprendibile.
4. Timeout troppo bassi possono impedire il progresso.
5. BQSKit può bloccarsi o fallire; isolamento e fallback rendono la pipeline
   terminabile.
6. L'upgrade di MQT Predictor non è stato necessario né considerato una
   soluzione garantita.
7. La fallback Qiskit usa lo stesso device con un compilatore alternativo.
8. Il dataset è ibrido: 610 RL, 1031 fallback e 5 legacy.
9. Le label sono sbilanciate verso `quantinuum_h2_56`.
10. Il JSON canonico contiene 600 record e 49 feature.
11. I QASM compilati restano nella cache come intermedi costosi.
12. `artifacts/models/` è canonico; la `.venv` contiene mirror runtime.
13. Il workspace è stato ridotto a cinque script operativi.
14. Il materiale obsoleto è archiviato in modo recuperabile.
15. Il JSON corrente è una base per il dataset LLM, non il dataset LLM finale.
16. Prima dell'export LLM va deciso se il modello deve scegliere il device,
    compilare il circuito oppure scegliere e spiegare i pass.

---
# Continuazione KB — architettura del prototipo LLM e validazione

## Contesto della conversazione

Questa sezione riassume la discussione sull'architettura del prototipo
interattivo basato su LLM e sulla validazione delle sue risposte. L'obiettivo
non è dimostrare che l'LLM sia migliore o allo stesso livello di MQT
Predictor, ma misurarne le capacità decisionali, esplicative e di rispetto
del contratto.

La proposta iniziale era:

    richiesta utente + circuito nella UI
            ↓
    parser ed estrazione delle caratteristiche
            ↓
    invio delle informazioni all'LLM
            ↓
    scelta di hardware e opzioni di compilazione
            ↓
    spiegazione della scelta nella UI
            ↓
    conferma facoltativa dell'utente
            ↓
    compilazione Qiskit e restituzione del circuito

Il flusso è valido come esperienza utente e come MVP. Non è però sufficiente
come architettura interna se l'LLM rimane l'unica autorità su compatibilità,
opzioni ammesse e correttezza. Queste responsabilità devono restare
deterministiche, verificabili e riproducibili.

---

## Architettura ibrida consigliata

Il flusso consigliato è:

    richiesta + circuito + obiettivo + vincoli
            ↓
    UI
            ↓
    application service / orchestratore
            ↓
    parsing e validazione del circuito
            ↓
    CircuitProfile e feature
            ↓
    catalogo hardware versionato
            ↓
    filtro deterministico dei candidati compatibili
            ↓
    DecisionContext con sole alternative ammesse
            ↓
    LLM decision maker
            ↓
    risposta JSON strutturata
            ↓
    validazione deterministica della risposta
            ↓
    raccomandazione e spiegazione nella UI
            ↓
    conferma dell'utente
            ↓
    adapter Qiskit o MQT Predictor
            ↓
    validazione del circuito compilato
            ↓
    QASM, configurazione, metriche, warning e provenienza

Responsabilità principali:

- La UI raccoglie input, obiettivo e vincoli e mostra i risultati; non
  contiene logica scientifica.
- Il parser trasforma il QASM in una rappresentazione canonica, ad esempio un
  QuantumCircuit, applica limiti e segnala input non valido.
- Il feature extractor genera il profilo del circuito e, quando necessario,
  le 49 feature compatibili con la pipeline MQT locale.
- Il catalogo hardware è la sorgente autorevole per numero di qubit, gate,
  connettività, proprietà del Target, compilatori e opzioni disponibili.
- Il filtro di compatibilità elimina prima della chiamata LLM le alternative
  impossibili.
- Il context builder presenta all'LLM soltanto informazioni e alternative
  rilevanti.
- L'LLM sceglie nello spazio ammesso e restituisce motivazioni ed evidenze.
- Il validator tratta l'output LLM come input non affidabile.
- Il compiler adapter esegue con Qiskit o MQT la decisione già validata.
- Il result validator controlla il circuito compilato e registra gli
  artefatti.

La separazione è logica: per il primo prototipo UI e backend possono stare
nello stesso processo; non servono microservizi.

---

## Distinzione rispetto a MQT Predictor

Se l'LLM sceglie sia hardware sia configurazione Qiskit, il task è
concettualmente vicino al predictor del 2023:

    circuito → device + compilatore + impostazioni

MQT Predictor 2025 separa invece:

    circuito → classificatore supervisionato sceglie il device
             → policy RL specifica del device sceglie i pass
             → circuito compilato

Una pipeline in cui l'LLM sceglie la configurazione e Qiskit la esegue è
quindi un sistema LLM + Qiskit distinto, non MQT Predictor 2025.

Sono state suggerite due modalità:

    llm_qiskit:
        LLM sceglie device e opzioni;
        Qiskit esegue la configurazione validata.

    mqt_predictor:
        il classificatore MQT sceglie il device;
        la policy RL sceglie i pass;
        l'LLM può presentare o spiegare il risultato.

MQT Predictor può fungere da baseline senza diventare una soglia che l'LLM
deve necessariamente eguagliare.

---

## Informazioni da fornire all'LLM

Non conviene inviare soltanto il vettore numerico grezzo. Il DecisionContext
dovrebbe contenere:

- obiettivo di ottimizzazione;
- vincoli espliciti dell'utente;
- profilo sintetico e feature rilevanti del circuito;
- soli device compatibili;
- metadati hardware necessari alla decisione;
- compilatori e opzioni consentite;
- eventuali esempi recuperati dal dataset o dalla KB.

Esempio concettuale:

    {
      "objective": "expected_fidelity",
      "user_constraints": {
        "preferred_vendor": null
      },
      "circuit": {
        "num_qubits": 12,
        "depth": 84,
        "gate_count": 230,
        "two_qubit_gate_count": 41,
        "entanglement_ratio": 0.178
      },
      "compatible_devices": [
        {
          "id": "ibm_falcon_127",
          "num_qubits": 127
        }
      ],
      "allowed_options": {
        "optimization_level": [0, 1, 2, 3],
        "layout_method": ["trivial", "dense", "sabre"],
        "routing_method": ["basic", "lookahead", "sabre"]
      }
    }

Catalogo e allowlist devono provenire dal backend e non dalla memoria interna
dell'LLM.

---

## Contratto strutturato della risposta

L'LLM non dovrebbe restituire soltanto prosa, codice o pass arbitrari. Deve
produrre JSON aderente a uno schema, per esempio:

    {
      "selected_device": "ibm_falcon_127",
      "compiler": "qiskit",
      "options": {
        "optimization_level": 3,
        "layout_method": "sabre",
        "routing_method": "sabre",
        "seed_transpiler": 42
      },
      "reasons": [
        {
          "choice": "selected_device",
          "claim": "Il dispositivo ha capacità sufficiente.",
          "evidence": [
            "circuit.num_qubits",
            "devices.ibm_falcon_127.num_qubits"
          ]
        }
      ],
      "alternatives": [],
      "warnings": [
        "Expected fidelity è una stima, non una misura hardware."
      ]
    }

La spiegazione mostrata nella UI può essere ricavata da questi campi, così
rimane collegata alla decisione effettivamente eseguita. Una confidence
dichiarata dall'LLM non va trattata come probabilità calibrata.

---

## Conferma e riproducibilità

La conferma dell'utente deve riferirsi a un identificatore immutabile della
raccomandazione, costruito almeno da:

- hash del circuito sorgente;
- decisione validata;
- versione del catalogo hardware;
- versione del modello LLM;
- versione del prompt;
- versioni delle librerie;
- seed di compilazione.

In questo modo viene compilata esattamente la configurazione mostrata.

Una API minima può usare:

    POST /recommendations
        richiesta + QASM + obiettivo + vincoli
        → raccomandazione + recommendation_id

    POST /compilations
        recommendation_id
        → job_id

    GET /compilations/{job_id}
        → stato + circuito + metriche + artefatti

---

## Perché ricontrollare i vincoli già mascherati

Il masking prima della chiamata LLM riduce lo spazio di scelta, ma un prompt
non garantisce l'output. Il modello può comunque inventare un device, un
livello di ottimizzazione o una combinazione non prevista. Gli stessi vincoli
devono quindi essere ricontrollati nella risposta.

Non bisogna però duplicare le regole. La stessa policy deve generare la
maschera e validare l'output:

    allowed_options = policy.compute_allowed_options(context)

    prompt = context_builder.build(
        context=context,
        allowed_options=allowed_options,
    )

    raw_response = llm.generate(prompt)
    decision = decision_parser.parse(raw_response)

    violations = policy.validate(
        decision=decision,
        allowed_options=allowed_options,
    )

Questo evita divergenze tra le alternative dichiarate nel prompt e quelle
accettate dal backend.

---

## Tre livelli distinti di controllo

### Validazione della risposta LLM

Stabilisce se la decisione è utilizzabile, senza giudicare se sia la migliore:

- JSON sintatticamente valido;
- schema rispettato;
- campi obbligatori presenti;
- assenza di campi sconosciuti, se lo schema è chiuso;
- device appartenente ai candidati;
- compilatore e opzioni nelle allowlist;
- tipi e intervalli corretti;
- vincoli utente rispettati;
- coerenza tra i campi;
- motivazioni collegate a dati realmente presenti.

### Validazione della compilazione

Avviene dopo la conferma dell'utente:

- Qiskit o l'adapter accetta la configurazione;
- la compilazione termina senza errore;
- il circuito usa operazioni supportate dal Target;
- la connettività è rispettata;
- il circuito risulta eseguibile sul device;
- il comportamento è preservato, quando verificabile.

Questo non è un controllo di performance. Un circuito può essere più profondo
o meno ottimizzato e risultare comunque valido.

Per circuiti piccoli la preservazione semantica può essere controllata tramite
equivalenza di operatori o simulazione. Per circuiti grandi servono controlli
più economici e compatibili con misure, reset e circuiti non unitari.

### Valutazione delle capacità dell'LLM

Serve all'esperimento e produce misure:

- percentuale di JSON validi al primo tentativo;
- rispetto dello schema e delle alternative ammesse;
- grounding delle spiegazioni;
- successo della compilazione;
- stabilità su richieste ripetute;
- sensibilità a obiettivi e vincoli diversi;
- capacità di correggersi dopo feedback;
- eventuale accordo con MQT Predictor o ground truth offline.

Accordo con MQT e qualità della figure of merit possono essere metriche
descrittive, ma non criteri binari di validità.

---

## Controlli ulteriori rispetto alle allowlist

Valori singolarmente validi possono formare combinazioni non valide. Servono:

- controllo strutturale di JSON, schema, campi e tipi;
- controllo referenziale di device e profili;
- controllo degli intervalli numerici;
- controllo cross-field tra compilatore, device e opzioni;
- controllo dei vincoli utente;
- controllo di grounding delle affermazioni;
- controllo di eseguibilità della configurazione;
- controllo di basis e connettività sul risultato.

È inoltre utile separare il parsing dell'intento dalla decisione. Se obiettivo
e vincoli sono anche campi espliciti della UI, è più facile capire se un
fallimento appartiene alla comprensione linguistica o alla scelta.

---

## Grounding delle spiegazioni

La prosa libera è difficile da validare. Sono preferibili coppie
claim/evidence:

    {
      "claim": "Il dispositivo ha capacità sufficiente.",
      "evidence": [
        {
          "field": "circuit.num_qubits",
          "value": 20
        },
        {
          "field": "devices.ibm_falcon_127.num_qubits",
          "value": 127
        }
      ]
    }

Il backend può verificare che:

- i campi citati esistano;
- i valori coincidano con il DecisionContext;
- l'evidenza riguardi il device selezionato;
- non vengano citate metriche assenti;
- expected_fidelity non venga presentata come misura hardware;
- la spiegazione riguardi le opzioni realmente selezionate.

Questo non dimostra che tutta la spiegazione sia perfetta, ma rende
misurabili molte allucinazioni.

---

## Non correggere silenziosamente

Per misurare le capacità dell'LLM bisogna conservare:

- prompt e DecisionContext;
- risposta originale;
- risultato del parsing;
- violazioni trovate;
- eventuale feedback di correzione;
- risposta dopo il retry;
- decisione effettivamente eseguita;
- risultato della compilazione.

Correggere silenziosamente, per esempio convertendo "three" in 3, farebbe
apparire il modello più capace.

È possibile usare un retry controllato:

    primo tentativo non valido
            ↓
    registrazione del fallimento first-pass
            ↓
    feedback strutturato con gli errori
            ↓
    secondo tentativo dell'LLM

Si misurano così:

    first_pass_validity = rispetto immediato del contratto
    repair_success      = capacità di correggersi dopo feedback

Stati utili:

    valid_first_pass
    valid_after_repair
    invalid_json
    invalid_schema
    invalid_reference
    constraint_violation
    unsupported_explanation
    compiler_configuration_error
    compilation_error
    compiled_but_not_target_valid
    success

---

## Performance e criterio di successo

Il criterio principale può essere:

    La risposta dell'LLM è sintatticamente valida, rispetta i vincoli,
    è giustificata con informazioni disponibili e, se richiesto,
    produce una compilazione corretta per il Target selezionato.

Non è necessario imporre:

    La configurazione scelta deve essere la migliore possibile.

Depth, gate count, expected fidelity, accordo con la label offline, accordo
con MQT Predictor e regret possono comunque essere salvati come misure
descrittive del comportamento.

---

## Scheletro logico suggerito

Per separare il prototipo dagli esperimenti MQT già presenti:

    prototype/
    ├── src/quantum_assistant/
    │   ├── main.py
    │   ├── config.py
    │   ├── ui/
    │   ├── api/
    │   ├── domain/
    │   ├── ingestion/
    │   │   ├── qasm_parser.py
    │   │   └── circuit_validator.py
    │   ├── analysis/
    │   │   ├── feature_extractor.py
    │   │   └── intent_parser.py
    │   ├── hardware/
    │   │   ├── catalog.py
    │   │   └── compatibility.py
    │   ├── decision/
    │   │   ├── context_builder.py
    │   │   ├── llm_client.py
    │   │   ├── response_validator.py
    │   │   └── mqt_baseline.py
    │   ├── compilation/
    │   │   ├── qiskit_adapter.py
    │   │   ├── mqt_adapter.py
    │   │   └── result_validator.py
    │   ├── evaluation/
    │   └── storage/
    ├── schemas/
    │   ├── recommendation_request.schema.json
    │   ├── decision_context.schema.json
    │   ├── llm_decision.schema.json
    │   └── compilation_result.schema.json
    └── tests/
        ├── unit/
        ├── integration/
        └── fixtures/circuits/

---

## Riutilizzo del dataset LLM esistente

Il dataset end-to-end già prodotto contiene gran parte del DecisionContext:

- QASM sorgente;
- feature del circuito;
- figure of merit;
- catalogo hardware;
- ranking del device selector;
- ground truth offline quando disponibile;
- trace della policy RL;
- circuito compilato;
- score e validazione finale.

Conviene derivare i contratti del prototipo dallo schema esistente. Se i
record vengono usati come esempi few-shot o tramite retrieval, bisogna evitare
data leakage: il circuito valutato e circuiti quasi duplicati o della stessa
famiglia non devono apparire come esempi contenenti la risposta corretta.

---

## Sintesi operativa finale

1. La proposta iniziale è valida come esperienza utente.
2. La UI non deve orchestrare direttamente parser, LLM e compilatore.
3. Parsing, feature extraction e compatibilità restano deterministici.
4. L'LLM sceglie soltanto tra alternative esplicitamente ammesse.
5. La risposta deve essere JSON strutturato e validabile.
6. I vincoli usati per mascherare l'input vanno ricontrollati nell'output.
7. La stessa policy deve generare la maschera e validare la decisione.
8. Servono anche controlli cross-field e di grounding.
9. Validità della decisione, validità della compilazione e qualità della
   scelta sono concetti distinti.
10. Non è richiesto che l'LLM raggiunga MQT Predictor in performance.
11. Performance e accordo con MQT possono essere misure descrittive.
12. Risposta originale ed errori devono essere conservati.
13. Le correzioni non devono alterare la misura first-pass.
14. Un retry controllato misura anche la capacità di repair.
15. Dopo la conferma va compilata la decisione mostrata e versionata.
16. Il risultato include circuito, configurazione, validazione, metriche,
    warning e provenienza.
17. MQT Predictor può restare una modalità separata e una baseline.
18. Il dataset LLM esistente è una base naturale, ma va usato senza leakage.

---

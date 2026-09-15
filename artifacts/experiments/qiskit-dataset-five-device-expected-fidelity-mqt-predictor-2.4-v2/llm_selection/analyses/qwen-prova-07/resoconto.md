# Analisi della prova tecnica qwen-prova-07

Il 14 settembre 2026 la prova è durata dalle 15:18:30 alle 19:14:06, ora italiana:
3 ore, 55 minuti e 36 secondi. Il programma è terminato con codice 0, ma ha
registrato zero scelte valide su cinque circuiti. Non è iniziata la validation.

## Che cosa ha fatto

Il comando ha verificato i pesi, caricato Qwen3.5-4B e sottoposto al modello
cinque circuiti train, uno alla volta. Per ogni circuito ha recuperato cinque
esempi dal Dataset e preparato una richiesta completa. Il modello doveva scegliere
un dispositivo compatibile e una configurazione Qiskit, con riferimenti alle
evidenze fornite. Alla fine il programma controllava la risposta.

Non ha addestrato modelli, aggiornato il Training set, prodotto nuove compilazioni
o eseguito circuiti su hardware quantistico. È una prova di sostenibilità tecnica.

Profilo effettivo: Qwen3.5-4B Q8_0, cache q8_0, contesto 147.456 token,
llama.cpp b10930 su Windows/Vulkan, RX 6750 XT 12 GB, tutti i livelli richiesti
sulla GPU, una richiesta alla volta, batch 512, micro-batch 128, sei thread.
Configurazione p1_t0: controlli aggiuntivi nel prompt, temperatura 0,
seed 20260913 e ragionamento esteso disabilitato. Limiti: 2.048 token di risposta,
3.600 secondi per chiamata, massimo tre chiamate per correggere risposte non conformi.
Sono state effettuate cinque chiamate: nessuna correzione o ripetizione di trasporto.

## Prompt processing e percentuali

È il calcolo sul testo in ingresso prima di scrivere la risposta.
Include istruzioni, circuito, dispositivi, esempi RAG ed evidenze.
I token sono frammenti di testo, non parole o circuiti.
Dopo la lettura inizia la generazione della risposta.
Il tempo limite comprende entrambe le fasi e le eventuali pause.

progress=0.99 significa circa 99%, non 99,99%. Negli ultimi conteggi salvati:

- su2random_indep_qiskit_50: 132.096 su 133.176 token, 99,189%; mancavano 1.080 token, lo 0,811%.
- su2random_indep_tket_50: 132.096 su 133.700 token, 98,800%; mancavano 1.604 token, l'1,200%.

Sono osservazioni precedenti all'annullamento, non misure al momento esatto del timeout.
Nessuna delle due chiamate ha restituito testo. È scaduto il tempo, non il contesto:
anche 133.700 + 2.048 è inferiore ai 147.456 token disponibili.

## Risultati

| Circuito | Token ingresso | Lettura | Generazione | Totale chiamata | Esito registrato |
|---|---:|---:|---:|---:|---|
| ae_indep_qiskit_60 | 110.880 | 42 min 59 s | 8 min 31 s | 51 min 31 s | Errore del programma |
| dj_indep_tket_2 | 80.612 | 22 min 59 s | 7 min 32 s | 30 min 31 s | Errore del programma |
| portfoliovqe_indep_qiskit_6 | 83.905 | 24 min 48 s | 7 min 05 s | 31 min 53 s | Errore del programma |
| su2random_indep_qiskit_50 | 133.176 | Incompleta | Nessuna risposta | 60 min | Timeout |
| su2random_indep_tket_50 | 133.700 | Incompleta | Nessuna risposta | 60 min | Timeout |

I primi tre casi riportano cannot pickle 'mappingproxy' object.
Ho ricontrollato le risposte originali senza chiamare il modello.
Le impronte del codice coincidono con quelle della prova; anche i prompt ricostruiti
coincidono con quelli salvati.

- ae: 2.048 token prodotti; limite raggiunto e JSON troncato.
- dj: 1.993 token, fine naturale e JSON leggibile; riferimenti storici senza claim sorgente, riferimenti non dichiarati e parametri incoerenti. Proposta non accettata: ibm_falcon_127.
- portfoliovqe: 1.856 token, fine naturale e JSON leggibile; evidenze associate al record sbagliato, riferimenti mancanti e parametri incoerenti. Proposta non accettata: quantinuum_h2_56.

Quindi: testo ricevuto in 3/5 chiamate (60%); JSON sintatticamente valido in 2/5 (40%);
raccomandazioni valide in 0/5. I due JSON completi sono proposte rifiutate,
non decisioni utilizzabili per valutare il dispositivo migliore.

## Difetto del programma

llm_selection/run.py:50 usa dataclasses.asdict sui ValidationIssue.
Questi contengono details, reso immutabile tramite MappingProxyType in
prototype/quantum_assistant/models.py. La copia profonda di asdict fallisce.
Il metodo to_dict già presente converte correttamente questi oggetti.
La riproduzione e gli errori di validazione sono in offline_validation.json.

Il difetto maschera l'errore nella risposta come infrastructure_failure e blocca
la correzione automatica. Tre decision.json riportano anche measured_call_seconds=0,
pur conservando i tempi reali nei rispettivi call/response.json.
Questa analisi usa i tempi originali: quegli zeri non sono misure reali.
Il codice del sistema e gli esiti originali non sono stati modificati.

## Perché è lento

I prompt sommano 542.273 token in ingresso. Gli ultimi conteggi registrano
539.589 token elaborati. Le risposte prodotte sommano 5.897 token.
Le chiamate durano complessivamente 3 ore, 53 minuti e 56 secondi.
La lettura occupa circa 3 ore e 30 minuti, circa il 90% del tempo delle chiamate;
la scrittura delle tre risposte circa 23 minuti.

Recupero e ricostruzione del contesto: 5,68–7,60 secondi per circuito.
Verifica dei pesi: 38,02 secondi. Avvio registrato del server: 14,51 secondi.
Queste fasi non spiegano le ore di attesa.

Anche il circuito da due qubit genera 80.612 token. Il prompt inviato contiene
circa 158.000 caratteri: circa 105.000 per gli esempi e 30.000 per il registro
delle evidenze. Queste grandezze sono caratteri, non token.
La parte dominante è il materiale consegnato al modello, non soltanto il circuito.
La codifica reversibile dei grafi completi è già applicata.

Velocità media di lettura: 36,8–58,5 token/s; scrittura: 4,0–4,4 token/s.
All'inizio del primo prompt si osservano circa 467 token/s su 1.536 token;
alla fine la media scende a circa 43 token/s. Il costo aumenta con il contesto.
È coerente con l'architettura, che comprende anche attenzione completa.
Non abbiamo misurato separatamente il costo delle singole operazioni Vulkan.

Tutte le chiamate hanno timings.cache_n=0: nessun prefisso risulta riutilizzato.
usage.cached_tokens contiene invece un contatore finale diverso, che supera
perfino la dimensione del prompt. Non va interpretato come risparmio misurato.

## Risorse e limiti

13.161 campioni delle risorse. Attività media GPU 98,56%, misurata sull'intera scheda.
Hotspot massimo 94 °C; edge massimo 74 °C; zero pause termiche e zero arresti
del monitor. Il profilo effettivo aveva pausa hotspot a 105 °C e ripresa sotto
100 °C: fa fede launch.json, non le soglie generiche nel protocollo.
Questa analisi non modifica né raccomanda di alzare tali soglie.

RAM Windows disponibile minima 2,77 GiB. Picco Python 1,67 GiB, cumulativo del processo.
Memoria GPU del server: dedicata massima 7,32 GiB, condivisa 0,67 GiB.
La memoria condivisa da sola non dimostra paginazione o trasferimento dei calcoli.
I private bytes non sono RAM residente. Le medie sono pesate per campione.
Non abbiamo evidenza di arresti per RAM; non possiamo quantificare il vantaggio
di un altro motore, precisione, cache o dimensione dei blocchi senza nuove prove.

## Che cosa manca prima della validation

Questa prova verifica caricamento, dimensione dei prompt, generazione, controlli
delle risposte e raccolta dei dati. Mostra che il profilo non è ancora pronto.
Non misura qualità della scelta, regret, fidelity o generalizzazione.
Sono casi train; il recupero può includere lo stesso circuito richiesto.

Occorre correggere il salvataggio degli errori e dei tempi, verificarlo sulle
risposte conservate e provare una rappresentazione meno ripetitiva di cataloghi
ed evidenze che mantenga informazione e riproducibilità.
Vanno verificati anche spazio di risposta, correttezza dei riferimenti e riuso
dei prefissi. Variazioni di precisione o micro-batch richiedono prove distinte.
Aumentare solo il timeout non accelera nulla: serve tempo anche per scrivere.

Nessuna nuova inferenza è stata avviata per questa analisi.

## Artefatti e riproducibilità

- statistics.json: aggregati, risorse, configurazione e limiti.
- per_circuit.csv e per_circuit.json: misure per circuito.
- offline_validation.json: riesame delle risposte e riproduzione del difetto.
- prompt_section_characters.json: dimensioni dopo la codifica reversibile.
- source_hashes.json: impronte dei 98 file originali letti, circa 21,1 MB; non include l'intera copia del codice o i pesi.
- analyze.py: procedura eseguita. Richiede la .venv e il contesto locale originale. Rifiuta di sovrascrivere risultati esistenti.
- analysis_manifest.json: impronte dei file di questa analisi.

Per riprodurre l'analisi, copiare analyze.py in una nuova cartella di analisi
ed eseguirlo dalla radice del progetto con:
PYTHONPATH=. .venv/bin/python PERCORSO/analyze.py

I dati originali sono sotto controllers/qwen-prova-07,
technical_episodes/qwen-prova-07 e servers/qwen-prova-07-qwen.
Quest'ultimo percorso punta ai registri Windows sul disco D.
Non è un esperimento di validation e non produce una relazione LaTeX di validation.

Riferimenti esterni di supporto, distinti dai fatti osservati:
[contatori llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
e [architettura Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B).
Le pagine descrivono software corrente; per la prova fa fede b10930.

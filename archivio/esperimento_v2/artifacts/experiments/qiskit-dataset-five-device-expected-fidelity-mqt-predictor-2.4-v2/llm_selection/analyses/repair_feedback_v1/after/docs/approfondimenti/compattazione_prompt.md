# Prompt essenziale dell'assistente

Dal 18 settembre 2026 chat del prototipo, prove automatiche ed esportazione
usano la vista essenziale, ora alla revisione `minimal-v3-repair1-20260918`.
Il modello riceve JSON.
TOON non è usato.

## Che cosa vede il modello

Il programma prepara ancora la richiesta completa. Conserva QASM, identificativi
originali, manifest e registro delle evidenze nei dati dell'esperimento.
Prima dell'invio produce una vista più piccola:

- circuito corrente con tutte le caratteristiche numeriche originali;
- obiettivo e vincoli normalizzati;
- un catalogo dei dispositivi compatibili e delle configurazioni ammesse;
- cinque esempi nello stesso ordine del recupero;
- per ciascun esempio: circuito e caratteristiche, nomi dei dispositivi
  compatibili, dispositivo vincente e prime tre configurazioni ordinate,
  con associazione al dispositivo, mediana storica e parità già registrate.

Le feature non sono arrotondate e gli zeri restano presenti. Il modello non
riceve QASM, hash, manifest, versioni dei dati, copie del registro delle evidenze
o descrizioni hardware ripetute dentro gli esempi. I risultati storici non
sono nuove misure del circuito da valutare.

La topologia completa è indicata esplicitamente come tale, senza elencare
tutti gli archi. Le altre topologie mantengono l'elenco dei collegamenti.
Se tutti i dispositivi ammettono le configurazioni del catalogo, non si ripete
l'elenco completo per ogni dispositivo; eventuali restrizioni restano esplicite.

## Risposta e controlli

La risposta ha quattro campi:

```json
{
  "selected_device": "ibm_falcon_27",
  "config_id": "o2_default_default",
  "claim": "Motivazione breve delle due scelte, basata sugli esempi citati.",
  "evidence": ["E2", "E4"]
}
```

È un esempio di formato, non una risposta prodotta da Qwen.
La versione 3.0.0 è registrata dal programma; il modello non deve ricopiarla.
Il programma ricava i parametri Qiskit dal catalogo e usa il primo seed del
protocollo, attualmente 0. Non corregge silenziosamente le scelte.

E1...E5 sono riferimenti locali, assegnati nell'ordine del recupero.
La mappa resta uguale durante le correzioni della stessa richiesta e non viene
inviata al modello. Il contesto delle citazioni contiene anche l'identità
della richiesta, il catalogo e impronte del registro e della richiesta effettiva.
Controlla sorgente, obiettivo, vincoli e feature, evitando di riutilizzare
una mappa appartenente a un'altra richiesta.

Il validatore verifica formato, dispositivo compatibile, configurazione ammessa
e appartenenza delle citazioni agli esempi forniti. Rifiuta riferimenti
sconosciuti e duplicati. Con risultati storici richiede almeno una citazione;
senza RAG richiede una lista vuota. Lo stesso esempio può motivare entrambe le
scelte. Non servono identificativi separati di claim o caveat.

**La risoluzione della citazione non verifica semanticamente il testo libero
e non dimostra che il modello abbia causalmente usato quell'esempio.**
Questo limite è registrato anche nella raccomandazione e nelle avvertenze.
Le vecchie verifiche multilivello non sono applicate al nuovo claim libero.
La compilazione rimane protetta: occorrono una raccomandazione emessa e
validata dal servizio e la conferma dell'utente.

## File e registri

La vista è in `prototype/prompting/minimal.py`; i messaggi in
`prototype/prompting/rendering.py`. Il contratto esterno è
`schemas/llm_recommendation_v3.schema.json`.
Lo stesso schema usato nelle istruzioni vincola la generazione.

Ogni tentativo conserva `prompt.json` completo, `encoding.json` con
revisione e corrispondenze, richiesta effettiva e risposta originale.
La raccomandazione validata conserva sia gli alias sia gli ID originali risolti.
Dalla revisione `minimal-v3-repair1-20260918`, gli errori rimandati al modello
sono frasi brevi in `previous_validation_errors`, senza codici lunghi o copie
della risposta precedente. Ogni tipo di errore compare una sola volta:

- Dispositivo non ammesso: scegliere `selected_device` dagli ID di `compatible_hardware`.
- Configurazione non ammessa: scegliere `config_id` da `configuration_catalog`,
  rispettando i vincoli del dispositivo.
- Evidence non valida: usare gli ID di `retrieved_labeled_examples`, senza
  duplicati e con almeno un riferimento. Senza esempi storici usare `[]`.

Una sola frase finale chiede di restituire l'intero JSON per il circuito corrente.
Gli altri errori di formato ricevono un richiamo allo schema.
Il programma reinvia il contesto ridotto completo, con gli stessi esempi e alias;
il primo tentativo resta identico. Nei registri canonici rimangono i codici
e i dettagli originali. Nessun valore arbitrario della risposta errata viene
reinserito nel prompt.
Le prove avviate con una revisione diversa non possono essere riprese con le
nuove correzioni, anche se il testo del primo tentativo è uguale.
Nuove istruzioni richiedono un nuovo nome della prova; gli esiti precedenti
non vengono sovrascritti.

Il formato v2 rimane leggibile con `compact.py`, `legacy_rendering.py`
e il validatore storico. Il parametro `legacy_contract=True` del costruttore
serve soltanto alla riproduzione esplicita delle prove precedenti.
Il percorso ordinario usa v3. Non è richiesta la ricostruzione del documento
canonico a partire dalla vista ridotta.

## Misure del 18 settembre

Sono stati confrontati tre casi train, senza inferenza:

| Circuito | Token prima | Token dopo | Riduzione |
| --- | ---: | ---: | ---: |
| dj_indep_tket_2 | 34.318 | 11.667 | 66,00% |
| ae_indep_qiskit_60 | 75.193 | 11.382 | 84,86% |
| portfoliovqe_indep_qiskit_6 | 36.265 | 12.692 | 65,00% |

Conteggi ottenuti con `llama-tokenize.exe` b10930 e lo stesso GGUF Qwen Q8_0
del caso di riferimento. Il formato nativo è ripreso dalla richiesta
archiviata: un messaggio utente, nessuno strumento, ragionamento disattivato.
Per il primo caso è verificata l'uguaglianza dell'intera sequenza degli ID dei
token con quella prodotta dal server originale, non solo del numero.

Il primo riferimento è una richiesta effettivamente inviata in passato.
Gli altri due riferimenti sono ricostruiti con il formato v2.
Le richieste nuove sono preparate e contate, non inviate al modello.
Lo schema leggibile fa parte del testo contato; `json_schema` passato
separatamente a llama.cpp vincola la generazione e non aggiunge token al prompt.
I conteggi delle singole sezioni sono diagnostici e non necessariamente additivi.

Non sono misure di qualità, latenza o memoria. Alcuni esempi train includono
lo stesso circuito: queste prove non dimostrano generalizzazione.
Non sono stati avviati selezione sulla validation o accesso al test.

Dati, richieste e log sono in
`artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/prompt_minimal_v3/`.
Le procedure riproducibili sono `llm_selection/minimal_audit.py` e
`llm_selection/tokenize_files.ps1`: preparazione, conteggio locale e
conclusione del controllo sono passaggi separati. Usare sempre una nuova
cartella di destinazione.

La precedente centralizzazione del 16 settembre e la codifica reversibile
restano documentate nei loro artefatti storici. I loro risultati non sono
attribuiti a questa revisione.

Il recupero reale e la compatibilità dei vecchi prompt train sono stati
verificati per tutti e tre i casi. Risposte di esempio costruite dalle
etichette storiche superano il nuovo validatore; non sono nuove risposte LLM.
La suite completa ha superato 236 test. I log comprendono anche gli errori
iniziali, corretti prima della consegna.

# Prompt chiaro e compatto — 15 settembre 2026

Questa modifica prepara la prossima prova tecnica. Il circuito completo,
la metrica e tutti i cinque esempi RAG restano nel prompt. La struttura JSON
della risposta resta quella dello schema 2.0.0. Le regole del validatore non
sono state allentate.

## Che cosa è cambiato

Prima sono state chiarite le istruzioni sulle fonti. Gli identificativi creati
nella risposta sono distinti da quelli delle fonti. `evidence_ref_ids` deve
indicare un `reference_id` della risposta, non un `source_id`. Ogni riferimento
storico richiede anche `source_claim_id`; i parametri della configurazione
devono comprendere dispositivo e configurazione. La compatibilità corrente
usa una lista vuota di riferimenti: non è una misura storica.

Questi erano problemi della risposta manuale DJ: la scelta del dispositivo era
coerente con l'esempio, ma le citazioni collegavano gli oggetti sbagliati.
La grammatica JSON può garantire la forma ammessa, non la correttezza di questi
collegamenti. Il controllo semantico rimane necessario.

È stato corretto anche il salvataggio degli errori. Alcuni dettagli erano
dizionari immutabili che `dataclasses.asdict` non riusciva a copiare. Ora gli
errori reali arrivano al tentativo di correzione e vengono conservati insieme
alla risposta e ai tempi misurati.

Poi è stato accorciato il testo con una rappresentazione reversibile:

- gli identificativi lunghi delle fonti diventano sigle come `R1`, `C1`, `E1`;
- gli oggetti ripetuti compaiono una volta, nella raccolta `shared_values`;
- le serie di oggetti omogenei usano una sola intestazione di colonne;
- i grafi completi mantengono la precedente regola esatta sugli archi.

Nessun valore numerico viene arrotondato. Il QASM della richiesta resta
integrale, con gli stessi byte. Non vengono eliminati esempi, risultati delle
compilazioni, campi o configurazioni. Prima dell'invio il programma ricostruisce
l'intero oggetto originale e ne controlla l'uguaglianza.

La mappa fra sigle e identificativi lunghi resta in `encoding.json`. Il modello
scrive gli stessi campi di prima, usando le sigle ricevute per le fonti.
L'applicazione ripristina soltanto gli identificativi noti nei tre campi
`record_id`, `source_claim_id` e `source_id`. Non aggiunge campi mancanti,
non inventa citazioni e non cambia la scelta. La risposta originale rimane
sempre disponibile.

## Misure dei prompt

Il confronto usa le stesse istruzioni chiarite, prima e dopo la compattazione,
con il tokenizer ufficiale Qwen. Non comprende i pochi token del formato
nativo della chat. Non è quindi identico al conteggio del server della vecchia
prova, che per DJ era 80.612 token.

| Circuito train | Prima | Dopo | Riduzione |
| --- | ---: | ---: | ---: |
| ae_indep_qiskit_60 | 111.346 | 75.181 | 32,5% |
| dj_indep_tket_2 | 81.011 | 34.306 | 57,7% |
| portfoliovqe_indep_qiskit_6 | 84.304 | 36.253 | 57,0% |
| su2random_indep_qiskit_50 | 133.575 | 90.819 | 32,0% |
| su2random_indep_tket_50 | 134.099 | 91.504 | 31,8% |

Sono stati verificati **93 prompt su 93**: cinque train e 88 validation.
Tutti conservano cinque esempi. La mediana sui soli prompt validation è
36.630 token, con una riduzione mediana del 56,6%; l'intervallo è 33.899–91.635.
Questo controllo non esegue la validation, non consulta i suoi score e non
accede al test.

I circuiti grandi restano lunghi anche dopo la riduzione. Conservare tutto il
QASM pone un limite alla riduzione possibile. La reversibilità dimostra che
i dati sono rimasti; non dimostra da sola che un modello interpreti altrettanto
bene la nuova rappresentazione.

Dati riproducibili: [riepilogo JSON](reports/prompt_lossless_v2.json).
L'audit completo è sotto `$LLM_OUTPUT/prompt_audits/lossless-v2-check-01/`.

## Verifica dell'esempio train

Il recupero RAG è stato rieseguito per tutti i cinque casi train. In ogni caso
è presente lo stesso circuito, con la stessa metrica e distanza zero.
È al primo posto in quattro casi, compreso DJ; per
`portfoliovqe_indep_qiskit_6` è al secondo posto fra risultati a distanza zero.
Il controllo confronta anche l'impronta del sorgente: due circuiti diversi
possono avere distanza zero sulle caratteristiche.

Per DJ l'esempio indica `ibm_falcon_127` e `o2_default_default`;
`o3_default_default` è a pari merito per quel dispositivo.
Prima di una prova train, il programma blocca l'inferenza se l'esempio identico
non è stato recuperato a distanza zero. Non modifica l'ordine del RAG e non
inserisce una risposta aggiuntiva.

Dopo la generazione, `train_self_check` distingue:

- `matches_primary_label`: stessa coppia dell'etichetta principale;
- `matches_tied_optimum`: stessa coppia o configurazione a pari merito;
- `uses_self_record_for_both_claims`: risposta valida e citazioni dell'esempio
  identico sia per il dispositivo sia per la configurazione.

Le citazioni provano ciò che la risposta dichiara come fonte, non il processo
interno del modello. Il successo su un circuito presente nel Dataset RAG
verifica il funzionamento; non misura la generalizzazione ai circuiti nuovi.

## Esito reale Qwen sul solo DJ

La prova `qwen-prompt-v2-02` è conclusa. Sono state effettuate tre chiamate:
una risposta iniziale e due correzioni. **Zero risposte su tre sono completamente
valide.** Tutte e tre rispettano il JSON e lo schema; tutte scelgono
`ibm_falcon_127` con `o2_default_default`, la coppia dell'esempio identico.

Restano però errori nei collegamenti: una fonte sulla configurazione viene usata
per sostenere la scelta del dispositivo; un riferimento viene riutilizzato per
più affermazioni; compaiono affermazioni su configurazioni diverse da quella
scelta. Alcune avvertenze hanno citazioni mancanti o incompatibili.
Quindi `uses_self_record_for_both_claims` resta falso: non certifichiamo come
corretto l'uso delle fonti solo perché la coppia scelta è giusta.

| Tentativo | Token ingresso | Lettura prompt | Generazione | Token uscita | Esito |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 34.318 | 118,79 s | 22,98 s | 1.310 | Errore semantico |
| 2 | 34.787 | 93,13 s | 17,22 s | 984 | Errore semantico |
| 3 | 34.515 | 91,78 s | 23,37 s | 1.337 | Errore semantico |

La somma delle tre chiamate HTTP è 367,63 secondi, circa 6 minuti e 8 secondi.
Il tempo dell'episodio, esclusa la preparazione del contesto e l'avvio del server,
è 369,43 secondi. I prompt di correzione includono gli errori appena riscontrati;
i tempi del server indicano `cache_n=0` in tutte le chiamate.

Per confronto, il primo tentativo DJ di `qwen-prova-07` leggeva 80.612 token
in 1.378,92 secondi e generava 1.993 token in 452,35 secondi. Nella nuova prova
la prima lettura richiede circa 11,6 volte meno tempo. È un confronto osservato
tra due esecuzioni, non una stima causale del solo effetto della compattazione:
non è stata eseguita una replica del vecchio prompt nelle condizioni di oggi.
Il limite di uscita è diverso, ma nessuna delle tre risposte nuove lo raggiunge.

Il monitor registra un massimo di 7.461.003.264 byte di memoria GPU dedicata
(circa 6,95 GiB), 720.523.264 byte di memoria GPU condivisa, un minimo di
3.657.748.480 byte di RAM libera e un massimo hotspot di 104 °C.
Sono estremi campionati durante le chiamate, non massimi continui garantiti.
Il profilo usa già tutti i livelli sulla GPU; non è stata aumentata la VRAM
assegnata. Queste misure non dimostrano la causa unica della vecchia lentezza.
Il server è stato chiuso al termine.

I dati completi sono nel [resoconto JSON](reports/qwen_prompt_v2_dj.json).
Il testo originale è disponibile separatamente per
[tentativo 1](reports/qwen_prompt_v2_dj_responses/attempt_1.txt),
[tentativo 2](reports/qwen_prompt_v2_dj_responses/attempt_2.txt) e
[tentativo 3](reports/qwen_prompt_v2_dj_responses/attempt_3.txt).
Le sigle presenti in questi testi sono quelle effettivamente prodotte da Qwen.

Il resoconto e le copie testuali si rigenerano senza inferenza:

```bash
.venv/bin/python -m llm_selection.prompt_report \
  --audit lossless-v2-check-01 --technical-label qwen-prompt-v2-02 \
  --output llm_selection/reports/qwen_prompt_v2_dj.json
```

La nuova rappresentazione riduce i tempi e il programma ora gestisce gli errori,
ma il modello non ha ancora prodotto una risposta interamente valida.
Questo singolo circuito non giustifica né l'avvio della validation completa
né una conclusione sulla dimensione del modello. L'esperimento negativo è conservato.

## Usare il prompt in chat

Dal terminale Ubuntu, nella cartella del progetto:

```bash
cd /home/elio/Tesi-mqt-2.4-v2
LLM_OUTPUT="$PWD/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection"
.venv/bin/python -m llm_selection.chat
```

Quando il server è pronto, aprire `http://127.0.0.1:8089` nel browser Windows.
Aprire una nuova conversazione e incollare **tutto** questo file:

```text
$LLM_OUTPUT/prompt_audits/lossless-v2-check-01/train/dj_indep_tket_2/prompt_chat.txt
```

Il file contiene già circuito, metrica, cinque esempi e istruzioni. L'avvio
della chat da solo non applica automaticamente tutti i parametri e il vincolo
JSON dell'esperimento. Per confrontare i tempi occorre registrare le impostazioni,
disabilitare il ragionamento esteso e usare la stessa macchina. Esportare la chat
prima di chiuderla. Terminare il server con Ctrl+C nel suo terminale.

Per rigenerare i prompt e verificare il recupero, scegliere un nome nuovo:

```bash
.venv/bin/python -m llm_selection.prompt_audit \
  --label controllo-prompt-02 --verify-retrieval --all-splits
```

Il comando non chiama Qwen. Usa il tokenizer già presente nell'ambiente
separato degli artefatti; non modifica `uv.lock`.

## Ripetere la prova tecnica

Chiudere prima l'eventuale server della chat. Il comando seguente usa lo stesso
profilo hardware di `qwen-prova-07`, sul solo DJ. Il nome deve essere nuovo:

```bash
.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label qwen-prompt-v2-03 \
  --precision Q8_0 --context 147456 --cache-type q8_0 \
  --batch 512 --micro-batch 128 --gpu-layers all \
  --pause-hotspot 105 --resume-hotspot 100 \
  --maximum-hotspot 108 --maximum-edge 95 \
  --circuit dj_indep_tket_2 \
  --technical-timeout 3600 --technical-max-attempts 3
```

Queste soglie sono quelle della prova di riferimento registrata, non i valori
predefiniti della guida generale. Il comando conserva temperature, memoria,
pause, prompt, risposte, errori, token e tempi. Alla prima risposta valida termina;
le chiamate successive servono soltanto a correggere errori.

Alla ripresa del lavoro il 15 settembre, `configuration.py` conteneva già
`max_tokens=4096`. È stato conservato. La vecchia prova usava 2048:
il confronto dei tempi totali deve dichiarare anche questa differenza.
Il limite è un massimo, non una lunghezza obbligatoria. Lo schema della risposta
e il ragionamento disabilitato restano invariati.

Una nuova rappresentazione richiede un nuovo nome dell'esperimento.
Il programma rifiuta di riusare episodi conclusi con istruzioni diverse.

## Controlli del codice e conservazione

Sono passati 68 controlli automatici: 28 sulla selezione, otto sulla compattazione
e il ciclo di correzione, 21 sulle citazioni, 11 sulla validazione dell'uscita.
Si possono ripetere con:

```bash
PYTHONPATH=.:tests .venv/bin/python -m unittest \
  test_llm_selection test_compact_prompt test_claim_evidence_validation test_llm_output_validation
```

Le 98 impronte dei file della vecchia prova `qwen-prova-07` risultano invariate.
Errori di avvio, controlli falliti durante lo sviluppo e correzioni sono registrati
in `$LLM_OUTPUT/analyses/prompt_v2/`. Il primo avvio `qwen-prompt-v2-01`
è stato interrotto dal limite di attesa dello strumento prima dell'inferenza:
la verifica SHA-256 aveva prodotto un risultato valido. Il tentativo resta
conservato e la ripartenza usa un nome nuovo.

Per pubblicare codice e documentazione: [istruzioni GitHub](GITHUB.md).

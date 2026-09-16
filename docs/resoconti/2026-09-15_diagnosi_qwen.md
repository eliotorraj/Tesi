# Diagnosi delle prime risposte Qwen — 15 settembre 2026

Questo resoconto riguarda la prova `qwen-prova-07`, precedente al prompt compatto.
Conserva i problemi osservati e il piano di diagnosi formulato allora.
Il problema di registrazione `mappingproxy` e la compattazione sono stati poi
corretti: esiti e limiti sono nel [resoconto successivo](2026-09-15_prompt_compatto.md).
Le proposte in fondo non sono tutte prove già eseguite.

I file citati appartengono a:

```text
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/manual_examples/qwen-prova-07/
```

## Leggere ciò che Qwen ha già scritto

Nella cartella manual_examples/qwen-prova-07:

- ae_indep_qiskit_60.risposta.txt: testo originale, troncato al limite.
- dj_indep_tket_2.risposta.txt: testo originale completo.
- portfoliovqe_indep_qiskit_6.risposta.txt: testo originale completo.
- schema_checks.json: controllo indipendente dello schema sulle risposte originali.
- manifest.json: origine e impronte di prompt e testi esportati.

I testi sono copie esatte del campo content. Non sono stati corretti o completati.

## Limite della risposta e generazione vincolata

I 2.048 token sono un limite massimo per chiamata, non una lunghezza obbligatoria.
Non provengono da un calcolo sperimentale documentato: configurazione e protocollo
li indicano come soglia iniziale da verificare. Nella prova ae si sono rivelati
insufficienti. dj si è fermato naturalmente a 1.993 e portfoliovqe a 1.856.

La generazione vincolata ERA attiva: tutte le richieste hanno json_schema.
Le tre risposte con evento finale registrano una grammatica di 6.640 caratteri.
Un validatore JSON Schema indipendente conferma:

| Caso | JSON leggibile | Schema rispettato | Regole semantiche rispettate |
|---|---|---|---|
| ae | No, troncato | No, documento incompleto | Non valutabili pienamente |
| dj | Sì | Sì | No |
| portfoliovqe | Sì | Sì | No |
| Due su2random | Nessun testo | Non valutabile | Non valutabile |

La grammatica limita ciò che il modello può emettere. Non garantisce che una
risposta interrotta sia completa, né che tutti i vincoli JSON Schema siano supportati.
Non garantisce riferimenti reali, collegamenti corretti tra record e affermazioni
o scelta scientificamente migliore. Uno schema può essere reso più restrittivo,
per esempio con identificativi ammessi e costanti per la richiesta, ma le relazioni
tra evidenze vanno ancora controllate.

Nel caso dj i reference_id dichiarati iniziano con claim_, mentre le affermazioni
citano evidence_ non dichiarati tra quei reference_id. Entrambe sono stringhe
accettate dallo schema, ma il collegamento è errato. Manca anche il claim sorgente
richiesto dalle regole semantiche per i risultati storici.
Il difetto mappingproxy nasconde questi errori e impedisce i tentativi di correzione.

## Piano per capire la causa, prima di cambiare modello

Queste sono prove proposte, non eseguite. Correggere prima la registrazione degli
errori e verificarla sulle risposte conservate, senza nuove chiamate.
Le prove devono restare sul train e separate dalla validation.

| Prova | Che cosa tenere uguale o cambiare | Come interpretare |
|---|---|---|
| Schema e copia su casi brevi | Stesso 4B, grammatica attiva, 10–20 casi sintetici con risposta verificabile e pochi record | Errori già qui indicano istruzioni, schema o gestione dei riferimenti; verificare prima l'infrastruttura |
| Limite della risposta | Stessi prompt e modello; confrontare 2.048 e 4.096, ulteriori aumenti solo se ancora troncato | Se sparisce finish_reason=limit ma restano riferimenti sbagliati, il limite spiegava il taglio, non gli errori semantici |
| Lunghezza del contesto | Stessi fatti rilevanti e compito verificabile; aggiungere distrattori controllati, per esempio 4k/16k/64k/128k token contati con tokenizer | Successo breve e fallimento lungo indicano difficoltà nel contesto lungo; contesto capiente non implica uso affidabile di tutto il testo |
| Rappresentazione | Stesso circuito e stesse evidenze; eliminare duplicazioni in modo reversibile o usare alias con corrispondenza conservata | Miglioramento del 4B indica un problema almeno in parte di rappresentazione; dichiarare che il prompt è cambiato |
| Dimensione | Stessa famiglia, versione di addestramento per quanto possibile, precisione, prompt, schema, modalità di ragionamento e budget; 4B contro taglia maggiore | Vantaggio ripetuto sui medesimi casi senza timeout è evidenza a favore della maggiore capacità, non prova che conti soltanto il numero di parametri |

Usare prima i cinque casi esistenti per correggere il sistema. Per il confronto di
capacità, scegliere prima dei risultati un piccolo insieme train più ampio, per
esempio 20 circuiti con dimensioni diverse. Applicare le stesse condizioni a tutti.
Con campionamento stocastico usare gli stessi seed in più repliche.
Temperatura 0 non richiede ripetere identiche chiamate salvo verifica della ripetibilità.

Per ogni prova conservare: modello/revisione/precisione, prompt e schema, seed e
parametri, token di ingresso/uscita, finish_reason, tempi separati, riuso cache,
memoria, risposta completa, errori di sintassi/schema/semantica e correzioni.
Confrontare il successo su tutti i casi e la semantica anche tra sole risposte complete.
Un timeout non dimostra scarsa capacità di ragionamento.

Distinguere i quattro criteri: fine della risposta, JSON valido, schema valido,
contenuto coerente. La qualità del dispositivo scelto è un ulteriore criterio:
questa diagnosi non usa gli score di validation/test.

Per calibrare il limite di uscita misurare risposte conformi complete sul train
con un limite esplorativo sufficiente, poi fissare una soglia con margine documentato.
Le risposte troncate sono misure incomplete della lunghezza necessaria, non massimi
osservati. Il criterio va fissato prima della validation e separato per tokenizer,
mantenendo un confronto equo tra famiglie.

Fonti ufficiali consultate:
[server b10930](https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md)
e [grammatiche e limiti del supporto JSON Schema](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md).


## Richiesta nativa storica (spostata dalla guida chat il 16 settembre)

Questa procedura conserva il formato precedente e non passa dal costruttore
comune dei prompt. È materiale di diagnosi storica.

## Ripetere una richiesta con lo schema realmente applicato

È disponibile anche dj_indep_tket_2.request_original.json: richiesta nativa originale,
con json_schema, prompt già formattato e n_predict=2048.
dj_indep_tket_2.schema.json contiene lo schema da solo.

Dopo l'avvio del server, il seguente comando Ubuntu effettua UNA nuova inferenza
e registra richiesta, flusso, risposta e tempi in una cartella distinta.
Non si deve incollare request_original.json nella chat.
Questo esempio modifica esplicitamente il limite a 4.096 e il timeout a 5.400 s;
è una nuova prova tecnica, non una riproduzione con parametri identici.

```bash
cd /home/elio/Tesi-mqt-2.4-v2
.venv/bin/python - <<'PY'
from datetime import datetime, timezone
from llm_selection.common import OUTPUT, read_json, write_json
from llm_selection.gateway import generate
label = datetime.now(timezone.utc).strftime("qwen-manuale-%Y%m%d-%H%M%S")
directory = OUTPUT / "manual_calls" / label
directory.mkdir(parents=True, exist_ok=False)
request = read_json(OUTPUT / "manual_examples/qwen-prova-07/dj_indep_tket_2.request_original.json")
request["n_predict"] = 4096
write_json(directory / "experiment.json", {
    "phase": "train_manual_diagnostic", "circuit": "dj_indep_tket_2",
    "original_run": "qwen-prova-07", "output_limit": 4096,
    "timeout_seconds": 5400,
    "note": "Server started separately: record the manual_chats session name and settings."
})
result = generate(request, directory / "call", timeout=5400)
(directory / "risposta.txt").write_text(result["content"], encoding="utf-8")
print(result["content"])
print("Fine:", result["finish_reason"], "secondi:", result["elapsed_seconds"])
print("File:", directory)
PY
```

La chiamata seguente usa direttamente il collegamento al server.
Non convalida semanticamente la risposta e non la trasforma in una decisione ufficiale.
Per una misura confrontabile partire da un server senza precedenti conversazioni
o registrare il riuso del prefisso tramite timings.cache_n.


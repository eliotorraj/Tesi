# Chat manuale con Qwen, Phi o Gemma

Questa guida spiega l'avvio di uno dei tre modelli locali e la conservazione
delle prove manuali sul train. La chat non avvia la validation.
Il riferimento scientifico resta il [protocollo](../protocollo_sperimentale.md).

## Scegliere il modello

Da Ubuntu, nella radice del progetto, usare **uno** di questi comandi:

```bash
.venv/bin/python -m llm_selection.chat --model qwen
.venv/bin/python -m llm_selection.chat --model phi
.venv/bin/python -m llm_selection.chat --model gemma
```

Senza `--model` continua ad avviarsi Qwen.
Il comando verifica i pesi e avvia il server. Quando compare il messaggio di
pronto, aprire [la chat locale](http://127.0.0.1:8089) nel browser Windows.

Il terminale deve restare aperto. Ctrl+C chiude il server posseduto da quella
sessione; chiudere la sola pagina non spegne il server.
Una sessione già presente non viene sostituita automaticamente.

Per controllare soltanto file e profilo, senza avviare il modello:

```bash
.venv/bin/python -m llm_selection.chat --model phi --check
```

`--check` non legge tutti i pesi per ricalcolarne l'impronta, non invia richieste
al server e non dimostra che il profilo sia sostenibile. L'impronta viene
verificata al vero avvio.

## Profili iniziali

| Modello | Pesi | Contesto | Cache |
| --- | --- | ---: | --- |
| Qwen3.5-4B | Q8_0 | 147.456 | q8_0 |
| Phi-4-mini-instruct | Q8_0 | 114.688 | q4_0 |
| Gemma 4 E4B-it | Q8_0 | 131.072 | q4_0 |

Sono profili per cominciare le prove manuali, non configurazioni finali
selezionate sulla validation. Il profilo Qwen conserva i valori dell'avvio
precedente, senza dipendere dal suo file di registro.
Le soglie del monitor restano quelle comuni definite in `hardware.py`.

È possibile scegliere precisione dei pesi, contesto e cache:

```bash
.venv/bin/python -m llm_selection.chat --model phi \
  --precision Q8_0 --context 32768 --cache-type q4_0
```

I pesi della precisione richiesta devono già essere presenti. Il programma
rifiuta contesti non positivi o superiori al limite nativo dichiarato per
quel modello. Tutti i livelli sono assegnati alla GPU con i parametri di
lotto già comuni al progetto.

## Usare il prompt ridotto dell'esperimento

La prova tecnica automatica prepara e invia direttamente il prompt compatto.
Nella chat manuale aprire invece un file `prompt_chat.txt`, selezionare tutto
e incollarlo in una nuova conversazione. Un esempio già conservato è:

```text
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/prompt_audits/lossless-v2-check-01/train/dj_indep_tket_2/prompt_chat.txt
```

Contiene circuito DJ, metrica, cinque esempi RAG e istruzioni.
L'esportatore `llm_selection.prompt_audit` usa la
[compattazione comune](compattazione_prompt.md). I conteggi del vecchio audit
sono riferiti al tokenizer Qwen; non sono conteggi misurati per Phi o Gemma.

Il browser applica il formato e le impostazioni della propria chat.
Incollare uno schema nel testo non attiva automaticamente la generazione
vincolata o il validatore semantico dell'esperimento. Per confronti tecnici
registrare temperatura, ragionamento e limite di uscita effettivamente usati.

## Conservare la prova

Il nome predefinito contiene modello, data e ora UTC. Per indicarne uno nuovo
usare, per esempio, `--label phi-chat-personale-01`.

Gli artefatti sono sotto `llm_selection/manual_chats/NOME/` nella cartella
dell'esperimento. `request.json` registra modello, profilo e versione dei
valori predefiniti; provenienza, eventi e misure delle risorse vengono
conservati come nelle precedenti chat.

Il programma di avvio non intercetta automaticamente la conversazione nel
browser. Esportare messaggi e impostazioni nella cartella della sessione.
Non aprire contemporaneamente la chat e una prova automatica sullo stesso server.

## Prove precedenti

Il [resoconto del prompt compatto](../resoconti/2026-09-15_prompt_compatto.md)
contiene misure, errori e risposte Qwen già ottenute. La
[diagnosi precedente](../resoconti/2026-09-15_diagnosi_qwen.md) conserva il
percorso di analisi delle prime risposte.

La selezione del modello in questa guida viene controllata con avvii simulati.
Il caricamento reale dei tre modelli resta una prova distinta dai controlli
del programma.

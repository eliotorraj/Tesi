# Selezione del modello linguistico locale

> **Seconda validation, 19 settembre 2026:** la nuova procedura con fatti strutturati, temperature 0/0,4/0,7 e recupero delle interruzioni è descritta nella [guida v2](v2/README.md). I comandi sotto documentano la procedura storica v1.

Questa cartella prepara il confronto fra Qwen, Phi e Gemma. Serve a scegliere
quale modello locale e quali impostazioni usare per proporre un dispositivo
quantistico e una configurazione Qiskit, aiutandosi con esempi del Dataset RAG.

Il modello riceve tutte le caratteristiche numeriche del circuito, la metrica,
le alternative ammesse e cinque esempi recuperati dal train. I dati sono
codificati in TOON; lo schema e la risposta restano JSON.
Il programma controlla il formato, le scelte ammesse e i riferimenti E1...E5.
Questi controlli non certificano la verità della motivazione libera.

La codifica corrente è `minimal-v3-toon1-20260919`. Per installarla su un nuovo
ambiente usare `.venv/bin/python -m llm_selection.setup_toon`.
Misure, istruzioni e comandi per le prove train sono nel
[resoconto TOON](../docs/resoconti/2026-09-19_prompt_toon.md).

## Come si inserisce nel progetto

1. Si preparano gli input usando il [prototipo](../prototype/README.md) e il Dataset.
2. Si fanno prove tecniche su circuiti train, per controllare tempi, memoria e risposte.
3. Si fissano modelli, prompt e parametri prima di consultare gli score di validation.
4. Si confrontano le alternative sulla validation e si registra la scelta locale.
5. Si generano tabelle, figure e testo LaTeX a partire dai risultati conservati.

La valutazione finale sul test è una fase successiva del [protocollo](../docs/protocollo_sperimentale.md).
Lo [stato aggiornato del progetto](../README.md) indica le fasi effettivamente concluse.
I controlli sui prompt e le prove train non dimostrano la qualità sui circuiti nuovi.
Gli esiti recenti sono nel [resoconto del prompt compatto](../docs/resoconti/2026-09-15_prompt_compatto.md).

## Orientarsi e mostrare ciò che esiste

Dal terminale Ubuntu, nella cartella principale del progetto:

```bash
.venv/bin/python -m llm_selection.cli doctor
.venv/bin/python -m llm_selection.cli status
.venv/bin/python -m llm_selection.cli technical-summary
```

Questi comandi leggono la preparazione e i registri; non caricano i modelli.
`doctor` controlla la presenza dei componenti, non la qualità delle risposte.
Per una demo si possono aprire anche i [resoconti e i testi già prodotti](reports/README.md).

I comandi di esecuzione, pausa, ripresa e produzione della relazione sono nella
[guida operativa](../docs/approfondimenti/selezione_llm.md).
La [guida alla chat locale](../docs/approfondimenti/chat_locale.md) riguarda le prove manuali.

La prova tecnica usa automaticamente il [prompt compatto comune](../docs/approfondimenti/compattazione_prompt.md),
anche per le richieste di correzione.

## Che cosa contiene ogni file

### Avvio e conduzione delle prove

| File | A cosa serve |
| --- | --- |
| `__init__.py` | Identifica questa cartella come modulo Python. |
| `cli.py` | Offre i comandi di controllo, riepilogo, pausa e analisi. |
| `controller.py` | Conduce le prove in sequenza, avviando un solo modello alla volta. |
| `run.py` | Esegue i singoli casi e conserva risposte, correzioni e decisioni. |
| `configuration.py` | Definisce le varianti del prompt e i parametri comuni della generazione. |
| `prepare.py` | Prepara inventario e prompt train/validation senza leggere gli score di validation. |
| `study.py` | Fissa le condizioni prima della selezione e sigilla le decisioni raccolte. |
| `evaluate.py` | Confronta le decisioni sigillate usando la matrice Qiskit già calcolata. |
| `finalize.py` | Registra la configurazione locale scelta, senza aprire il test. |
| `technical.py` | Riassume le prove train, compresi errori e arresti. |
| `chat.py` | Avvia Qwen, Phi o Gemma come chat manuale, con `--model`, separata dalla selezione. |

### Preparazione e controllo dei messaggi

| File | A cosa serve |
| --- | --- |
| `output_contract.py` | Mantiene compatibili i vecchi import delle regole, ora condivise in `prototype/prompting/`. |
| `compact_prompt.py` | Rimanda alla codifica condivisa in `prototype/prompting/`, mantenendo gli import precedenti. |
| `complete_graph.py` | Offre la prova esplorativa sui grafi e riusa la codifica comune. |
| `wire.py` | Mantiene compatibili i vecchi import della codifica tabellare comune. |
| `tokenization.py` | Usa un ambiente separato per contare i token dei diversi modelli. |
| `token_counts.py` | Conta in anticipo i token dei prompt preparati. |
| `inspect_tokenization.py` | Approfondisce il conteggio su un prompt tecnico train. |
| `probe_wire.py` | Misura una rappresentazione candidata sui prompt tecnici, senza inferenza. |
| `prompt_audit.py` | Esporta e verifica prompt, conservazione dei dati e recupero degli esempi. |
| `train_check.py` | Controlla il recupero del circuito train identico e le fonti citate nella risposta. |
| `prompt_report.py` | Ricava un resoconto dei prompt e di una prova train dai registri esistenti. |

### Collegamento al modello e conservazione

| File | A cosa serve |
| --- | --- |
| `acquire.py` | Scarica i pesi riprendendo trasferimenti interrotti e verificando provenienza e impronte. |
| `weights.py` | Verifica i pesi sul disco Windows prima dell'uso. |
| `gateway.py` | Invia richieste fra WSL e il server Windows, conservando gli scambi originali. |
| `hardware.py` | Definisce i limiti operativi e traduce il profilo in parametri del server. |
| `common.py` | Centralizza percorsi e scritture dei registri. |
| `storage.py` | Mantiene i registri Windows su D: e i loro collegamenti nel progetto. |
| `provenance.py` | Registra versioni, ambiente e copie del codice usato. |
| `recovery.py` | Esamina scritture interrotte senza eliminare i file originali. |
| `server_state.py` | Verifica lo stato del processo senza inventare informazioni sull'arresto. |
| `runtime_check.py` | Elenca i componenti dell'ambiente separato senza caricare modelli. |
| `smoke_transport.py` | Esegue una piccola prova sintetica del collegamento, distinta dalla selezione. |

### Report a partire dai dati

| File | A cosa serve |
| --- | --- |
| `report.py` | Genera tabelle, sorgenti LaTeX e relazione dai dati della selezione. |
| `plots.py` | Disegna i grafici nell'ambiente separato delle analisi. |
| `render_pdf.py` | Converte tutte le pagine del PDF in immagini da controllare. |
| `setup_report.py` | Installa gli strumenti separati necessari per grafici e LaTeX. |

### Programmi di supporto Windows

| File | A cosa serve |
| --- | --- |
| `serve.ps1` | Avvia il server locale e registra memoria, temperature, pause e arresti. |
| `stop.ps1` | Arresta il server identificato dai registri della specifica esecuzione. |
| `inspect_server.ps1` | Controlla che il processo registrato sia ancora quello in esecuzione. |
| `gpu_monitor.ps1` | Campiona l'uso della memoria GPU del server. |
| `AmdSensors.cs` | Legge i sensori della scheda AMD senza cambiarne le impostazioni. |
| `verify_weights.ps1` | Calcola e confronta l'impronta del file dei pesi in Windows. |
| `probe_storage.ps1` | Misura la scrittura dei registri su un percorso Windows. |
| `launch_technical.ps1` | Avvia da Windows una prova train in WSL e ne conserva l'uscita. |

## Dove sono i risultati

[`reports/`](reports/README.md) contiene piccoli riepiloghi pubblicabili e copie delle risposte.
I registri completi, i pesi e le singole esecuzioni sono negli
[artefatti dell'esperimento](../artifacts/README.md), sotto `llm_selection/`.
Non sono file sorgenti di questa cartella.

La cronologia delle diagnosi è in [docs/resoconti/](../docs/resoconti/README.md).
I dettagli per usare la procedura sono in [docs/approfondimenti/](../docs/approfondimenti/README.md).

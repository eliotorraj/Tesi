# Registri delle prove LLM

[Indice dell’esperimento](../README.md) ·
[Programmi e comandi](../../../../llm_selection/README.md)

Qui si conserva la traccia completa delle prove dei modelli locali.
Il codice operativo è nella cartella `llm_selection/` alla radice del progetto.
Questa cartella contiene dati prodotti da quel codice.

## Mappa dei gruppi

| Cartella o file | A cosa serve |
| --- | --- |
| `models/<modello>/` | Pesi GGUF, impronte, verifiche, informazioni di provenienza e documentazione originale del modello. |
| `preparation/` | Inventario iniziale, caratteristiche della macchina, informazioni sulle versioni, conteggi preliminari dei token e copia del protocollo precedente all’emendamento. |
| `runtime/` | Esecutore llama.cpp e ambiente ausiliario. Le librerie e la loro documentazione appartengono ai fornitori. |
| `prompts/train/`, `prompts/validation/` | Richieste preparate e dati che consentono di ricostruirle. Un prompt preparato non dimostra che una valutazione sia stata svolta. |
| `technical/` | Prove di avvio e sostenibilità: comando, output, memoria, uscita ed eventuale richiesta di arresto. |
| `technical_episodes/<prova>/` | Tentativi automatici sui circuiti train, comprese risposte non valide e interruzioni. |
| `technical_transport/` | Prove sullo scambio di richieste e risposte con il server. |
| `controllers/<prova>/` | Richiesta di esecuzione, eventi, verifiche dei pesi e conclusione del controllore. |
| `servers/<avvio>/` | Comando del server, output e misure delle risorse durante la sua attività. |
| `background/` | Tracce delle esecuzioni avviate in secondo piano. |
| `code_snapshots/` | Copie del codice utilizzato da una prova, per ricostruirla dopo modifiche successive. |
| `prompt_audits/` | Verifiche del contenuto effettivo delle richieste e della rappresentazione compatta. |
| `proposals/` | Proposte esplorate, confronti dei token e controlli associati, incluse alternative scartate. |
| `manual_chats/` | Richieste, provenienza ed eventi delle chat tecniche manuali. |
| `manual_examples/` | Esempi e risposte esportati per un’ispezione manuale. |
| `analyses/` | Resoconti e materiali usati per capire risultati, errori e modifiche delle prove tecniche. |
| `incidents/` | Diagnosi di arresti inattesi e problemi di memoria o registrazione. |
| `storage_checks/` | Controlli dello spazio e della collocazione dei file. |
| `controller.lock`, `execution.lock` | Blocchi di coordinamento tra programmi; la sola presenza non dimostra che un processo sia ancora attivo. |

I pesi possono risiedere sul disco D: ed essere raggiunti dal progetto.
I file `*_manifest.json` e `*_verified.json` ne registrano identità e verifica.
File `*.corrupt-*`, `*.part.*`, `*.transfer.json` e
`*.download_events.jsonl` conservano anche errori e interruzioni del trasferimento.

## Come leggere una prova automatica

Dentro `technical_episodes/<prova>/<modello>/<configurazione>/<circuito>/`:

| Gruppo | Significato |
| --- | --- |
| `begin.json` | Inizio dell’elaborazione del circuito. |
| `attempt_<n>/started.json`, `prompt.json`, `encoding.json` | Inizio della chiamata, richiesta effettiva e sua codifica. |
| `attempt_<n>/audit/` | Applicazione del formato di chat e conteggio dei token. |
| `attempt_<n>/call/` | Richiesta, risposta, flusso generato e messaggi di errore. |
| `attempt_<n>/summary.json` | Esito e misure del singolo tentativo, inclusi i controlli sulla risposta. |
| `decision.json` | Esito terminale del circuito e numero di chiamate/correzioni. |
| `provenance.json`, `invocations/*/provenance.json` ai livelli superiori | Identità del codice, dei pesi e delle condizioni di esecuzione. |

Un `finished.json` del controllore indica che il programma ha finito:
i singoli circuiti possono comunque essere falliti.
Il numero di `decision.json` non conta tutti gli avvii o le chiamate fisiche,
perché esistono anche tentativi interrotti prima della decisione finale.

## Resoconti tecnici da cui partire

- [qwen-prova-07](analyses/qwen-prova-07/resoconto.md): cinque circuiti train,
  richieste molto lunghe, errori e timeout della prova del 14 settembre.
- [Chat manuale sul circuito DJ](analyses/manual_dj_2026-09-14/resoconto.md):
  analisi della risposta e dei collegamenti alle fonti.
- [Proposta di riduzione del prompt](proposals/2026-09-14_prompt_reduction/proposta.md):
  motivazione e controlli della rappresentazione compatta.
- `analyses/prompt_v2/`: verifiche del codice e delle risposte dopo quella modifica.
  Gli script conservati qui sono strumenti della singola analisi, non comandi
  ordinari per avviare la selezione.

## Stato e interpretazione delle prove

Il [README principale](../../../../README.md) riporta la fase attuale.
Il [resoconto della ricognizione](../../../../docs/resoconti/2026-09-16_ricognizione_documentazione.md)
conserva i conteggi osservati. Le prove tecniche sul train non rappresentano
la selezione sulla validation e non certificano un modello finale.

# Provare il prototipo, passo per passo

Questa guida porta da una copia della repository a una raccomandazione e a un circuito compilato. Non richiede di aprire `archivio/`, addestrare MQT Predictor o eseguire il Test. I comandi di questa prima prova usano Windows e il profilo CPU.

## 1. Preparare cartella e programmi

Scaricare o clonare la repository. Aprire PowerShell nella cartella `prototipo/` su un disco Windows locale, per esempio `C:\progetti\Tesi\prototipo`. Sono necessari **Python 3.12**, con il comando `py`, e **Node.js 22 con npm**, disponibili nel PATH.

```powershell
cd C:\progetti\Tesi\prototipo
py -3.12 --version
node --version
npm.cmd --version
.\setup.ps1 -RuntimeProfile cpu -DownloadRuntime
```

La preparazione crea `.venv/`, installa le dipendenze Python fissate, installa il codec TOON dal lock npm, prepara llama.cpp b10930 per CPU e costruisce l'indice RAG dai dati train inclusi. Se il runtime è già presente, si può omettere `-DownloadRuntime`. Non vengono scaricati i pesi del modello.

Se la politica PowerShell della sessione blocca gli script locali, usare:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -RuntimeProfile cpu -DownloadRuntime
```

Non serve modificare la politica globale del computer.

## 2. Fornire i pesi del modello

Usare il GGUF **Qwen3.5-4B-Q8_0.gguf**, dalla [revisione fissata](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/e87f176479d0855a907a41277aca2f8ee7a09523). Se è già disponibile, copiarlo; altrimenti procurarsi quel file della revisione indicata. Si può conservarlo, per esempio, in `C:\modelli\`.

Il file atteso misura **4.482.403.488 byte** e ha SHA-256:

```text
10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1
```

Il percorso è un parametro. Non rinominare o modificare i sigilli per usare pesi diversi. `verify-model.ps1` e gli avviatori confrontano dimensione e impronta con `config.json`.

## 3. Verificare la preparazione

```powershell
.\.venv\Scripts\python.exe app.py check
```

Il risultato `status: ready` conferma versioni Python, dati train, catalogo hardware e funzionamento del codec TOON. Il comando non interroga il server, non misura la qualità del modello e non esegue la batteria di sviluppo.

`app.py prepare` crea l'indice RAG se manca e controlla quello esistente, senza ripetere l'installazione. Se l'indice è incompatibile, si ferma: non lo ricostruisce in silenzio.

## 4. Avviare il server

Nella prima finestra PowerShell:

```powershell
.\server-laptop.ps1 -ModelPath C:\modelli\Qwen3.5-4B-Q8_0.gguf
```

Lasciare aperta la finestra. La verifica dell'impronta legge l'intero file dei pesi e può richiedere tempo. Il profilo CPU usa un contesto di 16.384 token e richiede almeno 9 GiB di memoria libera prima dell'avvio; GPU integrata e NPU non vengono utilizzate.

In una seconda finestra PowerShell controllare il server:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8089/health -TimeoutSec 5
```

Attendere `status: ok`. Una risposta di caricamento non indica che il modello sia pronto.

## 5. Eseguire il circuito incluso

Sempre nella seconda finestra, dalla cartella `prototipo/`:

```powershell
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27 --compile
```

Il vincolo `--device` limita esplicitamente i candidati a Falcon 27, così la prima richiesta è più piccola. Il programma recupera cinque esempi, chiede a Qwen una scelta, la controlla e compila il Bell. Non esegue il circuito su hardware quantistico.

Per ricevere soltanto la raccomandazione, omettere `--compile`. Per usare un proprio circuito, sostituire `examples/bell.qasm` con il percorso di un file **OpenQASM 2**. `--device` può essere ripetuto per ammettere più dispositivi; senza questa opzione vengono valutati quelli compatibili. Richieste più grandi possono superare il contesto del profilo CPU.

## 6. Leggere il risultato

Il programma stampa dispositivo, identificativo della configurazione, parametri Qiskit e cartella creata in `runs/`. In quella cartella:

- `input.qasm` e `begin.json` conservano circuito e configurazione dell'esecuzione;
- `prompt.json`, `retrieval.json` ed `encoding.json` spiegano gli esempi e la preparazione dell'input;
- `attempt_*/` conserva richieste, risposte, token e controlli dei tentativi;
- `decision.json` contiene la scelta e lo stato delle verifiche;
- `compiled.qasm` e `compilation.json` sono presenti quando la compilazione richiesta riesce;
- `end.json` indica il completamento; `failure.json` conserva un errore.

`accepted_with_unverified_facts` significa che al terzo tentativo è stata accettata una coppia ammessa, ma alcuni fatti non sono verificati. L'ipotesi libera resta una proposta del modello. Il [documento tecnico](architettura_e_flusso.md) spiega queste condizioni e i controlli effettivi.

Per fermare il server premere Ctrl+C nella sua finestra. I registri del server sono separati da quelli del client e il loro percorso viene stampato all'avvio.

## Desktop e WSL/Linux

Sul desktop previsto dagli avviatori usare `setup.ps1 -RuntimeProfile desktop -DownloadRuntime` e `server-desktop.ps1 -ModelPath ...`; nel client scegliere `--profile desktop`. Il profilo usa Vulkan, contesto 60.000 e controlli termici AMD. I requisiti e i limiti sono nel [documento sul runtime](installazione_e_runtime.md).

Per il client Linux/WSL, con Python 3.12 e Node.js 22/npm già installati nella distribuzione Linux:

```bash
cd /percorso/della/repository/prototipo
bash setup.sh
.venv/bin/python app.py check
.venv/bin/python app.py run examples/bell.qasm --profile desktop --compile
```

`setup.sh` prepara il client; non avvia né installa un server llama.cpp Linux. In WSL si può usare il server Windows avviato separatamente: `curl.exe` deve essere raggiungibile dal PATH WSL. Un server su Linux nativo va predisposto a parte con le impostazioni del profilo. Il client accetta soltanto un indirizzo locale (`localhost` o `127.0.0.1`).

Non copiare `.venv/` o l'indice `runtime/rag/` fra sistemi operativi. Le prove sul portatile non equivalgono alle misure sperimentali del desktop.

## Oppure:

Aprite powershell come amministratore e avviate il tutto con questo comando:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Tesi-mqt\prototipo-native\server-desktop.ps1" -ModelPath "D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models\qwen\Q8_0.gguf"

Controllate lo stato in un altro terminale WSL con:
curl.exe --fail http://127.0.0.1:8089/health

## Problemi e approfondimenti

Se manca una dipendenza, rieseguire la preparazione nel sistema corrente. Se il controllo dei dati fallisce, ripristinare i file originali; non riscrivere i sigilli. Se il contesto è insufficiente, il programma non invia la generazione e non elimina esempi automaticamente. Se si interrompe il collegamento al modello, l'esecuzione termina conservando i registri.

Per gli esperimenti usare il [protocollo corrente](protocollo_sperimentale.md) e [archivio/valutazione/](../../archivio/valutazione/README.md). La batteria completa di sviluppo è separata dall'uso descritto qui.

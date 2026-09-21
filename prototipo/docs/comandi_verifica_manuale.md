# Comandi per le verifiche manuali

Verifica dei comandi: 21 settembre 2026. Sono riferiti al ramo
`riorganizzazione-prototipo` e al computer fisso attuale. Graphify e Qwen non
sono stati avviati per queste prove: l'esecuzione resta all'utente.
La revisione degli script è descritta nel
[rapporto del 21 settembre](../../archivio/riorganizzazione_2026_09_21/revisione_script/README.md).

## 1. Aggiornare Graphify — terminale Ubuntu/WSL

Eseguire dalla radice, non da `archivio/esperimento_v2`. Non aggiornare il
pacchetto: i comandi sono verificati sul codice locale di **graphifyy 0.9.63**.
La nuova `.graphifyignore` esclude runtime, dati generati e copie ripetute dei
sorgenti. Restano codice corrente, codice sperimentale, test e documenti.
Le esclusioni non cancellano alcun dato dal progetto.

```bash
cd /home/elio/Tesi-mqt-2.4-v2
export PATH="$HOME/.local/bin:$PATH"
git branch --show-current
```

Il ramo stampato deve essere `riorganizzazione-prototipo`. Poi salvare il grafo
precedente ed eseguire l'aggiornamento; ogni esecuzione produce un registro nuovo:

```bash
mkdir -p .workspace_archive
copia_grafo=".workspace_archive/graphify-prima-$(date +%Y%m%d-%H%M%S)"
set -o pipefail
cp -a graphify-out "$copia_grafo" &&
    graphify update . 2>&1 | tee "${copia_grafo}-aggiornamento.log"
```

Attendere il messaggio `Code graph updated`. Il primo passaggio può richiedere
tempo perché deve riconciliare il vecchio grafo con lo spostamento delle cartelle.
Non eseguire due aggiornamenti contemporaneamente. Non aggiungere `--force`
in caso di errore: conservare il registro per capire quale controllo è fallito.
Il comando è strutturale, senza richieste a modelli: aggiorna codice e struttura
dei documenti supportati, ma non rifà l'analisi semantica dei testi e degli articoli.
Quella richiede successivamente `/graphify --update` in una sessione dell'assistente.

Dopo il successo, rigenerare la vista e controllare una ricerca:

```bash
graphify export html
graphify query "Qwen facts retrieval compilation" --budget 1500
```

Il vecchio grafo ha 68.244 nodi; l'esportazione HTML può rappresentare le comunità
anziché tutti i singoli nodi. I riferimenti al codice corrente devono usare
`prototipo/` o `archivio/esperimento_v2/`. Non eliminare a mano `.needs_update`
per far apparire riuscito un aggiornamento che ha segnalato errori.

## 2. Avviare Qwen sul fisso — PowerShell Windows

La cartella nativa e i runtime sono già presenti su questo PC. Copiare le
versioni correnti degli avviatori dalla cartella WSL alla copia nativa. Queste
istruzioni non copiano indici, ambienti Python o registri delle prove.

```powershell
$Sorgente = "\\wsl.localhost\Ubuntu\home\elio\Tesi-mqt-2.4-v2\prototipo"
$Destinazione = "D:\Tesi-mqt\prototipo-native"
$Modello = "D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models\qwen\Q8_0.gguf"
New-Item -ItemType Directory -Path $Destinazione -Force | Out-Null
$FileAvvio = "server-desktop.ps1", "server-desktop-internal.ps1", "verify-model.ps1", "AmdSensors.cs", "config.json"
foreach ($Nome in $FileAvvio) {
    Copy-Item -LiteralPath (Join-Path $Sorgente $Nome) -Destination $Destinazione -Force
}
if (-not (Test-Path -LiteralPath $Modello)) { throw "Pesi Qwen non trovati" }
if (-not (Test-Path -LiteralPath (Join-Path $Destinazione "runtime\desktop\llama-server.exe"))) { throw "Runtime desktop non trovato" }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Destinazione\server-desktop.ps1" -ModelPath $Modello
```

Lasciare aperta questa finestra. Il controllo SHA256 legge circa 4,48 GB:
attendere il messaggio di verifica dei pesi. Poi il controllore inizializza i
sensori AMD e avvia il server Vulkan. Mantiene contesto 60.000, cache q8_0,
batch 512/128 e i controlli di temperatura della configurazione selezionata.
I registri sono sotto `%LOCALAPPDATA%\QwenPrototype\runs`, in una cartella nuova.
Non avviare un secondo server se il primo è ancora in esecuzione.

In una **seconda finestra PowerShell**, controllare che il caricamento sia finito:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8089/health" -TimeoutSec 5
```

Attendere `status: ok`. Un errore di connessione o una risposta di caricamento
non dimostrano che il modello sia pronto. Quando appare `ok`, passare al client.

## 3. Provare il percorso completo — terminale Ubuntu/WSL

Usare l'ambiente Python 3.12 già conservato nella radice del progetto:

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
../.venv/bin/python app.py prepare
../.venv/bin/python app.py run examples/bell.qasm --profile desktop --compile
```

Il primo comando verifica il train e prepara l'indice locale. Il secondo recupera
cinque esempi, chiede la configurazione a Qwen con temperatura 0, verifica la
risposta e compila il Bell con `seed_transpiler=0`. Questo circuito è una prova
tecnica, non un circuito del Test sperimentale.

Un risultato completo stampa `compiled: true`, dispositivo, configurazione e
percorso del registro sotto `prototipo/runs/`. `accepted_with_unverified_facts`
è un esito distinto da `success`: dopo tre tentativi può essere accettata una
coppia valida con fatti non verificati, come previsto dal contratto v4.
Per il primo circuito personale, sostituire `examples/bell.qasm` con il percorso
del proprio file OpenQASM 2. Non usare i circuiti riservati al Test.

WSL deve trovare `curl.exe` nel PATH: serve a raggiungere il server Windows su
localhost. Il Node 22 locale è già in `prototipo/runtime/node/bin/node`.
Non occorre eseguire `setup.ps1` o reinstallare l'ambiente per questa prova sul fisso.

## Se l'avvio non prosegue

Non disabilitare i controlli delle risorse. Conservare l'ultima riga stampata e
la cartella dei registri. Da una seconda finestra PowerShell:

```powershell
$Cartella = Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\QwenPrototype\runs" -Directory |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($Cartella) {
    $Cartella.FullName
    Get-ChildItem -LiteralPath $Cartella.FullName
    $ErroreServer = Join-Path $Cartella.FullName "stderr.log"
    if (Test-Path -LiteralPath $ErroreServer) { Get-Content -LiteralPath $ErroreServer -Tail 60 }
}
Get-Process -Name llama-server -ErrorAction SilentlyContinue |
    Select-Object Id, StartTime, CPU, WorkingSet64
```

Se non viene creata una cartella nuova, il blocco precede l'avvio: annotare
l'ultima riga stampata. I registri precedenti non descrivono quel nuovo tentativo.
Per interrompere usare Ctrl+C nella finestra del controllore e verificare
che il processo da esso avviato sia terminato. Evitare arresti indiscriminati
per nome se appartengono ad altre prove.

## Portatile Intel — prova separata

Sul portatile copiare `prototipo/`, i pesi GGUF e il runtime CPU. Preparare un
ambiente Windows nuovo, come nel README; non copiare `.venv`, `runtime/rag` o
`runs` dal fisso. Con Python 3.12 e Node 22 disponibili, da PowerShell:

```powershell
cd C:\percorso\prototipo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -RuntimeProfile cpu
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\server-laptop.ps1 -ModelPath "C:\modelli\Qwen3.5-4B-Q8_0.gguf"
```

Se manca il runtime, usare `-DownloadRuntime` soltanto nel comando `setup.ps1`.
In una seconda finestra, dopo `status: ok` dal controllo `/health`:

```powershell
cd C:\percorso\prototipo
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27 --compile
```

Il profilo CPU usa contesto 16.384 e richiede almeno 9 GiB liberi all'avvio.
GPU integrata e NPU non vengono usate. Il vincolo Falcon 27 è esplicito per
contenere la dimensione della richiesta. Questa prova non è equivalente alla
configurazione sperimentale desktop: memoria e tempi sul portatile vanno misurati.

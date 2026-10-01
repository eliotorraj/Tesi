# Provare il prototipo su Linux, passo per passo

Il prototipo legge un circuito OpenQASM 2, recupera esempi train, chiede a **Qwen3.5-4B Q8_0** una scelta e può compilarla con Qiskit. Non richiede di addestrare MQT o di rigenerare il Dataset. Il clone comprende gli esempi RAG; i pesi di Qwen si procurano separatamente.

Scegliere il percorso prima di iniziare:

- **Nuovo utente Linux senza GPU:** seguire il percorso A, dall'inizio alla fine. I comandi di installazione sono per Ubuntu 24.04 o Debian/Ubuntu compatibile; sulle altre distribuzioni cambiano i pacchetti di sistema.
- **Elio sul fisso con Radeon RX 6750 XT:** seguire il percorso B. Il client resta in Ubuntu/WSL; il server continua a usare gli avviatori PowerShell e la GPU Windows già predisposti.
- **Utente Linux con un'altra GPU:** preparare prima il client come nel percorso A, poi usare la variante GPU del [documento sul runtime](installazione_e_runtime.md#gpu-su-linux). Non usare gli script AMD del fisso come avviatori generici.

Una GPU compatibile è consigliata per far girare Qwen. La CPU permette di tentare una prima prova, ma l'elaborazione del prompt può essere molto lenta. **16 GB di RAM installata sono il minimo indicativo, non una garanzia:** servono almeno 9 GiB disponibili a Linux prima dell'avvio CPU e ulteriore margine durante la prova. In WSL conta la RAM assegnata alla distribuzione, non tutta quella del PC. Circuiti o richieste troppo grandi possono non essere eseguibili su questa macchina.

## Percorso A — Nuovo utente Linux, CPU

### A1. Aprire il terminale Linux e controllare le risorse

```bash
free -h
lscpu
```

In `free -h` guardare la colonna `available`. Chiudere applicazioni pesanti se non restano circa 9 GiB; lo swap non equivale a RAM disponibile. Prevedere spazio per il clone, le dipendenze, i sorgenti compilati di llama.cpp e circa 4,5 GB di pesi. Una riserva di 20 GB liberi è un'indicazione pratica, da aumentare se si conservano molte esecuzioni.

I comandi seguenti installano strumenti nel proprio account, salvo i pacchetti di sistema installati con `sudo`. Non eseguire il prototipo con `sudo`.

### A2. Installare i prerequisiti

```bash
sudo apt update
sudo apt install git curl ca-certificates build-essential cmake pkg-config libssl-dev libcurl4-openssl-dev
```

Servono Python 3.12 e Node.js 22 con npm. Se già disponibili, saltare le rispettive installazioni. Per Python usiamo [uv](https://docs.astral.sh/uv/getting-started/installation/), che può fornire Python senza sostituire quello del sistema:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12
uv --version
```

Per Node usiamo [nvm](https://github.com/nvm-sh/nvm#install--update-script). Il download esegue l'installatore ufficiale; se nvm è già presente, bastano caricamento e selezione di Node 22:

```bash
export NVM_DIR="$HOME/.nvm"
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
. "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
node --version
npm --version
```

`node --version` deve iniziare con `v22.`. Nei terminali successivi, se necessario, caricare di nuovo `nvm.sh` ed eseguire `nvm use 22`.

### A3. Clonare il ramo e preparare il client

Se il clone esiste già, entrarvi senza ripetere `git clone`. Per una nuova copia:

```bash
git clone --branch riproducibilita-esperimenti --single-branch \
  https://github.com/eliotorraj/Tesi.git "$HOME/Tesi-riproducibilita"
cd "$HOME/Tesi-riproducibilita/prototipo"
bash setup.sh
.venv/bin/python -B app.py check
```

Usare il proprio percorso se il clone ha un altro nome. **Da qui tutti i comandi del percorso A partono dalla cartella `prototipo/`.**

Il setup crea l'ambiente `.venv`, installa le versioni fissate, prepara il codec TOON e l'indice RAG. Non installa il server e non scarica i pesi. `status: ready` conferma il client, i dati e i Target; non conferma ancora l'inferenza. Non copiare un ambiente Python o un indice Qdrant da un altro PC.

### A4. Preparare llama.cpp per CPU

llama.cpp è il programma che carica Qwen. Si usa la revisione **b10930** e si compila sul PC corrente; così il percorso non dipende da un eseguibile Windows o da istruzioni CPU di un'altra macchina. I comandi seguono la [procedura ufficiale di compilazione](https://github.com/ggml-org/llama.cpp/blob/b10930/docs/build.md).

```bash
git clone --branch b10930 --depth 1 \
  https://github.com/ggml-org/llama.cpp.git runtime/llama.cpp
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-cpu \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF
cmake --build runtime/llama.cpp/build-cpu --config Release --target llama-server -j 2
runtime/llama.cpp/build-cpu/bin/llama-server --version
```

La compilazione può richiedere tempo. `-j 2` limita i processi del compilatore, non i thread usati dal modello. Se `runtime/llama.cpp` è già presente, saltare il clone e controllare la revisione con `git -C runtime/llama.cpp describe --tags --exact-match`. Non cancellare la cartella per aggirare un errore.

### A5. Procurarsi il GGUF esatto

Se i pesi sono già disponibili, usare il loro percorso nel comando di avvio. Altrimenti scaricarli dalla [revisione fissata](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/e87f176479d0855a907a41277aca2f8ee7a09523):

```bash
mkdir -p runtime/models
curl --fail --location --continue-at - \
  'https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q8_0.gguf' \
  --output runtime/models/Qwen3.5-4B-Q8_0.gguf
sha256sum runtime/models/Qwen3.5-4B-Q8_0.gguf
```

Il file deve misurare **4.482.403.488 byte** e avere SHA-256:

```text
10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1
```

`server.py` ricontrolla dimensione e impronta a ogni avvio. Una diversa quantizzazione non è intercambiabile con questi pesi: per scegliere un altro modello usare `riproducibilita/`, senza alterare i sigilli del prototipo.

### A6. Avviare Qwen nel primo terminale

```bash
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-cpu/bin/llama-server \
  --model runtime/models/Qwen3.5-4B-Q8_0.gguf \
  --profile cpu
```

Lasciare aperto il terminale. Il server usa la CPU, un contesto di 16.384 token, cache q8_0 e una richiesta alla volta. La GPU e la NPU non vengono attivate. Per scegliere meno thread aggiungere, per esempio, `--threads 4`.

L'avviatore stampa la cartella dei log sotto `runtime/server-runs/`. Se il server termina, leggere `stderr.log` ed `exit.json` in quella cartella. La verifica dei pesi e il caricamento richiedono tempo; l'assenza di testo nuovo nella finestra non implica un blocco.

### A7. Controllare il server e provare Bell nel secondo terminale

Aprire **un secondo terminale Linux**, rientrare nella cartella `prototipo/` e controllare:

```bash
cd "$HOME/Tesi-riproducibilita/prototipo"
curl --fail http://127.0.0.1:8089/health
```

Attendere `{"status":"ok"}`. Durante il caricamento può arrivare un errore HTTP 503; ripetere il controllo dopo qualche secondo. Poi:

```bash
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile cpu --transport native --timeout 3600 \
  --device ibm_falcon_27 --compile
```

Il circuito Bell è incluso nel clone. Il filtro Falcon 27 mantiene piccola la prima richiesta. Il limite di un'ora si applica a ogni chiamata HTTP: non è una stima della durata e fino a tre generazioni possono allungare la prova. Se la CPU è lenta, osservare i log prima di rilanciare il comando; ogni rilancio è una nuova esecuzione.

`--transport native` usa HTTP Linux anche in WSL. L'opzione `--device` del client sceglie un **dispositivo quantistico sintetico**, non la GPU del PC. Senza `--compile` si ottiene soltanto la raccomandazione. Per il proprio circuito sostituire `examples/bell.qasm` con un file OpenQASM 2; rimuovere o ripetere il filtro solo dopo la prima prova.

## Percorso B — Elio, fisso con GPU e client WSL

Questo percorso mantiene il server Windows Vulkan e i controlli AMD dei file `.ps1`. La GPU rilevata sul fisso è **AMD Radeon RX 6750 XT**. Gli script e `AmdSensors.cs` restano disponibili. Il client della repository continua a girare in Linux/WSL.

### B1. Preparare o controllare il client in Ubuntu/WSL

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
bash setup.sh
.venv/bin/python -B app.py check
```

Servono gli stessi Python 3.12 e Node 22 del percorso A. Se sono già installati non reinstallarli. Questo setup riguarda il client del clone corrente; non ricrea il server Windows già configurato.

### B2. Avviare il server del fisso

Solo in questo percorso aprire la finestra **PowerShell usata sul fisso**, con gli stessi permessi della configurazione già funzionante, ed eseguire:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Tesi-mqt\prototipo-native\server-desktop.ps1" -ModelPath "D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models\qwen\Q8_0.gguf"
```

Questi sono percorsi personali verificati sul fisso, non directory che un nuovo utente deve creare. Se vengono spostati, aggiornare i due parametri. L'avviatore usa contesto 60.000, Vulkan e i controlli termici AMD. Lasciare aperta la finestra del controllore; i suoi log sono separati da quelli del client.

La copia server su `D:` è distinta dal clone WSL: aggiornare il branch non aggiorna automaticamente quella copia. Per usarne una nuova, preparare una directory Windows completa con i file del prototipo e i runtime richiesti da `setup.ps1`; non mescolare soltanto singoli script con runtime incompatibili.

### B3. Lanciare il client dal clone corrente in WSL

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
curl.exe --fail http://127.0.0.1:8089/health
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile desktop --transport windows --timeout 3600 --compile
```

Qui `curl.exe` e `--transport windows` sono intenzionali: il server è su Windows. Per un server eseguito dentro Linux usare invece `curl` e `--transport native`. Se `curl.exe` non è nel PATH WSL, controllare l'interoperabilità Windows/WSL; non reinstallare Qwen per un problema di collegamento.

## Leggere il risultato e terminare la prova

Il client stampa il dispositivo scelto, `config_id`, i parametri Qiskit, l'esito dei controlli e una cartella nuova in `runs/`. In quella cartella:

| File | Che cosa permette di verificare |
| --- | --- |
| `input.qasm`, `begin.json` | Circuito, profilo, trasporto, configurazione e versioni. |
| `prompt.json`, `retrieval.json`, `encoding.json` | Esempi recuperati e dati preparati per Qwen. |
| `attempt_*/` | Richieste, risposte, token e controlli di ogni tentativo. |
| `decision.json` | Coppia scelta e stato dei fatti. |
| `compiled.qasm`, `compilation.json` | Circuito compilato e controlli, se richiesti e riusciti. |
| `end.json`, `failure.json` | Completamento oppure errore. |

`accepted_with_unverified_facts` indica una coppia ammessa accettata al terzo tentativo con fatti non interamente verificati. L'ipotesi del modello resta testo non certificato. La compilazione non invia nulla a un computer quantistico.

Premere Ctrl+C nel terminale del server per fermarlo. Conservare i registri se si vuole confrontare il comportamento tra PC; non presentarli come nuove misure del Test scientifico.

## Quando qualcosa non funziona

| Problema | Controllo e azione |
| --- | --- |
| `node` assente o versione diversa | Caricare nvm, scegliere Node 22 e ripetere `bash setup.sh`. |
| `.venv/bin/python` assente | Tornare in `prototipo/` e completare il setup Linux; non usare una `.venv` copiata da Windows. |
| `llama-server` assente | Completare A4 oppure correggere `--bin`. Il setup Python non installa questo eseguibile. |
| Pesi diversi | Confrontare revisione, dimensione e SHA-256; non modificare `config.json` per accettarli. |
| RAM insufficiente o processo ucciso | Controllare `free -h`, i log e i limiti WSL. Chiudere applicazioni; se non basta, usare più RAM o una GPU adeguata. |
| `/health` non risponde | Verificare caricamento, porta, log e sistema che ospita il server. Non confondere `curl` Linux e `curl.exe` Windows. |
| `Contesto insufficiente` | La richiesta più 4.096 token di risposta non entra nel profilo. Usare un circuito più piccolo, un filtro esplicito o un profilo più capiente solo su hardware adeguato. Gli esempi non vengono tagliati automaticamente. |
| Timeout CPU | Conservare il log, controllare che il server lavori e valutare un limite maggiore con `--timeout`; nessun tempo di completamento è garantito. |
| Porta occupata | Ispezionare il server già attivo oppure scegliere una nuova `--port` e lo stesso indirizzo con `app.py run --url`. |

Per un'altra GPU, profili e registri server vedere [installazione e runtime](installazione_e_runtime.md). Per nuove campagne, altri modelli o Dataset usare la [guida di riproducibilità](../../riproducibilita/documentazione/guida.md). Per capire i moduli leggere [architettura e flusso](architettura_e_flusso.md).

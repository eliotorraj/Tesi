# Installazione, server e profili

Per la sequenza completa usare la [guida passo passo](guida_passo_passo.md). Questo documento spiega quali impostazioni cambiano tra CPU, GPU Linux e fisso WSL/Windows.

## Componenti distinti

Il **client Python** estrae caratteristiche, recupera il Dataset train, costruisce il prompt e compila con Qiskit. `setup.sh` prepara Python 3.12 e le versioni di `requirements.txt`, installa il codec TOON 4.1.1 con Node.js 22/npm e verifica l'indice. Può usare Python fornito da uv. Non installa Torch, CUDA o modelli MQT.

Il **server llama.cpp** carica Qwen e risponde via HTTP locale. Si compila separatamente per CPU o per il backend della GPU. `server.py` avvia un eseguibile Linux; gli script `.ps1` rimangono gli avviatori Windows. Non copiare `.venv` o un eseguibile compilato per un altro sistema operativo.

I pesi distribuiti separatamente sono Qwen3.5-4B Q8_0, 4.482.403.488 byte, SHA-256 `10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1`. Revisioni e URL sono in `config.json`; il campo `local_path` conserva provenienza, mentre il percorso operativo è quello passato all'avviatore. La [guida](guida_passo_passo.md#a5-procurarsi-il-gguf-esatto) mostra il download.

## Profili concordati fra server e client

| Profilo | Uso | Contesto | Batch / microbatch | Accelerazione |
| --- | --- | ---: | --- | --- |
| `cpu` | Prima prova su Linux senza GPU | 16.384 | 128 / 64 | Nessuna; device `none`, zero strati GPU |
| `gpu` | Prima prova con GPU Linux compatibile | 16.384 | 128 / 64 | Strati su GPU, selezionabili |
| `desktop` | Fisso o macchina adeguata al contesto completo | 60.000 | 512 / 128 | GPU |
| `laptop` | Nome accettato dal client per l'avviatore Windows CPU | 16.384 | 128 / 64 nel relativo `.ps1` | CPU |

Tutti mantengono pesi Q8_0, temperatura 0, cache q8_0 e massimo 4.096 token di risposta. Scegliere lo stesso profilo nel server Linux e in `app.py run`. Il client non reimposta il contesto del server. Se input e budget di risposta eccedono il limite, interrompe prima della generazione senza tagliare esempi.

`--transport native` collega al server Linux, anche se Linux è in WSL. `--transport windows` usa `curl.exe` da WSL verso il server Windows. `auto`, valore predefinito mantenuto per gli avvii esistenti, sceglie Windows in WSL e HTTP nativo altrove. Le guide specificano il trasporto per evitare ambiguità.

## Memoria e tempi sulla CPU

Occorrono almeno 16 GB installati per tentare la prova ridotta. Il controllo Linux legge `MemAvailable` da `/proc/meminfo`: richiede 9 GiB liberi prima dell'avvio CPU e arresta il proprio server dopo tre rilevazioni consecutive sotto 2 GiB. In WSL questi valori riguardano la macchina virtuale. Lo swap non viene conteggiato come RAM.

I soli pesi occupano circa 4,18 GiB; cache, calcolo, client e sistema richiedono altro spazio. Il margine è prudenziale e non certifica che ogni richiesta entri in memoria. Anche un circuito piccolo può generare un prompt lungo per il catalogo e gli esempi. La guida limita esplicitamente i candidati a Falcon 27 per iniziare. Il profilo desktop a 60.000 token non è il percorso CPU proposto per 16 GB.

Il timeout HTTP predefinito del client è 600 secondi; la prima prova CPU usa esplicitamente 3.600. La durata effettiva dipende dalla macchina e non è garantita. Una GPU compatibile è consigliata soprattutto per ridurre l'attesa nella lettura del prompt.

## GPU su Linux

La GPU deve essere visibile al backend di llama.cpp, con driver adeguati. I nomi AMD del fisso non vengono incorporati nell'avviatore Linux. Per AMD/Intel/NVIDIA compatibili si può usare **Vulkan**; con NVIDIA è disponibile anche **CUDA**. Questi backend e le istruzioni di compilazione sono documentati nel [progetto llama.cpp](https://github.com/ggml-org/llama.cpp/blob/b10930/docs/build.md).

Per Vulkan, su Ubuntu/Debian, dopo i prerequisiti della guida:

```bash
sudo apt install libvulkan-dev glslc spirv-headers vulkan-tools
vulkaninfo --summary
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-vulkan \
  -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build runtime/llama.cpp/build-vulkan --config Release --target llama-server -j 2
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-vulkan/bin/llama-server --list-devices
```

Prima occorre aver clonato llama.cpp come nel passo A4. I pacchetti di sviluppo non installano automaticamente un driver adatto a ogni scheda: se `vulkaninfo` mostra soltanto un renderer software, non si sta usando la GPU fisica. In WSL verificare anche il supporto del backend nella propria configurazione; sul fisso il percorso Windows già funzionante rimane disponibile.

L'elenco di llama.cpp mostra gli identificativi utilizzabili, per esempio `Vulkan0`. Sono esempi, non nomi universali: scegliere quello realmente restituito dalla propria macchina con `--device`. Per una prima prova GPU, da `prototipo/`:

```bash
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-vulkan/bin/llama-server \
  --model runtime/models/Qwen3.5-4B-Q8_0.gguf --profile gpu
```

Nel secondo terminale:

```bash
curl --fail http://127.0.0.1:8089/health
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile gpu --transport native --timeout 3600 --device ibm_falcon_27 --compile
```

L'avviatore richiede tutti gli strati sulla GPU; con memoria video insufficiente si può scegliere un numero inferiore con `--gpu-layers N`, trasferendo altro lavoro alla CPU e alla RAM. Non esiste una soglia VRAM garantita per tutte le GPU: verificare allocazioni e strati effettivamente caricati in `stderr.log`. Passare a `desktop` su entrambi i comandi solo con memoria sufficiente per il contesto maggiore.

Per CUDA occorrono driver NVIDIA e CUDA Toolkit compatibili; la guida non li installa automaticamente. Con questi prerequisiti usare una directory separata:

```bash
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-cuda \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build runtime/llama.cpp/build-cuda --config Release --target llama-server -j 2
```

Passare poi `runtime/llama.cpp/build-cuda/bin/llama-server` a `--bin`. `--list-devices` e `--device` funzionano attraverso il backend, senza nomi fissi di schede. L'avviatore registra versione, impronta dell'eseguibile, dispositivi esposti e argomenti. L'interfaccia è quella del [server llama.cpp b10930](https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md).

## Sensori e avviatori del fisso

`server-desktop.ps1`, `server-desktop-internal.ps1`, `server-laptop.ps1`, `setup.ps1` e `verify-model.ps1` sono conservati. Il percorso desktop dipende da Windows, Vulkan, PsSuspend verificato e `AmdSensors.cs`; le soglie termiche sono quelle della macchina configurata. Non sono impostazioni da copiare indistintamente su un'altra scheda.

Il nuovo `server.py` Linux usa il rilevamento GPU del backend e controlla la RAM disponibile. **Non misura temperatura, consumo o memoria GPU e non implementa la pausa termica AMD.** Il log lo dichiara. Le protezioni del driver restano attive, ma non equivalgono al monitor applicativo del fisso. Per misure o pause termiche su altre GPU serve un adattatore appropriato ai sensori esposti dal sistema; non occorre modificare gli script personali per una prima prova Linux.

## Controlli e registri

`server.py --dry-run` con gli stessi argomenti dell'avvio verifica GGUF, eseguibile e margine RAM, poi mostra il comando senza caricare Qwen. `--list-devices` non richiede pesi. `/health` con `status: ok` conferma che il server è pronto; `app.py check` conferma soltanto client e dati.

I log Linux sono in `runtime/server-runs/<id>/`: `launch.json`, `stdout.log`, `stderr.log`, `resources.jsonl` ed `exit.json`. Il controllore termina solo il processo che ha avviato. I `.ps1` stampano la propria destinazione Windows. I registri del client sono invece in `runs/`, con input, prompt, risposte, verifiche e compilazione.

La prova CPU o GPU su un'altra macchina non garantisce risultati e tempi identici a una campagna scientifica. Per tali confronti conservare risorse, software, contesto e criteri nel [kit di riproducibilità](../../riproducibilita/README.md).

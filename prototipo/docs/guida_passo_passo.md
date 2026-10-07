# Run the prototype on Linux, step by step

The prototype reads OpenQASM 2, retrieves train examples, asks **Qwen3.5-4B Q8_0** for a device/configuration choice and can compile it with Qiskit. The clone includes the RAG examples. Obtain model weights separately; MQT training and Dataset regeneration are unnecessary for this demonstration.

Choose your setup:

- **New Linux user without a GPU:** follow path A. System package commands target Ubuntu 24.04 or compatible Debian/Ubuntu installations.
- **Original Radeon RX 6750 XT desktop:** follow path B for an Ubuntu/WSL client and the existing Windows server.
- **Another Linux GPU:** prepare the client using path A, then follow [Linux GPU setup](installazione_e_runtime.md#linux-gpu). The desktop AMD scripts are specific to that workstation.

A compatible GPU is recommended for inference. CPU prompt processing can be slow. **16 GB installed RAM is an indicative starting point, not a guarantee:** Linux needs at least 9 GiB available before CPU server startup and additional headroom during execution. In WSL, the distribution's assigned RAM is what matters. Large requests may exceed the available resources.

## Path A: Linux CPU

### A1. Check resources

```bash
free -h
lscpu
```

Check `available` in `free -h`. Close memory-heavy applications if less than about 9 GiB remains; swap is not available RAM. Allow space for the clone, dependencies, llama.cpp build and approximately 4.5 GB of weights. Around 20 GB free disk is a practical starting reserve, increased when retaining many runs. Use your own account for the prototype; only system package installation needs `sudo`.

### A2. Install prerequisites

```bash
sudo apt update
sudo apt install git curl ca-certificates build-essential cmake pkg-config libssl-dev libcurl4-openssl-dev
```

Python 3.12 and Node.js 22 with npm are required. Skip installation of prerequisites already available. [uv](https://docs.astral.sh/uv/getting-started/installation/) can provide Python without replacing the system interpreter:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12
uv --version
```

For Node.js, the following uses the pinned [nvm installer](https://github.com/nvm-sh/nvm#install--update-script). If nvm is already installed, load it and select Node.js 22:

```bash
export NVM_DIR="$HOME/.nvm"
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
. "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
node --version
npm --version
```

`node --version` must start with `v22.`. In later terminals, load `nvm.sh` and run `nvm use 22` again if needed.

### A3. Clone the branch and prepare the client

Enter an existing clone, or create a new one:

```bash
git clone --branch riproducibilita-esperimenti --single-branch \
  https://github.com/eliotorraj/Tesi.git "$HOME/Tesi-riproducibilita"
cd "$HOME/Tesi-riproducibilita/prototipo"
bash setup.sh
.venv/bin/python -B app.py check
```

Adjust the directory to your clone's location. **All remaining path A commands run from `prototipo/`.** Setup creates `.venv`, installs fixed dependencies, prepares TOON and builds the retrieval index. It neither installs llama.cpp nor downloads weights. `status: ready` confirms the client, data and Targets; it does not confirm inference. Recreate the environment and index locally instead of copying them from another platform.

### A4. Build llama.cpp for CPU

Use the fixed **b10930** revision and build on the current computer, following its [build instructions](https://github.com/ggml-org/llama.cpp/blob/b10930/docs/build.md):

```bash
git clone --branch b10930 --depth 1 \
  https://github.com/ggml-org/llama.cpp.git runtime/llama.cpp
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-cpu \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF
cmake --build runtime/llama.cpp/build-cpu --config Release --target llama-server -j 2
runtime/llama.cpp/build-cpu/bin/llama-server --version
```

`-j 2` limits build processes, not inference threads. If the source directory exists, check its revision with `git -C runtime/llama.cpp describe --tags --exact-match` and skip cloning. Retain an existing build when diagnosing errors.

<a id="a5-procurarsi-il-gguf-esatto"></a>
### A5. Obtain the exact GGUF

Use an existing matching file or download it from the [fixed model revision](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/e87f176479d0855a907a41277aca2f8ee7a09523):

```bash
mkdir -p runtime/models
curl --fail --location --continue-at - \
  'https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q8_0.gguf' \
  --output runtime/models/Qwen3.5-4B-Q8_0.gguf
sha256sum runtime/models/Qwen3.5-4B-Q8_0.gguf
```

Expected size: **4,482,403,488 bytes**. Expected SHA-256:

```text
10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1
```

`server.py` rechecks size and hash on every startup. Other quantizations require a new toolkit configuration, rather than changing the selected prototype's identity checks.

### A6. Start Qwen in the first terminal

```bash
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-cpu/bin/llama-server \
  --model runtime/models/Qwen3.5-4B-Q8_0.gguf \
  --profile cpu
```

Leave the terminal open. The CPU profile uses 16,384 context tokens, q8_0 cache and one request at a time, with no GPU/NPU acceleration. Add `--threads 4`, for example, to limit threads.

The launcher prints its directory under `runtime/server-runs/`. Inspect `stderr.log` and `exit.json` if it exits. Hash verification and loading take time; a quiet terminal does not itself mean the process is stuck.

### A7. Check the server and compile Bell

Open a second Linux terminal and return to `prototipo/`:

```bash
cd "$HOME/Tesi-riproducibilita/prototipo"
curl --fail http://127.0.0.1:8089/health
```

Wait for `{"status":"ok"}`. HTTP 503 can occur while loading; retry the health check after a short interval. Then run:

```bash
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile cpu --transport native --timeout 3600 \
  --device ibm_falcon_27 --compile
```

The included Bell circuit and Falcon 27 filter keep the first request small. The 3,600-second timeout applies to each HTTP call, not the whole command or an expected duration. Up to three generations may be needed. Check server logs before relaunching: each invocation creates a new run.

`--transport native` uses Linux HTTP, including in WSL. Client `--device` selects a **synthetic quantum device**, not the host GPU. Omit `--compile` for a recommendation only. After the first check, substitute your own OpenQASM 2 file and adjust the device filter as needed.

## Path B: original Windows GPU server with WSL client

This path uses the original **AMD Radeon RX 6750 XT**, Windows Vulkan runtime and PowerShell thermal monitoring. The client runs in the current Ubuntu/WSL clone.

### B1. Prepare the WSL client

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
bash setup.sh
.venv/bin/python -B app.py check
```

The same Python 3.12 and Node.js 22 prerequisites apply. This prepares the current clone's client without recreating the separately configured Windows server.

### B2. Start the desktop server

In the original workstation's PowerShell environment:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Tesi-mqt\prototipo-native\server-desktop.ps1" -ModelPath "D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models\qwen\Q8_0.gguf"
```

These are workstation-specific paths, not directories a new user should create. Adjust them if that installation has moved. The launcher uses 60,000 context tokens, Vulkan and AMD thermal checks. Keep the controller window open; server logs are separate from client logs.

The D: server copy is independent of the WSL clone. Updating this branch does not update that copy. Prepare a complete compatible Windows prototype/runtime installation when replacing it; copying individual scripts alone may mix incompatible versions.

### B3. Run the current WSL client

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
curl.exe --fail http://127.0.0.1:8089/health
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile desktop --transport windows --timeout 3600 --compile
```

`curl.exe` and `--transport windows` intentionally target Windows. Linux servers use `curl` and `--transport native`. If `curl.exe` is unavailable in WSL, check Windows interoperability and PATH.

## Read the result and stop the server

The client prints the device, `config_id`, Qiskit parameters, check outcomes and a new `runs/` directory:

| Files | Contents |
| --- | --- |
| `input.qasm`, `begin.json` | Input, profile, transport, configuration and versions. |
| `prompt.json`, `retrieval.json`, `encoding.json` | Retrieved examples and prepared model input. |
| `attempt_*/` | Requests, responses, tokens and checks for each attempt. |
| `decision.json` | Selected pair and fact status. |
| `compiled.qasm`, `compilation.json` | Successful optional compilation and checks. |
| `end.json`, `failure.json` | Completion or failure. |

`accepted_with_unverified_facts` means an allowed pair was accepted on the third attempt with some facts unverified. The free hypothesis is not semantically certified. Compilation does not submit a quantum hardware job. Press Ctrl+C in the server terminal to stop it. Preserve records when comparing machines; ordinary usage records are not new scientific Test measurements.

## Troubleshooting

| Problem | Check or action |
| --- | --- |
| Missing/wrong Node.js | Load nvm, select Node.js 22 and rerun setup. |
| Missing `.venv/bin/python` | Complete setup from `prototipo/`; use a Linux environment. |
| Missing llama-server | Complete A4 or correct `--bin`; Python setup does not install it. |
| Wrong weights | Verify revision, byte count and SHA-256. |
| Insufficient RAM or killed process | Check `free -h`, logs and WSL limits; free resources or use suitable hardware. |
| No health response | Check loading, port, logs and which operating system hosts the server. |
| Insufficient context | Input plus 4,096 output tokens exceeds the profile. Use a smaller circuit, explicit filter or a larger profile on suitable hardware; examples are not silently removed. |
| CPU timeout | Retain logs, check progress and consider a larger `--timeout`; completion time is not guaranteed. |
| Port already used | Inspect the existing server or choose a different `--port` and matching client `--url`. |

See [runtime configuration](installazione_e_runtime.md), [architecture](architettura_e_flusso.md) and the [new-experiment guide](../../riproducibilita/documentazione/guida.md) for the next steps.

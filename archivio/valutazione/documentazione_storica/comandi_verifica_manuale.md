# Historical manual verification commands

These commands were reviewed on 21 September 2026 for the
`riorganizzazione-prototipo` branch and the original desktop computer. Graphify
and Qwen were not started during that review. The script review is documented
in the [21 September report](../../riorganizzazione_2026_09_21/revisione_script/README.md).
This page preserves those machine-specific instructions. For a current setup,
start with the [prototype guide](../../../prototipo/docs/guida_passo_passo.md)
or the [reproduction toolkit guide](../../../riproducibilita/documentazione/guida.md).

## 1. Update Graphify — Ubuntu/WSL terminal

Run from the repository root, rather than `archivio/esperimento_v2`.
The commands were checked against the locally installed **graphifyy 0.9.63**;
they do not require updating the package. `.graphifyignore` excludes runtimes,
generated data and duplicate source copies. Current code, experimental code,
tests and documents remain eligible. These exclusions do not delete files.

```bash
cd /home/elio/Tesi-mqt-2.4-v2
export PATH="$HOME/.local/bin:$PATH"
git branch --show-current
```

The branch used for this historical review was `riorganizzazione-prototipo`.
Preserve the previous graph before updating it. Each invocation below creates
a new backup and log:

```bash
mkdir -p .workspace_archive
graph_backup=".workspace_archive/graphify-before-$(date +%Y%m%d-%H%M%S)"
set -o pipefail
cp -a graphify-out "$graph_backup" &&
    graphify update . 2>&1 | tee "${graph_backup}-update.log"
```

Wait for `Code graph updated`. Reconciling the graph with moved directories can
take time. Run one update at a time. If it fails, preserve the log instead of
adding `--force`. This structural update makes no model calls. It updates code
and supported document structure without repeating the semantic analysis of
texts and papers. That separate operation uses `/graphify --update` in an
assistant session.

The installed `update` command also regenerates HTML. Repeating
`graphify export html` was unnecessary in this version and could reuse stale
community analysis. On 21 September, that issue was resolved by archiving the
outdated analysis file, without modifying `graph.json`. After a successful
update, check a query:

```bash
graphify query "Qwen facts retrieval compilation" --budget 1500
```

The graph before that reorganization contained 68,244 nodes. The HTML view may
show communities instead of every node. Source references must follow the
repository layout in use. Do not remove `.needs_update` manually to conceal a
failed update.

## 2. Start Qwen on the original desktop — Windows PowerShell

The native directory and runtimes already existed on this computer. Copy the
launchers from WSL into that native directory. This does not copy indexes,
Python environments or experiment records.

```powershell
$Source = "\\wsl.localhost\Ubuntu\home\elio\Tesi-mqt-2.4-v2\prototipo"
$Destination = "D:\Tesi-mqt\prototipo-native"
$Model = "D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models\qwen\Q8_0.gguf"
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$LaunchFiles = "server-desktop.ps1", "server-desktop-internal.ps1", "verify-model.ps1", "AmdSensors.cs", "config.json"
foreach ($Name in $LaunchFiles) {
    Copy-Item -LiteralPath (Join-Path $Source $Name) -Destination $Destination -Force
}
if (-not (Test-Path -LiteralPath $Model)) { throw "Qwen weights not found" }
if (-not (Test-Path -LiteralPath (Join-Path $Destination "runtime\desktop\llama-server.exe"))) { throw "Desktop runtime not found" }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Destination\server-desktop.ps1" -ModelPath $Model
```

Keep the window open. The SHA256 check reads about 4.48 GB; wait for weight
verification to finish. The controller then initializes the AMD sensors and
starts the Vulkan server. The selected desktop configuration uses a 60,000-token
context, q8_0 cache, 512/128 batch sizes and temperature controls. Each run gets
a new directory under `%LOCALAPPDATA%\QwenPrototype\runs`. Do not start a second
server while the first one is running.

In a **second PowerShell window**, check whether loading has finished:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8089/health" -TimeoutSec 5
```

Wait for `status: ok`. A connection error or loading response does not confirm
that the model is ready. Start the client after the health check succeeds.

## 3. Try the complete pipeline — Ubuntu/WSL terminal

These commands use the Python 3.12 environment preserved at the repository root:

```bash
cd /home/elio/Tesi-mqt-2.4-v2/prototipo
../.venv/bin/python app.py prepare
../.venv/bin/python app.py run examples/bell.qasm --profile desktop --compile
```

The first command verifies the train Dataset and prepares the local index. The
second retrieves five examples, requests a Qwen recommendation at temperature
0, validates the response and compiles the Bell circuit with
`seed_transpiler=0`. Bell is a technical check, not an experimental Test circuit.

A completed run prints `compiled: true`, the device, the configuration and its
record directory under `prototipo/runs/`. `accepted_with_unverified_facts` is
distinct from `success`: after three attempts, a valid pair may be accepted with
unverified facts under the v4 contract. To try a personal circuit, replace
`examples/bell.qasm` with an OpenQASM 2 file. Keep reserved Test circuits separate.

WSL needs `curl.exe` on PATH to reach the Windows server through localhost.
The local Node.js 22 executable is `prototipo/runtime/node/bin/node`.
These instructions reused the existing desktop environment; they did not
require `setup.ps1` or reinstalling it.

## If startup stalls

Keep resource checks enabled. Preserve the last printed line and the run
directory. From another PowerShell window:

```powershell
$RunDirectory = Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\QwenPrototype\runs" -Directory |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($RunDirectory) {
    $RunDirectory.FullName
    Get-ChildItem -LiteralPath $RunDirectory.FullName
    $ServerError = Join-Path $RunDirectory.FullName "stderr.log"
    if (Test-Path -LiteralPath $ServerError) { Get-Content -LiteralPath $ServerError -Tail 60 }
}
Get-Process -Name llama-server -ErrorAction SilentlyContinue |
    Select-Object Id, StartTime, CPU, WorkingSet64
```

If no new directory is created, the failure precedes server startup. Record
the last printed line; older logs do not describe this attempt. Use Ctrl+C in
the controller window to stop it and verify that its child process has exited.
Avoid stopping unrelated experiment processes by name.

## Intel laptop — separate check

Copy `prototipo/`, the GGUF weights and the CPU runtime to the laptop. Create a
fresh Windows environment as described in the prototype guide. Do not copy the
desktop's `.venv`, `runtime/rag` or `runs`. With Python 3.12 and Node.js 22
available, run from PowerShell:

```powershell
cd C:\path\to\prototipo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -RuntimeProfile cpu
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\server-laptop.ps1 -ModelPath "C:\models\Qwen3.5-4B-Q8_0.gguf"
```

If the runtime is missing, add `-DownloadRuntime` to `setup.ps1` only. In a second
window, after `/health` returns `status: ok`:

```powershell
cd C:\path\to\prototipo
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27 --compile
```

The CPU profile uses a 16,384-token context and requires at least 9 GiB of free
memory at startup. It does not use the integrated GPU or NPU. Restricting the
device to Falcon 27 reduces request size. This check differs from the desktop
experiment: laptop memory use and timings must be measured separately.

# Installation, server and profiles

Use the [step-by-step guide](guida_passo_passo.md) for the complete sequence. This document explains CPU, Linux GPU and original WSL/Windows settings.

## Client and server

The **Python client** extracts features, retrieves train examples, builds prompts and compiles with Qiskit. `setup.sh` prepares Python 3.12 with `requirements.txt`, the TOON 4.1.1 codec through Node.js 22/npm, and the retrieval index. Python can come from uv. Client setup does not install Torch, CUDA or trained MQT models.

The **llama.cpp server** loads Qwen and serves local HTTP requests. Build it separately for CPU or your GPU backend. `server.py` launches Linux binaries; `.ps1` files launch the Windows runtimes. Environments and binaries must match their operating system.

The selected GGUF is Qwen3.5-4B Q8_0, **4,482,403,488 bytes**, SHA-256 `10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1`. `config.json` records revision and URL. Its `local_path` is provenance; the launcher argument selects the operational file. See the [download instructions](guida_passo_passo.md#a5-obtain-the-exact-gguf).

## Match client and server profiles

| Profile | Intended use | Context | Batch / microbatch | Acceleration |
| --- | --- | ---: | --- | --- |
| `cpu` | First Linux CPU trial | 16,384 | 128 / 64 | `device=none`, zero GPU layers |
| `gpu` | First compatible Linux GPU trial | 16,384 | 128 / 64 | Configurable GPU offload |
| `desktop` | Hardware supporting the full context | 60,000 | 512 / 128 | GPU |
| `laptop` | Client-compatible name for the Windows CPU launcher | 16,384 | 128 / 64 in its PowerShell script | CPU |

All retain Q8_0 weights, temperature 0, q8_0 cache and a 4,096-token response budget. Choose matching profiles on client and server; the client cannot resize server context. If input plus output budget does not fit, the client stops before generation without dropping examples.

`native` transport uses Linux HTTP, including within WSL. `windows` uses `curl.exe` from WSL to Windows. The compatibility default `auto` selects Windows in WSL and native HTTP elsewhere; explicit transport avoids ambiguity.

## CPU memory and timing

At least 16 GB installed RAM is an indicative starting point for the small trial. The Linux launcher reads `MemAvailable` from `/proc/meminfo`, requires 9 GiB available before CPU startup, and stops its own server after three consecutive readings below 2 GiB. WSL readings apply to the virtual machine. Swap is excluded.

Weights alone occupy about 4.18 GiB; cache, computation, client and OS need more. These checks do not guarantee that every request fits. Even a small circuit can create a long catalog/example prompt. The first-run guide filters to Falcon 27. A 60,000-token desktop context is not the proposed 16 GB CPU setup.

The client defaults to a 600-second HTTP timeout; the first CPU example explicitly uses 3,600 seconds. Actual duration depends on the machine. GPU acceleration is especially useful for prompt processing.

<a id="gpu-su-linux"></a>
## Linux GPU

The GPU needs a working driver and must be visible to the llama.cpp backend. The Linux launcher does not hard-code the original desktop's AMD device. Compatible AMD, Intel or NVIDIA systems may use Vulkan; NVIDIA also supports CUDA. Use the pinned revision's [build documentation](https://github.com/ggml-org/llama.cpp/blob/b10930/docs/build.md).

After cloning llama.cpp as in guide A4, Vulkan setup on Ubuntu/Debian is:

```bash
sudo apt install libvulkan-dev glslc spirv-headers vulkan-tools
vulkaninfo --summary
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-vulkan \
  -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build runtime/llama.cpp/build-vulkan --config Release --target llama-server -j 2
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-vulkan/bin/llama-server --list-devices
```

Development packages do not provide every device's driver. If `vulkaninfo` reports only a software renderer, the physical GPU is not being used. Check backend support in your particular WSL configuration; the original desktop can continue using its working Windows server.

Use identifiers returned by `--list-devices`, such as `Vulkan0`, rather than assuming universal names. For a first GPU trial from `prototipo/`:

```bash
.venv/bin/python -B server.py \
  --bin runtime/llama.cpp/build-vulkan/bin/llama-server \
  --model runtime/models/Qwen3.5-4B-Q8_0.gguf --profile gpu
```

In a second terminal:

```bash
curl --fail http://127.0.0.1:8089/health
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile gpu --transport native --timeout 3600 --device ibm_falcon_27 --compile
```

The launcher requests all GPU layers. With insufficient VRAM, `--gpu-layers N` can offload fewer layers, increasing CPU/RAM work. Check actual allocations and loaded layers in `stderr.log`; there is no universal guaranteed VRAM threshold. Select `desktop` on both commands only with resources for the larger context.

CUDA requires compatible NVIDIA drivers and the CUDA Toolkit. With those installed, use a separate build directory:

```bash
cmake -S runtime/llama.cpp -B runtime/llama.cpp/build-cuda \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build runtime/llama.cpp/build-cuda --config Release --target llama-server -j 2
```

Pass `runtime/llama.cpp/build-cuda/bin/llama-server` to `--bin`. Backend discovery supplies `--list-devices`/`--device`. The launcher records binary version/hash, exposed devices and arguments. Its interface targets [llama.cpp b10930](https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md).

## Original desktop monitoring

`server-desktop.ps1`, `server-desktop-internal.ps1`, `server-laptop.ps1`, `setup.ps1` and `verify-model.ps1` support the original Windows setup. Desktop operation depends on Vulkan, verified PsSuspend and `AmdSensors.cs`. Its thermal thresholds are machine-specific.

The Linux launcher discovers GPU devices and checks available RAM. It **does not measure GPU temperature, GPU memory or energy, and does not implement AMD thermal pausing**. Driver protections are separate from application monitoring. Supporting thermal pauses on other GPUs would require an appropriate sensor adapter.

## Checks and records

With normal startup arguments, `server.py --dry-run` verifies GGUF, binary and RAM headroom and prints the command without loading Qwen. `--list-devices` needs no weights. `/health` returning `status: ok` indicates server readiness; `app.py check` checks the client and its data.

Linux records are in `runtime/server-runs/<id>/`: `launch.json`, `stdout.log`, `stderr.log`, `resources.jsonl` and `exit.json`. The controller terminates only the process it started. PowerShell launchers print their Windows log locations. Client decisions are recorded separately in `runs/`.

Running on another host does not guarantee identical results or timings. For a scientific comparison, declare resources, versions, context and criteria through the [reproduction toolkit](../../riproducibilita/README.md).

# QAdviser prototype

This standalone prototype uses Qwen3.5-4B Q8_0 at temperature 0 to select a synthetic quantum device and a Qiskit configuration. It reads OpenQASM 2, retrieves train examples, checks the response and optionally compiles the circuit. It does not submit quantum hardware jobs or require trained MQT models.

## First run

Follow the [step-by-step guide](docs/guida_passo_passo.md) for Python 3.12, Node.js 22/npm, Python dependencies, llama.cpp b10930 and the exact GGUF file. It covers Linux CPU use and the original WSL client with a Windows AMD GPU server. A machine with 16 GB RAM is a starting point for the small CPU example, not a guarantee for every circuit or a full campaign.

After following the setup guide, activate the configured Python environment and start the server. Then run from this directory:

```bash
python -B app.py check
python -B app.py run examples/bell.qasm \
  --profile cpu --transport native --timeout 3600 \
  --device ibm_falcon_27 --compile
```

`check` checks the client installation. Start the server separately. Without `--compile`, `run` returns a recommendation only. See [installation and runtime](docs/installazione_e_runtime.md) for other GPUs, transport and logs.

## Directory map

| Entry | Purpose |
| --- | --- |
| `app.py` | Prepare the retrieval index, check installation and process a circuit. |
| `setup.sh`, `server.py` | Linux client setup and server startup. |
| `setup.ps1`, `server-*.ps1`, `verify-model.ps1`, `AmdSensors.cs` | Windows utilities; desktop thermal monitoring is AMD-specific. |
| [prototype/](prototype/README.md) | Circuit input, retrieval, prompts, validation and compilation. |
| [data/](data/README.md) | 396 unique train examples, circuits, transformation and the 422-source manifest. |
| [configs/](configs/README.md), `config.json` | Device catalog, Qiskit configurations and selected model settings. |
| [schemas/](schemas/README.md) | Framework and response contracts. |
| [qiskit_dataset/](qiskit_dataset/README.md), [scripts/](scripts/README.md) | Catalog loading and integrity helpers. |
| `portable_features.py`, `LICENSE-MQT-Predictor` | The 49-feature extractor and its attribution. |
| `examples/` | Bell circuit for a technical check. |
| [runtime/](runtime/README.md) | Runtime setup documentation. |
| [docs/](docs/README.md) | Guides, architecture and current scientific protocol. |

The client checks verifiable facts against supplied data; the free hypothesis is not semantically certified. On the third attempt, an allowed, structurally valid pair may be accepted with unverified facts, which is recorded.

For other models, Dataset generation, validation/Test or prototype export, use [riproducibilita/](../riproducibilita/README.md). This prototype runs without reading the toolkit or archive.

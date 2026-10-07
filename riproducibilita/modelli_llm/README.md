# LLM registry and server startup

`modelli.json` defines candidates; `provenienza_originale.json` records reference URLs, revisions and hashes. `server.py` launches or checks llama.cpp.

From the toolkit root after setup:

```bash
python configura.py modelli my-trial qwen
python configura.py modello my-trial qwen --file /path/to/Qwen3.5-4B-Q8_0.gguf
python configura.py risorse my-trial --server-bin /path/to/llama-server --gpu-layers 0
python configura.py verifica my-trial
python esperimento.py --esperimento my-trial server qwen --list-devices
python esperimento.py --esperimento my-trial server qwen
```

Use another terminal with the same environment for `server qwen --controlla`. Ctrl+C stops the launched process. The checker needs identity/context endpoints; inference uses `/apply-template`, `/tokenize` and JSON-schema-constrained `/completion`.

Unselected candidates keep their settings but need no weights. Register a different model or quantization with `aggiungi-modello`, providing a local GGUF, source, revision and precision. Changing a reference model's path does not change its expected hash. See the [recipes](../documentazione/configurazione.md).

CPU uses zero GPU layers and `device=none`. GPU profiles request acceleration; `--list-devices` shows backend identifiers. Check drivers and memory locally.

Linux servers use `native` transport, including in WSL. For the original externally started Windows server, configure `--trasporto windows`; the client uses `curl.exe`. Direct launch overrides are recorded, but planned resources should be fixed before preparation.

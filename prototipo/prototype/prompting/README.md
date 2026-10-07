# Prompts, TOON and facts v4

| Entry | Purpose |
| --- | --- |
| `minimal.py` | Build circuit, device and train-example views. |
| `toon.py` | Encode the view and verify a round trip. |
| `facts.py` | Build instructions and check choices and declared facts. |
| [toon_runtime/](toon_runtime/README.md) | Locked Node.js codec used by Python. |

Responses contain a device, a configuration, one or two facts and a free hypothesis. The client allows up to three complete responses. On the final attempt an allowed, structurally valid pair may be accepted with unverified facts, recorded explicitly. The hypothesis is not semantically certified.

Node.js 22 must be available in the client environment even when Qwen runs elsewhere. See [architecture and data flow](../../docs/architettura_e_flusso.md).

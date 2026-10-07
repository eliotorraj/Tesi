# Assistant modules

`quantum_assistant/` contains types and implementations for OpenQASM 2 input, 49 circuit features, device compatibility, retrieval and Qiskit compilation. `prompting/` builds TOON prompts and implements the facts v4 response contract.

Read `../app.py` first to see how the public client connects these operations. The LLM server runs separately through `server.py` on Linux or the supplied desktop PowerShell scripts. See [architecture](../docs/architettura_e_flusso.md) for relationships and the [usage guide](../docs/guida_passo_passo.md) for commands.

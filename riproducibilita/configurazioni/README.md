# Experiment settings

Use `configura.py` from the toolkit root for checked configuration commands:

```bash
python configura.py nuovo my-trial --profilo cpu
python configura.py sistemi my-trial llm_rag llm_senza_rag random
python configura.py dispositivi my-trial ibm_falcon_27
python configura.py mostra my-trial
```

[esperimenti/](esperimenti/README.md) stores named configurations and revisions. `esperimento.json` and `catalogo.json` are the distributed defaults for the explicit `--config` interface. `generazione_llm.json` contains shared prompt and generation settings; change it only as an explicit pre-campaign choice.

The catalog defines quantum Targets, Qiskit configurations, seeds and workers. `risorse` and `modello` configure host CPU/GPU and LLM resources. CPU/GPU profiles start with the same context and batch settings; check memory and backend support locally.

After `prepara`, use `configura.py duplica SOURCE NEW_NAME` for new conditions. See the [recipes](../documentazione/configurazione.md) and [guide](../documentazione/guida.md).

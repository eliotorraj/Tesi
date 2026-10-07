# Manual chat with Qwen, Phi or Gemma

This guide describes the archived local-chat launcher and preservation of manual train checks. Chat does not start validation. For the selected standalone system, use the [current prototype guide](../../../../prototipo/docs/guida_passo_passo.md); for a new experiment, use the [reproduction toolkit](../../../../riproducibilita/README.md). The [archived protocol](../protocollo_sperimentale.md) explains the historical procedure.

## Choose a model

Run these commands from `archivio/esperimento_v2/`, using the existing pinned Python environment. The examples use the repository-root `.venv`; substitute its path if the environment is elsewhere. Model weights and the historical Windows server installation are external prerequisites.

```bash
../../.venv/bin/python -m llm_selection.chat --model qwen
../../.venv/bin/python -m llm_selection.chat --model phi
../../.venv/bin/python -m llm_selection.chat --model gemma
```

Run one launcher at a time. Qwen remains the default when `--model` is omitted. The command checks weights and starts the server. When it reports readiness, open the [local chat](http://127.0.0.1:8089) in the Windows browser.

Keep the terminal open. Ctrl+C closes the server owned by that session; closing the browser page does not. An existing session is not automatically replaced.

To check only the file and profile:

```bash
../../.venv/bin/python -m llm_selection.chat --model phi --check
```

`--check` does not read all weights to recompute their fingerprint, send server requests or establish that the profile fits the available resources. The fingerprint is checked at actual startup.

## Initial historical profiles

| Model | Weights | Context | Cache |
| --- | --- | ---: | --- |
| Qwen3.5-4B | Q8_0 | 147456 | q8_0 |
| Phi-4-mini-instruct | Q8_0 | 114688 | q4_0 |
| Gemma 4 E4B-it | Q8_0 | 131072 | q4_0 |

These were starting profiles for manual checks, not the final validation-selected configurations. Qwen retained the earlier launch settings without depending on that launch's log. Monitor thresholds are defined in `llm_selection/hardware.py`.

You can select weight precision, context and cache:

```bash
../../.venv/bin/python -m llm_selection.chat --model phi \
  --precision Q8_0 --context 32768 --cache-type q4_0
```

The requested weights must already exist. The launcher rejects nonpositive contexts and contexts above the model's declared native limit. These historical profiles assign all layers to the GPU with the project's shared batch settings.

## Use the reduced experimental prompt

Automated technical checks prepare and submit the compact prompt directly. For manual chat, open a preserved `prompt_chat.txt` and paste its full contents into a new conversation. One historical example is:

```text
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/prompt_audits/lossless-v2-check-01/train/dj_indep_tket_2/prompt_chat.txt
```

This path is relative to the archived experiment root. It contains the DJ circuit, metric, five RAG examples and instructions. `llm_selection.prompt_audit` uses the [shared compaction](compattazione_prompt.md). Counts in the older audit use the Qwen tokenizer and are not measured Phi or Gemma counts.

The browser applies its own chat template and settings. Pasting a schema does not activate constrained generation or the experiment's semantic validator. Record the actual temperature, reasoning setting and output limit when making technical comparisons.

## Preserve the session

The default name includes the model and UTC timestamp. Supply a fresh label, for example `--label phi-manual-chat-01`, to choose another name.

Artifacts are under `llm_selection/manual_chats/NAME/` within the experiment's artifact directory. `request.json` records the model, profile and defaults version. Provenance, events and resource measurements are retained alongside it.

The launcher does not automatically capture the browser conversation. Export messages and settings into the session directory. Do not run manual chat and an automated check against the same server concurrently.

## Earlier evidence

The [compact-prompt report](../resoconti/2026-09-15_prompt_compatto.md) preserves Qwen measurements, errors and responses. The [earlier diagnosis](../resoconti/2026-09-15_diagnosi_qwen.md) records analysis of the first responses. These are historical records in their original language.

Launcher selection was checked with simulated starts. Loading the real models is separate from those software checks.

# Historical local LLM selection: operational guide

This guide covers the archived v1 procedure. The second validation study, introduced on 19 September 2026 with structured facts, temperatures 0/0.4/0.7 and interrupted-call recovery, is documented in [llm_selection/v2/](../../llm_selection/v2/README.md). The completed selection is preserved in the archive. **For new campaigns, use the [reproduction toolkit](../../../../riproducibilita/README.md).**

The [module README](../../llm_selection/README.md) explains the programs. The [archived protocol](../protocollo_sperimentale.md) records the historical rules. At the 15 September checkpoint, train technical checks were still in progress, the study was not frozen and no local winner had been selected. The [compact-prompt report](../resoconti/2026-09-15_prompt_compatto.md) preserves the failed DJ check and its measurements. Input prompt verification was not validation-based selection.

Commands below explain the historical workflow and require its external weights and Windows server installation. `doctor`, `status` and `technical-summary` inspect existing state. Launch commands load models and may occupy CPU, GPU and memory for long periods. A changed source revision cannot resume a frozen historical run.

## 1. Inspect the environment

Use Ubuntu/WSL. Paths below assume the archived experiment as the working directory and the pinned environment at the repository root:

```bash
cd /home/elio/Tesi-mqt-2.4-v2/archivio/esperimento_v2
LLM_OUTPUT="$PWD/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection"
../../.venv/bin/python -m llm_selection.cli doctor
../../.venv/bin/python -m llm_selection.cli status
```

`doctor` checks file presence; it does not rehash weights or prove that long prompts fit available resources. Before loading, SHA-256 is checked directly from Windows on the weights path, avoiding WSL cache reads. This may take minutes and records the method, fingerprint, size and duration.

The historical workstation kept BF16 and Q8_0 weights for Qwen3.5-4B, Phi-4-mini-instruct and Gemma 4 E4B-it. These are not clone contents. Its `models` link pointed to:

```text
D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models
```

Responses stayed in project artifacts. New Windows server/monitor logs used `server_logs` beside `models` on drive D, with per-run links at `servers/NAME-MODEL` in the project. Older records were not moved. This avoided durable Windows writes to the WSL share. D: disk capacity and WSL's assigned RAM are different resources. Preserve checkpoints, quarantined weights and earlier logs; inspect disk capacity with `df -h . /mnt/c /mnt/d` when needed.

The original engine used Windows, Vulkan and a 12 GB Radeon RX 6750 XT. MQT used the pinned Python environment. Only one LLM was loaded at a time.

## 2. Check hardware profiles on train

Technical commands submit the [shared compact prompt](compattazione_prompt.md), including repairs. For manual interaction, use the [chat guide](chat_locale.md).

Each command below processes five prepared train circuits without reading validation scores. Use fresh run names and run one command at a time. The profiles are starting points for checks, not final validated configurations. Qwen BF16 encountered the RAM limit. Phi initially considered BF16 with reduced cache, then Q8_0 under a new label if necessary. Gemma BF16 requires about 15 GB for weights alone, so its initial profile used Q8_0.

```bash
QWEN_TRIAL="qwen-technical-$(date +%Y%m%d-%H%M%S)"
../../.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label "$QWEN_TRIAL" \
  --precision Q8_0 --context 147456
```

```bash
PHI_TRIAL="phi-technical-$(date +%Y%m%d-%H%M%S)"
../../.venv/bin/python -m llm_selection.controller --technical \
  --model phi --label "$PHI_TRIAL" \
  --precision BF16 --context 114688 --cache-type q4_0
```

```bash
GEMMA_TRIAL="gemma-technical-$(date +%Y%m%d-%H%M%S)"
../../.venv/bin/python -m llm_selection.controller --technical \
  --model gemma --label "$GEMMA_TRIAL" \
  --precision Q8_0 --context 131072 --cache-type q4_0
```

`--precision` selects weight precision; `--cache-type` selects sequence-cache precision. A Q4 cache does not imply Q4 weights. Fewer `--gpu-layers` shift work to the CPU and may increase RAM needs. Profiles cannot change after freezing.

The default timeout is 3600 seconds per call, including process pauses. `--technical-timeout` affects technical checks without automatically changing the validation timeout. `--circuit dj_indep_tket_2` supports a single initial check, but freezing requires all five technical cases for the selected profile and at least one valid response. Preserve failures as well.

Progress appears approximately every 30 seconds. `prompt processing` describes input processing before response generation. `progress = 0.19` means 19% of that prompt, not 19% of the five checks. Tokens are not words. Speed is the phase average so far. The supervisor repeats the latest line when the server produces no new output, including during thermal pauses.

Inspect results from another terminal in the same directory:

```bash
../../.venv/bin/python -m llm_selection.cli technical-summary
../../.venv/bin/python -m llm_selection.cli status
```

Summaries include outcomes, calls and recorded stops. Details are under `controllers/NAME/`, `servers/NAME-MODEL/` and `technical_episodes/NAME/`. If the server stops, unprocessed cases remain pending. Completed cases are not repeated under the same identifier.

A RAM stop reports measured free memory, threshold and log path. The historical `qwen-prova-01` stopped on 14 September with 1.02 GiB free, below its 1.5 GiB limit, before generation. Python peaked at about 1.67 GiB and hotspot temperature was 52 °C. These observations concern feasibility, not response quality; the attempt remains preserved.

After a failed profile, change precision/cache only under a fresh name, update the corresponding trial variable and document both attempts. To resume an unchanged profile after a pause, use `--episode-label` as described below.

The initial encoding retained complete circuits and evidence. From 18 September, the minimal view retained features while omitting QASM, provenance and repetition from model text; originals stayed in records. Early measurements in `preparation/complete_graph_token_probe.json` included Gemma prompts exceeding native context. After compaction, each tokenizer/profile required new measurements. Context overflow fails before generation, reserving room for output and using the actual chat template.

Gemma E2B was an alternative to consider if E4B could not fit. This procedure did not install or select it automatically. Such a change required an updated experimental catalog before freezing.

## 3. Freeze profiles before scores

Assign the trial variables to the actual selected run names. When returning to a new terminal, read them from records rather than generating new names at this stage.

```bash
../../.venv/bin/python -m llm_selection.cli profiles \
  --qwen "$QWEN_TRIAL" --phi "$PHI_TRIAL" --gemma "$GEMMA_TRIAL" \
  --output "$LLM_OUTPUT/profiles_to_freeze.json"
```

Review the file and complete `precision_reason` with tried precisions, memory use, stops and reasons for the choice. Other fields must match technical records. An existing file is not overwritten.

Freezing checks five technical cases per family, a valid response, all 88 prompts and weight fingerprints. It rejects an already frozen study and validation decisions collected before freezing.

```bash
../../.venv/bin/python -m llm_selection.study freeze \
  --id local-llm-v1 --profiles "$LLM_OUTPUT/profiles_to_freeze.json"
```

The frozen study binds code, prompt, catalog, RAG index, parameters and dependencies. Do not delete its seal to rerun selection after observing scores.

| ID | Instructions | Temperature |
| --- | --- | ---: |
| p0_t0 | Base prompt | 0 |
| p0_t07 | Same base prompt | 0.7 |
| p1_t0 | Additional explicit checks | 0 |

Shared settings were five examples, at most three calls, timeout 3600 s, `top_p=0.95`, `top_k=40`, `min_p=0`, seed `20260913` and extended reasoning disabled. The output budget at the 15 September checkpoint was 4096 tokens, increased from 2048 in initial checks. Context, weight precision and memory settings were documented per model; the frozen record is authoritative.

## 4. Run validation

```bash
../../.venv/bin/python -m llm_selection.controller \
  --label "validation-start-$(date +%Y%m%d-%H%M%S)"
```

The grid has 792 episodes: three models × three settings × 88 circuits. Each allows at most three calls. The first valid response is final; subsequent calls repair invalid responses. The v1 procedure does not automatically retry transport failures.

The supervisor runs models sequentially, seals decisions, reads the existing Qiskit matrix, computes metrics, selects the local winner and generates reports. Earlier data remain if a phase fails.

Selection first maximizes valid, compilable choices on 88 cases. Ties use the lowest median absolute regret on the same comparable circuits, followed by first-call JSON validity, call count, measured time and tokens. Missing measurements do not become zero. No winner is invented if every candidate fails.

Runs may take hours or days; thermal pauses contribute to elapsed time. Technical checks are needed before estimating duration.

## 5. Inspect, pause and resume

From another terminal:

```bash
../../.venv/bin/python -m llm_selection.cli status
../../.venv/bin/python -m llm_selection.cli stop
```

`stop` finishes the current circuit, including its configurations and repairs, then closes the server. Wait until `status` shows `active_processes: []` and the main command returns.

Resume validation with a fresh supervisor label:

```bash
../../.venv/bin/python -m llm_selection.cli clear-stop
../../.venv/bin/python -m llm_selection.controller \
  --label "validation-resume-$(date +%Y%m%d-%H%M%S)"
```

The study stays the same; sealed models and completed episodes are skipped. To resume an unchanged technical profile:

```bash
../../.venv/bin/python -m llm_selection.cli clear-stop
../../.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label "qwen-resume-$(date +%Y%m%d-%H%M%S)" \
  --episode-label "$QWEN_TRIAL" --precision Q8_0 --context 147456
```

Keep all original hardware settings. Resume fills missing cases; it does not repeat completed ones. A changed profile requires a new technical run without `--episode-label`.

Ctrl+C interrupts the supervisor and requests server shutdown. An uncertain call remains a documented interruption rather than being silently repeated. An already saved complete response can be recovered and validated. After shutdown, use a new supervisor name and preserve incomplete files. Damaged writes may require artifact inspection.

On 15 September, the recorded defaults were hotspot pause at 105 °C, resume below 100 °C, stop at 108 °C hotspot or 95 °C edge, and free RAM below 1.5 GiB for three consecutive samples, sampled approximately once per second. Earlier 14 September instructions used different thresholds. Resume always uses the saved profile, not a later default. These are operational limits, not manufacturer specifications or a shutdown diagnosis. The monitor does not change voltage, clocks or fans. Later v2 settings are documented separately.

## 6. Rerun analysis only

After all models complete, if analysis was interrupted:

```bash
../../.venv/bin/python -m llm_selection.study seal
../../.venv/bin/python -m llm_selection.cli analyze
```

Sealing rejects missing decisions or changed artifacts. `analyze` reuses data without model calls. Analytical JSON is immutable; a new analysis producing different numbers is rejected.

To regenerate report sources and figures after selection:

```bash
../../.venv/bin/python -m llm_selection.report
```

`--sources-only` skips PDF compilation but still needs plotting packages. The report is not populated with invented results before runs.

## 7. Locate results and provenance

Paths are relative to `$LLM_OUTPUT`:

| Path | Contents |
| --- | --- |
| `models/` | External weights, provenance, revisions, precision and fingerprints. |
| `preparation/`, `technical/`, `incidents/` | Preparation, initial checks and historical interruptions. |
| `technical_episodes/` | Train checks, including rejected profiles. |
| `controllers/`, `servers/` | Commands, startup times, memory, temperatures, pauses and stops. |
| `code_snapshots/` | Exact sources used by runs. |
| `frozen_study.json` | Rules, settings and fingerprints fixed before scores. |
| `studies/ID/MODEL/CONFIG/CIRCUIT/` | Inputs, evidence, attempts, responses and decisions. |
| `studies/ID/analysis/episodes.csv` | One row per episode, including failures. |
| `studies/ID/analysis/trials.csv` | Nine-setting summary. |
| `studies/ID/analysis/selection.json` | Selection criteria, denominators and outcome. |
| `report/groups.csv` | Results by circuit family and qubit count. |
| `report/technical_episodes.csv`, `report/server_runs.csv` | Technical checks, rejected settings and stops. |
| `report/paired_uncertainty.json` | Paired comparisons and descriptive intervals. |
| `report/figures/` | Regenerable PNG/SVG plots. |
| `report/validation_selection.tex` | Thesis-ready fragment. |
| `report/standalone.tex`, `report/standalone.pdf` | Standalone source and PDF. |
| `report/preview/` | Page images for visual review. |
| `final_configuration.json` | Selected local configuration. |
| `selection_complete.json` | Verifiable selection-completion record. |

Original JSON/JSONL retains complete prompts and responses, evidence, errors, calls, repairs, tokens, times, resources and provenance. Missing fields stay null or blank. Memory maxima are sampled; Python's peak is cumulative for the process, not exclusive to one call. Reused Qiskit times are labeled historical. Whole-PC energy is not inferred from the ASIC sensor alone.

This selection updates local LLM roles only. It does not configure a frontier model, run validation `qcompile` or open the Test. The later no-RAG comparison and final evaluation have their own records.

## Historical checks and LaTeX setup

The 14 September delivery recorded 21 synthetic selection tests and four focused protocol checks, plus Python syntax, five PowerShell scripts and `git diff --check`. The report test generated temporary synthetic sources without real Test circuits, PDF compilation or plotting. Long-run feasibility and the real PDF were separate checks.

The historical report setup command downloads reporting dependencies:

```bash
../../.venv/bin/python -m llm_selection.setup_report
```

It installs Matplotlib, PyMuPDF and Tectonic in a separate artifact environment without changing MQT dependencies. Versions and provenance are recorded; the first compilation may download more TeX components.

To include a generated fragment, copy its source and figures and load `graphicx`, `booktabs`, `amsmath`, `seqsplit` and `hyperref`:

```latex
\newcommand{\ValidationFiguresPath}{chapters/validation/figures/}
% In the document body:
\input{chapters/validation/validation_selection.tex}
```

Inspect the compiled PDF and page previews before inclusion. Historical delivery checks do not replace verification of a newly generated document.

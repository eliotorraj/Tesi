# From initial setup to your own prototype

This guide walks through a new Linux campaign, from choosing inputs to evaluation and export. `configura.py` manages settings, checks values and preserves configuration revisions. `esperimento.py` runs the campaign phases.

To try the already selected system, use the [prototype guide](../../prototipo/docs/guida_passo_passo.md). This kit generates a new Dataset, selects settings on validation and exports another prototype. You supply any new circuits, GGUF weights, drivers and llama.cpp executable.

The main walkthrough uses an experiment named `cpu-trial`, Qwen and three Test methods. It is a reduced starting point for learning the commands. A suitable GPU is recommended for larger work: 16 GB of RAM does not guarantee enough memory for every circuit, model or context. One Target and one configuration cannot provide a meaningful comparison of alternative compilation choices. Once the workflow works, duplicate the experiment and expand its catalog.

<a id="come-leggere-i-comandi-della-guida"></a>
## Reading the commands

Run the two Python entry points from `riproducibilita/`. Arguments after the script name specify an action and its parameters. For example, after installation and input configuration, step 5 runs:

```bash
python esperimento.py --esperimento cpu-trial prepara
```

| Part | Meaning |
| --- | --- |
| `python` | The interpreter in the activated environment. |
| `esperimento.py` | The kit's phase runner. |
| `--esperimento cpu-trial` | The named configuration to use. |
| `prepara` | The requested subcommand: prepare and freeze inputs. |

Preparation checks inputs and saves the circuits, catalog and settings associated with that experiment. Freezing means that subsequent phases can detect changes to these conditions. To try different conditions, use another experiment name, optionally by duplicating the configuration.

“Before `prepara`” means before running that command in the terminal. Configuration comes first; Dataset generation, training and evaluation follow. Use `python esperimento.py --help` and `python esperimento.py prepara --help` to inspect the interface. Existing command identifiers remain unchanged for compatibility.

## 1. Install and check the Linux environment

Use Linux/Ubuntu or Ubuntu under WSL, Python 3.12, `uv`, Node.js 22/npm and a compatible llama.cpp executable. The [prototype guide](../../prototipo/docs/guida_passo_passo.md) covers prerequisites and the CPU build of llama.cpp b10930. For GPU builds, see the [Linux backends](../../prototipo/docs/installazione_e_runtime.md#gpu-su-linux).

From the clone root:

```bash
cd riproducibilita
bash setup.sh
source .venv/bin/activate
python esperimento.py verifica
```

All remaining commands run from `riproducibilita/` with this environment activated. In a new terminal, return to that directory and repeat `source .venv/bin/activate`. Alternatively, replace `python` with `.venv/bin/python`.

`setup.sh` uses the dependency lock with MQT Predictor 2.4.0 and installs TOON from the npm lock. It does not download weights, train models or recreate an existing environment. Before rebuilding `.venv`, preserve both canonical MQT artifacts and model copies installed inside the package. Node must be on `PATH`; `PROTOTIPO_NODE` can identify its executable explicitly.

## 2. Create a named configuration

```bash
python configura.py nuovo cpu-trial --profilo cpu --modelli qwen \
  --sistemi llm_rag llm_senza_rag random
python configura.py mostra cpu-trial
```

This creates `configurazioni/esperimenti/cpu-trial/` without changing the distributed reference settings. Multiple experiments can coexist. `mostra` lists active models, input paths, output locations and the maximum compilation-grid workload.

The CPU profile starts with a 16,384-token context, a 4,096-token output budget, batch 128, microbatch 64, zero GPU layers and one Qiskit worker. It does not reduce the circuit corpus, Targets, configurations or temperature grid. Reduce them explicitly for this walkthrough:

```bash
python configura.py dispositivi cpu-trial ibm_falcon_27
python configura.py compilazioni cpu-trial o2_default_default
python configura.py parametri cpu-trial --temperature 0
```

The protocol still requires three compilation seeds. With the supplied corpus, this reduced grid has up to 1,530 train/validation compilations before compatibility filtering. It is not an instant smoke test. To learn with fewer circuits, supply a smaller corpus in step 3.

<a id="se-usi-una-gpu-o-il-fisso"></a>
### GPU and desktop settings

There are two profiles:

| Profile | LLM computation | Weight storage |
| --- | --- | --- |
| `cpu` | CPU | System RAM |
| `gpu` | GPU for offloaded layers, with CPU support | VRAM for offloaded layers; RAM is still required |

`gpu_layers=999` requests all available layers, not literally 999 model layers. This does not guarantee that any GGUF fits in VRAM. If loading fails, choose a smaller model or explicitly offload fewer layers. Context and working buffers need memory in addition to weights.

Both profiles share the other initial settings: context 16,384, output budget 4,096, batch 128, microbatch 64 and one Qiskit worker. Change context with `modello --contesto` and Dataset compilation workers with `risorse --processi`, before preparation. Qiskit workers are not parallel LLM requests.

For a GPU machine:

```bash
python configura.py nuovo gpu-trial --profilo gpu
```

A desktop also uses `gpu`. To request the larger reference context and worker count, set them explicitly:

```bash
python configura.py nuovo desktop-trial --profilo gpu
python configura.py modello desktop-trial qwen --contesto 60000
python configura.py risorse desktop-trial --processi 6 --batch 512 --microbatch 128
```

These values are not inferred from the machine or GPU model. Check capacity first and use the chosen experiment name in subsequent commands.

All profiles initially use Linux `native` transport. If you retain the Windows server with a WSL client, set the WSL path to the same GGUF and select Windows transport:

```bash
python configura.py modello desktop-trial qwen \
  --file /mnt/d/path/to/Qwen3.5-4B-Q8_0.gguf --trasporto windows
```

Start Qwen with the personal Windows scripts described in the [prototype guide](../../prototipo/docs/guida_passo_passo.md). Those launchers and desktop sensors are model/host specific. Other LLMs need matching server settings. `esperimento.py server` launches Linux executables; its `--controlla` action can also inspect a Windows server through `curl.exe`.

## 3. Choose the circuits

No command is needed to retain the supplied 422 train, 88 validation and 90 Test circuits. Train contains 396 byte-distinct contents; aliases are preserved.

To use your own circuits, link a directory with three split subdirectories:

```bash
python configura.py circuiti cpu-trial --cartella "$HOME/trial-circuits" --crea
```

`--crea` only creates missing `train/`, `validation/` and `test/` directories. Place QASM files directly inside each split. The kit does not download or divide circuits, or modify the supplied corpus. Names must be unique across splits and each split must contain at least one circuit.

Do not place the same circuit in train and Test under different names. Preparation checks contents and instruction sequences, but cannot prove every quantum equivalence or independence between algorithm families. The fifty QASMBench circuits in `circuiti/esterni/` remain separate. To use them in a new split, copy the desired inputs and preserve their provenance.

## 4. Connect the GGUF and llama.cpp

Inspect the reference-model sources:

```bash
python configura.py disponibili modelli
```

Obtain the GGUF from the stated revision under its license. Store it at the configured default path, such as `modelli_llm/qwen/modello.gguf`, or link an existing file:

```bash
python configura.py modello cpu-trial qwen --file /path/to/Qwen3.5-4B-Q8_0.gguf
python configura.py risorse cpu-trial --server-bin /path/to/llama-server --threads 6
```

Replace example paths with real ones. Qwen, Phi and Gemma retain their expected reference hashes when their paths change. For another quantization or another LLM, register a new model with `aggiungi-modello`; see the [configuration cookbook](configurazione.md#register-another-llm).

A GPU backend can list its actual devices without loading the model:

```bash
python esperimento.py --esperimento gpu-trial server qwen --list-devices
python configura.py risorse gpu-trial --device DEVICE_ID_FROM_OUTPUT
```

Check the server log to confirm actual offloading. `999` is a request, not evidence of GPU use. No GPU model name needs to be replaced in the source code.

## 5. Check settings and prepare

Choose an external output root now if desired:

```bash
python configura.py risorse cpu-trial --risultati /path/to/results
```

Otherwise, output stays in the kit's areas, separated by experiment name. Review settings and inputs:

```bash
python configura.py mostra cpu-trial
python configura.py verifica cpu-trial
```

`configura.py verifica` checks split contents, names, byte-identical duplicates, active model files and GGUF hashes, and reports missing executables. It does not run inference or freeze the experiment. Hashing large files takes time. These checks do not establish memory capacity or arbitrary GGUF compatibility.

When inputs are ready:

```bash
python esperimento.py --esperimento cpu-trial prepara
python esperimento.py --esperimento cpu-trial stato
```

Preparation calls `prepare()` in [comune/corpus.py](../comune/corpus.py). It checks versions, Targets and split separation, parses QASM and extracts 49 features. Under `esecuzioni/cpu-trial/` in the chosen output root it writes:

- `circuits/`: copies of the assigned inputs.
- `manifest.json`: circuit features, provenance, splits and hashes.
- `catalogo.json`: quantum devices and Qiskit configurations.
- `contratto.json` and `ingressi_sigillati.json`: settings and fingerprints used for later integrity checks.

Dataset compilation and model training happen in later phases. Once the contract is written, the configurator protects the settings, even if a later preparation step fails. `stato` helps identify incomplete preparation. To change a choice:

```bash
python configura.py duplica cpu-trial cpu-trial-02
python configura.py parametri cpu-trial-02 --temperature 0 0.4 0.7
```

The copy inherits settings and input paths without copying results or presenting old training as new. Even with the same output root, it receives separate named subdirectories. Preserve the environment and source revision for resuming a run: source changes after freezing can make it incompatible.

`stato` remains available throughout. It lists artifacts, counts Test outcomes and suggests a next step. File presence alone does not certify success; the individual phases perform integrity checks.

## 6. Prepare MQT when selected

The `cpu-trial` walkthrough omits MQT, so continue to step 7. To include it in another campaign, declare it before preparation. `sistemi` replaces the entire method list:

```bash
python configura.py sistemi other-trial llm_rag llm_senza_rag random mqt
```

Installing MQT does not supply the trained policies and selector. After preparation, train one policy for every selected device. Inspect the catalog and start with one Target:

```bash
python esperimento.py --esperimento other-trial hardware
python esperimento.py --esperimento other-trial mqt rl --device ibm_falcon_27
```

Repeat the RL command for the remaining Targets. Training can be long. A request for 100,000 timesteps normally ends at 100,352 after completing the PPO rollout. Checkpoints and models go under `mqt/artefatti/<name>/`. A short smoke-training run verifies mechanics, not compilation quality.

After all policies are ready:

```bash
python esperimento.py --esperimento other-trial mqt selettore --dry-run
python esperimento.py --esperimento other-trial mqt selettore --compile-only --num-workers 1
python esperimento.py --esperimento other-trial mqt selettore --finalize-only --num-workers 1
python esperimento.py --esperimento other-trial mqt verifica
python esperimento.py --esperimento other-trial test tecnico-mqt
```

Collection compiles circuit/device pairs. Finalization builds the Training set and arrays, selects hyperparameters and trains the selector. Keep parameters consistent across the two phases. `mqt selettore --num-workers 1` can perform both. The technical check uses a synthetic Bell circuit without reading Test.

Trainer options are available through `mqt rl -- --help` and `mqt selettore -- --help`. Use the kit's `.venv`; environment checks protect the older repository installation. Trainer concurrency uses `--num-workers`, whereas `configura.py risorse --processi` controls Qiskit Dataset generation.

## 7. Generate the Dataset and validation matrix

```bash
python esperimento.py --esperimento cpu-trial dataset
```

This compiles train and validation across compatible devices, configurations and three seeds. It preserves errors, timeouts and compiled QASM. A configuration median requires all three seeds to succeed. RAG examples and normalization use train only.

Attempts go under `dataset/artefatti/<name>/`; the train package used by decisions goes under `esecuzioni/<name>/data/`, relative to the output root. Use `dataset --split train` and `dataset --split validation` to separate the work. The seal is created when both splits have all terminal attempts recorded, including failures. `dataset --aggrega` rebuilds aggregates without compilation.

Resume starts only attempts that have never begun. Interrupted attempts without an outcome become terminal; failures are not deleted to retry under the same name.

## 8. Run validation and select a candidate

```bash
python esperimento.py --esperimento cpu-trial validation congela
python esperimento.py --esperimento cpu-trial server qwen
```

The first command verifies all active GGUFs and freezes the grid. The second starts the server with its saved path, context, batch, threads and GPU layers. `cpu-trial` already has zero GPU layers. The terminal stays occupied; server records go under `esecuzioni/<name>/servers/`.

Open another terminal in the kit, activate the same environment, wait for loading and check the server:

```bash
python esperimento.py --esperimento cpu-trial server qwen --controlla
python esperimento.py --esperimento cpu-trial validation esegui --modello qwen
```

`--controlla` checks GGUF identity and exposed context without inference. If loading is still in progress, wait and repeat. If startup fails, inspect the server's `stderr.log`.

For multiple LLMs, stop the current server with Ctrl+C, start the next and repeat `validation esegui --modello ID`. Each command evaluates that model's temperature grid. The default port is shared, so run one candidate server at a time.

After all active candidates finish:

```bash
python esperimento.py --esperimento cpu-trial validation seleziona
python esperimento.py --esperimento cpu-trial validation report
python esperimento.py --esperimento cpu-trial stato
```

Decisions are sealed before their scores are read. The default rule ranks coverage, lower median regret on common circuits, fewer repairs/calls, complete time/token measurements and finally lexical order. Its reference is the best observed eligible median, not a theoretical optimum. Rejected candidates and denominators remain recorded. A single candidate still has validation measurements, but offers no comparison between candidates.

If the selected methods include `llm_wl` or `llm_wl_sintesi`, also run:

```bash
python esperimento.py --esperimento cpu-trial validation wl
```

This selects structural-retrieval depth from train and validation, without LLM inference or Test access.

## 9. Freeze and run Test

Start the selected model's server. MQT requires its trained artifacts and technical checks; WL requires retrieval selection. The initial walkthrough contains these three methods:

```bash
python esperimento.py --esperimento cpu-trial test congela
python esperimento.py --esperimento cpu-trial test esegui --metodo llm_rag
python esperimento.py --esperimento cpu-trial test esegui --metodo llm_senza_rag
python esperimento.py --esperimento cpu-trial test esegui --metodo random
python esperimento.py --esperimento cpu-trial test analizza
```

Run only the declared methods, preferably sequentially when comparing timings. Inspect alternatives with `configura.py disponibili sistemi`. The kit requires validation selection before Test freezing even if only Random or MQT is selected.

Every circuit receives an outcome. Errors, timeouts and interruptions remain visible. LLM records include prompts, evidence, requests, responses, repairs and measurable tokens. Missing scores remain missing; paired comparisons identify their common circuits.

Optional `test oracle` generates a separate reference grid that decision makers never read. It can require many more compilations than one method and is not needed to finish this walkthrough.

Reports go under `test/risultati/<name>/report/`. JSON and CSV need no LaTeX installation. Compile a standalone `report.tex` in its directory with `pdflatex -halt-on-error report.tex`, using a LaTeX distribution with PGFPlots. The validation report also includes a figure generated from stored data.

## 10. Export and preserve your work

```bash
python esperimento.py --esperimento cpu-trial esporta /path/to/new-prototype
python configura.py elenca
```

The export destination must be new. It receives the framework, train Dataset, catalog and selected configuration, including temperature, but no GGUF weights or validation/Test scores. It has its own README and setup and runs without the kit. The repository's supplied `prototipo/` remains autonomous.

Preserve settings, revisions, source, locks, every output area, server records and weights or verifiable sources. The kit does not commit or push; generated output and weights remain local. Continue with the [configuration cookbook](configurazione.md), [module map](mappa.md) and [experimental conditions](condizioni.md).

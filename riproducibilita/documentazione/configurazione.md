# Configure a campaign without editing JSON

Run these recipes from `riproducibilita/` after `source .venv/bin/activate`. Replace the example name `my-trial` with your own. If this is your first run, start with the [complete guide](guida.md).

`configura.py` changes settings; `esperimento.py` runs phases. Words such as `nuovo`, `mostra`, `prepara` and `dataset` are subcommands. “Before preparation” means before `python esperimento.py --esperimento my-trial prepara`, which freezes the experiment's inputs and settings. Command identifiers remain unchanged for compatibility.

## Create, inspect and duplicate settings

```bash
python configura.py nuovo my-trial --profilo cpu
python configura.py mostra my-trial
python configura.py elenca
python configura.py --help
python configura.py modello --help
```

A new experiment starts with Qwen and `llm_rag`, `llm_senza_rag`, `random`. The catalog initially includes all five Targets, twelve configurations and three reference temperatures. Profiles change initial resource settings only. To select models and methods immediately:

```bash
python configura.py nuovo gpu-comparison --profilo gpu --modelli qwen phi gemma \
  --sistemi llm_rag llm_senza_rag random llm_recupero_random mqt
```

The `cpu` profile runs the LLM on CPU with weights in RAM. `gpu` requests all possible layers on the GPU, using VRAM while still requiring CPU and RAM. Both start with context 16,384, output budget 4,096, batch 128, microbatch 64 and one Qiskit worker. Configure context, batches and concurrency separately; a desktop uses `gpu` with explicit resources. See the [profile guide](guida.md#gpu-and-desktop-settings).

Named settings live under `configurazioni/esperimenti/<name>/`. Each change creates a readable JSON revision and atomically updates `esperimento.json`. Rejected values leave the prior revision active. Commands do not delete revisions, results or weights, or publish to GitHub.

Once preparation writes the contract, further configuration changes are refused, including after a partial preparation failure. Duplicate the settings instead:

```bash
python configura.py duplica my-trial my-trial-02
python configura.py mostra my-trial-02
```

The copy includes settings and references to circuits/GGUFs, without results. If those source files change, the new experiment sees their contents at its own preparation time. Already frozen input copies remain separate. Protection also applies to prepared configurations using an external `--output` root.

## Select Test methods

```bash
python configura.py disponibili sistemi
python configura.py sistemi my-trial llm_rag llm_senza_rag random
```

`sistemi` replaces the entire list; it does not append implicitly.

| ID | Comparison | Additional prerequisite |
| --- | --- | --- |
| `llm_rag` | LLM with retrieved train examples | RAG Dataset and LLM selection |
| `llm_senza_rag` | LLM without retrieved examples | LLM selection |
| `random` | Random allowed device/configuration pair | Prepared catalog |
| `llm_recupero_random` | LLM with randomly sampled train examples | RAG Dataset and LLM selection |
| `mqt` | Supervised selector and RL policies | Training and `test tecnico-mqt` |
| `llm_rag_k1`, `llm_rag_k10` | RAG with one or ten examples | Enough eligible train examples |
| `llm_wl`, `llm_wl_sintesi` | Structural retrieval, without/with DAG summary | `validation wl` |

The kit follows Dataset → validation → selection → Test. Even a Random-only or MQT-only comparison currently requires validation selection before `test congela`. Omitting MQT removes its training prerequisite. Adding it declares intent; it neither starts training nor retrieves trained models automatically.

## Change the circuit corpus

```bash
python configura.py circuiti my-trial --cartella "$HOME/my-circuits" --crea
```

This links a directory; `--crea` creates missing split directories. Place `.qasm` files directly under `train/`, `validation/` and `test/`. Omit `--crea` if the split already exists. Existing files are not removed, and the kit does not generate or divide circuits for you.

Terminal paths are relative to the current working directory. The configurator stores kit-relative paths when possible, otherwise absolute paths. Quote paths containing spaces. Changing the corpus does not require changing schema fields.

## Select or extend the Qiskit catalog

The catalog describes synthetic quantum hardware and compiler options. Configure the host GPU under resources.

```bash
python configura.py disponibili dispositivi
python configura.py dispositivi my-trial ibm_falcon_27 quantinuum_h2_56
python configura.py disponibili compilazioni
python configura.py compilazioni my-trial o2_default_default o3_default_default o2_sabre_sabre
```

Both commands replace their lists. The first selected Target becomes the default. Target fingerprints come from the supplied reference and are checked during preparation. Standard configurations can be re-added by ID after exclusion.

To add a supported combination:

```bash
python configura.py aggiungi-compilazione my-trial o3_dense_basic \
  --ottimizzazione 3 --layout dense --routing basic --studio routing
```

The new ID must be unique and no longer than 64 characters; the combination must not already exist. Supported optimization levels are 2 and 3; layouts are `default`, `sabre`, `dense`, `trivial`; routing methods are `default`, `sabre`, `lookahead`, `basic`. `default` leaves the method unspecified in Qiskit. `--studio` is an analysis label (`baseline`, `layout`, `routing`), not a compiler argument.

A sixth Target or unsupported plugin/method requires coordinated code, schema and prompt changes. The configurator rejects unsupported choices. Custom combinations remain reusable while active; after excluding one with `compilazioni`, recreate it with `aggiungi-compilazione` to restore it. Its old definition remains in the revisions.

## Select registered models

```bash
python configura.py disponibili modelli
python configura.py modelli my-trial qwen phi
python configura.py modello my-trial qwen --file /disk/models/Qwen3.5-4B-Q8_0.gguf
```

`modelli` activates the selected registered candidates and deactivates the others, retaining their paths and parameters. Verification and validation freezing do not require inactive candidates' weights.

Changing a reference model's file path does not change its expected identity. Different contents fail the hash check. Register a new ID for different weights, including another quantization of the same model.

<a id="registrare-un-altro-llm"></a>
## Register another LLM

Obtain a GGUF compatible with your llama.cpp build, then record its source, revision and precision:

```bash
python configura.py aggiungi-modello my-trial my-llm \
  --file /disk/models/my-model.gguf \
  --fonte 'URL or verifiable source of the file' \
  --revisione 'identificativo-della-revisione' \
  --precisione Q4_K_M \
  --contesto 16384 --token-risposta 4096 --temperature 0 0.4
python configura.py modelli my-trial qwen my-llm
```

Replace placeholders with real values. Registration requires an existing local file and computes its SHA-256. Optional `--repository` records the base model repository when known. For locally produced weights, use an identifiable local revision and preserve the conversion procedure. The kit does not reconstruct missing provenance.

The candidate becomes active and inherits unspecified resources from the first active candidate, without inheriting its identity or hash. Review the summary: Qwen's context limit may not fit another model. Registration does not load the GGUF or certify compatibility, quality or memory capacity.

To change a registered candidate:

```bash
python configura.py modello my-trial my-llm \
  --contesto 8192 --token-risposta 2048 --temperature 0 0.2 \
  --timeout 1800 --url http://127.0.0.1:8090
```

The output budget must be smaller than context. Temperatures must be finite, non-negative and distinct; timeout is in seconds. Local native/Windows transports are supported, not remote providers. Sequential candidates can share a port.

## Set CPU, GPU and output resources

```bash
python configura.py risorse my-trial \
  --processi 1 --timeout-compilazione 100 \
  --threads 4 --gpu-layers 0 --batch 128 --microbatch 64 \
  --server-bin /path/to/llama-server \
  --risultati /disco/risultati
```

`--processi` and `--timeout-compilazione` control the Qiskit grid. Threads, GPU layers, batch and microbatch apply to all active model servers. Inactive candidates keep their prior settings; review them when reactivating. The MQT selector trainer uses its own `--num-workers`.

For a GPU backend:

```bash
python esperimento.py --esperimento my-trial server qwen --list-devices
python configura.py risorse my-trial --gpu-layers 999 --device GPU_ID
```

Use the backend's reported device ID. `--device auto` delegates selection to the backend; zero GPU layers cause the launcher to pass `--device none`. Fewer offloaded layers can reduce VRAM use, depending on model and hardware. There is no hard-coded GPU name to replace.

Use the same resource options with `modello` for one candidate, such as `modello my-trial qwen --threads 4 --gpu-layers 0`. `risorse` does not change context; use `modello --contesto`.

The output root is saved in the configuration and found through `--esperimento`, so later commands need no repeated `--output`. Keep resources constant during the campaign. Direct server arguments are recorded operational overrides; planned conditions belong in the configuration before preparation.

## Set temperatures, retrieval, seeds and selection

```bash
python configura.py parametri my-trial \
  --temperature 0 0.4 0.7 --k 5 --passi-rl 100000 \
  --seed 20260913 --seed-test 0 --seed-random 20260927 \
  --seed-compilazione 0 1 2 --wl 1 2 3 4 5 \
  --criterio median_regret
```

Specify only the options you want to change. Global temperatures apply to active candidates; `modello --temperature` sets an individual grid. `--k` accepts 1, 5 or 10, while the explicit Test variants retain their own `k`. WL retrieves five examples and selects depth among the supplied `--wl` values.

The protocol requires exactly three distinct compilation seeds. `--seed` controls LLM generation; `--seed-test` and `--seed-random` control their evaluation paths. Preserve the full settings: fixed seeds do not guarantee identical timings or determinism in every backend.

Selection supports `median_regret` or `mean_regret`, always prioritizing coverage. Lower-level generation settings remain in `configurazioni/generazione_llm.json`; editing them is an advanced operation to do before a campaign. There is no generic command to edit arbitrary schema fields.

## Check readiness without starting evaluation

```bash
python configura.py mostra my-trial
python configura.py verifica my-trial
python esperimento.py --esperimento my-trial stato
python esperimento.py --esperimento my-trial server qwen --controlla
```

| Command | Checks |
| --- | --- |
| `mostra` | Settings, paths, active candidates, counts and maximum grid workload; does not hash GGUF files. |
| `configura.py verifica` | Active inputs, names, byte-identical duplicates, GGUF hashes and server path; does not load models. |
| `esperimento.py verifica` | Kit installation and software components. |
| `stato` | Artifacts, prepared-input integrity when available and Test outcomes; suggests a next phase. |
| `server ID --controlla` | Identity and context of an already running server, without inference. |

Use `--help` on a command for supported options. Resolve missing inputs before preparation. After freezing, duplicate the experiment to change conditions; do not remove contracts or records to unlock it. See the [guide](guida.md) for execution order and the [conditions](condizioni.md) for interpretation and preservation.

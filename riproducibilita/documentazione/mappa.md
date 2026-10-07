# Module and data-flow map

Use this map to locate the implementation of a workflow step. The [guide](guida.md) explains execution order; the [configuration cookbook](configurazione.md) explains available settings.

## Entry points

- `configura.py` delegates to `comune/configuratore.py`, `configuratore_cli.py` and `configuratore_info.py`: validation, CLI parsing, summaries and atomic configuration revisions.
- `esperimento.py` dispatches campaign phases and selects a named configuration or explicit config/output paths.
- `comune/bootstrap.py` prepares local imports. Shared settings and path helpers resolve each experiment's output areas.

## Responsibilities

| Operation | Main implementation | Purpose |
| --- | --- | --- |
| Status | `comune/stato.py` | Inspect artifacts and integrity, summarize outcomes and suggest the next step without executing it. |
| LLM server | `modelli_llm/server.py` | Read the registry and launch/check the configured local runtime and CPU/GPU resources. |
| Corpus preparation | `comune/corpus.py`, `dataset/qiskit_dataset/core.py` and protocol helpers | Parse circuits, extract features, preserve provenance and check frozen inputs. |
| Catalog | `configurazioni/` and catalog helpers | Validate synthetic Targets and compiler configurations. |
| RL training | `mqt/addestra_rl.py` | Train device policies with checkpoints and action limits. |
| Supervised Training set | `mqt/addestra_selettore.py`, `mqt/` helpers | Compile circuit/device pairs, deduplicate sources, build arrays and train the selector. |
| Qiskit Dataset | `dataset/genera.py`, `dataset/qiskit_dataset/` | Run isolated attempts, aggregate medians and build train retrieval views. |
| Prompt preparation | `comune/framework/app.py:prepare` | Parse input, apply hardware eligibility, retrieve examples and encode the context. |
| Decision | `comune/framework/app.py:decide` | Call the LLM and validate the selected pair and facts. |
| Validation selection | `validation/seleziona.py` | Join sealed decisions with their evaluation matrix and apply the declared selection rule. |
| Retrieval variants | `comune/llm.py` and structural-retrieval helpers | Support Manhattan, random and WL retrieval and optional DAG summaries. |
| Test | `test/esegui.py`, worker and analysis modules | Execute declared methods and report terminal outcomes with explicit denominators. |
| Process and record handling | `comune/` | Enforce timeouts, atomic writes, frozen settings and terminal resume behavior. |
| Export | `comune/esporta.py` | Assemble the selected framework, catalog and train data as a standalone prototype. |

See the individual [folder READMEs](../README.md) for file-level navigation. Historical source snapshots in `archivio/` are not runtime dependencies of this kit.

## Data flow

```text
named configuration + circuits + catalog + software versions
                         |
                       prepare
                         |
             frozen inputs and experiment contract
                         |
        +----------------+---------------------+
        |                                      |
  MQT RL policies                      Qiskit train/validation grid
        |                                      |
  circuit/device Training set          train RAG Dataset + score matrix
        |                                      |
  supervised selector                  LLM validation decisions
        |                                      |
  technical Bell checks                frozen model/retrieval selection
        |                                      |
        +----------------+---------------------+
                         |
                  frozen Test methods
                         |
                outcomes and derived reports
                         |
             optional standalone prototype export
```

MQT training is required only when that method is selected. Validation and Test scores never enter the prompt for the same decision. The host GPU runs the LLM; the synthetic quantum Targets describe the compilation destination. These are separate kinds of hardware.

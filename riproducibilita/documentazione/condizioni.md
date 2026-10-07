# Conditions, limits and preservation

The kit makes the project's tools reusable. Each campaign generates its own results; historical scores are not imported as new measurements. Even with identical circuits, weights and seeds, timings, timeouts and LLM choices can vary with CPU, GPU, memory, concurrency and runtime.

The [current protocol](../../prototipo/docs/protocollo_sperimentale.md) remains the scientific reference. Scoring formulas and compilation checks derive from the original sources; interfaces now support configurable paths and corpus sizes. The default LLM selection rule prioritizes coverage and median regret. `mean_regret` is also available and must be declared before starting.

## Supplied reference conditions

The main corpus has 600 sources: 422 train, 88 validation and 90 Test. Train contains 396 byte-distinct contents. The original manifest preserves family and generator metadata. New files are identified as user-provided; no scientific family is invented. Hash and instruction-sequence checks prevent obvious split overlaps, but do not prove the absence of general quantum equivalences or shared algorithms.

The catalog contains five synthetic MQT Bench 2.2.3 Targets, twelve Qiskit configurations and seeds 0, 1 and 2. `expected_fidelity` multiplies operation fidelities from the Target, with MQT Predictor 2.4.0 rounding. It is not a measurement on physical quantum hardware. Qubit compatibility determines which attempts are possible.

`modelli_llm/provenienza_originale.json` identifies repositories, revisions, filenames and SHA-256 hashes for the Q8_0 Qwen, Phi and Gemma GGUFs. It does not independently attest the base revision of each conversion. The reference runtime is llama.cpp b10930. The supplied registry uses context 60,000, q8_0 cache, batch 512 and microbatch 128. Linux CPU, Vulkan/CUDA and the historical Windows desktop server are distinct execution conditions. Weights and runtimes are obtained separately under their licenses.

## Named configurations

`configura.py nuovo` creates settings separate from the distributed reference. It initially selects Qwen and three Test methods without MQT. CPU/GPU profiles use smaller context, batches and worker counts; CPU also uses zero GPU layers. These new conditions are visible in summaries and revisions and do not automatically reproduce the reference campaign. Reducing circuits, Targets, configurations or temperatures requires explicit choices.

The configurator accepts the Target/options subset supported by the schemas. It does not certify arbitrary GGUF compatibility or machine capacity. After preparation, change conditions by duplicating settings under a new name, preserving prior results.

## Execution differences to report

The kit keeps the facts v4 contract and three complete attempts, but does not reproduce the historical Windows thermal supervisor and automatic interruption recovery. Here, an interruption or transport error remains a recorded outcome without silent regeneration. Declare this difference when comparing costs or failures with earlier results.

A compatible GPU is recommended for inference. The indicative 16 GB minimum concerns an initial reduced prototype run, not every model or campaign. Declare a 16,384-token context, fewer workers or a smaller grid before freezing. `--list-devices` lists host devices through llama.cpp; IBM/Quantinuum catalog Targets instead describe synthetic quantum hardware.

The kit server records its executable, devices and arguments, but does not measure GPU temperature, memory or energy. Personal desktop PowerShell scripts retain AMD measurements; those measurements must not be attributed to generic Linux runs. WSL/Windows use requires explicit transport and verifiable access to the same GGUF.

The MQT trainer retains spawned workers and hash deduplication. Ordinary finalization requires full expected-sample coverage before publishing the selector. Comparisons with an incomplete historical collection, such as 384 samples with different timeouts, must state those conditions. A fully collected Training set produces a new artifact; it does not retroactively replace the evaluated selector. Smoke training does not demonstrate compilation quality.

Kit WL selection prioritizes coverage and minimizes mean regret of the best pair among five retrieved examples. This does not itself measure subsequent LLM decision quality. Freeze the selected retrieval configuration before Test.

Test supports LLM + RAG, no-RAG LLM, Random, random retrieval, MQT, RAG `k=1`/`k=10`, and WL with/without a DAG summary. The kit does not implement LLM fine-tuning or remote-provider execution.

## External corpus

The fifty QASMBench circuits remain separate: 30 small, 15 medium and 5 large, with a manifest, license and revision. To use them, create a new train/validation/Test directory, copy the desired inputs and link it in the configuration. QASM files must be directly inside their splits and have unique names. Keep the supplied `esterni/` copy intact.

This workflow regenerates data and selection under a new experiment ID. It does not justify using an external-Test result to choose a model retroactively.

## Preserve the evidence

Keep settings, source, dependency locks, all output areas, server logs and weights or verifiable revisions. Canonical RL policies live under `mqt/artefatti/<id>/models/rl`; the selector lives under `mqt/artefatti/<id>/modelli`. Installed copies inside `.venv` are operational copies and must match their canonical artifacts.

Summaries are derived products; attempts, prompts, responses and compilations are primary evidence. Do not replace failed outcomes with successes from later campaigns. Report seconds and tokens when measured. These launchers do not collect peak memory or energy; missing measurements remain explicit.

Weights, environments, indexes and new output are not automatically uploaded to GitHub. The clone contains inputs and procedures. Synthetic-server checks validate software; they are neither LLM experimental results nor MQT training.

## Common problems

| Problem | Action |
| --- | --- |
| Missing GGUF | Obtain the correct file or configure its existing path; weights are not included in the clone. |
| Unexpected GGUF hash | Restore the expected revision or register a new model deliberately. Changing a path does not change identity. |
| Empty split or duplicate name | Fix the corpus before preparation. |
| Prepared experiment cannot be edited | Use `duplica` and a new name; retain contracts and records. |
| Server executable missing | Set a Linux `--server-bin` and check executable permissions. |
| Server not ready | Wait for loading; if it exits, inspect the reported `stderr.log`. |
| Insufficient memory or context | Choose a smaller GGUF, fewer workers or another context in a new configuration. Preserve the failed outcome. |

The traditional `esperimento.py --config FILE --output DIRECTORY ...` and standalone `modelli_llm/server.py` interfaces remain available. Put `--config` and `--output` before the phase. The separate launcher reads `RIPRO_CONFIG` and `RIPRO_OUTPUT`. Named configurations are easier for ordinary use because they keep those paths aligned.

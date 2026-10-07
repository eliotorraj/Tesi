# Experimental protocol

This is the current protocol reference. The standalone application lives in `prototipo/`; new campaigns run through the autonomous [reproducibility kit](../../riproducibilita/README.md). Historical inputs, results and frozen sources remain in `archivio/`. The kit's [conditions](../../riproducibilita/documentazione/condizioni.md) identify operational differences from the recorded campaigns.

The reference environment uses Python 3.12, `mqt.predictor==2.4.0` and the exact versions in the relevant `uv.lock`. Historical MQT Predictor 2.3.0 material must not be treated as the current environment.

## 1. Evaluation unit and metric

The evaluation unit is a circuit. Compilation seeds and LLM repair attempts are repeated operations on that circuit, not independent additional samples.

The score is expected fidelity computed from fixed synthetic Target properties. It characterizes compilation choices under those properties; it is not a fidelity measured on physical quantum hardware. Missing scores remain missing rather than becoming zero.

## 2. Corpus and split roles

The supplied corpus contains 600 circuits: 422 train, 88 validation and 90 Test. Exact source-hash deduplication produces 396 train representatives for the RAG Dataset and the supervised Training set. Two two-qubit real-amplitudes/random circuits that are semantically equivalent but not byte-identical remain in train; hash deduplication is not semantic deduplication.

Use **Dataset** for the examples supplied to the LLM through RAG. Use **Training set** for circuit/device pairs used to train the supervised MQT selector. These have different roles even when derived from the same train circuits.

Train supplies examples, normalization and training inputs. Validation selects model, generation settings and retrieval parameters. Test evaluates the frozen selection. No decision may receive its own evaluation score or a validation/Test example as retrieval evidence.

For a custom corpus, create train, validation and Test splits before preparation. Preserve source and family metadata when known, and record missing provenance rather than inventing it. Hash and instruction-level checks do not establish algorithm-family independence.

The supplied Test has already been evaluated. Reusing it is a replication, not a new independent Test. Recorded pilot exposure includes `qpeexact_indep_tket_60` and `routing_indep_qiskit_12`; adaptive model choices and possible pretraining exposure to public benchmarks also limit independence claims.

## 3. Hardware and Qiskit search space

The reference catalog contains five MQT Bench 2.2.3 synthetic Targets, in this order: `ibm_falcon_27`, `ibm_heron_133`, `ibm_falcon_127`, `ibm_heron_156` and `quantinuum_h2_56`. Their fingerprints are checked before use.

The standard Qiskit catalog contains twelve configurations:

| Optimization level | Layout | Routing | Configuration ID |
| --- | --- | --- | --- |
| 2 | default | default | `o2_default_default` |
| 3 | default | default | `o3_default_default` |
| 2 | sabre | sabre | `o2_sabre_sabre` |
| 2 | dense | sabre | `o2_dense_sabre` |
| 2 | trivial | sabre | `o2_trivial_sabre` |
| 3 | sabre | sabre | `o3_sabre_sabre` |
| 3 | dense | sabre | `o3_dense_sabre` |
| 3 | trivial | sabre | `o3_trivial_sabre` |
| 2 | sabre | lookahead | `o2_sabre_lookahead` |
| 2 | sabre | basic | `o2_sabre_basic` |
| 3 | sabre | lookahead | `o3_sabre_lookahead` |
| 3 | sabre | basic | `o3_sabre_basic` |

`default` leaves the corresponding choice to Qiskit. The generation grid uses seeds 0, 1 and 2, a 100-second timeout per compilation and `num_processes=1` inside Qiskit. The reference catalog permits six external workers; new named CPU/GPU profiles start with one. Record the actual resources rather than assuming all profiles reproduce historical timings.

A configuration is eligible for its median score only when all three seeds succeed. The reference is the best eligible median observed in the measured grid, not a theoretical optimum. Preserve partial outcomes, errors and timeouts; do not retry failures until success under the same run identity.

## 4. RAG and the LLM decision

The selected retrieval representation has 49 features. Apply `log1p` to the 44 count/size dimensions and normalize each dimension by the maximum absolute train value, using one for a zero maximum. Leave the five bounded structural features untransformed before scaling. Fit no preprocessing on validation or Test.

The selected system uses Manhattan distance, Qdrant 1.19 and five train examples compatible with the input's hardware mask. Each example reports a winning device and up to three configurations for that device. Official TOON 4.1.1 encoding preserves the compact prompt view; raw QASM and extended provenance are excluded from that view.

The v4 decision consists of an allowed device/configuration pair, one or two checkable facts and a free-text hypothesis. Allow at most three LLM calls. Repair invalid facts on the first two; the third may accept a valid pair with unverified facts. Invalid schema or pair still fails. The hypothesis remains semantically unverified.

The selected reference model is Qwen in Q8 precision at temperature zero, using the `local-llm-v2` identity and its recorded configuration. The kit also registers Qwen, Phi and Gemma candidates with reference temperatures 0, 0.4 and 0.7. Record the exact GGUF hash, revision, quantization, backend, driver, context, output budget and thread settings. The reference context is 60,000 with a 4,096-token output budget and thinking disabled; new resource profiles can differ.

## 5. Validation and selection

Freeze the candidate grid before evaluating it. Seal decisions before reading their scores. Preserve every candidate, including rejected candidates, failures and incomplete cases.

The kit defaults to `median_regret`: first maximize coverage, then minimize median regret on common evaluable circuits, then prefer fewer repairs/calls, lower measured time and tokens when complete, and finally lexical order. `mean_regret` is also supported and must be selected before the campaign. These configurable kit rules must not be retroactively attributed to a historical selection that used different criteria.

For circuit `i`, regret is `R_i − S_i`, where `R_i` is the best eligible median observed in the reference grid and `S_i` is the selected pair's score. Zero median regret does not imply that every circuit received an optimal choice.

The kit's WL validation selects a depth by maximum coverage and then mean regret of the best pair among five retrieved examples. The historical structural-retrieval study used the first example and selected `h=24`; these are different procedures. Retrieval selection uses train and validation only.

Analyses of alternative `k`, Manhattan/WL retrieval and DAG summaries on the same Test are supplementary comparisons. They do not redefine the principal configuration selected on validation or provide a fresh independent Test for subsequent choices.

## 6. MQT Predictor preparation

The MQT Predictor 2.4.0 workflow uses the architecture with a supervised device selector and device-specific RL compilation policies. Distinguish it from the 2023 compilation-option predictor. Installing the package alone does not make `qcompile` ready for use.

Train and retain five RL policies and the supervised selector. Requesting 100,000 RL timesteps can produce 100,352 actual timesteps because training completes a rollout. Record both quantities.

The deduplicated reference Training set has 396 circuits and 1,878 compatible circuit/device pairs. Learn the classes actually present among winning devices; do not force a missing class such as `ibm_falcon_27` into the labels. Deduplication of supervised examples does not mean that RL uses an identical deduplicated input procedure.

The kit requires full Training-set coverage, canonical artifacts, runtime installation of the five policies and successful Bell checks for both RL and combined selector/RL compilation. A smoke-trained model verifies the pipeline only. It is not evidence of compilation quality. Preserve canonical and installed model copies before rebuilding an environment.

## 7. Test execution

The reference Test plan supports five main methods and four retrieval variants. New named configurations initially select `llm_rag`, `llm_senza_rag` and `random`, without MQT. Declare the intended methods before preparation; adding MQT also requires its training and technical checks.

The no-RAG method receives no retrieved examples and can use the hardware-capacity fact. Random selects an allowed pair with its recorded seed. LLM methods retain the three-call limit. Each selected Qiskit pair is compiled once per Test circuit with seed zero; MQT follows its separate compilation pipeline and broader action space.

Compilation timeouts run in isolated processes. Resume starts only work that has never begun; interrupted work without a final result becomes terminal. The kit does not silently recreate historical external supervisors or restart policies. An optional oracle grid is evaluated separately and is never read by the decision makers.

MQT's larger search space and the 100-second timeout make the comparison asymmetric. Report completion coverage separately from score comparisons on common successful circuits. Do not interpret missing MQT results as zero fidelity.

## 8. Measurements and reporting

Preserve raw decisions, prompts, responses, retrieval evidence, retries, seeds, versions, input/source hashes, resource settings and terminal outcomes. Report quality, coverage, causes of failure, total and phase timings, calls and measurable tokens. Use seconds for time and state the denominator of every aggregate.

Use common circuits for paired comparisons and retain explicit exclusions. Keep memory measurements separate from token counts and distinguish measured values from estimates or reused results. Linux kit records do not provide equivalent GPU power, temperature or energy measurements when those were not collected.

Versioned analysis generates JSON, CSV and standalone validation LaTeX reports and figures from stored results. These are descriptive comparisons unless an explicit statistical procedure is implemented and documented. Preserve figure provenance and the configuration selected by the declared rule.

## 9. Identity, preservation and deployment

Use a new `experiment_id` or a separate output root for each new campaign. Preparation freezes input and source identities; source or configuration changes after freezing require a new campaign rather than overwriting records or bypassing integrity checks. Frozen historical manifest paths are logical source references and must not be rewritten casually.

The exported prototype contains the selected framework, catalog and train Dataset, without validation/Test scores or GGUF weights. Its Bell demonstration verifies operation, not generalization. A 16,384-token CPU profile and a 60,000-token historical profile are different execution conditions. A machine with 16 GB of RAM may support small demonstrations, but that alone does not establish capacity for the full campaign.

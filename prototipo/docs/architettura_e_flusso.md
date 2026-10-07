# Architecture and execution flow

This document explains how the standalone prototype turns an OpenQASM 2 circuit into a device and compilation-configuration recommendation. For installation and commands, start with the [step-by-step guide](guida_passo_passo.md). For the experimental conditions, see the [protocol](protocollo_sperimentale.md).

## 1. Components and boundaries

`app.py` coordinates circuit parsing, 49-feature extraction, hardware eligibility, retrieval of up to five train examples, TOON encoding, local LLM inference and response validation. Compilation with the selected Qiskit configuration is optional. The prototype uses the selected LLM + RAG system; RAG is the retrieval technique within that system.

The hardware catalog contains synthetic MQT Bench Targets with fixed properties. It does not contact quantum hardware. Running the prototype does not require the trained MQT Predictor device selector or RL policies. Feature extraction uses the local `portable_features` implementation and retains its MIT attribution.

The main folders separate application modules (`prototype/`), train data and catalogs (`data/`), runtime files (`runtime/`) and new execution records (`runs/`). Feature extraction is in `portable_features.py`; runtime profiles are defined in `config.json`. The [module README](../prototype/README.md) and the repository's [reproducibility kit](../../riproducibilita/README.md) provide further navigation.

## 2. Input and parsing

The public command accepts a UTF-8 OpenQASM 2 file. Repeated `--device` options restrict the eligible devices. The internal `prepareUiSubmission` path retains an empty legacy `user_text` field; the public interface does not interpret a free-text hardware request.

The structured request model supports provider and device restrictions, minimum and maximum qubit counts, native gates and a hardware snapshot. The current CLI exposes the device restriction. `expected_fidelity` is the supported metric.

JSON input checks reject duplicate keys and non-finite numbers. The QASM input limit is 2,100,000 UTF-8 bytes. Only the `qelib1.inc` include is allowed. Parsing uses `qasm2.loads` with the supported legacy classical instructions and `strict=False`; these parser settings do not bypass the application's input checks.

A valid circuit must contain at least one qubit. Preparation records its width, depth, operation names, feature vector and source SHA-256. Non-finite features and invalid inputs fail before retrieval or inference.

## 3. The 49 circuit features

The vector contains 42 operation counts, the number of qubits, circuit depth and five structural features. Extraction does not first decompose every operation into a universal basis. An operation outside the 42 named counters has no dedicated count in the vector.

The structural features use a DAG with barriers removed. Let `n` be the number of qubits, `D` its depth, `gate_count` the number of gate nodes and `two_qubit_count` the number of two-qubit operations:

| Feature | Definition and boundary cases |
| --- | --- |
| `program_communication` | Sum of the degrees in the undirected two-qubit interaction graph, divided by `n(n−1)`; zero for one qubit. |
| `critical_depth` | Number of two-qubit operations on the longest DAG path, divided by `two_qubit_count`; zero when there are no two-qubit operations. The implementation identifies these operations by name. |
| `entanglement_ratio` | `two_qubit_count / gate_count`, with the empty-circuit boundary handled explicitly. |
| `parallelism` | `max(((gate_count / D) − 1) / (n − 1), 0)`; zero for one qubit or zero depth. |
| `liveness` | Number of active qubit/layer cells divided by `nD`, with the zero-depth boundary handled explicitly. |

The structural features are bounded between zero and one. The original circuit-depth feature and the barrier-free structural depth `D` are distinct quantities.

## 4. Hardware eligibility

`MqtHardwareCatalog` loads the MQT Bench Targets and checks the expected software versions, qubit counts, native operations, coupling maps and fingerprints. A catalog mismatch is an error. A Target that cannot otherwise be loaded is reported as unavailable.

`RequestSemanticValidator` checks request identifiers and the snapshot. The UI submission path also checks current bounds. Gate names are normalized, including `cnot` to `cx` and `i` to `id`. Duplicate restrictions, invalid intervals and conflicting provider/device constraints are rejected.

The hardware mask is a sorted list of device IDs satisfying all applicable restrictions: provider, explicit allowlist, circuit width, requested native gates, metric support and availability. An empty mask stops execution before retrieval. This does not imply that every input operation must already be native: the compiler can decompose operations for the selected Target.

The mask determines eligibility. It is not an anonymization step.

## 5. Train data and retrieval

The supplied RAG Dataset contains 396 deduplicated train records in the `global_multi_device` view. Loading checks the seal, train manifest, IDs, software versions, features, Target metadata, provenance and uniqueness of source hashes. Optional feature verification recomputes the vectors from the stored circuits.

Preprocessing applies `log1p` to the 44 count/size features and leaves the five structural features unchanged. Each dimension is divided by its maximum absolute value in train, or by one if that maximum is zero. There is no centering, clipping or L2 normalization. A new input can therefore exceed one in a dimension.

The local Qdrant index is generated under `runtime/rag/index/`. It stores float32 vectors. Existing indexes are checked against the manifest, software, record count, IDs and payloads. A new index is built in a temporary location, verified, reopened and then promoted atomically.

Retrieval filters by experiment, train split and metric. It also requires the historical winning device of an example to belong to the current hardware mask. Equal qubit count is not required. All eligible candidates are fetched and reranked with exact float64 Manhattan distance. Qdrant scores are checked with absolute tolerance `1e-5` and relative tolerance `1e-6`; equal distances are ordered by RAG record ID. The selected system retrieves at most five examples.

`LocalReferenceRetriever` and `DisabledRetriever` are explicit alternatives used by supporting code. They are not automatic fallbacks when Qdrant fails. The internal `prepare(rag=False)` option is not a public standalone CLI flag.

## 6. Prompt construction and TOON

Context construction checks the registry, historical rankings, labels and associated claims. An inconsistent record is rejected rather than silently dropped.

The compact prompt view includes the current circuit's name, qubit count, depth, operation counts and full feature vector; eligible hardware IDs and connectivity; the configuration catalog; and examples labeled `E1` to `E5`. Each example includes its winning device and up to three reported configurations for that device, with median scores and recorded ties. These are not three different devices.

The view omits raw QASM, source hashes, extended provenance, retrieval distances and the full registry. It retains `circuit_id` and family information, so it must not be described as anonymous. Input features are not rounded. Scores in the prompt belong only to train examples, never to the decision being evaluated. Local example aliases are mapped back to their records in the execution log.

TOON combines feature rows for the current circuit and examples. Connectivity can use an adjacency representation when ordering allows exact reconstruction; fully connected hardware has an explicit compact representation. The official TOON 4.1.1 package, run with Node.js 22, must round-trip the compact view exactly. This check applies to that view, not to fields deliberately omitted from the original context document.

The selected `facts` messages use the v4 response contract. Some internal compatibility components, including an intermediate `StructuredPromptBuilder` contract, retain v3 names. Their presence does not change the final messages sent in this workflow.

## 7. Local inference

Inference uses a local HTTP endpoint, with native or Windows transport as configured. Each attempt applies the chat template with thinking disabled, tokenizes the resulting input and requests a completion under the v4 contract. The selected configuration uses temperature zero and a maximum output of 4,096 tokens.

The historical reference profile has a 60,000-token context; the smaller CPU/GPU profiles start at 16,384. The client verifies that input tokens plus the reserved output budget fit the configured context. Requests use `stream=False`, even where a historical configuration retains a `stream` field set to true.

Temperature zero and a fixed seed do not guarantee identical results across backend versions or hardware. The [runtime guide](installazione_e_runtime.md) explains profiles, transport, memory checks and server logs.

## 8. Decision schema and facts

The v4 response has exactly these fields: `selected_device`, `config_id`, `facts` and `hypothesis`. It does not contain executable compiler code. Validation rejects unknown fields, duplicate keys and non-finite JSON values, and limits the response to 65,536 UTF-8 bytes.

There must be one or two distinct facts and a non-empty hypothesis of at most 1,000 characters. The selected device/configuration pair must exist in the allowed catalogs, and the device must have enough qubits.

| Fact type | What is checked |
| --- | --- |
| `selected_pair_among_reported_best` | The selected pair appears among the reported example configurations, including recorded ties. This does not mean it is a unique global optimum. |
| `selected_device_matches_example` | The selected device matches the referenced example. This makes no claim about its configuration. |
| `same_qubit_count_as_example` | The input and example have the same qubit count. This does not establish equal topology or performance. |
| `selected_device_has_enough_qubits` | The selected device can hold the input circuit. This fact has no `example_id` and makes no quality claim. |

A valid decision need not copy a train pair. The free-text hypothesis is not checked semantically. References to invalid example aliases are recorded as non-blocking hypothesis violations. Records therefore keep `explanation_fully_verified=False` and `hypothesis_status=not_semantically_verified`.

The schema validator implements the required subset of JSON Schema. Unsupported keywords are rejected instead of being assumed to work.

## 9. Attempts and acceptance

The system permits up to three complete LLM attempts. Repairs keep the same problem and provide structured validation feedback; they do not simply paste the previous raw answer into the next prompt.

A valid pair with verified facts is accepted. Invalid facts trigger a repair on the first two attempts. On the third, an otherwise valid pair can be accepted with `accepted_with_unverified_facts`. An invalid pair or schema still fails. Transport errors, insufficient context and truncated responses stop the standalone run; it has no automatic experimental supervisor or hidden retrieval fallback.

A decision accepted with unverified facts may still be compiled because its device/configuration pair passed the required checks. Toolkit execution contracts and recovery procedures must not be attributed to a standalone demonstration that did not use them.

## 10. Optional compilation

The selected configuration resolves locally to optimization level, layout and routing. The transpiler seed defaults to zero. Before compilation, the application rechecks metric and qubit compatibility, parses the QASM into a `QuantumCircuit` and transpiles against the selected Target. A default layout or routing method is omitted from the call so Qiskit can choose it.

Post-compilation checks allow barriers, verify the native basis with `GatesInBasis`, and check the coupling map with `CheckMap` when applicable. The record contains the compiled OpenQASM 2, depth, size, operation counts and effective parameters.

These checks do not constitute a formal equivalence proof. The standalone command does not execute the circuit on quantum hardware or report a measured hardware fidelity. It also does not compute the experimental expected-fidelity score.

## 11. Execution records

Each run receives a timestamp/random identifier and creates its JSON records exclusively, avoiding overwrite. The records cover:

- Start: input hash, profile, parameters, seed, software and source hashes, retrieval and prompt encoding.
- Attempts: HTTP requests and responses, measurable tokens and timings, context checks and validation feedback.
- Decision: selected pair, fact checks and hypothesis status.
- Optional compilation: effective options and compiled circuit.
- End or failure: the terminal outcome and associated error.

Standalone inputs are labeled `technical_prototype` and `user_input_not_experimental_test`. They do not automatically become experimental Test cases. Host memory and power consumption are not measured by this execution path.

## 12. Deployment boundary

Client setup installs the Python and Node.js dependencies, not a Windows or Linux LLM server. The server build, model weights, GPU backend and logs are separate runtime responsibilities. Historical AMD measurements refer to their recorded host; they are not measurements of a new Linux deployment. Use the [installation guide](guida_passo_passo.md) to configure the local runtime and the [reproducibility kit](../../riproducibilita/README.md) to run new campaigns.

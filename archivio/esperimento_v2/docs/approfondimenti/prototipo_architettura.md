# Historical quantum assistant architecture

This guide describes the typed-claim architecture recorded on 15 September 2026, including the 9 September v2 alignment. It explains the archived implementation and its decisions. The selected standalone prototype uses the later facts/hypothesis contract: see the [current architecture guide](../../../../prototipo/docs/architettura_e_flusso.md). For repository navigation, use the [main README](../../../../README.md).

<img width="1444" height="736" alt="Historical quantum assistant architecture" src="https://github.com/user-attachments/assets/74cb16d9-e73e-4484-ab68-6f6494885862" />

The [archived protocol](../protocollo_sperimentale.md) documents the historical rules. The Dataset source, relative to `archivio/esperimento_v2/`, is:

```text
datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/expected_fidelity/full/global/rag_examples.jsonl
```

## Purpose and flow

The assistant prepares a compilation recommendation for an OpenQASM 2 circuit. The user chooses a metric and may restrict eligible devices. Deterministic checks validate the request before Dataset retrieval or LLM access.

```text
structured request
  → format and circuit checks
  → hardware constraint checks
  → eligible-device mask
       → no eligible device: stop
       → eligible devices: search the Dataset
  → immutable registry of retrieved examples
  → LLM request
  → JSON response and evidence checks
       → invalid response with attempts left: retry
       → exhausted attempts: stop with an error
       → valid response: user confirmation
  → deterministic Qiskit compilation
```

In this historical contract, the model proposes a device, Qiskit configuration, typed claims and evidence references. It does not generate executable code, compile the circuit or write the explanation displayed to the user. The application renders that explanation from validated content. Compilation is a separate confirmed step.

At the time of this record, request preparation, catalog, masking, response checks, retrieval and compilation were implemented and could be tested with a simulated gateway. Connecting a real LLM and assessing recommendation quality were still future steps. Later studies and the selected prototype are documented separately; these historical statuses must not be read as the current project status.

## Files and responsibilities

Paths below are relative to `archivio/esperimento_v2/`.

| File or directory | Responsibility |
| --- | --- |
| `prototype/__init__.py` | Makes the prototype importable. |
| `prototype/quantum_assistant/models.py` | Request, catalog, mask, evidence, recommendation and compilation data structures. |
| `prototype/quantum_assistant/ports.py` | Interfaces between components, allowing catalog, retrieval and LLM implementations to change independently. |
| `prototype/quantum_assistant/errors.py` | Structured request errors. |
| `prototype/quantum_assistant/schema_validation.py` | Local JSON schema checks. |
| `prototype/quantum_assistant/services.py` | Preparation, retrieval, recommendation and compilation coordination. |
| `prototype/quantum_assistant/controller.py` | Operations for a UI and storage of validated recommendations. |
| `prototype/quantum_assistant/factory.py` | Local component wiring and replaceable LLM connection. |
| `prototype/quantum_assistant/__init__.py` | Public exports. |

Concrete implementations are in `prototype/quantum_assistant/adapters/`:

| File | Responsibility |
| --- | --- |
| `request.py` | JSON and OpenQASM 2 parsing, circuit features and normalized constraints. |
| `hardware.py` | MQT catalog and hardware mask. |
| `context.py` | Immutable evidence registry and model context. |
| `rag_features.py` | Feature order, train-fitted transformation and Manhattan distance. |
| `rag_dataset.py` | Permitted JSONL source, provenance and evidence checks. |
| `qdrant_context.py` | Persistent local database, nearest examples and explicit exhaustive reference implementation. |
| `rag_checks.py` | Checks all 88 validation cases through prompt construction. |
| `explanations.py` | Deterministic explanation from validated material. |
| `llm.py` | Configurable LLM gateway. |
| `validation.py` | Strict JSON, schema, catalog, mask, configuration, claim and evidence checks. |
| `compilation.py` | Confirmed `qiskit.transpile` call and output checks. |
| `parsing.py` | Imports retained for compatibility with the earlier prototype. |
| `__init__.py` | Public adapter exports. |

The related schemas are `assistant_request.schema.json`, `hardware_catalog.schema.json`, `hardware_mask_result.schema.json` and the historical `llm_recommendation.schema.json`. They describe the request, catalog snapshot, mask diagnostics and typed-claim recommendation. The last schema does not accept a free-form explanation.

Request checks are covered by `tests/test_request_constraints.py`; full-flow checks by `test_prototype_architecture.py`; response and retry checks by `test_llm_output_validation.py`; historical evidence checks by `test_claim_evidence_validation.py`.

## Structured request

Constraints are predefined fields populated from the catalog, not a free-text sentence. They allow provider and device restrictions, minimum and maximum physical qubit counts, and required native gates. `allowed_device_ids` is the only direct device allowlist; a complementary denylist is not accepted. Omit unused constraints. Present lists must be nonempty and unique. The supported metric is `expected_fidelity`.

```json
{
  "schema_version": "1.0.0",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "catalog_snapshot_id": "hardware_catalog_0000000000000000000000000000000000000000000000000000000000000000",
  "circuit": {
    "format": "openqasm2",
    "name": "bell",
    "source": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];"
  },
  "figure_of_merit_id": "expected_fidelity",
  "hardware_constraints": {
    "allowed_provider_ids": ["ibm"],
    "allowed_device_ids": ["ibm_falcon_127"],
    "device_qubits": {"min": 50, "max": 150},
    "required_native_gate_ids": ["cx"]
  }
}
```

The snapshot ID above is a placeholder. A real request must use the ID returned by the current catalog.

The first check requires one valid JSON object, with no duplicate keys, nonfinite values or unknown fields. Identifiers, types and lists must match the closed schema. The circuit must be valid OpenQASM 2 with at least one qubit, restricted includes and complete finite features.

The second check compares providers, devices, gates, metric, qubit range and snapshot identity with the catalog. Gate aliases are normalized; collisions are reported. Errors contain a code, field path and message. Invalid requests stop before Dataset or LLM access.

## Catalog and hardware mask

The catalog combines MQT Bench Targets with twelve Qiskit configurations. It records provider, qubit count, native operations, connectivity, Target availability, supported metric, usable configurations, versions and source fingerprints. Validation and masking use the same snapshot.

The mask combines every constraint, including the circuit's actual qubit count, which the user cannot reduce. A true entry means the device is eligible. `excluded_devices` contains diagnostics, not another user constraint. Reasons include an excluded provider/device, insufficient qubits, missing gates or an unavailable Target. An entirely false mask produces `NO_ELIGIBLE_DEVICE` without retrieval or an LLM call.

## Retrieval, recommendation and compilation

Default retrieval uses persistent local Qdrant on the v2 train JSONL only. It filters experiment, objective and allowed winning devices before selecting `k`. Manhattan distance uses 49 features: `log1p` for counts, depth and qubits, identity for indicators, followed by division by each train maximum absolute value, or 1 when that maximum is zero. There is no centering, clipping or L2 normalization. Validation and user requests do not refit divisors.

Qdrant distances are checked against the float64 formula with absolute tolerance `1e-5` or relative tolerance `1e-6`. All filtered candidates are retrieved and sorted by canonical distance and RAG ID, including ties at the `k` boundary. Embedded search is exhaustive, without HNSW or payload-index acceleration.

The model context includes the circuit and features, objective, eligible hardware, retrieved examples, citable evidence registry, twelve permitted configurations and response contract. A concrete model connection is injected. Local simulated and explicitly unconfigured gateways support technical checks.

The historical response must match the request, schema version and catalog snapshot; choose a masked-in device; use `expected_fidelity`; and select a configuration allowed for that device. Reasons are typed claims, parameters and evidence IDs. After validation and confirmation, `qiskit.transpile` runs the selected plan. The output must respect the Target's operations and connectivity.

## Response checks and retries

The gateway may return JSON text, UTF-8 bytes or a parsed object. Text must contain exactly one JSON object. Extra prose, Markdown fences, multiple objects, duplicate keys and nonfinite values are rejected. Nested `qiskit_plan`, `claims` and `evidence_refs` are also closed schemas.

The immutable evidence registry is built once from the retrieved examples. It retains complete labeled records, historical results, configurations, source claims and scientific caveats. Earlier-format records can provide context but cannot support typed historical claims.

Each response reference must resolve the full record/source-claim/evidence relationship and match the recommended device and configuration. References cannot be invented, duplicated, unused or shared by multiple output claims. With historical results, the response must support both choices and include one current-compatibility claim. Without history, only current compatibility and structured evidence-unavailability claims are permitted.

`explanations.py` renders the final explanation exclusively from validated references and claims. Caveats identify results as observations on historical circuits, not measurements of the current request.

Repair feedback contains only code, path and message. Claim/reference errors can trigger retries, up to three total attempts by default. Invalid requests, inconsistent Dataset/catalog data, no eligible devices and gateway failures do not enter this retry policy. Exhaustion returns `LLM_OUTPUT_VALIDATION_EXHAUSTED`. The normalized request, mask, retrieved examples and registry remain unchanged between attempts. Compilation accepts only a validated recommendation issued by the same service instance.

## v2 alignment decisions

The parser accepts the Dataset pipeline's OpenQASM instructions, including `u`, `cry` and `cp`. Includes are limited to Qiskit's `qelib1.inc`. Default components use `configs/qiskit_dataset_configurations_v2.json`; an explicit catalog can still be supplied. Target hashes use the v2 pipeline function and are checked against frozen values. Version or Target mismatches stop the service.

The hardware catalog contract became `2.0.0`, with snapshot fingerprint schema `assistant-hardware-catalog/3` and Target schema `qiskit-dataset-target/2`. Requests remained `1.0.0`, but must acquire a new snapshot after this change.

Manhattan replaced the earlier mean of `abs(q[i]-c[i])/(1+max(abs(q[i]),abs(c[i])))`. These formulas are not equivalent; the old formula is not a fallback. The default five examples are distinct from the three configurations stored for each winning device.

Examples retain the winning device only; other devices are not added to balance labels. If constraints exclude every historical winner, the registry remains empty. This does not mean the requested device is unusable.

The 396 train examples were retained. `realamprandom_indep_qiskit_2` and `realamprandom_indep_tket_2` share a semantic fingerprint and both belong to train. This can double-weight that precedent in retrieval; the recorded design accepted that redundancy. File-hash, semantic-hash and circuit-group separation checks remain active. This is not a completed general audit of all equivalent or nearly equivalent circuits.

## Qdrant commands

From `archivio/esperimento_v2/`, with the repository-root environment:

```bash
../../.venv/bin/python scripts/17_rag_v2.py prepare
../../.venv/bin/python scripts/17_rag_v2.py verify
../../.venv/bin/python scripts/17_rag_v2.py validation
../../.venv/bin/python scripts/17_rag_v2.py query --qasm /path/to/circuit.qasm --k 5
../../.venv/bin/python scripts/17_rag_v2.py query --qasm /path/to/circuit.qasm --k 5 --backend reference
```

`build_default_service` accepts `retrieval_backend="qdrant"` (default), `"reference"` or `"none"`; `retrieval_limit` sets `k`. `none` deliberately disables retrieval. The historical `dataset_required` argument remains accepted for compatibility, but missing active-retrieval inputs always fail. A Qdrant error does not silently select the reference implementation.

JSONL remains the source. Manifest, transformation and database are under `artifacts/experiments/<experiment_id>/rag/index/`. Repeated `prepare` checks an existing collection without adding points. Preserve an inconsistent collection before explicitly rebuilding it. Consult the archived protocol for its transfer procedure; use the autonomous toolkit for new campaigns. Zero compatible examples is a valid outcome; database errors and altered collections stop the flow. These technical checks do not measure LLM quality.

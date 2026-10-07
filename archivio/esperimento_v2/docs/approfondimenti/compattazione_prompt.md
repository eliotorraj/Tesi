# Minimal assistant prompt: historical v3 design

This guide documents the prompt introduced on 18 September 2026 and its TOON revision, `minimal-v3-toon1-20260919`. The selected prototype subsequently adopted the v4 `facts`/`hypothesis` response. Use the [current architecture guide](../../../../prototipo/docs/architettura_e_flusso.md) for that system and the [v2 selection guide](../../llm_selection/v2/README.md) for the later study.

The earlier measurements below concern reducing JSON content. The [TOON report](../resoconti/2026-09-19_prompt_toon.md) measures the additional encoding savings on five train circuits for all three models. Prompt data use TOON; the response schema and required response remain JSON.

## What the model sees

The program still prepares the complete request and preserves QASM, original identifiers, manifests and the evidence registry. It derives a smaller view before transmission:

- The current circuit with all original numerical features.
- The normalized objective and constraints.
- Compatible devices and allowed configurations.
- Five examples in retrieval order.
- For each example: circuit and features, compatible device names, winning device and the first three ranked configurations, including their device association, historical median and recorded ties.

Features are not rounded, and zeros remain present. The model does not receive QASM, hashes, manifests, data versions, duplicate evidence registries or repeated hardware descriptions inside examples. Historical results are not measurements of the current circuit.

Complete topology is represented explicitly without listing every edge. Other topologies retain all directed links. TOON may group links by source qubit only when the transformation also preserves original edge order. Features become a table with columns for the current circuit and examples. The encoding is decoded and compared with the minimal view before transmission. A full per-device configuration list is omitted when every device accepts the catalog; restrictions remain explicit.

## Historical v3 response and checks

The v3 response has four fields:

```json
{
  "selected_device": "ibm_falcon_27",
  "config_id": "o2_default_default",
  "claim": "A brief explanation of both choices, based on the cited examples.",
  "evidence": ["E2", "E4"]
}
```

This is a format example, not a Qwen response. The program records version 3.0.0; the model does not repeat it. Qiskit parameters come from the catalog, using the protocol's first seed, 0. Choices are not silently repaired.

E1–E5 are local aliases assigned in retrieval order. Their mapping stays fixed during repairs and is not sent to the model. Citation context also binds the request identity, catalog, registry fingerprint and actual request fingerprint. It checks sources, objective, constraints and features so a mapping from another request cannot be reused.

The validator checks format, device compatibility, allowed configuration and membership of citations in the supplied examples. Unknown and duplicate references are rejected. Historical results require at least one citation; no-RAG requests require an empty list. One example can support both choices. Separate claim and caveat identifiers are unnecessary in v3.

**Resolving a citation does not verify free-text semantics or prove that the model causally used that example.** Recommendations and caveats record this limitation. The earlier multilevel checks do not apply to v3's free claim. Compilation still requires a recommendation issued and validated by the service and explicit confirmation.

## Files and records

The view is implemented in `prototype/prompting/minimal.py`, and rendering in `prototype/prompting/rendering.py`. The external contract is `schemas/llm_recommendation_v3.schema.json`. The schema shown in instructions also constrains generation.

Each attempt preserves the complete `prompt.json`, `encoding.json` with revision and mappings, the actual request and the original response. The validated recommendation retains aliases and resolved original IDs.

From `minimal-v3-repair1-20260918`, feedback uses short sentences in `previous_validation_errors`, without long codes or copies of the previous response. Each error type appears once:

- Choose `selected_device` from the compatible hardware IDs.
- Choose `config_id` from the configuration catalog, respecting the selected device's constraints.
- Use valid, distinct example IDs for evidence, with at least one reference when history is supplied; otherwise use `[]`.

A final sentence asks for the complete JSON for the current circuit. Other format errors refer to the schema. Repairs resend the full reduced context with unchanged examples and aliases; the first attempt remains unchanged. Canonical logs preserve original codes and details. Arbitrary values from an invalid response are not inserted back into the prompt.

Runs from a different revision cannot resume under the new feedback, even if their first prompt matches. Changed instructions require a fresh run name; earlier outcomes are not overwritten.

The v2 format remains readable through `compact.py`, `legacy_rendering.py` and its historical validator. `legacy_contract=True` explicitly reconstructs earlier checks. At this stage, the normal path used v3; reconstructing the canonical document from the reduced view was unnecessary.

## Measurements from 18 September

Three train cases were compared without inference:

| Circuit | Tokens before | Tokens after | Reduction |
| --- | ---: | ---: | ---: |
| dj_indep_tket_2 | 34318 | 11667 | 66.00% |
| ae_indep_qiskit_60 | 75193 | 11382 | 84.86% |
| portfoliovqe_indep_qiskit_6 | 36265 | 12692 | 65.00% |

Counts use `llama-tokenize.exe` b10930 and the same Qwen Q8_0 GGUF as the reference. The native template reproduces the archived request: one user message, no tools and reasoning disabled. For the first case, the entire token-ID sequence was checked against the original server output, not just the count.

The first reference was an actually submitted request. The other two were reconstructed using v2. New requests were prepared and counted, not submitted. The readable schema is included in the counted text; the separately supplied `json_schema` constrains llama.cpp generation without adding prompt tokens. Section counts are diagnostic and need not be additive.

These are not quality, latency or memory measurements. Some train examples include the same circuit, so the checks do not demonstrate generalization. This audit did not start validation selection or open the Test.

Data, requests and logs are preserved under:

```text
artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/prompt_minimal_v3/
```

The path is relative to `archivio/esperimento_v2/`. Reproduction tools are `llm_selection/minimal_audit.py` and `llm_selection/tokenize_files.ps1`. Preparation, local token counting and audit completion are separate steps. Use a new destination directory.

The earlier 16 September centralization and reversible encoding remain documented in their own artifacts; their results are not attributed to this revision. Real retrieval and old train-prompt compatibility were checked for all three cases. Responses constructed from historical labels passed the validator; they were not new LLM responses. The historical delivery reported 236 passing tests and retained the initial failures corrected before delivery.

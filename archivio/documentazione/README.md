# English guide to frozen README snapshots

This directory provides English navigation for README files embedded in frozen experiment artifacts. Their original files remain unchanged because they belong to source snapshots, before/after comparisons or generated report bundles. Altering them would invalidate recorded fingerprints. Use the current [prototype guide](../../prototipo/docs/guida_passo_passo.md) or [experiment toolkit](../../riproducibilita/README.md) for new work.

The entries below explain where these snapshots belong. They do not turn historical commands or statuses into current instructions.

## Post-validation audit of local-llm-v1

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/post_validation_audit_20260919/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/post_validation_audit_20260919/README.md).

This September 19 audit examines the completed `local-llm-v1` study, whose recorded winner was `qwen/p0_t07`. It does not change that study or the later facts v4 selection. Of 792 episodes, 789 responses were accepted on the first attempt and three failed in transport after resource-monitor shutdowns. Application acceptance did not certify the explanations.

`audit.py` extracts attempts and integrity checks; `review.py` groups and reviews claims. `attempts.*`, `reviewed_attempts.*`, `claim_groups.json`, `review_notes.json` and `summary.json` expose the analysis. `transport_failures.json` and prompt comparison files separate transport issues from content observations. Inputs and checks are recorded by fingerprints.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Minimal prompt v3 audit

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/prompt_minimal_v3/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/prompt_minimal_v3/README.md).

This directory records the September 18 `minimal-v3-20260918` revision with response schema 3.0.0. It retained full features, catalog and five train examples while moving QASM and provenance out of the model text. This revision predates TOON and facts v4.

`native_counts_final/report.json` contains the final tokenizer measurements; `native_counts/` preserves preliminary measurements. Qwen input counts fell from 34,318 to 11,667, 75,193 to 11,382 and 36,265 to 12,692 for the three audited train examples. Checks, test logs and example provenance are stored alongside them. These are prompt measurements, not new Test outcomes.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Compact repair-feedback revision

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/README.md).

This records `minimal-v3-repair1-20260918`, which sends a complete reduced prompt again after an invalid response and groups feedback by device, configuration or evidence error. The maximum remains three responses with the same five examples.

`before/` and `after/` preserve source revisions; `changes.diff` describes the change. `checks.json` and test logs document validation. `phi_example/` and its preparation script preserve a technical example. Raw error codes remain in canonical records; the shorter model-facing feedback does not erase them.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Prompt snapshot after repair-feedback changes

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/after/prototype/prompting/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/after/prototype/prompting/README.md).

This source snapshot contains `minimal.py` and `rendering.py` for `minimal-v3-repair1-20260918`. It builds the compact view, E1–E5 aliases, schema v3 messages and grouped repair feedback. Full QASM and provenance remain in canonical records.

The snapshot documents this specific revision; it is not the current facts v4 implementation or a standalone installation. The enclosing analysis contains the before/after diff and checks.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/README.md) · [Current repository guide](../../README.md)

## Prompt snapshot before repair-feedback changes

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/before/prototype/prompting/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/before/prototype/prompting/README.md).

This source snapshot contains `minimal.py` and `rendering.py` for `minimal-v3-20260918`, before grouped repair feedback. It documents compact prompt content, E1–E5 references and schema v3 response handling. The enclosing analysis preserves the corresponding change and checks. It is historical source evidence, not a separate application.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/repair_feedback_v1/README.md) · [Current repository guide](../../README.md)

## LLM selection snapshot after TOON integration

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/after/llm_selection/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/after/llm_selection/README.md).

The retained files document provenance, codec setup and token auditing after TOON integration on September 19. `setup_toon.py` prepares the codec, while `toon_audit.py` and `toon_report.py` measure and report prepared prompts. This partial source snapshot does not contain a complete runnable workspace. See its enclosing analysis and the current toolkit for their respective uses.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Prompt snapshot after TOON integration

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/after/prototype/prompting/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/after/prototype/prompting/README.md).

`minimal.py` and `rendering.py` build the historical minimal-v3 view; `toon.py` and `toon_runtime/` add reversible TOON encoding with the pinned official codec. The revision is `minimal-v3-toon1-20260919`; input data use TOON while schema and response remain JSON.

This snapshot preserves the integration stage. The selected prototype uses the later facts v4 response policy.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## LLM selection snapshot before TOON integration

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/before/llm_selection/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/before/llm_selection/README.md).

This partial snapshot preserves `provenance.py` and the documentation state before the September 19 TOON change. It belongs to the enclosing before/after analysis and is not a complete LLM selection installation. The full archived selection code is under `archivio/esperimento_v2/llm_selection/`.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Prompt snapshot before TOON integration

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/before/prototype/prompting/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/before/prototype/prompting/README.md).

`minimal.py` and `rendering.py` preserve `minimal-v3-repair1-20260918`: compact JSON input, schema v3 responses and grouped repair feedback. The adjacent `after/` snapshot adds TOON encoding. These files document source history rather than a new experimental result.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Native token counts on five train circuits

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/native_counts/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/native_counts/README.md).

`qwen/`, `phi/` and `gemma/` store model-specific tokenizer evidence. `report.json` summarizes counts; manifests and metadata identify the prepared requests. Reduced JSON inputs are checked against archived token IDs, while the earlier v2 representation is reconstructed with its match status recorded.

TOON counts include the full template and schema. They measure prepared input tokens without inference and do not measure output or future repair tokens. The sibling report explains the comparison.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Original, reduced and TOON prompt comparison

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/report/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/report/README.md).

`index.html` presents the token comparison; `confronto_token.png` and `.svg` provide the chart. It covers five train circuits with five retrieved examples, without new inference. Full source counts are in the sibling `native_counts/` directory.

Qwen totals are 328,123 for earlier v2 input, 60,687 for reduced JSON and 55,762 for TOON. Phi totals are 269,360, 46,844 and 44,670; Gemma totals are 343,014, 64,578 and 58,249. Tokenizers differ by model. These reductions concern input representation, not compilation quality or future response cost.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Explained local-llm-v2 validation report

Original: [archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/studies/local-llm-v2/report_explained/README.md](../../archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/studies/local-llm-v2/report_explained/README.md).

`standalone.pdf` is the compiled report; `validation_selection.tex` is the thesis-ready text; `figures/` holds PNG/SVG figures. `model_costs.csv`, `model_costs.json` and `trial_details.csv` contain numeric summaries. `provenance.json` identifies inputs and generator. The adjacent original `report/` is a separate artifact.

This September 20 explanation clarifies seed versus circuit medians, fact denominators, repairs, time and token counts. Regret means in this report are descriptive and do not rewrite its frozen selection. The historical generator is `scripts/report_local_validation_v2.py` in the archived experiment workspace.

[Parent directory](../esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) · [Current repository guide](../../README.md)

## Earlier incremental-report generator

Original: [archivio/valutazione/rag_incrementale/verifiche_sviluppo/report_mqtbench90_formato_qasmbench50_20261003/precedente/report/README.md](../../archivio/valutazione/rag_incrementale/verifiche_sviluppo/report_mqtbench90_formato_qasmbench50_20261003/precedente/report/README.md).

This snapshot preserves the report generator before the October 3 layout revision. `genera.py` reads completed, verified campaign records and writes JSON, CSV, LaTeX/PDF, figures and provenance into a new output directory.

The earlier presentation emphasized cumulative differences and memory growth. It is source history for existing reports, not the current generator entry point. The enclosing revision record explains the replacement and its checks.

[Parent directory](../valutazione/rag_incrementale/verifiche_sviluppo/report_mqtbench90_formato_qasmbench50_20261003/README.md) · [Current repository guide](../../README.md)

## Structured-fact supplement

Original: [archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/README.md](../../archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/README.md).

`analisi_fatti.pdf` and `.tex` analyze 90 final decisions for each of three LLM systems, including earlier attempts: 418 checked responses in total. Free hypotheses are not semantically validated.

`audit_fatti.json`, `audit_fatti_esteso.json` and `campione_fallimento.json` contain counts and illustrative responses. `revisioni/` preserves earlier presentations; `verifica_finale.json` and `controllo_visivo/` record checks. The random-retrieval campaign has 35/90 fully valid final responses and 125/180 valid final facts in this saved analysis. Raw responses and evidence aliases retain their original content.

[Parent directory](../valutazione/test/report_generati/README.md) · [Current repository guide](../../README.md)

## Earlier fact-supplement revision

Original: [archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/revisioni/campione_fallimento_20260928T001622Z/README.md](../../archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/revisioni/campione_fallimento_20260928T001622Z/README.md).

This revision preserves a five-page, two-method supplement with three examples before the later random-retrieval extension. `audit_fatti.json` stores counts, attempts, sample responses and source fingerprints; `analisi_fatti.tex` and `.pdf` hold the presentation. `revisione.json` and `verifica_finale.json` identify the revision.

Use the parent supplement for the later analysis; this directory retains the earlier state rather than additional experimental outcomes.

[Parent directory](../valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/README.md) · [Current repository guide](../../README.md)

## Fact-supplement revision before extension

Original: [archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/revisioni/due_evidenze_random_20260928T002632Z/README.md](../../archivio/valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/revisioni/due_evidenze_random_20260928T002632Z/README.md).

This snapshot preserves the two-method supplement and its invalid-fact example before the later presentation with two distinct evidence records and random retrieval. `audit_fatti.json` and `campione_fallimento.json` hold the evidence; LaTeX/PDF and revision/verification files preserve the presentation.

The parent supplement indexes the later version. Free hypotheses remain unvalidated text, and saved examples are not corrected into new model outputs.

[Parent directory](../valutazione/test/report_generati/30dd5b4f737c058e/analisi_fatti/README.md) · [Current repository guide](../../README.md)

## Original four-system report generator snapshot

Original: [archivio/valutazione/test/report_generati/30dd5b4f737c058e/generatore/README.md](../../archivio/valutazione/test/report_generati/30dd5b4f737c058e/generatore/README.md).

These Python modules and LaTeX fragments are the generator revision associated with report `30dd5b4f737c058e`. Historical paths in the source refer to its original repository layout. The snapshot alone is not a standalone installation; reproducing it requires its matching input records and environment.

The maintained archive report entry points are under `archivio/valutazione/test/report/`. This copy establishes how the stored report was produced and is distinct from newly generated analyses.

[Parent directory](../valutazione/test/report_generati/README.md) · [Current repository guide](../../README.md)

## Five-system comparison report

Original: [archivio/valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/README.md](../../archivio/valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/README.md).

`confronto/latex/verifica.pdf` is the compiled comparison; `confronto/` also contains LaTeX, tables and figures. This extends the four-system report with LLM + Random RAG. `confronto.json` stores measures, `provenienza.json` records source identities and `generatore/` preserves the generator revision. Completion/editorial records distinguish analysis from presentation changes.

The five-system comparison uses the saved campaigns and their documented conditions, including the separately trained MQT selector. It adds no new inference or compilation outcomes.

### Subdirectories

| Directory | Contents |
| --- | --- |
| [generatore/](../valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/generatore/README.md) | Five-system generator snapshot. |

[Parent directory](../valutazione/test/report_generati/confronto_cinque_sistemi/README.md) · [Current repository guide](../../README.md)

## Five-system generator snapshot

Original: [archivio/valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/generatore/README.md](../../archivio/valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/generatore/README.md).

These analysis modules and LaTeX fragments produced report `21aa899c01f8ca21`. They load the recorded campaigns, compute comparisons and generate presentation; they do not run the scientific Test.

This copy records the source version used by its parent report. Use `archivio/valutazione/test/report/` for the archive's report entry points and a new destination for a revised analysis. Retain the matching source and input fingerprints for exact historical reproduction.

[Parent directory](../valutazione/test/report_generati/confronto_cinque_sistemi/21aa899c01f8ca21/README.md) · [Current repository guide](../../README.md)

## Earlier five-system presentation

Original: [archivio/valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/README.md](../../archivio/valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/README.md).

This snapshot preserves the five-system report before the recorded editorial change. `confronto/` holds PDF/LaTeX, tables and figures; `confronto.json` and `provenienza.json` identify measures and sources; `generatore/` preserves the corresponding analysis code.

The current saved presentation is indexed in the enclosing five-system report area. This copy exists to reconstruct the earlier document without treating it as another run.

### Subdirectories

| Directory | Contents |
| --- | --- |
| [generatore/](../valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/generatore/README.md) | Earlier five-system generator snapshot. |

[Parent directory](../valutazione/test/report_generati/confronto_cinque_sistemi/README.md) · [Current repository guide](../../README.md)

## Earlier five-system generator snapshot

Original: [archivio/valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/generatore/README.md](../../archivio/valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/generatore/README.md).

This is the generator copy retained with the earlier editorial version. Python modules compute summaries and panels; LaTeX fragments supply the document sections. The code requires its corresponding source records and historical layout.

It is provenance material, not a separate operational toolkit. Refer to the enclosing revision and the parent report index for the later presentation.

[Parent directory](../valutazione/test/report_generati/confronto_cinque_sistemi/revisioni_editoriali/21aa899c01f8ca21_20260928T000545Z/prima/README.md) · [Current repository guide](../../README.md)

## Four-system report layout checks

Original: [archivio/valutazione/test/report_generati/controlli/revisione_struttura/README.md](../../archivio/valutazione/test/report_generati/controlli/revisione_struttura/README.md).

`prima/`, `seconda/` and `finale/` preserve rendered previews and verification records for the report layout revision. The final recorded comparison has 45 pages and ten four-panel figures.

The recorded verification passed 22 generator checks and matched numeric tables and source fingerprints against the earlier report. This directory documents rendering and data consistency, not another Test execution.

[Parent directory](../valutazione/test/report_generati/README.md) · [Current repository guide](../../README.md)

## WL source before the h=30 extension

Original: [archivio/valutazione/validation_dag_wl/revisioni_codice/prima_estensione_h30_513fd2b9d8/archivio/valutazione/validation_dag_wl/README.md](../../archivio/valutazione/validation_dag_wl/revisioni_codice/prima_estensione_h30_513fd2b9d8/archivio/valutazione/validation_dag_wl/README.md).

This snapshot preserves `valida.py` and documentation for the h=1–6 grid before wl_v3 expanded to h=1–30. It used the same 88 validation circuits, 396 train examples and k=5 retrieval without LLM calls or new compilations.

It records the historical selection procedure at that revision. The parent validation area contains later runs and the h=24 selection; this snapshot is not another current entry point.

[Parent directory](../valutazione/validation_dag_wl/README.md) · [Current repository guide](../../README.md)

## WL source before the h=6 extension

Original: [archivio/valutazione/validation_dag_wl/revisioni_codice/prima_estensione_h6_dc489e43af/archivio/valutazione/validation_dag_wl/README.md](../../archivio/valutazione/validation_dag_wl/revisioni_codice/prima_estensione_h6_dc489e43af/archivio/valutazione/validation_dag_wl/README.md).

This snapshot preserves `valida.py` and the original wl_v1 h=1–3 comparison with Manhattan on 88 validation circuits, using 396 train examples and k=5. It documents the state before the adaptive grid extensions.

The enclosing validation area indexes later runs and selection. This source revision is retained for provenance, not presented as the current grid.

[Parent directory](../valutazione/validation_dag_wl/README.md) · [Current repository guide](../../README.md)

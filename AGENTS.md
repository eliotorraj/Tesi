# Project guidance

## Local knowledge base

- Treat every file under `knowledge/` as the project's primary local knowledge base.
- Read `knowledge/riassunto_kb_mqt_predictor.md` first for the conversation context, then consult the papers when a claim needs confirmation.
- Distinguish clearly between the 2023 compilation-option predictor and the 2025 MQT Predictor architecture.
- Distinguish facts from the papers, facts from current software documentation, and our own engineering inferences.
- For current APIs and installation details, prefer the official MQT repository, documentation, and PyPI metadata because the software may have changed since publication.

## MQT Predictor testing

- The current experiment uses Python 3.12 with `mqt.predictor==2.4.0` and the exact pins in `uv.lock`. MQT Predictor 2.3.0 is historical material in `archivio/`.
- Use `docs/protocollo_sperimentale.md` as the only current experimental protocol. Active Dataset and artifacts are under their respective `experiments/` directories.
- Preserve the original corpus in `archivio/protocollo_v1/datasets/expected_fidelity/full/`; v2 still verifies it. Frozen manifest paths are logical references resolved by `resolve_source_reference`, not paths to rewrite.
- Do not assume that `qcompile` works immediately after installation. MQT Predictor 2.x requires trained RL models and a trained supervised device selector.
- A smoke-trained model only validates the pipeline; it is not evidence of compilation quality.
- Preserve trained model artifacts before recreating `.venv`, including runtime copies inside the installed package directory and canonical artifacts under `artifacts/experiments/`.

## Terminology

- When i want to talk about the set for RAG/fine-tuning of the LLM i will talk about "Dataset"
- Instead when i want to talk about the set of couples (circuit,device) for the ML model training, then i will say "Training set"

## LeanCTX

- Use LeanCTX selectively for targeted searches, `map`/`signatures` reads, and verbose command output; keep compression enabled by default.
- Use native tools for small exact operations or if the server points to another project. Do not repeat a rejected path or silently run in the wrong directory.
- Use full/raw output only for the exact source, errors, numbers, or paper claims needed as evidence.
- Keep tool discovery output short. Plugin statistics do not establish net Codex token or cost savings.

## Reports

When writing the documentation of an implemented task you have done, follow this principles:
- Use a simple and natural language, easy to understand
- Avoid English loanwords unless necessary
- No long or complex sentences. The goal is to explain what we actually did—the details don't matter!
- The goal is to understand what this part of the project excatly does, in general terms
- If necessary for clarity, create a separated readme to describe the actual task, and place it in the most specific folder of the task implemented
# Project guidance

## Local knowledge base

- Treat every file under `knowledge/` as the project's primary local knowledge base.
- Read `knowledge/riassunto_kb_mqt_predictor.md` first for the conversation context, then consult the papers when a claim needs confirmation.
- Distinguish clearly between the 2023 compilation-option predictor and the 2025 MQT Predictor architecture.
- Distinguish facts from the papers, facts from current software documentation, and our own engineering inferences.
- For current APIs and installation details, prefer the official MQT repository, documentation, and PyPI metadata because the software may have changed since publication.

## MQT Predictor testing

- The reproducible baseline is Python 3.12 with `mqt.predictor==2.3.0` and the compatibility pins from its official v2.3.0 lockfile.
- Do not assume that `qcompile` works immediately after installation. MQT Predictor 2.x requires trained RL models and a trained supervised device selector.
- A smoke-trained model only validates the pipeline; it is not evidence of compilation quality.
- Preserve trained model artifacts before recreating `.venv`, because MQT Predictor 2.3.0 stores them inside the installed package directory.

## Terminology

- When i want to talk about the set for RAG/fine-tuning of the LLM i will talk about "Dataset"
- Instead when i want to talk about the set of couples (circuit,device) for the ML model training, then i will say "Training set"

## LeanCTX

- Prefer LeanCTX MCP tools for repository exploration.
- Use `ctx_search` instead of broad recursive searches when possible.
- Use `ctx_read` with map or signatures mode before requesting full files.
- Use `ctx_tree` instead of recursively listing the repository.
- Use `ctx_shell` for commands whose output may be large.
- Expand compressed or partial results when exact source text is required.
- Do not use lossy summaries as evidence for exact code, test failures, numerical results, or paper claims.

## Reports

When writing the documentation of an implemented task you have done, follow this principles:
- Use a simple and natural language, easy to understand
- Avoid English loanwords unless necessary
- No long or complex sentences. The goal is to explain what we actually did—the details don't matter!
- The goal is to understand what this part of the project excatly does, in general terms
- If necessary for clarity, create a separated readme to describe the actual task, and place it in the most specific folder of the task implemented
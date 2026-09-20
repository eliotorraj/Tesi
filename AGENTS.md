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


## Reports

When writing the documentation of an implemented task you have done, follow this principles:
- Use a simple and natural language, easy to understand
- Avoid English loanwords unless necessary
- No long or complex sentences. The goal is to explain what we actually did—the details don't matter!
- The goal is to understand what this part of the project excatly does, in general terms
- If necessary for clarity, create a separated readme to describe the actual task, and place it in the most specific folder of the task implemented

## Documentazione dello sviluppo e degli esperimenti per la tesi

- Documentare lo sviluppo del progetto e gli esperimenti è un obiettivo principale, insieme al funzionamento del sistema. Conservare decisioni, motivazioni, modifiche e limiti, con particolare attenzione alle prove sperimentali.
- Predisporre la raccolta dei dati prima delle prove. Durante tutta la validation conservare informazioni sufficienti per ricostruire gli esperimenti e produrre successivamente immagini, grafici, tabelle e analisi per la tesi.
- Registrare tutte le configurazioni provate, anche quelle scartate, e tutti i tentativi, inclusi errori, timeout, correzioni e interruzioni. Distinguere prove tecniche, selezione sulla validation e valutazione finale sul test. Non sovrascrivere o eliminare esiti sfavorevoli.
- Conservare dati originali leggibili da programma e metadati di provenienza: circuito e split, identificativi delle esecuzioni, modelli e revisioni, precisione dei pesi, prompt e risposte, evidenze RAG, parametri, seed quando disponibili, versioni del codice e delle dipendenze, hardware e risorse assegnate. Non salvare segreti.
- Raccogliere qualità delle scelte, successi e fallimenti, cause degli errori, numero di chiamate e correzioni, tempi delle diverse fasi, token e consumo di memoria, quando misurabili. Indicare unità, metodo di misura e dati mancanti; distinguere misure, stime e risultati riutilizzati da esecuzioni precedenti.
- Mantenere la separazione tra train, validation e test anche nei registri e nelle analisi. Gli score usati per valutare una decisione non devono entrare nel prompt o nelle evidenze della stessa decisione. Dichiarare sempre denominatori e circuiti effettivamente confrontabili.
- Rendere riproducibili le analisi: generare riepiloghi, tabelle e figure dai dati conservati tramite procedure versionate. Documentare aggregazioni, esclusioni, scelte statistiche e motivazione della configurazione finale.
- Per gli esperimenti di validation produrre anche un documento LaTeX inseribile nella tesi, con descrizione, impostazioni, risultati, grafici, criteri di selezione e limiti. Conservare sorgenti e figure, offrire una compilazione autonoma di verifica e controllare il documento compilato.
- Usare un linguaggio semplice nel testo. La semplicità espositiva non giustifica l'omissione dei dati e dei dettagli necessari a riprodurre gli esperimenti: collocarli in tabelle, appendici o documenti specifici.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

# Evaluation of selected settings

`esegui.py` freezes the plan and executes one method at a time. `score.py` computes the metric. `analizza.py` produces JSON, CSV and LaTeX summaries. `oracle.py` runs an optional exhaustive reference grid separate from decision makers. [risultati/](risultati/README.md) links to the Test evaluation documentation.

Available IDs: `llm_rag`, `llm_senza_rag`, `random`, `llm_recupero_random`, `mqt`, `llm_rag_k1`, `llm_rag_k10`, `llm_wl`, `llm_wl_sintesi`. Declare methods before preparation. WL requires a validation selection; MQT requires verified models and successful technical checks. All planned methods must satisfy prerequisites before freezing.

From the toolkit root:

```bash
python esperimento.py --esperimento my-trial test congela
python esperimento.py --esperimento my-trial test esegui --metodo llm_rag
python esperimento.py --esperimento my-trial test analizza
```

Run every planned method before final comparison. Match LLM server identity/context and run sequentially for timing comparisons. Errors and timeouts remain recorded. Resume does not silently repeat started cases; missing scores do not become zero. See the [guide](../documentazione/guida.md).

The completed QASMBench comparison and its oracle records are in [archivio/valutazione/](../../archivio/valutazione/README.md), separate from newly generated toolkit results.

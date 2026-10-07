# Validation and selection

`seleziona.py` freezes candidates, records decisions and selects model/temperature settings on common observable circuits. `wl.py` selects structural retrieval depth using `dag_wl_core.py`. Reports use `comune/relazioni.py`; [risultati/](risultati/README.md) links to the validation documentation.

After Dataset generation, from the toolkit root:

```bash
python esperimento.py --esperimento my-trial validation congela
python esperimento.py --esperimento my-trial validation esegui --modello qwen
python esperimento.py --esperimento my-trial validation seleziona
python esperimento.py --esperimento my-trial validation report
```

Run every configured model with its corresponding server before selection. `validation wl` is needed only for WL variants. Choose candidates and temperatures before preparation with `configura.py modelli`, `modello` and `parametri`.

Validation scores are read after decisions are sealed and never enter their prompts. The toolkit defaults to `median_regret`; the [conditions](../documentazione/condizioni.md) explain differences from the historical experiment. Fix context, hardware, timeouts and criterion before the campaign.

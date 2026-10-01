# Test: misurare i sistemi già scelti

`esegui.py` congela il piano e valuta un metodo per volta. `score.py` calcola la metrica; `analizza.py` produce riepiloghi, CSV e LaTeX; `oracle.py` costruisce il riferimento facoltativo separato dai decisori. Gli esiti sono in `risultati/<id>/`.

Metodi: `llm_rag`, `llm_senza_rag`, `random`, `llm_recupero_random`, `mqt`, `llm_rag_k1`, `llm_rag_k10`, `llm_wl`, `llm_wl_sintesi`. Dichiararli prima di `prepara`. WL richiede la propria selezione; MQT modelli validati e prove Bell riuscite. La ripresa non rigenera casi iniziati. Errori e timeout restano esiti e gli score mancanti non diventano zero.

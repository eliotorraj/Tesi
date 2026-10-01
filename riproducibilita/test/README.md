# Test delle impostazioni selezionate

`esegui.py` congela il piano e valuta un metodo per volta. `score.py` calcola la metrica; `analizza.py` produce JSON, CSV e LaTeX; `oracle.py` genera una griglia facoltativa separata dai decisori. Gli esiti sono in `risultati/<id>/`.

I metodi disponibili sono `llm_rag`, `llm_senza_rag`, `random`, `llm_recupero_random`, `mqt`, `llm_rag_k1`, `llm_rag_k10`, `llm_wl`, `llm_wl_sintesi`. Dichiarare l'elenco prima di `prepara`. WL richiede la propria selezione; MQT modelli verificati e prove Bell riuscite. Tutti i metodi previsti devono soddisfare i prerequisiti prima del congelamento.

Da `riproducibilita/` usare `.venv/bin/python -B esperimento.py test congela`, poi `test esegui --metodo ID` e `test analizza`. Per gli LLM mantenere server e contesto concordati con il registro. Eseguire in sequenza se si confrontano i tempi. Errori e timeout restano conservati; la ripresa non rigenera casi iniziati e gli score mancanti non diventano zero. Vedere la [guida](../documentazione/guida.md).

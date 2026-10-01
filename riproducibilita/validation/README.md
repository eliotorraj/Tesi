# Validation delle impostazioni

`seleziona.py` congela i candidati, registra le decisioni e sceglie modello/temperatura sui circuiti comuni. `wl.py` seleziona la profondità del recupero strutturale con `dag_wl_core.py`. I report vengono generati da `comune/relazioni.py`; i risultati sono in `risultati/<id>/`.

Dopo la generazione Dataset usare, da `riproducibilita/`, `.venv/bin/python -B esperimento.py validation congela`, poi `validation esegui --modello ID` con il server corrispondente, `validation seleziona` e `validation report`. `validation wl` è richiesto soltanto per le varianti WL.

Gli score validation vengono letti dopo il sigillo delle decisioni e non entrano nel prompt. Contesto ridotto, CPU, GPU, timeout e griglia dei modelli sono condizioni da fissare prima della prova. I 16 GB della prima prova del prototipo non garantiscono che questa campagna completa sia praticabile. Criteri e denominatori sono descritti nelle [condizioni](../documentazione/condizioni.md).

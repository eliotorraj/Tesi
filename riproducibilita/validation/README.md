# Validation: selezionare le impostazioni

`seleziona.py` congela la griglia, registra le decisioni e sceglie il vincitore sui circuiti comuni. `wl.py` seleziona la profondità del recupero strutturale con `dag_wl_core.py`. I report sono generati da `comune/relazioni.py`.

Comandi: `esperimento.py validation congela`, `esegui --modello ID`, `seleziona`, `report` e facoltativamente `wl`. Gli esiti sono in `risultati/<id>/`. Gli score del circuito validation non entrano nel suo prompt. Vedere le [condizioni](../documentazione/condizioni.md).

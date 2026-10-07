# QASMBench development checks

`test_strumenti.py` covers records, timeouts, integrity and a technical Bell compilation. `compatibilita.py` checks parsing, features and compatible devices without scoring. `candidati.py` inspects candidate QASM; `selettore_bell.py` checks selector output without RL compilation; `inventario_selettori.py` inventories artifacts.

`registri/` stores check evidence and `esclusi/` preserves four sources excluded before selection. `collega_selettore.py` and `predisponi_strumenti.py` record original setup operations and should not be rerun as routine checks. These tools document preparation separately from the 50-circuit comparison.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

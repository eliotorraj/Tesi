# Verifiche di sviluppo

Queste prove sono separate dal confronto sperimentale.

- `test_strumenti.py`: registri, timeout, confronto, integrità e compilazione di un Bell sintetico.
- `compatibilita.py`: parsing dei cinquanta file, 49 caratteristiche e dispositivi compatibili; nessuno score.
- `candidati.py`: controllo statico dei QASM scaricati.
- `registri/`: evidenze dei controlli, incluse le esclusioni.
- `selettore_bell.py`: prova del selettore scelto su un Bell sintetico, senza compilazione RL.
- `inventario_selettori.py`: inventario in sola lettura degli artefatti trovati.
- `collega_selettore.py`: registro della scelta iniziale del selettore; non rilanciarlo.
- `esclusi/`: quattro sorgenti originali scartati prima della selezione definitiva.
- `predisponi_strumenti.py`: registro della prima derivazione del codice; non rilanciarlo.

Dalla radice del repository:

```bash
.venv/bin/python archivio/valutazione/test_qasmbench/verifiche/test_strumenti.py
.venv/bin/python archivio/valutazione/test_qasmbench/verifiche/compatibilita.py
```

Nessuno di questi comandi avvia inferenze LLM o compilazioni MQT sui QASMBench.
I circuiti piccoli e grandi restano riservati alla futura esecuzione esplicita.

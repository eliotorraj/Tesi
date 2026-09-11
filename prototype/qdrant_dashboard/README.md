# Esplorare il Dataset con Qdrant

La dashboard ufficiale si apre su [localhost:6333/dashboard](http://localhost:6333/dashboard/).
Per funzionare richiede Docker Desktop e il contenitore Qdrant in esecuzione.
Se il browser mostra «connessione rifiutata», avviare prima i servizi.

## Avvio

Da PowerShell, nella radice del progetto:

```powershell
docker desktop start
docker compose -f prototype/qdrant_dashboard/compose.yaml up -d
```

Poi, da WSL nella stessa radice:

```bash
.venv/bin/python scripts/18_qdrant_dashboard.py
```

Il comando controlla il Dataset e l'indice originale, copia i punti nella
raccolta vuota e verifica il risultato. Se la raccolta esiste già, la controlla
senza riscriverla. Una raccolta alterata o incompleta produce un errore.
Il controllo richiede vettori identici in float32. Per i punteggi ammette
solo l'arrotondamento minimo del passaggio JSON, registrato nel resoconto.

## Cosa vedere

Aprire **Collections**, poi **circuit49_manhattan_v1**.
La raccolta contiene 396 esempi train, ciascuno con un vettore di 49 valori
e i dati associati al circuito.

- `circuit_id`: identificativo del circuito.
- `selected_device_id`: dispositivo vincente nell'esempio.
- `record.retrieval_input.circuit.features.values`: caratteristiche originali.
- `record`: esempio completo con configurazioni, risultati e provenienza.

I vettori mostrati da Qdrant contengono le caratteristiche trasformate.
Il loro ordine e i divisori sono descritti nel file `rag/index/transform.json`
dell'esperimento. Le ricerche manuali della dashboard sono esplorative:
il recupero del prototipo aggiunge i controlli di provenienza, i filtri e
l'ordinamento canonico delle parità previsti dal protocollo.

## Dove sono i dati

La dashboard usa Qdrant server 1.19.1 e una copia separata, conservata nel
volume Docker `tesi-mqt24-dashboard_dashboard-data`. Il progetto continua
a usare l'indice locale incorporato in Python e le dipendenze di `uv.lock`.
Le modifiche nella dashboard non vengono propagate all'indice originale.
Non vengono importati esempi validation o test.

La porta 6333 è accessibile solo dal computer locale.
Il controllo della copia viene salvato sotto
`artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/rag/dashboard/verification.json`.

Per fermare il servizio conservando i dati, dalla radice del progetto:

```powershell
docker compose -f prototype/qdrant_dashboard/compose.yaml stop
```

Per riaprirlo, ripetere il comando di avvio. Non serve importare di nuovo i punti.

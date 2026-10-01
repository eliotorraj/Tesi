# Verifiche sintetiche del Test

Queste prove controllano il software con circuiti tecnici, dati artificiali e
risposte simulate. Non avviano Qwen, non valutano il corpus Test e non
addestrano i modelli di confronto.

- `test_indipendenti.py`: isolamento dei metodi, ripresa, errori, metriche e score.
- `test_server.py`: requisiti del server e identità del modello.
- `test_trasporto.py`: errori nelle chiamate e conservazione dei registri.
- `test_percorsi.py`: separazione delle cartelle, chiavi storiche degli hash e
  rifiuto di ripresa con codice diverso dal contratto congelato.

Dalla radice del repository:

```bash
.venv/bin/python -m unittest discover -s archivio/valutazione/test/verifiche -v
```

I risultati sperimentali esistenti non devono cambiare durante queste prove.
Le verifiche del generatore dei report sono nella cartella sorella
`report/verifiche/`.

`test_numero_esempi.py` verifica su Bell il recupero a 1 e 10 esempi,
l'ordine Manhattan, i riferimenti E10, la codifica TOON, le correzioni,
i token e l'isolamento delle campagne. Le risposte LLM e la compilazione
sono simulate; nessun circuito Test reale viene eseguito.

# Prova esplorativa MQT

Questa cartella conserva la valutazione MQT con il selettore disponibile.
Al 25 settembre 2026 contiene 90 esiti sui 90 circuiti Test, raccolti il
24 settembre. Il confronto resta esplorativo: il selettore usa 384 dei 396
campioni train previsti, con 12 esclusi e 1853 compilazioni riuscite su 1878
coppie. La raccolta unisce successi a 100 secondi e recuperi a 300 secondi.

Le quattro classi del selettore sono i dispositivi vincitori osservati.
Falcon 27 resta fra i cinque modelli RL ma non ha etichette vincenti.
Il Test usa una compilazione per circuito, timeout di 100 secondi, gli stessi
Target e la stessa expected fidelity del confronto originale.
La prova non completa il Test MQT conforme al contratto originale.

## Struttura

| Percorso | Funzione |
| --- | --- |
| `mqt_predictor.py` | Ingresso della prova separata. |
| `piano.json` | Criteri comuni al Test e deroghe esplicite sull'addestramento. |
| `provenienza_codice.json` | Impronte del codice originale copiato per la prova. |
| [strumenti/](strumenti/README.md) | Esecuzione, controlli, score e lettura del modello locale. |
| `runtime/` | Copia locale del selettore, separata dal modello MQT globale. |
| `preparazione/` | Controlli e contratto congelato della prova esplorativa. |
| `prove_tecniche/` | Le prove Bell, comprese quelle fallite. |
| `risultati/mqt_predictor/` | Esiti, sessioni, circuiti compilati e misure originali. |
| `verifiche/` | Controlli sintetici sulle classi e sul collegamento ML/RL. |

La struttura interna dei risultati è descritta nel
[README del Test](../test/README.md). Il generatore dei
[report](../test/report/README.md) legge questa area come fonte MQT separata
e la indica esplicitamente nelle tabelle e nei grafici.
Il [resoconto storico](SVILUPPO.md) conserva correzioni e tentativi.

## Verifiche e compatibilità

Dalla radice del repository, nell'ambiente WSL completo:

```bash
.venv/bin/python archivio/valutazione/test_mqt_esplorativo/verifiche/test_selettore.py -v
.venv/bin/python archivio/valutazione/test_mqt_esplorativo/mqt_predictor.py --verifica
```

Il primo comando usa dati sintetici e non apre il Test. Il secondo verifica i
requisiti e conserva un nuovo controllo preliminare. `--tecnico` e `--esegui`
restano ingressi sperimentali espliciti; le sei prove Bell sono richieste dal
protocollo prima dell'esecuzione MQT.

Il worker passa un Target a `rl_compile`, come richiede l'API 2.4.0.
Le prime sei prove fallite per il passaggio del nome del dispositivo sono
conservate. Il modello locale è letto da questa area: il selettore incompleto
non viene installato nel runtime globale.

La riorganizzazione del 25 settembre ha cambiato i percorsi e le impronte dei
sorgenti, senza modificare piani, contratti, modelli o risultati.
**Il contratto congelato non può essere ripreso con codice diverso.**
I rapporti possono invece leggere gli esiti già salvati dalla nuova posizione.
Per fonti, limiti e riproducibilità consultare il
[protocollo corrente](../../../prototipo/docs/protocollo_sperimentale.md)
e il [registro della riorganizzazione](../../riorganizzazione_2026_09_25/README.md).

# Valutazione finale del framework

Questa cartella conserva i programmi e i dati del confronto sui 90 circuiti
Test. Non serve per usare il prototipo. Il programma per un circuito libero è
[`prototipo/app.py`](../../../prototipo/README.md).

Al 25 settembre 2026 sono presenti 90 esiti per LLM + RAG, 90 per LLM senza
RAG e 90 per Random, raccolti dal 21 settembre. I 90 esiti MQT del 24 settembre
sono nella [prova esplorativa separata](../test_mqt_esplorativo/README.md):
non completano il Test MQT conforme al contratto originale.

Le regole e i limiti aggiornati sono nel
[protocollo sperimentale](../../../prototipo/docs/protocollo_sperimentale.md).
Il [resoconto storico](SVILUPPO.md) conserva le correzioni effettuate durante
lo sviluppo; i suoi percorsi si riferiscono alla struttura di allora.

## Struttura

| Percorso | Funzione |
| --- | --- |
| `llm_rag.py`, `llm_senza_rag.py`, `mqt_predictor.py`, `casuale.py` | Un ingresso indipendente per ciascun metodo. |
| `piano.json` | Impostazioni sperimentali conservate senza modifiche. |
| [strumenti/](strumenti/README.md) | Controlli, esecuzione, misura dello score e riepiloghi. |
| [verifiche/](verifiche/README.md) | Controlli automatici su casi sintetici e risposte simulate. |
| `preparazione/` | Controlli preliminari e contratto congelato. |
| `prove_tecniche/` | Prove Bell, errori e controlli esterni al Test. |
| `risultati/<metodo>/` | Esiti originali, richieste LLM, risposte, compilazioni e tempi. |
| `confronti/` | Confronti prodotti dall'analisi precedente. |
| [report/](report/README.md) | Generatore dei documenti completi per la tesi. |
| `report_generati/` | Versioni dei documenti, dati, figure e copie del generatore. |
| `analizza.py` | Riepilogo precedente dei metodi già eseguiti. |

Dentro ogni cartella `risultati/<metodo>/`, `esecuzione.json` identifica la
raccolta e `sessioni/` conserva avvii e riprese. `circuiti/<id>/` contiene
l'ingresso, i tentativi LLM quando previsti, la decisione, la cartella
`compilazione/` e l'esito finale `esito.json`. Anche errori, timeout e
interruzioni restano conservati. `analisi/<impronta>/` contiene i riepiloghi
precedenti dello stesso metodo.

## Consultazione e verifiche

Dalla radice del repository, con l'ambiente Python 3.12 già preparato:

```bash
.venv/bin/python -m unittest discover -s archivio/valutazione/test/verifiche -v
.venv/bin/python -m unittest discover -s archivio/valutazione/test/report/verifiche -v
```

Questi comandi verificano il software con dati sintetici. Non aprono il Test,
non chiamano Qwen e non addestrano MQT. Il
[generatore dei report](report/README.md) spiega come analizzare gli esiti
esistenti e produrre nuovi documenti senza nuove compilazioni quantistiche.

Gli ingressi sperimentali conservano `--verifica`, `--tecnico` e `--esegui`.
Per esempio, il solo controllo preliminare di Random si richiama così:

```bash
.venv/bin/python archivio/valutazione/test/casuale.py --verifica
```

Le dipendenze del prototipo bastano per i due LLM e Random. MQT richiede
WSL/Linux, l'ambiente completo fissato nell'esperimento, i cinque modelli RL
e il selettore verificato. La guida è in
[addestramento/mqt/](../addestramento/mqt/README.md).
Le sei prove tecniche MQT rimangono un requisito del suo avvio sperimentale.
I LLM richiedono il profilo desktop e il GGUF indicato con `--model-path`.
Il profilo laptop ridotto non sostituisce quello del protocollo.

## Effetto della riorganizzazione

I programmi ora leggono il framework da `prototipo/` e i dati sperimentali da
`archivio/valutazione/`. Le fonti congelate restano in
`archivio/esperimento_v2/`. Gli originali non sono stati riscritti.

Le chiavi del codice nei nuovi controlli conservano la forma logica precedente
(`test/...`, `addestramento/mqt/...`); sono cambiate le posizioni fisiche.
Gli adattamenti dei sorgenti cambiano però le loro impronte. Per questo
**il codice corrente rifiuta la ripresa di un contratto congelato con una
revisione diversa**. Non cancellare né aggiornare il contratto per aggirare il
controllo. La riorganizzazione non autorizza nuove valutazioni del Test.
La copia precedente dei sorgenti è conservata nel
[registro della riorganizzazione](../../riorganizzazione_2026_09_25/README.md).

I percorsi assoluti nei vecchi registri restano testimonianza dell'esecuzione.
I lettori correnti trovano esiti e contratti dalla nuova cartella, senza
riscrivere quegli indirizzi. I rapporti precedenti restano consultabili;
rigenerare un rapporto produce una nuova versione.

Risultati, modelli e registri voluminosi sono esclusi da Git. Un clone contiene
i programmi e le istruzioni, ma richiede il trasferimento separato di questi
dati per riprodurre le analisi sperimentali.

## Integrazioni del 27 settembre 2026

- [LLM con cinque esempi casuali](recupero_random/README.md): avvio separato
  in [llm_recupero_random.py](llm_recupero_random.py), con contratto e registri
  propri. Lo sviluppo non avvia i 90 casi.
- [Analisi dei fatti verificabili](report_generati/30dd5b4f737c058e/analisi_fatti/README.md):
  supplemento separato al PDF, tre campioni e conteggi sull'intero Test.
- [Similarità dei circuiti e miglioramenti](similarita_circuiti_e_miglioramenti.txt):
  proposte e fonti primarie, con separazione tra fatti e ipotesi progettuali.

## Numero di esempi RAG: 1 e 10

Gli avvii [llm_rag_1_esempio.py](llm_rag_1_esempio.py) e
[llm_rag_10_esempi.py](llm_rag_10_esempi.py) conservano il recupero Manhattan
del RAG classico, con campagne e contratti separati. Registrano qualità,
fatti, token e tempi. Comandi e limiti sono nella
[guida al numero di esempi](numero_esempi/README.md).

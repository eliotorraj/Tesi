# Mappa del funzionamento

`esperimento.py` sceglie la fase e importa il modulo necessario. `bootstrap.py` prepara gli import. `comune/settings.py` risolve configurazione e percorsi: è il primo punto da leggere per capire dove finiscono ingressi e risultati.

| Domanda | Punto di partenza | Collegamento |
| --- | --- | --- |
| Come si avvia Qwen o un altro LLM? | `modelli_llm/server.py` e `modelli.json` | Backend CPU/GPU, `--list-devices`, contesto e trasporto Linux/Windows. |
| Come si preparano i circuiti? | `comune/corpus.py` | Caratteristiche in `dataset/qiskit_dataset/core.py`, integrità in `comune/scripts/mqt_predictor_protocol.py`. |
| Quali dispositivi/configurazioni? | `configurazioni/catalogo.json` | Validazione in `catalog.py` e `mqt/gestione.py`. |
| Come si addestra RL? | `mqt/addestra_rl.py` | Ambiente MQT, limiti delle azioni, checkpoint e metadati. |
| Come nasce il Training set? | `mqt/addestra_selettore.py` | `deduplica.py`, `motore_ml.py`, compilazioni, array e classificatore. |
| Come nasce un esempio RAG? | `dataset/genera.py` | Processo `worker.py`, compilazione `generation.py`, mediane ed esempi `views.py`. |
| Come si crea il prompt? | `comune/framework/app.py:prepare` | Parsing, maschera hardware, recupero Qdrant, contesto e TOON. |
| Dove si verifica la risposta? | `comune/framework/app.py:decide` | `prototype/prompting/facts.py` e schemi di risposta. |
| Perché vince un candidato? | `validation/seleziona.py` | Decisioni sigillate, matrice validation e tabella dei criteri. |
| Come cambia il recupero? | `comune/llm.py` | Qdrant, campionamento casuale, oppure `validation/dag_wl_core.py`. |
| Come si esegue Test? | `test/esegui.py` | Scelta, processo isolato, esito e `test/analizza.py`. |
| Come si evitano sovrascritture? | `comune/settings.py`, `comune/processi.py` | Contratti, scritture atomiche senza sostituzione, esiti terminali. |
| Come si esporta? | `comune/esporta.py` | Framework autonomo con solo train, catalogo e scelta congelata. |

```text
Circuiti + catalogo + versioni
             |
           prepara
             |
       +-----+---------------------+
       |                           |
   RL per device              Dataset Qiskit
       |                      train + validation
  Training set MQT                 |
       |                      Dataset RAG train
  selettore + Bell                 |
       |                    validation candidati
       |                           |
       +-------------------- modello selezionato
                                   |
                         congela ed esegui Test
                                   |
                         report e nuovo prototipo
```

Train costruisce modelli ed evidenze; validation sceglie impostazioni; Test misura scelte già fissate. Gli score validation e Test non entrano nel prompt della decisione sullo stesso circuito.

La CPU/GPU del PC ospita il server LLM e non coincide con i Target quantistici. Le condizioni della prima prova sono nella [guida](guida.md); per usare il prototipo già selezionato su Linux CPU o sul fisso partire dalla [guida dedicata](../../prototipo/docs/guida_passo_passo.md). I file del kit sono autonomi rispetto a quel prototipo.

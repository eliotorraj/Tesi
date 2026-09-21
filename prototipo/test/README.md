# Test indipendenti

Questa è l'area operativa del confronto finale. Ogni comando avvia **un solo
metodo sui medesimi 90 circuiti Test**, salva ogni caso e produce il proprio
rapporto. Non serve attendere il selettore ML per eseguire gli altri metodi.

Il protocollo è [qui](../docs/protocollo_sperimentale.md). L'archivio viene letto
per verificare provenienza, sigilli e sorgenti; i suoi programmi non vengono
usati per aprire il nuovo Test. La dimostrazione `app.py` rimane separata.

## Quale comando usare

Comandi dalla radice del repository, con Python 3.12 e le dipendenze del
prototipo. Nell'ambiente WSL già preparato:

| Metodo | Controllo preliminare | Avvio o ripresa |
| --- | --- | --- |
| LLM + RAG | `.venv/bin/python prototipo/test/llm_rag.py --verifica` | `.venv/bin/python prototipo/test/llm_rag.py --esegui --model-path PERCORSO_GGUF` |
| LLM senza RAG | `.venv/bin/python prototipo/test/llm_senza_rag.py --verifica` | `.venv/bin/python prototipo/test/llm_senza_rag.py --esegui --model-path PERCORSO_GGUF` |
| MQT Predictor | `.venv/bin/python prototipo/test/mqt_predictor.py --verifica` | `.venv/bin/python prototipo/test/mqt_predictor.py --esegui` |
| Random | `.venv/bin/python prototipo/test/casuale.py --verifica` | `.venv/bin/python prototipo/test/casuale.py --esegui` |

Per usare l'ambiente Windows del prototipo sostituire `.venv/bin/python` con
`prototipo\.venv\Scripts\python.exe`. Per MQT usare **WSL/Linux** e l'ambiente
completo fissato nel lock dell'esperimento. Le dipendenze del prototipo
bastano per i due LLM e Random: questi tre non caricano i modelli MQT.

Il comando senza una delle opzioni `--verifica`, `--tecnico` o `--esegui`
non parte. `--esegui` è la scelta esplicita di aprire quel metodo.
Non è previsto un comando che esegua tutti i metodi.

## LLM: server e prova tecnica

Avviare il server con il profilo **desktop**, come descritto nella
[guida del prototipo](../README.md). Il profilo laptop a contesto ridotto
non è ammesso per questi Test. Non usare contemporaneamente i due client LLM
sullo stesso server: l'indipendenza degli avvii non richiede simultaneità.

Il GGUF fornito a `--model-path` deve essere quello dichiarato dal server.
Il controllo verifica hash, dimensione, percorso del modello effettivo e
contesto 60.000 tramite `/props`. Il server predefinito è
`http://127.0.0.1:8089`; `--url` permette un'altra porta locale.

Prima della valutazione si può provare il flusso con un Bell sintetico:

```bash
.venv/bin/python prototipo/test/llm_rag.py --tecnico --model-path /mnt/d/PERCORSO/Q8_0.gguf
.venv/bin/python prototipo/test/llm_senza_rag.py --tecnico --model-path /mnt/d/PERCORSO/Q8_0.gguf
```

Queste prove non aprono il Test e finiscono in `prove_tecniche/`.
La compilazione è automatica: non compare una richiesta di conferma.
Sono consentite al massimo tre risposte complete per correggere la risposta,
con le regole v4. Un errore di trasporto è registrato e terminale per quel caso;
non scatta una ripetizione nascosta.

## MQT: requisiti separati

Preparare prima il selettore con la [guida ML](../addestramento/mqt/README.md).
Le copie RL e ML usate da MQT devono coincidere con i modelli canonici.
La provenienza ML deve riferirsi agli stessi cinque RL e allo stesso corpus.

Dopo `--verifica`, eseguire:

```bash
.venv/bin/python prototipo/test/mqt_predictor.py --tecnico
```

Questo esegue cinque prove RL e una selezione ML seguita da compilazione RL
su Bell. Prima di `--esegui` devono riuscire tutte e sei, con gli stessi
modelli che saranno usati nel Test. Le due chiamate interne sono le stesse
di `qcompile` 2.4.0; sono separate per misurare selezione e compilazione.

## Dove sono risultati, grafici e LaTeX

```text
prototipo/test/
  piano.json                         impostazioni del nuovo Test
  preparazione/
    verifiche/                       controlli riusciti e falliti
    contratto_congelato.json          creato al primo --esegui
  risultati/
    llm_rag/                         un'esecuzione ufficiale per metodo
    llm_senza_rag/
    mqt_predictor/
    random/
      esecuzione.json                identità, codice, ambiente e contratto
      sessioni/                      ogni avvio e ripresa
      circuiti/<circuit_id>/
        begin.json                   ingresso e identità del sorgente
        input.qasm
        prompt.json                  solo per metodi con scelta Qiskit
        retrieval.json               preparazione ed evidenze RAG
        attempt_*/                   richieste, risposte, controlli e tempi LLM
        decision.json                scelta salvata prima della compilazione
        compilazione/
          job.json
          compiled.qasm
          result.json
          stdout.txt
          stderr.txt
        esito.json                   metriche finali, anche per fallimenti
      analisi/<impronta>/
        riepilogo.json
        tabelle/circuiti.csv
        grafici/score.csv
        grafici/score.tex
        latex/risultati.tex           testo inseribile nella tesi
        latex/verifica.tex            documento autonomo
        latex/verifica.pdf            se pdflatex è disponibile
        completato.json
  confronti/<impronta>/               analisi fra metodi già eseguiti
  prove_tecniche/<metodo>/<id>/        mai mescolate con il Test
  strumenti/                         implementazione condivisa
  verifiche/                         regressioni automatiche sintetiche
```

I file `esito.json` sono la fonte primaria. I rapporti sono rigenerabili.
Una nuova analisi ha una nuova impronta se cambiano dati o generatore.
Per rigenerare i rapporti disponibili e il confronto, senza avviare compilazioni:

```bash
.venv/bin/python prototipo/test/analizza.py
```

Per compilare manualmente un rapporto, entrare nella sua cartella `latex/`
ed eseguire `pdflatex -halt-on-error verifica.tex`. Serve TeX Live con PGFPlots.
Il frammento `risultati.tex` usa il grafico nella cartella sorella `grafici/`;
conservare questa struttura o adattare gli input nella tesi.
Non sono necessari servizi grafici o chiamate a modelli per l'analisi.

## Ripresa, errori e interpretazione

Rilanciare lo stesso comando `--esegui`. I casi con un esito non vengono
ripetuti. Se un processo è stato arrestato senza esito, il caso resta
`interrupted`, con score mancante: non viene rilanciato per ottenere un
risultato migliore. I casi successivi proseguono. Un fallimento non blocca
l'intero insieme. Non cancellare la cartella per ripetere il Test.

Il contratto comune viene congelato al primo avvio ufficiale e verificato
negli avvii successivi. Include codice, piano, configurazione, fonte e RAG.
Non modificare prompt, impostazioni o dipendenze dopo aver visto i risultati.
Un blocco per metodo evita due esecuzioni contemporanee sullo stesso registro.

Lo score medio usa solo i successi e dichiara quanti sono. Nel confronto
appaiato entrano solo i circuiti riusciti per entrambi, con identità esplicite.
Fallimenti e circuiti mancanti sono mostrati a parte. Token e tempi ignoti
rimangono null. I token di input sono quelli del prompt completo per chiamata,
anche quando il server riusa la cache; i contatori del server restano nei grezzi.

La nuova valutazione usa **un seed, 0**, per ogni metodo Qiskit e un'esecuzione
MQT. Le tre compilazioni della validation restano storiche: qui non si produce
la loro mediana. Non esiste una scelta della migliore fra più compilazioni.
Random estrae una coppia compatibile, in modo uniforme e riproducibile,
senza nuova estrazione dopo un fallimento.

## Verifica dello sviluppo

```bash
.venv/bin/python -m unittest discover -s prototipo/test/verifiche -v
```

Queste prove usano dati sintetici e risposte simulate. Non avviano Qwen
né il Test. Le prove reali con Qwen richiedono il server avviato dall'utente.
Il [resoconto](SVILUPPO.md) conserva modifiche, correzioni e limiti.

I risultati, i controlli e le prove tecniche sono esclusi da Git per dimensione.
Conservarli e trasferirli separatamente insieme ai modelli; un pull non li recupera.

# LLM + RAG con recupero DAG/WL

Avvio: ../llm_rag_dag_wl.py.
Cinque esempi scelti con WL; contenuto e formato del prompt LLM restano quelli
attuali. Il DAG non viene inviato al modello.

Questa cartella conserva soltanto preparazione, prove tecniche, indici e risultati
di questo metodo. Non usa gli indici o gli esiti della variante con sintesi.
Il codice comune è in ../strumenti/dag_wl_*.py; gli esperimenti precedenti e il
prototipo non sono stati modificati.

Prima eseguire la validation descritta in ../../validation_dag_wl/README.md.
Dopo la scelta di h e il congelamento esplicito:

~~~bash
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl.py \
  --verifica --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl.py \
  --tecnico --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA \
  --url http://127.0.0.1:8089 --model-path PERCORSO_Q8_0_GGUF
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl.py \
  --esegui --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA \
  --url http://127.0.0.1:8089 --model-path PERCORSO_Q8_0_GGUF
~~~

I percorsi sono segnaposto da sostituire. Senza selezione, --esegui viene rifiutato.
--verifica senza configurazione controlla l'ambiente e dichiara ready_for_test=false.
--tecnico senza configurazione usa soltanto Bell sintetico e --h-tecnico (default 1).
Non esegue i 90 circuiti.

Il contratto include lo stesso GGUF, temperatura 0, generazione e limiti del
protocollo corrente. Si riusano compilatore, verifiche dei fatti e registri del
runner esistente. Nessuno score Test entra nel recupero o nel prompt.

L'indice privato è sotto risultati/llm_rag_dag_wl/indice. È verificato e caricato
una volta per sessione. Il suo costo sta nei file preparazione/, separato dai
tempi per circuito. retrieval.json conserva DAG, tempi, graduatoria completa,
cinque esempi e impronta dell'indice. Gli errori/interruzioni rimangono registrati.

Il riepilogo è sotto risultati/llm_rag_dag_wl/analisi/. Lo stesso comando riprende
solo casi non iniziati, senza ripetere quelli già conclusi. Un cambio di codice,
indice o configurazione blocca una ripresa incompatibile.

Questa è un'estensione sul Test già esposto. Non è una nuova verifica indipendente.

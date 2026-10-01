# LLM + RAG con recupero DAG/WL e sintesi nel prompt

Avvio: ../llm_rag_dag_wl_sintesi.py.
Usa gli stessi parametri WL e gli stessi cinque esempi del metodo solo recupero.
Aggiunge al messaggio una sintesi deterministica del DAG del circuito corrente
e di ciascuno degli esempi E1-E5. Non cambia lo schema della risposta, i controlli
dei fatti, i tentativi, il modello o i parametri di generazione.

La sintesi comprende conteggi delle operazioni, strati di dipendenza, ampiezza
massima degli strati, interazioni fra coppie di qubit e le otto transizioni dirette
più frequenti con ruolo degli operandi. Dichiara quante tipologie di transizione
sono omesse. Gli strati includono le barriere e non sono durate fisiche.
Le statistiche delle interazioni considerano solo le operazioni a due qubit.
La sintesi non è una descrizione completa né una previsione dello score.

La codifica è TOON, come nel prompt originale, con verifica della decodifica.
Il messaggio originale viene conservato come prefisso; la sintesi è aggiunta in
un blocco dedicato. L'adattatore vive solo nel processo di questo avvio: non modifica
i sorgenti del prototipo e viene ripristinato anche in caso di errore.
Il controllo del contesto conta l'intero messaggio aumentato. Nessun taglio
silenzioso degli esempi o della sintesi.

Dopo la validation separata e il congelamento della stessa configurazione usata
dal metodo solo recupero:

~~~bash
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl_sintesi.py \
  --verifica --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl_sintesi.py \
  --tecnico --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA \
  --url http://127.0.0.1:8089 --model-path PERCORSO_Q8_0_GGUF
.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl_sintesi.py \
  --esegui --config-wl PERCORSO_CONFIGURAZIONE_CONGELATA \
  --url http://127.0.0.1:8089 --model-path PERCORSO_Q8_0_GGUF
~~~

Indici, preparazione, prove tecniche, risultati e analisi sono privati di questa
cartella. L'indice è ricostruito dagli stessi train; non legge risultati dell'altro
metodo. Il contratto ne verifica la rappresentazione e la provenienza.

prompt.json conserva le sei sintesi. retrieval.json ne registra l'impronta.
encoding.json continua a descrivere la vista base; il testo effettivo completo
e i token sono conservati nei registri template/tokenize/completion di ogni
tentativo. Le ipotesi restano semanticamente non verificate: non si introducono
nuovi fatti ammessi solo perché il grafo è disponibile.

Valgono i controlli e le regole di ripresa descritti in ../dag_wl_retrieval/README.md.
La guida alla validation è ../../validation_dag_wl/README.md.
Il grafo graphify non è stato aggiornato.

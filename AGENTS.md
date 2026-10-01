# Project guidance

## Local knowledge base

- Treat every file under `archivio/esperimento_v2/knowledge/` as the project's primary local knowledge base.
- Read `archivio/esperimento_v2/knowledge/riassunto_kb_mqt_predictor.md` first for the conversation context, then consult the papers when a claim needs confirmation.
- Distinguish clearly between the 2023 compilation-option predictor and the 2025 MQT Predictor architecture.
- Distinguish facts from the papers, facts from current software documentation, and our own engineering inferences.
- For current APIs and installation details, prefer the official MQT repository, documentation, and PyPI metadata because the software may have changed since publication.

## MQT Predictor testing

- The current experiment uses Python 3.12 with `mqt.predictor==2.4.0` and the exact pins in `uv.lock`. MQT Predictor 2.3.0 is historical material in `archivio/`.
- Use `prototipo/docs/protocollo_sperimentale.md` as the only current experimental protocol. The frozen Dataset and artifacts are under `archivio/esperimento_v2/`; the standalone demonstrator is `prototipo/`.
- Preserve the original corpus in `archivio/esperimento_v2/archivio/protocollo_v1/datasets/expected_fidelity/full/`; v2 still verifies it. Frozen manifest paths are logical references resolved by `resolve_source_reference`, not paths to rewrite.
- Do not assume that `qcompile` works immediately after installation. MQT Predictor 2.x requires trained RL models and a trained supervised device selector.
- A smoke-trained model only validates the pipeline; it is not evidence of compilation quality.
- Preserve trained model artifacts before recreating `.venv`, including runtime copies inside the installed package directory and canonical artifacts under `artifacts/experiments/`.

## Terminology

- When i want to talk about the set for RAG/fine-tuning of the LLM i will talk about "Dataset"
- Instead when i want to talk about the set of couples (circuit,device) for the ML model training, then i will say "Training set"


## Reports

When writing the documentation of an implemented task you have done, follow this principles:
- Use a simple and natural language, easy to understand
- Avoid English loanwords unless necessary
- No long or complex sentences. The goal is to explain what we actually did—the details don't matter!
- The goal is to understand what this part of the project excatly does, in general terms
- If necessary for clarity, create a separated readme to describe the actual task, and place it in the most specific folder of the task implemented

## Scrittura della tesi in forma di articolo scientifico

Queste indicazioni si applicano alla stesura e alla revisione della tesi e prevalgono sulle indicazioni generali di `Reports` per quanto riguarda stile, lunghezza dei periodi e terminologia. Le regole sulla conservazione delle evidenze e sulla riproducibilità restano valide.

- Mantenere rigore scientifico: sostenere le affermazioni con fonti o risultati verificabili, distinguere fatti, ipotesi e interpretazioni e non attribuire ai risultati conclusioni più ampie di quelle consentite dalle condizioni sperimentali.
- Conservare la verbosità esplicativa delle sezioni già approvate: usare una prosa discorsiva, comprensibile e sufficientemente articolata, con periodi anche lunghi quando aiutano a spiegare un concetto. Evitare sia frasi telegrafiche sia ripetizioni e approfondimenti non pertinenti.
- Rispettare un flusso di lettura coerente, mettendosi nei panni di un lettore esperto della materia che incontra per la prima volta questo lavoro. Introdurre termini, componenti, dispositivi e configurazioni prima di impiegarli nelle spiegazioni successive; ordinare le sezioni secondo le dipendenze concettuali. All'interno di ciascuna sezione, quando aiuta la comprensione, raccontare gli esperimenti in ordine cronologico, accompagnando il lettore dal punto di partenza alle difficoltà incontrate, alle scelte compiute, al modo in cui sono state attuate e ai risultati. Usare passaggi discorsivi e periodi sufficientemente articolati, mantenendo il rigore scientifico e senza trasformare il racconto in una cronaca di dettagli operativi.
- Per ciascuna sottosezione sperimentale della sezione 4 seguire, quando applicabile, questo percorso: punto di partenza e composizione dell'ambiente di test; svolgimento della prova; misure, grafici e tabelle; discussione delle implicazioni. Presentare il confronto dei cinque sistemi come una valutazione unitaria, senza ricostruire l'ordine delle idee, le date delle esecuzioni o la loro posizione rispetto al congelamento quando non servono a interpretare il confronto. Conservare questi dettagli nei registri e nei materiali di supporto, mantenendo nel testo le differenze metodologiche e i denominatori rilevanti, senza attribuire al confronto condizioni identiche o una pianificazione preventiva non documentate. La prosa deve accompagnare le figure e spiegare il significato dei risultati, evitando di ripetere sistematicamente i valori già leggibili nei grafici o nelle tabelle.
- Spiegare le motivazioni delle scelte metodologiche e progettuali, le ipotesi su cui si basano e i limiti rilevanti. Una formula, una trasformazione o una metrica deve essere accompagnata dalla definizione delle sue quantità e da una spiegazione del suo ruolo; la semplicità espositiva non giustifica omissioni necessarie alla comprensione.
- Evitare riferimenti espliciti a cartelle e percorsi locali nel testo della tesi, salvo quando siano indispensabili per dimostrare un fatto. Descrivere la funzione degli artefatti e conservare i dettagli operativi e di provenienza nella documentazione di supporto.
- Correggere sintassi, grammatica, punteggiatura e lessico, mantenendo uniformità terminologica e rispettando il significato delle revisioni dell'utente e l'ambito della modifica richiesta.
- Usare i nomi inglesi e gli identificativi originali per campi specifici, dispositivi, configurazioni e componenti internazionali, come RAG, prompt, retriever e hardware quantistico. Preferire LLM a «modello linguistico»; spiegare i termini alla prima introduzione quando necessario e rispettare la distinzione tra Dataset e Training set definita in `Terminology`.
- Presentare gli esperimenti e i test della tesi come valutazioni ufficiali e rigorose, senza definirli genericamente «esplorativi». Se le condizioni differiscono tra sistemi o rispetto ai lavori di riferimento, per esempio nel Training set utilizzato da MQT, specificare la differenza e le sue conseguenze sull'interpretazione del confronto: una differenza di condizioni non rende di per sé invalido il test. Dichiarare comunque i limiti effettivi e mantenere distinta la funzione di prove tecniche, selezione sulla validation e valutazione sul test.
- Considerare le lunghezze previste come riferimenti flessibili: privilegiare la qualità e la chiarezza del racconto degli esperimenti rispetto al rispetto rigido del numero di pagine. Per la sezione 4, «Esperimenti e analisi», le circa 6–7 pagine inizialmente previste, includendo grafici e tabelle, possono diventare circa 8 o aumentare di qualche pagina se questo migliora significativamente la spiegazione del percorso sperimentale. Non tagliare motivazioni o passaggi necessari solo per rientrare nella lunghezza indicativa; l'autore valuterà eventuali riduzioni dopo la lettura. Consultare i report, i documenti LaTeX e i risultati disponibili nella repository per scegliere le evidenze pertinenti, senza trasferirli integralmente nell'articolo o introdurre ripetizioni.
- Selezionare grafici e tabelle per la loro rilevanza rispetto alle domande sperimentali e per la loro capacità di rendere chiari i confronti, includendo anche risultati sfavorevoli quando necessari a un'interpretazione corretta. Preferire confronti riassuntivi tra tutti i sistemi effettivamente confrontabili ed evitare duplicazioni tra testo, grafici e tabelle. Un confronto sugli score, uno sui tempi e uno sui token sono esempi possibili, non una suddivisione obbligatoria; collocare i dettagli secondari nei materiali di supporto.
- Mantenere figure e tabelle compatte, occupando il minor spazio ragionevole senza compromettere la leggibilità umana di testo, assi, legende, unità e valori. Verificare la resa nel documento compilato; le didascalie devono consentire di capire cosa viene confrontato e in quali condizioni.

## Documentazione dello sviluppo e degli esperimenti per la tesi

- Documentare lo sviluppo del progetto e gli esperimenti è un obiettivo principale, insieme al funzionamento del sistema. Conservare decisioni, motivazioni, modifiche e limiti, con particolare attenzione alle prove sperimentali.
- Predisporre la raccolta dei dati prima delle prove. Durante tutta la validation conservare informazioni sufficienti per ricostruire gli esperimenti e produrre successivamente immagini, grafici, tabelle e analisi per la tesi.
- Registrare tutte le configurazioni provate, anche quelle scartate, e tutti i tentativi, inclusi errori, timeout, correzioni e interruzioni. Distinguere prove tecniche, selezione sulla validation e valutazione finale sul test. Non sovrascrivere o eliminare esiti sfavorevoli.
- Conservare dati originali leggibili da programma e metadati di provenienza: circuito e split, identificativi delle esecuzioni, modelli e revisioni, precisione dei pesi, prompt e risposte, evidenze RAG, parametri, seed quando disponibili, versioni del codice e delle dipendenze, hardware e risorse assegnate. Non salvare segreti.
- Raccogliere qualità delle scelte, successi e fallimenti, cause degli errori, numero di chiamate e correzioni, tempi delle diverse fasi, token e consumo di memoria, quando misurabili. Indicare unità, metodo di misura e dati mancanti; distinguere misure, stime e risultati riutilizzati da esecuzioni precedenti.
- Mantenere la separazione tra train, validation e test anche nei registri e nelle analisi. Gli score usati per valutare una decisione non devono entrare nel prompt o nelle evidenze della stessa decisione. Dichiarare sempre denominatori e circuiti effettivamente confrontabili.
- Rendere riproducibili le analisi: generare riepiloghi, tabelle e figure dai dati conservati tramite procedure versionate. Documentare aggregazioni, esclusioni, scelte statistiche e motivazione della configurazione finale.
- Per gli esperimenti di validation produrre anche un documento LaTeX inseribile nella tesi, con descrizione, impostazioni, risultati, grafici, criteri di selezione e limiti. Conservare sorgenti e figure, offrire una compilazione autonoma di verifica e controllare il documento compilato.
- Usare un linguaggio semplice nel testo. La semplicità espositiva non giustifica l'omissione dei dati e dei dettagli necessari a riprodurre gli esperimenti: collocarli in tabelle, appendici o documenti specifici.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).



## Organizzazione dal 25 settembre 2026

- `prototipo/` contiene soltanto il framework utilizzabile, i dati train necessari al RAG e la documentazione corrente.
- `archivio/valutazione/` raccoglie Test, prove esplorative, addestramento MQT, verifiche di sviluppo e risultati. Non collocare nuove campagne sperimentali in `prototipo/`.
- I registri di utilizzo futuri in `prototipo/runs/` sono generati automaticamente e non sono versionati; quelli precedenti al riordino sono in `archivio/valutazione/prove_prototipo/`.
- I README spiegano la funzione delle cartelle e delle sottocartelle. I dettagli dei moduli, la guida e il protocollo corrente sono in `prototipo/docs/`.
- `app.py check` verifica l'installazione; le verifiche complete di sviluppo si avviano da `archivio/valutazione/verifiche_prototipo/checks.py`.

- `.graphifyignore` esclude ambienti, librerie installate e copie duplicate dal grafo; mantenerlo per evitare scansioni degli ambienti locali. Le esclusioni del grafo non eliminano dati dalla repository.


## Organizzazione dal 1 ottobre 2026

- `prototipo/` conserva il framework selezionato e resta autonomo.
- `riproducibilita/` è l'area operativa per nuove esecuzioni: circuiti, MQT, Dataset, LLM, validation, Test, configurazioni, documentazione ed esportazione di nuovi prototipi. Consultare il suo README e la guida.
- `archivio/` conserva storia, risultati e sorgenti congelati. Le copie storiche non sono dipendenze runtime del kit. Non riscrivere manifest congelati né spostarne arbitrariamente gli ingressi.
- Nuove campagne nelle destinazioni del kit, separate per `experiment_id`, oppure in una radice `--output`. Non riusare registri storici come risultati di nuove prove.
- Pesi e dati generati restano esclusi da Git; ingressi e segnaposto devono essere presenti nel clone.
- La guida dichiara le differenze operative dal protocollo storico. Non attribuire ai nuovi strumenti campagne non effettuate.

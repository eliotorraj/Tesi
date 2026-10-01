# Protocollo sperimentale corrente

Questo documento definisce le condizioni scientifiche del progetto e distingue l'uso del prototipo dalle nuove campagne. Il programma pronto all'uso è in `prototipo/`; circuiti configurabili, addestramento, generazione Dataset, validation e Test sono in [riproducibilita/](../../riproducibilita/README.md). Risultati conclusi, piani congelati e cronologia restano nell'archivio e non vengono riscritti quando si aggiorna una guida.

L'ambiente sperimentale usa Python 3.12 e MQT Predictor 2.4.0, con le versioni esatte del [lock del kit](../../riproducibilita/uv.lock). Il prototipo contiene soltanto le dipendenze necessarie all'uso. I numeri di versione del corpus, dello studio LLM e del contratto di risposta identificano oggetti diversi.

## 1. Obiettivo e unità di confronto

Si valuta se un LLM, aiutato da esempi di compilazione, sceglie una coppia dispositivo/configurazione Qiskit di buona qualità. La metrica è `expected_fidelity` sui Target sintetici MQT Bench. Non si misura un'esecuzione su un computer quantistico reale.

L'unità di confronto è il circuito. Chiamate aggiuntive, seed e tentativi non diventano osservazioni indipendenti. Le domande riguardano qualità, copertura, contributo degli esempi RAG, confronto con MQT e scelte casuali, tempi e token.

## 2. Dati e separazione degli ingressi

Il corpus distribuito contiene 600 OpenQASM 2: 422 train, 88 validation e 90 test. Il train ha 396 contenuti distinti per SHA-256. Gli alias byte-identici restano nel manifest ma non diventano esempi RAG o campioni supervisionati aggiuntivi. I due realamprandom a 2 qubit semanticamente uguali restano nel train; la deduplicazione per hash non dimostra diversità algoritmica.

**Dataset** indica gli esempi per RAG/LLM. **Training set** indica i dati circuito/dispositivo per il selettore supervisionato MQT; la sua tabella finale assegna a ciascun circuito il miglior dispositivo osservato.

Train costruisce trasformazione, esempi e modelli. Validation sceglie le impostazioni. Test misura soltanto scelte già fissate. Score e vincitore del circuito corrente non entrano nel suo prompt, nelle sue evidenze o nella decisione di un concorrente.

Per un nuovo corpus dichiarare gli split prima di `prepara`. I controlli rilevano contenuti e sequenze di istruzioni sovrapposti, non ogni equivalenza quantistica né famiglie condivise. Per nuovi ingressi famiglia e provenienza devono essere fornite, non dedotte arbitrariamente.

Il Test distribuito è già stato valutato. Riutilizzarlo permette una replica, non lo rende un nuovo Test indipendente. Restano pertinenti i limiti documentati: esposizione nel pilota di `qpeexact_indep_tket_60` e `routing_indep_qiskit_12`, selezione LLM adattiva e possibile presenza di MQT Bench nei dati di addestramento degli LLM. Una nuova partizione non elimina automaticamente questi rischi.

## 3. Ambiente e spazio delle scelte

Il [catalogo del kit](../../riproducibilita/configurazioni/catalogo.json) distribuisce cinque Target: `ibm_falcon_27`, `ibm_heron_133`, `ibm_falcon_127`, `ibm_heron_156`, `quantinuum_h2_56`. I Target sono ricostruiti da MQT Bench 2.2.3 e verificati per impronta. Il filtro esclude quelli incompatibili con qubit e vincoli.

| Configurazione | Livello | Layout | Routing |
| --- | --- | --- | --- |
| `o2_default_default` | 2 | predefinito | predefinito |
| `o3_default_default` | 3 | predefinito | predefinito |
| `o2_sabre_sabre` | 2 | sabre | sabre |
| `o2_dense_sabre` | 2 | dense | sabre |
| `o2_trivial_sabre` | 2 | trivial | sabre |
| `o3_sabre_sabre` | 3 | sabre | sabre |
| `o3_dense_sabre` | 3 | dense | sabre |
| `o3_trivial_sabre` | 3 | trivial | sabre |
| `o2_sabre_lookahead` | 2 | sabre | lookahead |
| `o2_sabre_basic` | 2 | sabre | basic |
| `o3_sabre_lookahead` | 3 | sabre | lookahead |
| `o3_sabre_basic` | 3 | sabre | basic |

Le opzioni predefinite lasciano l'algoritmo a Qiskit. Per la generazione del Dataset e della matrice validation si usano seed 0, 1, 2, limite per compilazione 100 secondi e `num_processes=1` dentro Qiskit. I sei processi esterni predefiniti si riducono prima del congelamento se la RAM non basta. Cambiare parallelismo, hardware o timeout è una condizione da registrare.

Una mediana eleggibile richiede tutti e tre i seed riusciti. Un massimo fra coppie eleggibili è il miglior riferimento osservato; se la matrice è incompleta non è un oracle esaustivo. Nessun errore viene riprovato silenziosamente fino al successo.

## 4. Recupero e contratto della risposta

Il recupero ordinario usa 49 caratteristiche: conteggi, profondità e qubit trasformati con `log1p`, più cinque indicatori strutturali. Ogni coordinata viene divisa per il massimo assoluto del solo train, con divisore 1 se nullo. Non si applicano centratura o taglio. La distanza è Manhattan; parità e filtri sono deterministici. Qdrant locale 1.19.0 conserva l'indice derivato. Non occorre un servizio cloud o un modello di embedding.

Il percorso ordinario recupera cinque esempi train. Ogni esempio mostra il dispositivo vincente e fino a tre configurazioni di quel dispositivo, non tre dispositivi diversi. Gli score del train possono comparire nelle evidenze; quelli del circuito da decidere no.

La vista dell'LLM contiene caratteristiche complete, dispositivi compatibili, catalogo e, con RAG, gli esempi. Omette QASM e provenienza estesa. Il codec TOON ufficiale 4.1.1 viene controllato mediante ricostruzione; la risposta resta JSON.

Il contratto facts v4 richiede `selected_device`, `config_id`, uno o due fatti distinti e un'ipotesi fino a 1.000 caratteri. La coppia deve essere ammessa; i fatti vengono verificati soltanto contro il prompt. L'ipotesi non è verificata semanticamente.

Si accetta la prima risposta conforme con fatti corretti. Si consentono al massimo tre tentativi completi con correzioni. Al terzo si può accettare una coppia conforme con fatti non verificati, dichiarando `accepted_with_unverified_facts`. Schema o coppia invalidi restano fallimenti. Non si sceglie la risposta in base allo score futuro.

## 5. Modelli e validation

Il prototipo pronto all'uso fissa **Qwen3.5-4B Q8_0 a temperatura 0**, selezionato nello studio `local-llm-v2`. Identità dei pesi, SHA-256 e parametri sono in `prototipo/config.json`; il nome commerciale da solo non identifica l'artefatto.

Per una nuova selezione il registro distribuito propone Qwen, Phi e Gemma Q8_0 con temperature 0, 0,4 e 0,7. Si può scegliere un altro elenco prima del congelamento. L'impostazione di riferimento è contesto 60.000, massimo output 4.096, pensiero esteso disattivato e parametri di generazione conservati nel JSON. Runtime, driver, backend, thread e quantizzazione sono condizioni dell'esecuzione.

Le decisioni validation sono sigillate prima che il valutatore legga gli score. Il criterio predefinito ordina per maggiore copertura di scelte valide e compilabili, minore regret mediano sui circuiti comuni, meno correzioni e chiamate, tempi e token se completi, infine ordine lessicografico. `mean_regret` è un'alternativa configurabile prima dell'esecuzione, da dichiarare.

Per una scelta con score S e miglior riferimento osservato R sullo stesso circuito, il regret è R − S: misura la perdita rispetto allo spazio effettivamente osservato. Copertura del riferimento e denominatori devono accompagnare il risultato. Un regret mediano nullo non rende ottima ogni scelta.

La selezione WL confronta le profondità dichiarate in `wl_iterations`, privilegiando copertura e regret medio della migliore coppia fra i cinque esempi recuperati. Valuta il recupero strutturale sulla validation, non le successive decisioni dell'LLM sul Test.

## 6. MQT Predictor

Il confronto usa l'architettura in cui un selettore supervisionato sceglie il dispositivo e una politica RL specifica sceglie i passaggi di compilazione. È distinta dal predittore di opzioni di compilazione del lavoro del 2023.

Occorrono cinque politiche RL e il classificatore addestrato sul solo train. La sola installazione di MQT Predictor non rende disponibile `qcompile`. Il riferimento distribuito richiede 100.000 passi, normalmente 100.352 al termine del rollout PPO.

Il selettore usa un rappresentante per hash train; il corpus distribuito prevede 396 campioni e 1.878 coppie circuito/dispositivo compatibili. Le classi sono i dispositivi effettivamente vincenti, anche se non comprendono tutti e cinque. Non creare classi artificiali. La deduplicazione supervisionata non implica che ogni fase RL usi la stessa deduplicazione.

Prima del Test MQT verificare copertura richiesta, identità dei modelli canonici e delle copie runtime, cinque prove minime RL e una prova ML+RL su Bell. Un addestramento breve verifica il software, non la qualità. Un selettore costruito su raccolta incompleta va identificato come condizione diversa e non presentato come quello completo.

## 7. Nuovo Test

Il piano predefinito del kit comprende **LLM+RAG, LLM senza RAG, Random, recupero casuale e MQT**. Sono disponibili anche RAG k=1/k=10 e WL con/senza sintesi. Dichiarare i metodi prima di `prepara`; completare la validation e i requisiti specifici prima di `test congela`. L'elenco non introduce provider remoti o fine-tuning non implementati.

Confrontare i metodi sugli stessi circuiti congelati. Il percorso senza RAG non recupera esempi e richiede un fatto sulla capacità del dispositivo; non inventa evidenze. Random campiona una coppia compatibile con seme dichiarato. Gli LLM mantengono tre tentativi per la conformità. Ogni metodo esegue una sola compilazione per circuito con il seed Test dichiarato, predefinito 0 per Qiskit; il seme interno MQT non viene assimilato a quello Qiskit.

Le compilazioni sono isolate con timeout e gli esiti terminali non vengono sostituiti. Non si cambia configurazione dopo un fallimento o dopo aver visto risultati parziali. Nel kit interruzioni e problemi di trasporto restano registrati, senza il recupero automatico del supervisore della validation conservato nell'archivio.

Un oracle facoltativo produce una griglia separata. Non è un decisore e nessun suo score entra nei prompt. I controlli di compilazione riguardano base e collegamenti; non dimostrano equivalenza quantistica formale.

## 8. Misure, conservazione e interpretazione

Conservare tutti i tentativi, inclusi timeout, errori, interruzioni e candidati scartati. I registri comprendono circuito, split, impronte, configurazione, modello e revisione, prompt, esempi, risposte, chiamate, correzioni, token e tempi quando misurati. Non salvare segreti.

`expected_fidelity` combina le fedeltà delle operazioni del Target con l'arrotondamento di MQT 2.4.0. Indicare successi, fallimenti e score mancanti. Le medie si calcolano sugli score disponibili con denominatore; un fallimento non diventa zero. I confronti appaiati usano i circuiti comuni e ne conservano gli identificativi.

Tempi in secondi, token e memoria sono quantità diverse. Una misura assente rimane tale; una stima non diventa un dato misurato. Il nuovo server Linux registra RAM disponibile di sistema, non consumo energetico o memoria/temperatura GPU. Non equiparare questo registro alle misure del monitor AMD del fisso.

I report del kit sono generati dai registri e identificati mediante impronte. Comprendono JSON, CSV e LaTeX; il report validation include una figura. Le analisi descrittive non dimostrano da sole superiorità statistica o equivalenza. Non trasferire automaticamente piani statistici di precedenti rapporti a una nuova campagna.

Ogni nuovo esperimento ha un `experiment_id` e destinazioni proprie. Modifiche agli ingressi o al codice dopo il congelamento richiedono un nuovo identificativo. Gli output, i pesi e le copie runtime dei modelli MQT devono essere salvati separatamente da Git. Le [condizioni del kit](../../riproducibilita/documentazione/condizioni.md) completano le istruzioni operative.

## 9. Uso dimostrativo e risorse

`app.py run` su un circuito personale o su Bell è un utilizzo del prototipo, non un Test di generalizzazione. I profili CPU e GPU ridotti usano 16.384 token; il desktop ne usa 60.000. Un PC Linux con 16 GB può tentare la prova CPU se ha memoria libera sufficiente; non è una garanzia di completamento o di qualità equivalente.

Cambiare contesto, backend o hardware non modifica automaticamente le regole scientifiche. Per un confronto dichiarare queste differenze prima delle prove e conservare i registri. La [guida pratica](guida_passo_passo.md) separa il nuovo utente Linux dal fisso WSL/Windows; la [guida di riproducibilità](../../riproducibilita/documentazione/guida.md) accompagna una nuova campagna completa.

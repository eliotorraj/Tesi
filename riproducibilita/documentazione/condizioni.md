# Condizioni, limiti e conservazione

Questa area rende riutilizzabili gli strumenti del progetto. Ogni esecuzione produce i propri risultati: non importa score storici facendoli passare per nuove misure. Anche con stessi circuiti, pesi e seed, tempi, timeout e scelte LLM possono variare con CPU, GPU, memoria, parallelismo e runtime.

Il riferimento scientifico resta il protocollo corrente. Formule e controlli di compilazione derivano dai sorgenti originali; le interfacce sono adattate per avere percorsi e numero di circuiti configurabili. Il criterio LLM predefinito privilegia copertura e regret mediano; è disponibile anche `mean_regret`, da dichiarare prima di iniziare.

## Condizioni distribuite

Il corpus principale contiene 600 sorgenti: 422 train, 88 validation e 90 test. I contenuti train byte-distinti sono 396. Il manifest originale conserva famiglia e generatore. Per nuovi file queste informazioni sono indicate come fornite dall'utente; non si inventa una famiglia scientifica. Hash e sequenza di istruzioni impediscono sovrapposizioni evidenti fra split, ma non provano l'assenza di equivalenze quantistiche generali o algoritmi condivisi.

Il catalogo contiene cinque Target sintetici MQT Bench 2.2.3, dodici configurazioni Qiskit e seed 0, 1, 2. `expected_fidelity` è il prodotto delle fedeltà delle operazioni sul Target, con l'arrotondamento di MQT Predictor 2.4.0. Non è una misura su hardware quantistico. I tentativi dipendono dalla compatibilità in qubit.

`modelli_llm/provenienza_originale.json` identifica repository, revisioni, file e SHA-256 dei GGUF Q8_0 di Qwen, Phi e Gemma. Non attesta indipendentemente la revisione base di ciascuna conversione. Il riferimento software è llama.cpp b10930. Il registro distribuito richiede contesto 60.000, cache q8_0, batch 512 e micro-batch 128. Linux CPU, Vulkan/CUDA e il server Windows del fisso sono condizioni di esecuzione da distinguere. Pesi e programmi sono forniti separatamente, rispettandone le licenze.

## Configurazioni nominate

`configura.py nuovo` crea impostazioni separate dai riferimenti distribuiti. Per impostazione iniziale seleziona Qwen e tre sistemi Test senza MQT; il profilo `cpu` riduce contesto, batch, processi e strati GPU. Queste sono condizioni nuove, visibili nel riepilogo e nelle revisioni, e non riproducono automaticamente la campagna di riferimento. Circuiti, Target, configurazioni e temperature si riducono solo con scelte esplicite.

Il configuratore accetta il sottoinsieme di Target e opzioni previsto dagli schemi; non certifica l'eseguibilità di un GGUF arbitrario o la capacità della macchina. Dopo la preparazione si modifica un esperimento soltanto duplicandone le impostazioni con un altro nome, senza riscrivere i risultati precedenti.

## Risorse e condizioni da dichiarare

Gli avviatori del kit mantengono facts v4 e tre tentativi completi, ma non riproducono il supervisore Windows con sensori termici e recupero automatico delle interruzioni della validation storica. Qui un'interruzione o un errore di trasporto resta un esito conservato, senza rigenerazioni silenziose. Dichiarare questa differenza confrontando costi e fallimenti con gli esiti precedenti.

Una GPU compatibile è consigliata per l'inferenza. Il minimo indicativo di 16 GB riguarda una prima prova ridotta del prototipo, non tutti i candidati o tutte le campagne. Contesto 16.384, meno processi o una griglia ridotta devono essere dichiarati prima del congelamento. Il rilevamento `--list-devices` usa il backend llama.cpp; i Target IBM/Quantinuum del catalogo sono invece hardware quantistico sintetico.

Il server del kit registra eseguibile, dispositivi e argomenti, ma non raccoglie temperatura, memoria GPU o energia. Sul fisso i `.ps1` mantengono le misure AMD: non attribuirle alle esecuzioni Linux generiche. I percorsi WSL/Windows richiedono trasporto esplicito e accesso verificabile allo stesso GGUF.

Il trainer MQT conserva processi spawn e deduplicazione per hash. L'avvio ordinario richiede copertura completa dei campioni previsti prima di pubblicare il selettore. Un confronto con un selettore ottenuto da raccolta incompleta, per esempio con 384 campioni e timeout differenti, deve dichiarare quelle condizioni. Un Training set completo produce un nuovo artefatto e non sostituisce retroattivamente quello valutato. Una politica addestrata brevemente per collaudare il codice non dimostra la qualità di compilazione.

La selezione WL del kit minimizza il regret medio della migliore coppia fra i cinque esempi recuperati, dando priorità alla copertura. Non misura da sola la qualità delle successive decisioni LLM. La configurazione scelta viene congelata prima del Test.

Test supporta LLM+RAG, LLM senza RAG, Random, recupero casuale, MQT, RAG k=1/k=10 e WL con/senza sintesi. Non introduce fine-tuning LLM o provider remoti non implementati.

## Corpus esterno

I cinquanta QASMBench sono separati: 30 small, 15 medium e 5 large, con manifest, licenza e revisione. Per usarli preparare una nuova directory train/validation/test, copiarvi gli ingressi desiderati e dichiararla nella configurazione. I QASM devono essere direttamente dentro gli split e avere nomi univoci. Conservare intatta la copia in `esterni/`.

La procedura rigenera dati e selezione per il nuovo identificativo. Non trasforma un risultato ottenuto su un test esterno in un criterio retroattivo per scegliere il modello.

## Evidenze da conservare

Conservare configurazione, codice, lock, tutte le aree di output, registri server e pesi o revisioni verificabili. Le politiche canoniche sono sotto `mqt/artefatti/<id>/models/rl`; il selettore è sotto `mqt/artefatti/<id>/modelli`. Le copie installate nella `.venv` sono operative e devono coincidere con quelle canoniche.

I riepiloghi sono derivati; tentativi, prompt, risposte e compilazioni sono evidenze primarie. Non sostituire fallimenti con successi di una prova successiva. Tempi in secondi e token vengono riportati quando misurati; memoria di picco e consumo energetico non sono raccolti da questi avviatori. I dati mancanti restano espliciti.

Pesi, ambienti, indici e nuovi output non sono caricati automaticamente su GitHub. Nel clone si trovano ingressi e procedure. Il collaudo con server sintetico verifica il software: non è un risultato sperimentale degli LLM né un addestramento MQT.

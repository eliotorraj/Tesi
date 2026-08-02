# Prototipo LLM per suggerimento e compilazione quantistica

Questa directory contiene lo scheletro architetturale del prototipo.

L'obiettivo è tenere separati:

- dialogo con l'utente;
- lettura e analisi deterministica del circuito;
- compatibilità hardware;
- ricerca nel Dataset dei casi più utili;
- richiesta all'LLM;
- controllo del suggerimento prodotto dall'LLM;
- compilazione Qiskit autorizzata dall'utente.

## Flusso

~~~mermaid
flowchart LR
    UI["Interfaccia utente"] --> C["Gestore delle richieste"]
    C --> P["Lettura QASM + caratteristiche del circuito"]
    P --> F["Filtro di compatibilità"]
    H["Catalogo hardware MQT"] --> F
    F --> R["Ricerca di casi simili"]
    D["Dataset"] --> R
    R --> B["Preparazione della richiesta"]
    B --> L["Collegamento con l'LLM"]
    L --> V["Validatore deterministico"]
    V -->|"non valida e tentativi disponibili"| B
    V -->|"valida"| C
    C --> UI

    UI -->|"conferma esplicita"| C2["Richiesta di compilazione"]
    C2 --> S["Suggerimento già controllato"]
    S --> Q["Compilazione deterministica con Qiskit"]
    Q --> X["Controllo dei gate e delle connessioni"]
    X --> UI
~~~

La compilazione non è uno strumento usato liberamente dal modello. L'LLM propone
un piano Qiskit limitato a parametri ammessi; il programma lo controlla e
Qiskit lo esegue soltanto dopo la conferma dell'utente.

## Componenti

I nomi nella seconda colonna sono quelli usati nel codice. La terza colonna
spiega il loro significato.

| Parte | Nome nel codice | Cosa fa |
| --- | --- | --- |
| Gestore della UI | PrototypeController | Riceve le richieste della UI e conserva temporaneamente i suggerimenti già controllati |
| Lettore del circuito | QasmRequestParser | Legge OpenQASM 2 e calcola le 49 caratteristiche MQT |
| Catalogo hardware | MqtHardwareCatalog | Carica le informazioni sugli hardware disponibili |
| Filtro di compatibilità | WidthCompatibilityFilter | Esclude gli hardware troppo piccoli o vietati dall'utente |
| Ricerca nel Dataset | ContextRetriever | Trova nel Dataset i casi più simili alla richiesta corrente |
| Preparazione della richiesta | StructuredPromptBuilder | Prepara il testo e i dati da inviare all'LLM |
| Collegamento con l'LLM | LlmGateway | Invia la richiesta all'LLM e ne riceve la risposta; deve ancora essere realizzato |
| Controllo della risposta | StructuredRecommendationValidator | Verifica hardware, metrica e parametri Qiskit suggeriti |
| Coordinatore | PrototypeService | Esegue i passaggi nell'ordine corretto e riprova quando la risposta non è valida |
| Compilatore | QiskitDeterministicCompiler | Compila localmente con Qiskit e controlla il risultato |

Il filtro iniziale non confronta i gate del circuito ancora indipendente
dall'hardware con i gate nativi. Quel confronto eliminerebbe hardware validi
prima che Qiskit abbia tradotto il circuito. All'inizio si controllano quindi la
larghezza del circuito e i vincoli dell'utente. Dopo la compilazione si
controllano i gate e le connessioni del circuito ottenuto.

## Struttura dei file

~~~text
prototype/
  README.md
  quantum_assistant/
    __init__.py
    controller.py
    factory.py
    models.py
    ports.py
    services.py
    adapters/
      __init__.py
      compilation.py
      context.py
      llm.py
      parsing.py
      validation.py
~~~

## Dati scambiati tra la UI e il programma

La UI invia una richiesta chiamata UiSubmission che contiene:

- testo dell'utente;
- circuito OpenQASM 2;
- metrica da ottimizzare (figure of merit);
- eventuale lista degli hardware ammessi;
- vincoli aggiuntivi.

Il gestore restituisce:

- risposta controllata;
- spiegazione e avvisi;
- hardware compatibili e non compatibili;
- numero di tentativi fatti con l'LLM;
- identificativi degli esempi recuperati dal Dataset;
- indicazione che la compilazione richiede conferma.


## Formato obbligatorio della risposta dell'LLM

Il componente che comunica con l'LLM deve restituire dati organizzati in questo modo:

~~~json
{
  "selected_device": "ibm_falcon_27",
  "figure_of_merit": "expected_fidelity",
  "compiler": "qiskit",
  "qiskit_plan": {
    "optimization_level": 2,
    "seed_transpiler": 0,
    "layout_method": "sabre",
    "routing_method": "sabre"
  },
  "explanation": "Spiegazione leggibile dall'utente.",
  "evidence": [
    "live_request.circuit.features",
    "record_id:..."
  ],
  "warnings": [
    "Expected fidelity è una stima, non una misura hardware."
  ]
}
~~~

Il programma rifiuta la risposta nei seguenti casi:

- hardware non presente tra quelli compatibili;
- metrica diversa da quella richiesta;
- compilatore diverso da Qiskit;
- livello di ottimizzazione fuori dall'intervallo 0-3;
- seed non intero o negativo;
- metodo di posizionamento o instradamento non ammesso;
- spiegazione o liste malformate.

Gli errori trovati vengono aggiunti alla richiesta successiva, in modo che l'LLM
possa correggersi. Dopo il numero massimo di tentativi il programma si ferma e
segnala che non è riuscito a ottenere una risposta valida.

## Dataset, richiesta all'LLM e RAG

Per il primo prototipo conviene cercare nel Dataset pochi casi simili e
aggiungerli alla richiesta inviata all'LLM. Questo metodo viene chiamato RAG.
È una buona prima scelta perché:

- il Dataset e gli hardware cambieranno durante gli esperimenti;
- è utile indicare gli esempi usati;
- non serve riaddestrare il modello a ogni aggiornamento;
- si può controllare quanta informazione viene inviata all'LLM.

Il lettore del file JSON "llm_mqt_full_pipeline_[metric].json" usa soltanto il campo input di ogni esempio. Rispetta
quindi la regola del Dataset attuale:

- input: utilizzabile nella richiesta all'LLM;
- expected_output: risultato atteso, utilizzabile per l'addestramento;
- deterministic_ground_truth: informazione riservata alla valutazione.

Il RAG consulta il Dataset completo, ma non lo invia interamente all’LLM. Per ogni richiesta cerca un numero limitato di casi simili, ad esempio cinque, e aggiunge soltanto quelli alla richiesta. Questi casi possono contenere caratteristiche del circuito, hardware scelto, punteggi, passi RL e circuito compilato. Per velocizzare la ricerca potrà essere creato un indice derivato dal Dataset.


## Come si collegano e si avviano i componenti

La funzione build_default_service prepara il servizio principale e collega il
lettore del circuito, il filtro di compatibilità, la ricerca nel Dataset, il
controllo della risposta e il compilatore Qiskit.

Rimane da fornire il componente che effettua davvero la chiamata all'LLM. Nel
codice seguente si chiama collegamento_llm:

~~~python
from pathlib import Path

from prototype.quantum_assistant.factory import build_default_service

# Segnaposto: sarà sostituito dopo aver scelto l'LLM.
collegamento_llm = ...

service = build_default_service(
    device_names=("ibm_falcon_27", "ibm_falcon_127"),
    dataset_path=Path("datasets/llm_mqt_full_pipeline_expected_fidelity.json"),
    llm_gateway=collegamento_llm,
    max_llm_attempts=3,
    retrieval_limit=5,
)
~~~

Questo esempio significa:

- device_names: hardware che il prototipo deve prendere in considerazione;
- dataset_path: posizione del file del Dataset;
- llm_gateway: componente che invia la richiesta all'LLM e riceve la risposta;
- max_llm_attempts=3: al massimo tre tentativi se la risposta non è valida;
- retrieval_limit=5: inserisce nella richiesta al massimo cinque casi simili
  trovati nel Dataset.

collegamento_llm è quindi un segnaposto, non un oggetto già disponibile. Il
frammento non è ancora eseguibile così com'è. Prima bisognerà scegliere quale
LLM usare e scrivere il piccolo componente che sa comunicare con quel servizio
o con un modello locale.

Questa parte viene fornita dall'esterno per poter cambiare LLM senza modificare
il lettore del circuito, il filtro, il validatore o il compilatore. Al momento
non è stato scelto alcun servizio LLM e il prototipo non effettua chiamate di
rete.

## Limiti intenzionali dello scheletro

- nessuna interfaccia utente concreta;
- nessun collegamento concreto a un LLM;
- nessun motore di ricerca vettoriale per il RAG;
- Dataset per LLM ancora incompleto (non sta ancora sfruttando punteggi, passi RL e circuiti compilati. Quando il formato
  definitivo del Dataset sarà pronto, dovremo aggiornare la ricerca RAG affinché utilizzi anche queste informazioni)

Questi confini permettono di completare prima il modello supervisionato e il
Dataset, mantenendo già stabile l'architettura applicativa.

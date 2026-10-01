# Prototipo: dal circuito alla compilazione

Questa cartella contiene il framework utilizzabile in autonomia. Riceve un circuito OpenQASM 2, filtra i dispositivi compatibili, recupera esempi train e chiede a Qwen una configurazione. Controlla la risposta e, su richiesta, compila il circuito con Qiskit.

Il programma non legge `archivio/`. Utilizza **Qwen3.5-4B Q8_0 a temperatura 0**, secondo la selezione local-llm-v2. La compilazione adatta il circuito a Target sintetici con Qiskit: non simula lo stato quantistico e non invia lavori a un computer quantistico.

## Iniziare

Seguire la [guida passo passo](docs/guida_passo_passo.md), dalla preparazione del computer al primo risultato. Servono Python 3.12, Node.js 22 con npm, il runtime llama.cpp e i pesi GGUF indicati nella guida. `setup.ps1` e `setup.sh` preparano le dipendenze; i pesi sono forniti separatamente.

Dopo la preparazione e l'avvio del server, da `prototipo/`:

```powershell
.\.venv\Scripts\python.exe app.py check
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27 --compile
```

Il comando stampa la scelta e il percorso dei registri. Senza `--compile` restituisce la raccomandazione. Il Bell incluso serve a provare l'uso, senza utilizzare il Test sperimentale.

## Come è organizzata

| Elemento | Funzione |
| --- | --- |
| `app.py` | Avvio del programma: preparazione, controllo dell'installazione e uso su un circuito. |
| [prototype/](prototype/README.md) | Moduli per leggere il circuito, recuperare esempi, interrogare il modello, controllare e compilare. |
| [data/](data/README.md) | Esempi train, circuiti e impronte necessari al recupero RAG. |
| [configs/](configs/README.md), `config.json` | Configurazioni Qiskit consentite e impostazioni del modello scelto. |
| [schemas/](schemas/README.md) | Forme ammesse per richieste, evidenze e risposte. |
| [qiskit_dataset/](qiskit_dataset/README.md), [scripts/](scripts/README.md) | Catalogo e controlli di integrità usati dal framework. |
| `portable_features.py` | Estrazione delle caratteristiche; provenienza e licenza nei file accanto. |
| `examples/` | Piccolo circuito Bell per il primo utilizzo. |
| [runtime/](runtime/README.md) | Programmi e indice locale installati o generati durante la preparazione. |
| `setup.*`, `server-*.ps1`, `verify-model.ps1`, `AmdSensors.cs` | Preparazione e avvio del modello, verifica dei pesi e controllo delle risorse. |
| [docs/](docs/README.md) | Guida, protocollo corrente e documenti tecnici. |
| `runs/` | Registri dei nuovi utilizzi; viene creata dal programma ed è esclusa da Git. |

I dati distribuiti comprendono 396 esempi train unici. Il manifest conserva le 422 sorgenti train, inclusi gli alias. Nessun risultato validation o Test viene usato per decidere sul nuovo circuito.

## Come leggere il risultato

Una coppia dispositivo/configurazione ammessa può essere accettata al terzo tentativo anche con fatti non verificati: il risultato lo dichiara. L'ipotesi libera del modello non è certificata semanticamente. Il profilo laptop ha un contesto più piccolo del desktop; una richiesta troppo grande viene fermata senza eliminare esempi in silenzio.

I particolari sono in [architettura e flusso](docs/architettura_e_flusso.md) e [installazione e runtime](docs/installazione_e_runtime.md).

## Esperimenti e sviluppo

Test, addestramento MQT, verifiche complete e risultati sono in [archivio/valutazione/](../archivio/valutazione/README.md). Sono attività distinte dall'uso del framework. I vecchi registri `runs/` sono conservati fra le prove precedenti nell'archivio.

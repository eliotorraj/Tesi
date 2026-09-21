# Prototipo Qwen con esempi train

Questa cartella funziona senza leggere `archivio/`. Riceve un circuito OpenQASM 2,
recupera cinque esempi train, chiede a Qwen una coppia dispositivo/configurazione,
controlla la risposta e, se richiesto, compila con Qiskit.

La configurazione deriva da **local-llm-v2: Qwen3.5-4B Q8_0, temperatura 0**.
Usa il prompt `facts-v4-toon3-20260919`, il contratto 4.0.0 e al massimo tre
risposte complete. Dopo la terza, una coppia ammessa puo essere accettata anche
con fatti non verificati: questo esito e sempre dichiarato. L'ipotesi libera
non riceve una certificazione semantica. Un errore di trasporto interrompe la
prova; non viene mascherato da una nuova risposta del modello.

## Preparazione Windows

Servono Python **3.12** (con launcher `py`) e Node.js **22**. Copiare tutta la
cartella sul computer, inclusi `runtime/cpu/` e il GGUF se gia disponibili.
Gli ambienti Python, gli indici e i registri non vanno copiati da Linux a Windows.
Ricrearli con:

```powershell
cd C:\percorso\prototipo
.\setup.ps1 -RuntimeProfile cpu
# Se il runtime non e stato copiato:
.\setup.ps1 -RuntimeProfile cpu -DownloadRuntime
```

Lo script installa le dipendenze CPU fissate in `requirements.txt`. Non installa
Torch, CUDA, ROCm, OpenVINO o software NPU. Il server CPU non usa la GPU integrata
ne la NPU. Il runtime e [llama.cpp b10930](https://github.com/ggml-org/llama.cpp/releases/tag/b10930).
Il codec TOON ufficiale 4.1.1 e incluso con la propria licenza.
Per il desktop usare `-RuntimeProfile desktop`; questo profilo richiede il
runtime Vulkan e PsSuspend gia verificato, e conserva i controlli termici AMD.
`-DownloadRuntime` autorizza solo questi piccoli runtime, mai i pesi del modello.

Il modello selezionato e `Qwen3.5-4B-Q8_0.gguf`, **4.482.403.488 byte**, SHA256:
`10cc391b403021dd11c614679d2fd92f611c3681d29e29651b717316965d61e1`.
La [revisione GGUF precisa](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/e87f176479d0855a907a41277aca2f8ee7a09523)
e registrata anche in `config.json`. Copiare il file esistente sul laptop,
per esempio in `runtime/models/Qwen3.5-4B-Q8_0.gguf`: non serve riscaricarlo.
Il server ne verifica dimensione e SHA256 prima di avviarsi.

## Avvio e utilizzo

In una finestra PowerShell, avviare uno dei due server:

```powershell
# Laptop Intel Ultra 7 155H, RAM 16 GB:
.\server-laptop.ps1 -ModelPath C:\modelli\Qwen3.5-4B-Q8_0.gguf
# Desktop AMD attuale:
.\server-desktop.ps1 -ModelPath D:\modelli\Qwen3.5-4B-Q8_0.gguf
```

Il processo di inferenza parte nascosto. Lasciare aperta la finestra del
controllore; Ctrl+C termina il server che essa ha avviato. I registri server
sono nella cartella stampata all'avvio (`-RunRoot` permette di sceglierla).
In una seconda finestra, dopo che il server risponde:

```powershell
.\.venv\Scripts\python.exe app.py check
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27
.\.venv\Scripts\python.exe app.py run examples/bell.qasm --profile laptop --device ibm_falcon_27 --compile
```

L'esempio laptop limita esplicitamente il confronto a IBM Falcon 27; il budget
di contesto della richiesta completa con cinque dispositivi non e garantito.
Per il desktop sostituire `laptop` con `desktop` e omettere il vincolo se desiderato. `--device ibm_falcon_27`
limita i candidati; l'opzione e ripetibile. La risposta riporta tutti i parametri
proposti per `qiskit.compiler.transpile`. `--compile` applica la proposta con
`seed_transpiler=0`, modificabile con `--seed-transpiler`.
Il Bell incluso e un circuito tecnico creato appositamente, non appartiene
alla valutazione sul test.

In WSL/Linux sono disponibili `setup.sh` e gli stessi comandi `app.py`.
Per lo sviluppo locale e possibile usare `../.venv/bin/python app.py ...`;
questa comodita non e una dipendenza del prototipo. In WSL, le chiamate al
server Windows passano da `curl.exe`; su Windows nativo usano HTTP Python.

## Profili e memoria

| Impostazione | Desktop GPU | Laptop CPU |
| --- | --- | --- |
| Pesi | Q8_0 | Q8_0 |
| Temperatura | 0 | 0 |
| Contesto totale | 60.000 token | 16.384 token |
| Massimo output | 4.096 token | 4.096 token |
| Cache KV | q8_0 | q8_0 |
| Batch / microbatch | 512 / 128 | 128 / 64 |
| Thread | 6 | 6, modificabili |

Il profilo laptop e una **prova tecnica diversa dal profilo sperimentale**.
Non dimostra le stesse prestazioni o la stessa qualita osservata sul desktop.
Il prompt conserva cinque esempi e tutte le caratteristiche: se input piu
4.096 token supera il contesto, il programma si ferma prima della generazione.
Non accorcia silenziosamente circuito o esempi. Circuiti con grandi Target
possono quindi superare il profilo laptop.

Budget prudenziale stimato, non misurato sul laptop: circa 4,18 GiB per i
pesi, 1-3 GiB per cache e calcolo, 1-2 GiB per Python/Qiskit/Qdrant, oltre a
Windows e alle altre applicazioni. Prima dell'avvio si richiedono 9 GiB liberi;
il server viene fermato dopo tre campioni con meno di 2 GiB disponibili.
Questi margini non garantiscono che ogni circuito entri nei 16 GB. Il contesto
60.000 non e proposto come avvio CPU sicuro su quella macchina. I registri
misurano memoria e tempi effettivi per correggere la stima dopo la prima prova.

## Dati, verifiche e limiti

`data/` contiene solo i 396 esempi train e i loro QASM, il manifest train,
la trasformazione originale e il catalogo originale. Nessun risultato
validation/test viene letto. I dati, gli schemi e i cataloghi hanno sigilli
SHA256 controllati prima del recupero. I cinque Target sintetici vengono
ricostruiti da MQT Bench e confrontati con le impronte originali.

Il recupero usa Qdrant locale, 49 caratteristiche, trasformazione ricavata
solo dal train e distanza Manhattan. Tutti i candidati filtrati vengono
ordinati con distanza float64 e identificativo: stessa regola del congelato.
L'indice derivato viene ricreato in `runtime/rag/` per il sistema corrente.

Il client contiene le sole funzioni di estrazione tratte da MQT Predictor
2.4.0 sotto licenza MIT. Non carica ne addestra modelli MQT. Il catalogo runtime
limita il controllo delle dipendenze allo stack realmente necessario;
il catalogo originario resta in `data/catalog_original.json`. Questi
adattamenti rendono il prototipo portabile, senza riscrivere l'esperimento.

Ogni esecuzione crea una cartella nuova in `runs/`: input, provenienza, versioni,
prompt, esempi recuperati, token, risposte grezze, controlli, errori e tempi.
La compilazione facoltativa aggiunge `compiled.qasm` e i controlli di base e
connettivita. Le nuove scelte non ricevono score di valutazione nel prompt.
I risultati sono prove tecniche del prototipo, non risultati di generalizzazione.

Vedere [guida passo passo](docs/guida_passo_passo.md) e
[protocollo del prototipo](docs/protocollo_sperimentale.md).

## Verifica di questa separazione

Sono passati i controlli offline sulle 396 estrazioni train, sul recupero
Qdrant confrontato con il riferimento, sui fatti v4, sui tre tentativi,
sul rifiuto preventivo del contesto e sulla compilazione del Bell tecnico.
La prima esecuzione del controllo aveva un campo aggiuntivo errato nel dato
sintetico; e stato corretto, preservando il resoconto del tentativo.

L'installazione pulita sul laptop e l'inferenza CPU non sono state eseguite.
Per avviare da un progetto WSL, copiare il controllore e il runtime su un disco
Windows nativo: l'esecuzione da percorso UNC ha mostrato un blocco prima del
server. Anche il tentativo da copia nativa e rimasto bloccato prima della
creazione del server; la causa non e stata isolata. **Nessuna inferenza reale
e stata completata durante questa separazione.** I controllori avviati sono
stati fermati. Il dettaglio e in `docs/verifica_tecnica.json`.
Se PowerShell rifiuta gli script locali non firmati, usare nella sola sessione
`pwsh -NoProfile -ExecutionPolicy Bypass -File .\server-laptop.ps1 -ModelPath ...`;
non occorre cambiare la politica globale del computer.

Vedere anche: [Comandi manuali verificati sul fisso](docs/comandi_verifica_manuale.md).

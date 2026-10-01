# Prototipo: dal circuito alla compilazione

Il prototipo usa Qwen3.5-4B Q8_0 a temperatura 0 per scegliere un dispositivo quantistico sintetico e una configurazione Qiskit. Parte da un circuito OpenQASM 2, recupera esempi train, controlla la risposta e, con `--compile`, produce il circuito compilato. Non invia lavori a hardware quantistico e non richiede modelli MQT addestrati.

## Prima prova

La [guida passo passo](docs/guida_passo_passo.md) contiene due percorsi completi: **Linux senza GPU**, per un nuovo utente con almeno 16 GB di RAM e sufficiente memoria libera, e **fisso di Elio**, con client WSL e server Windows sulla Radeon RX 6750 XT. Una GPU compatibile è consigliata; CPU e memoria limitate non garantiscono che ogni richiesta sia eseguibile.

Su Linux servono Python 3.12, Node.js 22/npm, llama.cpp b10930 e il GGUF esatto. Dopo aver seguito installazione e avvio del server CPU nella guida, da questa cartella:

```bash
.venv/bin/python -B app.py check
.venv/bin/python -B app.py run examples/bell.qasm \
  --profile cpu --transport native --timeout 3600 \
  --device ibm_falcon_27 --compile
```

`check` verifica il client, non il server. L'esempio Bell e il filtro Falcon 27 permettono una prima richiesta contenuta. Senza `--compile` si riceve soltanto una raccomandazione. Per una GPU Linux diversa da quella del fisso seguire [installazione e runtime](docs/installazione_e_runtime.md#gpu-su-linux).

## Dove trovare le parti

| Elemento | Funzione |
| --- | --- |
| `app.py` | Prepara l'indice, controlla il client e coordina una nuova richiesta. |
| `server.py`, `setup.sh` | Avvio server e preparazione client Linux. |
| `setup.ps1`, `server-*.ps1`, `verify-model.ps1`, `AmdSensors.cs` | Strumenti Windows conservati per il fisso; i controlli termici desktop sono specifici AMD. |
| [prototype/](prototype/README.md) | Lettura QASM, recupero RAG, prompt, controlli e compilazione. |
| [data/](data/README.md) | 396 esempi train unici, QASM, trasformazione e manifest delle 422 sorgenti. |
| [configs/](configs/README.md), `config.json` | Catalogo Qiskit, identità Qwen e parametri fissati. |
| [schemas/](schemas/README.md) | Contratti delle richieste e risposte. |
| [qiskit_dataset/](qiskit_dataset/README.md), [scripts/](scripts/README.md) | Catalogo e verifiche di integrità. |
| `portable_features.py` | Estrattore delle 49 caratteristiche; licenza MQT conservata accanto al codice. |
| `examples/bell.qasm` | Circuito tecnico per iniziare. |
| [runtime/](runtime/README.md) | Eseguibili, indice derivato, pesi e log server locali. |
| `runs/` | Registri client delle singole richieste; generati e non versionati. |
| [docs/](docs/README.md) | Guide, spiegazione dei moduli e protocollo scientifico corrente. |

Il programma è autonomo: non legge `archivio/` o `riproducibilita/`. I pesi non sono nel clone. I fatti verificabili sono controllati sui dati forniti; l'ipotesi libera del modello non è certificata. Al terzo tentativo una coppia ammessa può essere accettata con fatti non verificati, dichiarandolo nel risultato.

Per scegliere altri modelli, rigenerare il Dataset, fare validation/Test o esportare un altro prototipo usare [riproducibilita/](../riproducibilita/README.md). L'archivio conserva le evidenze concluse, senza essere una dipendenza dell'avvio.

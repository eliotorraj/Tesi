# Riduzione aggiuntiva dei prompt con TOON

19 settembre 2026. Questa modifica precede la selezione sulla validation.
Serve a riprovare i cinque circuiti train con Qwen, Phi e Gemma.

## Risultato

TOON è installato e attivo per i dati del prompt. La risposta resta JSON.
Sono conservati tutti i valori delle feature, gli zeri, gli esempi e il loro
ordine. Lo schema della risposta e le correzioni restano invariati.

La conversione diretta non risparmiava token. La soluzione usa una tabella
delle caratteristiche con colonne `current`, `E1`...`E5` e raggruppa gli archi
hardware per qubit sorgente quando questo è esattamente reversibile.
Ogni prompt viene decodificato e confrontato con la vista ridotta.

Totali di token di ingresso sui cinque circuiti, misurati con i tokenizer
nativi dei rispettivi modelli Q8_0 e includendo il template di chat:

| Modello | Precedente v2 | JSON ridotto | Ridotto + TOON | Risparmio su JSON |
| --- | ---: | ---: | ---: | ---: |
| Qwen | 328.123 | 60.687 | 55.762 | 8,12% |
| Phi | 269.360 | 46.844 | 44.670 | 4,64% |
| Gemma | 343.014 | 64.578 | 58.249 | 9,80% |

Il precedente v2 è ricostruito sugli stessi dati, salvo i casi identificati
come richiesta storica esatta. Usava già alias. Il documento completo conserva
anche il confronto con il JSON senza alias.
La base JSON ridotta riproduce esattamente tutti gli ID dei token delle
15 richieste archiviate. Non sono nuove inferenze: qualità, tempi e consumo
delle risposte TOON vanno ancora misurati con le prove.

## Documento e dati

- [Documento completo con dettagli per circuito, metodo e limiti](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/report/README.md)
- [Pagina con grafico e collegamenti ai prompt testuali](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/report/index.html)
- [Conteggi e provenienza leggibili da programma](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/toon_train_20260919/native_counts/report.json)

La cartella dell'analisi conserva le prove di formato, anche quelle scartate,
i registri di installazione, i controlli e i file originali dei conteggi.
L'encoder ufficiale è `@toon-format/toon` 4.1.1; Node Linux è 22.23.2.
Le versioni e le impronte sono fissate nel progetto.
Il grafo viene aggiornato sulle sorgenti interessate, senza estrarre
nuovamente gli artefatti storici degli esperimenti.

## Comandi per i cinque circuiti train

Da `/home/elio/Tesi-mqt-2.4-v2`, uno alla volta:

```bash
.venv/bin/python -m llm_selection.controller --technical --model qwen --label "qwen-toon-01" --precision Q8_0 --context 147456
```

```bash
.venv/bin/python -m llm_selection.controller --technical --model phi --label "phi-toon-01" --precision Q8_0 --context 30000
```

```bash
.venv/bin/python -m llm_selection.controller --technical --model gemma --label "gemma-toon-01" --precision Q8_0 --context 30000
```

Non serve un'opzione TOON. Questi comandi usano il nuovo formato predefinito,
`p1_t0` e fino a tre tentativi. Usare nuove etichette per conservare le prove
precedenti. I risultati sono in
`artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/technical_episodes/<etichetta>/`.
Non sono prove sulla validation o sul test.

## Riproduzione della misura

L'installazione si riproduce dalla radice WSL:

```bash
.venv/bin/python -m llm_selection.setup_toon
```

La preparazione dei prompt non avvia i modelli:

```bash
.venv/bin/python -m llm_selection.toon_audit --output artifacts/toon_confronto_nuovo
```

Usare una cartella nuova. Il programma prepara i tre manifesti
`qwen_tokenize.json`, `phi_tokenize.json` e `gemma_tokenize.json`.
Da PowerShell Windows, eseguire per ciascun manifesto il conteggio con
`llm_selection/tokenize_files.ps1 -ManifestPath PERCORSO_ASSOLUTO_MANIFESTO`.
I percorsi sono prodotti dal programma per il runtime llama.cpp già presente.
Poi, nuovamente da WSL:

```bash
.venv/bin/python -m llm_selection.toon_audit --output artifacts/toon_confronto_nuovo --finish
```

Il rapporto JSON e il primo riepilogo Markdown vengono creati dai conteggi.
Per rigenerare anche pagina HTML e figure, eseguire `llm_selection/toon_report.py`
con un interprete che abbia Matplotlib, senza modificare l'ambiente MQT:

```bash
python llm_selection/toon_report.py --audit artifacts/toon_confronto_nuovo --output artifacts/toon_confronto_nuovo/report
```

Per l'analisi consegnata è stato usato il runtime locale delle analisi.
I parametri e i registri sono conservati insieme ai risultati.

## Verifiche e limiti

Sono passati tutti i 244 test della suite. I sei controlli specifici TOON
sono stati ripetuti dopo la verifica finale dell'ordine degli archi.
La ricostruzione è controllata anche sui 15 prompt reali dei tre modelli.

Questo controllo è reversibile rispetto alla vista essenziale.
Non ricostruisce i dati deliberatamente esclusi dal prompt: QASM, manifest
e identificativi lunghi restano nei documenti canonici dell'esperimento.
La codifica non garantisce che Phi risolva gli errori precedenti.
La verifica delle evidenze continua a controllare i riferimenti, non la
verità semantica del claim.

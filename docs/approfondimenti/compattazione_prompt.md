# Compattazione comune dei prompt

La rappresentazione compatta è definita in
[prototype/prompting/](../../prototype/prompting/README.md).
Serve alla selezione LLM, al collegamento locale del prototipo e
all'esportazione dei prompt per le prove manuali.

## Il comando tecnico usa già il prompt ridotto

Da Ubuntu, nella radice del progetto:

```bash
QWEN_PROVA="qwen-tecnica-$(date +%Y%m%d-%H%M%S)"
.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label "$QWEN_PROVA" \
  --precision Q8_0 --context 147456
```

Non serve un'opzione aggiuntiva. Il percorso è:

```text
controller → run.episode → configuration.payload
           → prototype.prompting.rendering.messages
           → codifica compatta → formato nativo del modello → invio
```

La prima richiesta e le eventuali correzioni seguono lo stesso percorso.
Il profilo tecnico esegue i casi train previsti dalla procedura; non avvia
la selezione sulla validation.

## Dati completi e rappresentazione per il modello

Il costruttore del prototipo prepara il contesto completo: richiesta, circuito,
catalogo, esempi, registro delle evidenze, schema di risposta ed eventuali errori.
Il componente comune:

- sostituisce gli identificativi lunghi delle fonti con sigle;
- conserva una sola copia dei valori ripetuti;
- rappresenta alcuni gruppi di oggetti come tabelle;
- usa una regola esatta per i soli grafi completi.

Il circuito, i valori numerici, gli esempi e lo schema della risposta restano
invariati. Prima di proseguire viene verificata la ricostruzione dell'oggetto
originale. Questa proprietà non dimostra che un modello sappia interpretarlo
correttamente: i controlli semantici restano necessari.

Il Dataset Qiskit, gli esempi originali e l'indice Qdrant non cambiano.
La trasformazione avviene dopo il recupero degli esempi.

## Un solo punto da modificare

| File condiviso | Responsabilità |
| --- | --- |
| `compact.py` | Codifica completa, verifica inversa, impronte e ripristino degli identificativi nella risposta. |
| `rendering.py` | Istruzioni e costruzione dei messaggi nelle varianti già previste. |
| `output_contract.py` | Regole esplicite delle relazioni fra affermazioni e fonti. |
| `complete_graph.py` | Rappresentazione dei grafi completi. |
| `wire.py` | Codifica e lettura delle tabelle. |

`llm_selection/configuration.py` conserva griglia e parametri di generazione,
ma richiama il costruttore comune. I vecchi moduli di codifica in
`llm_selection/` rimandano all'implementazione condivisa per mantenere
compatibili gli import precedenti.

Per nuovi collegamenti a modelli utilizzare il componente comune. Il trasporto
HTTP grezzo riceve invece una richiesta già formattata: non deve tentare di
compattarla nuovamente. Le chiamate diagnostiche con richieste storiche restano
riconoscibili come riproduzioni di quel formato.

## Registri e provenienza

Ogni tentativo automatico conserva il prompt completo in `prompt.json`, la
versione e la mappa delle sigle in `encoding.json`, e la richiesta effettiva
negli artefatti del trasporto. La risposta originale rimane conservata.
Prima della validazione si ripristinano soltanto gli identificativi noti;
non si correggono scelte o collegamenti sbagliati.

Le copie del codice delle prove includono anche `prototype/prompting/`.
La revisione della codifica resta `lossless-v2-20260914`: lo spostamento del
codice mantiene lo stesso formato. Le nuove copie del codice distinguono
comunque l'implementazione centralizzata dalle prove precedenti.

## Chat manuale

La [guida della chat](chat_locale.md) permette di scegliere Qwen, Phi o Gemma.
Per incollare il contesto dell'esperimento usare un `prompt_chat.txt` esportato
da `llm_selection.prompt_audit`: l'esportatore usa lo stesso costruttore comune.

La chat libera del browser non trasforma automaticamente testo arbitrario e non
applica da sola lo schema di generazione o il validatore dell'esperimento.
L'avvio della chat e l'esecuzione della prova tecnica sono operazioni separate.

## Verifiche della centralizzazione — 16 settembre 2026

È stato conservato un riferimento dei messaggi prima della modifica.
Sono stati confrontati tutti i 93 prompt preparati (5 train e 88 validation)
nelle varianti base e con istruzioni di controllo: **186 messaggi identici**,
con mappe della codifica e file sorgente invariati. Nessuna inferenza o nuova
compilazione è stata necessaria. Il contenuto del test non è stato letto.

I test mirati controllano il messaggio passato al trasporto, le correzioni,
il ripristino delle fonti, la provenienza del codice e la scelta del modello
della chat con avvii simulati. **67 test mirati superati**. I controlli `--check` sui file reali sono
riusciti per Qwen, Phi e Gemma senza avviare server. Il caricamento e
la generazione reali non sono stati rieseguiti durante il training RL.

I dati del controllo sono conservati nel [registro JSON](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/prompt_centralization_2026-09-16/verification.json),
con impronte dei messaggi e uscita dei test nella stessa cartella.

Per ripetere i test mirati da Ubuntu:

```bash
PYTHONPATH=.:tests .venv/bin/python -m unittest \
  test_compact_prompt test_llm_chat test_llm_selection test_claim_evidence_validation -v
```

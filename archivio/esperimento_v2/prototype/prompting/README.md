# Rappresentazione dei prompt

Questo componente separa i dati completi dell'esperimento dal testo inviato
al modello. La vista corrente è `minimal-v3-toon1-20260919`.
I dati in ingresso usano TOON; lo schema e la risposta restano JSON.

- `minimal.py`: selezione dei contenuti, alias E1...E5, contesto delle citazioni,
  schema v3 e metadati esterni.
- `rendering.py`: messaggi comuni a chat, prove e correzioni.
- `toon.py`: disposizione reversibile delle feature e dei collegamenti hardware,
  codifica TOON e verifica automatica della ricostruzione.
- `toon_runtime/`: encoder ufficiale `@toon-format/toon` 4.1.1 e versioni fissate.
- `compact.py`, `complete_graph.py`, `wire.py`, `output_contract.py`,
  `legacy_rendering.py`: lettura e confronto del precedente formato v2.

La riduzione avviene dopo il recupero. Non cambia Dataset, indice, distanza,
numero/ordine degli esempi o caratteristiche numeriche.
QASM e provenienza restano nel documento canonico, fuori dal testo LLM.

La risposta corrente contiene dispositivo, configurazione, claim libero e
citazioni degli esempi. I controlli applicativi risolvono le citazioni e
verificano la scelta; non certificano la verità della motivazione.

Procedura, misure e limiti nella
[guida](../../docs/approfondimenti/compattazione_prompt.md).

Le correzioni aggiungono una frase per dispositivo, configurazione o evidence
non ammessi. Gli errori dello stesso tipo compaiono una sola volta.
La richiesta di restituire il JSON completo compare una sola volta in fondo
al messaggio. Il primo tentativo non riceve istruzioni di correzione.

## Installazione riproducibile

Dalla radice del progetto:

```bash
.venv/bin/python -m llm_selection.setup_toon
```

La procedura installa Node Linux e l'encoder nelle cartelle locali del progetto.
Verifica le impronte fissate e usa `npm ci`. Non cambia l'ambiente Python MQT.
Node è conservato negli artefatti; `node_modules/` non va aggiunto a Git.
Se manca l'encoder, l'invio fallisce con l'indicazione del comando di installazione.

Le feature condividono una tabella, con colonne `current`, `E1`...`E5`.
I collegamenti diretti usano liste di vicini quando è possibile ricostruire
esattamente anche l'ordine degli archi. La decodifica viene verificata prima
dell'invio; nessuna feature o cifra viene eliminata intenzionalmente.
`messages(..., serialization="json")` riproduce il precedente JSON ridotto
per i confronti. La risposta e la gestione degli errori non cambiano.

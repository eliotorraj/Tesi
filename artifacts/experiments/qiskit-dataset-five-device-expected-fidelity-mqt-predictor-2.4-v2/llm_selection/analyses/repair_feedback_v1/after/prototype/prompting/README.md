# Rappresentazione dei prompt

Questo componente separa i dati completi dell'esperimento dal testo inviato
al modello. La vista corrente è `minimal-v3-repair1-20260918`.

- `minimal.py`: selezione dei contenuti, alias E1...E5, contesto delle citazioni,
  schema v3 e metadati esterni.
- `rendering.py`: messaggi comuni a chat, prove e correzioni.
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

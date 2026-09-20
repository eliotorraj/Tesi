# Tesi — LLM e compilazione quantistica

**Stato al 20 settembre 2026 — branch di lavoro `riorganizzazione-prototipo`:** validation ufficiale v2 conclusa; modello
selezionato **Qwen3.5-4B Q8_0, temperatura 0**. Il Test resta chiuso.

## Le due aree del progetto

| Dove andare | Che cosa contiene |
| --- | --- |
| [prototipo/](prototipo/README.md) | Prova autonoma: circuito, RAG, Qwen, raccomandazione e compilazione Qiskit opzionale. Avvio fisso GPU e portatile CPU. |
| [archivio/](archivio/README.md) | Evoluzione del lavoro, esperimenti, codice originale, Dataset, Training set, prove fallite e rapporti. |

Per capire esattamente il prossimo passo leggere la
[guida passo passo](prototipo/docs/guida_passo_passo.md) e il
[protocollo corrente](prototipo/docs/protocollo_sperimentale.md).

La cartella locale [tesi/](tesi/README.md) contiene la stesura LaTeX ed è esclusa
da Git. `.venv/`, `.codex/`, `.workspace_archive/` e `graphify-out/` sono strumenti
locali; non sono altre fasi dell'esperimento. `.vscode/` contiene preferenze editor.

## Punti da completare prima del Test

Il vecchio controllo di apertura consulta ancora la selezione v1. Occorre
collegarlo alla selezione ufficiale v2, verificare la variante senza RAG,
il modello di frontiera, i modelli MQT e tutti i requisiti del protocollo.
Una dimostrazione del prototipo non sostituisce questi controlli.

## Ripristino e provenienza

Lo stato precedente al riordino è su GitHub nel tag
`pre-riorganizzazione-2026-09-20`, commit `e9f5155c716b052a9fc889ca355840f584b9da38`.
`main` comprende anche la storia precedente. I dati già esclusi da Git,
i pesi esterni e la tesi locale vanno trasferiti separatamente.
La [documentazione del riordino](archivio/riorganizzazione_2026_09_20/README.md)
conserva spostamenti, verifiche e limiti.

## Limite della prima consegna

Il recupero, i controlli e la compilazione sono verificati senza LLM. La prova
reale Qwen non è conclusa: il controllore Windows è rimasto bloccato prima del
server, senza chiamate al modello. Consultare gli [esiti tecnici](prototipo/docs/verifica_tecnica.json).
Il portatile non è stato misurato. La revisione manuale degli script è ancora
parziale. `main` conserva il salvataggio precedente al riordino fino alla
chiusura di questi controlli.

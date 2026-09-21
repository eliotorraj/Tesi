# Tesi — LLM e compilazione quantistica

**Stato al 21 settembre 2026 — branch di lavoro `riorganizzazione-prototipo`:** validation ufficiale v2 conclusa; modello
selezionato **Qwen3.5-4B Q8_0, temperatura 0**. Il Test resta chiuso.

## Le due aree del progetto

| Dove andare | Che cosa contiene |
| --- | --- |
| [prototipo/](prototipo/README.md) | Prova autonoma: circuito, RAG, Qwen, raccomandazione e compilazione Qiskit opzionale. Avvio fisso GPU e portatile CPU. |
| [archivio/](archivio/README.md) | Evoluzione del lavoro, esperimenti, codice originale, Dataset, Training set, prove fallite e rapporti. |

Per capire esattamente il prossimo passo leggere la
[guida passo passo](prototipo/docs/guida_passo_passo.md) e il
[protocollo corrente](prototipo/docs/protocollo_sperimentale.md).



## Avviare un Test o addestrare MQT

- [Test indipendenti](prototipo/test/README.md): quattro script, controlli per
  metodo, ripresa e cartelle separate per risultati, grafici e LaTeX.
- [Selettore ML sul portatile](prototipo/addestramento/mqt/README.md): aggiornamento
  da GitHub, trasferimento dei cinque RL, addestramento e sincronizzazione.

Il controllo operativo consulta la selezione **local-llm-v2**. MQT richiede
il proprio selettore e sei prove tecniche; la sua indisponibilità non blocca
LLM+RAG, LLM senza RAG o Random. Il Test non è stato eseguito durante lo sviluppo.
Il [resoconto](prototipo/test/SVILUPPO.md) distingue prove sintetiche e limiti.

## Ripristino e provenienza

Lo stato precedente al riordino è su GitHub nel tag
`pre-riorganizzazione-2026-09-20`, commit `e9f5155c716b052a9fc889ca355840f584b9da38`.
`main` comprende anche la storia precedente. I dati già esclusi da Git,
i pesi esterni e la tesi locale vanno trasferiti separatamente.
La [documentazione del riordino](archivio/riorganizzazione_2026_09_20/README.md)
conserva spostamenti, verifiche e limiti.

## Stato delle verifiche

Il recupero, i controlli e la compilazione sono verificati senza LLM. La prova
reale Qwen non è conclusa: il controllore Windows è rimasto bloccato prima del
server, senza chiamate al modello. Consultare gli [esiti tecnici](prototipo/docs/verifica_tecnica.json).
Il portatile non è stato misurato. La [revisione manuale dei 147 script](archivio/riorganizzazione_2026_09_21/revisione_script/README.md) è completata: i difetti rilevati sono documentati e restano da correggere nella prossima versione operativa. `main` conserva il salvataggio precedente al riordino fino alla
chiusura di questi controlli.

I [comandi per aggiornare Graphify e provare Qwen](prototipo/docs/comandi_verifica_manuale.md) sono pronti per l’esecuzione manuale.

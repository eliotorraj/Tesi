# Completamento della revisione del 21 settembre 2026

Questa cartella conserva la lettura manuale degli script rimasti dalla prima
consegna. I sorgenti dell'esperimento non sono stati riscritti: manteniamo
le versioni che hanno prodotto i risultati e ne documentiamo i limiti.

- [Rapporto e priorita](revisione_script/README.md).
- [Rassegna dei 147 script](revisione_script/rassegna_147_script.md).
- [Comandi manuali per Graphify e Qwen](../../prototipo/docs/comandi_verifica_manuale.md).

L'aggiornamento del grafo e la prova reale del modello sono affidati all'utente.
Questa attivita non apre il Test e non cambia la selezione Qwen a temperatura zero.

## Esito Graphify

L’aggiornamento eseguito dall’utente e riuscito: 5.770 nodi, 11.201 archi e 439 comunita. La successiva esportazione HTML leggeva un’analisi vecchia; il file obsoleto e stato archiviato e l’HTML rigenerato correttamente (439 comunita, 775 collegamenti). Il grafo JSON non e cambiato. Dettagli in [graphify_esito.json](graphify_esito.json). Non e stata eseguita inferenza Qwen.

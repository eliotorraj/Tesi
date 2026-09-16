# Riepiloghi pubblicabili delle prove LLM

Questa cartella conserva piccoli estratti dei risultati che si possono leggere
senza aprire gli artefatti completi. I numeri provengono dai registri delle prove.
Le spiegazioni e i limiti sono nel [resoconto del prompt compatto](../../docs/resoconti/2026-09-15_prompt_compatto.md).

| File o cartella | Contenuto |
| --- | --- |
| `prompt_lossless_v2.json` | Misure della rappresentazione compatta e verifica che tutti i dati si ricostruiscano. Comprende i prompt dei cinque casi train e degli 88 casi validation. |
| `qwen_prompt_v2_dj.json` | Unisce quelle verifiche al riepilogo della prova tecnica Qwen sul solo circuito DJ train. |
| [`qwen_prompt_v2_dj_responses/`](qwen_prompt_v2_dj_responses/README.md) | Testi originali delle tre risposte della stessa prova. |

Il controllo di 93 prompt verifica gli input. Non esegue la selezione sulla
validation e non misura la qualità delle scelte sui suoi circuiti.
Nella prova DJ i tre tentativi producono JSON conforme allo schema, ma nessuno
supera tutti i controlli sul significato delle citazioni. La scelta della coppia
attesa non basta a rendere valida la risposta.

I dati completi restano sotto `artifacts/experiments/` nell'area `llm_selection/`.
Questi estratti non sostituiscono prompt, richieste, registri e misure originali.
`prompt_report.py` li ricava dai dati salvati; i comandi sono nel resoconto collegato.

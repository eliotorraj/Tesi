# Resoconti dello sviluppo e delle prove

Questo è il punto di accesso alla storia tecnica del progetto.
Per capire che cosa fa il sistema oggi partire dal [README principale](../../README.md).
Per le regole scientifiche usare il [protocollo corrente](../protocollo_sperimentale.md).

## Documenti recenti

| Documento | Che cosa permette di ricostruire |
| --- | --- |
| [Seconda validation: fatti e ipotesi](2026-09-19_validation_fatti_v4.md) | Nuovo contratto, correzioni, ripresa delle interruzioni, regret osservato e prove train. |
| [Ricognizione e riordino del 15–16 settembre](2026-09-16_ricognizione_documentazione.md) | Stato osservato, riorganizzazione, fonti controllate e limiti della verifica. |
| [Prompt compatto, 15 settembre](2026-09-15_prompt_compatto.md) | Riduzione reversibile dei prompt, controlli e prova Qwen sul circuito train DJ. |
| [Diagnosi Qwen, 15 settembre](2026-09-15_diagnosi_qwen.md) | Lettura delle risposte precedenti, errori e ipotesi da verificare. |
| [Pubblicazione GitHub, 15 settembre](2026-09-15_pubblicazione_github.md) | Istruzioni e osservazioni di una consegna precedente; non è una procedura operativa attuale. |
| [Rimozione LFS](../manutenzione/rimozione_lfs_2026-09-15/README.md) | Successivo intervento sulla cronologia Git e trasferimento dei dati esterni. |
| [Riordino dell'archivio, 9 settembre](2026-09-09_riordino_archivio.md) | Testo del precedente README dell'archivio e verifiche svolte allora. |
| [Cronologia del progetto fino al 9 settembre](cronologia_progetto_fino_al_9_settembre_2026.md) | Testo integrale della precedente KB: studio, decisioni, tentativi, problemi e cambiamenti. |

I due documenti su Git descrivono momenti diversi della stessa giornata.
I vecchi identificativi di commit possono essere stati sostituiti dalla
riscrittura documentata nella manutenzione.

## Risultati e resoconti vicini ai dati

I documenti generati restano insieme ai dati che descrivono, per conservarne
la provenienza e consentirne la rigenerazione. Non vengono copiati qui.

| Materiale | Dove leggerlo |
| --- | --- |
| Dataset Qiskit: formati, gruppi e rapporti dei cinque dispositivi | [Guida del Dataset corrente](../../datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/README.md) |
| Confronto Qiskit globale | [Rapporto generato](../../datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/expected_fidelity/full/global/reports/device_comparison.md) |
| Registri completi delle prove LLM | [Guida degli artefatti LLM](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/README.md) |
| Qwen: prova automatica precedente su cinque train | [qwen-prova-07](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/qwen-prova-07/resoconto.md) |
| Qwen: risposta manuale sul circuito DJ | [Analisi del 14 settembre](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/analyses/manual_dj_2026-09-14/resoconto.md) |
| Alternative per ridurre i prompt | [Proposta del 14 settembre](../../artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection/proposals/2026-09-14_prompt_reduction/proposta.md) |
| Piccoli riepiloghi JSON e risposte originali Qwen | [llm_selection/reports/](../../llm_selection/reports/README.md) |

## Materiale precedente e stesura

- [Struttura e implementazione del Dataset Qiskit v1](dataset_qiskit_v1.md).

- [Protocolli e documenti sostituiti](../../archivio/documentazione/README.md).
- [Relazioni periodiche in Word e PDF](../../archivio/resoconti/README.md).
- [Guide di dettaglio](../approfondimenti/README.md).
- [Bozza locale della tesi](../../tesi/README.md), se presente sulla macchina.

Le copie storiche conservano terminologia e percorsi dell'epoca. I conteggi dei
test riportati lì appartengono a quelle verifiche; non sono nuove misure.
Nessun resoconto tecnico sul train equivale a una selezione conclusa sulla
validation o a un confronto finale sul test.

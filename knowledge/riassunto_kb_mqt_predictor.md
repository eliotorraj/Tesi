# Riassunto del progetto e dei concetti MQT

Aggiornamento documentale: **15 settembre 2026**.
Per lo stato verificato e la prossima attività leggere il [README principale](../README.md).
Per le regole usare solo il [protocollo sperimentale](../docs/protocollo_sperimentale.md).

## Obiettivo della tesi

Valutare se un modello linguistico, aiutato da esempi di compilazioni precedenti,
riesce a scegliere un dispositivo e una configurazione Qiskit di buona qualità.
La scelta viene confrontata con lo stesso LLM senza esempi, un LLM di frontiera,
MQT Predictor, configurazioni Qiskit fisse e una scelta casuale.

Il lavoro attuale usa MQT Predictor **2.4.0**, Python **3.12** e le dipendenze
esatte di `uv.lock`. I risultati della versione 2.3.0 sono storici.

## Le distinzioni da mantenere

| Termine | Significato nel progetto |
| --- | --- |
| Dataset | Esempi destinati al RAG o a un eventuale adattamento dell'LLM. |
| Training set | Dati circuito-dispositivo per il selettore supervisionato di MQT Predictor. |
| Train | Circuiti dai quali ricaviamo esempi e dati di apprendimento. |
| Validation | Circuiti usati per scegliere la configurazione prima del confronto finale. |
| Test | Circuiti riservati alla valutazione finale, ancora protetti dalle condizioni di apertura. |
| Prova tecnica | Controllo del funzionamento, senza conclusioni sulla generalizzazione. |

Le valutazioni delle coppie circuito-dispositivo servono a ricavare l'etichetta
del selettore: nella tabella supervisionata finale ogni circuito ha come
etichetta il dispositivo migliore tra quelli valutati.

## I due lavori MQT

**Paper del 2023.** Il modello supervisionato predice una configurazione che
comprende tecnologia, dispositivo, compilatore e impostazioni.

**Architettura MQT Predictor del 2025.** Il modello supervisionato sceglie il
dispositivo. Una politica di apprendimento per rinforzo (RL), specifica del
dispositivo e della metrica, sceglie poi i passaggi di compilazione.

Il flusso MQT è quindi:

```text
circuito → caratteristiche → selettore ML → dispositivo → compilatore RL
```

Il flusso del nostro assistente usa invece esempi di compilazioni Qiskit:

```text
circuito e vincoli → dispositivi compatibili → esempi RAG
                 → scelta LLM → controlli → compilazione Qiskit
```

Il progetto non ha dimostrato che uno dei due metodi sia superiore all'altro.
Il fine-tuning dell'LLM non è una fase già eseguita dell'esperimento corrente.

## Che cosa significa qualità

Un circuito sorgente è ancora indipendente dal dispositivo: deve essere
adattato alle operazioni e ai collegamenti consentiti dall'hardware scelto.

La metrica `expected_fidelity` stima la qualità combinando le fedeltà delle
operazioni e della lettura. Nel nostro esperimento si usano Target sintetici
di MQT Bench: non si misura un'esecuzione su un computer quantistico reale.

Un dispositivo “migliore” è migliore per quel circuito, quella metrica,
quelle proprietà hardware e quella procedura di compilazione. Cambiando questi
elementi possono cambiare anche le etichette del selettore.

Un modello addestrato solo per una prova minima dimostra che la procedura
funziona; non dimostra buona qualità di compilazione.

## Dati e recupero correnti

Il corpus contiene 600 circuiti sorgente. Il Dataset corrente e gli artefatti
si trovano sotto `datasets/experiments/` e `artifacts/experiments/`.
Il corpus originale in `archivio/protocollo_v1/datasets/expected_fidelity/full/`
serve ancora a verificarne la provenienza; i suoi vecchi punteggi non vengono riusati.

Il RAG usa solo gli esempi train della vista globale. Confronta 49 caratteristiche
numeriche del circuito, con trasformazione e scala ricavate solo dal train,
tramite distanza Manhattan. Qdrant locale conserva l'indice derivato.
Non si usano gli score del circuito da valutare per suggerire la sua risposta.

## Storia e fonti

Il precedente riassunto univa teoria e molte conversazioni in oltre 6.000 righe.
Il testo originale è conservato integralmente nella
[cronologia fino al 9 settembre](../docs/resoconti/cronologia_progetto_fino_al_9_settembre_2026.md).
Contiene anche il confronto storico con TuniQ e motivazioni delle prime scelte;
i suoi comandi e stati vanno letti nel loro contesto temporale.

Gli articoli sono elencati nel [README delle fonti](README.md).
Le guide tecniche sono in [docs/approfondimenti/](../docs/approfondimenti/README.md).
I resoconti delle prove recenti sono in [docs/resoconti/](../docs/resoconti/README.md).

Distinguere sempre fatti degli articoli, comportamento del software fissato
nel progetto e decisioni sperimentali della tesi.

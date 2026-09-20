# Dal modello scelto al confronto finale

## Dove siamo

La validation ufficiale local-llm-v2 è conclusa. Ha scelto Qwen3.5-4B Q8_0,
temperatura 0. Il Test è ancora chiuso. Il vecchio vincitore a temperatura 0,7
rimane solo nella storia della prima selezione.

## Provare il prototipo

1. Aprire `prototipo/` e seguire il suo README per preparare Python e il modello.
2. Sul fisso avviare `server-desktop.ps1 -ModelPath PERCORSO_GGUF`.
   Sul portatile usare `server-laptop.ps1 -ModelPath PERCORSO_GGUF`.
   I percorsi sono parametri; il portatile usa CPU e non richiede la NPU.
3. Eseguire `python app.py prepare` e `python app.py check`.
4. Eseguire `python app.py run examples/bell.qasm --profile desktop --compile`,
   Per la prima prova portatile usare `--profile laptop --device ibm_falcon_27`,
   dichiarando il vincolo a quel dispositivo. Sostituire il file con un proprio QASM.
5. Leggere la coppia proposta, lo stato dei fatti, l'ipotesi e i registri in
   `runs/`. Senza `--compile` si ottiene solo la raccomandazione.

Il server e il client devono usare lo stesso profilo. Il portatile dispone di
16 GB totali: GPU/NPU condividono la RAM, non sono ulteriori 8,9 GB dedicati da
sommare. La prova effettiva su quel portatile resta necessaria per misurare
memoria e velocità. Un prompt troppo grande viene rifiutato senza eliminare
silenziosamente evidenze o diminuire il budget della risposta.

## Ripercorrere l'esperimento

1. **Corpus e partizioni:** verificare 600 sorgenti, hash e separazione
   422/88/90. Il corpus originale resta conservato nell'archivio.
2. **Matrice Qiskit:** train e validation sono già stati compilati, includendo
   timeout e altri esiti. Non rifare tentativi per migliorare i risultati.
3. **RAG:** 396 esempi train, 49 caratteristiche, trasformazione train,
   Manhattan e cinque vicini. Nessun punteggio del circuito da decidere.
4. **Validation locale:** consultare lo studio local-llm-v2 e il suo rapporto.
   Qwen a t=0 è la scelta finale; la selezione v1 rimane separata.
5. **MQT:** verificare i cinque modelli RL, costruire/completare il Training set,
   verificare classificatore e sei prove minime. Un avvio registrato non prova
   il completamento del training.
6. **Preparazione finale:** collegare il controllo pre-Test alla selezione v2;
   definire esplicitamente la variante senza RAG con contratto coerente;
   congelare modello di frontiera, piani, parametri e analisi statistica.
7. **Apertura:** soltanto dopo tutti i controlli positivi produrre il record
   che autorizza il Test. Il vecchio comando pre-Test usa ancora la selezione v1.
8. **Decisioni:** prima generare e sigillare le tre scelte LLM sul Test.
9. **Compilazioni:** poi qcompile e matrice Qiskit Test. Solo ora si valutano
   qualità e regret. L'indice RAG train non cambia.
10. **Analisi:** confronti appaiati, denominatori, fallimenti, statistiche,
    figure e testo riproducibile per la tesi.

Il [protocollo](protocollo_sperimentale.md) specifica numeri, criteri e limiti.
I comandi sperimentali storici vanno eseguiti dalla radice
`archivio/esperimento_v2/`, con l'ambiente congelato. Non copiare alla cieca
comandi con vecchi percorsi assoluti del PC.

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
5. **Preparare il Test:** seguire [la guida dei quattro metodi](../test/README.md).
   Il controllo consulta local-llm-v2; il primo avvio ufficiale congela il
   contratto. Non occorre una matrice esaustiva Test.
6. **LLM e Random:** eseguire il controllo del metodo e una prova tecnica;
   poi avviare singolarmente i 90 casi quando desiderato.
7. **MQT:** completare [il selettore](../addestramento/mqt/README.md), verificare
   i cinque RL, il classificatore e le sei prove tecniche. Questo passaggio
   non blocca gli altri metodi.
8. **Risultati:** ogni metodo salva i casi in test/risultati/<metodo>/ e il
   proprio rapporto in analisi/. Tabelle, grafici e LaTeX hanno cartelle distinte.
9. **Confronto:** analizza.py legge i risultati disponibili e dichiara quelli
   mancanti. Non avvia altri metodi né ripete casi già conclusi.

Il [protocollo](protocollo_sperimentale.md) specifica numeri, criteri e limiti.
I comandi sperimentali storici vanno eseguiti dalla radice
`archivio/esperimento_v2/`, con l'ambiente congelato. Non copiare alla cieca
comandi con vecchi percorsi assoluti del PC.

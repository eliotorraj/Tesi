# Predisposizione del 30 settembre 2026

È stata aggiunta una campagna separata in `archivio/valutazione/test_qasmbench/`.
La campagna è documentata come **ulteriore test indipendente su QASMBench**.
Il selettore scelto dall'utente è quello corrente da 384 campioni, copiato in `runtime/`;
la provenienza è in `selettore_mqt.json`. Le note seguenti conservano anche le verifiche
precedenti alla scelta del modello.
Il corpus precedente, il Dataset RAG, il Training set e gli artefatti dei test precedenti
non sono stati modificati. Non è stata avviata alcuna valutazione sui 50 circuiti esterni.

## Selezione

Fonte fissata alla revisione QASMBench
`357b942396d5c2b7cbc1c229c585a6ef5ccaebac`.
Sono stati scelti 30 piccoli (2–10 qubit), 15 medi (11–27) e 5 grandi (28–140).
La scelta ragionata copre famiglie e dimensioni diverse senza usare esiti di compilazione.
Non è un campionamento probabilistico della raccolta.

Prima di fissare il manifest sono stati scartati inverseqft_n4, square_root_n18,
vqe_uccsd_n4 e il sostituto intermedio bb84_n8. I motivi sono nel README.
Le copie scartate sono conservate in `verifiche/esclusi/`.
Il primo registro cumulativo è
`verifiche/registri/c6f39883f966454da5dd51a319aa72e2.json`.
I primi controlli individuali si fermavano rispettivamente su inverseqft_n4,
vqe_uccsd_n4 e bb84_n8; questi errori non sono risultati sperimentali.

Il manifest verifica SHA-256, fasce, assenza di duplicati interni e assenza di copie
byte-identiche nel corpus MQT da 600 circuiti. Non verifica equivalenza semantica.
Tutti i cinquanta file superano anche parsing del prototipo, estrazione delle
49 caratteristiche e filtro hardware: registro
`verifiche/registri/compatibilita-ab154e00b7d44586afccdc1f7f6e6f78.json`.

## Strumenti e regole

I moduli sono derivati dagli strumenti del Test esistente, con impronte delle fonti
in `provenienza_codice.json`. Le copie sono autonome rispetto agli avviatori precedenti;
riusano il framework di `prototipo/` e le verifiche degli artefatti addestrati.
Il programma storico `verifiche/predisponi_strumenti.py` documenta la prima derivazione:
non va rilanciato e non rappresenta le correzioni successive.

Le modifiche specifiche sono il manifest esterno, le quote 30/15/5,
la partizione `external_test`, il contratto separato, le cartelle di registrazione
e i due soli metodi richiesti. Il worker MQT passa a rl_compile un oggetto Target,
come richiede l'API installata 2.4.0. Conserva la scelta prima della compilazione
e fissa il seed di campionamento RL a 0. I registri non sono sovrascrivibili.
Le prove Bell sono separate dagli esiti esterni.

L'analisi futura legge soltanto questa campagna. Produce riepiloghi, CSV e grafici,
senza avviare gli altri metodi. I confronti di qualità usano i soli successi comuni.
Errori, timeout, interruzioni e assenze sono riportati separatamente.
Non è disponibile un oracle e non si calcola regret.

## Verifiche e limiti locali

Nove verifiche automatiche sono riuscite (otto in gruppo e una successiva sul generatore completo): integrità della selezione, protezione
dei percorsi e dei registri, confronto con esiti mancanti, interruzioni, timeout,
rifiuto di esiti estranei, compilazione di un Bell sintetico con Qiskit e produzione di JSON/CSV/rapporto su esiti sintetici.
L'ultima prova Bell è terminata con circuito valido sul Target e score finito.
Questa prova non misura la qualità sui cinquanta QASMBench.

La verifica LLM + RAG è riuscita: selezione local-llm-v2, 31.307 file dello studio,
396 record RAG, 408 file della fonte train, versioni e cinque Target.
Il server LLM e il GGUF non sono stati avviati/verificati in rete in questa sessione.

Le prime verifiche complete LLM e MQT avevano un limite esterno di 120 secondi e
sono state interrotte dallo strumento prima dell'esito. Il controllo LLM è stato
ripetuto con un limite più ampio ed è riuscito. Una seconda verifica MQT è stata
interrotta durante il controllo CRC di archivi RL molto grandi, dopo avere
accertato l'assenza del selettore ML. È stato quindi anticipato il controllo
della presenza del selettore: la verifica finale termina indicando il requisito mancante.

**Nella verifica iniziale del percorso MQT standard** non era presente
`trained_clf_expected_fidelity.joblib` sia nell'area canonica sia nel pacchetto installato;
non è presente neppure il modello operativo in `addestramento/mqt/modelli/`.
Il controllo finale non certifica i cinque RL: li dichiara non verificati perché manca ML.
Non sono stati installati modelli incompleti, riaddestrati modelli o avviate prove MQT.
Le sei prove sintetiche MQT restano richieste prima dell'esecuzione.

Dopo la segnalazione dell'utente è stata estesa la ricerca. Un selettore esiste nella
`.venv` del progetto diverso `/home/elio/Tesi/`: 672.369 byte, SHA-256
`2481a764db5c4f0740788f3b852febea88595cbb37a27aeda95f467861fcaf16`,
49 caratteristiche, tre classi (Falcon 27, Falcon 127, H2 56), senza metadati affiancati.
Il caricamento segnala scikit-learn 1.7.1 contro 1.9.0 dell'ambiente corrente.
Questo non dimostra che sia il selettore previsto dal protocollo attuale.
Nella repository corrente esiste inoltre il selettore della prova esplorativa:
SHA-256 `681da87b3d373d27edd9bbabd7424d2b9eb16bf0d18794147fdcdbbe4faa4189`,
384 campioni, quattro classi, metadati presenti, caricamento senza avvisi.
Le copie non sono state modificate. L'inventario è in `verifiche/registri/selettori-*.json`.
La formulazione iniziale «il selettore manca» era troppo generale: manca nel runtime
atteso di questa repository, non in ogni ambiente disponibile. L'utente ha poi scelto il selettore corrente da 384 campioni. Ne è stata creata
una copia locale, senza cambiare la .venv o la fonte. Una prova del solo selettore
su Bell sintetico è riuscita e ha scelto Falcon 127. Non sono state eseguite le sei
prove complete ML/RL né inferenze sui cinquanta QASMBench.

La campagna viene indicata come **ulteriore test indipendente**, secondo la richiesta
dell'utente. Il dettaglio sperimentale conserva 384 campioni su 396, 12 esclusioni,
1.853 compilazioni riuscite su 1.878 coppie e i limiti 100/300 secondi della raccolta
che ha prodotto il selettore. La nuova valutazione usa 100 secondi per circuito.

Con il selettore scelto, la verifica completa MQT è poi riuscita: cinque copie RL
canoniche e runtime, integrità degli archivi, metadati di addestramento, classi ML,
384 sorgenti train e impronte del selettore. Entrambi gli avvii hanno quindi superato
il controllo preliminare. Restano da eseguire, quando richiesto, le sei prove Bell MQT
e il test vero e proprio. Gli archivi RL vengono controllati una sola volta per
coppia dopo avere accertato l'identità SHA-256: il controllo resta equivalente.

L'accesso nativo al terminale e la scrittura nativa non erano disponibili per un
errore tecnico di avvio. Graphify è stato usato per l'esplorazione; LeanCTX è servito
come trasporto per leggere, scrivere ed eseguire comandi. Non è stata usata ricerca
semantica LeanCTX. Il grafo è aggiornato con estrazione AST, senza chiamate API LLM.

I registri runtime sono esclusi da Git: conservarli su disco e includerli nei backup.
`verifiche/registri/` contiene le evidenze leggere di predisposizione.

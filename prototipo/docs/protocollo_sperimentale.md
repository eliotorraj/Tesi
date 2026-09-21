# Protocollo sperimentale corrente

Documento operativo aggiornato il **21 settembre 2026**. L'esperimento sui
circuiti mantiene l'identità **2.0.0**, con MQT Predictor **2.4.0**. La selezione
LLM ufficiale è **local-llm-v2**, con contratto di risposta **4.0.0**.
Questi numeri indicano tre cose diverse. La selezione locale v1 è storica.

Questa guida conserva le regole della validation e introduce il Test indipendente
delle sezioni 7–10. Non avvia il Test e non cambia le partizioni. Il testo precedente, con la cronologia
degli emendamenti e tutti i vecchi comandi, è conservato integralmente in
[archivio](../../archivio/esperimento_v2/docs/protocollo_sperimentale.md).
Per percorrere le fasi nell'ordine leggere la [guida pratica](guida_passo_passo.md).

## 1. Domanda della tesi e unità di confronto

Vogliamo capire se un LLM, aiutato da esempi di compilazione, sceglie bene
un dispositivo e una configurazione di `qiskit.compiler.transpile()`.
La misura è `expected_fidelity`, calcolata sui Target sintetici di MQT Bench.
Non eseguiamo circuiti su un computer quantistico reale.

L'unità statistica è il **circuito**, non una chiamata LLM o un seed.
Le domande correnti riguardano contributo del RAG, confronto con MQT Predictor
e Random, affidabilità, qualità, tempi e token. Il riferimento osservato
è facoltativo e secondario. Le ipotesi storiche con modello di frontiera,
dieci baseline e oracle sono conservate nell'archivio; non sono il piano
operativo del Test indipendente. Un risultato non significativo non dimostra
equivalenza.

## 2. Dati e separazione

Il corpus contiene **600 circuiti: 422 train, 88 validation, 90 test**.
Train costruisce gli esempi e i modelli. Validation sceglie la configurazione.
Test serve una sola volta per il confronto finale dopo tutti i controlli.

**Dataset** indica gli esempi per RAG/LLM. **Training set** indica i dati
circuito-dispositivo per il selettore supervisionato MQT.
Il RAG usa **396 circuiti train distinti per SHA-256**: i 26 alias byte-identici
non diventano nuovi esempi. Anche il selettore ML usa un solo campione per
ciascuno degli stessi 396 hash train, con 1.878 coppie compatibili sui cinque
dispositivi. Il corpus verificato resta quello dei 422 file originali. Per ogni
hash il rappresentante è il nome file lessicograficamente minimo; una mappa
conserva tutti i 26 alias. La deduplicazione precede compilazione, costruzione
degli array, validazione incrociata interna e fit finale del selettore.
Le cache precedenti non vengono mescolate a questa esecuzione.

Questa revisione riguarda il selettore ML. I cinque modelli RL già addestrati
sui 422 file restano invariati: non si afferma che l'intero addestramento RL
sia stato deduplicato. La base di contenuti unici è condivisa con il RAG,
ma le procedure e le informazioni usate dai metodi restano diverse.

I due realamprandom a 2 qubit semanticamente uguali
restano entrambi nel train; questa ridondanza è dichiarata.

Validation e test non entrano in indice, trasformazione, esempi o evidenze.
Score e vincitore del circuito da decidere non sono visibili durante la scelta.
I manifest congelati conservano i riferimenti logici originali. Lo spostamento
in archivio non ne riscrive il contenuto né ne cambia l'identità.

Limiti già noti: il pilota storico aveva compilato due circuiti poi assegnati
al test (`qpeexact_indep_tket_60` e `routing_indep_qiskit_12`). Prima del confronto
va documentato se questa esposizione possa avere influenzato decisioni successive.
Non possiamo escludere che MQT Bench sia nei dati di addestramento degli LLM.
La seconda validation è stata decisa dopo la prima: è una revisione adattiva,
non una replica indipendente.

## 3. Ambiente e spazio di scelta congelati

L'esperimento usa Python **3.12** e le versioni esatte di
[uv.lock](../../archivio/esperimento_v2/uv.lock).
Il [catalogo originale](../../archivio/esperimento_v2/configs/qiskit_dataset_configurations_v2.json)
conserva versioni, impronte dei Target, seed e opzioni di compilazione.
I vecchi dati e modelli MQT 2.3.0 non sono cache valide per questo esperimento.

Dispositivi: `ibm_falcon_27`, `ibm_heron_133`, `ibm_falcon_127`,
`ibm_heron_156`, `quantinuum_h2_56`. Si escludono i candidati incompatibili
con il circuito e con il Target; non si impongono preferenze opzionali
su fornitore, costo o latenza nelle richieste sperimentali.

| Configurazione | Livello | Layout | Instradamento |
| --- | --- | --- | --- |
| `o2_default_default` | 2 | predefinito | predefinito |
| `o3_default_default` | 3 | predefinito | predefinito |
| `o2_sabre_sabre` | 2 | sabre | sabre |
| `o2_dense_sabre` | 2 | dense | sabre |
| `o2_trivial_sabre` | 2 | trivial | sabre |
| `o3_sabre_sabre` | 3 | sabre | sabre |
| `o3_dense_sabre` | 3 | dense | sabre |
| `o3_trivial_sabre` | 3 | trivial | sabre |
| `o2_sabre_lookahead` | 2 | sabre | lookahead |
| `o2_sabre_basic` | 2 | sabre | basic |
| `o3_sabre_lookahead` | 3 | sabre | lookahead |
| `o3_sabre_basic` | 3 | sabre | basic |

Le opzioni predefinite lasciano a Qiskit la scelta dell'algoritmo.
Per il Dataset train/validation ogni coppia è stata compilata con seed **0, 1, 2**. Limite per compilazione:
**100 secondi**, sei processi esterni e `num_processes=1` in Qiskit.
Il timeout è terminale: non si cambia seed per ottenere un risultato favorevole.
Train e validation hanno prodotto **87.120 tentativi: 82.621 successi e 4.499 timeout**.

## 4. Recupero RAG

Ogni esempio contiene dispositivo vincente e fino a tre configurazioni valide
di quel dispositivo. Non sono i tre migliori dispositivi. Le etichette non
vengono bilanciate artificialmente.

Le **49 caratteristiche** descrivono il circuito. Conteggi dei gate, profondità
e numero di qubit ricevono `log1p`; gli altri cinque indicatori restano invariati.
Ogni coordinata è divisa per il massimo assoluto calcolato solo sul train;
un divisore nullo diventa 1. Non si centrano o tagliano i valori.
La distanza è Manhattan, con ricerca esatta, filtri di compatibilità e
ordinamento deterministico delle parità secondo l'implementazione congelata.
Si recuperano **k=5** esempi. Se non ne esistono di compatibili, lo si dichiara.

Qdrant locale **1.19.0** conserva una copia derivata ricostruibile; non serve
un servizio cloud o un modello di embedding. Lo score, il dispositivo vincente
e il testo non entrano nel vettore. L'integrità di fonte train, caratteristiche,
trasformazione, payload, indice e Target deve essere verificata.

## 5. Validation ufficiale conclusa

Studio: `local-llm-v2`. Griglia: Qwen, Phi e Gemma, ciascuno a temperatura
**0, 0,4 e 0,7**. Un solo prompt, **792 episodi** sugli stessi 88 validation.
Prima del congelamento: cinque circuiti train per ciascuna delle nove
combinazioni; sono prove tecniche e possono recuperare sé stessi.

Il vincitore è **Qwen3.5-4B, Q8_0, temperatura 0 (`qwen/p0_t0`)**.
La fonte è `studies/local-llm-v2/final_configuration.json`, non l'omonimo file
globale della selezione v1, che indica ancora temperatura 0,7.

Il profilo ufficiale usa contesto 60.000, cache `q8_0`, batch 512,
micro-batch 128, massimo 4.096 token di risposta, seed 20260913,
`top_p=0.95`, `top_k=40`, `min_p=0`, penalità di ripetizione 1 e nessuna
penalità di presenza/frequenza. Il pensiero esteso è disattivato.
La revisione del prompt è `facts-v4-toon3-20260919`.
Versioni, parametri completi, modello GGUF, SHA-256 e provenienza sono negli
artefatti congelati: la sigla commerciale del modello da sola non basta.

La richiesta canonica conserva QASM e provenienza; la vista inviata al modello
con/senza RAG usa le caratteristiche numeriche complete e omette quei due campi.
I dati della vista sono codificati in TOON con encoder 4.1.1; schema e risposta
rimangono JSON. La codifica viene verificata per ricostruzione dei dati.

### Contratto di risposta v4

La risposta deve contenere dispositivo e configurazione ammessi, **uno o due
fatti distinti** e un'ipotesi libera fino a 1.000 caratteri. I fatti verificabili
riguardano coppia presente nei risultati mostrati, stesso dispositivo, stesso
numero di qubit o capacità del dispositivo. Si controllano solo dati del prompt.
L'ipotesi non riceve una certificazione semantica e può contenere errori.

La prima risposta conforme con coppia ammessa e fatti corretti è definitiva.
I fatti errati possono attivare correzioni, fino a **tre tentativi logici**.
Al terzo, una risposta ancora conforme con coppia ammessa viene accettata anche
con fatti errati: l'esito dichiara `accepted_with_unverified_facts=true`.
JSON non conforme, numero di fatti errato o coppia non ammessa restano fallimenti.
Non si recupera una vecchia risposta perché aveva una coppia migliore.

Una chiamata interrotta viene archiviata e si ripete lo stesso tentativo logico.
Una risposta completa già salvata viene recuperata senza nuova generazione.
Le chiamate fisiche e i costi contano anche le interruzioni. Un timeout senza
interruzione delle risorse rimane terminale. Dopo tre recuperi di trasporto
senza causa accertata il supervisore resta sospeso e riprendibile.

I limiti operativi del desktop durante la validation erano hotspot massimo
110 °C, pausa 105 °C, ripresa 100 °C; edge massimo 95 °C; RAM disponibile
almeno 1 GiB per tre campioni. Il ricaricamento attende tre campioni favorevoli
con hotspot non oltre 100 °C ed edge sotto 92 °C. Sono scelte operative
registrate, non specifiche del produttore o certificazioni del dispositivo.

### Come è stato scelto il vincitore

Si ordinano i candidati per: più scelte valide e compilabili; minore regret
osservato mediano sui circuiti comuni; meno correzioni; meno chiamate fisiche;
tempi e token solo se completi; ordine lessicografico.
Il riferimento osservato è la massima mediana fra le coppie compatibili con
**tutti e tre i seed riusciti**. Esiste sugli 88 validation. Le 70 matrici
incomplete sono dichiarate; l'oracle esaustivo esiste solo sugli altri 18.

Qwen a temperatura 0 ha **88/88 scelte valide e compilabili**, regret osservato
mediano 0, **43 correzioni** e 131 chiamate fisiche. I fatti finali sono tutti
verificati in **70/88** episodi; **18/88** sono accettati con fatti non verificati.
La mediana zero non significa che ogni scelta sia ottima. Il criterio delle
correzioni scioglie la parità finale. Non è una prova di superiorità sul Test.
Le analisi della validation sono descrittive: 2.000 ricampionamenti del circuito,
seed 20260913, intervalli al 95% e denominatori dichiarati.

## 6. MQT Predictor prima del confronto finale

MQT 2.4.0 richiede cinque politiche RL, una per dispositivo, e un classificatore
supervisionato che scelga tra tutti e cinque. Non basta installare il pacchetto.
Target di addestramento RL: 100.000 passi; contatore atteso a fine rollout:
100.352. Il Training set conserva le prove circuito-dispositivo; l'etichetta
supervisionata finale è il dispositivo migliore fra quelli valutati.
Servono anche cinque prove minime RL e una prova completa `qcompile` riuscite.
Un modello addestrato solo per una prova tecnica non dimostra qualità.
Lo stato effettivo dei modelli va verificato dagli artefatti, non dedotto dai log.

## 7. Preparazione al Test indipendente

**Emendamento del 21 settembre 2026, prima della valutazione Test.**
Il confronto comprende esattamente quattro metodi: **LLM + RAG, stesso LLM
senza RAG, MQT Predictor e Random**. Il modello di frontiera e le dieci
baseline Qiskit fisse sono esclusi dal nuovo piano. La loro verifica non
è più un prerequisito. Le analisi storiche della validation restano immutate.

Il problema del vecchio `scripts/15_release_test_v2.py` è risolto nel nuovo
percorso operativo: `prototipo/test/strumenti/gates.py` consulta direttamente
`studies/local-llm-v2/`, verifica studio, configurazione finale, selezione,
sigilli dei modelli e impronte degli input e dei risultati della validation.
Non usa `llm_selection.finalize` né il record globale v1. Lo script archiviato
rimane una fonte storica; non è il comando di apertura del Test corrente.

I controlli comuni verificano versioni pertinenti, cinque Target, corpus,
partizioni, catalogo, fonte RAG train e selezione v2. Il piano corrente è
`prototipo/test/piano.json`. Il primo `--esegui` congela il contratto con
impronte di codice, piano, configurazione, fonte e RAG. Gli avvii successivi
devono coincidere. Non si riutilizzano i vecchi piani con frontiera e oracle
come concorrenti. La preparazione non richiede nuovi punteggi Test.

**I requisiti MQT sono specifici di MQT.** La mancanza del classificatore non
impedisce gli altri tre Test. Prima del Test MQT servono cinque RL conformi,
un selettore a cinque classi addestrato sugli stessi RL e sul solo train,
copie runtime identiche, cinque prove RL e una prova completa ML+RL.
L'identità dei modelli viene registrata e verificata alla ripresa.

Per i due LLM si usano gli stessi pesi Qwen Q8_0, temperatura 0, parametri
ufficiali e contesto desktop 60.000. All'avvio si verificano GGUF, dimensione,
SHA-256 e modello dichiarato dal server. Il profilo laptop ridotto non
appartiene alla valutazione finale. La prova tecnica senza/con RAG può
essere eseguita su Bell tramite `--tecnico`.

### Contratto senza RAG

Il modello non riceve esempi; non viene aperto il Dataset o l'indice durante
la decisione. Restano caratteristiche del circuito, dispositivi e catalogo.
Lo schema v4 resta lo stesso. L'istruzione aggiuntiva richiede esattamente
un fatto `selected_device_has_enough_qubits`, senza `example_id`.
Non sono inventate evidenze sostitutive. I fatti con riferimenti a esempi
assenti risultano non verificati.

Restano tre tentativi completi, prima risposta accettabile definitiva e
accettazione al terzo tentativo di una coppia conforme con fatti eventualmente
non verificati, esplicitamente segnalata. L'ipotesi libera non è certificata.
Nessuna regola viene scelta in base ai risultati Test.

## 8. Esecuzioni autonome

Ogni metodo ha un proprio script in `prototipo/test/`:

| Metodo | Script | Risultati |
| --- | --- | --- |
| LLM + RAG | `llm_rag.py` | `risultati/llm_rag/` |
| LLM senza RAG | `llm_senza_rag.py` | `risultati/llm_senza_rag/` |
| MQT Predictor | `mqt_predictor.py` | `risultati/mqt_predictor/` |
| Random | `casuale.py` | `risultati/random/` |

`--verifica` controlla senza valutare. `--tecnico` usa circuiti sintetici e
scrive in `prove_tecniche/`. `--esegui` apre soltanto il metodo scelto,
esegue i medesimi 90 circuiti e permette la ripresa. Non esiste un esecutore
che avvii i quattro metodi in sequenza. Gli avvii possono avvenire in giorni
diversi. Condividere risorse simultaneamente può alterare la latenza; per i
tempi comparabili evitare esecuzioni concorrenti sulla stessa macchina.

**Una sola compilazione per circuito e metodo.** Il seed Qiskit è 0.
Questa scelta sostituisce i tre seed del precedente piano Test, aderendo
alle 90 compilazioni richieste per ciascun metodo. La validation mantiene
la mediana storica dei tre seed. Per MQT si esegue una selezione supervisionata
seguita da RL: le stesse due operazioni di qcompile 2.4.0, misurate separatamente.
Il seed interno MQT non è controllato e non viene presentato come seed Qiskit.

Il timeout esterno è 100 secondi per processo, compreso il suo avvio.
Qiskit usa `num_processes=1`; ogni metodo compila un circuito alla volta.
Il fallimento è terminale per quel caso e non cambia configurazione o seed.
Random estrae uniformemente una coppia compatibile; il seme deriva da
20260921 e SHA-256 del circuito. Non estrae nuovamente dopo un fallimento.

I due LLM compilano automaticamente la scelta: la conferma interattiva è
saltata. Il limite della chiamata è 3.600 secondi; sono ammessi fino a tre
tentativi completi per la conformità, senza retry automatici di trasporto.
Questa politica del nuovo Test è distinta dai recuperi del supervisore
storico della validation. Tutte le chiamate fisiche restano nei registri.

La decisione Qiskit viene salvata prima della compilazione. Nessun metodo
legge esiti, score o scelte dei concorrenti per decidere. Non si richiede
più una matrice esaustiva globale prima della valutazione: la protezione
dalla contaminazione è data dal contratto congelato e dagli input separati.
L'utente non modifica prompt o regole dopo aver visto risultati parziali.

## 9. Metriche e conservazione

L'unità di confronto resta il circuito. Ogni metodo pubblica esiti per tutti
i 90 casi, compresi fallimenti e interruzioni. Successi più fallimenti
coincidono con i casi conclusi; quelli ancora da elaborare sono distinti.

| Metrica primaria | Definizione |
| --- | --- |
| Successi | Compilazione terminata, circuito eseguibile sul Target, score finito |
| Fallimenti | Errori, timeout o interruzioni terminali; cause distinte |
| Retry | Chiamate LLM aggiuntive oltre la prima, per caso e totali; zero per compilazione e trasporto automatico |
| Score per circuito | Expected fidelity MQT 2.4.0, arrotondamento a 10 decimali, una compilazione |
| Score medio | Media sui successi, con denominatore; nessuna imputazione dei fallimenti |
| Token LLM | Input completo tokenizzato e output del server, per chiamata e cumulativi, inclusi tentativi falliti quando misurabili |
| Tempo totale | Dall'ingresso del circuito nel procedimento al suo esito, incluse preparazione, RAG, correzioni, processo e compilazione |
| Tempo compilazione | Misurato dentro il processo intorno a transpile o rl_compile |
| Tempo risposta LLM | Dall'invio della chiamata di generazione alla risposta completa; somma delle chiamate se ci sono correzioni |

I tempi usano `perf_counter` e secondi. Il tempo del processo di compilazione
è distinto dalla sola chiamata al compilatore. Se un processo muore senza
misura interna, il tempo compilatore rimane null. Token ignoti restano null;
si conservano anche somme parziali note. I token di input sono contati per
intero anche con cache; i contatori di calcolo effettivo restano nelle risposte
originali. Latenza e token non vengono confusi con costo monetario.

**Metriche secondarie:** tempo RAG; tempo complessivo di preparazione e scelta;
tempo selezione ML; chiamate fisiche; fatti non verificati; mediana dello
score; cause di errore; profondità e dimensione del circuito compilato;
log-score non arrotondato e indicazioni di arrotondamento a zero o underflow.
Memoria ed energia non sono raccolte in questa versione e sono dichiarate
mancanti. Nessuna stima viene presentata come misura.

L'oracle non è un metodo. Può essere assente. Un eventuale riferimento è
la migliore compilazione conosciuta nel preciso insieme di configurazioni,
seed e tentativi osservati. Non è la migliore configurazione possibile
in assoluto. La distanza dal riferimento è secondaria; vanno documentati
copertura, provenienza e criterio del riferimento. Un massimo parziale
non viene chiamato oracle esaustivo. Nessuno score di riferimento entra
nel prompt del circuito che si sta valutando.

I registri conservano circuito, SHA-256, split, metodo, configurazione,
modello/revisione/precisione, prompt, evidenze, risposte, verifiche, tentativi,
tempi, token, versione del codice, dipendenze, sistema operativo e risorse note.
Sono salvati prima e durante l'esecuzione, non solo al termine.
Non vengono salvati segreti.

Una ripresa salta ogni esito già concluso. Un caso senza esito dopo un arresto
improvviso viene conservato come interrotto, con qualità mancante; non viene
ripetuto per ottenere un risultato favorevole. I casi successivi proseguono.
I rapporti precedenti e i tentativi sfavorevoli rimangono disponibili.

## 10. Analisi e documenti

Ogni esecuzione produce il proprio riepilogo, tabella per circuito,
grafico degli score e sorgenti LaTeX. Le cartelle `tabelle/`, `grafici/`
e `latex/` sono distinte sotto `analisi/<impronta>/`.
`latex/risultati.tex` è inseribile nella tesi; `latex/verifica.tex`
è compilabile autonomamente con TeX Live e PGFPlots. Se pdflatex è presente
si produce anche il PDF. Dati e versione del generatore identificano l'analisi.

`prototipo/test/analizza.py` legge soltanto risultati già salvati.
Non avvia metodi mancanti. Il confronto dichiara metodi disponibili,
circuiti conclusi, successi, fallimenti e insieme comune. La differenza
di score è calcolata sui successi comuni, mantenendo l'appaiamento per
circuito. Non si confrontano soltanto medie con denominatori differenti.

Il nuovo piano descrittivo confronta LLM+RAG con ciascuno degli altri tre
metodi. Usa 10.000 ricampionamenti appaiati del circuito, seed 20260901
e intervalli percentile al 95% della differenza media di score. Con meno
di due circuiti comuni l'intervallo non viene stimato.
Il vecchio piano di 14 test sul regret non si applica al nuovo insieme
di metodi e all'oracle facoltativo. Non si dichiara superiorità statistica
sulla base di queste sole analisi descrittive.

Tutti i cambiamenti sono stabiliti prima del Test. L'esposizione storica
dei due circuiti ricordata nella sezione 2 resta un limite dichiarato;
non viene cancellata dall'emendamento. Un'eventuale analisi che li escluda
deve essere secondaria, separata e dichiarata.

## 11. Dimostrazione e tracciabilità

`prototipo/` è una dimostrazione autonoma del modello selezionato. Il profilo
portatile modifica le risorse e il contesto: non è una replica della validation.
Una prova su un nuovo circuito tecnico non apre il Test e non prova qualità generale.
L'archivio conserva codice, dati, tentativi sfavorevoli, sigilli, rapporti LaTeX,
figure e procedure originali. Le copie congelate non vengono ottimizzate in-place.
Per controllarne gli hash usare
`python archivio/riorganizzazione_2026_09_20/verifica_integrita.py` dalla radice.

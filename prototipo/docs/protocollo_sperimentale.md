# Protocollo sperimentale corrente

Documento operativo consolidato il **20 settembre 2026**. L'esperimento sui
circuiti mantiene l'identità **2.0.0**, con MQT Predictor **2.4.0**. La selezione
LLM ufficiale è **local-llm-v2**, con contratto di risposta **4.0.0**.
Questi numeri indicano tre cose diverse. La selezione locale v1 è storica.

Questa guida riunisce le regole già definite. Non avvia il Test e non cambia
partizioni, punteggi, ipotesi o soglie. Il testo precedente, con la cronologia
degli emendamenti e tutti i vecchi comandi, è conservato integralmente in
[archivio](../../archivio/esperimento_v2/docs/protocollo_sperimentale.md).
Per percorrere le fasi nell'ordine leggere la [guida pratica](guida_passo_passo.md).

## 1. Domanda della tesi e unità di confronto

Vogliamo capire se un LLM, aiutato da esempi di compilazione, sceglie bene
un dispositivo e una configurazione di `qiskit.compiler.transpile()`.
La misura è `expected_fidelity`, calcolata sui Target sintetici di MQT Bench.
Non eseguiamo circuiti su un computer quantistico reale.

L'unità statistica è il **circuito**, non una chiamata LLM o un seed.
Le domande riguardano contributo del RAG, confronto con un modello di frontiera,
MQT Predictor e metodi semplici, distanza dall'oracle, affidabilità, tempo,
costo e differenze per famiglia o numero di qubit.

Le ipotesi predefinite richiedono regret mediano inferiore a quello della
variante senza RAG, del modello di frontiera, di MQT e delle baseline semplici.
Per i primi due confronti richiedono anche successo non inferiore.
Un risultato non significativo non dimostra equivalenza.

## 2. Dati e separazione

Il corpus contiene **600 circuiti: 422 train, 88 validation, 90 test**.
Train costruisce gli esempi e i modelli. Validation sceglie la configurazione.
Test serve una sola volta per il confronto finale dopo tutti i controlli.

**Dataset** indica gli esempi per RAG/LLM. **Training set** indica i dati
circuito-dispositivo per il selettore supervisionato MQT.
Il RAG usa **396 circuiti train distinti per SHA-256**: i 26 alias byte-identici
non diventano nuovi esempi. I due realamprandom a 2 qubit semanticamente uguali
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
Ogni coppia viene compilata con seed **0, 1, 2**. Limite per compilazione:
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

## 7. Condizioni obbligatorie prima di aprire il Test

Devono risultare verificati: versioni esatte; cinque Target invariati;
corpus e partizioni integri; catalogo e configurazione LLM congelati;
piani validation/test coerenti; matrice validation completa dei tentativi;
RAG solo train e indice coerente con la verifica sugli 88 validation a k=5;
cinque modelli RL e classificatore a cinque classi; sei prove minime MQT;
selezione ufficiale conclusa e tutti i sigilli integri.

**Problema operativo individuato il 20 settembre:** il vecchio
`scripts/15_release_test_v2.py` richiama ancora `llm_selection.finalize`, cioè
la selezione globale v1. Non è sufficiente che quello script restituisca esito
positivo: occorre collegare esplicitamente il controllo alla selezione
`local-llm-v2`, congelare i metodi finali con/senza RAG e il relativo contratto,
verificare il modello di frontiera e aggiornare i piani prima dell'apertura.
La nuova cartella dimostrativa non sostituisce queste verifiche sperimentali.
Questa attività di preparazione al Test resta distinta dal riordino.

Il protocollo finale richiede la stessa configurazione del modello nei due
metodi con/senza RAG. Il contratto v4 basato su fatti degli esempi necessita
anche di una gestione esplicita del caso senza esempi: va definita e verificata
prima di aprire il Test, senza scegliere la regola in base ai suoi risultati.
Il modello di frontiera usa invece il suo prompt diretto distinto, con QASM,
cinque dispositivi e dodici configurazioni, senza maschera applicativa o RAG.

## 8. Ordine obbligatorio del confronto sul Test

1. Concludere i controlli precedenti, congelare impostazioni e piano di analisi,
   quindi produrre il record di apertura. Il Test resta chiuso fino ad allora.
2. Materializzare i circuiti Test nei manifest dei cinque dispositivi.
3. Produrre, registrare e sigillare le decisioni di LLM+RAG, stesso LLM senza RAG
   e modello di frontiera, **prima** di rendere disponibili gli score Qiskit Test.
4. Eseguire `qcompile` tre volte per circuito, in processi nuovi.
5. Produrre la matrice Qiskit Test con i tre seed e i limiti congelati.
6. Ricostruire le viste e valutare tutti i metodi richiesti. Il RAG train resta
   identico; validation e test non si aggiungono all'indice.
7. Generare analisi, tabelle, figure e testo per la tesi da dati conservati.

I metodi sono: LLM+RAG; stesso LLM senza RAG; modello di frontiera; MQT;
Qiskit predefinito ai livelli 2 e 3 su ciascuno dei cinque dispositivi
(**dieci baseline distinte**); scelta casuale congelata; oracle esaustivo.
Il casuale estrae uniformemente una coppia compatibile per ripetizione,
senza nuova estrazione dopo un fallimento. Non si sceglie a posteriori
il dispositivo migliore delle baseline fisse.
Il modello di frontiera ha una chiamata e restituisce solo coppia dispositivo/configurazione;
nessuna correzione guidata. Retry di trasporto, se previsti, vanno congelati e contati.

## 9. Metriche, mancanze e confronti

Il valore primario per circuito è la mediana dei tre score, disponibile solo
con tre successi. Per MQT gli indici 0,1,2 sono ripetizioni, non seed Qiskit
controllati. Per il casuale possono rappresentare tre coppie diverse.
L'oracle richiede l'intera matrice compatibile riuscita; un massimo parziale
non viene chiamato oracle. Le parità esatte seguono l'ordine dispositivo/configurazione
del catalogo; quasi parità rel_tol=1e-12, abs_tol=1e-15 sono segnalate.

Regret assoluto = score oracle meno score metodo. Regret relativo = regret
assoluto diviso score oracle, non disponibile con oracle zero.
Non si tronca un regret negativo: va conservato e indagato.
La metrica primaria rimane expected_fidelity; si conserva anche il log naturale
quando calcolabile, indicando underflow e dati mancanti senza valori inventati.
Il riferimento osservato usato per selezionare v2 non sostituisce automaticamente
l'oracle nella valutazione confermativa del Test.

Se una ripetizione fallisce, aggregato e regret primari sono null con motivo.
Si conservano comunque tentativi riusciti, errori e timeout. Nessuna imputazione.
Le baseline non applicabili per larghezza sono dichiarate ed escluse dal proprio
denominatore di applicabilità, senza confonderle con fallimenti.
Qualità sui successi, tasso di successo e numerosità comune vanno mostrati insieme.

Registrare successo per tentativo e tre-su-tre, tipi di errore, accuratezza di
dispositivo/configurazione/coppia dove applicabile, tempi separati di recupero,
scelta, chiamate, compilazioni, attesa e totale; chiamate fisiche, correzioni,
token, costi e memoria quando misurabili. MQT non ha un config_id Qiskit.
Il tempo della raccomandazione si conta una volta, non tre.

Conservare run_id, circuito/hash/split, repetition_index, qiskit_seed,
attempt_index, modelli/revisioni/precisione, prompt e risposte, evidenze,
parametri, versioni, hardware e risorse. Distinguere misure, stime, riusi e dati
mancanti. Nessun segreto. Un run terminale non viene rifatto per migliorare l'esito;
una ripresa conserva causa e tentativi precedenti.

## 10. Piano statistico finale

Il piano finale è distinto dalla selezione descrittiva. Seed **20260901**;
**10.000** ricampionamenti del circuito con rimpiazzo, mantenendo appaiati i metodi;
intervalli percentile al 95%. Riportare n totale/applicabile/completato/comune,
media, mediana, deviazione standard campionaria (n-1), IQR con quantili lineari,
famiglie e classi 1–10, 11–27, 28–56, 57–90 qubit. Gruppi con meno di cinque
circuiti restano puramente descrittivi.

Confronti sul regret: Wilcoxon bilaterale appaiato, zero_method=pratt,
alpha=0,05, algoritmo e libreria congelati. Correzione Holm per i 14 confronti
primari: senza RAG, frontiera, MQT, casuale, dieci baseline fisse. Un confronto
non eseguibile rimane nella famiglia con p convenzionale 1. L'oracle è riferimento.
Completamento tre-su-tre: McNemar esatto, famiglia corretta separatamente con Holm.
Latenza, token, costo, log-score e sottogruppi sono analisi secondarie.

Un confronto favorevole richiede insieme p corretto sotto0,05, direzione prevista,
intervallo della differenza senza zero, denominatori/fallimenti mostrati e tasso
di completamento osservato non inferiore sullo stesso insieme applicabile.
Non si modifica la metrica o il sottoinsieme dopo il Test. Il contributo del RAG
è sostenuto dal confronto con/senza RAG, non da una vittoria su altre baseline.

## 11. Dimostrazione e tracciabilità

`prototipo/` è una dimostrazione autonoma del modello selezionato. Il profilo
portatile modifica le risorse e il contesto: non è una replica della validation.
Una prova su un nuovo circuito tecnico non apre il Test e non prova qualità generale.
L'archivio conserva codice, dati, tentativi sfavorevoli, sigilli, rapporti LaTeX,
figure e procedure originali. Le copie congelate non vengono ottimizzate in-place.
Per controllarne gli hash usare
`python archivio/riorganizzazione_2026_09_20/verifica_integrita.py` dalla radice.

# Seconda validation: fatti controllabili e ipotesi libera

Data: 19 settembre 2026. Studio: `local-llm-v2`.
La procedura corrente è descritta nel [protocollo](../protocollo_sperimentale.md)
e nella [guida operativa](../../llm_selection/v2/README.md).

## Perché è stata modificata

La prima validation verificava soprattutto la forma della risposta e la coppia
scelta. Un testo plausibile poteva attribuire agli esempi fatti che non
contenevano. La nuova versione separa la decisione, alcuni fatti controllabili
e una motivazione che rimane un'ipotesi.

Il confronto precedente resta conservato. Questa revisione nasce dopo aver
esaminato quella validation: non costituisce un esperimento indipendente.
Il test non viene aperto.

## Risposta e verifiche

Lo schema v4 richiede una coppia dispositivo/configurazione, uno o due fatti
e un'ipotesi libera, lunga al massimo 1000 caratteri. Il prompt chiede frasi
complete, senza riferimenti come E1 o E3 nella motivazione. Il limite è stato
aumentato da 400 a 1000 su richiesta dell'utente.

I fatti possono attestare quattro cose: la coppia compare fra i risultati
mostrati di un esempio; il dispositivo coincide con quello dell'esempio;
i due circuiti hanno lo stesso numero di qubit; il dispositivo ha abbastanza
qubit. Il primo fatto comprende le configurazioni mostrate e i pareggi
espliciti: non significa necessariamente essere il vincitore unico.

Il controllo legge soltanto i dati già presenti nel prompt. Non usa un secondo
modello. L'ipotesi non viene valutata semanticamente: la verifica dei fatti non
certifica il testo libero né dimostra la bontà della scelta.

Un fatto errato produce una richiesta di correzione con i dati pertinenti.
Sono disponibili tre risposte complete. Dopo la terza, una risposta conforme
con coppia ammessa resta un successo anche se i fatti sono errati:
`accepted_with_unverified_facts=true`. Una struttura non conforme o una
coppia non ammessa rimangono un fallimento.

## Interruzioni e costi

Una chiamata interrotta non consuma un tentativo logico. I file originali sono
spostati in `interrupted/attempt_N/<id>/`; alla ripresa viene ricreato
`attempt_N`. I costi fisici misurabili restano nel resoconto. Non vengono
eliminati gli errori precedenti. Una risposta completa già salvata viene invece
recuperata senza una nuova chiamata.

La soglia RAM è 1 GiB. Il limite hotspot è 110 °C, con pausa a 105 °C e ripresa
a 100 °C; il limite edge resta 95 °C. Il recupero richiede tre campioni favorevoli.
Questi sono limiti operativi richiesti dall'utente, non una garanzia specifica
del produttore verificata per la RX 6750 XT.

Le interruzioni dovute alle risorse attendono il recupero e ripartono.
Tre interruzioni di trasporto senza causa accertata sospendono la procedura,
che rimane riprendibile. Un timeout reale senza interruzione delle risorse
resta terminale. Tempi o token non disponibili restano mancanti, non valgono zero.

## Esperimento e regret

Si usa un solo prompt alle temperature 0, 0,4 e 0,7:
`p0_t0`, `p0_t04`, `p0_t07`.
Con tre modelli e 88 circuiti sono 792 episodi di validation.
Il train tecnico usa cinque circuiti per tutte le nove combinazioni: 45 episodi.

Il regret principale confronta la scelta con la migliore mediana osservata
fra le coppie riuscite con tutti i seed 0, 1 e 2. Questo riferimento esiste
per tutti gli 88 circuiti. Per 70 circuiti la matrice è incompleta: non si
presenta quindi questo riferimento come massimo esaustivo. Il confronto
esaustivo sui 18 circuiti resta aggiuntivo. Se manca lo score della coppia
scelta, il suo regret resta mancante e il denominatore viene dichiarato.

La selezione ordina completezza delle scelte compilabili, regret mediano
sui circuiti comuni, correzioni e costo. Legge i risultati Qiskit soltanto
dopo aver sigillato tutte le decisioni dei modelli.

## Tracciabilità e verifiche

Sono conservati prompt, risposte, correzioni, controlli dei fatti, interruzioni,
parametri, copie del codice, impronte dei pesi e input, risorse e costi.
Gli artefatti del nuovo studio sono separati da quelli di `local-llm-v1`.
Il congelamento richiede che il codice di inferenza e valutazione sia identico
a quello delle prove train. Correzioni limitate al rapporto o al congelamento
sono registrate separatamente; per il modulo dello studio viene confrontato
anche l'albero sintattico, escludendo solo le funzioni di congelamento.
Le impronte originali dei tentativi non vengono riscritte.

La suite completa ha superato **266 test**. Comprende vincoli dello schema,
pareggi storici, controllo dei fatti, successo con fatti errati al terzo
tentativo, recupero senza una chiamata aggiuntiva, ripetizione del tentativo
interrotto e valutazione su una matrice incompleta.

Le prove preparatorie sono conservate in `development/train_prompt1`,
`development/train_prompt2` e `development/train_compatibility_fix`.
I manifest registrano il motivo della ripetizione e le impronte dei file.
Il primo prompt produceva spesso testi tagliati al limite di 400 caratteri;
il secondo chiedeva una frase breve; il terzo accoglie il limite di 1000.
L'ultimo passaggio corregge una regressione di importazione trovata dai test
e riconosce le interruzioni per risorse anche quando il server originale è
già stato sostituito.

Durante una prova preparatoria la RAM disponibile è scesa a 865185792 byte.
Il supervisore ha conservato la chiamata interrotta, atteso il recupero
e iniziato a ricaricare il server. L'esecuzione è stata poi fermata
volontariamente per applicare la correzione emersa dai test.
Il registro originale è `servers/local-llm-v2-20260919-202234-qwen-0/resource_abort.json`.

## Esito delle prove definitive

Sono concluse tutte le 45 prove: 45 coppie ammesse, 35 risposte finali con fatti
verificati e 10 accettate con fatti ancora errati. Questi sono esiti tecnici
sul train, non una stima di qualità sulla validation.

| Modello | Episodi | Fatti corretti alla prima | Fatti corretti alla fine | Accettati con fatti errati | Correzioni | Chiamate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen | 15 | 10 | 11 | 4 | 9 | 24 |
| phi | 15 | 4 | 14 | 1 | 14 | 29 |
| gemma | 15 | 5 | 10 | 5 | 17 | 32 |

Le correzioni portano le risposte con fatti verificati da 19/45 a 35/45.
Sono state effettuate 85 chiamate di generazione e 40 correzioni. Il controllo
deterministico dei fatti ha richiesto circa 6,33 secondi complessivi; non usa
un secondo modello. Le chiamate correttive costituiscono il costo aggiuntivo
principale. Non è stata interrotta alcuna chiamata di generazione in questa
esecuzione definitiva.

Il primo caricamento di Gemma è stato fermato perché la RAM disponibile è
scesa sotto 1 GiB. Il supervisore ha atteso e il secondo caricamento è riuscito,
senza modificare i parametri. Questo evento precede gli episodi: è nei registri
del supervisore, non nel contatore delle chiamate di generazione interrotte.

Le ipotesi degli 85 tentativi hanno una lunghezza fra 87 e 491 caratteri.
Nessuna raggiunge il limite di 1000. La presenza di punteggiatura finale è
soltanto un controllo formale, non una prova di correttezza. Gli ID E1–E5
compaiono in 11/85 testi, inclusi 8/45 testi finali: l'istruzione di evitarli
non è sempre rispettata. Non si aggiunge una correzione semantica automatica,
coerentemente con la scelta di lasciare libera l'ipotesi.

Il rapporto è in technical_report: sorgenti LaTeX, PDF di quattro pagine,
figure PNG/SVG, CSV e verification.json. È stato compilato e controllato
visivamente, con etichette leggibili e senza avvisi di impaginazione.
Una correzione a una frase LaTeX e alla disposizione delle etichette è stata
eseguita dopo il train. Sono cambiamenti del rapporto, non dell'inferenza.
Le revisioni sono registrate in technical_code_reviews nel manifest congelato.
Tutte le 45 richieste iniziali sono state ricostruite con impronta identica;
i controlli su tutte le 85 risposte sono stati ricalcolati e coincidono
con gli esiti conservati.

La validation non è stata avviata. Il comando di avvio e ripresa è:

    .venv/bin/python -m llm_selection.v2 validate --study local-llm-v2

Non cambiare l'identificativo per riprendere una esecuzione interrotta.


Lo studio è stato congelato il 2026-09-19T19:05:43.904125+00:00. Il comando verify ha
confermato le impronte del codice, degli input e delle prove train, oltre
all'integrità dei file storici della prima validation. Gli episodi della
nuova validation sono ancora zero e il test resta chiuso.

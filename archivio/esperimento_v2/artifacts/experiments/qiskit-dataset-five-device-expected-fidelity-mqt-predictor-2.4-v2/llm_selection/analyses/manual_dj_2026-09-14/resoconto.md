# Analisi della risposta manuale di Qwen sul circuito DJ

La risposta passa lo schema JSON, ma non i controlli sui collegamenti tra affermazioni e fonti.
La scelta di ibm_falcon_127 con o2_default_default è ammessa per questa richiesta.
Questa analisi non misura la qualità della compilazione né dimostra che la scelta sia ottimale.

## Dati analizzati

L'utente ha fornito il JSON nel messaggio e il ragionamento in un allegato.
Il JSON è stato trascritto rimuovendo gli escape Markdown prima degli underscore.
Se le sequenze letterali `\_` fossero presenti nel file prodotto da Qwen, il testo non sarebbe JSON valido.
L'analisi strutturale e semantica riguarda la versione normalizzata, senza altre correzioni.

Il ragionamento è conservato byte per byte in reasoning_utente.txt: 25.184 caratteri e 2.394 parole separate da spazi.
La parola “Wait” compare 23 volte. È un conteggio del testo, non una misura della capacità di ragionamento.

La chat corrisponde al server qwen-chat-20260914-182526, task 93.
La ricostruzione locale del prompt originale verifica il suo hash, quello del QASM e gli identificativi della richiesta.
È una prova tecnica su train. Non è un risultato di validation o test.

## Tempi misurati dal server

| Fase | Prova automatica DJ, qwen-prova-07 | Chat manuale |
|---|---:|---:|
| Token del prompt | 80.612 | 80.617 |
| Lettura del prompt | 1.378,919 s (22 min 59 s) | 1.416,346 s (23 min 36 s) |
| Token generati | 1.993 | 12.501 |
| Generazione | 452,348 s (7 min 32 s) | 2.965,559 s (49 min 26 s) |
| Totale delle due fasi | 1.831,267 s (30 min 31 s) | 4.381,905 s (73 min 2 s) |
| Velocità di generazione | circa 4,41 token/s | circa 4,22 token/s |

Il tempo totale è la somma dei tempi del modello, non include tutto l'avvio del server o il lavoro dell'utente.
I token di generazione del server non distinguono ragionamento, risposta finale e marcatori del modello.
Non attribuiamo quindi un numero preciso di token al solo ragionamento.

La chat ha generato circa 6,27 volte i token della prova automatica.
L'aumento di durata è soprattutto nella generazione; la lettura del prompt ha richiesto circa 37 secondi in più.
La chat mostra un ragionamento esteso, mentre la prova automatica chiedeva enable_thinking=false e limitava l'uscita a 2.048 token.
Gli altri parametri della chat e l'eventuale grammatica della richiesta non sono ricostruibili completamente dal log.
Questo confronto descrive due esecuzioni; non è un confronto sperimentale con tutti i parametri controllati.

## Cosa ha fatto bene

Qwen ha ripreso il request_id e il catalog_snapshot_id della richiesta.
Ha scelto un dispositivo compatibile e una configurazione consentita.
Il livello 2, layout e routing null corrispondono a o2_default_default; il seed 0 è ammesso.
Il dispositivo e la configurazione corrispondono al primo risultato storico citato, a distanza 0 nel recupero.

Questi fatti confermano l'ammissibilità della scelta.
Il caso di train con evidenza a distanza 0 non dimostra generalizzazione.
Il punteggio storico menzionato dal modello non è una nuova misura del circuito compilato in questa chat.

## Errori nei riferimenti

Il validatore produce 21 segnalazioni di 9 tipi.
Diverse sono conseguenze dello stesso problema, quindi non equivalgono a 21 errori indipendenti.
Il risultato ordinario limita il resoconto a 12 voci, compresa l'indicazione degli errori omessi.
Per l'analisi abbiamo esteso soltanto tale limite nel processo locale e salvato tutte le segnalazioni.

| Problema | Evidenza |
|---|---|
| Riferimenti non collegati | I 4 claims citano evidence_…; nessun reference_id dichiarato ha quel valore. |
| Manca source_claim_id | Tutti i 4 riferimenti historical_result omettono l'identificativo dell'affermazione storica sorgente. |
| Fonte duplicata | I 4 riferimenti ripetono la stessa tupla di fonte senza distinguere il claim sorgente. |
| Parametri incompleti | historical_configuration_support contiene configuration_id, ma richiede anche device_id. |
| Compatibilità corrente spiegata con storia | live_compatibility deve avere evidence_ref_ids vuoto: la controlla il programma sulla richiesta corrente. |
| Avvertenza collegata alla fonte sbagliata | scientific_caveat cita un risultato storico; richiede invece la specifica avvertenza del registro. |

C'è anche una correzione necessaria che i primi errori impediscono di verificare a valle:
il source_claim selected_device scelto nel registro contiene cinque evidence_ids.
Il validatore richiede di citarle tutte, mentre Qwen ha riutilizzato soltanto la prima.
La correzione dei soli nomi dei riferimenti non sarebbe quindi sufficiente.

Esempio concettuale di collegamento:

```text
claims[].evidence_ref_ids = ["ref1"]
                         ↓
evidence_refs[].reference_id = "ref1"
    record_id       → record storico
    source_claim_id → affermazione nel record
    source_id       → evidenza di quell'affermazione
```

ref1 è un identificativo locale della risposta e può essere breve.
Gli identificativi delle fonti devono invece esistere nel registro, oppure essere risolti da alias tramite una mappa verificata.

## Cosa mostra il ragionamento

La scelta del dispositivo e della configurazione appare nella prima parte del testo.
In seguito il modello torna molte volte su claim_id, reference_id, source_claim_id e source_id.
Arriva a questa regola sbagliata:

> And evidence_ref_ids in claims must match source_id in evidence_refs.

Devono corrispondere a reference_id.
Il modello tratta inoltre “live” come se implicasse accesso a hardware online.
Nel progetto indica la compatibilità con la richiesta corrente, verificata localmente.

Il testo mostra quindi una difficoltà nel rappresentare e collegare le fonti.
Non dimostra da solo un'incapacità di scegliere una configurazione quantistica.

## Un limite del nostro prompt

Lo schema passato al modello controlla la struttura, ma non esprime molte relazioni applicate dal validatore.
source_claim_id è definito tra le proprietà ma non obbligatorio per i riferimenti storici nello schema.
Non sono esplicitate nello schema le combinazioni di parameters richieste per ciascun claim_type.
Le regole del prompt non chiariscono il collegamento evidence_ref_ids → reference_id, il divieto di prove storiche per live_compatibility o l'obbligo di citare tutto l'insieme di evidenze del claim sorgente.

La generazione con grammatica usata dalla prova automatica vincolava quello schema.
La validità di questo JSON mostra che il solo schema attuale non basta a ottenere una raccomandazione accettata.
Per la chat manuale non abbiamo una cattura della richiesta che dimostri quali vincoli fossero attivi.

Non possiamo attribuire l'esito soltanto ai 4 miliardi di parametri.
Prima va eliminata questa ambiguità del contratto.

## Proposte

1. Provare il prompt compatto con identificativi brevi, mantenendo inizialmente cinque esempi: la bozza già misurata contiene 18.372 token invece di 80.612. Aggiungere poche istruzioni precise sui collegamenti; il nuovo conteggio andrà misurato.
2. Aggiungere un esempio minimo di risposta accettata e le regole mancanti. regole_esplicite_proposte.txt raccoglie quelle ricavate dal validatore.
3. Valutare una risposta più semplice dal modello: scelta del dispositivo, configurazione e affermazioni storiche pertinenti. Il programma può poi costruire riferimenti, metadati e avvertenze con regole fisse. Questo cambia il contratto e va sperimentato e documentato.
4. Confrontare cinque e due esempi solo dopo aver chiarito il formato, a parità delle altre impostazioni.
5. Valutare il ragionamento attivo o disattivato e, successivamente, un modello più grande con confronti controllati.

Per ciascuna prova registrare: token in ingresso e uscita, tempo di lettura e generazione, JSON valido, schema rispettato, riferimenti validi, decisione accettata, correzioni necessarie e qualità della scelta quando misurabile.
Prima di riattivare le correzioni automatiche resta da risolvere il problema già rilevato nella serializzazione degli errori del runner.

Queste sono proposte. L'analisi non ha modificato il prompt operativo, il validatore, il profilo GPU o gli esiti originali e non ha avviato nuove inferenze.

## Artefatti e riproducibilità

- risposta_utente_normalizzata.json: trascrizione da validare.
- reasoning_utente.txt: allegato originale.
- validation.json e validation_all_issues.json: esito ordinario e diagnostica completa.
- preliminary.json: conteggi del testo e tempi estratti dal log.
- cited_registry_record.json: record storico realmente citato.
- server.*.snapshot.*: copie dei log, delle risorse e della configurazione.
- provenance.json e manifest.json: provenienza e hash.
- analyze.py: procedura locale di ricostruzione e analisi.
- analysis_attempts.json: registra anche il primo tentativo, fermato da una dipendenza non presente. È stato usato il validatore già incluso nel progetto, senza installare dipendenze.

analyze.py crea i file in modalità esclusiva per non sovrascrivere esiti.
Per ripetere l'analisi, copiare lo script e il JSON trascritto in una nuova cartella, mantenendo accessibili gli originali indicati nel codice, ed eseguire dalla radice del progetto con PYTHONPATH=. e .venv/bin/python.

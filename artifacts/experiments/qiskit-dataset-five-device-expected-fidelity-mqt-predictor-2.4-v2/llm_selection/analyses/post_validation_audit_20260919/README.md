# Controllo della validation locale conclusa

19 settembre 2026. Studio `local-llm-v1`, vincitore registrato `qwen/p0_t07`.
Questo e un controllo descrittivo successivo alla selezione. Non modifica il
protocollo, i prompt, i successi/fallimenti, il vincitore o i file sigillati.
Nessuna nuova inferenza, compilazione Qiskit o lettura dei circuiti test.

## Esito principale

Ci sono 792 episodi e 792 tentativi: 789 risposte accettate al primo invio e
3 errori di trasporto. Nessuna risposta ricevuta ha attivato le correzioni.
I tre errori dipendono dall'arresto del server da parte del monitor delle risorse.
Non sono tre risposte errate dei modelli.

Il successo applicativo non certifica la motivazione. Le spiegazioni contengono
errori verificabili, citazioni deboli e conclusioni non dimostrate, anche nel
modello vincitore. Esistono anche motivazioni plausibili e riferimenti storici
coerenti: non tutte le risposte sono sbagliate.

## I tre errori di trasporto

| Modello/configurazione | Circuito | Causa registrata | Durata chiamata |
| --- | --- | --- | ---: |
| qwen/p1_t0 | qft_indep_qiskit_6 | Hotspot 108 gradi C; limite operativo raggiunto | 3,119 s |
| phi/p0_t07 | qft_indep_tket_50 | Hotspot 108 gradi C; limite operativo raggiunto | 1,663 s |
| gemma/p0_t07 | pricingcall_indep_qiskit_5 | RAM libera 1.572.421.632 byte, circa 1,46 GiB, sotto 1,5 GiB | 1,990 s |

Tutti riportano `curl_exit_code=56`, `Recv failure: Connection was reset`,
`stream_done=false` e risposta vuota. I file `resource_abort.json` collocano
l'arresto dentro l'intervallo della chiamata. Gemma non e stato fermato dalla
temperatura: il campione era a 98 gradi C di hotspot e 66 di edge. Il monitor
arresta per RAM dopo tre campioni consecutivi sotto soglia.

`gateway.generate()` fa una sola richiesta HTTP al server locale Windows.
`run.summarize_response()` classifica l'interruzione come `transport_failure`.
Il ciclo di `run.episode()` continua solo quando lo stato e `invalid_output`:
le tre chiamate sono un massimo per correggere una risposta ricevuta ma non
conforme, non tre tentativi garantiti per ogni genere di errore. Non esistono
ripetizioni automatiche del trasporto. La decisione di fallimento viene salvata
prima di controllare se il server e ancora disponibile. Alla ripresa si saltano
le decisioni gia terminali. Questo spiega il singolo tentativo conservato.

Le regole corrispondono al codice congelato e al protocollo. Dal punto di vista
scientifico, la misura di successo include quindi anche l'affidabilita del
sistema di esecuzione: non misura soltanto la capacita del modello di rispondere.

## Effetto sulla scelta

Il primo criterio e il numero di decisioni valide e compilabili su 88 casi.
Le tre combinazioni interrotte hanno 87/88; le altre sei hanno 88/88.
Il secondo criterio confronta il regret assoluto mediano sui soli 18 circuiti
comuni con oracle disponibile. I 70 casi senza oracle non entrano nel regret.

| Configurazione | Successi/88 | Regret mediano disponibile (18 circuiti) |
| --- | ---: | ---: |
| qwen/p0_t07 | 88 | 0,0019003071 |
| gemma/p0_t07 | 87 | 0,00161533715 |
| phi/p0_t07 | 87 | 0,00196187125 |

Qwen rimane il vincitore delle regole fissate. Gemma avrebbe il regret mediano
piu basso sui casi misurabili, ma e escluso al primo criterio per il problema
RAM. Non e corretto concludere che Qwen abbia la migliore qualita assoluta di
compilazione fra tutti i candidati, ne cambiare il vincitore retroattivamente.
La qualita delle tre risposte mai ottenute resta sconosciuta.

## Copertura e metodo del controllo claim/evidence

- Esaminati tutti i 792 tentativi. Per i tre senza risposta claim ed evidence
  non sono valutabili. Il denominatore delle spiegazioni e quindi 789.
- Controllati manifest, hash sorgente, esempi RAG, alias, coppia scelta e risultati
  storici forniti per ogni tentativo.
- Tutti gli esempi recuperati appartengono al train. Nessuno ha lo stesso hash
  sorgente del circuito corrente. Tutte le richieste native coincidono con il
  template archiviato. Nelle sezioni correnti del prompt non sono comparsi campi
  di score/regret: i median_score sono negli esempi storici.
- Le 789 spiegazioni sono state raggruppate in 645 formulazioni non vuote,
  sostituendo nomi, numeri e alias per ridurre le ripetizioni. Sono state lette
  tutte le formulazioni; i controlli sui dati riguardano comunque ciascuna riga.
- Per ogni tentativo sono conservati testo originale, citazioni, dati correnti,
  porte del dispositivo, sostegno storico e osservazioni. La lettura qualitativa
  e dell'assistente, non di annotatori umani indipendenti.
- Non viene prodotta una percentuale globale di correttezza semantica. Le frasi
  vaghe, le analogie e le pretese di causalita non sono tutte decidibili con
  questi controlli. Nessun risultato originario viene rietichettato.

## Che cosa emerge

| Modello | Risposte ricevute | Nome storico non corrispondente alle citazioni | Coppia senza sostegno diretto nelle prime configurazioni/parita citate |
| --- | ---: | ---: | ---: |
| Qwen | 263 | 0 | 18 |
| Phi | 263 | 18 | 14 |
| Gemma | 263 | 0 | 112 |
| Totale | 789 | 18 | 144 |

Le colonne possono sovrapporsi. Il primo indicatore confronta identificativi
espliciti: anche una variante Qiskit nominata al posto di Tket viene segnalata.
Il secondo non e automaticamente un errore: il modello puo scegliere una coppia
non presente fra i vincitori storici. In tal caso l'esempio non prova che quella
coppia abbia ottenuto lo score o il primo posto che eventualmente le attribuisce.
Alcune risposte Gemma motivano soltanto compatibilita e configurazione di base:
sono scelte consentite, ma la citazione aggiunge poco sostegno specifico.

Le parita sono un altro limite. Il segnale automatico sul superlativo ne
individua 194, ma non e un conteggio di errori: una configurazione puo avere il
massimo a pari merito. Sono scorrette le pretese di superiorita esclusiva o il
trasferimento di quel risultato a un circuito mai misurato.

### Esempi verificati

Gli identificativi seguenti rimandano a `studies/local-llm-v1/`, sempre
`attempt_1/summary.json`. Sono ricercabili nella tabella completa.

| Tentativo | Affermazione | Verifica |
| --- | --- | --- |
| phi/p1_t0/qft_indep_tket_40 | Nomina graphstate tket 40 e cita E1 | E1 e ae tket 40; graphstate e E3. Le configurazioni di E3 sono a pari score. |
| gemma/p0_t07/qft_indep_tket_9 | Attribuisce al QFT corrente score 0,9723011068 | Quel numero e di graphstate tket 9, esempio E5 del train. |
| phi/p0_t0/qft_indep_tket_60 | Attribuisce al QFT corrente mediana 0,5548196521 | Il numero e di graphstate tket 60, esempio E3 del train. |
| qwen/p0_t07/qft_indep_qiskit_12 | 12 qubit superano la capacita di Falcon 27 | Falso: 12 e minore di 27. Heron 156 non e l'unica scelta compatibile. |
| qwen/p0_t07/pricingcall_indep_tket_7 | Falcon 127 ha CCX nativa | CCX non compare nelle operazioni del Target fornito. Va decomposta. |
| qwen/p0_t07/qft_indep_qiskit_11 | Il circuito usa 5 CP | Le feature riportano 55 CP. Cinque e il numero di SWAP. |
| qwen/p0_t0/qft_indep_tket_10 | Il circuito richiede 156 qubit | Ne richiede 10. 156 e la capacita del dispositivo. |
| qwen/p1_t0/qft_indep_qiskit_12 | Le 66 CP sono native su Quantinuum | Il Target espone rx, ry, rz, rzz, measure e if_else; CP non e nativa. |

Non basta quindi verificare che E1 esista. Serve verificare se il fatto enunciato
riguarda davvero quel circuito, dispositivo, configurazione, numero e tipo di
risultato. La piena connettivita elimina vincoli di collegamento, ma non rende
tutte le porte native e non dimostra la migliore fedelta per un circuito nuovo.

Il validatore v3 controlla JSON, schema, compatibilita, configurazione ammessa,
claim non vuoto e appartenenza delle citazioni agli esempi forniti. Non verifica
la verita del testo libero. Lo dichiara nelle avvertenze. La grammatica imposta
sul server facilita inoltre JSON e alias formalmente corretti al primo invio.
La qualita della spiegazione non entra nella selezione corrente.

Un esempio con dati storici coerenti e `phi/p0_t07/qftentangled_indep_qiskit_7`:
i tre score citati coincidono con E1, E2 ed E3. Anche qui sono valori del train e
parita, non una misura del QFT. La correttezza di una parte della spiegazione non
certifica l'intera conclusione.

## Differenza tra p0_t0 e p1_t0

Sono entrambi a temperatura zero e usano gli stessi dati, cinque esempi RAG,
TOON, schema JSON, limite di 4096 token, seed e validatore. La verifica dei
messaggi originali su 264 coppie modello/circuito conferma che l'unica differenza
e la frase finale aggiunta da p1:

> Check that the device is compatible, config_id is allowed for it, and every cited example ID was supplied. Do not report a measured score for the new circuit.

In italiano: controlla dispositivo, configurazione ed esistenza degli esempi
citati; non attribuire al circuito nuovo uno score misurato.

E un'istruzione al modello, non un controllo software aggiuntivo, una seconda
chiamata o un ragionamento esteso. Gli errori in p1 mostrano che l'istruzione non
assicura che il claim sia corretto. p0_t07 usa invece il prompt p0 con temperatura
0,7. Zero non implica la stessa risposta fra prompt diversi.

## File e riproduzione

- `audit.py`: estrazione delle risposte, controlli riproducibili e collegamento
  fra errori di trasporto e registri delle risorse.
- `review.py`: esportazione dei dati correnti, confronto dei prompt e annotazioni.
- `reviewed_attempts.csv`: tabella leggibile di tutti i tentativi, con note.
- `reviewed_attempts.jsonl`: stessa revisione con dati correnti e prove dettagliate.
- `attempts.jsonl`, `attempts.csv`: estrazione originale e segnali automatici.
- `claim_groups.json`, `review_notes.json`: formulazioni e metodo qualitativo.
- `transport_failures.json`: errori, tempi e campioni che hanno causato l'arresto.
- `summary.json`: conteggi e criteri applicati dal selettore originale.
- `prompt_integrity_checks.json`: confronto con il template e provenienza train.
- `prompt_variant_comparison.json`: confronto p0/p1 per tutte le 264 coppie.
- `input_fingerprints.json`: SHA-256 dei file letti, inclusi i registri esterni.

Dalla radice del progetto, con `AUDIT` impostato alla cartella di questo documento:

```bash
.venv/bin/python "$AUDIT/audit.py"
.venv/bin/python "$AUDIT/review.py"
```

Questi comandi aggiornano soltanto gli output derivati nella cartella dell'audit.
Le annotazioni qualitative sono esplicite nel codice e nel JSON e possono essere
riviste da un secondo lettore. I controlli circoscritti e i conteggi sono
riproducibili; il testo libero non e trattato come formalmente dimostrato.

## Conseguenze per il seguito

Conservare la selezione originale e riportare separatamente le interruzioni
infrastrutturali. Non ripetere soltanto i tre episodi per sostituire i fallimenti
nella classifica gia congelata. Un diverso trattamento del trasporto o della
qualita delle motivazioni richiede un esperimento distinto o un emendamento
esplicito che conservi tutti gli esiti e motivi la comparabilita.

Per una versione futura si possono strutturare i fatti citati (esempio, coppia,
valore, parita) e confrontarli deterministicamente. La spiegazione libera puo
restare, ma va distinta dai fatti verificati e dall'ipotesi sul circuito nuovo.
Il presente controllo non implementa tali cambiamenti.

## Effetto osservato della checklist sulle scelte

Confronto descrittivo della coppia dispositivo/configurazione. Si usano solo i
circuiti con risposta ricevuta in entrambe le condizioni, senza riempire il
fallimento Qwen.

| Modello | Circuiti comuni | Dispositivo diverso | Coppia diversa |
| --- | ---: | ---: | ---: |
| Qwen | 87 | 9 | 10 |
| Phi | 88 | 0 | 5 |
| Gemma | 88 | 13 | 15 |

La checklist puo quindi cambiare la scelta pur mantenendo temperatura zero.
Questi conteggi non dimostrano che p1 migliori il risultato. I dati sono in
`p0_p1_choice_comparison.json`, generati da `review.py`.

La verifica finale in `verification.json` ha controllato 6.350 file di ingresso
e nove file della prova della selezione: nessuna modifica rilevata.

# Seconda validation locale: fatti e ipotesi

Questa versione mantiene separati la scelta del modello, i fatti controllabili
e l'ipotesi libera. Il riferimento normativo è
[il protocollo sperimentale](../../docs/protocollo_sperimentale.md).

## Risposta e successo

Lo schema è schemas/llm_recommendation_v4.schema.json. Richiede selected_device,
config_id, da uno a due fatti distinti e hypothesis (massimo 1000 caratteri).
Il prompt chiede un'ipotesi naturale senza ID E1–E5; il testo non viene
certificato né respinto per il suo contenuto semantico.

I fatti ammessi sono: coppia presente tra le configurazioni mostrate nell'esempio
(compresi i pareggi espliciti), stesso dispositivo dell'esempio, stesso numero
di qubit dell'esempio, dispositivo con abbastanza qubit.
Sono controllati esclusivamente sui dati del prompt. La parola "best" nel primo
tipo indica le configurazioni riportate, non necessariamente il primo posto.

La prima risposta conforme con coppia ammessa e fatti corretti termina
l'episodio. Un fatto errato attiva una correzione. Al terzo tentativo, una
risposta ancora conforme con coppia ammessa viene accettata anche se i fatti
restano errati: status=success e accepted_with_unverified_facts=true.
Schema non conforme (anche zero o più di due fatti) o coppia non ammessa
rimangono un fallimento. Non si recupera una coppia precedente se l'ultima
risposta ha una coppia non ammessa. Successo della risposta non equivale
a compilazione completata: la valutazione riusa i tre seed Qiskit e lo distingue.

L'ipotesi può comunque contenere errori. facts_status non certifica l'ipotesi,
la rilevanza della motivazione né una relazione causale con la scelta.

## Interruzioni

I tentativi logici sono al massimo tre. Una chiamata interrotta viene spostata
in interrupted/attempt_N/<identificativo>/, con i suoi file originali.
Non consuma un tentativo; la ripresa ricrea attempt_N. Una risposta già
completa e salvata viene recuperata senza ripetere la generazione.

Le interruzioni per risorse recuperano automaticamente dopo tre campioni
favorevoli. Il limite hotspot è 110 °C, la pausa 105 °C e la ripresa 100 °C.
Il limite edge resta 95 °C; la RAM disponibile deve restare sopra 1 GiB.
Per ricaricare il server si attendono almeno 1 GiB, hotspot non superiore
a 100 °C e edge sotto 92 °C. Sono impostazioni operative richieste, non una
garanzia del produttore sulla scheda specifica.

Tre interruzioni di trasporto senza causa di risorse accertata sospendono
il supervisore, senza creare un fallimento del modello. Si riprende con
lo stesso comando. Gli errori applicativi non vengono ritentati all'infinito.
Un timeout reale senza interruzione delle risorse resta un timeout terminale.

Il contatore llm_calls comprende le chiamate fisiche, incluse quelle interrotte.
repair_count riguarda solo le correzioni. Token e tempi non misurabili
rimangono null; i valori osservati sono riportati separatamente.
Le pause brevi del processo mantengono la chiamata in corso; solo una
chiamata effettivamente interrotta deve essere rigenerata.

## Comandi

Eseguire da /home/elio/Tesi-mqt-2.4-v2 con il Python del progetto.
Ogni studio ha un identificativo esplicito. Non usare local-llm-v1, che è storico.

    .venv/bin/python -m llm_selection.v2 prepare --study local-llm-v2
    .venv/bin/python -m llm_selection.v2 train --study local-llm-v2
    .venv/bin/python -m llm_selection.v2 freeze --study local-llm-v2
    .venv/bin/python -m llm_selection.v2 verify --study local-llm-v2

Il train esegue 5 circuiti × 3 temperature × 3 modelli, con lo stesso budget
della validation. Controlla il funzionamento, non la generalizzazione:
nel train l'esempio del circuito stesso può essere recuperato.

Il comando seguente è riservato all'avvio esplicito dell'utente:

    .venv/bin/python -m llm_selection.v2 validate --study local-llm-v2

Esegue le 792 combinazioni della validation, sigilla i risultati, calcola
l'analisi e produce il rapporto LaTeX/PDF. Lo stesso comando riprende una
esecuzione interrotta; non cambiare l'identificativo dello studio.
Ctrl+C ferma i processi posseduti dal supervisore; le risposte concluse restano.
Un file stop_requested.json nella radice dello studio richiede una pausa
fra i circuiti. Prima della ripresa rimuovere soltanto quel file, se creato
volontariamente. Non avviare contemporaneamente due supervisori.

Per rigenerare soltanto il rapporto delle prove train:

    .venv/bin/python -c "from llm_selection.v2.report import build_report; build_report('local-llm-v2', technical=True)"

Per rigenerare il rapporto dopo la validation:

    .venv/bin/python -m llm_selection.v2 report --study local-llm-v2

## Regret e scelta

La mediana di expected_fidelity richiede tutti i seed 0, 1 e 2 riusciti.
Il riferimento osservato è la migliore mediana disponibile per ciascun circuito.
Copre tutti gli 88 circuiti della validation esistente. Le 70 matrici incomplete
non diventano oracle completi; il regret esaustivo sui 18 casi resta aggiuntivo.
Uno score della coppia assente resta null, anche se esiste il riferimento.

La selezione privilegia: scelte valide e compilabili; regret osservato mediano
sui circuiti comuni; minor numero di correzioni; minor numero di chiamate fisiche;
tempi e token completi; ordine lessicografico. Non si penalizzano direttamente
i fatti errati come fallimenti della scelta dopo l'esaurimento delle correzioni.

Le decisioni sono sigillate prima di leggere la matrice di valutazione.
Prima del congelamento si conservano solo gli hash degli input di valutazione.
La nuova versione è una revisione adattiva dopo la prima validation: non è
una replica indipendente e non apre il test.

## Artefatti

preparation.json fotografa le impostazioni iniziali. Le revisioni effettuate
durante le prove train restano in development; frozen_study.json definisce
il contratto e i parametri effettivamente usati dalla nuova validation.

Tutto lo studio vive in llm_selection/studies/<study_id>/:
- preparation.json, profiles_to_freeze.json, frozen_study.json e provenance.json;
- prompts/train e prompts/validation: copie dei contesti canonici;
- technical/<modello>/<configurazione>/<circuito>: prove sul train;
- <modello>/<configurazione>/<circuito>: episodi della validation;
- attempt_N: prompt, codifica, richiesta, flusso, risposta, riepilogo,
  fact_validation.json e, quando necessario, repair_feedback.json;
- interrupted: chiamate annullate nel conteggio logico, conservate integralmente;
- controllers: attese, recuperi e cicli di caricamento;
- analysis: riferimento osservato, controlli dei fatti, CSV, selezione e impronte;
- final_configuration.json e selection_complete.json: scelta di questo studio;
- report: LaTeX, PDF, figure PNG/SVG, CSV e confronti appaiati;
- technical_report: rapporto separato delle prove train.

I file prompt.json conservano il contesto canonico originale, che può riportare
ancora il contratto precedente. Il messaggio effettivamente inviato al modello
e lo schema v4 sono in call/request.json; encoding.json ne registra revisione
e impronte. Per ricostruire la richiesta usare questi ultimi artefatti.

Pesi, eseguibili e registri nativi Windows rimangono condivisi e identificati
dai manifest. Non vengono sovrascritti risultati o vincitore di local-llm-v1.
La nuova configurazione finale è specifica dello studio; l'eventuale adozione
nel protocollo finale/test deve riferirsi esplicitamente a questo nuovo artefatto,
senza usare automaticamente la configurazione globale storica.

## Verifiche riproducibili

    .venv/bin/python -m unittest discover -s tests -p test_llm_selection_v2.py -v

I test coprono fatti e pareggi, vincoli 1–2, ipotesi non certificata, correzioni,
successo con fatti errati al terzo tentativo, coppia finale non ammessa,
recupero di risposta conclusa, ripetizione del medesimo tentativo dopo reset,
riferimento su matrice incompleta e isteresi delle risorse.

## Correzioni del solo rapporto dopo il train

I begin.json mantengono sempre le impronte del codice realmente usato.
Il congelamento ammette differenze limitate a report.py, plots.py e alle
sole funzioni di congelamento in study.py. Nel terzo caso confronta l'albero
sintattico del resto del modulo con la copia originale: inferenza, sigilli,
verifica degli input e analisi devono restare identici. Ogni differenza
ammessa viene elencata in technical_code_reviews. Dopo il congelamento,
anche il codice del rapporto è vincolato dalle impronte dello studio.

## Rapporto esplicativo del 20 settembre 2026

Dopo la validation di local-llm-v2 è disponibile report_explained/standalone.pdf
nella cartella dello studio. Chiarisce mediane, boxplot e denominatori e aggiunge
grafici dei tempi e dei token per modello e temperatura. Il rapporto originale
e il codice congelato restano conservati. Per rigenerare questa versione:

    .venv/bin/python -m scripts.report_local_validation_v2 --study local-llm-v2

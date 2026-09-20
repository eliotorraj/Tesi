# Riduzione del prompt — 18 settembre 2026

La revisione corrente è minimal-v3-20260918; il contratto di risposta è 3.0.0.
Qwen riceve feature complete, catalogo hardware/configurazioni e cinque esempi.
QASM, provenienza, hash e ripetizioni restano nei registri, fuori dal prompt.
La risposta richiede dispositivo, configurazione, claim libero e citazioni E1...E5.
Non è usato TOON.

## Conteggi finali

| Circuito train | Prima | Dopo | Riduzione |
| --- | ---: | ---: | ---: |
| dj_indep_tket_2 | 34318 | 11667 | 66.00% |
| ae_indep_qiskit_60 | 75193 | 11382 | 84.86% |
| portfoliovqe_indep_qiskit_6 | 36265 | 12692 | 65.00% |

Il rapporto definitivo è [native_counts_final/report.json](native_counts_final/report.json).
I conteggi preliminari restano in native_counts/. Non mescolare le due revisioni.
Misure con il tokenizer effettivo llama.cpp b10930 e il GGUF Qwen Q8_0.
Il formato nativo è ripreso dall'episodio archiviato, a parità di messaggio unico
e ragionamento disattivato. Per il primo riferimento coincide l'intera sequenza
degli ID dei token con quella conservata dal server. Gli altri due riferimenti
sono ricostruzioni v2. Le nuove richieste non sono state inviate al modello.

Il testo include lo schema leggibile. Lo schema separato usato come vincolo
di generazione non aggiunge token al prompt. I contributi delle sezioni sono
nel rapporto e non sono necessariamente additivi.

## Verifiche

- Suite completa: 236 test superati in tests_full_final.log.
- Dopo l'aggiunta dello schema alla provenienza: 21 test mirati superati
  in tests_targeted_after_provenance.log.
- Controlli di sintassi Python e delle differenze dei file pertinenti riusciti.
- Recupero reale verificato su tutti e tre i casi train, senza cambiare i dati.
  Le risposte di formato costruite dalle etichette passano il validatore.
  Dettagli in real_train_verification.json.
- La mappa è vincolata alla richiesta, al sorgente, al catalogo, alle feature,
  ai vincoli e al registro. Il compilatore resta protetto dalla validazione
  e dalla conferma.
- provenance.json conserva copia del codice e degli schemi, versioni,
  dipendenze, hardware e stato Git. I log RL e le modifiche preesistenti
  non appartengono a questo intervento.

## Esempi e limiti

[Nuovo prompt completo già formattato](native_counts_final/dj_indep_tket_2/after.txt).

[Risposta di esempio](response_example.json): costruita da una fonte storica,
non generata da Qwen. La sua origine è dichiarata in response_example_origin.txt.
Il modello non deve restituire metadati della richiesta né parametri Qiskit
già determinati dal config_id.

Le citazioni sono risolte a fonti effettivamente fornite; questo non certifica
semanticamente il claim e non dimostra uso causale degli esempi.
Nessuna misura nuova di qualità, latenza o memoria. Nessuna selezione sulla
validation, apertura del test, inferenza LLM o addestramento sperimentale.
Gli esempi train possono contenere lo stesso sorgente: non è generalizzazione.

## Tentativi conservati

I primi controlli fallivano perché alcuni test usavano ancora la risposta v2
e perché il confronto fra liste e tuple rendeva diversa la vista dopo il
salvataggio JSON. Le fixture storiche sono esplicite; il nuovo percorso ha
test propri. Tutti i log iniziali rimangono nella cartella.

Il server locale non era attivo: server_health.json e server_props.json
conservano gli esiti. Il conteggio è stato completato con il tokenizer locale,
senza avviare il modello.

Il primo avvio PowerShell dello script di conteggio richiedeva un criterio
di esecuzione valido per il solo processo. Una segnalazione nativa su stderr
era trattata come errore PowerShell; ora si usa il vero codice di uscita e si
conserva stderr. Infine un percorso UNC di 264 caratteri non era apribile dal
tokenizer: i file mancanti sono stati riprovati con il prefisso UNC esteso.
I log originali, retry_reason.json, tokenize_retry.json e i rapporti incompleti
rimangono separati dal rapporto finale. Il riepilogo ora richiede tutti i file
di conteggio prima di dichiarare il controllo completo.

graphify update . ha tentato di analizzare oltre 118 mila file senza API ed è
stato interrotto. L'aggiornamento successivo usa solo i sorgenti modificati;
lo scope è conservato in graphify_incremental_scope.json. Le copie storiche
nel grafo non sono considerate codice attivo.

## Riproduzione

Usare una nuova cartella di destinazione. Dalla radice WSL:

    .venv/bin/python -m llm_selection.minimal_audit --reference-attempt PERCORSO_ATTEMPT --output NUOVA_CARTELLA

Da PowerShell eseguire llm_selection/tokenize_files.ps1 con -ManifestPath
impostato sul tokenize_manifest.json creato. Se necessario, usare una policy
per il solo processo; non modificare la configurazione globale di Windows.

Poi da WSL:

    .venv/bin/python -m llm_selection.minimal_audit --output NUOVA_CARTELLA --finish

Il controllo fallisce se mancano conteggi o se il riferimento nativo non
riproduce gli ID dei token originali. Non serve un server LLM attivo.

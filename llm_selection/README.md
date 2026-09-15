# Selezione locale LLM: guida per eseguire le prove

Questa procedura confronta tre famiglie e tre impostazioni sui medesimi
88 circuiti di validation. Registra ogni tentativo e prepara i dati della tesi.
Il riferimento scientifico resta [il protocollo](../docs/protocollo_sperimentale.md).

**Aggiornamento del 15 settembre 2026:** sono disponibili il [prompt compatto e i suoi controlli](PROMPT_COMPATTO.md),
il testo DJ da incollare in chat e le [istruzioni GitHub](GITHUB.md).
La nuova rappresentazione conserva tutti i cinque esempi RAG e il circuito completo.

**Stato alla consegna iniziale, 14 settembre 2026:** pesi e motore locale sono presenti;
la validation non è iniziata, lo studio non è congelato e non esiste un vincitore.
Le prove lunghe sono lasciate all'utente. I comandi di controllo non avviano modelli.
I controlli automatici del codice non dimostrano ancora che i tre modelli riescano
a completare questi prompt sull'hardware disponibile.

## 1. Aprire Ubuntu e controllare la preparazione

Usare il terminale Ubuntu/WSL. Tutti i comandi seguenti partono da questa cartella:

```bash
cd /home/elio/Tesi-mqt-2.4-v2
LLM_OUTPUT="$PWD/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection"
.venv/bin/python -m llm_selection.cli doctor
.venv/bin/python -m llm_selection.cli status
```

Il primo comando controlla la presenza dei file; non ricalcola le impronte dei
pesi e non certifica la sostenibilità dei prompt. Le impronte SHA-256 vengono
controllate prima del caricamento, direttamente da Windows sul percorso dei pesi,
per evitare di leggerli attraverso la cache WSL. Anche questa operazione può
richiedere minuti. La prova registra metodo, impronta, dimensione e durata.

Sono già conservati BF16 e Q8_0 per Qwen3.5-4B, Phi-4-mini-instruct e Gemma 4
E4B-it. Il collegamento `"$LLM_OUTPUT/models"` punta a:

```text
D:\Tesi-mqt\llm-selection\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\models
```

Le risposte restano nella cartella degli artefatti del progetto. I nuovi registri
scritti dal server e dal monitor Windows risiedono su D, sotto la cartella
`server_logs` accanto a `models`. Un collegamento per esecuzione mantiene il percorso
`servers/NOME-MODELLO` nel progetto. I vecchi registri non vengono spostati.
Questo evita le scritture con salvataggio forzato da Windows alla condivisione WSL.
Lo spazio del disco D: e il limite di RAM assegnato a WSL sono cose diverse.
Non cancellare checkpoint, pesi in quarantena o vecchi registri per fare spazio.
Controllare lo spazio, se necessario, con `df -h . /mnt/c /mnt/d`.

Il motore usa Windows, Vulkan e la RX 6750 XT da 12 GB. Il codice MQT continua
a usare `.venv` e le versioni di `uv.lock`. Un solo modello viene caricato alla volta.


## 2. Provare i profili hardware sul train

Ogni comando seguente esegue cinque circuiti train preparati per le prove tecniche.
Non legge gli score della validation. I nomi delle esecuzioni devono essere nuovi.

**I profili seguenti sono punti di partenza da verificare, non configurazioni
finali già validate.** Qwen BF16 ha già incontrato il limite operativo di RAM.
Per Phi si propone una prima prova con pesi BF16 e cache ridotta; se fallisce,
provare Q8_0 con un nome diverso. Gemma BF16 occupa circa 15 GB solo per i pesi:
la prova iniziale usa Q8_0. La qualità finale si sceglie soltanto con la validation.

Eseguire uno alla volta, attendendo la fine di ciascun comando:

```bash
.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label qwen-prova-01 \
  --precision Q8_0 --context 147456
```

```bash
.venv/bin/python -m llm_selection.controller --technical \
  --model phi --label phi-prova-01 \
  --precision BF16 --context 114688 --cache-type q4_0
```

```bash
.venv/bin/python -m llm_selection.controller --technical \
  --model gemma --label gemma-prova-01 \
  --precision Q8_0 --context 131072 --cache-type q4_0
```

`--precision` riguarda i pesi. `--cache-type` riguarda la memoria delle sequenze
già elaborate; sono due scelte diverse. Una cache Q4 non significa pesi Q4.
Il parametro `--gpu-layers` permette di provare un numero minore di livelli sulla
GPU, ma aumenta il lavoro sulla CPU e può aumentare la RAM necessaria.
Non cambiare questi parametri dopo il congelamento.

Il limite predefinito è 3600 secondi per chiamata, incluse le pause del processo.
Le prove tecniche possono usare `--technical-timeout`, ma un timeout tecnico
diverso non cambia automaticamente quello della validation.
`--circuit dj_indep_tket_2` permette una singola prova iniziale; da sola non basta
per congelare lo studio. Per il profilo scelto vanno completati tutti e cinque
i casi tecnici, con almeno una risposta valida. Anche i fallimenti devono restare.

Durante il comando viene mostrata una riga di avanzamento ogni circa 30 secondi.
`prompt processing` indica la lettura del prompt prima della produzione della
risposta. `progress = 0.19` significa il 19% di quel prompt, non il 19% delle
cinque prove. Il numero di token non è un numero di parole. La velocità indicata
è la media della fase fino a quel momento. Il supervisore ripete l’ultima riga
se il server non ne ha prodotta una nuova, anche durante le pause termiche.
Per esaminare gli esiti, da un secondo terminale nella stessa cartella:

```bash
.venv/bin/python -m llm_selection.cli technical-summary
.venv/bin/python -m llm_selection.cli status
```

Il riepilogo include esiti, chiamate e arresti registrati. I dettagli sono in
`controllers/NOME/`, `servers/NOME-MODELLO/` e `technical_episodes/NOME/`.
Se il server si arresta, i casi ancora da elaborare restano in attesa.
Un caso già concluso non viene ripetuto sotto lo stesso identificativo.

Se compare un arresto per RAM, il supervisore mostra la memoria libera misurata,
la soglia e il percorso del registro. Chiudere i programmi non necessari prima
della nuova prova. Il 14 settembre `qwen-prova-01` è stato fermato con 1,02 GiB liberi,
sotto il limite di 1,5 GiB, prima di qualsiasi generazione. Il processo Python
aveva raggiunto un picco di circa 1,67 GiB. La temperatura hotspot era 52 °C.
Questi dati sono un problema di sostenibilità della prova, non un giudizio sulla
qualità della risposta del modello. Il tentativo resta conservato.

Se un profilo tecnico fallisce, si può cambiare precisione/cache e usare un
nome nuovo, ad esempio `phi-prova-02`. Conservare e motivare entrambe le prove.
Per riprendere invece lo stesso profilo dopo una pausa, usare `--episode-label`,
come spiegato nel punto 6.

La connettività completa è rappresentata con una regola esatta e reversibile:
il contenuto del circuito e delle evidenze non viene tagliato. I conteggi
esplorativi sono in `preparation/complete_graph_token_probe.json`. Alcuni prompt
di Gemma superano comunque il contesto nativo: saranno fallimenti di contesto,
con zero chiamate di generazione. Il controllo usa il formato di chat effettivo
e riserva anche lo spazio per l'uscita.

Gemma E2B resta un'alternativa da valutare se E4B non è sostenibile, ma non è
installata né selezionata automaticamente da questa procedura. In quel caso
il catalogo sperimentale va aggiornato e documentato prima del congelamento.

## 3. Fissare i profili prima di leggere gli score

Quando le tre prove tecniche sono concluse, inserire i nomi realmente scelti:

```bash
.venv/bin/python -m llm_selection.cli profiles \
  --qwen qwen-prova-01 --phi phi-prova-01 --gemma gemma-prova-01 \
  --output "$LLM_OUTPUT/profiles_to_freeze.json"
```

Controllare `profiles_to_freeze.json`. Il campo `precision_reason` va completato
con la motivazione concreta: precisioni provate, consumo di memoria, eventuali
arresti e motivo della scelta. Gli altri campi devono corrispondere ai registri
delle prove. Il file non viene sovrascritto se esiste già.

Il congelamento controlla i cinque casi tecnici per ogni famiglia, la presenza
di una risposta valida, gli 88 prompt e le impronte dei pesi. Non accetta uno
studio già congelato o decisioni di validation raccolte prima del congelamento.

```bash
.venv/bin/python -m llm_selection.study freeze \
  --id local-llm-v1 --profiles "$LLM_OUTPUT/profiles_to_freeze.json"
```

Da questo momento non modificare codice, prompt, catalogo, indice RAG, parametri
o dipendenze MQT. I controlli rilevano le modifiche e bloccano la prosecuzione.
Il congelamento è intenzionalmente vincolante: non cancellarlo per rilanciare
una selezione dopo averne visto gli score.

La griglia comune è:

| Identificativo | Istruzioni | Temperatura |
| --- | --- | ---: |
| p0_t0 | Prompt base | 0 |
| p0_t07 | Stesso prompt base | 0,7 |
| p1_t0 | Controlli espliciti aggiuntivi | 0 |

Restano comuni: cinque esempi RAG, uscita massima 4096 token (valore presente
alla ripresa del 15 settembre; 2048 nelle prime prove), timeout 3600 s,
al massimo tre chiamate, top_p 0,95, top_k 40, min_p 0 e seed 20260913.
Il ragionamento esteso è disabilitato. Tutti gli altri valori sono nel file
congelato. Contesto, precisione e memoria vengono invece documentati per modello.

## 4. Avviare l'intera validation

```bash
.venv/bin/python -m llm_selection.controller --label validation-avvio-01
```

Sono 792 episodi: 3 modelli × 3 configurazioni × 88 circuiti.
Ogni episodio ha al massimo tre chiamate. La prima risposta valida è definitiva;
le altre chiamate servono solo a correggere risposte non conformi.
I problemi di trasporto non causano ripetizioni automatiche.

Il supervisore esegue i modelli in sequenza. Al termine sigilla tutte le decisioni,
legge la matrice Qiskit già disponibile, calcola le metriche, fissa il vincitore
locale e genera relazione e figure. Se una fase fallisce, i dati precedenti restano.

Il primo criterio è il numero di scelte valide e compilabili sugli 88 casi.
A parità si sceglie il regret assoluto mediano più basso sullo stesso insieme di
circuiti confrontabili. Seguono JSON valido alla prima chiamata, numero di
chiamate, tempi e token misurati. Le misure mancanti non diventano zero.
Se tutti falliscono non viene inventato un vincitore.

Questo comando può durare molte ore o giorni: non è disponibile una stima
affidabile prima delle prove tecniche complete. Le pause per temperatura
contribuiscono alla durata. Non serve tenere una conversazione AI in attesa.

## 5. Controllare, mettere in pausa e riprendere

Da un secondo terminale Ubuntu nella cartella del progetto:

```bash
.venv/bin/python -m llm_selection.cli status
.venv/bin/python -m llm_selection.cli stop
```

`stop` completa il circuito in corso, comprese le sue configurazioni e correzioni,
poi chiude il server. Può quindi non essere immediato. Aspettare che `status`
mostri `active_processes: []` e che il comando principale restituisca il prompt.

Per riprendere la validation:

```bash
.venv/bin/python -m llm_selection.cli clear-stop
.venv/bin/python -m llm_selection.controller --label validation-ripresa-01
```

Usare un nuovo nome per ogni avvio del supervisore. Lo studio resta lo stesso.
I modelli già sigillati e gli episodi conclusi vengono saltati.

Per riprendere le prove tecniche dello stesso profilo:

```bash
.venv/bin/python -m llm_selection.cli clear-stop
.venv/bin/python -m llm_selection.controller --technical \
  --model qwen --label qwen-ripresa-01 --episode-label qwen-prova-01 \
  --precision Q8_0 --context 147456
```

Mantenere tutti i parametri hardware originali. La ripresa riempie i casi mancanti;
non ripete quelli già conclusi. Se si cambia profilo, iniziare invece una nuova
prova tecnica senza `--episode-label`.

`Ctrl+C` interrompe subito il supervisore e richiede l'arresto del server.
Una chiamata senza esito certo resta un'interruzione documentata e non viene
rilanciata di nascosto. Se la risposta completa era già salvata, viene recuperata
e validata. Dopo uno spegnimento riprendere con un nome nuovo: non eliminare file
incompleti. I controlli di provenienza possono richiedere un esame degli artefatti
se una scrittura è stata danneggiata.

Il monitor sospende solo il processo di inferenza quando l'hotspot GPU raggiunge
80 °C e lo riprende sotto 65 °C. Arresta la prova a 95 °C di hotspot, 85 °C del
sensore edge o RAM libera sotto 1,5 GiB per tre campioni consecutivi.
Il campionamento è circa una volta al secondo. Questi limiti sono operativi:
non sono una diagnosi dello spegnimento né garantiscono di impedirne ogni causa.
Non vengono modificati tensioni, frequenze o ventole.

## 6. Rilanciare soltanto le analisi

Se i tre modelli sono conclusi ma manca l'analisi, ad esempio dopo un errore
di installazione del compilatore LaTeX:

```bash
.venv/bin/python -m llm_selection.study seal
.venv/bin/python -m llm_selection.cli analyze
```

Il sigillo fallisce se mancano decisioni o se gli artefatti sono cambiati.
`analyze` riusa i dati e non richiama i modelli. I JSON analitici sono immutabili:
se una nuova analisi produce numeri diversi, viene rifiutata.

Per rigenerare solo la relazione e le figure dopo una selezione conclusa:

```bash
.venv/bin/python -m llm_selection.report
```

`--sources-only` evita la compilazione PDF, ma richiede comunque i pacchetti
dei grafici. La relazione non viene prodotta con numeri fittizi prima delle prove.

## 7. Dove trovare i dati della tesi

Tutti i percorsi seguenti sono relativi a `"$LLM_OUTPUT"`.

| Percorso | Contenuto |
| --- | --- |
| models/ | Pesi, provenienza, revisioni, precisione, impronte |
| preparation/, technical/, incidents/ | Preparazione, prove iniziali e interruzioni storiche |
| technical_episodes/ | Prove train, comprese quelle scartate |
| controllers/, servers/ | Comandi, tempi di avvio, memoria, temperature, pause e arresti |
| code_snapshots/ | Copie del codice usato nelle diverse esecuzioni |
| frozen_study.json | Regole, parametri e impronte fissate prima degli score |
| studies/ID/MODELLO/CONFIG/CIRCUITO/ | Input, evidenze, tentativi, risposta e decisione |
| studies/ID/analysis/episodes.csv | Una riga per episodio, incluse le mancate riuscite |
| studies/ID/analysis/trials.csv | Riepilogo delle nove combinazioni |
| studies/ID/analysis/selection.json | Criteri applicati, denominatori e scelta |
| report/groups.csv | Risultati per famiglia di circuito e numero di qubit |
| report/technical_episodes.csv, report/server_runs.csv | Prove tecniche, configurazioni scartate e arresti |
| report/paired_uncertainty.json | Confronti appaiati e intervalli descrittivi |
| report/figures/ | Grafici PNG e SVG rigenerabili |
| report/validation_selection.tex | Sorgente inseribile nella tesi |
| report/standalone.tex, report/standalone.pdf | Documento autonomo di verifica |
| report/preview/ | Immagini delle pagine da controllare visivamente |
| final_configuration.json | Configurazione locale scelta |
| selection_complete.json | Prova verificabile della selezione conclusa |

I registri originali JSON/JSONL conservano prompt e risposte complete, evidenze,
errori, numero di chiamate, correzioni, token, tempi, risorse e provenienza.
I campi mancanti restano `null` o vuoti nei CSV. I massimi di memoria sono
campionati; il massimo Python è cumulativo del processo, non esclusivo della
singola chiamata. I tempi Qiskit storici sono indicati come riutilizzati.
Il consumo energetico dell'intero PC non viene dedotto dal solo sensore ASIC.


La selezione aggiorna solo i ruoli locali con e senza RAG. Non configura il modello
di frontiera, non esegue qcompile sulla validation e non apre il test.
L'ablazione senza RAG e il confronto finale rimangono fasi successive del protocollo.

## Verifiche della consegna

Il 14 settembre 2026 sono passati 21 test sintetici di `test_llm_selection.py`
e quattro test mirati del protocollo: matrice Qiskit, timeout qcompile,
configurazione LLM non definita e limiti di generazione. Sono stati controllati
anche la sintassi Python, i cinque script PowerShell e `git diff --check`.
Il test del resoconto genera sorgenti in una cartella temporanea con dati sintetici;
non compila PDF e non esegue i grafici. Nessun circuito del test reale è stato
usato per questi controlli. La sostenibilità delle prove lunghe e l'aspetto del
PDF finale restano da verificare attraverso le esecuzioni dell'utente.

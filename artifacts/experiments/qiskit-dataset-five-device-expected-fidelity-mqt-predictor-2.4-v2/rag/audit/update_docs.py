from pathlib import Path

def edit(path, changes):
    p=Path(path); s=p.read_text()
    for old,new in changes:
        assert old in s, (path,old[:80])
        s=s.replace(old,new,1)
    p.write_text(s)

section = """La raccolta usa **Qdrant locale persistente 1.19.0**, tramite il client
ufficiale. Non richiede un server, un account cloud o un modello di embedding.
Il solo ingresso è il JSONL globale train. Qdrant ne conserva una copia derivata,
ricostruibile: non è un secondo Dataset operativo.

Per ogni esempio vengono memorizzati un UUID deterministico, le 49 feature
trasformate, l'identificativo RAG, l'esperimento, lo split, il dispositivo
vincente e il record originale con provenienza ed evidenze. Dispositivo,
configurazioni, score, testo e altre etichette non entrano nel vettore.
Prima dell'inserimento si verificano schema, hash train, unicità per hash
sorgente, identità, Target, feature ed evidenze. Gli esempi devono coincidere
con quelli ricostruiti in memoria dagli aggregati train. La preparazione
ricalcola inoltre le feature dai circuiti train, senza compilarli.

### Trasformazione e distanza

La versione del recupero è `circuit49-log1p-train-maxabs-manhattan/1`.
L'ordine esplicito delle 49 coordinate è in
`prototype/quantum_assistant/adapters/rag_features.py` e in
`rag/index/transform.json`. Non dipende dall'ordine delle chiavi JSON.

Per una coordinata `i`:

```text
t_i(x) = log1p(x_i)   per gate_count_*, depth e num_qubits
t_i(x) = x_i          per gli altri cinque indicatori
d_i    = max assoluto di t_i nei soli 396 esempi train; se zero, vale 1
z_i(x) = t_i(x) / d_i
D(q,c) = somma_i abs(z_i(q) - z_i(c))
```

Si usa `Distance.MANHATTAN`: una distanza minore indica maggiore vicinanza.
Non si centra, non si tagliano i valori e non si normalizza la lunghezza del
vettore. Un ingresso oltre il massimo train può quindi superare 1.
I divisori si stimano solo sui 396 esempi train e restano identici per
validation, test e richieste successive. Valori mancanti, inattesi, non finiti,
conteggi negativi o frazionari e indicatori fuori [0, 1] vengono rifiutati.
Il numero di qubit deve essere almeno 1.

Il logaritmo riduce la prevalenza dei conteggi molto grandi. La divisione
rende confrontabili le scale delle coordinate sul train. È una scelta
progettuale, non un risultato dei paper MQT né una prova che questi vicini
portino alle raccomandazioni migliori. Le molte coordinate dei gate possono
avere un peso complessivo maggiore dei cinque indicatori. Le correlazioni
tra feature e la distribuzione sbilanciata dei vincitori restano limiti.

Questa formula **sostituisce** la precedente media di
`abs(q_i-c_i)/(1+max(abs(q_i),abs(c_i)))`. Le due formule non sono equivalenti.
La precedente scala dipendeva dalla coppia confrontata; ora la scala è fissa
e stimata sul train. Non esiste un ripiego automatico alla vecchia formula.

### Ricerca esatta, filtri e parità

I filtri per esperimento, train, obiettivo e dispositivo vincente ammesso
dalla maschera sono passati alla ricerca Qdrant. La scelta dei primi `k`
avviene dopo questi filtri. Il valore predefinito è **5 esempi**; le **3
configurazioni** del vincitore sono invece dati interni a ciascun esempio.

La modalità locale esegue una ricerca esaustiva. Non usa HNSW e non accelera
i filtri con indici dei dati associati. Il parametro `exact=True` non aggiunge
effetti in questa modalità, che è già esatta. Queste proprietà sono confermate
dal [codice ufficiale del client 1.19.0](https://github.com/qdrant/qdrant-client/blob/v1.19.0/qdrant_client/local/qdrant_local.py)
e dalla [documentazione della modalità locale](https://pypi.org/project/qdrant-client/1.19.0/).

Qdrant conserva vettori a precisione float32. Per questo piccolo Dataset
si recuperano tutti i candidati filtrati e si controllano tutte le distanze
contro la formula float64. La tolleranza segue `math.isclose`:
errore assoluto 1e-5 oppure relativo 1e-6. Uno scarto superiore è un errore.
Il risultato viene ordinato per distanza canonica float64 e poi per
identificativo RAG originale. La tolleranza non raggruppa le quasi-parità.
Questo passaggio gestisce anche le parità sul confine dei primi `k`.
Il costo è una seconda scansione dei candidati: non rivendichiamo un aumento
di velocità rispetto al riferimento locale.

Zero candidati compatibili è ammesso e produce un registro vuoto. Una raccolta
assente, incompleta, incompatibile o alterata ferma invece il flusso.
Un blocco o guasto del database produce un errore distinto e non attiva
automaticamente un altro recupero.

### Artefatti, comandi e sincronizzazione

Tutti gli artefatti sono sotto
`artifacts/experiments/<identificativo>/rag/`:

- `index/qdrant/`: database persistente;
- `index/transform.json`: ordine, trasformazioni, divisori e impronta;
- `index/manifest.json`: fonte JSONL, provenienza train, impronta dei punti,
  metrica, dimensione, numero di punti, versioni software e impronta di uv.lock;
- `verification.json`: verifica della raccolta;
- `validation_check.json`: prova tecnica sugli 88 circuiti validation;
- `audit/`: registrazioni delle verifiche e del confronto con i file iniziali.

Dalla radice, dentro WSL o Ubuntu:

```bash
.venv/bin/python scripts/17_rag_v2.py prepare
.venv/bin/python scripts/17_rag_v2.py verify
.venv/bin/python scripts/17_rag_v2.py validation
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO_CIRCUITO.qasm --k 5
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO_CIRCUITO.qasm --k 5 --backend reference
```

`query` prepara il prompt e le evidenze senza chiamare un LLM. Si può
aggiungere `--devices ibm_falcon_127` per provare una maschera ristretta.
Queste prove rifiutano i circuiti test noti prima del parsing.
`validation` legge solo i sorgenti validation: non usa i loro score o vincitori.
Controlla parsing, maschera, recupero, registro, prompt e confronto indipendente
delle distanze. Non misura la qualità delle raccomandazioni LLM.

`prepare` crea l'indice in una cartella temporanea, lo verifica, lo riapre e
solo allora lo rende disponibile. Se l'indice esiste già, lo verifica senza
riscriverlo: la ripetizione non aggiunge punti. Se non coincide con la fonte
o con la trasformazione, il comando fallisce. Per ricostruirlo deliberatamente,
chiudere i processi che lo usano, conservare la vecchia cartella `rag/index/`
con un altro nome e rieseguire `prepare`. Le cartelle temporanee lasciate da
una preparazione fallita servono alla diagnosi e non vengono usate dal servizio.
Non ricostruire un indice già congelato per il test.

Sull'altro computer usare lo stesso codice, uv.lock e versione Python indicata
nel manifest. Per aggiungere le dipendenze senza ricreare l'ambiente:
`uv sync --frozen --inexact --python 3.12`. Sincronizzare il Dataset corrente
completo, il manifest sorgente e gli artefatti necessari alle verifiche.
È preferibile ricostruire Qdrant dal JSONL con `prepare`, poi confrontare
manifest e trasformazione e lanciare `verify`. In alternativa copiare
`rag/index/` per intero a database chiuso. Non unire file SQLite di due copie
e non aprire contemporaneamente la stessa cartella da più processi.
La modalità locale consente un solo client aperto su quella cartella.

Il recupero locale `reference` usa il JSONL e la stessa trasformazione
verificata, senza interrogare il database. Si seleziona esplicitamente con
`retrieval_backend="reference"` nella factory. Il valore predefinito è
`"qdrant"`; `"none"` serve alla variante senza RAG. Un nome sconosciuto fallisce.
Il vecchio nome `JsonDatasetContextRetriever` ora indica il riferimento v2:
non accetta più JSON storici senza provenienza train.
"""

edit("docs/protocollo_sperimentale.md", [
("Qdrant non è ancora integrato. La distanza tra vettori resta la similarità\ncorrente. Un confronto con un'altra euristica è un possibile lavoro successivo,\nnon un requisito per iniziare l'integrazione.",
 "Qdrant locale persistente è integrato nella factory del prototipo. Usa ricerca\nesatta Manhattan sulle 49 feature trasformate con divisori stimati solo sul train.\nIl riferimento locale esplicito usa la stessa nuova formula."),
("Solo `global/rag_examples.jsonl` del Dataset attuale alimenterà Qdrant.",
 "Solo `global/rag_examples.jsonl` del Dataset attuale alimenta Qdrant."),
("La similarità resta basata sulla distanza tra vettori. La trasformazione delle\nfeature, la normalizzazione, la distanza concreta e `k` vanno registrati e\ncongelati sulla validation insieme ai parametri dell’indice. Un’altra euristica\npotrà essere confrontata in seguito. Qdrant non è ancora integrato.", section.strip()),
("modelli, trasformazioni delle feature e parametri del recupero si scelgono sulla\nvalidation e si congelano prima del test.",
 "modelli e parametri finali si verificano sulla validation e si congelano prima\ndel test. La trasformazione RAG qui definita stima i divisori solo sul train."),
("| tensorboard | 2.21.0 |", "| tensorboard | 2.21.0 |\n| qdrant-client | 1.19.0 |"),
("7. indice RAG composto soltanto da train;",
 "7. JSONL solo train e raccolta Qdrant effettiva completa, con vettori, dati\n   associati, impronte e divisori coerenti; verifica tecnica sugli 88 validation\n   riferita alla stessa raccolta e a `k=5`;"),
("Il record di apertura contiene le impronte dei file congelati. Se uno cambia,",
 "Il record di apertura include manifest, trasformazione, file persistenti Qdrant\n(escluso il blocco di accesso) e resoconto tecnico validation. Se uno cambia,")
])

edit("README.md", [
("| Esempi da indicizzare |", "| Esempi indicizzati |"),
("100 secondi e sei processi. La similarità resta la distanza tra vettori.\nQdrant e il collegamento a un LLM reale sono ancora da integrare.",
 "100 secondi e sei processi. Qdrant locale persistente è integrato: ricerca\nesatta Manhattan sulle 49 feature, con trasformazione log1p e divisori stimati\nsolo sui 396 esempi train. Il collegamento a un LLM reale resta da completare."),
(".venv/bin/python scripts/10_aggregate_qiskit_dataset.py --require-all-supported --check-only",
 ".venv/bin/python scripts/10_aggregate_qiskit_dataset.py --require-all-supported --check-only\n.venv/bin/python scripts/17_rag_v2.py prepare\n.venv/bin/python scripts/17_rag_v2.py verify\n.venv/bin/python scripts/17_rag_v2.py validation"),
("L’ambiente si prepara con", "Database e manifest del recupero sono in `artifacts/experiments/<identificativo>/rag/`.\n`scripts/17_rag_v2.py query --qasm PERCORSO.qasm --k 5` prepara prompt ed evidenze.\nAggiungere `--backend reference` per il riferimento esaustivo locale. Il protocollo\nspiega trasformazione, limiti, ripetizione dell'indicizzazione e sincronizzazione.\n\nL’ambiente si prepara con")
])

edit("prototype/README.md", [
("collegamento simulato. La similarità corrente usa la distanza tra vettori.\nRestano da integrare Qdrant e il collegamento a un LLM reale e da valutarne\nil risultato sulla validation.",
 "collegamento simulato. La factory usa Qdrant locale persistente e la nuova\ndistanza Manhattan. Restano il collegamento a un LLM reale e la valutazione\ndella qualità delle sue raccomandazioni sulla validation."),
("- `context.py` legge esempi JSON o JSONL dal Dataset, ordina quelli più vicini,\n  costruisce il registro immutabile e prepara il contenuto per il modello;",
 "- `context.py` costruisce il registro immutabile e prepara il contenuto per il modello;\n- `rag_features.py` definisce ordine, trasformazione train e Manhattan;\n- `rag_dataset.py` verifica l'unico JSONL ammesso, la provenienza e le evidenze;\n- `qdrant_context.py` prepara e verifica il database locale, cerca i vicini e offre\n  il riferimento esaustivo esplicito;\n- `rag_checks.py` prova gli 88 validation fino alla costruzione del prompt;"),
("La ricerca locale legge sia il formato JSON precedente sia gli esempi JSONL del\nDataset corrente. Gli esempi vengono filtrati in base alla misura e ai\ndispositivi rimasti nella maschera. Poi vengono ordinati con una distanza\nsemplice tra le caratteristiche numeriche dei circuiti.\n\nLa distanza tra vettori resta la misura adottata per la versione corrente.\nI suoi parametri saranno congelati sulla validation. Un confronto con un’altra\neuristica è un possibile lavoro successivo.",
 "La ricerca predefinita usa Qdrant locale persistente sul solo JSONL train v2.\nFiltra esperimento, obiettivo e dispositivo vincente ammesso dalla maschera\nprima di scegliere i primi `k`. Usa Manhattan sulle 49 feature: log1p per\nconteggi, profondità e qubit, identità per gli indicatori; ogni coordinata è\ndivisa per il massimo assoluto train, o per 1 se quel massimo è zero.\nNon applica centraggio, clipping o normalizzazione L2. I divisori non cambiano\ncon validation o richieste degli utenti.\n\nLe distanze Qdrant sono controllate contro la formula float64, con tolleranza\nassoluta 1e-5 o relativa 1e-6. Si recuperano tutti i candidati filtrati e si\nordinano per distanza canonica e identificativo RAG. Questo risolve anche\nle parità al confine di `k`. La modalità incorporata è esaustiva, senza HNSW\nné accelerazione tramite indici dei dati associati."),
("1. valutazione sulla validation della distanza tra vettori già scelta;\n2. integrazione del sistema RAG definitivo;\n3. collegamento al modello linguistico scelto;\n4. valutazione comune di qualità, errori, tempi e costi.",
 "1. collegamento e congelamento del modello linguistico scelto;\n2. valutazione delle raccomandazioni sulla validation;\n3. valutazione comune di qualità, errori, tempi e costi."),
("Manteniamo la distanza corrente sui vettori di 49 feature. Per ogni componente\nsi calcola `abs(q[i] - c[i]) / (1 + max(abs(q[i]), abs(c[i])))` e si fa la media.\nSi ordinano i risultati per distanza crescente, poi per identificativo del\nrecord in caso di parità. Il limite predefinito del recupero è 5 esempi.\nQuesto numero è distinto dalle tre configurazioni conservate per il device\nvincente. Un'altra euristica potrà essere confrontata in seguito. Qdrant dovrà\npreservare o versionare esplicitamente la regola di ordinamento: questa\nnormalizzazione dipende dalla coppia di vettori e non equivale direttamente\nalla distanza euclidea o coseno dei vettori grezzi.",
 "La successiva integrazione Qdrant sostituisce la vecchia media\n`abs(q[i]-c[i])/(1+max(abs(q[i]),abs(c[i])))` con la Manhattan descritta sopra.\nLe due formule non sono equivalenti e la vecchia non è un ripiego.\nIl limite predefinito resta 5 esempi, distinto dalle tre configurazioni\nconservate per il dispositivo vincente.")
])
p=Path("prototype/README.md")
p.write_text(p.read_text()+"""
## Uso del recupero Qdrant

Dalla radice del progetto:

```bash
.venv/bin/python scripts/17_rag_v2.py prepare
.venv/bin/python scripts/17_rag_v2.py verify
.venv/bin/python scripts/17_rag_v2.py validation
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO.qasm --k 5
.venv/bin/python scripts/17_rag_v2.py query --qasm PERCORSO.qasm --k 5 --backend reference
```

La factory `build_default_service` accetta `retrieval_backend="qdrant"`
(predefinito), `"reference"` o `"none"`. `retrieval_limit` cambia `k`.
`none` disattiva deliberatamente il recupero per la variante senza RAG.
Il parametro storico `dataset_required` resta accettato per compatibilità:
nel recupero attivo una fonte assente produce sempre errore.
Non si torna automaticamente al riferimento locale se Qdrant fallisce.

Il JSONL resta la fonte. Manifest, trasformazione e database sono sotto
`artifacts/experiments/<identificativo>/rag/index/`.
La ripetizione di `prepare` verifica una raccolta esistente senza aggiungere
punti. Una raccolta incoerente deve essere conservata e ricostruita
esplicitamente. Per trasferimenti tra computer e ricostruzione seguire la
sezione RAG del [protocollo unico](../docs/protocollo_sperimentale.md).

Il registro è costruito solo dai primi `k` risultati. Mantiene gli stessi
controlli sui riferimenti e resta immutabile tra i tentativi dell'LLM.
Zero esempi compatibili è un esito normale; errore del database e raccolta
alterata fermano il flusso. Le prove tecniche non misurano la qualità LLM.
""")
p=Path("knowledge/riassunto_kb_mqt_predictor.md")
s=p.read_text()
s=s.replace("> Il materiale precedente è in", "> Qdrant locale persistente 1.19.0 è ora integrato. Il recupero corrente usa\n> Manhattan sulle 49 feature, con log1p e divisori stimati solo sul train.\n> La vecchia distanza nei resoconti storici non descrive più il codice attuale.\n> Il materiale precedente è in",1)
s += """
## Integrazione Qdrant — 9 settembre 2026

Il recupero corrente usa solo i 396 esempi train del JSONL globale v2.
Il client ufficiale Qdrant 1.19.0 conserva una raccolta locale persistente
di 396 punti. Le 49 coordinate seguono un ordine esplicito. Conteggi, depth e
num_qubits usano log1p; i cinque indicatori restano invariati. Ogni coordinata
è divisa per il massimo assoluto osservato nel train, oppure per 1 se nullo.
I divisori non dipendono da validation, test o richieste successive.

Si usa la somma delle differenze assolute, senza centraggio, clipping o L2.
Questa scelta sostituisce la precedente distanza personalizzata: non è una
formula equivalente. Si filtrano prima esperimento, obiettivo e vincitore
compatibile con la maschera. I primi 5 esempi sono ordinati per Manhattan
float64 e identificativo RAG, dopo il controllo delle distanze Qdrant float32.
La modalità locale è esaustiva e non usa HNSW o indici accelerati sui filtri.

Gli artefatti sono in `artifacts/experiments/<identificativo>/rag/`.
Lo script `scripts/17_rag_v2.py` prepara, verifica e prova il recupero.
Il riferimento locale si sceglie esplicitamente con `--backend reference`.
Schema, provenienza train, sorgenti, feature, evidenze e raccolta vengono
controllati. Il JSONL resta l'unico Dataset operativo.

Sono prove di correttezza tecnica, non della qualità delle raccomandazioni.
Il test rimane sigillato; nessun nuovo training o popolamento Qiskit è stato
richiesto dall'integrazione. Regole complete e comandi sono nel protocollo unico.
"""
p.write_text(s)
print("Updated README, prototype README, protocol and current KB summary.")

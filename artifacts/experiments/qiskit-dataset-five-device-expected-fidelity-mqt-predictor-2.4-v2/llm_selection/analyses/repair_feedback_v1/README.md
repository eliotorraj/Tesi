# Correzioni compatte degli errori

Revisione: minimal-v3-repair1-20260918. Contratto di risposta: 3.0.0.

Dopo una risposta non valida, il programma reinvia il prompt ridotto completo.
Il campo previous_validation_errors contiene una frase per tipo di errore:
dispositivo, configurazione Qiskit o evidence. Gli errori dello stesso tipo
compaiono una sola volta. Una frase finale chiede di rispondere di nuovo con
l'intero JSON per il circuito corrente.

I messaggi indirizzano al catalogo hardware, al catalogo delle configurazioni
e agli ID degli esempi già presenti. Senza RAG viene richiesta evidence vuota.
Gli altri errori di formato ricevono un richiamo allo schema. Non si copiano
risposte errate, hash, cataloghi o esempi. Nei registri canonici rimangono i
codici e i dettagli degli errori.

Il primo tentativo, i cinque esempi, le feature, gli alias e il massimo di tre
chiamate restano invariati. La revisione è registrata fuori dal testo LLM.
Una nuova revisione richiede una nuova etichetta, anche se il primo prompt è
identico: non si mescolano correzioni diverse nello stesso episodio.

## Verifica

56 test superati: 13 sul prompt minimo, 28 sulla selezione LLM, 10 sul formato
compatto e 5 sull'architettura del prototipo. I log sono conservati qui.
I controlli includono errori reali del validatore, riferimenti inesistenti e
duplicati, più errori insieme, configurazioni incompatibili, assenza di RAG,
chat, prove tecniche, stabilità del contesto e protezione della compilazione.

Il confronto con il caso Phi fallito verifica che il testo del primo messaggio
è identico a quello archiviato. In phi_example/ si trovano:

- errore_aggiunto.txt: il solo messaggio di correzione.
- prompt_precedente.txt: il testo inviato nel secondo tentativo storico.
- prompt_corretto_non_inviato.txt: la nuova richiesta preparata con lo stesso contesto.
- prepared_request_not_sent.json: richiesta completa preparata.
- verification.json: provenienza e controlli.

Per riprodurre questo esempio dalla radice del progetto, con una cartella
phi_example non ancora presente, usare .venv/bin/python con il sorgente
prepare_phi_example.py (eseguito con -c o con la radice nel PYTHONPATH).
Lo script crea solo file, senza chiamare il modello.

Non sono state eseguite nuove inferenze, validation o valutazioni sul test.
Non è ancora misurata l'efficacia dei messaggi su Phi né il loro costo in token.
I risultati storici non vengono modificati o riclassificati.
Il primo avvio dello script di preparazione aveva un errore di escape delle
righe; è stato corretto. Entrambi i log rimangono disponibili.

La copia dei sorgenti prima/dopo e changes.diff delimitano questa modifica;
le altre modifiche già presenti nel progetto non sono incluse.
L'aggiornamento del grafo è limitato ai quattro sorgenti modificati:
lo scope e il log sono conservati separatamente.

# Circuiti di ingresso

`train/`, `validation/` e `test/` contengono rispettivamente 422, 88 e 90 file OpenQASM 2. Per un nuovo esperimento si possono sostituire prima di `prepara`, oppure indicare una nuova radice `corpus` nella configurazione. Ogni radice deve avere questi tre split con i QASM direttamente al loro interno.

Usare nomi univoci tra split. Il programma rifiuta sovrapposizioni byte-identiche o di istruzioni; questi controlli non provano indipendenza algoritmica. I 422 train hanno 396 contenuti distinti: gli alias restano nel manifest, senza aggiungere esempi RAG o campioni ML.

`manifest_originale.json` conserva la provenienza dei circuiti distribuiti: non va riscritto per quelli personali. Le copie della nuova esecuzione finiscono in `esecuzioni/<id>/circuits/`. I [QASMBench](esterni/qasmbench/README.md) sono ingressi opzionali separati. Una prova CPU limitata si esegue più facilmente con il Bell del prototipo; ridurre un corpus scientifico costituisce una nuova condizione, da dichiarare.

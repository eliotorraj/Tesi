# Strumenti della campagna QASMBench

`runner.py` avvia un solo metodo e registra gli esiti.
`worker.py` compila in un processo separato, con termine esterno di 100 secondi.
`gates.py` verifica dati, configurazione, versioni e Target e congela il contratto.
`mqt_gate.py` controlla selettore, politiche RL e provenienza dei modelli.
`common.py` gestisce percorsi e registri che non possono essere sovrascritti.
`score.py` calcola la stessa expected fidelity del progetto.

Le dipendenze riutilizzate sono il framework in `prototipo/` e i controlli degli
artefatti addestrati nell'archivio. Nessun modulo importa gli avviatori dei test precedenti.
Non sono inclusi modelli nuovi né vengono modificati i modelli installati.

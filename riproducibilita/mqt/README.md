# MQT: Target, politiche RL e selettore

`gestione.py` mostra i Target quantistici e verifica l'ambiente dedicato. `addestra_rl.py` addestra le politiche per dispositivo. `addestra_selettore.py`, `motore_ml.py` e `deduplica.py` raccolgono le compilazioni circuito/dispositivo, preparano il Training set e addestrano il classificatore. `validazione_selettore.py` controlla il selettore ottenuto.

L'ambiente è Python 3.12 con MQT Predictor 2.4.0 e il lock del kit. L'installazione non include politiche o classificatore. I comandi `esperimento.py mqt ...` e le prove Bell sono descritti nella [guida](../documentazione/guida.md). I modelli e le evidenze finiscono in `artefatti/<id>/`.

Questi lavori sono distinti dall'inferenza Qwen. Una GPU disponibile per llama.cpp non garantisce che PyTorch/MQT la usino. Valutare RAM, durata e numero di processi prima della raccolta. Non ricreare la `.venv` senza conservare sia i modelli canonici sia le copie installate nel pacchetto. Un addestramento breve è un controllo tecnico, non una misura di qualità.

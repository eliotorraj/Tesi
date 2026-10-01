# MQT: hardware, RL e selettore

`gestione.py` mostra i Target, protegge l’ambiente dedicato e verifica gli artefatti. `addestra_rl.py` addestra una politica per dispositivo; `addestra_selettore.py` coordina il ramo supervisionato. `motore_ml.py` raccoglie compilazioni e genera Training set, array e classificatore. `deduplica.py` seleziona un rappresentante per contenuto QASM; `validazione_selettore.py` controlla classi e modello.

Usare `esperimento.py mqt ...` secondo la [guida](../documentazione/guida.md). `artefatti/<id>/` contiene modelli, metadati, Training set, cache e registri. La sola installazione di MQT non fornisce i modelli addestrati.

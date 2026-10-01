# Messaggi e risposte del modello

Questa cartella prepara le informazioni inviate al modello e controlla la
sua proposta. L'ingresso usa TOON; la risposta usa JSON con contratto v4.
Il testo distingue fatti verificabili e ipotesi libera sulla scelta.

| File o cartella | Funzione |
| --- | --- |
| [minimal.py](minimal.py) | Ricava la vista essenziale dai dati completi e assegna agli esempi gli alias E1–E5. Conserva anche lo schema v3 usato dal documento intermedio. |
| [facts.py](facts.py) | Costruisce il messaggio corrente, applica lo schema v4 e verifica coppia e fatti dichiarati. |
| [toon.py](toon.py) | Organizza caratteristiche e collegamenti in TOON; controlla che la decodifica ricostruisca esattamente la vista iniziale. |
| [toon_runtime/](toon_runtime/README.md) | Contiene il collegamento all'encoder ufficiale e i file che ne fissano la versione. |

QASM, provenienza completa e registro delle evidenze restano nei dati locali.
Il modello riceve caratteristiche del circuito, hardware compatibile,
configurazioni ammesse e fino a cinque esempi train. I nomi dei dispositivi
restano leggibili; E1–E5 identificano soltanto gli esempi nella richiesta.

La revisione corrente è `facts-v4-toon3-20260919`. La gestione dei tentativi
successivi è in [app.py](../../app.py). L'ipotesi scritta in linguaggio
naturale non viene certificata dal verificatore.

La [guida](../../docs/guida_passo_passo.md) descrive l'installazione.
[Architettura e flusso](../../docs/architettura_e_flusso.md) spiega la
trasformazione dei dati, le regole dei fatti e l'accettazione dopo le correzioni.

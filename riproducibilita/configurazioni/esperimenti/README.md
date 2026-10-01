# Configurazioni con un nome

`configura.py nuovo NOME` crea qui una cartella per ogni esperimento. Il file `NOME/esperimento.json` è il punto d'ingresso corrente; `NOME/revisioni/` conserva catalogo, registro LLM, configurazione e descrizione del comando per ogni modifica. La pubblicazione del nuovo punto d'ingresso è atomica: una modifica rifiutata lascia attiva la configurazione precedente.

Il kit ritrova la configurazione con `esperimento.py --esperimento NOME ...`. I file contengono impostazioni e riferimenti agli ingressi, non pesi o risultati. I percorsi interni al kit sono relativi; ingressi o eseguibili esterni possono avere percorsi assoluti da adattare su un altro PC prima di preparare la prova. I file di blocco locali sono esclusi da Git; configurazioni e revisioni possono essere versionate e vanno conservate con i risultati.

Dopo la preparazione il configuratore impedisce modifiche, anche se gli output sono in un'altra radice. Per una nuova prova usa `duplica`, senza cancellare i contratti. Le configurazioni degli altri esperimenti non cambiano l'identità del codice di una campagna avviata; le modifiche ai sorgenti rimangono invece soggette ai controlli d'integrità.

Vedi il [ricettario](../../documentazione/configurazione.md) e usa `configura.py mostra NOME` per un riepilogo leggibile.

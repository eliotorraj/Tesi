# Sviluppo del 24 settembre 2026

Richiesta: prova completa MQT con il selettore disponibile, stessi criteri originali e risultati separati.
La copia iniziale dei moduli del Test e registrata in provenienza_codice.json.
Le differenze riguardano area dei risultati, selettore locale, controllo della provenienza effettiva e dichiarazione dei limiti nei rapporti.
Lo score e copiato senza modifiche. Il piano conserva tutte le impostazioni originali, salvo identita e descrizione delle deroghe.
Non e stato cambiato il comportamento delle due funzioni di MQT: predizione del dispositivo e compilazione RL.

Il vincolo delle cinque classi era errato: un dispositivo puo non vincere mai.
La correzione vale per addestramento, sincronizzazione e controllo operativo. Nessuna etichetta artificiale viene aggiunta.
Le classi devono coincidere con quelle osservate durante il fit, restare tra i dispositivi ammessi e produrre probabilita valide.
L'archivio congelato rimane invariato.

Per questa prova non servono 396 campioni o le dichiarazioni experiment_id, protocol, protocol_version e matches_frozen_protocol nel metadato ML.
Restano verifiche sulle versioni, sui Target, sul train e sul suo manifest, sulle etichette e su tutti i cinque RL.
Il selettore e identificato da SHA-256 nel piano; i suoi metadati originali rimangono intatti.

Cinque regressioni sintetiche riuscite: quattro classi, classe singola, classi invalide, larghezza delle caratteristiche e identita dei criteri/isolamento.
I controlli completi e le prove Bell conservano anche gli esiti sfavorevoli nelle cartelle della prova.

## Prima prova Bell

Tutti i sei casi sono falliti: AttributeError, str senza build_coupling_map.
Il worker originale convertiva il Target in nome prima di passarlo a rl_compile.
L'API installata richiede un Target. Nella sola prova separata si conserva ora
l'oggetto restituito dal selettore; per i cinque Bell RL si usa get_device.
La modifica corregge il tipo passato alla stessa funzione, senza cambiare criteri,
modello, azioni RL o timeout. Gli esiti precedenti restano conservati.
Il primo controllo completo era riuscito; le versioni e gli artefatti erano conformi.

## Verifiche della correzione

Sette regressioni sintetiche superate. Sono inclusi probabilita non finite o non normalizzate
e il controllo che sia passato un Target a rl_compile, sia dopo ML sia nelle prove forzate.
Il controllo completo degli artefatti e del corpus e riuscito.
L'aggiornamento del grafo e lasciato all'utente come richiesto; il tentativo e stato interrotto.

Seconda serie Bell: 6 successi su 6, inclusi ML+RL e i cinque RL. Gli esiti sono in prove_tecniche/mqt_predictor/45bf489f760a47cf8b23c5cb16307b3e/.

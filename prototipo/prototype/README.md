# Componenti del prototipo

Questa cartella contiene le regole e i componenti Python usati dal programma
[app.py](../app.py). Trasforma un circuito in una richiesta controllata,
recupera esempi dal Dataset train e verifica la proposta del modello.
La compilazione facoltativa è eseguita da Qiskit.

| Cartella | Funzione |
| --- | --- |
| [quantum_assistant/](quantum_assistant/README.md) | Strutture dati, lettura del circuito, vincoli hardware, recupero delle evidenze e compilazione. |
| [prompting/](prompting/README.md) | Preparazione del testo per il modello, codifica TOON e controllo della risposta v4. |

Il coordinamento delle fasi e il collegamento al server locale sono in
[app.py](../app.py), fuori da questa libreria. I dati distribuiti, i cataloghi
e gli schemi sono nelle cartelle sorelle `data/`, `configs/` e `schemas/`.
I moduli mantengono anche alcune strutture compatibili con le versioni
precedenti; il percorso effettivamente usato è quello descritto in
[architettura e flusso](../docs/architettura_e_flusso.md).

Per usare il programma partire dalla
[guida passo passo](../docs/guida_passo_passo.md).
Le cartelle `__pycache__/`, quando presenti, sono generate da Python.

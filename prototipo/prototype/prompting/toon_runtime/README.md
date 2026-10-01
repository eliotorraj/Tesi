# Encoder TOON

Questa cartella permette ai moduli Python di usare l'encoder ufficiale
`@toon-format/toon`, fissato alla versione **4.1.1**.

| Contenuto | Funzione |
| --- | --- |
| [codec.mjs](codec.mjs) | Riceve una richiesta JSON da Python e restituisce il testo TOON e i dati decodificati, oppure decodifica un testo TOON. |
| [package.json](package.json) e [package-lock.json](package-lock.json) | Fissano la dipendenza JavaScript e la sua installazione riproducibile. |
| [node-lock.json](node-lock.json) | Conserva versione e riferimenti del runtime Node usato per predisporre l'encoder. |
| `node_modules/` | Dipendenze installate localmente; non sono sorgenti da versionare. |

[toon.py](../toon.py) richiede Node.js 22 e confronta i dati prima e dopo la
codifica. Se i valori cambiano, la richiesta al modello viene fermata.
L'installazione si esegue con le procedure generali della
[guida](../../../docs/guida_passo_passo.md).

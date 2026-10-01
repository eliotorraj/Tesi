# Prompt, TOON e risposta facts v4

`minimal.py` costruisce la vista del circuito, dei Target e degli esempi train. `toon.py` la codifica tramite il codec ufficiale e controlla che la decodifica ricostruisca gli stessi dati. `facts.py` prepara le istruzioni, definisce lo schema v4 e verifica coppia e fatti dichiarati dal modello.

La risposta contiene dispositivo, configurazione, uno o due fatti e un'ipotesi libera. Il comando può chiedere fino a tre risposte complete. Al terzo tentativo una coppia strutturalmente valida e ammessa può essere accettata con fatti non verificati, registrandolo. L'ipotesi libera non riceve una certificazione semantica.

`toon_runtime/` richiede Node.js 22 e installazione npm dal lock. Lo prepara `setup.sh` su Linux. La stessa preparazione Python/TOON serve sia al percorso CPU sia al client del fisso: il server llama.cpp è separato. Per il dettaglio leggere [architettura e flusso](../../docs/architettura_e_flusso.md).

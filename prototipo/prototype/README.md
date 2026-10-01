# Moduli dell'assistente

`quantum_assistant/` contiene strutture dati e operazioni: lettura OpenQASM 2, 49 caratteristiche, maschera dei Target, recupero degli esempi, controllo della risposta e compilazione Qiskit. `prompting/` prepara il testo TOON e il contratto facts v4 realmente usato dal comando pubblico.

Il punto d'ingresso è `app.py` nella cartella superiore. Il server Qwen è un processo separato, avviato con `server.py` su Linux oppure con gli script PowerShell del fisso. L'hardware che esegue l'LLM non modifica i Target quantistici del catalogo.

Per navigare i collegamenti tra moduli leggere [architettura e flusso](../docs/architettura_e_flusso.md). Per avviare una prova leggere la [guida](../docs/guida_passo_passo.md).

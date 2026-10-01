# Componenti condivisi

`settings.py` risolve i percorsi e protegge i contratti; `corpus.py` congela gli ingressi; `processi.py` isola le compilazioni; `llm.py` gestisce modelli e registri; `relazioni.py` genera report; `esporta.py` produce il nuovo prototipo; `controlli.py` verifica l’installazione.

`framework/` è la copia riutilizzabile dei moduli dell’assistente, adattata al kit. `scripts/` conserva gli aiutanti MQT derivati dal progetto originale. `template_export/` contiene il supporto minimo per i prototipi generati. Non sono collegamenti al prototipo esistente e non importano codice dall’archivio.

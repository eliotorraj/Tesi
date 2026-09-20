# Struttura attuale del prototipo

Verificato sul codice di prototype/quantum_assistant/services.py, controller.py, factory.py e adapters/compilation.py, e sulle guide prototype/README.md e llm_selection/v2/README.md.

Il diagramma rappresenta il servizio applicativo Python. La validation sperimentale v2 ha regole distinte: al terzo tentativo può accettare una coppia ammessa con fatti non verificati. Il controllo Qiskit verifica operazioni e connettività, non equivalenza semantica o qualità della scelta. Gli errori di compilazione interrompono la restituzione.

Immagine prodotta con image_gen integrato il 20 settembre 2026. Riferimento visivo: immagine allegata dall'utente.

## Prompt

Create a high-resolution Italian architecture flowchart for a university thesis, landscape 3:2, crisp readable text, white background, flat outlined rectangular boxes and decision diamonds, orthogonal dark gray arrow connectors, generous spacing, professional restrained visual. Inspired by a traditional flowchart with navy user boxes, green input boxes, teal data boxes, red LLM boxes and ochre compilation boxes. No icons or decorative imagery. Title: "Struttura attuale del prototipo". Subtitle: "Assistente per la scelta del dispositivo e della configurazione Qiskit".

Organize as three broad columns, main flow down left, then down center, then down right. All text in Italian, use labels exactly below. Top column headings "1 · Richiesta e contesto", "2 · Proposta e controlli", "3 · Compilazione".

LEFT column top navy box "Utente / interfaccia Python" with small line "Circuito OpenQASM 2 + vincoli". Arrow downward to green box "Lettura e controllo della richiesta" small "Estrazione di 49 caratteristiche". Arrow down to green "Filtro di compatibilità" small "Dispositivi ammessi dai vincoli". A small adjacent green data box "Catalogo" / "5 dispositivi · 12 configurazioni Qiskit" feeds filter and also prompt logically (one neat connector optional). Small side exit from filter labelled "Nessun dispositivo" to terminal "Errore". Continue downward from filter to teal box "Recupero RAG · Qdrant locale" small "5 esempi train simili e compatibili" and "Distanza Manhattan". Teal cylinder at left bottom "Dataset RAG" / "Esempi di compilazioni Qiskit" / "Solo train" feeds RAG. Route RAG arrow into top center prompt box.

CENTER column top red outline box "Costruzione del prompt" small "Circuito, vincoli, alternative ammesse" and "Esempi e registro delle evidenze". Arrow down red box "LLM configurabile" small "Scelta: dispositivo + configurazione" / "Risposta JSON con riferimenti". Arrow down ochre diamond "Proposta valida?" with nearby tiny text "Formato, compatibilità, piano e riferimenti". A left loop from diamond labelled "No · correzione" returns to prompt; on loop show small note "Massimo 3 tentativi". A separate short exit labelled "Tentativi esauriti" to small terminal "Errore". Valid branch labelled "Sì" leads down teal box "Proposta conservata dal servizio" small "Spiegazione dai dati validati". Route this box to right column top decision.

RIGHT top ochre diamond "Conferma dell’utente?" no branch right to purple terminal "Fine"; yes branch down to ochre box "Compilazione Qiskit" small "Piano approvato · Target MQT Bench". Arrow down ochre box "Controllo del circuito compilato" small "Operazioni consentite e connettività". Arrow down navy box "Restituzione del risultato" small "OpenQASM 2, profondità, operazioni" / "Esito dei controlli".

Bottom separate pale gray strip, visibly separated from main flow, label "Confini del diagramma" and three short notes:
"Interfaccia Python disponibile; applicazione grafica completa ancora da realizzare."
"LLM sceglie dal catalogo; Qiskit compila. Non viene eseguito hardware quantistico reale."
"La validation sperimentale v2 è un percorso separato: fatti controllati e ipotesi libera, con registrazione dei tentativi."
Do not imply experiment v2 accepts unchecked facts in main prototype. No MQT Predictor as main compiler, no PDF document retrieval, no LLM training node. Keep all nodes distinct with no overlaps or crossing text. Ensure clear arrow direction and flow across column transitions. Diagram should be complete with margins and no clipping.

## Seconda versione
Su richiesta utente, image_gen ha rimosso la parola attuale dal titolo, indicata dalla maschera bianca, e ricentrato il titolo Struttura del prototipo. Il resto del diagramma è conservato. File: struttura_prototipo-v2.png. Prompt: rimuovere esclusivamente la parola attuale nella zona selezionata, mantenendo tutti i blocchi, le frecce, i testi e i colori.

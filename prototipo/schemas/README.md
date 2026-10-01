# Schemi dei dati

Questi file JSON descrivono la forma ammessa per richieste, catalogo hardware, risultato del filtro, esempi RAG e raccomandazioni. Permettono ai moduli di rifiutare dati incompleti o non conformi.

La risposta inviata da Qwen usa il contratto v4 in `llm_recommendation_v4.schema.json`. Gli schemi precedenti restano necessari ai componenti condivisi e ai controlli interni; la loro presenza non indica che siano il contratto LLM corrente. Il [documento tecnico](../docs/architettura_e_flusso.md) distingue i passaggi.

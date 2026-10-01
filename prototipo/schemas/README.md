# Contratti JSON

Gli schemi descrivono richieste, evidenze e risposte ammesse. Il comando pubblico usa `llm_recommendation_v4.schema.json` tramite `prototype/prompting/facts.py`; altri schemi sono necessari alle strutture intermedie del framework.

Un JSON sintatticamente valido non basta: si controllano anche appartenenza al catalogo, compatibilità del dispositivo e fatti rispetto al prompt. Le impronte dei contratti fanno parte dell'integrità del pacchetto. Per il significato dei controlli leggere [architettura e flusso](../docs/architettura_e_flusso.md).

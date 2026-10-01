# Impostazioni dell'esperimento

Il punto di ingresso consigliato è `configura.py`, dalla cartella `riproducibilita/`. Crea un esperimento con un nome e cambia le impostazioni tramite comandi controllati, senza editare schemi JSON:

```bash
python configura.py nuovo mia-prova --profilo cpu
python configura.py sistemi mia-prova llm_rag llm_senza_rag random
python configura.py dispositivi mia-prova ibm_falcon_27
python configura.py mostra mia-prova
```

[esperimenti/](esperimenti/README.md) conserva configurazioni nominate e revisioni. `esperimento.json` e `catalogo.json` qui alla radice restano i valori distribuiti, usati anche dall'interfaccia tradizionale. `generazione_llm.json` contiene prompt e parametri comuni di basso livello; modificarlo richiede una scelta avanzata prima delle campagne.

Il catalogo descrive Target quantistici, configurazioni Qiskit, seed e processi. CPU e GPU del PC si impostano invece con `risorse` e `modello`. I due profili `cpu` e `gpu` scelgono dove eseguire il LLM e partono dalle stesse altre impostazioni. Contesto, batch e processi si regolano separatamente; il fisso usa anch’esso `gpu`. La disponibilità e la memoria della scheda vanno verificate sul computer utilizzato.

Dopo `prepara` le modifiche sono bloccate; `configura.py duplica ORIGINE NUOVO_NOME` conserva le impostazioni e separa i nuovi risultati. Leggi il [ricettario](../documentazione/configurazione.md) per tutti i comandi e la [guida](../documentazione/guida.md) per la sequenza completa.

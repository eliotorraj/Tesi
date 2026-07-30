# Risultati del dataset LLM pilota

Artefatto:

```text
output/llm_dataset/mqt_pipeline_expected_fidelity_5seeds.json
```

Configurazione:

- MQT Predictor 2.3.0;
- figure of merit `expected_fidelity`;
- 8 circuiti target-independent del mini-training set locale;
- 5 seed per circuito;
- inferenza PPO stocastica, coerente con il comportamento di `qcompile`;
- massimo 100 azioni per trace;
- timeout di 120 secondi per compilazione;
- selector locale con candidati `ibm_falcon_127` e `quantinuum_h2_56`.

Risultati:

| Campo | Valore |
|---|---:|
| Record totali | 40 |
| Trace complete | 35 |
| Record con errore | 5 |
| Timeout | 0 |
| Sequenze di pass distinte tra i successi | 5 |
| Lunghezza minima trace riuscita | 11 |
| Lunghezza massima trace riuscita | 42 |
| Lunghezza media trace riuscita | 21,2 |
| Accordo predizione selector / label offline | 40/40 |

Tutti i cinque errori riguardano `mini_wide_pair_28`: la policy applica 100
azioni senza scegliere `terminate`. Questi record sono conservati come esempi
negativi con trace parziale completa.

L'accordo 40/40 tra selector e label offline è soltanto un controllo di
coerenza della pipeline. I circuiti appartengono allo stesso mini-dataset usato
per costruire il classificatore locale, quindi questo valore non misura la
generalizzazione del selector e non va riportato come accuratezza su test.

Le cinque sequenze distinte dipendono dai cinque seed e ricorrono su più
circuiti. Il dataset è quindi sufficiente per verificare schema, logging,
serializzazione e costruzione di esempi LLM, ma non è ancora sufficiente per
addestrare o valutare scientificamente un decisore LLM.

La successiva generazione dovrebbe:

1. usare molti più circuiti e famiglie;
2. separare manifest di training, validation e test per famiglia;
3. generare più trace per circuito e possibilmente da checkpoint PPO diversi;
4. conservare successi, fallimenti e timeout;
5. aggiungere una seconda figure of merit soltanto come esperimento separato;
6. non usare il futuro test LLM per costruire esempi o scegliere prompt.

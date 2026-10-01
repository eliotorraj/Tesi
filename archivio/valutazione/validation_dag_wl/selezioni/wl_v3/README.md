# Scelta finale: h = 24, k = 5

La scelta usa esclusivamente la validation wl_v3: 88 casi riusciti e osservabili
per tutti i 31 metodi. I registri originali sono intatti. Le medie sono state
ricalcolate dai singoli esiti e le impronte sono state verificate.

| Metodo | Score medio trasferito | Regret medio | Regret migliore fra le coppie mostrate | Confronto medio (s) |
| --- | ---: | ---: | ---: | ---: |
| Manhattan | 0.778026094945 | 0.013636827584 | 0.006446392755 | 0.008290 |
| h=23 | 0.784247390652 | 0.007415531877 | 0.000510713331 | 0.205737 |
| h=24 | 0.784251054082 | 0.007411868448 | 0.000556488563 | 0.215976 |
| h=25 | 0.784251054082 | 0.007411868448 | 0.000575471633 | 0.231291 |
| h=26 | 0.784251054082 | 0.007411868448 | 0.000575471633 | 0.240433 |
| h=27 | 0.784251054082 | 0.007411868448 | 0.000575471633 | 0.252565 |

Il criterio principale era il trasferimento della prima coppia del primo esempio:
copertura, regret medio sui casi comuni, mediana. Il miglior valore esatto si
raggiunge per h=24,25,26,27, con mediana zero. h=24 è il primo minimo e usa meno
iterazioni. Il criterio secondario sui cinque esempi favorisce anch'esso h=24
rispetto a h=25..27. I tempi riportati misurano solo il confronto delle
rappresentazioni, non la preparazione completa o l'inferenza LLM.

Fra h=24 e h=25..27 gli score coincidono su ciascuno degli 88 circuiti, ma gli
esempi non sono tutti uguali: l'insieme dei cinque cambia rispettivamente
in 8, 11 e 12 casi. Pertanto la parità dello score trasferito non dimostra
equivalenza delle risposte LLM.

h=23 è praticamente equivalente sul criterio principale: la differenza media è
appena 0.000003663430. La differenza viene solo da qftentangled_indep_tket_4:
0.9792348078 per h=23 contro 0.9795571896 per h=24.
h=23 costa leggermente meno e ha un indicatore secondario migliore.
La scelta h=24 segue il minimo esatto del criterio principale concordato;
non è un'affermazione di superiorità statistica rispetto a h=23.

Rispetto a Manhattan, h=24 migliora il trasferimento in 25 casi, pareggia in 57
e peggiora in 6. Il guadagno medio di score è 0.006224959136, cioè circa
0.6225 punti percentuali sulla scala 0..1.

Da h=28 il criterio principale peggiora soprattutto su qft_indep_qiskit_40
(0.3863090939 con h=24 contro 0.0101830323) e qftentangled_indep_qiskit_40
(0.3622062509 contro 0.0078495524). Questo non giustifica ulteriori aumenti
delle iterazioni sulla base dell'andamento osservato.

## Limiti

Questi sono score storici trasferiti, non score dell'LLM. Il migliore fra
le coppie mostrate è un indicatore ottimistico e non una scelta disponibile
al modello tramite gli score del circuito corrente. Le 70 matrici incomplete
rendono il riferimento un migliore osservato. La selezione è adattiva:
tre griglie sono state esaminate sugli stessi 88 validation.
Gli istogrammi conservati contengono ancora 0..30; la similarità selezionata
usa esclusivamente i contributi 0..24. La sintesi nel prompt non cambia.

## Configurazione e riproducibilità

wl_h24.json è il contratto congelato, verificato dal lettore usato da entrambi
gli avvii. I controlli preliminari di entrambi i Test hanno restituito
ready_for_test=true. Il server e il GGUF saranno verificati all'avvio delle
prove con inferenza. Nessun Test è stato avviato durante questa analisi.

Per ricalcolare l'analisi, dalla radice:

~~~bash
.venv/bin/python archivio/valutazione/validation_dag_wl/selezioni/wl_v3/analisi/genera_analisi.py
~~~

Il file analisi/analisi_scelta.json conserva tutti i metodi, le differenze per
circuito e le impronte del riepilogo, del contratto e del generatore.
Non modificare il codice sperimentale dopo il congelamento senza aprire una
nuova revisione documentata.

## Avvio dei due Test

Dal terminale WSL, con il server Qwen già avviato sul profilo desktop:

~~~bash
cd /home/elio/Tesi-mqt-2.4-v2
WL_CONFIG="archivio/valutazione/validation_dag_wl/selezioni/wl_v3/wl_h24.json"
WL_MODEL="/mnt/d/Tesi-mqt/llm-selection/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/models/qwen/Q8_0.gguf"

.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl.py \
  --esegui --config-wl "$WL_CONFIG" --model-path "$WL_MODEL" \
  --url http://127.0.0.1:8089

.venv/bin/python archivio/valutazione/test/llm_rag_dag_wl_sintesi.py \
  --esegui --config-wl "$WL_CONFIG" --model-path "$WL_MODEL" \
  --url http://127.0.0.1:8089
~~~

Eseguire uno alla volta. Per una prova preliminare su Bell sostituire
--esegui con --tecnico, senza cambiare gli altri argomenti.
I risultati restano separati in test/dag_wl_retrieval/ e test/dag_wl_sintesi/.
Il grafo graphify non è stato aggiornato.

# Catalogo delle scelte Qiskit

`qiskit_dataset_configurations_v2.json` definisce i cinque Target sintetici, le dodici configurazioni e le versioni controllate dal client. Il modello sceglie un `config_id`; il programma ne ricava i parametri, senza eseguire codice prodotto dall'LLM.

Il catalogo riguarda hardware quantistico sintetico, non la CPU/GPU che esegue Qwen. Per l'accelerazione locale leggere [installazione e runtime](../docs/installazione_e_runtime.md). Per cambiare lo spazio sperimentale usare [riproducibilita/configurazioni](../../riproducibilita/configurazioni/README.md), senza riscrivere le impronte del prototipo selezionato.

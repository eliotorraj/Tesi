# expected_fidelity

Questa cartella contiene i due scope del Dataset Qiskit diretto, separati per
device:

- `pilot/<device_id>`: 10 circuiti nel manifest, split 6/2/2;
- `full/<device_id>`: 600 circuiti nel manifest, split 422/88/90.

Ogni coppia circuito-device compatibile produce 36 tentativi. Falcon-27 compila
6 circuiti del pilot (216 tentativi), Quantinuum H2-56 ne compila 8 (288), i
tre device piu larghi tutti e 10 (360).

Ogni sottocartella pilot contiene anche `reports/pilot_report.md` e CSV
dettagliati. `pilot/device_comparison.md` confronta automaticamente tutti i
report disponibili, sia sull'insieme compatibile per device sia sul sottoinsieme
di circuiti comune.

I file direttamente sotto `pilot/` e `full/` sono lo snapshot storico
Falcon-127 precedente alla separazione e non vengono sovrascritti. La procedura
completa è in `docs/qiskit_dataset.md`.

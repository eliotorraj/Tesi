# Qiskit compilation cache

`expected_fidelity/runs/run_<fingerprint>.json` records individual attempts. `expected_fidelity/compiled_qasm/` holds compiled circuits for successful attempts. Attempt identity includes circuit, Target, configuration, seed and conditions.

Errors and terminal timeouts are outcomes, not missing jobs to repeat automatically. Dataset generation aggregates these records while keeping cached and newly executed measurements distinguishable, especially for timing.

[Parent directory](../README.md) · [Current repository guide](../../../../../../README.md)

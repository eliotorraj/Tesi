# Historical Dataset inputs and results

`expected_fidelity/pilot/` holds the reduced pilot and device reports. `expected_fidelity/full/` holds the original 600-circuit split manifest, QASM sources and earlier per-device results. CSV, JSON and JSONL files are generated measurements and summaries.

Repeated device/circuit subdirectories follow the same data layout; they are not separate applications. Preserve split membership and original source bytes when verifying later experiment provenance.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [expected_fidelity/](expected_fidelity/README.md) | Early expected-fidelity Dataset. |

[Parent directory](../README.md) · [Current repository guide](../../../../../README.md)

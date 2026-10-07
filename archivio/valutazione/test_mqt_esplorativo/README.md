# Separately contracted MQT evaluation

This directory preserves the 90-circuit MQT run using the available reduced-coverage selector. Its Training set contains 384 of 396 planned samples, with 12 excluded; collection combined 100-second successes and 300-second recovery attempts, yielding 1,853 successful circuit/device compilations out of 1,878.

`mqt_predictor.py` launches the method; `piano.json` records conditions and deviations. `strumenti/` contains the implementation and `verifiche/` its software checks. Test compilation uses a 100-second limit and one attempt per circuit. There are 90 recorded outcomes, including 75 successful compilations. The historical directory name is retained; interpret the comparison using its explicit conditions.

## Subdirectories

| Directory | Contents |
| --- | --- |
| [strumenti/](strumenti/README.md) | Utilities for the separate MQT run. |

[Parent directory](../README.md) · [Current repository guide](../../../README.md)

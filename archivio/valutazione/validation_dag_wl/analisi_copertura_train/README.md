# Train graph propagation coverage

`calcola_diametri.py` reconstructs the train graphs and measures component diameters. It covers 422 train records corresponding to 396 distinct QASM contents, checking hashes and graph reconstruction.

For propagation distance, the predecessor/successor graph can be treated as undirected; parallel edges do not change distance. The saved measurement finds maximum diameter 110, median 10 and minimum 5. At h=24, 360/396 unique graphs are fully covered; h=30 covers 375/396. These structural observations do not call the LLM, compile circuits or replace the validation-selected depth.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)

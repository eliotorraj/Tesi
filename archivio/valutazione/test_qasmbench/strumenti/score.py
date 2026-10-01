"""Expected fidelity di MQT Predictor 2.4.0; copia minima MIT, senza dipendenze RL.
Copyright (c) 2023-2026 Chair for Design Automation, TUM.
Copyright (c) 2025-2026 Munich Quantum Software Company GmbH.
Licenza: ../../LICENSE-MQT-Predictor. La prova verifica l'identita numerica.
"""
import math
import numpy as np

def expected_fidelity(circuit, target):
    product = 1.0
    log_score = 0.0
    for item in circuit.data:
        if item.operation.name == "barrier":
            continue
        indices = tuple(circuit.find_bit(q).index for q in item.qubits)
        if len(indices) not in (1, 2):
            raise ValueError("Numero di qubit non supportato dallo score MQT.")
        fidelity = 1 - target[item.operation.name][indices].error
        product *= fidelity
        log_score = log_score + math.log(fidelity) if fidelity > 0 else -math.inf
    score = float(np.round(product, 10).item())
    if not math.isfinite(score):
        raise ValueError("Score non finito.")
    return {"score": score, "log_score_unrounded": log_score if math.isfinite(log_score) else None,
            "rounded_to_zero": score == 0 and product > 0, "underflow": product == 0 and math.isfinite(log_score)}

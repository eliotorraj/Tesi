"""Expected fidelity from MQT Predictor 2.4.0; minimal MIT-licensed copy without RL dependencies.
Copyright (c) 2023-2026 Chair for Design Automation, TUM.
Copyright (c) 2025-2026 Munich Quantum Software Company GmbH.
License: ../../LICENSE-MQT-Predictor. The check verifies numerical identity.
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
            raise ValueError('Qubit count unsupported by the MQT score.')
        fidelity = 1 - target[item.operation.name][indices].error
        product *= fidelity
        log_score = log_score + math.log(fidelity) if fidelity > 0 else -math.inf
    score = float(np.round(product, 10).item())
    if not math.isfinite(score):
        raise ValueError('Non-finite score.')
    return {"score": score, "log_score_unrounded": log_score if math.isfinite(log_score) else None,
            "rounded_to_zero": score == 0 and product > 0, "underflow": product == 0 and math.isfinite(log_score)}

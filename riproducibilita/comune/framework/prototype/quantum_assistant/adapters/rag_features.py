"""Trasformazione train-only delle 49 feature e distanza Manhattan canonica."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from qiskit_dataset.experiment_v2 import stable_sha256

# Ordine fissato, indipendente dalle chiavi JSON e dalle future API MQT.
FEATURE_ORDER = (
    "gate_count_u3", "gate_count_u2", "gate_count_u1", "gate_count_cx",
    "gate_count_id", "gate_count_u0", "gate_count_u", "gate_count_p",
    "gate_count_x", "gate_count_y", "gate_count_z", "gate_count_h",
    "gate_count_s", "gate_count_sdg", "gate_count_t", "gate_count_tdg",
    "gate_count_rx", "gate_count_ry", "gate_count_rz", "gate_count_sx",
    "gate_count_sxdg", "gate_count_cz", "gate_count_cy", "gate_count_swap",
    "gate_count_ch", "gate_count_ccx", "gate_count_cswap", "gate_count_crx",
    "gate_count_cry", "gate_count_crz", "gate_count_cu1", "gate_count_cp",
    "gate_count_cu3", "gate_count_csx", "gate_count_cu", "gate_count_rxx",
    "gate_count_rzz", "gate_count_rccx", "gate_count_rc3x", "gate_count_c3x",
    "gate_count_c3sqrtx", "gate_count_c4x", "num_qubits", "depth",
    "program_communication", "critical_depth", "entanglement_ratio",
    "parallelism", "liveness",
)
TRANSFORM_VERSION = "circuit49-log1p-train-maxabs-manhattan/1"
LOG_FEATURES = frozenset(FEATURE_ORDER[:44])
SCORE_ABS_TOL = 1e-5
SCORE_REL_TOL = 1e-6


class RetrievalIntegrityError(ValueError):
    """Dati o raccolta incoerenti: non equivale a zero risultati."""

    code = "RAG_INTEGRITY_ERROR"
    retryable = False

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "retryable": self.retryable, "message": str(self)}


def transform_unscaled(features: Mapping[str, Any]) -> tuple[float, ...]:
    if not isinstance(features, Mapping) or set(features) != set(FEATURE_ORDER):
        missing = sorted(set(FEATURE_ORDER) - set(features)) if isinstance(features, Mapping) else list(FEATURE_ORDER)
        extra = sorted(set(features) - set(FEATURE_ORDER)) if isinstance(features, Mapping) else []
        raise RetrievalIntegrityError(f"Feature mancanti={missing}, inattese={extra}.")
    result = []
    for name in FEATURE_ORDER:
        raw = features[name]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise RetrievalIntegrityError(f"Feature {name}: numero atteso.")
        try:
            value = float(raw)
        except OverflowError as error:
            raise RetrievalIntegrityError(f"Feature {name}: valore troppo grande.") from error
        if not math.isfinite(value) or value < 0:
            raise RetrievalIntegrityError(f"Feature {name}: valore non finito o negativo.")
        if name in LOG_FEATURES:
            if not value.is_integer() or (name == "num_qubits" and value < 1):
                raise RetrievalIntegrityError(f"Feature {name}: conteggio fuori dominio.")
            value = math.log1p(value)
        elif value > 1:
            raise RetrievalIntegrityError(f"Feature {name}: indicatore fuori [0, 1].")
        result.append(value)
    return tuple(result)


@dataclass(frozen=True)
class FeatureTransform:
    divisors: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.divisors) != 49 or any(not math.isfinite(x) or x <= 0 for x in self.divisors):
            raise RetrievalIntegrityError("Divisori non validi.")

    @classmethod
    def fit_train(cls, features: Iterable[Mapping[str, Any]]) -> FeatureTransform:
        rows = [transform_unscaled(row) for row in features]
        if not rows:
            raise RetrievalIntegrityError("Nessun esempio train per la trasformazione.")
        return cls(tuple(max(abs(row[i]) for row in rows) or 1.0 for i in range(49)))

    def apply(self, features: Mapping[str, Any]) -> tuple[float, ...]:
        return tuple(x / d for x, d in zip(transform_unscaled(features), self.divisors, strict=True))

    def artifact(self, *, source_sha256: str, experiment_id: str) -> dict[str, Any]:
        core = {
            "version": TRANSFORM_VERSION, "experiment_id": experiment_id,
            "fit_split": "train", "source_jsonl_sha256": source_sha256,
            "feature_order": list(FEATURE_ORDER), "dimension": 49,
            "transforms": ["log1p" if n in LOG_FEATURES else "identity" for n in FEATURE_ORDER],
            "divisors": list(self.divisors), "scaling": "train_max_abs_or_one",
            "centering": False, "clipping": False, "l2_normalization": False,
            "distance": "Manhattan", "canonical_precision": "float64",
            "qdrant_vector_precision": "float32",
            "score_abs_tolerance": SCORE_ABS_TOL, "score_rel_tolerance": SCORE_REL_TOL,
            "ranking": "all_filtered_candidates_then_float64_distance_then_rag_id",
        }
        return {**core, "sha256": stable_sha256(core)}


def manhattan(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.fsum(abs(a - b) for a, b in zip(left, right, strict=True))

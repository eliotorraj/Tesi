"""Backward-compatible imports for request parsing and hardware masking."""

from .hardware import (
    DEVICE_DEFINITIONS,
    HardwareMaskBuilder,
    MqtHardwareCatalog,
    WidthCompatibilityFilter,
)
from .request import (
    FEATURE_NAMES,
    GATE_ALIASES,
    QasmRequestParser,
    RequestInput,
    RequestSemanticValidator,
    normalize_gate_id,
)

__all__ = [
    "DEVICE_DEFINITIONS",
    "FEATURE_NAMES",
    "GATE_ALIASES",
    "HardwareMaskBuilder",
    "MqtHardwareCatalog",
    "QasmRequestParser",
    "RequestInput",
    "RequestSemanticValidator",
    "WidthCompatibilityFilter",
    "normalize_gate_id",
]

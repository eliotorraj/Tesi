"""Espone gli adattatori locali usati dal prototipo."""

from .compilation import QiskitDeterministicCompiler
from .context import (
    EvidenceRegistryDataError,
    JsonDatasetContextRetriever,
    StructuredEvidenceRegistryBuilder,
    StructuredPromptBuilder,
)
from .explanations import DeterministicExplanationRenderer
from .hardware import HardwareCatalogIntegrityError
from .llm import CallableLlmGateway, UnconfiguredLlmGateway
from .parsing import (
    HardwareMaskBuilder,
    MqtHardwareCatalog,
    QasmRequestParser,
    RequestSemanticValidator,
    WidthCompatibilityFilter,
)
from .validation import StructuredRecommendationValidator

__all__ = [
    "CallableLlmGateway",
    "DeterministicExplanationRenderer",
    "EvidenceRegistryDataError",
    "HardwareCatalogIntegrityError",
    "HardwareMaskBuilder",
    "JsonDatasetContextRetriever",
    "MqtHardwareCatalog",
    "QasmRequestParser",
    "RequestSemanticValidator",
    "QiskitDeterministicCompiler",
    "StructuredEvidenceRegistryBuilder",
    "StructuredPromptBuilder",
    "StructuredRecommendationValidator",
    "UnconfiguredLlmGateway",
    "WidthCompatibilityFilter",
]

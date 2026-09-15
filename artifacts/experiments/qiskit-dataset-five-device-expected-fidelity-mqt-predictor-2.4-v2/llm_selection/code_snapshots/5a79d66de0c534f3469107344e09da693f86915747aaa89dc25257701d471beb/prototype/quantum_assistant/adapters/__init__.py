"""Espone gli adattatori locali usati dal prototipo."""

from .compilation import QiskitDeterministicCompiler
from .context import (
    EvidenceRegistryDataError,
    JsonDatasetContextRetriever,
    StructuredEvidenceRegistryBuilder,
    StructuredPromptBuilder,
)
from .qdrant_context import QdrantContextRetriever, LocalReferenceContextRetriever, RetrievalDatabaseError
from .rag_features import RetrievalIntegrityError
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
    "QdrantContextRetriever",
    "LocalReferenceContextRetriever",
    "RetrievalDatabaseError",
    "RetrievalIntegrityError",
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

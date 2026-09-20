"""Costruzione del prototipo locale con gli adattatori predefiniti."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from qiskit_dataset.catalog import V2_CATALOG_PATH, load_catalog

from .adapters.compilation import QiskitDeterministicCompiler
from .adapters.context import (
    StructuredEvidenceRegistryBuilder,
    StructuredPromptBuilder,
)
from .adapters.parsing import (
    HardwareMaskBuilder,
    MqtHardwareCatalog,
    QasmRequestParser,
    RequestSemanticValidator,
)
from .adapters.validation import StructuredRecommendationValidator
from .adapters.qdrant_context import QdrantContextRetriever, LocalReferenceContextRetriever, DisabledContextRetriever
from .adapters.rag_dataset import DEFAULT_DATASET, DEFAULT_RAG_ROOT
from .ports import LlmGateway
from .services import PrototypeService


def build_default_service(
    *,
    device_names: Sequence[str],
    dataset_path: Path = DEFAULT_DATASET,
    rag_root: Path = DEFAULT_RAG_ROOT,
    retrieval_backend: str = "qdrant",
    llm_gateway: LlmGateway,
    max_llm_attempts: int = 3,
    retrieval_limit: int = 5,
    dataset_required: bool = False,
    configuration_catalog_path: Path = V2_CATALOG_PATH,
) -> PrototypeService:
    """Costruisce il servizio lasciando sostituibile il collegamento all'LLM."""
    backends = {"qdrant": QdrantContextRetriever, "reference": LocalReferenceContextRetriever, "none": DisabledContextRetriever}
    if retrieval_backend not in backends:
        raise ValueError("retrieval_backend deve essere qdrant, reference oppure none.")
    configuration_catalog = load_catalog(configuration_catalog_path)
    hardware_catalog = MqtHardwareCatalog(
        device_names,
        configuration_catalog=configuration_catalog,
    )
    return PrototypeService(
        parser=QasmRequestParser(),
        hardware_catalog=hardware_catalog,
        semantic_validator=RequestSemanticValidator(),
        compatibility_filter=HardwareMaskBuilder(),
        context_retriever=backends[retrieval_backend](dataset_path, rag_root=rag_root),
        prompt_builder=StructuredPromptBuilder(
            configuration_catalog=configuration_catalog,
        ),
        evidence_registry_builder=StructuredEvidenceRegistryBuilder(
            configuration_catalog=configuration_catalog,
        ),
        llm_gateway=llm_gateway,
        validator=StructuredRecommendationValidator(
            configuration_catalog=configuration_catalog,
        ),
        compiler=QiskitDeterministicCompiler(),
        max_llm_attempts=max_llm_attempts,
        retrieval_limit=retrieval_limit,
    )
